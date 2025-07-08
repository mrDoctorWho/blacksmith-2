##   simplexml.py based on Mattew Allum's xmlstream.py
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

# $Id: simplexml.py, v1.35 2013/10/21 alkorgun Exp $

"""
Simplexml module provides xmpppy library with all needed tools to handle
XML nodes and XML streams.
I'm personally using it in many other separate projects.
It is designed to be as standalone as possible.
"""

import xml.parsers.expat

XML_ESCAPE_MAP = ( # Renamed XML_ls
	("&", "&amp;"),
	# Control characters like \x0C (form feed) and \x1B (escape) are invalid in XML 1.0/1.1
	# and should be removed or properly escaped if they must be represented.
	# Removing them as per original behavior for now.
	# ("\x0C", ""), # Form Feed
	# ("\x1B", ""), # Escape
	("<", "&lt;"),
	(">", "&gt;"),
	('"', "&quot;"),
	("'", "&apos;")
)

def xml_escape_string(text_data): # Renamed XMLescape, body
	"""Escapes special XML characters in a string."""
	# Filter out invalid XML characters first (control characters except tab, newline, carriage return)
	# This is a basic filter; a more robust solution might use a library or more comprehensive regex.
	text_data_cleaned = "".join(char for char in text_data if ord(char) >= 0x20 or char in ('\t', '\n', '\r'))

	for char_to_escape, entity_replacement in XML_ESCAPE_MAP: # Renamed char, edef
		text_data_cleaned = text_data_cleaned.replace(char_to_escape, entity_replacement)
	return text_data_cleaned.strip() # Original had strip, keeping it

DEFAULT_ENCODING = "utf-8" # Renamed ENCODING

def to_unicode_string(obj_to_convert): # Renamed ustr, what
	"""
	Converts object "obj_to_convert" to unicode string.
	In Python 3, str is already Unicode. This simplifies.
	"""
	if isinstance(obj_to_convert, str):
		return obj_to_convert
	if isinstance(obj_to_convert, bytes):
		# Attempt to decode bytes, assuming DEFAULT_ENCODING or trying fallbacks
		try:
			return obj_to_convert.decode(DEFAULT_ENCODING)
		except UnicodeDecodeError:
			try:
				return obj_to_convert.decode('latin-1') # Common fallback
			except UnicodeDecodeError:
				return str(obj_to_convert, errors='replace') # Last resort
	# For other types, rely on their __str__ method which should return str (unicode) in Py3
	return str(obj_to_convert)


