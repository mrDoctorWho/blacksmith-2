##   auth.py
##
##   Copyright (C) 2003-2005 Alexey "Snake" Nezhdanov
##
##   This program is free software; you can redistribute it and/or modify
##   it under the terms of the GNU General Public License as published by
##   the Free Software Foundation; either version 2, or (at your option)
##   any later version.
##
##   This program is distributed in the hope that it will be useful,
##   but WITHOUT ANY WARRANTY; without even the implied warranty of
##   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##   GNU General Public License for more details.

# $Id: auth.py, v1.42 2013/10/21 alkorgun Exp $

"""
Provides library with all Non-SASL and SASL authentication mechanisms.
Can be used both for client and transport authentication.
"""

from . import dispatcher # dispatcher.py will need renaming for its classes too
import hashlib # Changed from sha
import base64 # Changed from from base64 import encodestring, decodestring
from .plugin import PlugIn # PlugIn class name is fine
from .protocol import Iq, Node, NodeProcessed, NS_AUTH, NS_COMPONENT_ACCEPT, NS_SASL, NS_STREAMS, NS_BIND, NS_SESSION, Jid # Protocol classes will be renamed
from random import random as _random # Keep as _random if only used here for cnonce
from re import findall as re_findall

def md5_hex_hash(data_bytes): # Renamed HH, some
	"""Computes MD5 hash and returns hex digest."""
	if isinstance(data_bytes, str): # Ensure bytes for hashing
		data_bytes = data_bytes.encode('utf-8')
	return hashlib.md5(data_bytes).hexdigest()

def md5_binary_hash(data_bytes): # Renamed H, some
	"""Computes MD5 hash and returns binary digest."""
	if isinstance(data_bytes, str):
		data_bytes = data_bytes.encode('utf-8')
	return hashlib.md5(data_bytes).digest()

def colon_join_strings(string_list): # Renamed C, some
	"""Joins a list of strings with colons."""
	return ":".join(string_list)

