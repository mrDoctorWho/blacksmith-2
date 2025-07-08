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

# $Id: transports.py, v1.36 2013/11/03 alkorgun Exp $

"""
This module contains the low-level implementations of xmpppy connect methods or
(in other words) transports for xmpp-stanzas.
Currently here is three transports:
direct TCP connect - TcpSocketConnection class
proxied TCP connect - HttpProxySocketConnection class (CONNECT proxies)
TLS connection - TlsHandler class. Can be used for SSL connections also.

Transports are stackable so you - f.e. TlsHandler use HttpProxySocketConnection or TcpSocketConnection as more low-level transport.

Also exception 'TransportError' is defined to allow capture of this module specific exceptions.
"""

import sys
import socket
from . import dispatcher # dispatcher.py and its classes will be refactored
import base64 # Changed from from base64 import encodestring
from select import select
from .simplexml import to_unicode_string # Renamed ustr
from .plugin import PlugIn
# Assuming protocol classes will be renamed in protocol.py (e.g., Iq -> IqStanza)
from .protocol import Iq, Node, NodeProcessed, ErrorStanza, Jid, \
                      NS_TLS, NS_STREAMS # Import specific namespaces needed

# http://pydns.sourceforge.net
try:
	import dns # This will use the refactored dns package
except ImportError:
	dns = None

DATA_RECEIVED = 'DATA RECEIVED' # Already PEP 8 compliant
DATA_SENT = 'DATA SENT' # Already PEP 8 compliant
DEBUG_SCOPE_CONNECT_PROXY = 'CONNECT_PROXY' # Renamed DBG_CONNECT_PROXY
DEBUG_SCOPE_SOCKET = "socket" # Added for TCPsocket
DEBUG_SCOPE_TLS = "TLS" # Added for TLS

BUFFER_LENGTH = 1024 # Renamed BUFLEN

class TransportError(Exception): # Renamed error
	"""
	An exception to be raised in case of low-level errors in methods of 'transports' module.
	"""
	def __init__(self, comment_string): # Renamed comment
		"""
		Cache the descriptive string.
		"""
		self._comment_string = comment_string

	def __str__(self):
		"""
		Serialize exception into pre-cached descriptive string.
		"""
		return self._comment_string