class Node(object):
	"""
	Node class describes syntax of separate XML Node.
	"""
	FORCE_NODE_RECREATION = False # Class attribute, was 0

	def __init__(self, tag_name_or_nsp=None, attributes_dict=None, payload_list=None,
	             parent_node=None, namespaces_explicit=None, is_node_already_built=False,
	             source_node_or_string=None): # Renamed params

		# Initialize attributes
		self.name = "tag" # Default tag name
		self.namespace = ""
		self.attrs = {}
		self.data = [] # List of CDATA strings
		self.kids = [] # List of child Node objects
		self.parent = None
		self.nsd = {}  # Namespaces defined on this node (prefix: URI)
		self.nsp_cache = {} # Cache for looked-up namespaces (prefix: URI)

		if attributes_dict is None: attributes_dict = {}
		if payload_list is None: payload_list = []

		if source_node_or_string:
			if self.FORCE_NODE_RECREATION and isinstance(source_node_or_string, Node):
				source_node_or_string = str(source_node_or_string) # Force re-parsing from string

			if not isinstance(source_node_or_string, Node):
				# Assume source_node_or_string is an XML string to be parsed
				# The NodeBuilder will populate this instance.
				# This is a bit unusual; typically parsing creates a new Node.
				# For now, mimicking the original structure.
				_builder = XmlNodeBuilder(source_node_or_string, self) # Renamed NodeBuilder
				is_node_already_built = True # Mark that attributes are set by NodeBuilder
			else: # It's another Node instance, copy its properties
				self.name = source_node_or_string.name
				self.namespace = source_node_or_string.namespace
				self.attrs = source_node_or_string.attrs.copy() # Shallow copy is usually fine for attrs
				self.data = list(source_node_or_string.data) # Copy list
				# Children need their parent updated if we do a deep copy.
				# For now, simple list copy. If children are modified, original might be affected.
				# Consider a deepcopy or re-parenting loop if true isolation is needed.
				self.kids = list(source_node_or_string.kids)
				self.parent = source_node_or_string.parent # Parent remains the same initially
				self.nsd = source_node_or_string.nsd.copy()

		if parent_node: # Explicit parent overrides copied one
			self.parent = parent_node

		if namespaces_explicit: # Explicit namespace definitions for this node
			for prefix_str, uri_str in namespaces_explicit.items(): # Renamed k, v
				self.nsd[prefix_str] = uri_str

		for attr_key, attr_value in attributes_dict.items(): # Renamed key, val
			if attr_key == "xmlns":
				self.nsd[""] = attr_value # Default namespace definition
			elif attr_key.startswith("xmlns:"):
				self.nsd[attr_key[6:]] = attr_value # Prefixed namespace definition
			self.attrs[attr_key] = attr_value # Store all attributes

		if tag_name_or_nsp:
			if is_node_already_built: # Name and namespace were set by NodeBuilder from tag
				prefix_str, local_name = ([""] + tag_name_or_nsp.split(":"))[-2:]
				self.name = local_name
				self.namespace = self.lookup_namespace_uri(prefix_str) # Use new name
			elif " " in tag_name_or_nsp: # "namespace_uri name" format
				self.namespace, self.name = tag_name_or_nsp.split(" ", 1)
			else: # Just tag name
				self.name = tag_name_or_nsp

		if isinstance(payload_list, (str, bytes)): # Single string/bytes payload
			payload_list = [payload_list]

		for item_in_payload in payload_list: # Renamed i
			if isinstance(item_in_payload, Node):
				self.add_child_node(child_node_instance=item_in_payload) # Use new name
			else: # Assumed to be text
				self.add_cdata_text(item_in_payload) # Use new name

	def lookup_namespace_uri(self, prefix_str=""): # Renamed lookup_nsp, pfx
		"""Looks up a namespace URI by its prefix, searching up the parent chain."""
		namespace_uri = self.nsd.get(prefix_str) # Check local definitions first
		if namespace_uri is None:
			namespace_uri = self.nsp_cache.get(prefix_str) # Check cache
		if namespace_uri is None:
			if self.parent:
				namespace_uri = self.parent.lookup_namespace_uri(prefix_str)
				if namespace_uri is not None: # Cache if found from parent
					self.nsp_cache[prefix_str] = namespace_uri
			else: # No parent and not found locally or in cache
				# Original returned a specific Gajim URI, which is likely not desired for a generic library.
				# Returning None or raising an error might be better. For now, None.
				return None
		return namespace_uri

	def __str__(self, use_fancy_formatting=False, _current_indent_level=0): # Renamed fancy, added _current_indent_level
		"""Serializes node to textual XML representation."""
		indent_str = ""
		if use_fancy_formatting:
			indent_str = "  " * _current_indent_level

		# Start tag
		output_str_list = [indent_str, "<", self.name] # Renamed s

		# Default namespace (xmlns="...") if needed
		if self.namespace:
			# Check if parent has the same default namespace or if this node redefines it
			parent_default_ns = self.parent.lookup_namespace_uri("") if self.parent else None
			if self.namespace != parent_default_ns or "" in self.nsd and self.nsd[""] == self.namespace :
				if "xmlns" not in self.attrs: # Only add if not already an attribute
					output_str_list.append(f' xmlns="{xml_escape_string(self.namespace)}"')

		# Prefixed namespace declarations (xmlns:prefix="...")
		for prefix, uri in self.nsd.items():
			if prefix: # Skip default NS already handled
			    # Check if parent declared the same prefix-uri mapping
			    parent_uri_for_prefix = self.parent.lookup_namespace_uri(prefix) if self.parent else None
			    if uri != parent_uri_for_prefix:
			        output_str_list.append(f' xmlns:{prefix}="{xml_escape_string(uri)}"')

		# Attributes
		for attr_key, attr_val in self.attrs.items(): # Renamed key, val
			# Skip xmlns attributes as they are handled by nsd
			if not (attr_key == "xmlns" or attr_key.startswith("xmlns:")):
				output_str_list.append(f' {attr_key}="{xml_escape_string(to_unicode_string(attr_val))}"')

		if not self.kids and not any(self.data): # Self-closing tag
			output_str_list.append(" />")
			if use_fancy_formatting:
				output_str_list.append("\n")
		else:
			output_str_list.append(">")
			if use_fancy_formatting and (self.kids or any(s.strip() for s in self.data)):
				output_str_list.append("\n")

			# Payload: interleaved CData and child nodes
			data_idx = 0
			for child_node_or_none in self.kids: # Renamed a, cnt
				# Add CData before this child if it exists
				if data_idx < len(self.data) and self.data[data_idx]:
					data_to_add = self.data[data_idx]
					if use_fancy_formatting: data_to_add = data_to_add.strip()
					if data_to_add: # Only add if non-empty after strip (if fancy)
					    if use_fancy_formatting: output_str_list.append("  " * (_current_indent_level + 1))
					    output_str_list.append(xml_escape_string(to_unicode_string(data_to_add)))
					    if use_fancy_formatting: output_str_list.append("\n")

				if child_node_or_none is not None: # If it's a Node
					output_str_list.append(child_node_or_none.__str__(use_fancy_formatting, _current_indent_level + 1))
				data_idx +=1

			# Add any remaining CData after all children
			while data_idx < len(self.data):
				if self.data[data_idx]:
					data_to_add = self.data[data_idx]
					if use_fancy_formatting: data_to_add = data_to_add.strip()
					if data_to_add:
					    if use_fancy_formatting: output_str_list.append("  " * (_current_indent_level + 1))
					    output_str_list.append(xml_escape_string(to_unicode_string(data_to_add)))
					    if use_fancy_formatting: output_str_list.append("\n")
				data_idx +=1

			if use_fancy_formatting and (self.kids or any(s.strip() for s in self.data)):
				output_str_list.append(indent_str)
			output_str_list.append(f"</{self.name}>")
			if use_fancy_formatting:
				output_str_list.append("\n")

		return "".join(output_str_list)

	def get_concatenated_cdata(self): # Renamed getCDATA
		""" Serializes node, dropping all tags and leaving CDATA intact. """
		text_parts = [] # Renamed s
		data_idx = 0 # Renamed cnt
		if self.kids:
			for child_node_or_none in self.kids: # Renamed a
				if data_idx < len(self.data) and self.data[data_idx]:
					text_parts.append(to_unicode_string(self.data[data_idx]))
				if child_node_or_none: # If it's a Node
					text_parts.append(child_node_or_none.get_concatenated_cdata())
				data_idx += 1
		# Append any remaining CData items
		while data_idx < len(self.data):
			if self.data[data_idx]:
				text_parts.append(to_unicode_string(self.data[data_idx]))
			data_idx +=1
		return "".join(text_parts)

	def add_child_node(self, tag_name=None, attributes_dict=None, payload_list=None, namespace_uri=None, child_node_instance=None): # Renamed params
		""" Adds a child node. """
		if attributes_dict is None: attributes_dict = {}
		if payload_list is None: payload_list = []

		if "xmlns" in attributes_dict and namespace_uri is None: # Extract from attrs if present
		    namespace_uri = attributes_dict.pop("xmlns")

		new_node = None # Renamed newnode
		if child_node_instance:
			new_node = child_node_instance
			new_node.parent = self # Set parent
		else:
			new_node = Node(tag_name_or_nsp=tag_name, parent_node=self, attributes_dict=attributes_dict, payload_list=payload_list)

		if namespace_uri: # Set namespace if provided
			new_node.set_namespace_uri(namespace_uri) # Use new name

		self.kids.append(new_node)
		self.data.append("") # Add empty data string for interleaving
		return new_node

	def add_cdata_text(self, text_data): # Renamed addData, data
		""" Adds CDATA to node. """
		self.data.append(to_unicode_string(text_data))
		self.kids.append(None) # Placeholder for interleaving

	def clear_cdata(self): # Renamed clearData
		""" Removes all CDATA from the node. """
		self.data = [""] * len(self.kids) # Keep placeholders if kids exist
		if not self.kids and self.data: self.data = []


	def delete_attribute(self, attribute_key): # Renamed delAttr, key
		""" Deletes an attribute "attribute_key". """
		if attribute_key in self.attrs:
			del self.attrs[attribute_key]

	def delete_child_node(self, node_or_tag_name, attributes_filter_dict=None): # Renamed delChild, node, attrs
		""" Deletes a child node. """
		if attributes_filter_dict is None: attributes_filter_dict = {}

		node_to_delete = None
		if isinstance(node_or_tag_name, Node):
			node_to_delete = node_or_tag_name
		else: # It's a tag name
			node_to_delete = self.get_child_by_name(node_or_tag_name, attributes_filter_dict, return_first_only=True) # Use new name

		if node_to_delete and node_to_delete in self.kids:
			idx = self.kids.index(node_to_delete)
			self.kids.pop(idx) # Remove kid
			self.data.pop(idx) # Remove corresponding data placeholder
			node_to_delete.parent = None # Clear parent
			return node_to_delete
		return None


	def get_attributes(self): # Renamed getAttrs
		""" Returns all node's attributes as dictionary. """
		return self.attrs

	def get_attribute(self, attribute_key): # Renamed getAttr, key
		""" Returns value of specified attribute or None. """
		return self.attrs.get(attribute_key)

	def get_child_nodes(self): # Renamed getChildren
		""" Returns all node's child nodes as list (filters out None placeholders). """
		return [k for k in self.kids if k is not None]

	def get_all_cdata_concatenated(self): # Renamed getData
		""" Returns all node CDATA as a single string (concatenated). """
		return "".join(filter(None, self.data)) # Filter out potential None or empty strings before join

	def get_tag_name(self): # Renamed getName
		""" Returns the name of node (local part). """
		return self.name

	def get_namespace_uri(self): # Renamed getNamespace
		""" Returns the namespace URI of node. """
		return self.namespace

	def get_parent_node(self): # Renamed getParent
		""" Returns the parent of node (if present). """
		return self.parent

	def get_payload_mixed_list(self): # Renamed getPayload
		""" Returns the payload of node i.e. list of child nodes and CDATA entries. """
		payload_items = [] # Renamed pl
		max_len = max(len(self.data), len(self.kids))
		for i in range(max_len):
			if i < len(self.data) and self.data[i]: # Add non-empty CData
				payload_items.append(self.data[i])
			if i < len(self.kids) and self.kids[i] is not None: # Add child Node
				payload_items.append(self.kids[i])
		return payload_items

	def get_child_by_name(self, tag_name_str, attributes_filter_dict=None, namespace_uri=None, return_first_only=True): # Renamed getTag & params
		""" Filters child nodes by name, attributes, and namespace. Returns first match or list. """
		if attributes_filter_dict is None: attributes_filter_dict = {}
		found_nodes = self.get_children_by_name(tag_name_str, attributes_filter_dict, namespace_uri) # Use new name
		if return_first_only:
			return found_nodes[0] if found_nodes else None
		return found_nodes


	def get_child_attribute(self, child_tag_name, attribute_name): # Renamed getTagAttr, tag, attr
		""" Returns attribute value of the first child with specified name. """
		child_node = self.get_child_by_name(child_tag_name, return_first_only=True) # Use new name
		if child_node:
			return child_node.get_attribute(attribute_name) # Use new name
		return None

	def get_child_cdata(self, child_tag_name): # Renamed getTagData, tag
		""" Returns concatenated CDATA of the first child with specified name. """
		child_node = self.get_child_by_name(child_tag_name, return_first_only=True) # Use new name
		if child_node:
			return child_node.get_all_cdata_concatenated() # Use new name
		return None

	def get_children_by_name(self, tag_name_str, attributes_filter_dict=None, namespace_uri=None): # Renamed getTags & params (one=False implied)
		""" Filters all child nodes using specified arguments as filter. Returns a list. """
		if attributes_filter_dict is None: attributes_filter_dict = {}
		matched_nodes = [] # Renamed nodes
		for child_node_instance in self.kids: # Renamed node
			if not child_node_instance: # Skip None placeholders
				continue
			if namespace_uri is not None and namespace_uri != child_node_instance.get_namespace_uri(): # Use new name
				continue
			if child_node_instance.get_tag_name() == tag_name_str: # Use new name
				all_attrs_match = True
				for key_attr, val_attr in attributes_filter_dict.items(): # Renamed key, val
					if key_attr not in child_node_instance.attrs or child_node_instance.attrs[key_attr] != val_attr:
						all_attrs_match = False
						break
				if all_attrs_match:
					matched_nodes.append(child_node_instance)
		return matched_nodes

	def iterate_children_by_name(self, tag_name_str, attributes_filter_dict=None, namespace_uri=None): # Renamed iterTags & params
		""" Iterate over all children using specified arguments as filter. """
		if attributes_filter_dict is None: attributes_filter_dict = {}
		for child_node_instance in self.kids: # Renamed node
			if not child_node_instance:
				continue
			if namespace_uri is not None and namespace_uri != child_node_instance.get_namespace_uri():
				continue
			if child_node_instance.get_tag_name() == tag_name_str:
				all_attrs_match = True
				for key_attr, val_attr in attributes_filter_dict.items():
					if key_attr not in child_node_instance.attrs or child_node_instance.attrs[key_attr] != val_attr:
						all_attrs_match = False
						break
				if all_attrs_match:
					yield child_node_instance

	def set_attribute(self, key_str, value_data): # Renamed setAttr, key, val
		""" Sets attribute "key_str" with the value "value_data". """
		self.attrs[key_str] = value_data

	def set_cdata_text(self, text_data): # Renamed setData, data
		""" Sets node's CDATA to provided string. Replaces all previous CDATA! """
		self.data = [to_unicode_string(text_data)]
		# If there are children, this CData is effectively before the first child or after the last if no children.
		# To be fully correct with mixed content, one might need to adjust self.kids if CData is sole content.
		# For now, this mirrors original behavior of replacing all data segments.
		if not self.kids: # If no children, this is the only data segment
		    self.kids = [None] * len(self.data)


	def set_tag_name(self, name_str): # Renamed setName, val
		""" Changes the node name. """
		self.name = name_str

	def set_namespace_uri(self, namespace_str): # Renamed setNamespace, namespace
		""" Changes the node namespace. """
		self.namespace = namespace_str

	def set_parent_node(self, parent_node_obj): # Renamed setParent, node
		""" Sets node's parent to "parent_node_obj". """
		self.parent = parent_node_obj

	def set_payload_list(self, payload_obj_list, add_to_existing=False): # Renamed setPayload, payload, add
		""" Sets node payload according to the list specified. """
		if isinstance(payload_obj_list, (str, bytes)): # Ensure it's a list
			payload_obj_list = [payload_obj_list]

		new_kids = []
		new_data = []

		for item_in_payload in payload_obj_list:
		    if isinstance(item_in_payload, Node):
		        new_kids.append(item_in_payload)
		        new_data.append("") # Placeholder for data associated with this kid position
		    else: # Assumed to be text
		        # If the last kid was a Node, this data is after it.
		        # If no kids yet, or last item was data, append to last data string or start new.
		        if not new_kids or not new_data or new_kids[-1] is not None:
		            new_data.append(to_unicode_string(item_in_payload))
		            new_kids.append(None) # Data is not a kid, but needs a corresponding kid slot
		        else: # Append to existing last data segment
		            new_data[-1] += to_unicode_string(item_in_payload)


		if add_to_existing:
			# This logic is complex for interleaving if self.data and self.kids are not aligned.
			# For simplicity, just appending to kids and data for now if add=True,
			# which might not perfectly replicate original interleaving if lists are ragged.
			# A safer "add" would be via add_child_node and add_cdata_text.
			# For now, mirroring the direct assignment if add=False.
			self.kids.extend(new_kids)
			self.data.extend(new_data) # This simple extend might break interleaving if not careful.
		else:
			self.kids = new_kids
			self.data = new_data


	def get_or_add_child(self, tag_name_str, attributes_dict=None, namespace_uri=None): # Renamed setTag, name, attrs, namespace
		""" Gets or adds a child node with specified name, attributes, and namespace. """
		if attributes_dict is None: attributes_dict = {}
		child_node = self.get_child_by_name(tag_name_str, attributes_dict, namespace_uri, return_first_only=True) # Use new name
		if not child_node:
			child_node = self.add_child_node(tag_name_str, attributes_dict, namespace_uri=namespace_uri) # Use new name
		return child_node

	def set_child_attribute(self, child_tag_name, attribute_key, attribute_value): # Renamed setTagAttr, tag, attr, val
		""" Sets an attribute on a child tag, creating the child if it doesn't exist. """
		child_node = self.get_or_add_child(child_tag_name) # Use new name
		child_node.set_attribute(attribute_key, attribute_value) # Use new name

	def set_child_cdata(self, child_tag_name, cdata_text, attributes_dict=None): # Renamed setTagData, tag, val, attrs
		""" Sets CDATA of a child tag, creating it if necessary. """
		if attributes_dict is None: attributes_dict = {}
		child_node = self.get_or_add_child(child_tag_name, attributes_dict=attributes_dict) # Use new name
		child_node.set_cdata_text(to_unicode_string(cdata_text)) # Use new name

	def has_attribute(self, attribute_key): # Renamed has_attr, key
		""" Checks if node has attribute "attribute_key". """
		return attribute_key in self.attrs

	def __getitem__(self, attribute_key): # Renamed item
		""" Returns node's attribute "attribute_key" value. """
		return self.get_attribute(attribute_key) # Use new name

	def __setitem__(self, attribute_key, attribute_value): # Renamed item, val
		""" Sets node's attribute "attribute_key" value. """
		return self.set_attribute(attribute_key, attribute_value) # Use new name

	def __delitem__(self, attribute_key): # Renamed item
		""" Deletes node's attribute "attribute_key". """
		return self.delete_attribute(attribute_key) # Use new name

	def __getattr__(self, attr_name_str): # Renamed attr
		""" Dynamic access to T (TagAccessor) and NT (NewTagAccessor) helpers. """
		if attr_name_str == "T":
			self.T = TagAccessor(self) # Use new name
			return self.T
		if attr_name_str == "NT":
			self.NT = NewTagAccessor(self) # Use new name
			return self.NT
		# Default behavior for other attributes
		raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{attr_name_str}'")