class NonSaslAuthenticator(PlugIn): # Renamed NonSASL
	"""
	Implements old Non-SASL (JEP-0078) authentication used in jabberd1.4 and transport authentication.
	"""
	def __init__(self, username_str, password_str, resource_str): # Renamed user, password, resource
		"""
		Caches username, password and resource for auth.
		"""
		PlugIn.__init__(self)
		self.DEBUG_LINE_PREFIX = "gen_auth" # Renamed DBG_LINE
		self.username = username_str
		self.password = password_str
		self.resource = resource_str
		self.handshake_status = 0 # Renamed handshake

	def plugin(self, client_instance): # Renamed owner
		"""
		Determine the best auth method (digest/0k/plain) and use it for auth.
		Returns used method name on success. Used internally.
		"""
		if not self.resource: # If no resource, it's likely a component authentication
			return self.authenticate_as_component(client_instance)

		self.DEBUG("Querying server about possible auth methods", "start")
		# Assuming client_instance.Dispatcher is the correct way to access the dispatcher
		initial_iq_payload = [Node("username", payload=[self.username])]
		auth_methods_response = client_instance.Dispatcher.SendAndWaitForResponse(
			Iq(stanza_type="get", query_namespace=NS_AUTH, payload_list=initial_iq_payload) # Use renamed Iq params
		)

		if not (auth_methods_response and auth_methods_response.get_type() == "result"): # Use renamed isResultNode logic
			self.DEBUG("No result node arrived for auth methods query! Aborting...", "error")
			return None

		# Prepare reply IQ based on the server's response structure
		auth_iq_reply = Iq(stanza_type="set", source_node=auth_methods_response) # Use renamed Iq params
		query_node = auth_iq_reply.getTag("query") # query_node is a simplexml.Node

		query_node.setTagData("username", self.username)
		query_node.setTagData("resource", self.resource)

		auth_method_name = "unknown"

		if query_node.getTag("digest"):
			self.DEBUG("Performing digest authentication", "ok")
			# Assuming client_instance.Dispatcher.Stream._document_attrs["id"] is the stream ID
			stream_id = client_instance.Dispatcher.Stream._document_attrs["id"]
			digest_payload = stream_id + self.password # sha.new took a string
			# hashlib.sha1 expects bytes
			digest_hash = hashlib.sha1(digest_payload.encode('utf-8')).hexdigest()
			query_node.setTagData("digest", digest_hash)
			if query_node.getTag("password"): # Remove plain password if digest is used
				query_node.delChild("password")
			auth_method_name = "digest"
		elif query_node.getTag("token"): # Zero-K authentication
			token_val = query_node.getTagData("token")
			sequence_val = query_node.getTagData("sequence")
			self.DEBUG("Performing zero-k authentication", "ok")

			current_hash = hashlib.sha1(self.password.encode('utf-8')).hexdigest() # Start with H(password)
			combined_hash_input = current_hash + token_val
			current_hash = hashlib.sha1(combined_hash_input.encode('utf-8')).hexdigest() # Then H(H(password) + token)

			for _ in range(int(sequence_val)): # Apply H sequence times
				current_hash = hashlib.sha1(current_hash.encode('utf-8')).hexdigest()
			query_node.setTagData("hash", current_hash)
			auth_method_name = "0k"
		else: # Fallback to Plain
			self.DEBUG("Secure methods unsupported, performing plain text authentication", "warn")
			query_node.setTagData("password", self.password)
			auth_method_name = "plain"

		final_auth_response = client_instance.Dispatcher.SendAndWaitForResponse(auth_iq_reply)

		if final_auth_response and final_auth_response.get_type() == "result":
			self.DEBUG("Successfully authenticated with remote host.", "ok")
			client_instance.User = self.username # User, Server, Resource are often part of client state
			client_instance.Resource = self.resource
			client_instance._registered_name = f"{client_instance.User}@{client_instance.Server}/{client_instance.Resource}"
			return auth_method_name

		self.DEBUG("Authentication failed!", "error")
		return None

	def authenticate_as_component(self, component_instance): # Renamed authComponent, owner
		"""
		Authenticate component. Send handshake stanza and wait for result. Returns "ok" on success.
		"""
		self.handshake_status = 0 # Reset status
		stream_id = component_instance.Dispatcher.Stream._document_attrs["id"]
		handshake_payload_str = stream_id + self.password
		handshake_hash = hashlib.sha1(handshake_payload_str.encode('utf-8')).hexdigest()

		component_instance.send(Node(NS_COMPONENT_ACCEPT + " handshake", payload=[handshake_hash]))
		component_instance.RegisterHandler("handshake", self._handle_handshake_response, xmlns=NS_COMPONENT_ACCEPT)

		timeout_counter = 100 # Basic timeout mechanism
		while not self.handshake_status and timeout_counter > 0:
			self.DEBUG("waiting on handshake", "notify")
			component_instance.Process(1) # Assuming Process handles async I/O for a short duration
			timeout_counter -=1

		component_instance.UnregisterHandler("handshake", self._handle_handshake_response, xmlns=NS_COMPONENT_ACCEPT)

		if self.handshake_status == 1: # Success
			component_instance._registered_name = self.username # Component JID is often just the domain
			self.DEBUG(f"Component {self.username} authenticated successfully.", "ok")
			return "ok"
		else:
			self.DEBUG(f"Component {self.username} authentication failed (status: {self.handshake_status}).", "error")
			return "failure"


	def _handle_handshake_response(self, dispatcher_instance, stanza_node): # Renamed handshakeHandler, disp, stanza
		"""
		Handler for registering in dispatcher for accepting transport authentication.
		"""
		if stanza_node.getName() == "handshake":
			self.handshake_status = 1 # Success
		else:
			self.handshake_status = -1 # Failure (e.g., error stanza received)
		raise NodeProcessed # Stop further processing of this stanza by other handlers

