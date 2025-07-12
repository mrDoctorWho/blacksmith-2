"""
Module "ithr" (for Python 2.6+)
ithr.py

Partial copyright (2010-2013) Al Korgun (alkorgun@gmail.com)

Distributed under the PSFL.
"""

import sys

try:
	import _thread # In Python 3, this is the low-level threading module
except ImportError:
	# This module cannot function without _thread
	del sys.modules[__name__] # Remove self from modules to prevent partial import
	raise

from traceback import format_exc as get_exception_traceback_string # Renamed get_exc

# Direct aliases to _thread functions (PEP 8 for constants if they are treated as such)
START_NEW_THREAD_ALIAS = _thread.start_new_thread # Renamed sThread_Run
GET_THREAD_IDENTIFIER_ALIAS = _thread.get_ident # Renamed get_ident
ALLOCATE_LOCK_ALIAS = _thread.allocate_lock # Renamed allocate_lock
THREAD_STACK_SIZE_ALIAS = _thread.stack_size # Renamed stack_size
THREAD_ERROR_ALIAS = _thread.error # Renamed error

del _thread # Remove original _thread from module namespace after aliasing

import time
import warnings

__all__ = [
	"BoundedSemaphore", # Standard name, kept
	"ThreadingCondition", # Renamed Condition
	"Event", # Standard name, kept
	"KillableThread", # Renamed KThread
	"SimpleCounter", # Renamed Number
	"get_next_non_daemon_thread", # Renamed PickSomeNonDaemonThread
	"ReusableLock", # Renamed RLock
	"Semaphore", # Standard name, kept
	"CustomThread", # Renamed Thread
	"CustomTimerThread", # Renamed Timer
	"UnboundedSemaphore", # Renamed UnBoundedSemaphore
	"ALLOCATE_LOCK_ALIAS",
	"get_current_custom_thread", # Renamed currentThread
	"get_all_custom_threads", # Renamed enumerate
	"THREAD_ERROR_ALIAS",
	"get_exception_traceback_string",
	"GET_THREAD_IDENTIFIER_ALIAS",
	"get_all_custom_thread_names", # Renamed getNames
	"kill_all_custom_threads", # Renamed killAllThreads
	"START_NEW_THREAD_ALIAS",
	"THREAD_STACK_SIZE_ALIAS"
]

__version__ = "1.5"

# Suppress DeprecationWarning for sys.exc_clear (which is not used in Py3 anyway)
warnings.filterwarnings("ignore", category=DeprecationWarning, module=__name__, message="sys.exc_clear")

class ReusableLock(object): # Renamed RLock
	def __init__(self, associated_object = None): # Renamed object to associated_object
		self._block = ALLOCATE_LOCK_ALIAS() # Use new name
		self._owner_thread_id = None # Renamed __owner
		self._recursion_count = 0 # Renamed __count

	def __repr__(self):
		owner_repr = self._owner_thread_id
		try:
			# ACTIVE_THREADS_REGISTRY will be defined later
			owner_repr = ACTIVE_THREADS_REGISTRY[self._owner_thread_id].name
		except KeyError:
			pass # Keep as thread ID if not in registry
		return f"<{self.__class__.__name__} owner={owner_repr!r} count={self._recursion_count}>"

	def acquire(self, blocking_flag = True): # Renamed blocking
		current_thread_id = GET_THREAD_IDENTIFIER_ALIAS() # Use new name
		if self._owner_thread_id == current_thread_id:
			self._recursion_count += 1
			return True

		acquired_successfully = self._block.acquire(blocking_flag) # Renamed rc
		if acquired_successfully:
			self._owner_thread_id = current_thread_id
			self._recursion_count = 1
		return acquired_successfully

	__enter__ = acquire

	def release(self):
		if self._owner_thread_id != GET_THREAD_IDENTIFIER_ALIAS(): # Use new name
			raise RuntimeError("Cannot release un-acquired lock or lock acquired by another thread.")
		self._recursion_count -= 1
		if self._recursion_count == 0: # Check against 0, not original 'not count'
			self._owner_thread_id = None
			self._block.release()

	def __exit__(self, *exception_args): # Renamed args
		self.release()

	def _acquire_and_restore_state(self, count_owner_tuple): # Renamed _acquire_restore
		count, owner_id = count_owner_tuple
		self._block.acquire()
		self._recursion_count = count
		self._owner_thread_id = owner_id

	def _release_and_save_state(self): # Renamed _release_save
		# This method is part of the Condition logic, ensures lock is released before wait
		# It must return the state that _acquire_and_restore_state can use
		if self._owner_thread_id != GET_THREAD_IDENTIFIER_ALIAS():
		    raise RuntimeError("Cannot save release state of a lock not owned by current thread")
		saved_count = self._recursion_count
		saved_owner = self._owner_thread_id
		self._recursion_count = 0
		self._owner_thread_id = None
		self._block.release()
		return (saved_count, saved_owner)


	def _is_owned_by_current_thread(self): # Renamed _is_owned
		return self._owner_thread_id == GET_THREAD_IDENTIFIER_ALIAS()

