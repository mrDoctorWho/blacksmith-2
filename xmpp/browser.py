##   browser.py
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

# $Id: browser.py, v1.13 2013/11/03 alkorgun Exp $

"""
Browser module provides DISCO server framework for your application.
This functionality can be used for very different purposes - from publishing
software version and supported features to building of "jabber site" that users
can navigate with their disco browsers and interact with active content.

Such functionality is achieved via registering "DISCO handlers" that are
automatically called when user requests some node of your disco tree.
"""

from .dispatcher import XMPPDispatcher # Assuming renamed
from .plugin import PlugIn
# Assuming protocol classes will be renamed in protocol.py (e.g., Iq -> IqStanza)
from .protocol import Iq, Node, NodeProcessed, ErrorStanza, DataForm, \
                      NS_DISCO_INFO, NS_DISCO_ITEMS, ERR_ITEM_NOT_FOUND, \
                      NS_GROUPCHAT, NS_REGISTER, NS_SEARCH, NS_TIME, NS_VERSION # Import specific namespaces

DEBUG_SCOPE_BROWSER = "browser"

class DiscoBrowser(PlugIn): # Renamed Browser
	"""
	WARNING! This class is for components only. It will not work in client mode!

	Standard xmpppy class that is an ancestor of PlugIn and can be attached
	to your application.
	All processing will be performed in the handlers registered in the browser
	instance. You can register any number of handlers ensuring that for each
	node/jid combination only one (or none) handler registered.
	You can register static information or a function that will
	calculate the answer dynamically.
	Example of static info (see XEP-0030, examples 13-14):
	# component_conn - your xmpppy component connection instance.
	disco_browser = xmpp.browser.DiscoBrowser()
	disco_browser.PlugIn(component_conn)
	items_list = []
	item_dict = {}
	item_dict["jid"] = "catalog.shakespeare.lit"
	item_dict["node"] = "books"
	item_dict["name"] = "Books by and about Shakespeare"
	items_list.append(item_dict)
	# ... more items ...
	info_data = {"ids": [], "features": []}
	disco_browser.set_disco_handler({"items": items_list, "info": info_data})

	items should be a list of item dictionaries.
	Every item dictionary can have keys: "jid", "node", "name", "action".
	info_data should be a dictionary and must have keys "ids" and "features".
	Both should be lists:
		ids is a list of dictionaries (identity attributes).
		features is a list of feature URI strings.
	Example (see XEP-0030, examples 1-2)
	identities_list = []
	identities_list.append({"category": "conference", "type": "text", "name": "Play-Specific Chatrooms"})
	features_list = [NS_DISCO_INFO, NS_DISCO_ITEMS, NS_MUC]
	info_data = {"ids": identities_list, "features": features_list}
	# info_data["xdata"] = xmpp.protocol.DataForm() # XEP-0128
	disco_browser.set_disco_handler({"items": [], "info": info_data})
	"""
	def __init__(self):
		"""
		Initialises internal variables. Used internally.
		"""
		PlugIn.__init__(self)
		self.DEBUG_LINE_PREFIX = DEBUG_SCOPE_BROWSER
		self._exported_methods = [] # No methods exported by default for external calls via plugin owner
		# _handlers stores a nested dictionary: {target_jid_str: {disco_node_str_path: handler_func_or_dict}}
		# "" key for jid means default for any jid.
		# "" key for node path means handler for the jid itself (no node).
		# Path segments are keys in nested dicts, with a special key (e.g. 1 or True) holding the handler.
		self._handlers = {"": {True: None}} # Root handler for empty JID, empty node (default for server)

	def plugin(self, component_instance): # Renamed owner
		"""
		Registers its own iq handlers in your application dispatcher instance.
		Used internally.
		"""
		# _owner is set by PlugIn's plugin method
		self._owner.RegisterHandler("iq", self._handle_discovery_query, stanza_type="get", namespace=NS_DISCO_INFO)
		self._owner.RegisterHandler("iq", self._handle_discovery_query, stanza_type="get", namespace=NS_DISCO_ITEMS)

	def plugout(self):
		"""
		Unregisters browser's iq handlers from your application dispatcher instance.
		Used internally.
		"""
		self._owner.UnregisterHandler("iq", self._handle_discovery_query, stanza_type="get", namespace=NS_DISCO_INFO)
		self._owner.UnregisterHandler("iq", self._handle_discovery_query, stanza_type="get", namespace=NS_DISCO_ITEMS)

	def _traverse_disco_path(self, disco_node_str_path, target_jid_str, create_if_missing=False): # Renamed params
		"""
		Traverses the internal handler structure for a given JID and node path.
		Returns (parent_dictionary, key_for_handler) or (None, None).
		'key_for_handler' is typically True (or 1 in original) if the path exists.
		"""
		if target_jid_str in self._handlers:
			current_level_dict = self._handlers[target_jid_str] # Renamed cur
		elif create_if_missing:
			self._handlers[target_jid_str] = {True: None} # Add True key for handler at this JID level itself
			current_level_dict = self._handlers[target_jid_str]
		else: # JID not found and not creating
			current_level_dict = self._handlers.get("", {True:None}) # Fallback to default JID handler

		path_segments = []
		if disco_node_str_path: # If node is None or empty, refers to the JID itself
			path_segments = [segment for segment in disco_node_str_path.replace("\\", "/").split("/") if segment] # Normalize and split

		parent_dict_for_final_segment = current_level_dict
		for path_segment_str in path_segments: # Renamed i
			if path_segment_str in parent_dict_for_final_segment:
				parent_dict_for_final_segment = parent_dict_for_final_segment[path_segment_str]
			elif create_if_missing:
				# Store parent dict and current segment name for creating new level
				new_level_dict = {True: None, "_parent_dict_ref": parent_dict_for_final_segment, "_segment_name": path_segment_str}
				parent_dict_for_final_segment[path_segment_str] = new_level_dict
				parent_dict_for_final_segment = new_level_dict
			else: # Path segment not found and not creating
				# Check if there's a handler at the current level before this missing segment
				return parent_dict_for_final_segment, True if True in parent_dict_for_final_segment else None

		# At the end of the path (or if path was empty)
		if True in parent_dict_for_final_segment or create_if_missing: # True is the key for the handler itself
			return parent_dict_for_final_segment, True

		# Path exhausted but no specific handler at this exact node, and not creating
		# This case might mean we should fall back to a handler higher up if not exact match needed.
		# Original code's logic for this fallback was implicit in how it traversed.
		# For now, if no exact handler and not creating, return None, None if path was specified
		if disco_node_str_path: return None, None
		return parent_dict_for_final_segment, True # Handler for JID itself if node path was empty

	def set_disco_handler(self, handler_func_or_dict, disco_node_str="", target_jid_str=""): # Renamed params
		"""
		Registers a DISCO handler or static info for a specific JID and node.
		"""
		self.DEBUG(f"Registering handler {type(handler_func_or_dict)} for JID '{target_jid_str}' node->'{disco_node_str}'", "info")
		parent_dict, handler_key = self._traverse_disco_path(disco_node_str, target_jid_str, create_if_missing=True)
		if parent_dict is not None and handler_key is not None: # Should always be True or created if create_if_missing
			parent_dict[handler_key] = handler_func_or_dict
		else: # Should not happen with create_if_missing=True
		    self.DEBUG(f"Failed to traverse/create path for handler at JID '{target_jid_str}' node '{disco_node_str}'", "error")


	def get_disco_handler(self, disco_node_str="", target_jid_str=""): # Renamed params
		"""
		Returns the handler for a specific JID and node, falling back to defaults.
		"""
		parent_dict, handler_key = self._traverse_disco_path(disco_node_str, target_jid_str, create_if_missing=False)

		current_dict_to_check = parent_dict
		key_to_check = handler_key

		# Traverse up to find a handler if exact match not found
		while current_dict_to_check:
		    if key_to_check in current_dict_to_check and current_dict_to_check[key_to_check] is not None:
		        return current_dict_to_check[key_to_check]
		    # Move to parent dictionary in the path
		    if "_parent_dict_ref" in current_dict_to_check:
		        current_dict_to_check = current_dict_to_check["_parent_dict_ref"]
		        key_to_check = True # Check for handler at this parent level
		    else: # Reached top for this JID or default JID
		        break

		# If not found for specific JID, try default JID ("") with the same node path
		if target_jid_str != "": # Avoid infinite loop if already checking default
		    parent_dict_default_jid, handler_key_default_jid = self._traverse_disco_path(disco_node_str, "", create_if_missing=False)
		    current_dict_to_check = parent_dict_default_jid
		    key_to_check = handler_key_default_jid
		    while current_dict_to_check:
		        if key_to_check in current_dict_to_check and current_dict_to_check[key_to_check] is not None:
		            return current_dict_to_check[key_to_check]
		        if "_parent_dict_ref" in current_dict_to_check:
		            current_dict_to_check = current_dict_to_check["_parent_dict_ref"]
		            key_to_check = True
		        else:
		            break
		return None # No handler found

	def delete_disco_handler(self, disco_node_str="", target_jid_str=""): # Renamed params
		"""
		Unregisters DISCO handler for a specific JID and node.
		"""
		parent_dict, handler_key = self._traverse_disco_path(disco_node_str, target_jid_str, create_if_missing=False)
		if parent_dict and handler_key in parent_dict:
			handler_to_delete = parent_dict[handler_key]
			# If this is the only handler at this level, and it has a parent dict reference, delete the current level dict from parent
			if "_parent_dict_ref" in parent_dict and "_segment_name" in parent_dict:
			    grand_parent_dict = parent_dict["_parent_dict_ref"]
			    segment_name = parent_dict["_segment_name"]
			    # Check if only handler (True key) and meta keys exist
			    if all(k in [True, "_parent_dict_ref", "_segment_name"] for k in parent_dict.keys()):
			        del grand_parent_dict[segment_name]
			    else: # Other sub-nodes exist, just delete the handler
			        del parent_dict[handler_key]
			else: # Root for this JID or default JID
			    del parent_dict[handler_key]
			return handler_to_delete
		return None


	def _handle_discovery_query(self, dispatcher_instance, iq_request_stanza): # Renamed params
		"""
		Serves DISCO IQ request from a remote client.
		"""
		disco_node_id = iq_request_stanza.get_query_node_attribute() # Renamed node, Use new method name
		target_jid_obj = iq_request_stanza.get_to() # Target of the disco query
		target_jid_str = str(target_jid_obj) if target_jid_obj else ""

		# Fallback to component's own JID if 'to' is not specified or is the server itself
		# This is typical for component disco queries to the component itself.
		if not target_jid_obj or target_jid_obj.getDomain() == self._owner.Server: # Assuming _owner.Server is component's JID
		    target_jid_str = self._owner.Server # Disco on the component itself

		disco_node_id_str = disco_node_id if disco_node_id else "" # Renamed nodestr

		handler_func_or_dict = self.get_disco_handler(disco_node_id_str, target_jid_str) # Renamed handler

		if not handler_func_or_dict:
			self.DEBUG(f"No Handler for disco request to JID='{target_jid_str}' node='{disco_node_id_str}' ns='{iq_request_stanza.get_query_namespace()}'", "error")
			dispatcher_instance.send(ErrorStanza(iq_request_stanza, ERR_ITEM_NOT_FOUND)) # Use new name
			raise NodeProcessed()

		self.DEBUG(f"Handling disco request to JID='{target_jid_str}' node='{disco_node_id_str}' ns='{iq_request_stanza.get_query_namespace()}'", "ok")
		reply_iq_stanza = iq_request_stanza.build_reply("result") # Renamed rep
		if disco_node_id: # Add node attribute back to reply if it was in request
			reply_iq_stanza.set_query_node_attribute(disco_node_id) # Use new name

		query_node_reply = reply_iq_stanza.getTag("query") # Renamed q

		if iq_request_stanza.get_query_namespace() == NS_DISCO_ITEMS:
			items_list_result = [] # Renamed lst
			if isinstance(handler_func_or_dict, dict):
				items_list_result = handler_func_or_dict.get("items", [])
			else: # It's a callable handler
				items_list_result = handler_func_or_dict(dispatcher_instance, iq_request_stanza, "items")

			if items_list_result is None: # Handler indicated item not found
				dispatcher_instance.send(ErrorStanza(iq_request_stanza, ERR_ITEM_NOT_FOUND))
				raise NodeProcessed()
			for item_attributes_dict in items_list_result: # Renamed item
				query_node_reply.addChild("item", attrs=item_attributes_dict)

		elif iq_request_stanza.get_query_namespace() == NS_DISCO_INFO:
			info_data_dict = None # Renamed dt
			if isinstance(handler_func_or_dict, dict):
				info_data_dict = handler_func_or_dict.get("info", {})
			else: # Callable handler
				info_data_dict = handler_func_or_dict(dispatcher_instance, iq_request_stanza, "info")

			if info_data_dict is None:
				dispatcher_instance.send(ErrorStanza(iq_request_stanza, ERR_ITEM_NOT_FOUND))
				raise NodeProcessed()

			for identity_attributes_dict in info_data_dict.get("ids", []): # Renamed id
				query_node_reply.addChild("identity", attrs=identity_attributes_dict)
			for feature_uri_str in info_data_dict.get("features", []): # Renamed feature
				query_node_reply.addChild("feature", attrs={"var": feature_uri_str})
			if "xdata" in info_data_dict and isinstance(info_data_dict["xdata"], Node): # Check for DataForm
				query_node_reply.addChild(node=info_data_dict["xdata"])

		dispatcher_instance.send(reply_iq_stanza)
		raise NodeProcessed()