class TcpSocketConnection(PlugIn): # Renamed TCPsocket
	"""
	This class defines direct TCP connection method.
	"""
	def __init__(self, server_address_tuple=None, use_srv_records=True): # Renamed server, use_srv
		"""
		Caches connection point 'server_address_tuple'.
		It is a tuple of (host, port).
		If use_srv_records is True, library will lookup for SRV records.
		"""
		PlugIn.__init__(self)
		self.DEBUG_LINE_PREFIX = DEBUG_SCOPE_SOCKET
		self._exported_methods = [self.send, self.disconnect]
		self._target_server_address = server_address_tuple # Renamed _server
		self.use_srv_records = use_srv_records # Renamed use_srv
		self._socket_object = None # Renamed _sock
		self._socket_send_method = None # Renamed _send
		self._socket_recv_method = None # Renamed _recv
		self._data_seen_on_socket = False # Renamed _seen_data, for TLS pending data check

	def _srv_lookup(self, server_address_tuple_input): # Renamed srv_lookup, server
		"""
		SRV resolver. Takes server=(host, port) as argument. Returns new (host, port) pair.
		"""
		if dns: # Check if pydns is available
			host_str, _ = server_address_tuple_input
			query_string = f"_xmpp-client._tcp.{host_str}" # Renamed query
			try:
				# Assuming dns.Base has been refactored
				if not dns.Base.DEFAULT_DNS_SETTINGS.get('server'): # Check if nameservers are set
				    dns.Base.discover_name_servers()

				dns_request_obj = dns.Base.DnsQuery() # Use new name DnsQuery
				# SRV type from dns.Type (will be dns.Type.RECORD_TYPE_SRV)
				response_obj = dns_request_obj.send_request(name=query_string, qtype=dns.Type.SRV) # Use new name

				if response_obj and response_obj.answers:
					# Data for SRV record is (priority, weight, port, target)
					_priority, _weight, port_num, target_host_str = response_obj.answers[0]['data']
					return str(target_host_str), int(port_num)
			except dns.Base.DNSError as e: # Use new name DNSError
				self.DEBUG(f"DNS SRV lookup for {query_string} failed: {e}", "warn")
			except ImportError: # If dns.Base or dns.Type parts not yet refactored/available
			    self.DEBUG(f"pydns.Base or Type not fully available for SRV lookup of {query_string}.", "warn")

		return server_address_tuple_input # Return original if SRV lookup fails or pydns not available

	def plugin(self, owner_instance): # Renamed owner
		"""
		Fire up connection. Return "ok" on success.
		Also registers self.handle_disconnection method in the owner_instance's dispatcher.
		Called internally.
		"""
		if not self._target_server_address: # If not provided in constructor, get from owner
			self._target_server_address = (self._owner.server_host, self._owner.server_port) # Use renamed attributes

		actual_server_to_connect = self._target_server_address
		if self.use_srv_records:
			actual_server_to_connect = self._srv_lookup(self._target_server_address)

		if not self.connect_to_server(actual_server_to_connect): # Use new name
			return None # Connection failed

		self._owner.Connection = self # Set self as the Connection object on the owner
		self._owner.register_disconnect_handler(self.handle_disconnection) # Use new name
		return "ok"

	def get_host(self): # Renamed getHost
		""" Returns the 'host' value that is connection is [will be] made to. """
		return self._target_server_address[0] if self._target_server_address else None

	def get_port(self): # Renamed getPort
		""" Returns the 'port' value that is connection is [will be] made to. """
		return self._target_server_address[1] if self._target_server_address else None

	def connect_to_server(self, server_address_tuple_to_connect=None): # Renamed connect, server
		"""
		Try to connect to the given host/port. Does not lookup for SRV record here.
		Returns "ok" on success.
		"""
		if not server_address_tuple_to_connect:
			server_address_tuple_to_connect = self._target_server_address

		host_str, port_int = server_address_tuple_to_connect[0], int(server_address_tuple_to_connect[1])

		socket_address_family = socket.AF_INET
		# Prepare address for socket.connect, handling IPv6
		if ":" in host_str and hasattr(socket, "AF_INET6"): # Rudimentary IPv6 check
			socket_address_family = socket.AF_INET6
			# For AF_INET6, connect expects (host, port, flowinfo, scopeid)
			# However, typically flowinfo and scopeid are 0 for client connections.
			final_server_address = (host_str, port_int, 0, 0)
		else:
			final_server_address = (host_str, port_int)

		try:
			self._socket_object = socket.socket(socket_address_family, socket.SOCK_STREAM)
			self._socket_object.connect(final_server_address)
			self._socket_send_method = self._socket_object.sendall
			self._socket_recv_method = self._socket_object.recv
		except socket.error as socket_err: # Renamed error
			error_code = socket_err.errno if hasattr(socket_err, 'errno') else 'N/A' # Renamed code
			error_message = str(socket_err) # Renamed error
			self.DEBUG(f"Failed to connect to remote host {final_server_address!r}: {error_message} (Code: {error_code})", "error")
			return None # Explicitly return None on failure
		except Exception as e: # Catch other potential errors
			self.DEBUG(f"An unexpected error occurred during connection to {final_server_address!r}: {e}", "error")
			return None
		else:
			self.DEBUG(f"Successfully connected to remote host {final_server_address!r}.", "start")
			return "ok"

	def plugout(self):
		"""
		Disconnect from the remote server and unregister self.handle_disconnection method.
		"""
		if self._socket_object: # Check if socket exists
		    self._socket_object.close()
		if hasattr(self._owner, "Connection") and self._owner.Connection is self: # Check if we are the current connection
			del self._owner.Connection
			self._owner.unregister_disconnect_handler(self.handle_disconnection) # Use new name

	def receive(self):
		"""
		Reads all pending incoming data.
		In case of disconnection calls owner's _handle_disconnection() method and then raises IOError exception.
		"""
		if not self._socket_recv_method: raise IOError("Socket not connected or receive method not set.")

		all_data_received = b"" # Start with bytes
		try:
			# First read attempt
			initial_data_chunk = self._socket_recv_method(BUFFER_LENGTH) # Use new name
			if not initial_data_chunk: # Connection closed by peer
			    raise IOError("Socket closed by peer during receive.")
			all_data_received += initial_data_chunk

			# Subsequent non-blocking reads for any remaining data in buffer
			self._socket_object.setblocking(False) # Non-blocking for checking buffer
			while True:
				try:
					additional_data_chunk = self._socket_recv_method(BUFFER_LENGTH)
					if not additional_data_chunk: break # No more data or closed
					all_data_received += additional_data_chunk
				except socket.error as e:
					if e.errno == socket.errno.EWOULDBLOCK or e.errno == socket.errno.EAGAIN:
						break # No more data currently available
					else: # Actual socket error
						raise
		except (socket.error, IOError) as e: # Catch socket errors or explicit IOError
			self.DEBUG(f"Socket error/IOError while receiving data: {e}", "error")
			if hasattr(sys,'exc_clear'): sys.exc_clear() # Deprecated, but in original
			if hasattr(self._owner, '_handle_disconnection'): self._owner._handle_disconnection() # Call owner's disconnect
			raise IOError(f"Disconnected! Error during receive: {e}") # Re-raise as IOError
		finally:
		    if self._socket_object: self._socket_object.setblocking(True) # Restore blocking mode

		if all_data_received:
			self._data_seen_on_socket = True
			# For debugging, try to decode for printing, but work with bytes internally mostly
			try:
			    debug_data_repr = all_data_received.decode('utf-8', 'replace')
			except: # Fallback if not utf-8
			    debug_data_repr = repr(all_data_received)
			self.DEBUG(debug_data_repr, "got")
			if hasattr(self._owner, "Dispatcher") and self._owner.Dispatcher:
				self._owner.Dispatcher.dispatch_event("", DATA_RECEIVED, all_data_received) # Use new name
		else: # Should have been caught by initial_data_chunk check or error handling
			self.DEBUG("No data received, but no immediate error; possibly clean disconnect.", "warn")
			if hasattr(self._owner, '_handle_disconnection'): self._owner._handle_disconnection()
			raise IOError("Disconnected! No data received.")
		return all_data_received


	def send(self, data_to_send): # Renamed data
		"""
		Writes raw outgoing data. Blocks until done.
		If supplied data is unicode string, encodes it to utf-8 before send.
		"""
		if not self._socket_send_method: raise IOError("Socket not connected or send method not set.")

		if isinstance(data_to_send, str):
			bytes_to_send = data_to_send.encode("utf-8")
		elif isinstance(data_to_send, bytes):
		    bytes_to_send = data_to_send
		else: # Try to convert to string then bytes
			bytes_to_send = to_unicode_string(data_to_send).encode("utf-8") # Use new name

		try:
			self._socket_send_method(bytes_to_send)
		except socket.error as e: # Catch specific socket errors
			self.DEBUG(f"Socket error while sending data: {e}", "error")
			if hasattr(self._owner, '_handle_disconnection'): self._owner._handle_disconnection()
			# Optionally re-raise or handle as a disconnect
		except Exception as e: # Catch other errors during send
			self.DEBUG(f"Unexpected error while sending data: {e}", "error")
			if hasattr(self._owner, '_handle_disconnection'): self._owner._handle_disconnection()
		else:
			# For debugging, decode if possible, otherwise show repr
			debug_data_repr = repr(bytes_to_send)
			if len(bytes_to_send) < 200 : # Avoid decoding very large byte strings for debug
			    try:
			        debug_data_repr = bytes_to_send.decode('utf-8', 'replace').strip()
			        if not debug_data_repr: debug_data_repr = repr(bytes_to_send) # If all whitespace
			    except: pass # Keep repr if decode fails

			self.DEBUG(debug_data_repr, "sent")
			if hasattr(self._owner, "Dispatcher") and self._owner.Dispatcher:
				self._owner.Dispatcher.dispatch_event("", DATA_SENT, bytes_to_send) # Use new name

	def pending_data(self, timeout_seconds=0): # Renamed timeout
		"""
		Returns true if there is a data ready to be read.
		"""
		if not self._socket_object: return False
		# select() expects a list of readable objects (sockets, pipes, etc.)
		readable_sockets, _, _ = select([self._socket_object], [], [], timeout_seconds)
		return bool(readable_sockets) # True if self._socket_object is in readable_sockets

	def disconnect(self):
		"""
		Closes the socket.
		"""
		self.DEBUG("Closing socket.", "stop")
		if self._socket_object: # Check if socket exists before closing
		    self._socket_object.close()
		    self._socket_object = None # Mark as closed

	def handle_disconnection(self): # Renamed disconnected
		"""
		Called when a Network Error or disconnection occurs.
		Designed to be overidden by subclasses or specific client logic.
		"""
		self.DEBUG("Socket operation failed or disconnected.", "error")
		# Basic default behavior is to log. Owner's disconnect handlers will do more.