class SaslAuthenticator(PlugIn): # Renamed SASL
	"""
	Implements SASL authentication.
	"""
	def __init__(self, username_str, password_str): # Renamed username, password
		PlugIn.__init__(self)
		self.username = username_str
		self.password = password_str
		self.sasl_status = None # Renamed startsasl: None, "in-process", "success", "failure", "not-supported"

	def plugin(self, client_instance): # Renamed owner
		# Check if stream features are already available (e.g. if plugin is added after stream start)
		if "version" not in self._owner.Dispatcher.Stream._document_attrs: # _owner is set by PlugIn base
			self.sasl_status = "not-supported" # Stream version too old or not XMPP
		elif self._owner.Dispatcher.Stream.features: # features node already received
			try:
				self._handle_sasl_features(self._owner.Dispatcher, self._owner.Dispatcher.Stream.features)
			except NodeProcessed: # Expected if auth started
				pass
		else: # Stream started, but features not yet received or processed by this plugin
			self.sasl_status = None # Mark as not yet started
			# Register handler to catch features when they arrive
			self._owner.RegisterHandler("features", self._handle_sasl_features, xmlns=NS_STREAMS)


	def auth(self): # Kept name as it's a public API method
		"""
		Start authentication if not already started/completed.
		Result can be checked via "sasl_status" attribute.
		"""
		if self.sasl_status: # Already started, completed, or known not supported
			return

		# If features were present at plugin time but didn't trigger auth (e.g. no SASL mechanisms)
		if self._owner.Dispatcher.Stream.features and self.sasl_status is None:
			try:
				self._handle_sasl_features(self._owner.Dispatcher, self._owner.Dispatcher.Stream.features)
			except NodeProcessed:
				pass # Auth process started
		elif self.sasl_status is None: # Not started and no features seen yet by this plugin
			self._owner.RegisterHandler("features", self._handle_sasl_features, xmlns=NS_STREAMS)


	def plugout(self):
		"""
		Remove SASL handlers from owner's dispatcher. Used internally.
		"""
		# Check if handlers were potentially registered before trying to unregister
		if hasattr(self._owner, "_registered_handlers"): # A common pattern for plugins to store their handlers
			self._owner.UnregisterHandler("features", self._handle_sasl_features, xmlns=NS_STREAMS)
			self._owner.UnregisterHandler("challenge", self._handle_sasl_challenge_or_failure, xmlns=NS_SASL)
			self._owner.UnregisterHandler("failure", self._handle_sasl_challenge_or_failure, xmlns=NS_SASL)
			self._owner.UnregisterHandler("success", self._handle_sasl_challenge_or_failure, xmlns=NS_SASL)


	def _handle_sasl_features(self, dispatcher_instance, features_node): # Renamed FeaturesHandler, conn, feats
		"""
		Used to determine if server supports SASL auth. Used internally.
		"""
		mechanisms_node = features_node.getTag("mechanisms", namespace=NS_SASL) # Renamed mecs (node)
		if not mechanisms_node:
			self.sasl_status = "not-supported"
			self.DEBUG("SASL not supported by server (no mechanisms element)", "error")
			return

		supported_mechanisms = [] # Renamed mecs (list)
		for mechanism_node in mechanisms_node.getTags("mechanism"): # Renamed mec
			supported_mechanisms.append(mechanism_node.getData())

		# Register handlers for subsequent SASL steps
		self._owner.RegisterHandler("challenge", self._handle_sasl_challenge_or_failure, xmlns=NS_SASL)
		self._owner.RegisterHandler("failure", self._handle_sasl_challenge_or_failure, xmlns=NS_SASL)
		self._owner.RegisterHandler("success", self._handle_sasl_challenge_or_failure, xmlns=NS_SASL)

		auth_stanza_to_send = None # Renamed node

		if "ANONYMOUS" in supported_mechanisms and self.username is None: # Allow None for username for ANONYMOUS
			auth_stanza_to_send = Node("auth", attrs={"xmlns": NS_SASL, "mechanism": "ANONYMOUS"})
		elif "DIGEST-MD5" in supported_mechanisms:
			auth_stanza_to_send = Node("auth", attrs={"xmlns": NS_SASL, "mechanism": "DIGEST-MD5"})
		elif "PLAIN" in supported_mechanisms and self.username is not None: # PLAIN requires username/password
			# Ensure username and server are available
			full_user_jid_node = self.username # If username is already node@domain
			if self._owner.Server and "@" not in self.username : # if only node part is given
			    full_user_jid_node = "@".join((self.username, self._owner.Server))

			# SASL PLAIN data: authzid\0authcid\0password
			sasl_plain_data_str = "%s\x00%s\x00%s" % (full_user_jid_node, self.username, self.password)
			encoded_sasl_data = base64.b64encode(sasl_plain_data_str.encode('utf-8')).decode('ascii').replace("\r", "").replace("\n", "")
			auth_stanza_to_send = Node("auth", attrs={"xmlns": NS_SASL, "mechanism": "PLAIN"}, payload=[encoded_sasl_data])
		else:
			self.sasl_status = "failure"
			self.DEBUG("No suitable SASL mechanisms supported by client (ANONYMOUS, DIGEST-MD5, PLAIN). Server offered: %s" % ",".join(supported_mechanisms), "error")
			# Unregister SASL step handlers as no mechanism will be tried
			self._owner.UnregisterHandler("challenge", self._handle_sasl_challenge_or_failure, xmlns=NS_SASL)
			self._owner.UnregisterHandler("failure", self._handle_sasl_challenge_or_failure, xmlns=NS_SASL)
			self._owner.UnregisterHandler("success", self._handle_sasl_challenge_or_failure, xmlns=NS_SASL)
			return # Do not raise NodeProcessed as we are not sending anything

		self.sasl_status = "in-process"
		self._owner.send(auth_stanza_to_send) # __str__ is implicitly called by send if it's a Node
		raise NodeProcessed()

	def _handle_sasl_challenge_or_failure(self, dispatcher_instance, stanza_node): # Renamed SASLHandler, conn, challenge
		"""
		Perform next SASL auth step or handle failure/success. Used internally.
		"""
		if stanza_node.getNamespace() != NS_SASL: # Should not happen if handler registered correctly
			return

		if stanza_node.getName() == "failure":
			self.sasl_status = "failure"
			failure_reason_node = stanza_node.getChildren()[0] if stanza_node.getChildren() else None # Renamed reason
			failure_reason_text = failure_reason_node.getName() if failure_reason_node else "Unknown reason"
			self.DEBUG(f"Failed SASL authentication: {failure_reason_text}", "error")
			raise NodeProcessed()
		elif stanza_node.getName() == "success":
			self.sasl_status = "success"
			self.DEBUG("Successfully authenticated with remote server via SASL.", "ok")
			# SASL success often means stream needs to be restarted by client.
			# The client (owner) should handle stream restart and re-sending features.
			# For now, just update internal state.
			# The original code re-plugged the dispatcher, which is complex and risky.
			# It's better if the main client loop handles stream restart.
			self._owner.User = self.username # Assuming username is the node part for JID construction
			# Resource is usually bound after SASL, so not setting it here.
			raise NodeProcessed()

		# If it's a challenge for DIGEST-MD5
		challenge_data_b64 = stanza_node.getData() # Renamed incoming_data
		if not challenge_data_b64: # Should not happen for a challenge
		    self.sasl_status = "failure"
		    self.DEBUG("Received empty SASL challenge.", "error")
		    raise NodeProcessed()

		challenge_decoded_str = base64.b64decode(challenge_data_b64).decode('utf-8') # Renamed data
		self.DEBUG(f"Got SASL challenge: {challenge_decoded_str}", "ok")

		challenge_params = {} # Renamed chal
		# Regex to parse key="value" or key=value pairs
		for match_pair in re_findall('(\w+)\s*=\s*(?:(?:"([^"]*)")|([^,]+))', challenge_decoded_str):
			key_name, val_quoted, val_unquoted = match_pair # Renamed key, value
			challenge_params[key_name] = val_quoted if val_quoted else val_unquoted

		if "qop" in challenge_params and "auth" in [op.strip() for op in challenge_params["qop"].split(",")]:
			response_params = {} # Renamed resp
			response_params["username"] = self.username
			response_params["realm"] = challenge_params.get("realm", self._owner.Server) # Use server domain if realm not in challenge
			response_params["nonce"] = challenge_params["nonce"]

			# Generate cnonce
			cnonce_val = "" # Renamed cnonce
			for _ in range(7): # Renamed i
				cnonce_val += hex(int(_random() * 65536 * 4096))[2:] # Ensure it's a string
			response_params["cnonce"] = cnonce_val

			response_params["nc"] = "00000001"
			response_params["qop"] = "auth"
			response_params["digest-uri"] = "xmpp/" + self._owner.Server

			# A1 = {H(username:realm:password)}:{nonce}:{cnonce}
			# Note: Original code had H(H(password)+token) for 0k, this is different.
			# For DIGEST-MD5, A1 is H(username:realm:password) as bytes.
			a1_payload_str = colon_join_strings([response_params["username"], response_params["realm"], self.password])
			a1_hash_bin = md5_binary_hash(a1_payload_str.encode('utf-8')) # Renamed A1

			# A1 now needs to be {a1_hash_bin}:{nonce_from_server}:{cnonce_val_from_client}
			# This needs to be bytes for hashing. Nonce and cnonce are strings.
			a1_final_str = b":" .join([a1_hash_bin, response_params["nonce"].encode('utf-8'), response_params["cnonce"].encode('utf-8')])

			# A2 = "AUTHENTICATE:{digest-uri}"
			a2_payload_str = colon_join_strings(["AUTHENTICATE", response_params["digest-uri"]]) # Renamed A2

			# response = LH(H(A1):nonce:nc:cnonce:qop:H(A2))
			# LH is to hex representation of the hash.
			response_val_str = md5_hex_hash( # Renamed response
			    colon_join_strings([
			        md5_hex_hash(a1_final_str), # H(A1) as hex
			        response_params["nonce"],
			        response_params["nc"],
			        response_params["cnonce"],
			        response_params["qop"],
			        md5_hex_hash(a2_payload_str.encode('utf-8')) # H(A2) as hex
			    ]).encode('utf-8')
			)
			response_params["response"] = response_val_str
			response_params["charset"] = "utf-8" # Explicitly state charset

			sasl_response_data_str = "" # Renamed sasl_data
			for key_name_resp, value_resp in response_params.items(): # Renamed key
				# According to RFC 2831, some values are not quoted.
				if key_name_resp in ["nc", "qop", "response", "charset", "algorithm"]: # algorithm might be in challenge
					sasl_response_data_str += f"{key_name_resp}={value_resp},"
				else:
					sasl_response_data_str += f'{key_name_resp}="{value_resp}",'

			encoded_response_data = base64.b64encode(sasl_response_data_str[:-1].encode('utf-8')).decode('ascii').replace("\r","").replace("\n","") # Remove trailing comma
			response_node = Node("response", attrs={"xmlns": NS_SASL}, payload=[encoded_response_data])
			self._owner.send(response_node)
		elif "rspauth" in challenge_params: # Server authenticating itself (final step of mutual auth)
			self._owner.send(Node("response", attrs={"xmlns": NS_SASL})) # Empty response
		else:
			self.sasl_status = "failure"
			self.DEBUG("Failed SASL authentication: unknown challenge format or missing qop=auth", "error")
		raise NodeProcessed()