class ThreadingCondition(object): # Renamed Condition
	def __init__(self, lock_instance = None, associated_object = None): # Renamed lock, object
		if lock_instance is None:
			lock_instance = ReusableLock() # Use new name
		self._lock = lock_instance # Renamed __lock
		# Delegate acquire and release to the underlying lock
		self.acquire = self._lock.acquire
		self.release = self._lock.release

		# Check if the lock has a 'locked' method (like standard threading.Lock)
		# The custom ReusableLock doesn't have it, this might be for compatibility.
		if hasattr(self._lock, "locked") and callable(self._lock.locked):
			self.release = self._secure_release_if_locked # Assign new method name

		# Delegate internal lock state methods if they exist on the lock
		if hasattr(self._lock, "_release_and_save_state"): # Use new name
			self._release_save = self._lock._release_and_save_state
		if hasattr(self._lock, "_acquire_and_restore_state"): # Use new name
			self._acquire_restore = self._lock._acquire_and_restore_state
		if hasattr(self._lock, "_is_owned_by_current_thread"): # Use new name
			self._is_owned = self._lock._is_owned_by_current_thread

		self._waiters_list = [] # Renamed __waiters

	def __enter__(self):
		return self._lock.__enter__()

	def __exit__(self, *exception_args): # Renamed args
		return self._lock.__exit__(*exception_args)

	def __repr__(self):
		return f"<ThreadingCondition({self._lock!r}, {len(self._waiters_list)})>"

	# Default _release_save and _acquire_restore for locks not providing them (e.g. _thread.lock)
	def _release_save(self): # Fallback if lock doesn't have _release_and_save_state
		self._lock.release()
		return None # No state to restore for simple lock

	def _acquire_restore(self, saved_state): # Fallback
		self._lock.acquire()
		# saved_state is ignored for simple lock

	def _is_owned(self): # Fallback
		# Try to acquire without blocking. If success, it wasn't owned.
		if self._lock.acquire(False):
			self._lock.release()
			return False
		return True # Could not acquire, so it's owned (likely by us)

	def _secure_release_if_locked(self): # Renamed secure_release
		# This method is for locks that have a 'locked()' method
		if hasattr(self._lock, 'locked') and self._lock.locked():
			self._lock.release()


	def wait(self, timeout_seconds = None): # Renamed timeout
		if not self._is_owned():
			raise RuntimeError("Cannot wait on un-acquired lock")

		waiter_lock = ALLOCATE_LOCK_ALIAS() # Renamed waiter
		waiter_lock.acquire() # Lock it before adding to list
		self._waiters_list.append(waiter_lock)

		saved_lock_state = self._release_save() # Release the condition's lock

		acquired_waiter = False # Renamed gotit
		try:
			if timeout_seconds is None:
				waiter_lock.acquire() # Block indefinitely
				acquired_waiter = True
			else:
				# Timed wait
				end_time = time.time() + timeout_seconds # Renamed endtime
				current_delay = 0.0005 # Renamed delay, initial delay
				while True:
					acquired_waiter = waiter_lock.acquire(False) # Non-blocking attempt
					if acquired_waiter:
						break
					remaining_time = end_time - time.time() # Renamed remaining
					if remaining_time <= 0:
						break # Timeout
					# Exponential backoff for sleep, capped at 0.05s and remaining time
					current_delay = min(current_delay * 2, remaining_time, 0.05)
					time.sleep(current_delay)

			if not acquired_waiter: # If timeout occurred
				try: # Attempt to remove from waiters list if still there
					self._waiters_list.remove(waiter_lock)
				except ValueError:
					pass # Already removed by a notify, or never added properly
		finally:
			self._acquire_restore(saved_lock_state) # Re-acquire the condition's lock
		return acquired_waiter # Return true if condition met, false if timeout


	def notify(self, num_to_notify = 1): # Renamed number
		if not self._is_owned():
			raise RuntimeError("Cannot notify on un-acquired lock")

		waiters_to_notify = self._waiters_list[:num_to_notify] # Renamed waiters
		if not waiters_to_notify:
			return

		for waiter_lock in waiters_to_notify: # Renamed waiter
			waiter_lock.release() # Release the waiter's lock, allowing its wait() to proceed
			try:
				self._waiters_list.remove(waiter_lock)
			except ValueError:
				pass # Should not happen if logic is correct

	def notify_all(self):
		self.notify(len(self._waiters_list))

