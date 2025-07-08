## Ad-Hoc Command manager

## Mike Albon (c) 5th January 2005

##   This program is free software; you can redistribute it and/or modify
##   it under the terms of the GNU General Public License as published by
##   the Free Software Foundation; either version 2, or (at your option)
##   any later version.
##
##   This program is distributed in the hope that it will be useful,
##   but WITHOUT ANY WARRANTY; without even the implied warranty of
##   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##   GNU General Public License for more details.

# $Id: commands.py, v1.18 2013/11/05 alkorgun Exp $

"""
This module is an ad-hoc command processor for xmpppy. It uses the plug-in mechanism.
It depends on a DISCO browser manager.
"""

from .plugin import PlugIn
# Assuming protocol classes will be renamed (e.g., Iq->IqStanza, Error->ErrorStanza)
from .protocol import Iq, Node, NodeProcessed, ErrorStanza, DataForm, \
                      NS_COMMANDS, NS_DATA, \
                      ERR_BAD_REQUEST, ERR_ITEM_NOT_FOUND, ERR_FEATURE_NOT_IMPLEMENTED

# Assuming browser class will be DiscoBrowser from a refactored browser.py
# from .browser import DiscoBrowser

DEBUG_SCOPE_COMMANDS = "commands"

class AdHocCommandManager(PlugIn): # Renamed Commands
	"""
	Manages ad-hoc commands, integrating with a DiscoBrowser instance for discovery.
	"""
	def __init__(self, disco_browser_instance): # Renamed browser
		"""
		Initialises class, storing the DiscoBrowser instance.
		"""
		PlugIn.__init__(self)
		self.DEBUG_LINE_PREFIX = DEBUG_SCOPE_COMMANDS
		self._exported_methods = [] # No methods typically exported by a manager like this
		# _handlers: {target_jid_str: {command_node_name: {"disco": disco_handler, "execute": execute_handler}}}
		self._handlers = {"": {}} # Default handlers for commands on the component itself
		self._disco_browser = disco_browser_instance

	def plugin(self, client_or_component_instance): # Renamed owner
		"""
		Registers IQ handlers for command execution and discovery with the component's dispatcher.
		"""
		# _owner is set by PlugIn base
		self._owner.RegisterHandler("iq", self._handle_command_iq, stanza_type="set", namespace=NS_COMMANDS)
		self._owner.RegisterHandler("iq", self._handle_command_iq, stanza_type="get", namespace=NS_COMMANDS) # Allow gets for initial step?
		# Register this manager's disco handler with the main DiscoBrowser for the command namespace
		self._disco_browser.set_disco_handler(self._handle_disco_query_for_commands_node, node=NS_COMMANDS, target_jid_str="")


	def plugout(self):
		"""
		Removes handlers from the session.
		"""
		self._owner.UnregisterHandler("iq", self._handle_command_iq, stanza_type="set", namespace=NS_COMMANDS)
		self._owner.UnregisterHandler("iq", self._handle_command_iq, stanza_type="get", namespace=NS_COMMANDS)
		# Unregister from disco browser for all JIDs this manager was handling commands for
		for jid_str in list(self._handlers.keys()): # Iterate over copy if modifying
			self._disco_browser.delete_disco_handler(disco_node_str=NS_COMMANDS, target_jid_str=jid_str)


	def _handle_command_iq(self, dispatcher_instance, command_iq_stanza): # Renamed conn, request
		"""
		Internal method to route command execution requests to the appropriate handler.
		"""
		target_jid_str = str(command_iq_stanza.get_to()) # JID the command is addressed to
		command_node = command_iq_stanza.getTag("command", namespace=NS_COMMANDS)

		if not command_node:
			dispatcher_instance.send(ErrorStanza(command_iq_stanza, ERR_BAD_REQUEST))
			raise NodeProcessed()

		command_node_name = command_node.getAttr("node")
		if not command_node_name: # Node attribute is mandatory for specific commands
			dispatcher_instance.send(ErrorStanza(command_iq_stanza, ERR_BAD_REQUEST("Command node attribute missing")))
			raise NodeProcessed()

		# Check for specific JID handlers first, then default "" JID
		handler_set = self._handlers.get(target_jid_str, self._handlers.get("", {}))

		if command_node_name in handler_set:
			# Call the 'execute' method of the registered command handler object/dict
			command_handler_entry = handler_set[command_node_name]
			if "execute" in command_handler_entry and callable(command_handler_entry["execute"]):
				command_handler_entry["execute"](dispatcher_instance, command_iq_stanza)
			else:
				self.DEBUG(f"No executable 'execute' method for command {command_node_name} on JID {target_jid_str}", "error")
				dispatcher_instance.send(ErrorStanza(command_iq_stanza, ERR_ITEM_NOT_FOUND("Command execution handler not found")))
		else:
			dispatcher_instance.send(ErrorStanza(command_iq_stanza, ERR_ITEM_NOT_FOUND("Command not found at this JID/node")))
		raise NodeProcessed()

	def _handle_disco_query_for_commands_node(self, dispatcher_instance, disco_iq_request, disco_query_type): # Renamed conn, request, typ
		"""
		Internal method to process service discovery requests for the ad-hoc commands node (NS_COMMANDS).
		"""
		if disco_query_type == "items":
			items_list = [] # Renamed list
			# JID to which the disco query is addressed (could be component itself or a specific JID it handles)
			queried_jid_str = str(disco_iq_request.get_to())

			# Gather commands registered for the specific JID, or default JID if specific not found
			specific_jid_commands = self._handlers.get(queried_jid_str, {})
			default_jid_commands = self._handlers.get("", {})

			# Combine and de-duplicate command names (node names)
			# Prefer specific JID handlers over default ones if names clash (though unlikely with this structure)
			all_command_nodes_for_jid = {} # {command_node_name: handler_entry}
			all_command_nodes_for_jid.update(default_jid_commands)
			all_command_nodes_for_jid.update(specific_jid_commands) # Specific overrides default

			if all_command_nodes_for_jid:
				for command_node_name_str, handler_entry in all_command_nodes_for_jid.items():
					if "disco" in handler_entry and callable(handler_entry["disco"]):
						# The 'list' type for disco handler is a custom convention here
						# It should return a tuple: (jid_for_command, node_name, natural_name)
						list_item_info = handler_entry["disco"](dispatcher_instance, disco_iq_request, "list")
						if list_item_info and len(list_item_info) == 3:
							items_list.append(Node(tag="item", attrs={"jid": list_item_info[0],
							                                       "node": list_item_info[1],
							                                       "name": list_item_info[2]}))
				reply_iq = disco_iq_request.build_reply("result")
				if disco_iq_request.get_query_node_attribute(): # Use new method name
					reply_iq.set_query_node_attribute(disco_iq_request.get_query_node_attribute()) # Use new method name
				reply_iq.set_query_payload(items_list) # Use new method name
				dispatcher_instance.send(reply_iq)
			else: # No commands found for this JID or default
				dispatcher_instance.send(ErrorStanza(disco_iq_request, ERR_ITEM_NOT_FOUND))
			raise NodeProcessed()

		elif disco_query_type == "info":
			# This is info about the NS_COMMANDS node itself, not a specific command
			return {
				"ids": [{"category": "automation", "type": "command-list", "name": "Ad-Hoc Commands"}],
				"features": [NS_COMMANDS] # It supports the command namespace
			}
		return None # Should not happen for items/info

	def add_command(self, command_node_name_str, disco_handler_func, execute_handler_func, target_jid_str=""): # Renamed params
		"""
		Adds a new command.
		"""
		self.DEBUG(f"Adding command '{command_node_name_str}' for JID '{target_jid_str or 'default'}'", "info")
		if target_jid_str not in self._handlers:
			self._handlers[target_jid_str] = {}
			# Register a general disco handler for NS_COMMANDS *on this specific JID* if it's not the default "" JID
			if target_jid_str:
			    self._disco_browser.set_disco_handler(self._handle_disco_query_for_commands_node, node=NS_COMMANDS, target_jid_str=target_jid_str)

		if command_node_name_str in self._handlers[target_jid_str]:
			raise NameError(f"Command '{command_node_name_str}' already exists for JID '{target_jid_str}'")

		self._handlers[target_jid_str][command_node_name_str] = {"disco": disco_handler_func, "execute": execute_handler_func}
		# Register the specific command's disco handler under its own node
		self._disco_browser.set_disco_handler(disco_handler_func, node=command_node_name_str, target_jid_str=target_jid_str)

	def delete_command(self, command_node_name_str, target_jid_str=""): # Renamed params
		"""
		Removes a command.
		"""
		if target_jid_str not in self._handlers:
			raise NameError(f"JID '{target_jid_str}' not found in command handlers.")
		if command_node_name_str not in self._handlers[target_jid_str]:
			raise NameError(f"Command '{command_node_name_str}' not found for JID '{target_jid_str}'.")

		self.DEBUG(f"Deleting command '{command_node_name_str}' for JID '{target_jid_str or 'default'}'", "info")
		# disco_handler_to_remove = self._handlers[target_jid_str][command_node_name_str]["disco"] # Not needed if just deleting
		del self._handlers[target_jid_str][command_node_name_str]
		self._disco_browser.delete_disco_handler(disco_node_str=command_node_name_str, target_jid_str=target_jid_str)

		# If this was the last command for a specific JID (not default), remove its NS_COMMANDS disco handler
		if target_jid_str and not self._handlers[target_jid_str]:
		    del self._handlers[target_jid_str]
		    self._disco_browser.delete_disco_handler(disco_node_str=NS_COMMANDS, target_jid_str=target_jid_str)


	def get_command_handlers(self, command_node_name_str, target_jid_str=""): # Renamed params
		"""
		Returns the dictionary {"disco": disco_handler_func, "execute": execute_handler_func}.
		"""
		if target_jid_str not in self._handlers:
			raise NameError(f"JID '{target_jid_str}' not found.")
		if command_node_name_str not in self._handlers[target_jid_str]:
			# Fallback to default JID if not found for specific JID
			if "" in self._handlers and command_node_name_str in self._handlers[""]:
			    return self._handlers[""][command_node_name_str]
			raise NameError(f"Command '{command_node_name_str}' not found for JID '{target_jid_str}' or default.")
		return self._handlers[target_jid_str][command_node_name_str]