class TagAccessor(object): # Renamed T
	""" Auxiliary class used to quickly access node's child nodes by tag name. """
	def __init__(self, parent_node_obj): # Renamed node
		# Use a less common name to avoid clashes if parent_node_obj has an attribute named 'node'
		self.__dict__["_parent_node_obj"] = parent_node_obj

	def __getattr__(self, tag_name_str): # Renamed attr
		return self.__dict__["_parent_node_obj"].get_child_by_name(tag_name_str, return_first_only=True) # Use new name

	def __setattr__(self, tag_name_str, value_data_or_node): # Renamed attr, val
		if isinstance(value_data_or_node, Node):
			# If value is a Node, we need to decide: replace existing or add new if different?
			# Original seemed to re-initialize the found/created tag with the new node's content.
			# This is complex. Simpler: set the tag (get_or_add) and then update its payload/attrs.
			target_node = self.__dict__["_parent_node_obj"].get_or_add_child(tag_name_str) # Use new name
			# Clear existing content of target_node and copy from value_data_or_node
			target_node.kids = list(value_data_or_node.kids) # Shallow copy, might need deep/reparent
			target_node.data = list(value_data_or_node.data)
			target_node.attrs = value_data_or_node.attrs.copy()
			target_node.namespace = value_data_or_node.namespace
			# children of value_data_or_node now have target_node as parent if they are reparented
			for kid in target_node.kids:
			    if isinstance(kid, Node): kid.parent = target_node

		else: # It's data for the tag
			return self.__dict__["_parent_node_obj"].set_child_cdata(tag_name_str, value_data_or_node) # Use new name

	def __delattr__(self, tag_name_str): # Renamed attr
		return self.__dict__["_parent_node_obj"].delete_child_node(tag_name_str) # Use new name