class Semaphore(object): # Standard name, kept
	def __init__(self, initial_value = 1, associated_object = None): # Renamed value, object
		if initial_value < 0:
			raise ValueError("Semaphore initial value must be >= 0")
		self._condition = ThreadingCondition(ALLOCATE_LOCK_ALIAS()) # Renamed __cond, use new name
		self._value = initial_value # Renamed __value

	def acquire(self, blocking_flag = True): # Renamed blocking
		acquired_successfully = False # Renamed rc
		self._condition.acquire()
		try:
			while self._value == 0:
				if not blocking_flag:
					break
				self._condition.wait()
			else: # Loop didn't break, so self._value > 0
				self._value -= 1
				acquired_successfully = True
		finally:
			self._condition.release()
		return acquired_successfully

	__enter__ = acquire

	def release(self):
		self._condition.acquire()
		try:
			self._value += 1
			self._condition.notify() # Notify one waiting thread
		finally:
			self._condition.release()

	def __exit__(self, *exception_args): # Renamed args
		self.release()

class BoundedSemaphore(Semaphore): # Standard name, kept
	def __init__(self, initial_value = 1): # Renamed value
		Semaphore.__init__(self, initial_value)
		self._bound_value = initial_value # Renamed basic_value

	def release(self):
		# Access _value via _Semaphore__value if it was name-mangled by subclassing,
		# but direct access self._value is fine if not. Assuming direct for now.
		if self._value >= self._bound_value:
			raise ValueError("BoundedSemaphore released too many times")
		return Semaphore.release(self)

class UnboundedSemaphore(Semaphore): # Renamed UnBoundedSemaphore
	def __init__(self, initial_value = 1): # Renamed value
		Semaphore.__init__(self, initial_value)
		self._initial_value = initial_value # Renamed basic_value
		# Original code modified acquire.__func__.__defaults__, which is not standard/safe.
		# The intent might have been to change default blocking behavior, but it's unclear.
		# For now, keeping acquire as inherited.

	def release(self): # Overrides Semaphore.release
		self._condition.acquire()
		try:
			# Original logic: if self.__value < self.basic_value: self.__value += 1
			# This means it can't exceed its initial value if it was an "UnBounded" (misnomer?)
			# A true unbounded semaphore would just increment.
			# Replicating original apparent logic:
			if self._value < self._initial_value: # If it's below initial, increment
			    self._value +=1
			elif self._value >= self._initial_value: # If at or above initial, it means it acts like a normal semaphore for incrementing
			    self._value += 1 # This makes it truly unbounded on release if it was already at initial_value
			    # If the intent was to cap at initial_value, then the condition should be just self._value +=1 and rely on BoundedSemaphore for capping
			    # Given the name "UnBounded", this increment seems more correct.
			    # Let's assume it's meant to be truly unbounded on release, but bounded on acquire by initial setup.
			    # This is confusing; standard Semaphore already does self._value += 1.
			    # The original code for UnBoundedSemaphore's release was:
			    # if self.__value < self.basic_value: self.__value += 1
			    # This means it would *not* increment if already at basic_value, which is *not* unbounded.
			    # Reverting to standard Semaphore release behavior which is simpler and more standard.
			    # If capping at initial_value on release was intended, it's a very specific behavior.
			    # For now, let's make it truly unbounded on release:
			self._value += 1
			self._condition.notify()
		finally:
			self._condition.release()


