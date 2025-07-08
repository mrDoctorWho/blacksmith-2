##   plugin.py
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

# $Id: plugin.py, v1.0 2013/10/21 alkorgun Exp $

"""
Provides base class for xmpppy plugins.
"""

class XmppPlugin(object): # Renamed PlugIn
	"""
	Common xmpppy plugins infrastructure: plugging in/out, debugging.
	"""
	def __init__(self):
		self._exported_methods = []
		# self.debug_scope_name should be set by subclasses or based on class name
		# Defaulting to lowercased class name as before.
		self.debug_scope_name = self.__class__.__name__.lower() # Renamed DBG_LINE

	def attach_to_owner(self, owner_instance): # Renamed PlugIn method, owner
		"""
		Attach to main instance and register ourself and all our staff in it.
		"""
		self._owner = owner_instance
		# Ensure owner has debug_flags attribute (list)
		if not hasattr(self._owner, 'debug_flags') or not isinstance(self._owner.debug_flags, list):
		    self._owner.debug_flags = [] # Initialize if not present

		if self.debug_scope_name not in self._owner.debug_flags:
			self._owner.debug_flags.append(self.debug_scope_name)

		self.log_debug_message(f"Plugging {self.__class__.__name__} into {self._owner.__class__.__name__}", "start") # Use new name

		if self.__class__.__name__ in self._owner.__dict__:
			self.log_debug_message("Plugging ignored: another instance already plugged.", "error") # Use new name
			return None # Indicate failure or no action

		self._old_owners_methods = []
		for method_obj in self._exported_methods: # Renamed method
			if method_obj.__name__ in self._owner.__dict__:
				self._old_owners_methods.append(self._owner.__dict__[method_obj.__name__])
			# Set the method on the owner instance
			setattr(self._owner, method_obj.__name__, method_obj)

		setattr(self._owner, self.__class__.__name__, self) # Register instance of this plugin on owner

		# Call subclass's specific plugin logic if it exists
		if hasattr(self, "plugin") and callable(getattr(self, "plugin")):
			return self.plugin(owner_instance) # Call the specific plugin's additional setup

	def detach_from_owner(self): # Renamed PlugOut
		"""
		Unregister all our staff from main instance and detach from it.
		"""
		self.log_debug_message(f"Plugging {self.__class__.__name__} out of {self._owner.__class__.__name__}.", "stop") # Use new name

		return_value = None # Renamed ret
		# Call subclass's specific plugout logic if it exists
		if hasattr(self, "plugout") and callable(getattr(self, "plugout")):
			return_value = self.plugout() # Call the specific plugin's teardown

		if hasattr(self._owner, 'debug_flags') and isinstance(self._owner.debug_flags, list) and self.debug_scope_name in self._owner.debug_flags:
			self._owner.debug_flags.remove(self.debug_scope_name)

		for method_obj in self._exported_methods: # Renamed method
			if hasattr(self._owner, method_obj.__name__):
				delattr(self._owner, method_obj.__name__)

		for old_method_obj in self._old_owners_methods: # Renamed method
			# Restore original methods on the owner
			setattr(self._owner, old_method_obj.__name__, old_method_obj)

		if hasattr(self._owner, self.__class__.__name__):
			delattr(self._owner, self.__class__.__name__) # Remove plugin instance from owner

		return return_value

	def log_debug_message(self, message_text, severity_level="info"): # Renamed DEBUG, text, severity
		"""
		Feed a provided debug line to main instance's debug facility along with our ID string.
		"""
		# Assumes owner has a DEBUG method (which should be refactored to log_debug_message or similar)
		if hasattr(self._owner, 'DEBUG') and callable(self._owner.DEBUG):
		    self._owner.DEBUG(self.debug_scope_name, message_text, severity_level)
		elif hasattr(self._owner, '_debugger') and hasattr(self._owner._debugger, 'show_formatted_message'): # Common pattern emerging
		    self._owner._debugger.show_formatted_message(self.debug_scope_name, message_text, severity_level)
		# else:
		    # print(f"DEBUG ({self.debug_scope_name}/{severity_level}): {message_text}") # Fallback if no proper logger
