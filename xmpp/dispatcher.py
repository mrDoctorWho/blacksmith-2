##   transports.py
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

# $Id: dispatcher.py, v1.43 2013/10/21 alkorgun Exp $

"""
Main xmpppy mechanism. Provides library with methods to assign different handlers
to different XMPP stanzas.
Contains one tunable attribute: DEFAULT_TIMEOUT (25 seconds by default). It defines time that
Dispatcher.send_and_wait_for_response method will wait for reply stanza before giving up.
"""

from . import simplexml # simplexml.py will need renaming for its classes too
import sys
import time

from .plugin import PlugIn # PlugIn class name is fine
from .protocol import Iq, Presence, Message, Protocol, NodeProcessed, ErrorStanza, StreamError, \
                      NS_STREAMS, NS_CLIENT, NS_COMPONENT_ACCEPT, \
                      ERR_FEATURE_NOT_IMPLEMENTED, ERR_UNDEFINED_CONDITION, \
                      stream_exceptions # Using renamed classes from protocol.py
from xml.parsers.expat import ExpatError

DEFAULT_TIMEOUT = 25 # Renamed DefaultTimeout
STANZA_ID_COUNTER = 0 # Renamed ID

DEBUG_SCOPE_DISPATCHER = "dispatcher" # Renamed DBG_LINE

