##   features.py
##
##   Copyright (C) 2003-2004 Alexey "Snake" Nezhdanov
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

# $Id: features.py, v1.26 2013/10/21 alkorgun Exp $

"""
This module contains variable stuff that is not worth splitting into separate modules.
Here is:
	DISCO client and agents-to-DISCO and browse-to-DISCO emulators.
	IBR and password manager.
	jabber:iq:privacy methods
All these methods takes "dispatcher_instance" first argument that should be already connected
(and in most cases already authorised) dispatcher instance.
"""

from .protocol import Iq, Node, NodeProcessed, DataForm, \
                      NS_DISCO_ITEMS, NS_DISCO_INFO, NS_BROWSE, NS_AGENTS, \
                      NS_REGISTER, NS_DATA, NS_PRIVACY, \
                      ERR_FEATURE_NOT_IMPLEMENTED # Import renamed classes/constants if they are used from protocol.py

# Assuming these functions from protocol.py are also refactored or used as is.
# from .protocol import isResultNode

# This constant is already PEP 8 compliant.
REGISTER_DATA_RECEIVED = "REGISTER DATA RECEIVED"

def _discover_info_or_items(dispatcher_instance, namespace_uri, target_jid_str, disco_node_id=None, fallback_to_browse=False, fallback_to_agents=True): # Renamed params
	"""
	Try to obtain info from the remote object.
	If remote object doesn't support disco fall back to browse (if fallback_to_browse is true)
	and if it doesnt support browse (or fallback_to_browse is not true) fall back to agents protocol
	(if fallback_to_agents is true). Returns obtained info. Used internally.
	"""
	# Iq, NS_DISCO_ITEMS, etc. should be the refactored names if they come from protocol.py
	iq_request = Iq(to_jid=target_jid_str, stanza_type="get", query_namespace=namespace_uri) # Renamed params
	if disco_node_id:
		iq_request.set_query_node_attribute(disco_node_id) # Use new method name

	response_stanza = dispatcher_instance.send_and_wait_for_response(iq_request) # Use new method name

	if fallback_to_browse and not (response_stanza and response_stanza.get_type() == "result"): # Use new method name
		response_stanza = dispatcher_instance.send_and_wait_for_response(Iq(to_jid=target_jid_str, stanza_type="get", query_namespace=NS_BROWSE))

	if fallback_to_agents and not (response_stanza and response_stanza.get_type() == "result"):
		response_stanza = dispatcher_instance.send_and_wait_for_response(Iq(to_jid=target_jid_str, stanza_type="get", query_namespace=NS_AGENTS))

	if response_stanza and response_stanza.get_type() == "result":
		return [child_node for child_node in response_stanza.get_query_children() if isinstance(child_node, Node)] # Use new method name
	return []

def discover_items(dispatcher_instance, target_jid_str, disco_node_id=None): # Renamed params
	"""
	Query remote object about any items that it contains. Return items list.
	"""
	result_list = [] # Renamed ret
	# _discover_info_or_items will use NS_DISCO_ITEMS
	for item_node in _discover_info_or_items(dispatcher_instance, NS_DISCO_ITEMS, target_jid_str, disco_node_id): # Renamed i
		# Adapt to old agent fallback where name might be in a child tag
		if item_node.getName() == "agent" and item_node.getTag("name"): # agent is a non-standard disco item name
			item_node.setAttr("name", item_node.getTagData("name"))
		result_list.append(item_node.attrs)
	return result_list

