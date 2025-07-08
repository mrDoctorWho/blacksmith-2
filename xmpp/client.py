##   client.py
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

# $Id: client.py, v1.62 2013/10/21 alkorgun Exp $

"""
Provides PlugIn class functionality to develop extentions for xmpppy.
Also provides Client and Component classes implementations as the
examples of xmpppy structures usage.
These classes can be used for simple applications "AS IS" though.
"""

from . import debug as DebugModule # Renamed debug to DebugModule to avoid conflict with Debugger class
from . import transports
from . import dispatcher
from . import auth
from . import roster

from .plugin import PlugIn

# Assuming DebugModule.Debugger is the intended class
# And color constants are from DebugModule
DebugModule.Debugger.colors["socket"] = DebugModule.COLOR_DARK_GRAY
DebugModule.Debugger.colors["CONNECTproxy"] = DebugModule.COLOR_DARK_GRAY # Typo CONNECTproxy -> CONNECT_PROXY
DebugModule.Debugger.colors["nodebuilder"] = DebugModule.COLOR_BROWN
DebugModule.Debugger.colors["client"] = DebugModule.COLOR_CYAN
DebugModule.Debugger.colors["component"] = DebugModule.COLOR_CYAN
DebugModule.Debugger.colors["dispatcher"] = DebugModule.COLOR_GREEN
DebugModule.Debugger.colors["browser"] = DebugModule.COLOR_BLUE
DebugModule.Debugger.colors["auth"] = DebugModule.COLOR_YELLOW
DebugModule.Debugger.colors["roster"] = DebugModule.COLOR_MAGENTA
DebugModule.Debugger.colors["ibb"] = DebugModule.COLOR_YELLOW
DebugModule.Debugger.colors["down"] = DebugModule.COLOR_BROWN
DebugModule.Debugger.colors["up"] = DebugModule.COLOR_BROWN
DebugModule.Debugger.colors["data"] = DebugModule.COLOR_BROWN
DebugModule.Debugger.colors["ok"] = DebugModule.COLOR_GREEN
DebugModule.Debugger.colors["warn"] = DebugModule.COLOR_YELLOW
DebugModule.Debugger.colors["error"] = DebugModule.COLOR_RED
DebugModule.Debugger.colors["start"] = DebugModule.COLOR_DARK_GRAY
DebugModule.Debugger.colors["stop"] = DebugModule.COLOR_DARK_GRAY
DebugModule.Debugger.colors["sent"] = DebugModule.COLOR_YELLOW
DebugModule.Debugger.colors["got"] = DebugModule.COLOR_BRIGHT_CYAN

DEBUG_SCOPE_CLIENT = "client" # Renamed DBG_CLIENT
DEBUG_SCOPE_COMPONENT = "component" # Renamed DBG_COMPONENT