class AdHocCommandHandlerPrototype(PlugIn): # Renamed Command_Handler_Prototype
	"""
	Prototype for command handlers.
	"""
	command_name_node = "examplecommand" # Renamed name
	command_description = "An example command" # Renamed description
	disco_supported_features = [NS_COMMANDS, NS_DATA] # Renamed discofeatures

	# initial_actions_map: {"action_name": self.method_for_action}
	# Example: {"execute": self._execute_initial_stage}
	initial_actions_map = {} # Renamed initial

	def __init__(self, target_jid_str=""): # Renamed jid
		PlugIn.__init__(self)
		self.DEBUG_LINE_PREFIX = DEBUG_SCOPE_COMMANDS # Class attribute for debug scope
		self._session_id_counter = 0 # Renamed sessioncount, count
		self.active_sessions = {} # Renamed sessions: {session_id: {"jid": from_jid, "actions": {...}, "data":{...}}}

		self.static_disco_info = { # Renamed discoinfo
			"ids": [{
				"category": "automation",
				"type": "command-node",
				"name": self.command_description
			}],
			"features": self.disco_supported_features
		}
		self._target_jid_str = target_jid_str # JID this command handler is registered for (empty for default)

	def plugin(self, command_manager_instance): # Renamed owner
		"""
		Plugs this command handler into an AdHocCommandManager instance.
		"""
		self._command_manager = command_manager_instance # Renamed _commands
		self._owner = command_manager_instance._owner # The XMPP client/component instance
		self._command_manager.add_command(
		    self.command_name_node,
		    self._handle_disco_query,
		    self.execute_command_stage,
		    jid=self._target_jid_str
		)

	def plugout(self):
		"""
		Removes this command from the AdHocCommandManager.
		"""
		if hasattr(self, '_command_manager') and self._command_manager:
			self._command_manager.delete_command(self.command_name_node, jid=self._target_jid_str)

	def _generate_session_id(self): # Renamed getSessionID
		""" Returns a unique ID for the command session. """
		self._session_id_counter += 1
		return f"cmd-{self.command_name_node}-{self._session_id_counter}"

	def execute_command_stage(self, dispatcher_instance, command_iq_stanza): # Renamed Execute, conn, request
		"""
		Handles command execution IQs, routing to appropriate stage methods.
		"""
		command_node = command_iq_stanza.getTag("command", namespace=NS_COMMANDS)
		session_id = command_node.getAttr("sessionid")
		action_requested = command_node.getAttr("action")

		from_jid_str = str(command_iq_stanza.get_from())

		if action_requested is None: # If no action, default to "execute" for new session or current default
		    action_requested = "execute"

		if session_id and session_id in self.active_sessions:
			session_data = self.active_sessions[session_id]
			if session_data["jid_str"] == from_jid_str:
				if action_requested in session_data["actions_map"]: # Renamed actions
					# Execute the method associated with the action
					session_data["actions_map"][action_requested](dispatcher_instance, command_iq_stanza, session_id, session_data)
				else:
					dispatcher_instance.send(ErrorStanza(command_iq_stanza, ERR_BAD_REQUEST("Invalid action for current session stage.")))
			else: # JID mismatch for session ID
				dispatcher_instance.send(ErrorStanza(command_iq_stanza, ERR_BAD_REQUEST("Session ID belongs to another JID.")))
		elif session_id is None: # New session
			if action_requested in self.initial_actions_map:
				# Call the initial stage handler (e.g., self.initial_actions_map["execute"] might be self._execute_first_stage)
				self.initial_actions_map[action_requested](dispatcher_instance, command_iq_stanza, None, None) # No session_id or session_data yet
			else:
				dispatcher_instance.send(ErrorStanza(command_iq_stanza, ERR_BAD_REQUEST("Invalid initial action.")))
		else: # Session ID provided but not found
			dispatcher_instance.send(ErrorStanza(command_iq_stanza, ERR_ITEM_NOT_FOUND("Invalid session ID.")))
		raise NodeProcessed()

	def _handle_disco_query(self, dispatcher_instance, disco_iq_request, disco_query_type_str): # Renamed _DiscoHandler, conn, request, type
		"""
		Handles discovery events for this specific command node.
		"""
		if disco_query_type_str == "list": # This command node itself is an item.
			# Returns tuple: (jid_of_command_provider, command_node_name, natural_language_name)
			# jid_of_command_provider is usually the component's JID or where the command is hosted.
			# For a command handled by the component itself, this would be the component's JID.
			# If this command is registered for a specific JID via self._target_jid_str, use that.
			command_provider_jid = self._target_jid_str if self._target_jid_str else str(disco_iq_request.get_to())
			return (command_provider_jid, self.command_name_node, self.command_description)
		elif disco_query_type_str == "items": # A command node itself typically doesn't have sub-items.
			return [] # No sub-items for a specific command node by default.
		elif disco_query_type_str == "info": # Info about this command.
			return self.static_disco_info # Return pre-formatted dict
		return None # Should not be called with other types by AdHocCommandManager