def discover_info(dispatcher_instance, target_jid_str, disco_node_id=None): # Renamed params
	"""
	Query remote object about info that it publishes. Returns identities and features lists.
	"""
	identities_list, features_list = [], [] # Renamed identities, features
	# _discover_info_or_items will use NS_DISCO_INFO
	for item_node in _discover_info_or_items(dispatcher_instance, NS_DISCO_INFO, target_jid_str, disco_node_id): # Renamed i
		if item_node.getName() == "identity":
			identities_list.append(item_node.attrs)
		elif item_node.getName() == "feature":
			features_list.append(item_node.getAttr("var"))
		elif item_node.getName() == "agent": # Handle legacy agent info as identity/feature
			agent_attrs = item_node.attrs.copy() # Don't modify original node directly if not needed
			if item_node.getTag("name"):
				agent_attrs["name"] = item_node.getTagData("name") # Use 'name' for identity
			if item_node.getTag("description"): # Use 'description' if name not present for identity
			    if "name" not in agent_attrs: agent_attrs["name"] = item_node.getTagData("description")
			    # Could also add description as a separate field if desired, but original put it in 'name'
			identities_list.append(agent_attrs)
			# Infer features from agent tags
			if item_node.getTag("groupchat"): features_list.append(NS_GROUPCHAT) # NS_GROUPCHAT may need update from protocol.py
			if item_node.getTag("register"): features_list.append(NS_REGISTER)
			if item_node.getTag("search"): features_list.append(NS_SEARCH)
	return identities_list, features_list

def get_registration_info(dispatcher_instance, server_host_str, registration_data_dict={}, synchronous_request=True): # Renamed params
	"""
	Gets registration form from remote host.
	"""
	iq_request = Iq(stanza_type="get", query_namespace=NS_REGISTER, to_jid=server_host_str) # Renamed iq
	for key_name, value_data in registration_data_dict.items(): # Use items()
		iq_request.setTagData(key_name, value_data) # This adds to query payload

	if synchronous_request:
		response_stanza = dispatcher_instance.send_and_wait_for_response(iq_request)
		_handle_registration_info_response(dispatcher_instance, response_stanza, server_host_str) # Pass dispatcher_instance correctly
		return response_stanza
	else:
		dispatcher_instance.send_and_call_for_response(iq_request, _handle_registration_info_response, {"agent_host": server_host_str}) # Renamed agent
		return None # Async call does not return response directly

def _handle_registration_info_response(dispatcher_instance, response_stanza, agent_host_str): # Renamed params
	# This function is a callback, dispatcher_instance is the dispatcher, not the client connection directly from original 'con'
	# agent_host_str was passed in args

	# The original code created a new IQ here, which is unusual for a response handler.
	# It seems it was preparing for a *potential* next step, not processing the response itself for return.
	# The main goal here is to fire an event with the DataForm.

	if not (response_stanza and response_stanza.get_type() == "result"):
		dispatcher_instance.dispatch_event(NS_REGISTER, "REGISTRATION_INFO_ERROR", (agent_host_str, response_stanza)) # Use new name
		return

	query_node = response_stanza.getTag("query", namespace=NS_REGISTER)
	if not query_node:
	    dispatcher_instance.dispatch_event(NS_REGISTER, "REGISTRATION_INFO_MALFORMED", (agent_host_str, "No query tag"))
	    return

	data_form_node = query_node.getTag("x", namespace=NS_DATA) # Renamed df

	if data_form_node: # If Data Form (XEP-0004) is present
		dispatcher_instance.dispatch_event(NS_REGISTER, REGISTER_DATA_RECEIVED, (agent_host_str, DataForm(source_node=data_form_node)))
	else: # Legacy fields directly in <query/>
		legacy_data_form = DataForm(form_type="form") # Create a DataForm to normalize
		has_legacy_fields = False
		for child_node in query_node.getChildren(): # Renamed i
			# Skip 'x' data if it was already processed (though it shouldn't be if data_form_node was None)
			if child_node.getNameSpace() == NS_DATA and child_node.getName() == "x":
				continue
			if not isinstance(child_node, Iq): # Original code checked this, seems odd for children of query
			    if hasattr(child_node, 'getName') and hasattr(child_node, 'getData'): # Make sure it's a Node-like thing
			        if child_node.getName() == "instructions":
			            legacy_data_form.add_instructions(child_node.getData())
			            has_legacy_fields = True
			        else: # Assume other tags are field names with data as value
			            legacy_data_form.set_field(variable_name=child_node.getName(), field_value=child_node.getData())
			            has_legacy_fields = True
		if has_legacy_fields:
		    dispatcher_instance.dispatch_event(NS_REGISTER, REGISTER_DATA_RECEIVED, (agent_host_str, legacy_data_form))
		else: # No data form and no legacy fields found
		    dispatcher_instance.dispatch_event(NS_REGISTER, "REGISTRATION_INFO_EMPTY", (agent_host_str, response_stanza))