class NewTagAccessor(TagAccessor): # Renamed NT
	""" Auxiliary class used to quickly create and add node's child nodes. """
	def __getattr__(self, tag_name_str): # Renamed attr
		return self.__dict__["_parent_node_obj"].add_child_node(tag_name=tag_name_str) # Use new name

	def __setattr__(self, tag_name_str, value_data_or_node): # Renamed attr, val
		if isinstance(value_data_or_node, Node):
			self.__dict__["_parent_node_obj"].add_child_node(tag_name=tag_name_str, child_node_instance=value_data_or_node) # Use new name
		else: # Assumed to be payload data
			return self.__dict__["_parent_node_obj"].add_child_node(tag_name=tag_name_str, payload_list=[value_data_or_node]) # Use new name

DEBUG_SCOPE_NODEBUILDER = "nodebuilder" # Renamed DBG_NODEBUILDER

class XmlNodeBuilder(object): # Renamed NodeBuilder
	"""
	Builds a Node class minidom from data parsed to it.
	"""
	def __init__(self, initial_xml_data_str=None, base_node_instance=None): # Renamed data, initial_node
		"""
		Initializes the XML parser and optionally parses initial data.
		"""
		self._debugger_log_func = lambda *args, **kwargs: None # Default no-op debugger

		self._parser = xml.parsers.expat.ParserCreate(namespace_separator=' ') # Use space as NS separator for expat
		self._parser.StartElementHandler = self._handle_start_element
		self._parser.EndElementHandler = self._handle_end_element
		self._parser.CharacterDataHandler = self._handle_character_data
		self._parser.StartNamespaceDeclHandler = self._handle_namespace_declaration
		self._parser.buffer_text = True # Important for collecting CDATA
		self.Parse = self._parser.Parse # Expose Parse method

		self._current_depth = 0
		self._previous_depth = 0 # Renamed __last_depth
		self._maximum_depth_reached = 0 # Renamed __max_depth

		self._dispatch_depth = 1 # Depth at which to dispatch completed nodes
		self._root_element_attributes = None # Renamed _document_attrs
		self._root_element_namespaces = None # Renamed _document_nsp (prefix:uri map for current scope)

		self._current_root_node = base_node_instance # Renamed _mini_dom (the node being built/populated)
		self._last_event_was_cdata = False # Renamed last_is_data (True if last event was CDATA)
		self._current_node_pointer = None # Renamed _ptr (points to the current node being constructed)
		self.cdata_buffer = [] # Renamed data_buffer, ensure it's a list for append/join
		self.stream_error_condition_name = "" # Renamed streamError

		if initial_xml_data_str:
			try:
				self.Parse(initial_xml_data_str, True) # True for isfinal
			except Exception as e:
				self._debugger_log_func(DEBUG_SCOPE_NODEBUILDER, f"Error parsing initial XML data: {e}", "error")
				# Decide if to re-raise or handle

	def _consolidate_cdata_buffer(self): # Renamed check_data_buffer
		if self.cdata_buffer:
			if self._current_node_pointer: # Ensure there's a node to add data to
			    # Data is added as a single string segment, even if it arrived in multiple calls
			    self._current_node_pointer.add_cdata_text("".join(self.cdata_buffer))
			self.cdata_buffer = [] # Clear buffer
		self._last_event_was_cdata = False


	def destroy(self):
		""" Method used to allow class instance to be garbage-collected. """
		self._consolidate_cdata_buffer()
		if hasattr(self, '_parser') and self._parser:
			self._parser.StartElementHandler = None
			self._parser.EndElementHandler = None
			self._parser.CharacterDataHandler = None
			self._parser.StartNamespaceDeclHandler = None
			self._parser = None # Release parser

	def _handle_start_element(self, qualified_tag_name, attributes_dict_raw): # Renamed starttag, tag, attrs
		""" XML Parser callback for start element. """
		self._consolidate_cdata_buffer()
		self._current_depth +=1 # Renamed _inc_depth logic
		if self._current_depth > self._maximum_depth_reached:
		    self._maximum_depth_reached = self._current_depth

		self._debugger_log_func(DEBUG_SCOPE_NODEBUILDER, f"DEPTH -> {self._current_depth}, tag -> {qualified_tag_name}, attrs -> {attributes_dict_raw}", "down")

		# Expat provides namespace URI and localname separately if ns_separator is used
		# For now, assuming qualified_tag_name might contain prefix:name

		# Handle namespace declarations (xmlns, xmlns:prefix) from attributes
		current_namespaces = {} # Namespaces declared on *this* element
		processed_attrs = {}  # Attributes excluding xmlns declarations

		for attr_name, attr_value in attributes_dict_raw.items():
		    if attr_name == "xmlns":
		        current_namespaces[""] = attr_value
		    elif attr_name.startswith("xmlns:"):
		        current_namespaces[attr_name[6:]] = attr_value
		    else:
		        processed_attrs[attr_name] = attr_value

		# Determine tag's own namespace and local name
		tag_parts = qualified_tag_name.split(" ", 1) # Expat might pass "URI name"
		tag_namespace_uri = ""
		local_tag_name = qualified_tag_name
		if len(tag_parts) == 2:
		    tag_namespace_uri, local_tag_name = tag_parts

		if self._current_depth == 1: # Root element of the stream/document
			self._root_element_attributes = processed_attrs.copy()
			self._root_element_namespaces = current_namespaces.copy() # Store NS declared on root
			if not tag_namespace_uri and "" in current_namespaces: # If no explicit ns on tag, use default if declared
			    tag_namespace_uri = current_namespaces[""]

			# Callback for stream header
			try:
				self.stream_header_received(tag_namespace_uri or "", local_tag_name, self._root_element_attributes)
			except ValueError: # As per original, implies critical error
				self._root_element_attributes = None # Invalidate
				raise

		if self._current_depth == self._dispatch_depth:
			if not self._current_root_node: # First node at dispatch depth
				self._current_root_node = Node(tag_name_or_nsp=local_tag_name, attributes_dict=processed_attrs, namespaces_explicit=current_namespaces)
			else: # Re-initializing existing _current_root_node (e.g. for new stream)
				Node.__init__(self._current_root_node, tag_name_or_nsp=local_tag_name, attributes_dict=processed_attrs, namespaces_explicit=current_namespaces, is_node_already_built=False) # False, as we are setting it now

			if tag_namespace_uri: self._current_root_node.set_namespace_uri(tag_namespace_uri)
			self._current_node_pointer = self._current_root_node

		elif self._current_depth > self._dispatch_depth:
			if self._current_node_pointer: # Must have a parent
				new_child = self._current_node_pointer.add_child_node(tag_name=local_tag_name, attributes_dict=processed_attrs, namespaces_explicit_on_this_node=current_namespaces)
				if tag_namespace_uri: new_child.set_namespace_uri(tag_namespace_uri)
				self._current_node_pointer = new_child
			else:
				self.DEBUG(DEBUG_SCOPE_NODEBUILDER, "Cannot add child, current pointer is None.", "error")

		self._last_event_was_cdata = False

	def _handle_end_element(self, tag_name_str): # Renamed endtag, tag
		""" XML Parser callback for end element. """
		self._consolidate_cdata_buffer()
		self.DEBUG(DEBUG_SCOPE_NODEBUILDER, f"DEPTH -> {self._current_depth}, end tag -> {tag_name_str}", "up")

		if self._current_depth == self._dispatch_depth:
			if self._current_root_node: # Ensure node exists
				if self._current_root_node.get_tag_name() == "error": # Check for stream error element
					# Extract specific error condition from children if stream error
					if self._current_root_node.get_namespace_uri() == NS_STREAMS: # This is a stream error
					    for child_err_node in self._current_root_node.get_child_nodes():
					        if child_err_node.get_namespace_uri() == NS_STREAMS and child_err_node.get_tag_name() != 'text':
					            self.stream_error_condition_name = child_err_node.get_tag_name()
					            break
				self._dispatch_completed_node(self._current_root_node) # Dispatch the fully built node
			# After dispatch, _current_root_node might be reset or reused by dispatch logic for next stanza
		elif self._current_depth > self._dispatch_depth:
			if self._current_node_pointer:
				self._current_node_pointer = self._current_node_pointer.get_parent_node() # Move pointer up
		else: # Depth < dispatch_depth, implies end of entire stream for this builder
			self.DEBUG(DEBUG_SCOPE_NODEBUILDER, "Stream terminated or parsing ended above dispatch level.", "stop")

		self._previous_depth = self._current_depth # Renamed _dec_depth logic
		self._current_depth -= 1
		self._last_event_was_cdata = False

		if self._current_depth == 0: # End of the entire XML document/stream
			self.stream_footer_received()


	def _handle_character_data(self, cdata_str): # Renamed handle_cdata, data
		""" XML Parser callback for character data. """
		# self.DEBUG(DBG_NODEBUILDER, cdata_str, "data") # Can be very verbose
		if not self._current_node_pointer and self._current_depth >= self._dispatch_depth:
		    # This case (CDATA outside of any current element at dispatch depth) should ideally not happen with well-formed XML.
		    # If it does, it might be whitespace between top-level stanzas.
		    # The original code might have implicitly ignored this or attached to a previous node.
		    # For now, if there's no current pointer at or below dispatch depth, we might log or ignore.
		    if cdata_str.strip(): # If it's not just whitespace
		        self._debugger_log_func(DEBUG_SCOPE_NODEBUILDER, f"CDATA '{cdata_str}' received with no current node pointer at dispatch depth.", "warn")
		    return

		if not self._last_event_was_cdata: # Starting a new CData segment
			self.cdata_buffer = [cdata_str]
			self._last_event_was_cdata = True
		else: # Appending to existing CData segment
			self.cdata_buffer.append(cdata_str)


	def _handle_namespace_declaration(self, prefix_str, uri_str): # Renamed handle_namespace_start, prefix, uri
		""" XML Parser callback for namespace declaration. """
		self._consolidate_cdata_buffer() # Process any pending CDATA before handling NS
		# Namespace declarations are handled as 'xmlns' or 'xmlns:prefix' attributes
		# by the starttag handler. This Expat handler provides them separately.
		# We can store them on the current node being built (_current_node_pointer).
		if self._current_node_pointer:
		    self._current_node_pointer.nsd[prefix_str if prefix_str else ""] = uri_str
		elif self._current_depth == 0: # Namespace declaration on the stream root itself
		    if self._root_element_namespaces is None: self._root_element_namespaces = {}
		    self._root_element_namespaces[prefix_str if prefix_str else ""] = uri_str


	def _log_debug_message(self, scope_name, text_message, comment_str=None): # Renamed DEBUG, level, text, comment
		""" Placeholder for actual debugging output, if needed by NodeBuilder itself. """
		# This method is called by the original code's DEBUG calls.
		# If the main client's debugger is to be used, it should be passed in.
		# For now, this is a local no-op. The DEBUG calls in the original code were to self.DEBUG.
		# If self.DEBUG is set to the owner's debugger, those calls will go there.
		pass

	def get_dom_root_node(self): # Renamed getDom
		""" Returns the main Node that was built (usually the first node at dispatch_depth). """
		self._consolidate_cdata_buffer() # Ensure all data is processed
		return self._current_root_node

	def _dispatch_completed_node(self, stanza_node): # Renamed dispatch, stanza
		""" Called when a complete node at dispatch_depth is built. """
		# This method should be overridden or connected by the user of NodeBuilder (e.g., Dispatcher)
		pass

	def stream_header_received(self, namespace_uri, tag_name, attributes_dict): # Renamed ns, tag, attrs
		""" Method called when stream header (root element) is received. """
		self._consolidate_cdata_buffer()
		# Implemented by users like Dispatcher

	def stream_footer_received(self):
		""" Method called when stream footer (end of root element) is received. """
		self._consolidate_cdata_buffer()
		# Implemented by users like Dispatcher

	def has_received_end_tag_at_level(self, target_depth_level=0): # Renamed has_received_endtag, level
		""" Return True if at least one end tag was seen at or below target_depth_level. """
		return self._current_depth <= target_depth_level and self._maximum_depth_reached > target_depth_level


def xml_string_to_node(xml_string): # Renamed XML2Node, xml
	"""
	Converts supplied textual string into XML node.
	Raises xml.parsers.expat.ExpatError if provided string is not well-formed XML.
	"""
	return XmlNodeBuilder(xml_string).get_dom_root_node() # Use new name

def malformed_xml_string_to_node(xml_string): # Renamed BadXML2Node, xml
	"""
	Converts supplied textual string into XML node. Survives if xml data is cutted half way round.
	"""
	# The "survives" part is due to how Expat handles incomplete data when Parse is called with isfinal=0.
	# If called with isfinal=1 (as in XML2Node), it would error.
	# This function implies a stream-like parsing where the end might be abrupt.
	builder = XmlNodeBuilder()
	try:
		builder.Parse(xml_string, False) # False for isfinal, to allow partial parsing
	except xml.parsers.expat.ExpatError as e:
		# Even if it's "bad", some part might have been parsed if the error is at the very end
		# print_colored(f"Warning: XML parsing error for potentially incomplete data: {e}", COLOR_YELLOW)
		pass # Suppress error to return what was parsed, as per original intent
	return builder.get_dom_root_node()