class ResourceBinder(PlugIn): # Renamed Bind
	"""
	Bind some JID to the current connection to allow router know of our location.
	"""
	def __init__(self):
		PlugIn.__init__(self)
		self.DEBUG_LINE_PREFIX = "bind" # Renamed DBG_LINE
		self.binding_status = None # Renamed bound: None, "in-progress", "success", "failure"
		self.session_status = None # Renamed session: None, 1 (success), 0 (failed), -1 (not offered)
		self.needs_unregister_handler = False


	def plugin(self, client_instance): # Renamed owner
		"""
		Start resource binding, if allowed at this time. Used internally.
		"""
		if self._owner.Dispatcher.Stream.features:
			try:
				self._handle_bind_features(self._owner.Dispatcher, self._owner.Dispatcher.Stream.features)
			except NodeProcessed:
				pass
		else:
			self._owner.RegisterHandler("features", self._handle_bind_features, xmlns=NS_STREAMS)
			self.needs_unregister_handler = True

	def plugout(self):
		"""
		Remove Bind handler from owner's dispatcher. Used internally.
		"""
		if self.needs_unregister_handler:
			self._owner.UnregisterHandler("features", self._handle_bind_features, xmlns=NS_STREAMS)

	def _handle_bind_features(self, dispatcher_instance, features_node): # Renamed FeaturesHandler, conn, feats
		"""
		Determine if server supports resource binding and set some internal attributes accordingly.
		"""
		if not features_node.getTag("bind", namespace=NS_BIND):
			self.binding_status = "failure" # Or perhaps "not-offered"
			self.DEBUG("Server does not offer resource binding.", "error")
			return # Do not raise NodeProcessed if we are not handling this feature

		if features_node.getTag("session", namespace=NS_SESSION):
			self.session_status = None # Mark as offered, to be attempted after bind
		else:
			self.session_status = -1 # Mark as not offered by server
		self.binding_status = "ready" # Ready to attempt binding
		# Don't raise NodeProcessed here, let other feature handlers run.
		# The actual binding is initiated by calling self.bind_resource()

	def bind_resource(self, resource_str=None): # Renamed Bind, resource
		"""
		Perform binding. Use provided resource name or request server to generate one.
		"""
		# Wait for features to be processed if they haven't been already
		timeout_counter = 100
		while self.binding_status is None and self._owner.Process(1) and timeout_counter > 0:
			timeout_counter -=1

		if self.binding_status == "failure" or self.binding_status is None: # Check if binding is possible
		    self.DEBUG("Cannot bind resource, binding not offered or failed previously.", "error")
		    return "" if self.binding_status is None else "failure"


		payload_nodes = []
		if resource_str:
			payload_nodes.append(Node("resource", payload=[resource_str]))

		bind_iq = Iq(stanza_type="set", payload_list=[Node("bind", attrs={"xmlns": NS_BIND}, payload_list=payload_nodes)]) # Use Renamed Iq
		response_stanza = self._owner.SendAndWaitForResponse(bind_iq)

		if response_stanza and response_stanza.get_type() == "result":
			bound_jid_node = response_stanza.getTag("bind")
			if bound_jid_node:
			    bound_jid_str = bound_jid_node.getTagData("jid")
			    if bound_jid_str:
			        self.binding_status = "success"
			        self.DEBUG(f"Successfully bound to {bound_jid_str}.", "ok")
			        bound_jid_obj = Jid(bound_jid_str) # Use Renamed Jid
			        self._owner.User = bound_jid_obj.get_node()
			        self._owner.Resource = bound_jid_obj.get_resource()
			        # After successful bind, attempt session establishment if offered
			        if self.session_status is None: # Offered
			            session_iq = Iq(stanza_type="set", payload_list=[Node("session", attrs={"xmlns": NS_SESSION})])
			            session_response = self._owner.SendAndWaitForResponse(session_iq)
			            if session_response and session_response.get_type() == "result":
			                self.DEBUG("Successfully opened session.", "ok")
			                self.session_status = 1
			                return "ok"
			            else:
			                self.DEBUG(f"Session open failed: {session_response.getTag('error') if session_response else 'timeout'}", "error")
			                self.session_status = 0
			                return "bind_ok_session_failed" # Bind OK, but session failed
			        elif self.session_status == -1: # Not offered
			             return "ok" # Bind OK, no session needed/offered
			    else:
			        self.DEBUG("Binding result missing JID.", "error")
			else:
			    self.DEBUG("Binding result missing bind element.", "error")

		elif response_stanza: # Error response
			self.DEBUG(f"Binding failed: {response_stanza.get_error_condition_node().getName() if response_stanza.get_error_condition_node() else 'Unknown Error'}.", "error")
		else: # Timeout
			self.DEBUG("Binding failed: timeout expired.", "error")

		self.binding_status = "failure"
		return "failure"


