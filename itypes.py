"""
Module "itypes"
itypes.py

Copyright (2010-2013) Al Korgun (alkorgun@gmail.com)

Distributed under the GNU GPLv3.
"""

try:
	import sqlite3 as SQLITE3_MODULE # Keep original import name for clarity if needed locally
except ImportError:
	SQLITE3_MODULE = None
	# Define a placeholder connect that raises an error if sqlite3 is not available
	def connect_sqlite_db(*args, **kwargs): # Renamed connect
		raise RuntimeError("sqlite3 module is not installed, database functionality unavailable.")
else:
	connect_sqlite_db = SQLITE3_MODULE.connect # Use renamed alias

__all__ = [
	"WrappedInteger", # Renamed Number
	"SQLiteDatabaseWrapper"  # Renamed Database
]

__version__ = "0.8"

class WrappedInteger(object): # Renamed Number
	""" A simple wrapper around an integer to make it mutable. """
	def __init__(self, initial_value = 0): # Renamed number to initial_value, ensure int() is called if needed
		self.value = int(initial_value) # Renamed number to value

	def plus(self, increment_amount = 1): # Renamed number to increment_amount
		self.value += increment_amount
		return self.value

	def reduce(self, decrement_amount = 1): # Renamed number to decrement_amount
		self.value -= decrement_amount
		return self.value

	def __int__(self):
		return self.value # Direct access to int value

	_int = __int__ # Alias for internal use

	def __str__(self):
		return str(self.value)

	__repr__ = __str__
	_str = __str__ # Alias for internal use

	def __float__(self):
		return float(self.value)

	def __oct__(self):
		return oct(self.value) # Use built-in oct()

	# Comparison operators should compare the internal value
	def __eq__(self, other_number): # Renamed number
		return self.value == other_number
	def __ne__(self, other_number):
		return self.value != other_number
	def __gt__(self, other_number):
		return self.value > other_number
	def __lt__(self, other_number):
		return self.value < other_number
	def __ge__(self, other_number):
		return self.value >= other_number
	def __le__(self, other_number):
		return self.value <= other_number

class LazyPropertyDescriptor(object): # Renamed LazyDescriptor
	""" A descriptor for creating lazy-loaded properties. """
	def __init__(self, getter_function): # Renamed function
		self._getter_function = getter_function # Renamed fget, make private

	def __get__(self, instance_obj, owner_class): # Renamed instance, owner
		if instance_obj is None: # Called on the class, not an instance
			return self
		# Call the getter function, it's responsible for any caching if needed
		# The original implementation implicitly replaced the descriptor on the instance.
		# A more common pattern is to compute, store on instance, and return.
		# For now, just calling the getter. If it needs to set the attribute
		# on the instance to replace the descriptor, it can do so.
		value = self._getter_function(instance_obj)
		# Optionally, set the attribute on the instance to cache the value
		# setattr(instance_obj, self._getter_function.__name__, value)
		return value

class SQLiteDatabaseWrapper(object): # Renamed Database
	""" A wrapper for SQLite database connections with lazy connection. """
	_is_connected = False # Renamed __connected (PEP 8 private)

	def __init__(self, db_filename, db_lock = None, connection_timeout = 8): # Renamed params
		self.db_filename = db_filename
		self.db_lock = db_lock
		self.connection_timeout = connection_timeout
		self.database_connection = None # Initialize attributes, Renamed db
		self.database_cursor = None # Renamed cursor
		# Methods to be delegated after connection
		self.commit = None
		self.execute = None
		self.fetchone = None
		self.fetchall = None
		self.fetchmany = None


	def _connect_to_database(self): # Renamed __connect
		if self._is_connected: # Check before asserting
		    return # Already connected

		# assert not self._is_connected, "Database already connected" # Original assertion

		if SQLITE3_MODULE is None: # Check if sqlite3 module was imported
		    raise RuntimeError("sqlite3 module is not installed, cannot connect to database.")

		self.database_connection = connect_sqlite_db(self.db_filename, timeout=self.connection_timeout)
		self.database_cursor = self.database_connection.cursor()
		self._is_connected = True

		# Delegate methods after connection
		self.commit = self.database_connection.commit
		self.execute = self.database_cursor.execute
		self.fetchone = self.database_cursor.fetchone
		self.fetchall = self.database_cursor.fetchall
		self.fetchmany = self.database_cursor.fetchmany

	# Lazy properties for execute, db, cursor
	# The original used @LazyDescriptor on methods with the same name as attributes.
	# This can be confusing. A common pattern is to use @property.
	# For now, directly calling _connect_to_database in methods that need it.

	def __call__(self, *args_tuple, **kwargs_dict): # Renamed args
		""" Allows calling the instance like a function, typically to execute SQL. """
		if not self._is_connected:
			self._connect_to_database()
		if not self.execute: # Should be set by _connect_to_database
		    raise RuntimeError("Database not connected or execute method not available.")
		return self.execute(*args_tuple, **kwargs_dict)

	# Properties to ensure connection before accessing db or cursor directly
	@property
	def db(self): # Keep 'db' as a property name for compatibility if used directly
		if not self._is_connected:
			self._connect_to_database()
		return self.database_connection

	@property
	def cursor(self): # Keep 'cursor' as a property name
		if not self._is_connected:
			self._connect_to_database()
		return self.database_cursor

	def close(self):
		if not self._is_connected: # Check before asserting
		    #warnings.warn("Database connection already closed or not opened.", UserWarning)
		    return

		# assert self._is_connected, "Database not connected" # Original assertion

		if self.database_cursor:
			self.database_cursor.close()
		# Check if total_changes exists and is non-zero before committing
		if hasattr(self.database_connection, 'total_changes') and self.database_connection.total_changes > 0:
			if self.commit and callable(self.commit): # Ensure commit is available and callable
			    self.commit()
		if self.database_connection:
			self.database_connection.close()
		self._is_connected = False
		# Reset delegated methods
		self.database_connection = None
		self.database_cursor = None
		self.commit = None
		self.execute = None
		self.fetchone = None
		self.fetchall = None
		self.fetchmany = None


	def __enter__(self):
		if self.db_lock:
			self.db_lock.acquire()
		# Ensure connection is made when entering context
		if not self._is_connected:
		    self._connect_to_database()
		return self

	def __exit__(self, *exception_args): # Renamed args
		# Close connection when exiting context
		if self._is_connected: # Check if connected before trying to close
			self.close()
		if self.db_lock:
			self.db_lock.release()

# del LazyPropertyDescriptor # Not needed if it's used above