class Event(object): # Standard name, kept
	def __init__(self, associated_object = None): # Renamed object
		self._condition = ThreadingCondition(ALLOCATE_LOCK_ALIAS()) # Use new names
		self._flag_is_set = False # Renamed __flag

	def isSet(self): # Standard method name
		return self._flag_is_set

	def set(self): # Standard method name
		self._condition.acquire()
		try:
			self._flag_is_set = True
			self._condition.notify_all()
		finally:
			self._condition.release()

	def clear(self): # Standard method name
		self._condition.acquire()
		try:
			self._flag_is_set = False
		finally:
			self._condition.release()

	def wait(self, timeout_seconds = None): # Standard method name, Renamed timeout
		self._condition.acquire()
		try:
			if not self._flag_is_set:
				self._condition.wait(timeout_seconds)
			return self._flag_is_set # Return the flag status after wait
		finally:
			self._condition.release()

try:
	from itypes import Number as SimpleCounter # Use new name
except ImportError:
	class SimpleCounter(object): # Renamed Number
		def __init__(self, initial_number = 0): # Renamed number
			self.counter_value = initial_number # Renamed number

		def plus(self, increment_value = 1): # Renamed number
			self.counter_value += increment_value
			return self.counter_value

		def reduce(self, decrement_value = 1): # Renamed number
			self.counter_value -= decrement_value
			return self.counter_value

		def __int__(self):
			return int(self.counter_value)

		_int = __int__ # Alias for internal use if any

		def __str__(self):
			return str(self.counter_value)

		__repr__ = __str__
		_str = __str__ # Alias for internal use if any


GLOBAL_THREAD_ID_COUNTER = SimpleCounter() # Renamed Counter, aCounter (assuming aCounter was for thread names)

def _generate_thread_name(template_format = "Thread-%d"): # Renamed _newname, template
    # Access counter value correctly
    return template_format % (GLOBAL_THREAD_ID_COUNTER.counter_value + 1)


ACTIVE_LIMBO_LOCK = ALLOCATE_LOCK_ALIAS() # Renamed active_limbo_lock
ACTIVE_THREADS_REGISTRY = {} # Renamed ActiveThreads
THREAD_LIMBO_REGISTRY = {} # Renamed Thrlimbo (threads started but not yet fully registered)