class BaseClient(object): # Renamed CommonClient
	"""
	Base for XMPPClient and XMPPComponent classes.
	"""
	def __init__(self, server_host, server_port=5222, debug_scope_list=None): # Renamed params
		"""
		Caches server name and (optionally) port to connect to. "debug_scope_list" parameter specifies
		the debug IDs that will go into debug output. You can either specifiy an "include"
		or "exclude" list. The latter is done via adding "always" pseudo-ID to the list.
		Full list: ["nodebuilder", "dispatcher", "gen_auth", "SASL_auth", "bind", "socket",
		"CONNECT_PROXY", "TLS", "roster", "browser", "ibb"].
		"""
		if isinstance(self, XMPPClient): # Use new class name
			self.stanza_namespace, self.debug_scope_name = auth.NS_CLIENT, DEBUG_SCOPE_CLIENT # Use new name
		elif isinstance(self, XMPPComponent): # Use new class name
			self.stanza_namespace, self.debug_scope_name = dispatcher.NS_COMPONENT_ACCEPT, DEBUG_SCOPE_COMPONENT # Use new name

		self.default_stanza_namespace = self.stanza_namespace # Renamed defaultNamespace
		self.disconnect_handlers = []
		self.server_host = server_host # Renamed Server
		self.server_port = server_port # Renamed Port

		if debug_scope_list and not isinstance(debug_scope_list, list):
			# Default debug if not a list (original had ["always", "nodebuilder"])
			debug_scope_list = [DebugModule.DBG_ALWAYS, "nodebuilder"]
		elif not debug_scope_list: # If None or empty list
		    debug_scope_list = []


		self._debugger = DebugModule.Debugger(active_flags=debug_scope_list) # Renamed _DEBUG
		self.DEBUG = self._debugger.show_formatted_message # Renamed Show
		# self.debug_flags should refer to the list within the debugger instance
		# self.debug_flags = self._debugger.debug_flags # This was incorrect; debug_flags is an attribute of Debugger, not a list to append to here
		# The Debugger class itself should handle its own debug_flags.
		# If self.debug_scope_name needs to be added to the Debugger's known flags, that should happen in Debugger.
		# For now, assuming Debugger handles its flags internally based on active_flags.

		self._owner = self # This is a common pattern for plugins to reference their parent
		self._registered_jid_str = None # Renamed _registered_name
		self.register_disconnect_handler(self._default_disconnect_handler) # Use new name
		self.connection_status = "" # Renamed connected
		self.enable_routing_logic = False # Renamed _route (assuming boolean)

	def register_disconnect_handler(self, handler_func): # Renamed RegisterDisconnectHandler, handler
		"""
		Register handler that will be called on disconnect.
		"""
		self.disconnect_handlers.append(handler_func)

	def unregister_disconnect_handler(self, handler_func): # Renamed UnregisterDisconnectHandler, handler
		"""
		Unregister handler that is called on disconnect.
		"""
		self.disconnect_handlers.remove(handler_func)

	def _handle_disconnection(self): # Renamed disconnected
		"""
		Called on disconnection. Calls disconnect handlers and cleans things up.
		"""
		self.connection_status = ""
		self.DEBUG(self.debug_scope_name, "Disconnect detected", "stop")
		# Iterate in reverse for calling, but original list order is preserved
		for handler_func in reversed(self.disconnect_handlers): # Renamed dhnd
			handler_func()
		# No need to reverse again if we iterate over a reversed copy

		if hasattr(self, "TLS") and self.TLS: # Check if TLS plugin exists
			self.TLS.PlugOut() # TLS should be an instance of a TLS plugin class

	def _default_disconnect_handler(self): # Renamed DisconnectHandler
		"""
		Default disconnect handler. Just raises an IOError.
		"""
		raise IOError("Disconnected from server!")

	def event(self, event_name_str, event_args_dict={}): # Renamed eventName, args
		"""
		Default event handler. To be overriden.
		"""
		print_colored(f"Event: {event_name_str} - {event_args_dict}", DebugModule.COLOR_YELLOW) # Use print_colored

	def is_connected(self): # Renamed isConnected
		"""
		Returns connection state. F.e.: None / "tls" / "tcp+old_auth" .
		"""
		return self.connection_status

	def reconnect_and_reauthenticate(self, handlers_to_save=None): # Renamed reconnectAndReauth
		"""
		Example of reconnection method.
		"""
		should_save_dispatcher_handlers = False # Renamed Dispatcher_
		if handlers_to_save is None:
			should_save_dispatcher_handlers = True
			handlers_to_save = self.Dispatcher.dumpHandlers() # Dispatcher needs to be an attribute

		# Plugin management: use hasattr to check before calling PlugOut
		if hasattr(self, "ComponentBinder") and self.ComponentBinder: self.ComponentBinder.PlugOut()
		if hasattr(self, "ResourceBinder") and self.ResourceBinder: self.ResourceBinder.PlugOut()
		self.enable_routing_logic = False
		if hasattr(self, "NonSaslAuthenticator") and self.NonSaslAuthenticator: self.NonSaslAuthenticator.PlugOut()
		if hasattr(self, "SaslAuthenticator") and self.SaslAuthenticator: self.SaslAuthenticator.PlugOut()
		if hasattr(self, "TLS") and self.TLS: self.TLS.PlugOut()

		if should_save_dispatcher_handlers and hasattr(self, "Dispatcher") and self.Dispatcher:
			self.Dispatcher.PlugOut()

		# Proxy and socket plugins
		if hasattr(self, "HTTPProxySocket") and self.HTTPProxySocket: self.HTTPProxySocket.PlugOut()
		if hasattr(self, "TCPSocket") and self.TCPSocket: self.TCPSocket.PlugOut()

		# Re-establish connection and authentication
		# _server_host, _proxy_settings, _username, _password, _resource are assumed to be stored from previous connect/auth
		if not self.connect(server=(self._server_host, self.server_port), proxy=self._proxy_settings): # connect needs to store these
			return None
		if not self.auth(self._username, self._password, self._resource_str): # auth needs to store these
			return None

		if hasattr(self, "Dispatcher") and self.Dispatcher:
			self.Dispatcher.restoreHandlers(handlers_to_save)
		return self.connection_status

	def connect(self, server_address_tuple=None, proxy_settings=None, force_ssl_tls=None, use_srv_records=False): # Renamed params
		"""
		Make a tcp/ip connection, protect it with tls/ssl if possible and start XMPP stream.
		Returns None or "tcp" or "tls", depending on the result.
		"""
		if not server_address_tuple:
			server_address_tuple = (self.server_host, self.server_port)

		# Store for potential reconnect
		self._server_host = server_address_tuple[0] # Assuming server_address_tuple is (host, port)
		self._proxy_settings = proxy_settings

		socket_handler = None
		if proxy_settings:
			socket_handler = transports.HTTPProxyConnector(proxy_settings, server_address_tuple, use_srv_records) # Renamed class, params
		else:
			socket_handler = transports.TCPConnector(server_address_tuple, use_srv_records) # Renamed class, params

		connection_established = socket_handler.PlugIn(self) # self is passed as the client/component instance

		if not connection_established:
			socket_handler.PlugOut()
			return None

		self.connection_status = "tcp"

		# SSL/TLS handling (original logic was a bit mixed)
		# force_ssl_tls: None (auto), True (force), False (disable)
		port_for_ssl_check = self.Connection.getport() # Assuming self.Connection is set by socket_handler.PlugIn

		if force_ssl_tls or (force_ssl_tls is None and port_for_ssl_check in (5223, 443)):
			try:
				# The TLS plugin should handle the actual TLS negotiation.
				tls_plugin = transports.TLSConnection(self) # Pass client instance
				tls_plugin.PlugIn(self, now=True) # now=True implies immediate attempt
				if tls_plugin.tls_established: # Check a flag set by the TLS plugin
					self.connection_status = "ssl" # Or "tls" depending on what TLSConnection sets
				else: # TLS negotiation failed or not supported by server
				    if force_ssl_tls: # If forced, then this is a failure
				        self.DEBUG(self.debug_scope_name, "Forced TLS/SSL connection failed.", "error")
				        socket_handler.PlugOut() # Clean up socket
				        return None
				    # If auto and failed, continue with non-TLS (already "tcp")
			except transports.socket.sslerror as e: # More specific error
				self.DEBUG(self.debug_scope_name, f"SSL/TLS error: {e}", "error")
				socket_handler.PlugOut()
				return None
			except Exception as e: # Catch other potential errors during TLS plugin
				self.DEBUG(self.debug_scope_name, f"Error during TLS/SSL setup: {e}", "error")
				socket_handler.PlugOut()
				return None

		dispatcher.Dispatcher().PlugIn(self) # Initialize dispatcher after connection is set up

		# Wait for stream header
		timeout_counter = 100
		while self.Dispatcher.Stream._document_attrs is None and timeout_counter > 0:
			if not self.Process(1): # Process should return False on critical error/disconnect
				return None
			timeout_counter -=1
		if self.Dispatcher.Stream._document_attrs is None:
		    self.DEBUG(self.debug_scope_name, "Timeout waiting for stream header.", "error")
		    return None

		# Wait for stream features if XMPP 1.0
		if "version" in self.Dispatcher.Stream._document_attrs and self.Dispatcher.Stream._document_attrs["version"] == "1.0":
			timeout_counter = 100
			while not self.Dispatcher.Stream.features and timeout_counter > 0:
				if not self.Process(1): return None
				timeout_counter -= 1
			if not self.Dispatcher.Stream.features:
			    self.DEBUG(self.debug_scope_name, "Timeout waiting for stream features.", "error")
			    return None

		return self.connection_status