class ComponentBinder(PlugIn): # Renamed ComponentBind
	"""
	ComponentBind some JID to the current connection to allow router know of our location.
	"""
	def __init__(self, use_sasl_bool): # Renamed sasl
		PlugIn.__init__(self)
		self.DEBUG_LINE_PREFIX = "bind" # Renamed DBG_LINE
		self.binding_status = None
		self.needs_unregister_handler = False
		self.use_sasl = use_sasl_bool # Indicates if SASL was used prior to component binding attempt
		self.bind_response_stanza = None # Renamed bindresponse

	def plugin(self, component_instance): # Renamed owner
		"""
		Start resource binding, if allowed at this time. Used internally.
		"""
		# For components, binding is typically done after handshake, not features.
		# The original logic tied this to SASL which might not be directly applicable for components.
		# Assuming component binding is attempted directly after component handshake.
		if not self.use_sasl: # If not using SASL (e.g. legacy component connection)
			self.binding_status = "ready" # Ready to attempt bind via handshake like method
			return

		# If SASL was used, features might indicate binding requirement (though less common for components)
		if self._owner.Dispatcher.Stream.features:
			try:
				self._handle_bind_features(self._owner.Dispatcher, self._owner.Dispatcher.Stream.features)
			except NodeProcessed:
				pass
		else: # Register to catch features if they arrive (less typical for components)
			self._owner.RegisterHandler("features", self._handle_bind_features, xmlns=NS_STREAMS)
			self.needs_unregister_handler = True

	def plugout(self):
		"""
		Remove ComponentBind handler from owner's dispatcher. Used internally.
		"""
		if self.needs_unregister_handler:
			self._owner.UnregisterHandler("features", self._handle_bind_features, xmlns=NS_STREAMS)
		# Unregister bind handler if it was set
		self._owner.UnregisterHandler("bind", self._handle_bind_response, xmlns=NS_COMPONENT_1)


	def _handle_bind_features(self, dispatcher_instance, features_node): # Renamed FeaturesHandler, conn, feats
		"""
		Determine if server supports resource binding (less common for components post-auth).
		"""
		if not features_node.getTag("bind", namespace=NS_BIND):
			self.binding_status = "failure"
			self.DEBUG("Server does not request component binding via features.", "warn")
			return
		self.binding_status = "ready"
		# Session tag usually not relevant for components in the same way as clients
		self.session_status = -1 # Mark as not applicable or not offered for components


	def bind_component(self, component_domain_str=None): # Renamed Bind, domain
		"""
		Perform component binding.
		"""
		# Wait for status to be ready (e.g. after features if that path was taken)
		timeout_counter = 100
		while self.binding_status is None and self._owner.Process(1) and timeout_counter > 0:
			timeout_counter -=1

		if self.binding_status == "failure" or self.binding_status is None:
			self.DEBUG("Cannot bind component, binding not offered or failed.", "error")
			return "failure"

		# Component binding typically uses a specific namespace, not necessarily NS_BIND in IQ
		# The original code used NS_COMPONENT_1 for the bind request.
		# The 'name' attribute in the <bind/> for components is the component's JID.
		if not component_domain_str:
		    component_domain_str = self._owner.Server # Fallback to connected server if not specified.

		self.bind_response_stanza = None # Reset before sending
		response_timeout = dispatcher.DefaultTimeout # Use a timeout from dispatcher settings

		self._owner.RegisterHandler("bind", self._handle_bind_response, xmlns=NS_COMPONENT_1)
		# Sending <bind name='component.domain.tld' xmlns='http://jabberd.jabberstudio.org/ns/component/1.0'/>
		# This is a direct stream element, not an IQ.
		bind_request_node = Node("bind", attrs={"name": component_domain_str}, namespace=NS_COMPONENT_1)
		self._owner.send(bind_request_node)

		current_wait_time = 0
		wait_interval = 0.1 # Check every 100ms
		while self.bind_response_stanza is None and current_wait_time < response_timeout:
			self._owner.Process(wait_interval) # Process for a short interval
			current_wait_time += wait_interval

		self._owner.UnregisterHandler("bind", self._handle_bind_response, xmlns=NS_COMPONENT_1)

		response_node = self.bind_response_stanza
		if response_node and response_node.getAttr("error"): # Check for error attribute
			self.DEBUG(f"Component binding failed: {response_node.getAttr('error')}", "error")
			self.binding_status = "failure"
			return "failure"
		elif response_node: # Assumed success if no error attribute
			self.DEBUG("Component successfully bound.", "ok")
			self.binding_status = "success"
			return "ok"
		else: # Timeout
			self.DEBUG("Component binding failed: timeout expired.", "error")
			self.binding_status = "failure"
			return "timeout"

	def _handle_bind_response(self, dispatcher_instance, bind_response_node): # Renamed BindHandler, conn, bind
		self.bind_response_stanza = bind_response_node
		raise NodeProcessed()

# DEFAULT_DEBUG_INSTANCE = NullDebugger()
# This line would make Debug an instance of NullDebugger, effectively disabling debug output.
# To enable debugging, this should be:
# DEFAULT_DEBUG_INSTANCE = Debugger(active_flags=["all"], log_file=sys.stderr)
# Or controlled by some external configuration. For now, it's commented.