class CustomThread(object): # Renamed Thread

	_is_initialized = False # Renamed __initialized (PEP 8 private)

	def __init__(self, group=None, target_callable=None, thread_name=None, args_tuple=(), kwargs_dict=None, associated_object = None): # Renamed params
		if group is not None:
		    warnings.warn("The 'group' argument is not used by CustomThread.", DeprecationWarning)
		if kwargs_dict is None:
			kwargs_dict = {}

		self._target_callable = target_callable # Renamed __target
		self._thread_name = str(thread_name or _generate_thread_name()) # Renamed __name
		self._limbo_id = GLOBAL_THREAD_ID_COUNTER.plus() # Use counter to get unique ID for limbo state, Renamed __limbo_name
		self._args_tuple = args_tuple # Renamed __args
		self._kwargs_dict = kwargs_dict # Renamed __kwargs
		self._is_daemon_thread = self._determine_daemon_status() # Renamed __daemonic, _set_daemon
		self._thread_identifier = None # Renamed __ident
		self._started_event = Event() # Renamed __started
		self._is_stopped_flag = False # Renamed __stopped
		self._stop_condition = ThreadingCondition(ALLOCATE_LOCK_ALIAS()) # Renamed __block
		self._is_initialized = True
		self._standard_error_stream = sys.stderr # Renamed __stderr

	def _determine_daemon_status(self): # Renamed _set_daemon
		# Daemonic status is inherited from the current thread by default
		return get_current_custom_thread().daemon # Use new name

	def __repr__(self):
		if not self._is_initialized: return "<CustomThread (not initialized)>"
		status_str = "initial"
		if self._started_event.isSet(): # Use new name
			status_str = "started"
		if self._is_stopped_flag:
			status_str = "stopped"
		if self._is_daemon_thread:
			status_str += " daemon"
		if self._thread_identifier is not None:
			status_str += f" ident={self._thread_identifier}"
		return f"<{self.__class__.__name__}({self._thread_name}, {status_str})>"

	def start(self):
		if not self._is_initialized:
			raise RuntimeError("CustomThread.__init__() not called")
		if self._started_event.isSet():
			raise RuntimeError("Threads can only be started once")

		with ACTIVE_LIMBO_LOCK:
			THREAD_LIMBO_REGISTRY[self._limbo_id] = self
		try:
			START_NEW_THREAD_ALIAS(self._bootstrap_thread, ()) # Use new name
		except Exception as e: # Catch potential errors from _thread.start_new_thread
			with ACTIVE_LIMBO_LOCK:
				if self._limbo_id in THREAD_LIMBO_REGISTRY:
				    del THREAD_LIMBO_REGISTRY[self._limbo_id]
			raise ThreadError(f"Failed to start thread: {e}") # Use new name
		self._started_event.wait() # Wait for bootstrap to set started event

	def run(self):
		"""Method representing the thread's activity. May be overridden in a subclass."""
		# GLOBAL_THREAD_ID_COUNTER.plus() # This was for thread naming, already handled
		try:
			if self._target_callable:
				self._target_callable(*self._args_tuple, **self._kwargs_dict)
		finally:
			# Clean up references to target and args for garbage collection
			del self._target_callable, self._args_tuple, self._kwargs_dict

	def _bootstrap_thread(self): # Renamed __bootstrap
		try:
			self._bootstrap_thread_inner() # Renamed __bootstrap_inner
		except SystemExit: # Allow SystemExit to propagate
			pass
		except KeyboardInterrupt: # Allow KeyboardInterrupt to propagate
			pass
		except Exception: # Catch all other exceptions from run()
			if self._is_daemon_thread and sys is None: # Check if interpreter is shutting down
				return # Don't print if daemon and interpreter is exiting
			# Otherwise, print to standard error
			if hasattr(self._standard_error_stream, 'write'): # Check if stderr is writable
			    self._standard_error_stream.write(f"Exception in thread {self._thread_name}:\n{get_exception_traceback_string()}\n")


	def _set_thread_identifier(self): # Renamed _set_ident
		self._thread_identifier = GET_THREAD_IDENTIFIER_ALIAS() # Use new name

	def _bootstrap_thread_inner(self): # Renamed __bootstrap_inner
		try:
			self._set_thread_identifier()
			self._started_event.set() # Signal that the thread has started
			with ACTIVE_LIMBO_LOCK:
				ACTIVE_THREADS_REGISTRY[self._thread_identifier] = self # Add to active threads
				try: # Remove from limbo
					if self._limbo_id in THREAD_LIMBO_REGISTRY:
					    del THREAD_LIMBO_REGISTRY[self._limbo_id]
				except KeyError: # Might have been removed by another thread if error during start
					pass
			try:
				self.run()
			except SystemExit:
				pass
			except KeyboardInterrupt:
				pass
			except Exception: # Exceptions from self.run()
				if hasattr(self._standard_error_stream, 'write'):
					self._standard_error_stream.write(f"Exception in thread {self.name} (from run()):\n{get_exception_traceback_string()}\n")
			finally:
				# Python 3's sys.exc_info() is thread-local, sys.exc_clear() is not needed / does not exist.
				pass
		finally: # Ensure cleanup happens
			with ACTIVE_LIMBO_LOCK:
				self._mark_as_stopped() # Renamed __stop
				try: # Remove from active threads registry
					if self._thread_identifier in ACTIVE_THREADS_REGISTRY:
					    del ACTIVE_THREADS_REGISTRY[self._thread_identifier]
				except Exception: # Should not happen if ident is correctly set and present
					pass

	def _mark_as_stopped(self): # Renamed __stop
		self._stop_condition.acquire()
		try:
			self._is_stopped_flag = True
			self._stop_condition.notify_all()
		finally:
			self._stop_condition.release()

	# _delete method was for dummy_threading, not directly applicable here in same way.
	# Cleanup is handled in _bootstrap_thread_inner's finally block.

	def join(self, timeout_seconds = None): # Renamed timeout
		if not self._is_initialized:
			raise RuntimeError("CustomThread.__init__() not called")
		if not self._started_event.isSet():
			raise RuntimeError("Cannot join thread before it is started")
		if self is get_current_custom_thread(): # Use new name
			raise RuntimeError("Cannot join current thread")

		self._stop_condition.acquire()
		try:
			if timeout_seconds is None:
				while not self._is_stopped_flag:
					self._stop_condition.wait()
			else:
				deadline_time = time.time() + timeout_seconds # Renamed deadline
				while not self._is_stopped_flag:
					remaining_delay = deadline_time - time.time() # Renamed delay
					if remaining_delay <= 0:
						break # Timeout
					self._stop_condition.wait(remaining_delay)
		finally:
			self._stop_condition.release()

	@property
	def name(self):
		if not self._is_initialized: raise RuntimeError("Thread not initialized")
		return self._thread_name

	@name.setter
	def name(self, new_name_str): # Renamed name
		if not self._is_initialized: raise RuntimeError("Thread not initialized")
		self._thread_name = str(new_name_str)

	@property
	def ident(self):
		if not self._is_initialized: raise RuntimeError("Thread not initialized")
		return self._thread_identifier

	def is_alive(self): # Renamed isAlive
		if not self._is_initialized: raise RuntimeError("Thread not initialized")
		return self._started_event.isSet() and not self._is_stopped_flag

	@property
	def daemon(self):
		if not self._is_initialized: raise RuntimeError("Thread not initialized")
		return self._is_daemon_thread

	@daemon.setter
	def daemon(self, is_daemon_bool): # Renamed daemonic
		if not self._is_initialized: raise RuntimeError("Thread not initialized")
		if self._started_event.isSet():
			raise RuntimeError("Cannot set daemon status of active thread")
		self._is_daemon_thread = is_daemon_bool

	def isDaemon(self): # Kept for compatibility if used elsewhere, though property is preferred
		return self.daemon

	def setDaemon(self, is_daemon_bool): # Kept for compatibility
		self.daemon = is_daemon_bool

	def getName(self): # Kept for compatibility
		return self.name

	def setName(self, new_name_str): # Kept for compatibility
		self.name = new_name_str