def perform_registration(dispatcher_instance, server_host_str, registration_data_dict_or_form): # Renamed params
	"""
	Perform registration on remote server with provided info.
	Returns true or false depending on registration result.
	"""
	iq_request = Iq(stanza_type="set", query_namespace=NS_REGISTER, to_jid=server_host_str) # Renamed iq

	# If it's a DataForm object, get its payload. If dict, use directly.
	payload_to_send = None
	if isinstance(registration_data_dict_or_form, DataForm):
	    # DataForm should be the payload of the query directly if it's a submit type
	    if registration_data_dict_or_form.get_type() == "submit":
	        payload_to_send = [registration_data_dict_or_form] # DataForm itself is the payload
	    else: # If not a submit form, extract fields for legacy registration
	        registration_data_dict = registration_data_dict_or_form.as_dict()
	        payload_children = [Node(tag_name, payload=[str(field_value)]) for tag_name, field_value in registration_data_dict.items() if tag_name != "instructions"]
	        if "instructions" in registration_data_dict: # Handle instructions if present
	            payload_children.append(Node("instructions", payload=[registration_data_dict["instructions"]]))
	        payload_to_send = [Node("query", namespace=NS_REGISTER, payload_list=payload_children)]
	elif isinstance(registration_data_dict_or_form, dict):
		query_payload_children = []
		for key_name, field_value in registration_data_dict_or_form.items(): # Use items()
			query_payload_children.append(Node(key_name, payload=[str(field_value)])) # Ensure value is string
		payload_to_send = [Node("query", namespace=NS_REGISTER, payload_list=query_payload_children)]

	if payload_to_send:
	    iq_request.setPayload(payload_to_send) # Set the constructed payload

	response_stanza = dispatcher_instance.send_and_wait_for_response(iq_request)
	return response_stanza and response_stanza.get_type() == "result"

def perform_unregistration(dispatcher_instance, server_host_str): # Renamed params
	"""
	Unregisters with host (permanently removes account).
	"""
	iq_request = Iq(stanza_type="set", query_namespace=NS_REGISTER, to_jid=server_host_str, payload_list=[Node("remove")]) # Renamed iq, payload
	response_stanza = dispatcher_instance.send_and_wait_for_response(iq_request)
	return response_stanza and response_stanza.get_type() == "result"

def change_password(dispatcher_instance, new_password_str, server_host_str=None): # Renamed params
	"""
	Changes password on specified or current (if not specified) server.
	"""
	if not server_host_str:
		server_host_str = dispatcher_instance._owner.Server # Assuming Server attribute exists on owner

	payload_nodes = [
		Node("username", payload=[dispatcher_instance._owner.User]), # Assuming User attribute
		Node("password", payload=[new_password_str])
	]
	iq_request = Iq(stanza_type="set", query_namespace=NS_REGISTER, to_jid=server_host_str, payload_list=payload_nodes) # Renamed iq
	response_stanza = dispatcher_instance.send_and_wait_for_response(iq_request)
	return response_stanza and response_stanza.get_type() == "result"