class XMPPClient(BaseClient): # Renamed Client, CommonClient
	"""
	Example XMPP client class.
	"""
	def connect(self, server_address_tuple=None, proxy_settings=None, force_ssl_tls=None, use_srv_records=True): # Renamed params
		"""
		Connect to jabber server.
		"""
		# Call BaseClient.connect which establishes basic TCP and potentially SSL (if port is 5223/443 or force_ssl_tls is True)
		initial_connection_status = BaseClient.connect(self, server_address_tuple, proxy_settings, force_ssl_tls, use_srv_records)

		if not initial_connection_status: # Base connection failed
			return None

		# If force_ssl_tls was False, or if it was None and not an SSL port, we don't attempt STARTTLS.
		if force_ssl_tls is False:
			return self.connection_status

		# If already SSL (e.g. port 5223), STARTTLS is not applicable.
		if self.connection_status == "ssl":
			return self.connection_status

		# At this point, connection is "tcp". Check for STARTTLS feature.
		# The Dispatcher and Stream features should be populated by BaseClient.connect
		if not hasattr(self, "Dispatcher") or not self.Dispatcher.Stream.features:
			self.DEBUG(self.debug_scope_name, "No stream features found, cannot initiate STARTTLS.", "warn")
			return self.connection_status # Return current status ("tcp")

		tls_plugin = transports.TLSConnection(self) # Pass client instance
		tls_plugin.PlugIn(self) # Register feature handler for STARTTLS

		# Process messages to allow feature negotiation for STARTTLS
		# The TLS plugin's feature handler will initiate STARTTLS if available.
		timeout_counter = 100 # Wait for STARTTLS negotiation
		# TLS.starttls_initiated and TLS.tls_established would be flags set by the TLS plugin
		while hasattr(self, "TLS") and self.TLS and not self.TLS.tls_established and self.TLS.starttls_status != "failed" and timeout_counter > 0:
			if not self.Process(1): # If Process returns False, connection might have dropped
				self.DEBUG(self.debug_scope_name, "Connection lost during STARTTLS negotiation.", "error")
				return None # Or self.connection_status which would be "tcp"
			timeout_counter -= 1

		if hasattr(self, "TLS") and self.TLS and self.TLS.tls_established:
			self.connection_status = "tls" # Update status after successful STARTTLS
		elif hasattr(self, "TLS") and self.TLS and self.TLS.starttls_status == "failed":
			self.event("tls_failed") # Fire event if TLS explicitly failed
			# Continue with "tcp" if STARTTLS failed but was optional.
			# If STARTTLS was mandatory by server policy (not checked here), this might be an issue.
		elif timeout_counter == 0:
			self.DEBUG(self.debug_scope_name, "Timeout waiting for STARTTLS.", "warn")

		return self.connection_status


	def auth(self, username_str, password_str, resource_str="", use_sasl=True): # Renamed user, password, resource, sasl
		"""
		Authenticate connnection and bind resource.
		"""
		self._username = username_str
		self._password = password_str
		self._resource_str = resource_str

		# Wait for stream features if not already present (e.g., after STARTTLS)
		timeout_counter = 100
		while not (hasattr(self, "Dispatcher") and self.Dispatcher.Stream.features) and timeout_counter > 0:
			if not self.Process(1): return None # Connection lost
			timeout_counter -=1
		if not (hasattr(self, "Dispatcher") and self.Dispatcher.Stream.features):
		    self.DEBUG(self.debug_scope_name, "Stream features not available for authentication.", "error")
		    return None

		if use_sasl:
			sasl_authenticator = auth.SaslAuthenticator(username_str, password_str) # Use new class name
			sasl_authenticator.PlugIn(self) # This will check features and register handlers
			sasl_authenticator.auth() # This will initiate SASL if features allow

			timeout_counter = 200 # Increased timeout for SASL potentially multiple steps
			while sasl_authenticator.sasl_status == "in-process" and timeout_counter > 0:
				if not self.Process(1): return None # Connection lost
				timeout_counter -=1

			if sasl_authenticator.sasl_status == "success":
				resource_binder = auth.ResourceBinder() # Use new class name
				resource_binder.PlugIn(self)
				# Wait for bind features to be processed by ResourceBinder
				bind_timeout_counter = 100
				while resource_binder.binding_status is None and bind_timeout_counter > 0:
				    if not self.Process(1): return None
				    bind_timeout_counter -= 1

				if resource_binder.binding_status == "failure" or resource_binder.binding_status is None:
				    self.DEBUG(self.debug_scope_name, "Resource binding not offered or failed after SASL.", "error")
				    sasl_authenticator.PlugOut()
				    return None

				bind_result = resource_binder.bind_resource(resource_str) # Use new name
				if bind_result and "ok" in bind_result: # e.g. "ok" or "bind_ok_session_failed"
					self.connection_status += "+sasl"
					return "sasl_bind_ok" # More descriptive success
				else:
				    self.DEBUG(self.debug_scope_name, f"SASL OK, but Resource Binding failed: {bind_result}", "error")
			elif sasl_authenticator.sasl_status == "not-supported" and not resource_str: # Fallback to NonSASL if SASL not supported by server AND no resource given for NonSASL client auth
			    self.DEBUG(self.debug_scope_name, "SASL not supported by server, attempting Non-SASL (but resource is required for client Non-SASL).", "warn")
			    # NonSASL client auth requires a resource. If not provided, it's an issue.
			    # This path is tricky, as NonSASL for clients is different from components.
			    # The original code might have implicitly handled this by resource defaulting.
			    # For clarity, if resource_str is empty here for NonSASL client auth, it should likely fail or use a default.
			    # Let's assume for now if resource_str is empty, NonSASL client auth isn't viable.
			    if not resource_str:
			        self.DEBUG(self.debug_scope_name, "Non-SASL client auth requires a resource. None provided.", "error")
			        sasl_authenticator.PlugOut()
			        return None

			# Fallback to NonSASL if SASL failed or not supported (and resource is available)
			if sasl_authenticator.sasl_status != "success": # Covers "failure" and "not-supported" if resource is present
				if not resource_str: resource_str = "xmpppy" # Default resource for NonSASL
				non_sasl_authenticator = auth.NonSaslAuthenticator(username_str, password_str, resource_str) # Use new class name
				if non_sasl_authenticator.PlugIn(self): # This calls plugin() which does the auth
					self.connection_status += "+old_auth"
					if hasattr(self,"SASL") and self.SASL: self.SASL.PlugOut() # Clean up SASL if it was attempted
					return "old_auth"

			if hasattr(self,"SASL") and self.SASL: self.SASL.PlugOut() # Ensure SASL is plugged out if not successful
			return None # Auth failed overall

		else: # Not using SASL, try NonSASL directly
			if not resource_str: resource_str = "xmpppy" # Default resource
			non_sasl_authenticator = auth.NonSaslAuthenticator(username_str, password_str, resource_str)
			if non_sasl_authenticator.PlugIn(self):
				self.connection_status += "+old_auth"
				return "old_auth"
			return None


	def get_roster(self): # Renamed getRoster
		"""
		Return the Roster instance, previously plugging it in and
		requesting roster from server if needed.
		"""
		if not hasattr(self, "RosterManager"): # Assuming Roster class is RosterManager
			roster_manager_instance = roster.RosterManager() # Use new name
			roster_manager_instance.PlugIn(self)
			self.RosterManager = roster_manager_instance # Store it
		# getRoster method of RosterManager should fetch if not already fetched
		return self.RosterManager.get_roster_nodes() # Assuming RosterManager has get_roster_nodes

	def send_initial_presence(self, request_roster_on_presence=True): # Renamed sendInitPresence, requestRoster
		"""
		Send roster request and initial <presence/>.
		"""
		self.send_presence(request_roster=request_roster_on_presence) # Use new name

	def send_presence(self, to_jid=None, presence_type=None, request_roster=False): # Renamed sendPresence, jid, typ, requestRoster
		"""
		Send some specific presence state.
		"""
		if request_roster:
			if not hasattr(self, "RosterManager"):
				roster_manager_instance = roster.RosterManager()
				roster_manager_instance.PlugIn(self)
				self.RosterManager = roster_manager_instance
			self.RosterManager.request_roster() # Explicitly request roster
		# Presence class will be renamed
		self.send(Presence(to_jid=to_jid, stanza_type=presence_type))