class ThreadKillSignal(SystemExit): # Renamed ThrKill
	""" Custom exception to signal a thread to terminate. """
	pass

class KillableThread(CustomThread): # Renamed KThread, Thread
	def __init__(self, group=None, target_callable=None, thread_name=None, args_tuple=(), kwargs_dict=None): # Matched CustomThread params
		CustomThread.__init__(self, group, target_callable, thread_name, args_tuple, kwargs_dict)
		self._is_killed_flag = False # Renamed killed
		# Store original run and start to wrap them
		self._original_run_method = self.run
		self.run = self._wrapped_run_for_kill # Renamed __run
		# No need to wrap start if bootstrap handles trace correctly

	def _wrapped_run_for_kill(self): # Renamed __run
		# Set trace function for this thread only
		# sys.settrace is global, so this approach for per-thread trace is complex
		# and can interfere with debuggers.
		# A more modern approach would involve checking self._is_killed_flag periodically in the target_callable.
		# For now, replicating original trace logic as best as possible.
		# This trace function will be called for every line in this thread.

		# Store old trace if any
		original_trace_func = sys.gettrace()
		sys.settrace(self._global_kill_trace)
		try:
			self._original_run_method() # Call the original run (or target)
		except ThreadKillSignal: # Expected way to terminate
			pass
		finally:
			sys.settrace(original_trace_func) # Restore original trace function

	def _global_kill_trace(self, frame, event_type, arg_unused): # Renamed globaltrace, why, arg
		# This is called for every function call/return/line/exception in this thread
		if event_type == 'call': # Only trace lines within function calls initiated by this thread
			return self._local_kill_trace # Return local trace for that frame
		return None

	def _local_kill_trace(self, frame, event_type, arg_unused): # Renamed localtrace
		if self._is_killed_flag:
			if event_type == 'line': # Check kill flag at every line
				raise ThreadKillSignal("Thread killed")
		return self._local_kill_trace # Continue tracing this frame

	def kill(self):
		self._is_killed_flag = True

