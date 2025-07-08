##   roster.py
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

# $Id: roster.py, v1.21 2013/10/21 alkorgun Exp $

"""
Simple roster implementation. Can be used though for different tasks like
mass-renaming of contacts.
"""

from .plugin import PlugIn
from .protocol import Iq, Presence, Node, NodeProcessed, Jid, NS_ROSTER # Assuming these are (or will be) PEP 8 compliant

DEBUG_SCOPE_ROSTER = "roster" # Define as a global constant

class RosterManager(PlugIn): # Renamed Roster
	"""
	Defines a plenty of methods that will allow you to manage roster.
	Also automatically track presences from remote JIDs taking into
	account that every JID can have multiple resources connected. Does not
	currently support "error" presences.
	You can also use mapping interface for access to the internal representation of
	contacts in roster.
	"""
	def __init__(self):
		"""
		Init internal variables.
		"""
		PlugIn.__init__(self)
		self.DEBUG_LINE_PREFIX = DEBUG_SCOPE_ROSTER # Use new constant
		self._roster_data = {} # Renamed _data
		self.roster_received_flag = None # Renamed set (None: not requested, 0: requested, 1: received)
		self._exported_methods = [self.get_roster_handler_instance] # Renamed getRoster

	def plugin(self, client_instance, request_roster_on_plugin=True): # Renamed owner, request
		"""
		Register presence and subscription trackers in the owner's dispatcher.
		Also request roster from server if the "request_roster_on_plugin" argument is set.
		Used internally.
		"""
		# _owner is set by PlugIn base
		self._owner.RegisterHandler("iq", self._handle_roster_iq, stanza_type="result", namespace=NS_ROSTER) # Renamed RosterIqHandler, typ, ns
		self._owner.RegisterHandler("iq", self._handle_roster_iq, stanza_type="set", namespace=NS_ROSTER)    # Renamed RosterIqHandler, typ, ns
		self._owner.RegisterHandler("presence", self._handle_presence_stanza) # Renamed PresenceHandler
		if request_roster_on_plugin:
			self.request_roster_from_server() # Renamed Request

	def request_roster_from_server(self, force_request=False): # Renamed Request, force
		"""
		Request roster from server if it were not yet requested
		(or if the "force_request" argument is set).
		"""
		if self.roster_received_flag is None: # Not requested yet
			self.roster_received_flag = 0 # Mark as requested
		elif not force_request and self.roster_received_flag == 1: # Already received and not forcing
			return

		self._owner.send(Iq(stanza_type="get", query_namespace=NS_ROSTER)) # Use renamed Iq
		self.DEBUG("Roster requested from server", "start")

	def get_roster_handler_instance(self): # Renamed getRoster
		"""
		Requests roster from server if neccessary and returns self (the RosterManager instance).
		"""
		if self.roster_received_flag != 1: # If not received (None or 0)
			self.request_roster_from_server()

		timeout_counter = 250 # Wait up to 25 seconds (250 * 0.1s)
		while self.roster_received_flag != 1 and timeout_counter > 0:
			self._owner.Process(0.1) # Process with a small timeout
			timeout_counter -=1
		if self.roster_received_flag != 1:
		    self.DEBUG("Timeout or failure waiting for roster to be populated.", "error")
		    # Optionally raise an error or return None, depending on desired behavior
		return self

	def _handle_roster_iq(self, dispatcher_instance, iq_stanza): # Renamed RosterIqHandler, dis, stanza
		"""
		Handles incoming roster IQ stanzas (both 'result' from a get, and 'set' for pushes).
		"""
		query_node = iq_stanza.getTag("query", namespace=NS_ROSTER)
		if not query_node:
		    self.DEBUG("Roster IQ stanza missing query element.", "warn")
		    raise NodeProcessed() # Stop processing if malformed

		for item_node in query_node.getTags("item"): # Renamed item
			jid_str = item_node.getAttr("jid")
			if not jid_str: continue # Malformed item

			if item_node.getAttr("subscription") == "remove":
				if jid_str in self._roster_data:
					del self._roster_data[jid_str]
					self.DEBUG(f"Roster item {jid_str} removed.", "ok")
				# For a roster remove, we might not want to raise NodeProcessed immediately if part of a larger set.
				# However, the original code did. For now, let's assume individual item processing.
				# If this is part of a multi-item push, this behavior might be too aggressive.
				# For a roster 'set' that *only* contains a remove, this is fine.
				# If it's a roster 'result', a 'remove' item means it's no longer there.
				# The original "raise NodeProcessed() # a MUST" implies this handler fully manages roster items.
				# We should continue processing other items in the same push.
				continue # Process next item in the IQ

			self.DEBUG(f"Processing roster item {jid_str}...", "ok")
			if jid_str not in self._roster_data:
				self._roster_data[jid_str] = {"resources": {}} # Initialize if new

			self._roster_data[jid_str]["name"] = item_node.getAttr("name")
			self._roster_data[jid_str]["ask"] = item_node.getAttr("ask")
			self._roster_data[jid_str]["subscription"] = item_node.getAttr("subscription")

			item_groups = [] # Renamed groups
			for group_node in item_node.getTags("group"): # Renamed group
				item_groups.append(group_node.getData())
			self._roster_data[jid_str]["groups"] = item_groups

			# Ensure 'resources' dict exists, might be new item
			if "resources" not in self._roster_data[jid_str]:
				self._roster_data[jid_str]["resources"] = {}

		# Add self to roster (original behavior)
		# This might not be standard for all XMPP servers but reflects original logic
		self_jid_str = "@".join((self._owner.User, self._owner.Server)) # Assuming User and Server are set on owner
		if self_jid_str not in self._roster_data: # Only add if not already (e.g. from a push)
		    self._roster_data[self_jid_str] = {"resources": {}, "name": None, "ask": None, "subscription": "both", "groups": []} # Assuming 'both' for self

		self.roster_received_flag = 1 # Mark roster as received/processed
		raise NodeProcessed() # Indicates this handler fully processed the roster IQ

	def _handle_presence_stanza(self, dispatcher_instance, presence_stanza): # Renamed PresenceHandler, dis, pres
		"""
		Presence tracker. Used internally for setting items' resources state.
		"""
		from_jid_obj = Jid(presence_stanza.get_from()) # Renamed jid, use Jid object
		bare_jid_str = from_jid_obj.get_stripped_jid() # Use new method name
		resource_str = from_jid_obj.get_resource() # Use new method name

		if bare_jid_str not in self._roster_data:
			# Automatically add unknown entries to track their presence, marked as not in roster
			self._roster_data[bare_jid_str] = {
			    "name": None, "ask": None, "subscription": "none",
			    "groups": ["Not in Roster"], "resources": {}
			}
			self.DEBUG(f"Presence from unknown JID {bare_jid_str}, adding to track.", "info")

		roster_item = self._roster_data[bare_jid_str] # Renamed item
		stanza_type = presence_stanza.get_type() # Renamed typ

		if not stanza_type: # Available presence
			self.DEBUG(f"Processing available presence for {bare_jid_str}/{resource_str}", "ok")
			resource_data = { # Renamed res
			    "show": presence_stanza.get_show() or "available", # Default to 'available' if no show
			    "status": presence_stanza.get_status(),
			    "priority": presence_stanza.get_priority() or "0", # Default priority 0
			    "timestamp": presence_stanza.get_timestamp() or time.strftime("%Y%m%dT%H:%M:%S", time.gmtime()) # Ensure timestamp
			}
			roster_item["resources"][resource_str] = resource_data
		elif stanza_type == "unavailable":
			if resource_str in roster_item["resources"]:
				del roster_item["resources"][resource_str]
				self.DEBUG(f"Resource {resource_str} for {bare_jid_str} became unavailable.", "ok")
		# TODO: Handle presence type="error" (original comment)
		# TODO: Handle subscription-related presence types (subscribe, subscribed, unsubscribe, unsubscribed)
		# This handler currently only updates availability status. Subscription changes are via IQ.
		raise NodeProcessed()


	def _get_roster_item_data(self, jid_str, data_key_name): # Renamed _getItemData, jid, dataname
		"""
		Return specific data field for a bare JID from the roster.
		"""
		bare_jid = Jid(jid_str).get_stripped_jid() # Ensure bare JID
		if bare_jid in self._roster_data:
			return self._roster_data[bare_jid].get(data_key_name)
		return None

	def _get_roster_resource_data(self, full_jid_str, data_key_name): # Renamed _getResourceData, jid, dataname
		"""
		Return specific data field for a resource of a JID from the roster.
		If no resource specified in full_jid_str, finds the one with highest priority.
		"""
		jid_obj = Jid(full_jid_str)
		bare_jid = jid_obj.get_stripped_jid()
		resource_part = jid_obj.get_resource()

		if bare_jid in self._roster_data:
			item_resources = self._roster_data[bare_jid].get("resources", {})
			if not item_resources: return None

			target_resource_str = resource_part
			if not target_resource_str: # No resource specified, find highest priority
				highest_priority = -129 # Min XMPP priority is -128
				best_resource = None
				for res_name, res_data in item_resources.items():
					try:
						current_priority = int(res_data.get("priority", "0"))
						if current_priority > highest_priority:
							highest_priority = current_priority
							best_resource = res_name
					except ValueError:
						continue # Skip if priority is not a valid int
				target_resource_str = best_resource

			if target_resource_str and target_resource_str in item_resources:
				return item_resources[target_resource_str].get(data_key_name)
		return None

	def delete_roster_item(self, jid_str): # Renamed delItem, jid
		""" Delete contact "jid_str" from roster. """
		item_node_payload = Node("item", attrs={"jid": jid_str, "subscription": "remove"})
		iq_request = Iq(stanza_type="set", query_namespace=NS_ROSTER, payload_list=[item_node_payload])
		self._owner.send(iq_request)

	def get_ask_status(self, jid_str): # Renamed getAsk, jid
		""" Returns "ask" value of contact "jid_str" (e.g., 'subscribe'). """
		return self._get_roster_item_data(jid_str, "ask")

	def get_item_groups(self, jid_str): # Renamed getGroups, jid
		""" Returns groups list that contact "jid_str" belongs to. """
		return self._get_roster_item_data(jid_str, "groups") or []

	def get_item_name(self, jid_str): # Renamed getName, jid
		""" Returns name of contact "jid_str". """
		return self._get_roster_item_data(jid_str, "name")

	def get_resource_priority(self, full_jid_str): # Renamed getPriority, jid
		""" Returns priority of contact "full_jid_str". """
		priority_str = self._get_roster_resource_data(full_jid_str, "priority")
		return int(priority_str) if priority_str and priority_str.lstrip('-').isdigit() else 0


	def get_raw_roster_data(self): # Renamed getRawRoster
		""" Returns roster representation in internal format. """
		return self._roster_data

	def get_raw_roster_item(self, jid_str): # Renamed getRawItem, jid
		""" Returns roster item "jid_str" representation in internal format. """
		bare_jid = Jid(jid_str).get_stripped_jid()
		return self._roster_data.get(bare_jid)

	def get_resource_show_status(self, full_jid_str): # Renamed getShow, jid
		""" Returns "show" value of contact "full_jid_str". """
		return self._get_roster_resource_data(full_jid_str, "show")

	def get_resource_status_message(self, full_jid_str): # Renamed getStatus, jid
		""" Returns "status" value of contact "full_jid_str". """
		return self._get_roster_resource_data(full_jid_str, "status")

	def get_item_subscription(self, jid_str): # Renamed getSubscription, jid
		""" Returns "subscription" value of contact "jid_str". """
		return self._get_roster_item_data(jid_str, "subscription")

	def get_item_resources(self, jid_str): # Renamed getResources, jid
		""" Returns list of connected resources of contact "jid_str". """
		item_data = self._get_roster_item_data(jid_str, "resources")
		return list(item_data.keys()) if item_data else []

	def set_roster_item(self, jid_str, item_name=None, group_list=[]): # Renamed setItem, jid, name, groups
		""" Creates/updates roster item "jid_str" and sets its name and groups list. """
		iq_request = Iq(stanza_type="set", query_namespace=NS_ROSTER) # Renamed iq
		query_node = iq_request.getTag("query") # Renamed query

		attributes_dict = {"jid": jid_str} # Renamed attrs
		if item_name is not None: # Allow empty string for name
			attributes_dict["name"] = item_name

		item_node_obj = query_node.setTag("item", attrs=attributes_dict) # Renamed item
		for group_name in group_list: # Renamed group
			item_node_obj.addChild(node=Node("group", payload=[group_name]))
		self._owner.send(iq_request)

	def get_all_roster_jids(self): # Renamed getItems
		""" Return list of all [bare] JIDs that the roster is currently tracks. """
		return list(self._roster_data.keys())

	def keys(self):
		""" Same as get_all_roster_jids. Provided for dictionary-like interface. """
		return list(self._roster_data.keys())

	def __getitem__(self, jid_key_str): # Renamed item
		""" Get the contact in the internal format. Raises KeyError if JID "jid_key_str" is not in roster. """
		# Assuming jid_key_str is bare JID for direct dict access
		return self._roster_data[jid_key_str]

	def get_item(self, jid_key_str): # Renamed getItem, item
		""" Get the contact in the internal format (or None if JID "jid_key_str" is not in roster). """
		return self._roster_data.get(Jid(jid_key_str).get_stripped_jid()) # Ensure bare JID for lookup


	def send_subscription_request(self, to_jid_str): # Renamed Subscribe, jid
		""" Send subscription request to JID "to_jid_str". """
		self._owner.send(Presence(to_jid=to_jid_str, stanza_type="subscribe")) # Use new name

	def send_unsubscription_request(self, to_jid_str): # Renamed Unsubscribe, jid
		""" Ask for removing our subscription for JID "to_jid_str". """
		self._owner.send(Presence(to_jid=to_jid_str, stanza_type="unsubscribe")) # Use new name

	def send_authorization_approval(self, to_jid_str): # Renamed Authorize, jid
		""" Authorise JID "to_jid_str". Works only if this JID requested auth previously. """
		self._owner.send(Presence(to_jid=to_jid_str, stanza_type="subscribed")) # Use new name

	def send_authorization_removal(self, to_jid_str): # Renamed Unauthorize, jid
		""" Unauthorize JID "to_jid_str". Use for declining auth request or removing existing authorization. """
		self._owner.send(Presence(to_jid=to_jid_str, stanza_type="unsubscribed")) # Use new name