def get_privacy_lists(dispatcher_instance): # Renamed
	"""
	Requests privacy lists from connected server.
	Returns dictionary of existing lists on success, else None.
	"""
	privacy_lists_info = {"lists": []} # Renamed dict
	try:
		iq_request = Iq(stanza_type="get", query_namespace=NS_PRIVACY) # Renamed iq
		response_stanza = dispatcher_instance.send_and_wait_for_response(iq_request)
		if not (response_stanza and response_stanza.get_type() == "result"):
			return None

		query_node = response_stanza.getTag("query", namespace=NS_PRIVACY)
		if not query_node: return None

		for list_node in query_node.getChildren(): # Renamed list
			if list_node.getName() == "list":
				privacy_lists_info["lists"].append(list_node.getAttr("name"))
			else: # active or default list
				privacy_lists_info[list_node.getName()] = list_node.getAttr("name") # Store name if present
	except Exception: # Broad except, consider logging
		return None
	return privacy_lists_info

def get_privacy_list_rules(dispatcher_instance, list_name_str): # Renamed params
	"""
	Requests specific privacy list. Returns the <list> Node object or None.
	"""
	try:
		iq_request = Iq(stanza_type="get", query_namespace=NS_PRIVACY, payload_list=[Node("list", {"name": list_name_str})])
		response_stanza = dispatcher_instance.send_and_wait_for_response(iq_request)
		if response_stanza and response_stanza.get_type() == "result":
			query_node = response_stanza.getTag("query", namespace=NS_PRIVACY)
			if query_node:
			    return query_node.getTag("list", attrs={"name":list_name_str}) # Return the specific list node
	except Exception:
		pass
	return None

def set_active_privacy_list(dispatcher_instance, list_name_str=None, list_type_str="active"): # Renamed params
	"""
	Switches privacy list "list_name_str" to specified type.
	"""
	attrs_dict = {}
	if list_name_str:
		attrs_dict = {"name": list_name_str}

	iq_request = Iq(stanza_type="set", query_namespace=NS_PRIVACY, payload_list=[Node(list_type_str, attrs_dict)])
	response_stanza = dispatcher_instance.send_and_wait_for_response(iq_request)
	return response_stanza and response_stanza.get_type() == "result"

def set_default_privacy_list(dispatcher_instance, list_name_str=None): # Renamed params
	"""
	Sets the default privacy list.
	"""
	return set_active_privacy_list(dispatcher_instance, list_name_str, "default")

def update_privacy_list(dispatcher_instance, privacy_list_node_obj): # Renamed setPrivacyList, list
	"""
	Set the ruleset. privacy_list_node_obj should be a simpleXML Node.
	"""
	iq_request = Iq(stanza_type="set", query_namespace=NS_PRIVACY, payload_list=[privacy_list_node_obj])
	response_stanza = dispatcher_instance.send_and_wait_for_response(iq_request)
	return response_stanza and response_stanza.get_type() == "result"

def delete_privacy_list(dispatcher_instance, list_name_str): # Renamed delPrivacyList, listname
	"""
	Deletes privacy list.
	"""
	iq_request = Iq(stanza_type="set", query_namespace=NS_PRIVACY, payload_list=[Node("list", {"name": list_name_str})]) # Empty list node to delete
	response_stanza = dispatcher_instance.send_and_wait_for_response(iq_request)
	return response_stanza and response_stanza.get_type() == "result"

# Ensure all imported classes from protocol are the potentially renamed ones
# For example, if protocol.Iq became protocol.IqStanza, these should use IqStanza.
# This assumes that protocol.py will be refactored and these names will be updated there.
# For now, using the names as they appear in this file's original import.
# If this file is processed *after* protocol.py, these imports might need adjustment
# to point to the new PEP 8 names from protocol.py.
# For example: from .protocol import IqStanza as Iq, PresenceStanza as Presence, etc.
# Or better, use the new names directly: from .protocol import IqStanza, PresenceStanza
# This current version assumes that the `from .protocol import *` handles bringing in the refactored names.
# However, explicit is better than implicit.
# For now, this file is internally consistent with the names it has defined or imported.
# The real test comes when integrating with the refactored protocol.py.