class HttpProxySocketConnection(TcpSocketConnection): # Renamed HTTPPROXYsocket, TCPsocket
	"""
	HTTP (CONNECT) proxy connection class. Uses TcpSocketConnection as the base class,
	redefines only connect_to_server method.
	"""
	def __init__(self, proxy_settings_dict, target_server_tuple, use_srv_records=True): # Renamed proxy, server, use_srv
		"""
		Caches proxy and target addresses.
		'proxy_settings_dict' is a dictionary with 'host', 'port', and optional 'user', 'password'.
		'target_server_tuple' is (host, port).
		"""
		TcpSocketConnection.__init__(self, target_server_tuple, use_srv_records)
		self.DEBUG_LINE_PREFIX = DEBUG_SCOPE_CONNECT_PROXY # Use new name
		self._proxy_settings = proxy_settings_dict # Renamed _proxy

	def plugin(self, owner_instance): # Renamed owner
		"""
		Starts connection. Used interally. Returns "ok" on success.
		"""
		# Add specific debug scope if owner has debug_flags list (standardized in BaseClient)
		if hasattr(owner_instance, 'debug_flags') and isinstance(owner_instance.debug_flags, list):
		    if DEBUG_SCOPE_CONNECT_PROXY not in owner_instance.debug_flags:
		        owner_instance.debug_flags.append(DEBUG_SCOPE_CONNECT_PROXY)
		return TcpSocketConnection.plugin(self, owner_instance)

	def connect_to_server(self, target_server_address_tuple_ignored=None): # Renamed connect, dupe (ignored)
		"""
		Connects to proxy, authenticates if needed, then issues CONNECT to target.
		"""
		# Connect to the proxy server first
		proxy_host = self._proxy_settings["host"]
		proxy_port = self._proxy_settings["port"]
		if not TcpSocketConnection.connect_to_server(self, (proxy_host, proxy_port)): # Call parent's connect
			return None

		self.DEBUG("Proxy server contacted, performing CONNECT request.", "start")

		# _target_server_address is set by parent __init__ or plugin
		target_host, target_port = self._target_server_address

		http_connect_headers = [ # Renamed connector
			f"CONNECT {target_host}:{target_port} HTTP/1.0",
			"Proxy-Connection: Keep-Alive", # Standard header
			"Pragma: no-cache",
			f"Host: {target_host}:{target_port}", # Required for some proxies
			"User-Agent: xmpppy/HttpProxySocketConnection" # Be a good netizen
		]

		if "user" in self._proxy_settings and "password" in self._proxy_settings:
			credentials_str = f"{self._proxy_settings['user']}:{self._proxy_settings['password']}"
			# base64.encodestring is deprecated, use base64.b64encode
			encoded_credentials_bytes = base64.b64encode(credentials_str.encode('utf-8'))
			encoded_credentials_str = encoded_credentials_bytes.decode('ascii').strip() # Remove potential newlines
			http_connect_headers.append(f"Proxy-Authorization: Basic {encoded_credentials_str}")

		http_connect_headers.append("\r\n") # End of headers

		self.send("\r\n".join(http_connect_headers)) # Send the CONNECT request

		try:
			# Read first line of proxy response
			# The receive method now returns bytes, so decode for string operations
			proxy_reply_str = b""
			# Read until \n\n (some proxies might send multiple headers)
			# This is a simplified way, a proper HTTP parser would be better for robustness.
			timeout_for_reply = time.time() + 10 # 10 second timeout for proxy reply
			while b"\n\n" not in proxy_reply_str and time.time() < timeout_for_reply:
			    chunk = self.receive() # This might block based on socket settings
			    if not chunk: break # Connection closed
			    proxy_reply_str += chunk

			if not proxy_reply_str:
			    raise TransportError("No reply from proxy server.")

			# Decode after receiving full headers (or timeout)
			proxy_reply_str = proxy_reply_str.decode('latin-1', 'replace').replace("\r", "")

		except IOError as e:
			self.DEBUG(f"Proxy suddenly disconnected or I/O error: {e}", "error")
			if hasattr(self._owner, '_handle_disconnection'): self._owner._handle_disconnection()
			return None

		first_line = proxy_reply_str.split("\n")[0]
		try:
			http_protocol_version, status_code_str, status_description = first_line.split(" ", 2) # Renamed proto, code, desc
		except ValueError: # Not enough parts in status line
			raise TransportError(f"Invalid proxy reply status line: {first_line}")

		if status_code_str != "200":
			self.DEBUG(f"Proxy CONNECT failed: {http_protocol_version} {status_code_str} {status_description}", "error")
			if hasattr(self._owner, '_handle_disconnection'): self._owner._handle_disconnection()
			return None

		# We don't need to read the rest of the proxy headers after a 200 OK for CONNECT.
		# The socket is now tunneled to the target server.
		self.DEBUG("Proxy CONNECT successful. Connection established to target server.", "ok")
		return "ok"

	def _debug_log(self, text_message, severity_level): # Renamed DEBUG, text, severity
		""" Overwrites DEBUG to use the specific proxy debug scope. """
		# Assuming self._owner has a DEBUG method (which is self._debugger.show_formatted_message)
		if hasattr(self._owner, 'DEBUG'):
		    self._owner.DEBUG(DEBUG_SCOPE_CONNECT_PROXY, text_message, severity_level)
		else: # Fallback print if owner's DEBUG is not available
		    print(f"PROXY_DEBUG ({severity_level}): {text_message}")


