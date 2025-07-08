##   filetransfer.py
##
##   Copyright (C) 2004 Alexey "Snake" Nezhdanov
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

# $Id: filetransfer.py, v1.7 2013/10/21 alkorgun Exp $

"""
This module contains InBandBytestream class that is the simple implementation of JEP-0047.
Note that this is just a transport for data. You have to negotiate data transfer before
(via StreamInitiation most probably). Unfortunately SI is not implemented yet.
"""

import base64 # Changed from from base64 import encodestring, decodestring
from .dispatcher import PlugIn # PlugIn class name is fine
# Assuming protocol classes will be renamed in protocol.py (e.g., Iq -> IqStanza)
from .protocol import Iq, Node, NodeProcessed, ErrorStanza, Jid, \
                      NS_IBB, NS_AMP, ERR_BAD_REQUEST, ERR_ITEM_NOT_FOUND, ERR_UNEXPECTED_REQUEST

DEBUG_SCOPE_IBB = "ibb" # Renamed DBG_LINE

class InBandBytestream(PlugIn): # Renamed IBB
	"""
	IBB used to transfer small-sized data chunk over estabilished xmpp connection.
	Data is split into small blocks (by default 4096 bytes, matching XEP-0047 example),
	encoded as base 64 and sent to another entity that compiles these blocks back into the data chunk.
	This is very inefficient but should work under any circumstances. Note that
	using IBB normally should be the last resort.
	"""
	def __init__(self):
		"""
		Initialise internal variables.
		"""
		PlugIn.__init__(self)
		self.DEBUG_LINE_PREFIX = DEBUG_SCOPE_IBB # Use new constant name
		self._exported_methods = [self.open_ibb_stream] # Use new method name
		self._streams = {} # Stores active IBB stream details {stream_id: stream_info_dict}
		# AMP rules to request error if recipient cannot store/deliver or if resource does not match
		self._amp_error_rules_node = Node(NS_AMP + " amp", # Renamed _ampnode
			payload=[
				Node("rule", {"condition": "deliver-at", "value": "stored", "action": "error"}),
				Node("rule", {"condition": "match-resource", "value": "exact", "action": "error"})
			])

	def plugin(self, client_or_component_instance): # Renamed owner
		"""
		Register handlers for receiving incoming datastreams. Used internally.
		"""
		# _owner is set by PlugIn base class's plugin method
		self._owner.RegisterHandler("iq", self.handle_stream_open_reply, sid=None) # To catch replies to our open requests
		self._owner.RegisterHandler("iq", self.handle_ibb_iq, namespace=NS_IBB)
		self._owner.RegisterHandler("message", self.handle_incoming_data_stanza, namespace=NS_IBB)


	def handle_ibb_iq(self, dispatcher_instance, iq_stanza): # Renamed IqHandler, conn, stanza
		"""
		Handles IBB related IQ stanzas (open, close).
		"""
		stanza_type = iq_stanza.get_type() # Renamed typ
		self.DEBUG(f"handle_ibb_iq called type->{stanza_type}", "info")

		query_node = iq_stanza.getTag("query") # Though IBB uses direct children, not query for open/close
		open_node = iq_stanza.getTag("open", namespace=NS_IBB)
		close_node = iq_stanza.getTag("close", namespace=NS_IBB)

		if stanza_type == "set" and open_node:
			self.handle_stream_open_request(dispatcher_instance, iq_stanza)
		elif stanza_type == "set" and close_node:
			self.handle_stream_close_request(dispatcher_instance, iq_stanza)
		elif stanza_type == "result":
			# This might be a reply to a data stanza ack if data were sent via IQ (not standard)
			# Or a reply to our close stanza.
			self.handle_stream_open_reply(dispatcher_instance, iq_stanza) # Assuming it can handle generic results/errors for open
		elif stanza_type == "error":
			self.handle_stream_open_reply(dispatcher_instance, iq_stanza) # Errors for open/close
		else:
			dispatcher_instance.send(ErrorStanza(iq_stanza, ERR_BAD_REQUEST))
		raise NodeProcessed()

	def handle_stream_open_request(self, dispatcher_instance, open_iq_stanza): # Renamed StreamOpenHandler, conn, stanza
		"""
		Handles opening of new incoming stream. Used internally.
		"""
		error_condition = None # Renamed err
		open_node = open_iq_stanza.getTag("open", namespace=NS_IBB)
		stream_id = open_node.getAttr("sid") # Renamed sid
		block_size_str = open_node.getAttr("block-size") # Renamed blocksize

		self.DEBUG(f"StreamOpenHandler called sid->{stream_id} block-size->{block_size_str}", "info")

		block_size = 0
		try:
			block_size = int(block_size_str)
		except (ValueError, TypeError):
			error_condition = ERR_BAD_REQUEST

		if not stream_id or block_size <= 0 : # block-size must be positive
			error_condition = ERR_BAD_REQUEST
		elif stream_id in self._streams:
			error_condition = ERR_UNEXPECTED_REQUEST # Or ERR_CONFLICT if stream ID collision

		if error_condition:
			reply_stanza_obj = ErrorStanza(open_iq_stanza, error_condition) # Renamed rep
		else:
			self.DEBUG(f"Opening stream: id {stream_id}, block-size {block_size}", "info")
			reply_stanza_obj = Iq(stanza_type="result", to_jid=open_iq_stanza.get_from(), from_jid=open_iq_stanza.get_to(), attrs_dict={"id": open_iq_stanza.get_id()})
			# Store stream details
			# TODO: Consider a more robust temporary file solution
			temp_file_path = f"/tmp/xmpppy_ibb_received_{stream_id}"
			try:
			    file_obj = open(temp_file_path, "wb") # Open in binary write mode
			except IOError as e:
			    self.DEBUG(f"Failed to open temp file {temp_file_path}: {e}", "error")
			    reply_stanza_obj = ErrorStanza(open_iq_stanza, ERR_INTERNAL_SERVER_ERROR) # Using a generic error
			    dispatcher_instance.send(reply_stanza_obj)
			    return

			self._streams[stream_id] = {
				"direction": "<" + str(open_iq_stanza.get_from()), # Incoming
				"block-size": block_size,
				"file_object": file_obj, # Renamed fp
				"sequence_number": 0, # Renamed seq
				"synchronization_id": open_iq_stanza.get_id() # Renamed syn_id
			}
		dispatcher_instance.send(reply_stanza_obj)

	def open_ibb_stream(self, stream_id, recipient_jid_str, file_object_to_send, block_size=4096): # Renamed OpenStream & params
		"""
		Start new stream. Provide stream id, recipient JID, file object to send, and optional blocksize.
		"""
		if stream_id in self._streams:
			self.DEBUG(f"Stream ID {stream_id} already in use.", "error")
			return None

		recipient_jid = Jid(recipient_jid_str) # Use Jid class
		if not recipient_jid.getResource():
			self.DEBUG(f"Recipient JID {recipient_jid_str} must have a resource.", "error")
			return None # IBB requires a full JID

		self._streams[stream_id] = {
		    "direction": "|>" + str(recipient_jid), # Outgoing, pending confirmation |>
		    "block-size": block_size,
		    "file_object": file_object_to_send,
		    "sequence_number": 0,
		    "recipient_jid": recipient_jid # Store Jid object
		}
		self._owner.RegisterCycleHandler(self.handle_send_data_cycle) # Register if not already (or manage one global handler)

		# Construct the <open/> IQ
		open_payload_node = Node("open", attrs={"sid": stream_id, "block-size": str(block_size)}, namespace=NS_IBB)
		open_iq_request = Iq(stanza_type="set", to_jid=recipient_jid, payload_list=[open_payload_node]) # Renamed syn

		# Send and store ID for matching reply
		# The reply will be handled by handle_stream_open_reply
		sent_id = self._owner.send(open_iq_request)
		self._streams[stream_id]["synchronization_id"] = sent_id
		self.DEBUG(f"IBB open request sent for SID {stream_id} to {recipient_jid_str}, sync_id {sent_id}", "info")
		return self._streams[stream_id] # Return stream details dict

	def handle_send_data_cycle(self, dispatcher_instance): # Renamed SendHandler, conn
		"""
		Send next portion of data for active outgoing streams. Called periodically.
		"""
		self.DEBUG("handle_send_data_cycle called", "info")
		streams_to_remove = []
		for stream_id, stream_details in list(self._streams.items()): # Iterate over a copy for safe deletion
			if stream_details["direction"].startswith(">"): # Stream is open and ready to send data (was '|')
				data_chunk = stream_details["file_object"].read(stream_details["block-size"]) # Renamed chunk

				if data_chunk:
					encoded_data = base64.b64encode(data_chunk).decode('ascii')
					# IBB data is sent in <message type='chat'>, not IQ
					ibb_data_node = Node("data", {"sid": stream_id, "seq": str(stream_details["sequence_number"])}, payload=[encoded_data], namespace=NS_IBB) # Renamed datanode

					# Construct message stanza
					# from_jid should be the component's JID or client's full JID
					# For now, assuming self._owner has a proper JID set (e.g., self._owner._registered_jid_str)
					from_address = self._owner._registered_jid_str if hasattr(self._owner, '_registered_jid_str') else self._owner.Server

					message_stanza = Message(to_jid=stream_details["recipient_jid"], from_jid=from_address, stanza_type="chat", payload_list=[ibb_data_node])

					# Add AMP rules if needed (original code added self._amp_error_rules_node)
					# message_stanza.addChild(node=self._amp_error_rules_node) # This makes it non-standard IBB

					dispatcher_instance.send(message_stanza)
					self.DEBUG(f"Sent data chunk for SID {stream_id}, seq {stream_details['sequence_number']}", "ok")

					stream_details["sequence_number"] = (stream_details["sequence_number"] + 1) % 65536
				else: # End of file
					close_iq = Iq(stanza_type="set", to_jid=stream_details["recipient_jid"], payload_list=[Node("close", {"sid": stream_id}, namespace=NS_IBB)])
					dispatcher_instance.send(close_iq)
					dispatcher_instance.dispatch_event(DEBUG_SCOPE_IBB, "SUCCESSFUL_SEND", stream_details) # Use new constant
					streams_to_remove.append(stream_id)
					self.DEBUG(f"IBB stream SID {stream_id} closed after sending all data.", "ok")
			# elif stream_details["direction"].startswith("|>"):
				# Waiting for stream open confirmation - handled by StreamOpenReplyHandler

		for stream_id in streams_to_remove:
			if stream_id in self._streams: # Check if not already deleted by another handler
			    if hasattr(self._streams[stream_id]["file_object"], 'close'):
			        self._streams[stream_id]["file_object"].close()
			    del self._streams[stream_id]

		if not any(s_details["direction"].startswith('>') for s_details in self._streams.values()):
			# No more active sending streams, unregister cycle handler
			self._owner.UnregisterCycleHandler(self.handle_send_data_cycle)


	def handle_incoming_data_stanza(self, dispatcher_instance, message_stanza): # Renamed ReceiveHandler, conn, stanza
		"""
		Receive next portion of incoming datastream and store it.
		"""
		data_node = message_stanza.getTag("data", namespace=NS_IBB)
		if not data_node: return # Not an IBB data message

		stream_id = data_node.getAttr("sid") # Renamed sid
		sequence_num_str = data_node.getAttr("seq") # Renamed seq
		base64_encoded_data = data_node.getData() # Renamed data

		self.DEBUG(f"handle_incoming_data_stanza called sid->{stream_id} seq->{sequence_num_str}", "info")

		error_condition = None
		sequence_number = -1

		try:
			sequence_number = int(sequence_num_str)
			decoded_data_bytes = base64.b64decode(base64_encoded_data) # Renamed data
		except Exception: # Includes ValueError for int, and binascii.Error for b64decode
			error_condition = ERR_BAD_REQUEST # Malformed data
			decoded_data_bytes = b"" # Ensure it's bytes

		if not stream_id or stream_id not in self._streams:
			error_condition = ERR_ITEM_NOT_FOUND # Stream ID unknown
		elif not error_condition: # Only proceed if data was decoded and SID exists
			stream_details = self._streams[stream_id] # Renamed stream
			if not decoded_data_bytes: # Empty data payload in a data stanza
				error_condition = ERR_BAD_REQUEST
			elif sequence_number != stream_details["sequence_number"]:
				error_condition = ERR_UNEXPECTED_REQUEST # Sequence out of order
			else:
				try:
					stream_details["file_object"].write(decoded_data_bytes)
					stream_details["sequence_number"] = (stream_details["sequence_number"] + 1) % 65536
					self.DEBUG(f"Successfully received data for SID {stream_id}, seq {sequence_number}. Wrote {len(decoded_data_bytes)} bytes.", "ok")
				except IOError as e:
				    self.DEBUG(f"IOError writing to file for SID {stream_id}: {e}", "error")
				    error_condition = ERR_INTERNAL_SERVER_ERROR # Or some other appropriate error
				    # Consider closing the stream locally on write error
				    if stream_id in self._streams and hasattr(self._streams[stream_id]["file_object"], 'close'):
				        self._streams[stream_id]["file_object"].close()
				    if stream_id in self._streams:
				        del self._streams[stream_id]


		if error_condition:
			self.DEBUG(f"Error on receive for SID {stream_id}: {error_condition}", "error")
			# Send error IQ in response to the problematic data (though data comes in message)
			# XEP-0047 says "The recipient then acknowledges receipt of the data by sending an IQ-result to the sender."
			# This implies data was an IQ, but it is usually a message.
			# If data is in a message, an IQ error reply is not standard.
			# For now, sending an IBB close IQ with an error.
			error_iq = Iq(stanza_type="set", to_jid=message_stanza.get_from(), from_jid=message_stanza.get_to(),
			              payload_list=[Node("close", attrs={"sid": stream_id}, namespace=NS_IBB)])
			# Add error sub-element to the IQ itself
			error_iq.set_error(error_condition) # This will set type to "error"
			dispatcher_instance.send(error_iq)
			# Clean up broken stream
			if stream_id in self._streams:
			    if hasattr(self._streams[stream_id]["file_object"], 'close'):
			        self._streams[stream_id]["file_object"].close()
			    del self._streams[stream_id]
		raise NodeProcessed()


	def handle_stream_close_request(self, dispatcher_instance, close_iq_stanza): # Renamed StreamCloseHandler, conn, stanza
		"""
		Handle stream closure from remote after all data transmitted.
		"""
		stream_id = close_iq_stanza.getTag("close", namespace=NS_IBB).getAttr("sid") # Renamed sid
		self.DEBUG(f"handle_stream_close_request called sid->{stream_id}", "info")

		if stream_id in self._streams:
			stream_details = self._streams[stream_id]
			if hasattr(stream_details["file_object"], 'close'):
			    stream_details["file_object"].close() # Close the associated file

			reply_stanza_obj = close_iq_stanza.build_reply("result") # Use new name
			dispatcher_instance.send(reply_stanza_obj)
			dispatcher_instance.dispatch_event(DEBUG_SCOPE_IBB, "SUCCESSFUL_RECEIVE", stream_details)
			del self._streams[stream_id]
		else:
			dispatcher_instance.send(ErrorStanza(close_iq_stanza, ERR_ITEM_NOT_FOUND))
		raise NodeProcessed()

	# StreamBrokenHandler seems to be conflated with StreamOpenReplyHandler for errors
	# Let's keep StreamOpenReplyHandler to manage replies to our <open> requests (result or error)

	def handle_stream_open_reply(self, dispatcher_instance, reply_stanza): # Renamed StreamOpenReplyHandler, conn, stanza
		"""
		Handle remote side reply to our <open> request (result or error).
		"""
		synchronization_id = reply_stanza.get_id() # Renamed syn_id
		self.DEBUG(f"handle_stream_open_reply called for sync_id->{synchronization_id}, type->{reply_stanza.get_type()}", "info")

		stream_id_found = None
		for sid, stream_details_val in list(self._streams.items()): # Renamed stream
			if stream_details_val.get("synchronization_id") == synchronization_id:
				stream_id_found = sid
				break

		if not stream_id_found:
			self.DEBUG(f"Received reply for unknown sync_id {synchronization_id}", "warn")
			# This might be a reply for an already closed/failed stream or a generic IQ result/error not for IBB open.
			# If not NodeProcessed, other handlers might pick it up.
			return

		stream_details = self._streams[stream_id_found]

		if reply_stanza.get_type() == "error":
			error_name = reply_stanza.get_error_condition_node().getName() if reply_stanza.get_error_condition_node() else "Unknown error"
			self.DEBUG(f"Stream open failed for SID {stream_id_found}, error: {error_name}", "error")
			if stream_details["direction"].startswith("<"): # Incoming stream that we failed to acknowledge properly? Unlikely.
				dispatcher_instance.dispatch_event(DEBUG_SCOPE_IBB, "ERROR_ON_RECEIVE_SETUP", stream_details)
			else: # Outgoing stream we initiated
				dispatcher_instance.dispatch_event(DEBUG_SCOPE_IBB, "ERROR_ON_SEND_SETUP", stream_details)
			if hasattr(stream_details["file_object"], 'close'): stream_details["file_object"].close()
			del self._streams[stream_id_found]
			# If this was an outgoing stream that failed, unregister SendHandler if no other streams active
			if not any(s_details["direction"].startswith('>') for s_details in self._streams.values()):
			    self._owner.UnregisterCycleHandler(self.handle_send_data_cycle)

		elif reply_stanza.get_type() == "result":
			if stream_details["direction"].startswith("|>"): # Our outgoing stream open was accepted
				stream_details["direction"] = ">" + stream_details["direction"][2:] # Mark as active for sending
				dispatcher_instance.dispatch_event(DEBUG_SCOPE_IBB, "STREAM_COMMITTED", stream_details)
				self.DEBUG(f"IBB stream SID {stream_id_found} successfully opened for sending.", "ok")
			else: # Unexpected result, perhaps for a close IQ we sent.
			      # Or if this handler was mistakenly called for a non-open related IQ result.
				self.DEBUG(f"Received unexpected result for IBB stream SID {stream_id_found} with sync_id {synchronization_id}", "warn")
				# conn.send(ErrorStanza(reply_stanza, ERR_UNEXPECTED_REQUEST)) # Sending error for a result is usually not done.
		raise NodeProcessed()