class XMPPComponent(BaseClient): # Renamed Component, CommonClient
	"""
	XMPP Component class.
	"""
	def __init__(self, component_jid_or_domain, server_port=5347, server_type=None, debug_scope_list=None, additional_domains=None, use_sasl_bool=False, enable_routing=False, use_xcp=False): # Renamed params
		BaseClient.__init__(self, component_jid_or_domain, server_port=server_port, debug_scope_list=debug_scope_list)
		self.server_type = server_type
		self.use_sasl = use_sasl_bool # Renamed sasl
		self.enable_binding = enable_routing # Renamed bind to enable_binding, route to enable_routing
		self.use_xcp_features = use_xcp # Renamed xcp
		if additional_domains:
			self.additional_domains = additional_domains
		else:
			self.additional_domains = [component_jid_or_domain] # If only one domain, it's the primary one

	def connect(self, server_address_tuple=None, proxy_settings=None): # Renamed params
		"""
		Connects the component to the server.
		"""
		# Component connections typically don't use SRV or SSL/TLS in the same way clients do.
		# The `secure` parameter from Client.connect is not present here.
		if BaseClient.connect(self, server_address_tuple=server_address_tuple, proxy_settings=proxy_settings, force_ssl_tls=False, use_srv_records=False): # force_ssl_tls=False for components unless specified
			if self.connection_status and \
			   (self.server_type == "jabberd2" or (not self.server_type and self.Dispatcher.Stream.features is not None)) and \
			   (not self.use_xcp_features):
				self.default_stanza_namespace = auth.NS_CLIENT # Default to client namespace for stanzas after connect for some servers
				self.Dispatcher.RegisterNamespace(self.default_stanza_namespace)
				# Re-register protocols if namespace changes. This assumes Dispatcher handles this.
				self.Dispatcher.RegisterProtocol("iq", Iq) # Iq will be IqStanza
				self.Dispatcher.RegisterProtocol("message", Message) # Message will be MessageStanza
				self.Dispatcher.RegisterProtocol("presence", Presence) # Presence will be PresenceStanza
			return self.connection_status
		return None


	def _perform_component_bind(self, sasl_negotiated_bool): # Renamed dobind, sasl
		# This has to be done before binding, because we can receive a route stanza before binding finishes
		self.enable_routing_logic = self.enable_routing # Use the instance attribute
		if self.enable_binding: # Use new name
			for domain_str in self.additional_domains: # Renamed domains
				binder_plugin = auth.ComponentBinder(sasl_negotiated_bool) # Use new class name
				binder_plugin.PlugIn(self)
				# Wait for binding status to be ready (e.g. features processed if applicable)
				timeout_counter = 100
				while binder_plugin.binding_status is None and timeout_counter > 0:
					if not self.Process(1): return None # Connection lost
					timeout_counter -=1

				if binder_plugin.binding_status == "failure" or binder_plugin.binding_status is None:
				    self.DEBUG(self.debug_scope_name, f"Component binding not offered or failed for {domain_str}", "error")
				    binder_plugin.PlugOut()
				    return None

				bind_attempt_result = binder_plugin.bind_component(domain_str) # Use new name
				binder_plugin.PlugOut() # Clean up plugin after attempt
				if not bind_attempt_result or bind_attempt_result == "failure" or bind_attempt_result == "timeout":
					return None # Binding failed for this domain
			return "ok" # All domains bound successfully
		return "ok" # Binding not enabled, so considered successful in this context

	def auth(self, component_name_str, component_password_str): # Renamed name, password, removed dup
		"""
		Authenticate component.
		"""
		self._username = component_name_str # Store for potential re-auth logic
		self._password = component_password_str
		self._resource_str = "" # Components don't have resources in the client sense

		try:
			if self.use_sasl:
				sasl_auth_instance = auth.SaslAuthenticator(component_name_str, component_password_str) # Use new name
				sasl_auth_instance.PlugIn(self)
				sasl_auth_instance.auth() # Attempt SASL

				timeout_counter = 100
				while sasl_auth_instance.sasl_status == "in-process" and timeout_counter > 0:
					if not self.Process(1): return None # Connection lost
					timeout_counter -=1

				if sasl_auth_instance.sasl_status == "success":
					if self._perform_component_bind(sasl_negotiated_bool=True): # Use new name
						self.connection_status += "+sasl_bind" # More specific status
						return "sasl_component_auth_ok"
					else:
						self.DEBUG(self.debug_scope_name, "SASL auth OK, but component binding failed.", "error")
						return None
				elif sasl_auth_instance.sasl_status == "not-supported":
				    self.DEBUG(self.debug_scope_name, "SASL not supported by server, trying Non-SASL component handshake.", "warn")
				    # Fall through to NonSASL if SASL is not supported
				else: # SASL failed for other reasons
				    self.DEBUG(self.debug_scope_name, f"SASL authentication failed: {sasl_auth_instance.sasl_status}", "error")
				    return None

			# Non-SASL / Component Handshake (either as fallback or primary if use_sasl is false)
			non_sasl_auth_instance = auth.NonSaslAuthenticator(component_name_str, component_password_str, resource_str="") # Use new name
			auth_result = non_sasl_auth_instance.authenticate_as_component(self) # Use new name, pass self

			if auth_result == "ok":
				if self._perform_component_bind(sasl_negotiated_bool=False): # Use new name
					self.connection_status += "+component_handshake_bind"
					return "component_handshake_ok"
				else:
					self.DEBUG(self.debug_scope_name, "Component handshake OK, but binding failed.", "error")
					return None
			else:
				self.DEBUG(self.debug_scope_name, f"Component handshake authentication failed: {auth_result}", "error")
				return None

		except Exception as e:
			self.DEBUG(self.debug_scope_name, f"Failed to authenticate component {component_name_str}: {e}", "error")
			# Log the full exception for more details if possible
			self._debugger.show_formatted_message(self.debug_scope_name, f"Exception during auth: {e}", "error_exception")
			return None
		finally: # Ensure plugins are cleaned up if they were instantiated
		    if hasattr(self, "SaslAuthenticator") and self.SaslAuthenticator: self.SaslAuthenticator.PlugOut()
		    if hasattr(self, "NonSaslAuthenticator") and self.NonSaslAuthenticator: self.NonSaslAuthenticator.PlugOut()
		    if hasattr(self, "ComponentBinder") and self.ComponentBinder : self.ComponentBinder.PlugOut()