class TestAdHocCommand(AdHocCommandHandlerPrototype): # Renamed TestCommand
	"""
	Example command class.
	"""
	command_name_node = "testcommand"
	command_description = "A Noddy Example Command for XMPPPy"
	# discofeatures is inherited

	def __init__(self, target_jid_str=""): # Renamed jid
		AdHocCommandHandlerPrototype.__init__(self, target_jid_str)
		# Map initial "execute" action to the first stage method
		self.initial_actions_map = {"execute": self._execute_first_stage}

	def _execute_first_stage(self, dispatcher_instance, command_iq_stanza, _session_id, _session_data): # Renamed cmdFirstStage, conn, request
		# New session, _session_id and _session_data will be None from execute_command_stage
		session_id = self._generate_session_id() # Renamed getSessionID
		self.active_sessions[session_id] = {
			"jid_str": str(command_iq_stanza.get_from()),
			"actions_map": { # Possible actions from this stage
				"cancel": self._execute_cancel_stage, # Renamed cmdCancel
				"next": self._execute_second_stage,   # Renamed cmdSecondStage
				"execute": self._execute_second_stage # Default action if 'next' is implied
			},
			"data": {"calculation_type": None} # Store form data here
		}

		reply_iq = command_iq_stanza.build_reply("result")
		data_form = DataForm(form_type="form", title_text="Select type of operation", # Renamed title
			data_payload=[ # Renamed data
				"Use the combobox to select the type of calculation you would like to do, then click Next.",
				DataFormField(variable_name="calctype", description_text="Calculation Type", # Renamed name, desc, typ
					field_value=self.active_sessions[session_id]["data"]["calculation_type"], # Use new structure
					options_list=[ # Renamed options
						["circlediameter", "Calculate the Diameter of a circle"],
						["circlearea", "Calculate the area of a circle"]
					],
					field_type="list-single",
					is_required=True
			)])

		command_reply_node = Node("command",
			namespace=NS_COMMANDS,
			attrs={
				"node": self.command_name_node, # Use class attribute
				"sessionid": session_id,
				"status": "executing"
			},
			payload_list=[Node("actions", attrs={"execute": "next"}, payload_list=[Node("next")]), data_form] # Renamed replypayload
		)
		reply_iq.addChild(node=command_reply_node)
		self._owner.send(reply_iq) # _owner is the client/component instance
		raise NodeProcessed()

	def _execute_second_stage(self, dispatcher_instance, command_iq_stanza, session_id, session_data): # Renamed cmdSecondStage
		command_node = command_iq_stanza.getTag("command")
		data_form_node = command_node.getTag("x", namespace=NS_DATA)
		if not data_form_node:
		    dispatcher_instance.send(ErrorStanza(command_iq_stanza, ERR_BAD_REQUEST("Data form missing.")))
		    raise NodeProcessed()

		submitted_form = DataForm(source_node=data_form_node) # Renamed form
		calc_type_field = submitted_form.get_field("calctype") # Use new name
		if not calc_type_field or not calc_type_field.get_value():
		    # Re-present first stage if type not selected (or handle error)
		    self._execute_first_stage(dispatcher_instance, command_iq_stanza, None, None) # Treat as new effectively
		    return

		session_data["data"]["calculation_type"] = calc_type_field.get_value()
		session_data["actions_map"] = {
			"cancel": self._execute_cancel_stage,
			"previous": self._execute_first_stage, # Go back to first stage
			"execute": self._execute_third_stage,  # Default action for this stage
			"next": self._execute_third_stage     # Explicit next
		}
		self._send_second_stage_reply(dispatcher_instance, command_iq_stanza, session_id) # Renamed cmdSecondStageReply

	def _send_second_stage_reply(self, dispatcher_instance, original_iq_stanza, session_id): # Renamed cmdSecondStageReply
		reply_iq = original_iq_stanza.build_reply("result")
		data_form = DataForm(form_type="form", title_text="Enter the radius",
			data_payload=[
				"Enter the radius of the circle (numbers only)",
				DataFormField(description_text="Radius", variable_name="radius", field_type="text-single", is_required=True)
			])

		actions_node = Node("actions", attrs={"execute": "next"}, payload_list=[Node("next"), Node("prev")]) # 'complete' might be better if this is final input

		command_reply_node = Node("command",
			namespace=NS_COMMANDS,
			attrs={
				"node": self.command_name_node,
				"sessionid": session_id,
				"status": "executing"
			},
			payload_list=[actions_node, data_form]
		)
		reply_iq.addChild(node=command_reply_node)
		self._owner.send(reply_iq)
		raise NodeProcessed()

	def _execute_third_stage(self, dispatcher_instance, command_iq_stanza, session_id, session_data): # Renamed cmdThirdStage
		command_node = command_iq_stanza.getTag("command")
		data_form_node = command_node.getTag("x", namespace=NS_DATA)
		if not data_form_node:
		    dispatcher_instance.send(ErrorStanza(command_iq_stanza, ERR_BAD_REQUEST("Data form missing.")))
		    raise NodeProcessed()

		submitted_form = DataForm(source_node=data_form_node) # Renamed form
		radius_field = submitted_form.get_field("radius")

		radius_val = 0.0 # Renamed numb
		try:
			radius_val = float(radius_field.get_value())
		except (ValueError, TypeError, AttributeError): # Catch if field missing or not a number
			# Invalid input, re-present the second stage form
			self.DEBUG("Invalid radius input, re-sending second stage.", "warn")
			session_data["actions_map"]["execute"] = self._execute_third_stage # Ensure execute maps to current stage for retry
			self._send_second_stage_reply(dispatcher_instance, command_iq_stanza, session_id)
			return # NodeProcessed is raised in _send_second_stage_reply

		from math import pi # Import math if not already
		calculated_result = 0.0 # Renamed result
		if session_data["data"]["calculation_type"] == "circlearea":
			calculated_result = (radius_val ** 2) * pi
		else: # Default to circlediameter (or circumference based on original code's math)
			calculated_result = radius_val * 2 * pi # This is circumference, not diameter. Original code was 2*pi*r

		reply_iq = command_iq_stanza.build_reply("result")
		result_form = DataForm(form_type="result", data_payload=[DataFormField(variable_name="result", description_text="Calculation Result", field_value=str(calculated_result))])

		command_reply_node = Node("command",
			namespace=NS_COMMANDS,
			attrs={
				"node": self.command_name_node,
				"sessionid": session_id,
				"status": "completed" # Command finished
			},
			payload_list=[result_form]
		)
		reply_iq.addChild(node=command_reply_node)
		self._owner.send(reply_iq)
		del self.active_sessions[session_id] # Clean up session
		raise NodeProcessed()

	def _execute_cancel_stage(self, dispatcher_instance, command_iq_stanza, session_id, _session_data): # Renamed cmdCancel
		reply_iq = command_iq_stanza.build_reply("result")
		command_reply_node = Node("command",
			namespace=NS_COMMANDS,
			attrs={
				"node": self.command_name_node,
				"sessionid": session_id,
				"status": "canceled" # Corrected spelling
			})
		reply_iq.addChild(node=command_reply_node)
		self._owner.send(reply_iq)
		if session_id in self.active_sessions: # Clean up session
			del self.active_sessions[session_id]
		raise NodeProcessed()