class XMPPDispatcher(PlugIn): # Renamed Dispatcher
	"""
	Ancestor of PlugIn class. Handles XMPP stream, i.e. aware of stream headers.
	Can be plugged out/in to restart these headers (used for SASL f.e.).
	"""
	def __init__(self):
		PlugIn.__init__(self)
		self.handlers = {} # Stores registered handlers {xmlns: {tag_name: {type_ns_combo: [callbacks]}}}
		self._expected_responses = {} # Renamed _expected, stores {id: callback_or_stanza}
		self._default_stanza_handler = None # Renamed _defaultHandler
		self._pending_exceptions = []
		self._event_callback = None # Renamed _eventHandler
		self._cycle_callbacks = [] # Renamed _cycleHandlers
		self._exported_methods = [ # These are methods exposed by the plugin system
			self.process_stream_data,
			self.register_handler,
			# self.register_default_handler, # Original was commented out
			self.register_event_handler,
			self.unregister_cycle_handler,
			self.register_cycle_handler,
			self.register_handler_once,
			self.unregister_handler,
			self.register_stanza_protocol,
			self.wait_for_response,
			self.send_and_wait_for_response,
			self.send,
			self.send_and_call_for_response,
			self.disconnect,
			self.iter_process # Renamed iter
		]

	def dump_handlers(self): # Renamed dumpHandlers
		"""
		Return set of user-registered callbacks in it's internal format.
		Used within the library to carry user handlers set over Dispatcher replugins.
		"""
		return self.handlers

	def restore_handlers(self, handlers_dict): # Renamed restoreHandlers, handlers
		"""
		Restores user-registered callbacks structure from dump previously obtained via dump_handlers.
		"""
		self.handlers = handlers_dict

	def _initialize_dispatcher(self): # Renamed _init
		"""
		Registers default namespaces/protocols/handlers. Used internally.
		"""
		self.register_namespace("unknown")
		self.register_namespace(NS_STREAMS)
		self.register_namespace(self._owner.default_stanza_namespace) # Assuming _owner.default_stanza_namespace is set
		self.register_stanza_protocol("iq", Iq) # Iq from protocol.py
		self.register_stanza_protocol("presence", Presence) # Presence from protocol.py
		self.register_stanza_protocol("message", Message) # Message from protocol.py
		# self.register_default_handler(self.default_return_stanza_handler) # Original was commented
		self.register_handler("error", self.handle_stream_error, xmlns=NS_STREAMS)

	def plugin(self, owner_instance): # Renamed owner
		"""
		Plug the Dispatcher instance into Client class instance and send initial stream header. Used internally.
		"""
		# _owner is set by PlugIn's plugin method
		self._initialize_dispatcher()
		# Find the original send method of the owner if it exists (for raw send)
		self._raw_send_function = None # Renamed _owner_send
		if hasattr(self._owner, '_old_owners_methods'): # Check if this list exists
		    for method_obj in self._owner._old_owners_methods: # Renamed method
		        if method_obj.__name__ == "send": # Original "send" of the client/component
		            self._raw_send_function = method_obj
		            break
		if not self._raw_send_function:
		    # Fallback if _old_owners_methods isn't there or send isn't found
		    # This assumes the owner has a 'send_xml_string' or similar raw send method.
		    # This part is crucial and depends on how the owner (Client/Component) is structured.
		    # For now, let's assume the owner has a `_send_raw_xml` method.
		    # This might need adjustment based on actual owner capabilities.
		    if hasattr(self._owner, '_send_raw_xml'):
		        self._raw_send_function = self._owner._send_raw_xml
		    else:
		        # This is a critical dependency. If not found, sending the stream header will fail.
		        raise AttributeError("Dispatcher's owner does not have a suitable raw send method.")


		self._owner.lastErrNode = None # These seem to be error state vars on the owner
		self._owner.lastErr = None
		self._owner.lastErrCode = None
		self.initialize_stream() # Renamed StreamInit

	def plugout(self):
		"""
		Prepares instance to be destructed.
		"""
		if hasattr(self, 'xml_stream_parser') and self.xml_stream_parser: # Renamed Stream
			self.xml_stream_parser.dispatch = None
			self.xml_stream_parser.DEBUG = None # DEBUG should be from DebugModule
			self.xml_stream_parser.features = None
			self.xml_stream_parser.destroy()

	def initialize_stream(self): # Renamed StreamInit
		"""
		Send an initial stream header.
		"""
		self.xml_stream_parser = simplexml.NodeBuilder() # Renamed Stream
		self.xml_stream_parser._dispatch_depth = 2
		self.xml_stream_parser.dispatch = self.dispatch_stanza # Renamed dispatch
		self.xml_stream_parser.stream_header_received = self._check_stream_start
		# Assuming self._owner._debugger exists and is a Debugger instance
		if hasattr(self._owner, '_debugger') and self._owner._debugger:
		    # self._owner.debug_flags.append(simplexml.DEBUG_SCOPE_NODEBUILDER) # This was likely incorrect
		    # Instead, pass the debugger instance to the NodeBuilder if it uses it
		    self.xml_stream_parser.DEBUG = self._owner._debugger.show_formatted_message # Pass the show method
		else: # Fallback if no debugger on owner
		    self.xml_stream_parser.DEBUG = lambda *args, **kwargs: None


		self.xml_stream_parser.features = None
		self._stream_header_node = Node("stream:stream") # Renamed _metastream
		self._stream_header_node.setNamespace(self._owner.default_stanza_namespace) # Use correct attribute
		self._stream_header_node.setAttr("version", "1.0")
		self._stream_header_node.setAttr("xmlns:stream", NS_STREAMS)
		self._stream_header_node.setAttr("to", self._owner.server_host) # Use correct attribute

		# The raw send function must be available here
		if not self._raw_send_function:
		    raise RuntimeError("Raw send function not initialized for Dispatcher.")
		self._raw_send_function("<?xml version=\"1.0\"?>%s>" % str(self._stream_header_node)[:-2])


	def _check_stream_start(self, namespace_uri, tag_name, attributes_dict): # Renamed ns, tag, attrs
		if namespace_uri != NS_STREAMS or tag_name != "stream":
			raise ValueError(f"Incorrect stream start: ({tag_name},{namespace_uri}). Terminating.")

	def process_stream_data(self, timeout_seconds=8): # Renamed Process, timeout
		"""
		Check incoming stream for data waiting. If "timeout_seconds" is positive - block for max this time.
		Returns: length of processed data, "0" (str) if no data but alive, or 0 (int) if disconnected.
		"""
		for cycle_callback_func in self._cycle_callbacks: # Renamed handler
			cycle_callback_func(self) # Pass self (dispatcher instance)

		if self._pending_exceptions:
			exc_info_tuple = self._pending_exceptions.pop(0) # FIFO for exceptions
			raise exc_info_tuple[0](exc_info_tuple[1]).with_traceback(exc_info_tuple[2])

		if self._owner.Connection.pending_data(timeout_seconds): # Assuming Connection is set on owner
			try:
				received_data = self._owner.Connection.receive() # Renamed data
			except IOError: # Could be socket error
				self._owner._handle_disconnection() # Call owner's disconnect handler
				return 0 # Indicate disconnection

			if not received_data: # Connection closed by peer
			    self._owner._handle_disconnection()
			    return 0

			try:
				self.xml_stream_parser.Parse(received_data) # Renamed Stream
			except ExpatError as e:
				# Handle XML parsing errors, potentially raise a stream error
				self.DEBUG(DEBUG_SCOPE_DISPATCHER, f"XML ExpatError: {e}", "error")
				# Depending on policy, might raise specific XMPP stream error here
				# For now, let's assume it might be handled by subsequent pending exceptions or error handlers
				self._pending_exceptions.append((XmlNotWellFormedError, str(e), sys.exc_info()[2]))

			if self._pending_exceptions: # Check again after parse
				exc_info_tuple = self._pending_exceptions.pop(0)
				raise exc_info_tuple[0](exc_info_tuple[1]).with_traceback(exc_info_tuple[2])
			return len(received_data)
		return "0" # No data, but connection alive

	def iter_process(self, timeout_seconds=8): # Added iter_process as an alias for process_stream_data
	    return self.process_stream_data(timeout_seconds)


	def register_namespace(self, namespace_uri, debug_order="info"): # Renamed RegisterNamespace, xmlns, order
		"""
		Creates internal structures for newly registered namespace.
		"""
		self.DEBUG(f"Registering namespace \"{namespace_uri}\"", debug_order)
		self.handlers[namespace_uri] = {}
		self.register_stanza_protocol("unknown", Stanza, xmlns=namespace_uri) # Use renamed Stanza (Protocol)
		self.register_stanza_protocol("default", Stanza, xmlns=namespace_uri) # Use renamed Stanza (Protocol)

	def register_stanza_protocol(self, tag_name_str, protocol_class, xmlns=None, debug_order="info"): # Renamed RegisterProtocol, tag_name, Proto, order
		"""
		Used to declare some top-level stanza name to dispatcher.
		"""
		if not xmlns:
			xmlns = self._owner.default_stanza_namespace # Use correct attribute
		self.DEBUG(f"Registering protocol \"{tag_name_str}\" as {protocol_class.__name__}({xmlns})", debug_order)
		if xmlns not in self.handlers: self.register_namespace(xmlns) # Ensure namespace exists
		self.handlers[xmlns][tag_name_str] = {"type": protocol_class, "default": []}

	def register_namespace_handler(self, namespace_uri, handler_func, stanza_type_str="", child_ns_str="", make_first=False, is_system_handler=False): # Renamed params
		"""
		Register handler for processing all stanzas for specified namespace.
		"""
		self.register_handler("default", handler_func, stanza_type_str, child_ns_str, namespace_uri, make_first, is_system_handler)

	def register_handler(self, stanza_name_str, handler_func, stanza_type_str="", child_ns_str="", xmlns_uri=None, make_first=False, is_system_handler=False): # Renamed params
		"""Register user callback as stanzas handler."""
		if not xmlns_uri:
			xmlns_uri = self._owner.default_stanza_namespace
		self.DEBUG(f"Registering handler {handler_func.__name__} for \"{stanza_name_str}\" type->{stanza_type_str or 'any'} ns->{child_ns_str or 'any'}({xmlns_uri})", "info")

		if xmlns_uri not in self.handlers:
			self.register_namespace(xmlns_uri, "warn")
		if stanza_name_str not in self.handlers[xmlns_uri]:
			self.register_stanza_protocol(stanza_name_str, Stanza, xmlns_uri, "warn") # Default to base Stanza

		type_ns_combo_key = (stanza_type_str or "") + (child_ns_str or "") # Ensure consistent key
		if not type_ns_combo_key: type_ns_combo_key = "default" # For handlers that match any type/childNS

		if type_ns_combo_key not in self.handlers[xmlns_uri][stanza_name_str]:
			self.handlers[xmlns_uri][stanza_name_str][type_ns_combo_key] = []

		handler_entry = {"func": handler_func, "system": is_system_handler}
		if make_first:
			self.handlers[xmlns_uri][stanza_name_str][type_ns_combo_key].insert(0, handler_entry)
		else:
			self.handlers[xmlns_uri][stanza_name_str][type_ns_combo_key].append(handler_entry)

	def register_handler_once(self, stanza_name_str, handler_func, stanza_type_str="", child_ns_str="", xmlns_uri=None, make_first=False, is_system_handler=False): # Renamed params
		""" Unregister handler after first call (TODO: implement actual once logic if needed beyond simple register). """
		# Current implementation just registers it. "Once" behavior needs more logic.
		self.register_handler(stanza_name_str, handler_func, stanza_type_str, child_ns_str, xmlns_uri, make_first, is_system_handler)

	def unregister_handler(self, stanza_name_str, handler_func, stanza_type_str="", child_ns_str="", xmlns_uri=None): # Renamed params
		""" Unregister handler. """
		if not xmlns_uri:
			xmlns_uri = self._owner.default_stanza_namespace
		if xmlns_uri not in self.handlers or stanza_name_str not in self.handlers[xmlns_uri]:
			return

		type_ns_combo_key = (stanza_type_str or "") + (child_ns_str or "")
		if not type_ns_combo_key: type_ns_combo_key = "default"

		if type_ns_combo_key in self.handlers[xmlns_uri][stanza_name_str]:
			handlers_list = self.handlers[xmlns_uri][stanza_name_str][type_ns_combo_key]
			self.handlers[xmlns_uri][stanza_name_str][type_ns_combo_key] = [h for h in handlers_list if h["func"] != handler_func]

	def register_default_handler(self, handler_func): # Renamed RegisterDefaultHandler, handler
		""" Specify the handler that will be used if no NodeProcessed exception was raised. """
		self._default_stanza_handler = handler_func

	def register_event_handler(self, handler_func): # Renamed RegisterEventHandler, handler
		""" Register handler that will process events. """
		self._event_callback = handler_func

	def default_return_stanza_handler(self, dispatcher_instance, stanza_obj): # Renamed returnStanzaHandler, conn, stanza
		""" Return stanza back to the sender with <feature-not-implemennted/> error set. """
		if stanza_obj.get_type() in ("get", "set"): # Use new name
			dispatcher_instance.send(ErrorStanza(stanza_obj, ERR_FEATURE_NOT_IMPLEMENTED)) # Use new name

	def handle_stream_error(self, dispatcher_instance, error_node): # Renamed streamErrorHandler, conn, error
		condition_name = "unknown-stream-error" # Default
		error_text = error_node.getData() # Text from <stream:error><text>...</text></stream:error> or the condition itself

		for child_node in error_node.getChildren(): # Renamed tag
			if child_node.getNamespace() == NS_XMPP_STREAMS: # Specific stream error conditions
				if child_node.getName() == "text":
					error_text = child_node.getData()
				else: # This is the error condition element
					condition_name = child_node.getName()

		exception_class = STREAM_ERROR_EXCEPTION_MAP.get(condition_name, StreamError) # Use new map
		raise exception_class((condition_name, error_text))

	def register_cycle_handler(self, handler_func): # Renamed RegisterCycleHandler, handler
		""" Register handler that will be called on every process_stream_data() call. """
		if handler_func not in self._cycle_callbacks:
			self._cycle_callbacks.append(handler_func)

	def unregister_cycle_handler(self, handler_func): # Renamed UnregisterCycleHandler, handler
		""" Unregister handler that is called on every process_stream_data() call. """
		if handler_func in self._cycle_callbacks:
			self._cycle_callbacks.remove(handler_func)

	def dispatch_event(self, event_realm_str, event_name_str, event_data): # Renamed Event, realm, event, data
		""" Raise some event. """
		if self._event_callback:
			self._event_callback(event_realm_str, event_name_str, event_data)

	def dispatch_stanza(self, stanza_obj, current_session=None, is_direct_dispatch=False): # Renamed dispatch, stanza, session, direct
		"""
		Main procedure that performs XMPP stanza recognition and calling appropriate handlers for it.
		Called internally by the XML stream parser.
		"""
		if not current_session:
			current_session = self # 'self' is the dispatcher instance

		current_session.xml_stream_parser._mini_dom = None # Reset internal state of parser

		stanza_name = stanza_obj.getName()

		# Handle <route/> wrapper if routing is enabled for this dispatcher (component context)
		if not is_direct_dispatch and hasattr(self._owner, 'enable_routing_logic') and self._owner.enable_routing_logic:
			if stanza_name == "route":
				if stanza_obj.getAttr("error") is None: # Not an error route
					children_nodes = stanza_obj.getChildren()
					if len(children_nodes) == 1:
						stanza_obj = children_nodes[0] # Unwrap the actual stanza
						stanza_name = stanza_obj.getName()
					else: # Multiple stanzas inside route, dispatch each
						for child_node in children_nodes:
							self.dispatch_stanza(child_node, current_session, is_direct_dispatch=True)
						return # Processed all children
				# else: it's a route error, let it be dispatched as 'route'
			elif stanza_name == "presence":
				return # Components might ignore direct presence unless specifically handled
			elif stanza_name in ("features", "bind"): # Stream-level features, pass through
				pass
			else: # Unexpected stanza when routing is on
				raise UnsupportedStanzaType(f"Unexpected stanza '{stanza_name}' when routing is enabled.")

		if stanza_name == "features": # Handle stream features
			current_session.xml_stream_parser.features = stanza_obj
			# Note: Feature handlers (SASL, Bind, TLS) are registered for NS_STREAMS and "features" tag
			# This dispatch call will trigger them.

		stanza_xmlns = stanza_obj.getNamespace()
		if stanza_xmlns not in self.handlers:
			self.DEBUG(f"Unknown namespace: {stanza_xmlns}", "warn")
			stanza_xmlns = "unknown" # Fallback to 'unknown' namespace handlers

		if stanza_name not in self.handlers[stanza_xmlns]:
			self.DEBUG(f"Unknown stanza name: {stanza_name} in namespace {stanza_xmlns}", "warn")
			# Fallback to 'unknown' protocol in the current namespace, then 'unknown' in default if not found
			if "unknown" in self.handlers[stanza_xmlns]:
			    stanza_name = "unknown"
			elif xmlns_uri != self._owner.default_stanza_namespace and "unknown" in self.handlers.get(self._owner.default_stanza_namespace, {}):
			    stanza_xmlns = self._owner.default_stanza_namespace
			    stanza_name = "unknown"
			else: # Truly unknown
			    if self._default_stanza_handler:
			        self._default_stanza_handler(current_session, stanza_obj)
			    return
		else:
			self.DEBUG(f"Got {stanza_xmlns}/{stanza_name} stanza", "ok")

		# Convert Node to specific Protocol subclass if registered
		protocol_class_for_stanza = self.handlers[stanza_xmlns][stanza_name]["type"]
		if not isinstance(stanza_obj, protocol_class_for_stanza): # Check if it's already the right type
			stanza_obj = protocol_class_for_stanza(node=stanza_obj)

		stanza_type_attr = stanza_obj.get_type()
		if not stanza_type_attr: stanza_type_attr = "" # Normalize for key lookup

		stanza_child_namespaces = stanza_obj.get_child_namespaces() # Renamed getProperties
		stanza_id_attr = stanza_obj.get_id() # Renamed getID

		current_session.DEBUG(f"Dispatching {stanza_name} stanza with type->{stanza_type_attr or 'None'} props->{stanza_child_namespaces} id->{stanza_id_attr}", "ok")

		# Build list of matching handler categories
		handler_keys_to_try = ["default"]
		if stanza_type_attr in self.handlers[stanza_xmlns][stanza_name]:
			handler_keys_to_try.append(stanza_type_attr)
		for child_ns in stanza_child_namespaces:
			if child_ns in self.handlers[stanza_xmlns][stanza_name]:
				handler_keys_to_try.append(child_ns)
			if stanza_type_attr and (stanza_type_attr + child_ns) in self.handlers[stanza_xmlns][stanza_name]:
				handler_keys_to_try.append(stanza_type_attr + child_ns)

		# Consolidate all handlers to call
		final_handler_chain = [] # Renamed chain
		# Start with the most generic handlers for the namespace (if any for "default" tag)
		if "default" in self.handlers[stanza_xmlns].get("default", {}):
		    final_handler_chain.extend(self.handlers[stanza_xmlns]["default"]["default"])

		for key_str in handler_keys_to_try: # Renamed key
			if key_str and key_str in self.handlers[stanza_xmlns][stanza_name]:
				final_handler_chain.extend(self.handlers[stanza_xmlns][stanza_name][key_str])

		# Deduplicate handlers while preserving order (somewhat, Python dicts are ordered in 3.7+)
		# A simple list comprehension with a seen set is better for unique ordered handlers
		seen_handlers = set()
		unique_ordered_handlers = []
		for handler_entry in final_handler_chain:
		    if handler_entry["func"] not in seen_handlers:
		        unique_ordered_handlers.append(handler_entry)
		        seen_handlers.add(handler_entry["func"])
		final_handler_chain = unique_ordered_handlers

		user_handler_called = False # Renamed user, tracks if a non-system handler processed it

		# Handle expected responses first
		if stanza_id_attr and stanza_id_attr in current_session._expected_responses:
			user_handler_called = True # Mark as handled by expected response mechanism
			expected_item = current_session._expected_responses.pop(stanza_id_attr)
			if isinstance(expected_item, tuple): # It's a (callback, args) tuple
				callback_func, callback_args = expected_item # Renamed cb, args
				current_session.DEBUG(f"Expected stanza ID:{stanza_id_attr} arrived. Callback {callback_func.__name__}({callback_args}) found!", "ok")
				try:
					callback_func(current_session, stanza_obj, **callback_args)
				except NodeProcessed:
					pass # Callback indicated it fully handled the stanza
				except Exception: # Log other exceptions from callback
				    self._pending_exceptions.append(sys.exc_info())

			else: # It was a placeholder for a direct response
				current_session.DEBUG(f"Expected stanza ID:{stanza_id_attr} arrived!", "ok")
				current_session._expected_responses[stanza_id_attr] = stanza_obj # Store the actual stanza
		else: # Not an expected response, process general handlers
			user_handler_called = False
			for handler_entry in final_handler_chain:
				if not user_handler_called or handler_entry["system"]: # Call if not processed by user or if system handler
					try:
						handler_entry["func"](current_session, stanza_obj)
						user_handler_called = True # Mark that at least one user handler was called
					except NodeProcessed:
						user_handler_called = True # Stop further non-system handlers
						break
					except Exception:
						self._pending_exceptions.append(sys.exc_info()) # Store for main loop to raise

		if not user_handler_called and self._default_stanza_handler: # If no user handler processed it
			try:
				self._default_stanza_handler(current_session, stanza_obj)
			except Exception:
				self._pending_exceptions.append(sys.exc_info())


	def wait_for_response(self, stanza_id_str, timeout_duration=DEFAULT_TIMEOUT): # Renamed WaitForResponse, ID, timeout
		"""
		Block and wait until stanza with specific "id" attribute will come.
		"""
		self._expected_responses[stanza_id_str] = None # Placeholder
		abort_time = time.time() + timeout_duration
		self.DEBUG(f"Waiting for ID:{stanza_id_str} with timeout {timeout_duration}...", "wait")

		while stanza_id_str in self._expected_responses and self._expected_responses[stanza_id_str] is None:
			if not self.process_stream_data(0.04): # Returns 0 on disconnect
				self._owner.lastErr = "Disconnect" # lastErr/lastErrCode are on owner
				if stanza_id_str in self._expected_responses: del self._expected_responses[stanza_id_str] # Clean up
				return None
			if time.time() > abort_time:
				self._owner.lastErr = "Timeout"
				if stanza_id_str in self._expected_responses: del self._expected_responses[stanza_id_str] # Clean up
				return None

		response_stanza = self._expected_responses.pop(stanza_id_str, None) # Get and remove

		if response_stanza: # Check if we got a stanza
			error_code_val = response_stanza.get_error_code() # Use new name
			if error_code_val:
				self._owner.lastErrNode = response_stanza
				self._owner.lastErr = response_stanza.get_error_condition_node().getName() if response_stanza.get_error_condition_node() else "Unknown Error" # Use new name
				self._owner.lastErrCode = error_code_val
		return response_stanza

	def send_and_wait_for_response(self, stanza_obj, timeout_duration=DEFAULT_TIMEOUT): # Renamed SendAndWaitForResponse, stanza, timeout
		"""
		Put stanza on the wire and wait for recipient's response to it.
		"""
		return self.wait_for_response(self.send(stanza_obj), timeout_duration) # Use new name

	def send_and_call_for_response(self, stanza_obj, callback_func, callback_args_dict={}): # Renamed SendAndCallForResponse, stanza, func, args
		"""
		Put stanza on the wire and call back when recipient replies.
		"""
		self._expected_responses[self.send(stanza_obj)] = (callback_func, callback_args_dict)

	def send(self, stanza_obj_or_str): # Renamed stanza
		"""
		Serialize stanza and put it on the wire. Assign an unique ID to it before send if it's a Protocol instance.
		Returns assigned ID if applicable, otherwise None.
		"""
		global STANZA_ID_COUNTER # Use new name

		if isinstance(stanza_obj_or_str, str): # Raw XML string
		    if not self._raw_send_function: raise RuntimeError("Raw send function not available for sending string.")
		    self._raw_send_function(stanza_obj_or_str)
		    return None # No ID for raw strings

		# Assuming stanza_obj_or_str is a Stanza (or Protocol subclass) instance
		if not isinstance(stanza_obj_or_str, Stanza) and isinstance(stanza_obj_or_str, Node):
		    # If it's a basic Node, try to wrap it. This might be too generic.
		    # It's better if the caller creates the correct Stanza type.
		    # For now, assuming it's already a Stanza type or this path is not hit often.
		    pass


		current_id = stanza_obj_or_str.get_id() # Use new name
		if not current_id and isinstance(stanza_obj_or_str, (Iq, Message, Presence)): # Only auto-ID stanzas that typically use IDs
			STANZA_ID_COUNTER += 1
			current_id = str(STANZA_ID_COUNTER)
			stanza_obj_or_str.set_id(current_id) # Use new name

		# Set 'from' attribute if not already set and if owner has a registered JID
		if hasattr(self._owner, '_registered_jid_str') and self._owner._registered_jid_str and \
		   not stanza_obj_or_str.get_from() and isinstance(stanza_obj_or_str, Stanza): # Use new name
			stanza_obj_or_str.set_from(self._owner._registered_jid_str) # Use new name

		# Component routing logic
		if hasattr(self._owner, 'enable_routing_logic') and self._owner.enable_routing_logic and stanza_obj_or_str.getName() != "bind":
			to_jid_obj = stanza_obj_or_str.get_to() # Use new name
			target_domain = self._owner.server_host # Default to component's connected server
			if to_jid_obj and to_jid_obj.get_domain(): # Use new name
				target_domain = to_jid_obj.get_domain()

			from_jid_obj = stanza_obj_or_str.get_from() # Use new name
			source_domain = from_jid_obj.get_domain() if from_jid_obj else self._owner.server_host # Fallback for from

			# Create <route> stanza
			route_stanza = Stanza(name="route", to_jid=target_domain, from_jid=source_domain, payload_list=[stanza_obj_or_str])
			# The route stanza itself should not inherit the inner stanza's namespace directly
			# It uses the component's stream namespace by default or specific routing NS if defined
			# For now, let it use the default stream namespace set by the component.
			final_stanza_to_send = route_stanza
		else:
			final_stanza_to_send = stanza_obj_or_str

		# Ensure top-level stanzas sent over the stream use the stream's default namespace
		# if they don't have one already set (usually jabber:client or jabber:component:accept)
		if not final_stanza_to_send.getNamespace() and hasattr(self._owner, 'default_stanza_namespace'):
			final_stanza_to_send.setNamespace(self._owner.default_stanza_namespace)

		# Attach to a conceptual stream parent before serializing (for simplexml's asStr)
		if hasattr(self, '_stream_header_node'): # Check if stream header node exists
		    final_stanza_to_send.setParent(self._stream_header_node)

		if not self._raw_send_function: raise RuntimeError("Raw send function not available for sending stanza object.")
		self._raw_send_function(str(final_stanza_to_send)) # Convert to string for sending
		return current_id

	def disconnect(self):
		"""
		Send a stream terminator and and handle all incoming stanzas before stream closure.
		"""
		if hasattr(self, '_raw_send_function') and self._raw_send_function:
		    self._raw_send_function("</stream:stream>")
		# Process any final incoming data after sending close tag
		# This loop might not be strictly necessary if the server closes immediately
		# but good for catching any final messages/errors.
		timeout_counter = 50 # Short timeout for final processing
		while self.process_stream_data(0.01) and timeout_counter > 0: # Use new name
			timeout_counter -= 1
		# Disconnect handlers are called by owner's _handle_disconnection when Process detects closure.

	# iter method is an alias for process_stream_data
	iter_process = type(send)(process_stream_data.__code__, process_stream_data.__globals__, name = "iter_process", argdefs = process_stream_data.__defaults__, closure = process_stream_data.__closure__)