class TlsHandler(PlugIn): # Renamed TLS
	"""
	TLS connection used to encrypts already estabilished tcp connection.
	"""
	def __init__(self): # Added explicit __init__
	    PlugIn.__init__(self)
	    self.DEBUG_LINE_PREFIX = DEBUG_SCOPE_TLS
	    self.starttls_status = None # None, "in-progress", "success", "failure", "not-supported"
	    self._tcp_socket_handler = None # Will store the underlying TCPsocket/HTTPPROXYsocket instance
	    self.tls_established = False # Flag to indicate if TLS is active
	    self.starttls_status = None # Tracks negotiation: None, "proceed", "failure"

	def plugin(self, owner_instance, attempt_immediate_start=False): # Renamed PlugIn, owner, now
		"""
		If 'attempt_immediate_start' is true then starts using encryption immediately (for implicit SSL).
		Otherwise, waits for STARTTLS feature from server.
		"""
		# _owner is set by PlugIn base
		if hasattr(owner_instance, "TlsHandlerInstance"): # Prevent multiple TLS plugins
			self.DEBUG("TLS handler already plugged in.", "warn")
			return None

		PlugIn.plugin(self, owner_instance) # Call parent plugin
		owner_instance.TlsHandlerInstance = self # Register self on owner

		if attempt_immediate_start:
			return self._start_ssl_encryption()

		# Check if features already received
		if hasattr(self._owner.Dispatcher, 'Stream') and self._owner.Dispatcher.Stream.features:
			try:
				self._handle_stream_features(self._owner.Dispatcher, self._owner.Dispatcher.Stream.features)
			except NodeProcessed: # Expected if STARTTLS is initiated
				pass
		else: # Register to handle features when they arrive
			self._owner.RegisterHandlerOnce("features", self._handle_stream_features, xmlns=NS_STREAMS)
		self.starttls_status = None # Reset status until negotiation happens

	def plugout(self): # Removed now parameter
		"""
		Unregisters TLS handlers. Encryption cannot be stopped once started.
		"""
		if hasattr(self._owner, "TlsHandlerInstance"):
		    del self._owner.TlsHandlerInstance

		self._owner.UnregisterHandler("features", self._handle_stream_features, xmlns=NS_STREAMS)
		self._owner.UnregisterHandler("proceed", self._handle_starttls_response, xmlns=NS_TLS)
		self._owner.UnregisterHandler("failure", self._handle_starttls_response, xmlns=NS_TLS)
		PlugIn.plugout(self)


	def _handle_stream_features(self, dispatcher_instance, features_node): # Renamed FeaturesHandler, conn, feats
		"""
		Analyse server <features/> for STARTTLS support and initiate if found.
		"""
		if not features_node.getTag("starttls", namespace=NS_TLS):
			self.DEBUG("STARTTLS unsupported by remote server.", "warn")
			self.starttls_status = "not-supported" # Explicitly mark as not supported
			return

		self.DEBUG("STARTTLS supported by remote server. Requesting TLS start.", "ok")
		self._owner.RegisterHandlerOnce("proceed", self._handle_starttls_response, xmlns=NS_TLS)
		self._owner.RegisterHandlerOnce("failure", self._handle_starttls_response, xmlns=NS_TLS)
		# Send <starttls> - this is a direct child of stream, not an IQ.
		# The owner's send method should handle sending raw XML strings or Node objects.
		self._owner.send(Node("starttls", namespace=NS_TLS)) # Node will be serialized by owner.send
		self.starttls_status = "in-progress" # Mark that we've sent starttls
		raise NodeProcessed() # We've handled the features for STARTTLS

	def _pending_data_after_tls(self, timeout_seconds=0): # Renamed pending_data
		"""
		Returns true if there is data ready after TLS handshake.
		Relies on the underlying socket's _data_seen_on_socket flag or select.
		"""
		if self._tcp_socket_handler:
		    # After SSL handshake, data might have been read into SSL buffer
		    # SSLSocket.pending() tells if data is in SSL buffer
		    if hasattr(self._tcp_socket_handler._socket_object, 'pending') and self._tcp_socket_handler._socket_object.pending() > 0:
		        return True
		    # Fallback to select on the raw socket
		    return select([self._tcp_socket_handler._socket_object], [], [], timeout_seconds)[0]
		return False

	def _start_ssl_encryption(self): # Renamed _startSSL
		"""Wraps the existing socket with SSL/TLS."""
		if not hasattr(self._owner, 'Connection') or not self._owner.Connection:
		    self.DEBUG("No base connection available to start SSL/TLS.", "error")
		    return None

		self._tcp_socket_handler = self._owner.Connection # Store the original socket handler
		raw_socket = self._tcp_socket_handler._socket_object

		try:
			# Attempt to wrap the socket for SSL/TLS
			# For modern Python, ssl.SSLContext is preferred for more control
			# For simplicity here, replicating old socket.ssl if possible, or basic wrap
			import ssl
			context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT) # Modern way
			context.check_hostname = False # Adjust as needed for security
			context.verify_mode = ssl.CERT_NONE # Adjust as needed

			ssl_socket = context.wrap_socket(raw_socket, server_hostname=self._tcp_socket_handler.get_host())

			# Replace original socket methods with SSL socket methods
			self._tcp_socket_handler._socket_object = ssl_socket # The wrapped socket
			self._tcp_socket_handler._socket_send_method = ssl_socket.sendall
			self._tcp_socket_handler._socket_recv_method = ssl_socket.recv
			self._tcp_socket_handler._data_seen_on_socket = True # Assume data might be pending after handshake
			self._tcp_socket_handler.pending_data = self._pending_data_after_tls # Override pending_data for TLS

			# Forcing blocking for handshake, then can be non-blocking if asyncore is used later by dispatcher
			# This part is tricky with asyncore. Original code set _sock.setblocking(0) *within* TCPsocket.
			# For TLS handshake, blocking is often simpler.
			# ssl_socket.setblocking(True) # Ensure blocking for handshake
			# ssl_socket.do_handshake() # Explicit handshake if needed, wrap_socket often does it.
			# ssl_socket.setblocking(False) # Then back to non-blocking if required by async main loop

			self.tls_established = True
			self.starttls_status = "success" # If _start_ssl_encryption is called directly (implicit SSL)
			self.DEBUG("SSL/TLS encryption successfully started over existing connection.", "ok")
			return "ok"
		except ssl.SSLError as e:
			self.DEBUG(f"SSL/TLS handshake/wrapping failed: {e}", "error")
			self.starttls_status = "failure"
			self.tls_established = False
			# Potentially close the original socket if it's unusable
			# self._tcp_socket_handler.disconnect()
			return None
		except Exception as e:
		    self.DEBUG(f"Unexpected error during SSL/TLS setup: {e}", "error")
		    self.starttls_status = "failure"
		    self.tls_established = False
		    return None


	def _handle_starttls_response(self, dispatcher_instance, starttls_response_node): # Renamed StartTLSHandler, conn, starttls
		"""
		Handle server reply (<proceed/> or <failure/>) to <starttls/> request.
		"""
		if starttls_response_node.getNamespace() != NS_TLS:
			return # Not for us

		self.starttls_status = starttls_response_node.getName() # "proceed" or "failure"

		if self.starttls_status == "failure":
			self.DEBUG("Server sent <failure/> for STARTTLS.", "error")
			# No NodeProcessed, as this might be an event other parts of client want to know
			return

		self.DEBUG("Got STARTTLS <proceed/>. Switching to TLS/SSL...", "ok")
		if self._start_ssl_encryption() == "ok":
			# Successfully started TLS. Stream needs to be restarted.
			# The owner (Client) is responsible for sending a new stream header.
			# This plugin's job for negotiation is done.
			# We need to re-initialize the dispatcher's stream parser for the new encrypted stream.
			self.DEBUG("TLS established. Re-initializing stream for dispatcher.", "ok")
			self._owner.Dispatcher.plugout() # Clean up old stream state
			new_dispatcher = dispatcher.XMPPDispatcher() # Create a new dispatcher instance
			new_dispatcher.PlugIn(self._owner) # Plug it into the owner
			self._owner.Dispatcher = new_dispatcher # Replace old dispatcher

			# The owner should now send a new stream header over the encrypted connection.
			# self._owner.Dispatcher.initialize_stream() # This would send new <stream:stream>
		else:
			self.DEBUG("TLS handshake failed after <proceed/>.", "error")
			# Connection might be unusable now. The owner should handle this.
			# Consider calling owner's disconnect handler.
			self._owner._handle_disconnection() # Trigger disconnect
		raise NodeProcessed() # This handler has fully processed the <proceed/> or <failure/>