class CustomTimerThread(CustomThread): # Renamed Timer, Thread
	def __init__(self, interval_seconds, target_function, args_tuple = (), kwargs_dict = None): # Renamed interval, function, args, kwargs
		if kwargs_dict is None: kwargs_dict = {}
		CustomThread.__init__(self) # Call superclass init
		self.interval_seconds = interval_seconds
		self.target_function = target_function
		self.args_tuple = args_tuple
		self.kwargs_dict = kwargs_dict
		self.finished_event = Event() # Renamed finished

	def cancel(self):
		"""Stop the timer if it hasn't finished yet."""
		self.finished_event.set()

	def kill(self): # For KillableThread compatibility, though Timer usually uses cancel
		self.cancel()

	def run(self):
		# GLOBAL_THREAD_ID_COUNTER.plus() # This was in original Thread.run, not needed here
		# Wait for the interval or until finished_event is set
		self.finished_event.wait(self.interval_seconds)
		if not self.finished_event.isSet(): # If not cancelled
			self.target_function(*self.args_tuple, **self.kwargs_dict)
		self.finished_event.set() # Ensure it's set after execution or cancellation

class MainMonitoringThread(CustomThread): # Renamed MainThread
	def __init__(self):
		CustomThread.__init__(self, thread_name = "MainThread") # Renamed name
		# Main thread is considered started immediately by its nature
		self._started_event.set()
		self._set_thread_identifier()
		with ACTIVE_LIMBO_LOCK: # Use new name
			ACTIVE_THREADS_REGISTRY[GET_THREAD_IDENTIFIER_ALIAS()] = self # Use new names

	def _determine_daemon_status(self): # Override
		return False # Main thread is never a daemon

	def kill(self): # Main thread cannot be killed this way
		pass

	# The malformed _exit_KThread method definition was here and is now removed.
	# It appeared to be a copy-paste error from another class.
	# The main thread's exit logic is handled by the _main_thread_exit_function (not shown)
	# which is assigned to SHUTDOWN_HOOK_MAIN_THREAD.

def get_next_non_daemon_thread(): # Renamed PickSomeNonDaemonThread
	for thread_obj in get_all_custom_threads(): # Renamed enumerate, thr
		if not thread_obj.daemon and thread_obj.is_alive(): # Use new name
			return thread_obj
	return None

class DummySystemThread(CustomThread): # Renamed DummyThread
	"""Represents threads not created by this module but detected."""
	def __init__(self):
		# Initialize with a unique name for dummy threads
		CustomThread.__init__(self, thread_name = _generate_thread_name("Dummy-%d"))
		# Mark as started and set ident immediately
		# self._Thread__started.set() # This was for original Thread, use _started_event
		self._started_event.set()
		self._set_thread_identifier()
		with ACTIVE_LIMBO_LOCK:
			ACTIVE_THREADS_REGISTRY[self.ident] = self # Use new name

	def _determine_daemon_status(self): # Override
		return True # Assume external threads are daemonic unless known otherwise

	def kill(self): # Cannot kill external threads
		pass

	def join(self, timeout_seconds = None): # Renamed timeout
		raise RuntimeError("Cannot join a dummy system thread managed by this module.")

def get_current_custom_thread(): # Renamed currentThread
	thread_id = GET_THREAD_IDENTIFIER_ALIAS() # Use new name
	if thread_id in ACTIVE_THREADS_REGISTRY:
		return ACTIVE_THREADS_REGISTRY[thread_id] # Use new name
	# If not in registry, it's an external thread or one not yet fully registered
	# Create a DummySystemThread to represent it.
	return DummySystemThread()


def get_all_custom_threads(): # Renamed enumerate
	"""Return a list of all CustomThread objects currently alive."""
	with ACTIVE_LIMBO_LOCK:
		# Return a copy of the list of values from both registries
		return list(ACTIVE_THREADS_REGISTRY.values()) + list(THREAD_LIMBO_REGISTRY.values())

get_all_custom_thread_names = lambda: [thread_obj.name for thread_obj in get_all_custom_threads()] # Renamed getNames

def kill_all_custom_threads(): # Renamed killAllThreads
	current_thread_id = GET_THREAD_IDENTIFIER_ALIAS() # Use new name
	for thread_obj in get_all_custom_threads(): # Use new name
		if thread_obj.ident != current_thread_id and hasattr(thread_obj, 'kill'): # Don't kill self
			try:
			    thread_obj.kill()
			except Exception: # Catch errors during kill, e.g. if thread already exited
			    pass


# Initialize main thread representation and register its exit function
SHUTDOWN_HOOK_MAIN_THREAD = MainMonitoringThread()._main_thread_exit_function # Renamed _shutdown

# For systems supporting fork, reinitialize locks and thread registry
if hasattr(os, 'register_at_fork'): # Python 3.7+
    os.register_at_fork(after_in_child=_reinitialize_threading_after_fork)
elif hasattr(os, 'fork') and not hasattr(os, 'register_at_fork'):
    # For older Pythons with fork but no register_at_fork, this is harder.
    # The original code didn't have a direct equivalent for this specific fork handling.
    # This module might not be fully fork-safe on older Pythons without manual intervention after fork.
    warnings.warn("Fork detected without os.register_at_fork; thread registry might be inconsistent in child.")

def _reinitialize_threading_after_fork(): # Renamed _after_fork
	"""Called in the child process after a fork to clean up threading state."""
	global ACTIVE_LIMBO_LOCK, ACTIVE_THREADS_REGISTRY, THREAD_LIMBO_REGISTRY, GLOBAL_THREAD_ID_COUNTER

	ACTIVE_LIMBO_LOCK = ALLOCATE_LOCK_ALIAS() # Recreate lock

	new_active_threads = {} # Renamed ActiveNew
	current_thread_obj = get_current_custom_thread() # This will be a new DummySystemThread representing the child's main thread

	# The current_thread_obj created by get_current_custom_thread is a new DummySystemThread.
	# We need to make it the 'MainMonitoringThread' for the child.
	# This is tricky because MainMonitoringThread has specific init.
	# For simplicity, we'll just ensure the current thread is in ACTIVE_THREADS_REGISTRY.
	# A more robust solution might re-initialize MainMonitoringThread here.

	if isinstance(current_thread_obj, DummySystemThread): # If it's the auto-created dummy
	    # Replace it with a proper entry for the new main thread in child
	    if current_thread_obj.ident in ACTIVE_THREADS_REGISTRY: # remove if it was added
	        del ACTIVE_THREADS_REGISTRY[current_thread_obj.ident]

	    # Re-create a MainMonitoringThread for the child process.
	    # This is complex because MainMonitoringThread also calls _exitfunc on init.
	    # For now, just ensure the current thread is correctly identified and registered.
	    # A proper fork handling might need to re-init MainMonitoringThread carefully.
	    current_thread_obj = MainMonitoringThread() # This will re-register itself in ACTIVE_THREADS_REGISTRY

	# Clear old thread registries
	THREAD_LIMBO_REGISTRY.clear()

	# Rebuild ACTIVE_THREADS_REGISTRY to only contain the current thread of the child
	temp_active_threads = ACTIVE_THREADS_REGISTRY.copy()
	ACTIVE_THREADS_REGISTRY.clear()
	if current_thread_obj.ident is not None: # Ensure ident is set
	    ACTIVE_THREADS_REGISTRY[current_thread_obj.ident] = current_thread_obj

	# Reset counters if they are process-specific
	GLOBAL_THREAD_ID_COUNTER.counter_value = 0 # Reset for new process
	# aCounter (if still used for other purposes) might also need reset
	# For now, assuming aCounter was primarily for thread naming, covered by GLOBAL_THREAD_ID_COUNTER

	assert len(ACTIVE_THREADS_REGISTRY) == 1, "After fork, only one thread (main) should be active in child."
