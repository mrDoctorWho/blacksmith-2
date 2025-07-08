#!/usr/bin/python3
# coding: utf-8

# BlackSmith's core mark.2
# BlackSmith.py

# Code © (2010-2013) by WitcherGeralt [alkorgun@gmail.com]

# imports

from types import InstanceType, GeneratorType # NoneType not used directly in Py3
from traceback import print_exc as print_exception_traceback
from random import shuffle, randrange, choice
from re import compile as regex_compile
import subprocess # For get_pipe

import sys, os, gc, time, shutil, configparser # Was ConfigParser
import ast # For literal_eval

BS_CORE_PATH = getattr(sys.modules["__main__"], "__file__", None)
if BS_CORE_PATH:
	BS_CORE_PATH = os.path.abspath(BS_CORE_PATH)
	BS_ROOT_PATH = os.path.dirname(BS_CORE_PATH)
	if BS_ROOT_PATH:
		os.chdir(BS_ROOT_PATH)
else:
	BS_ROOT_PATH = os.getcwd()

from enconf import * # Keep wildcard for now, though specific imports are better

import xmpp # Original xmpp library
import ithr # Keep original name for now
import itypes # Keep original name for now

# Cache & Statistics

COLORS_ENABLED = hasattr(xmpp.debug, 'colors_enabled') and xmpp.debug.colors_enabled # Use original attribute name

COLOR_NONE = chr(27) + "[0m" # none
COLOR_YELLOW = chr(27) + "[33m" # yellow
COLOR_RED = chr(27) + "[31;1m" # red
COLOR_GREEN = chr(27) + "[32m" # green
COLOR_BLUE = chr(27) + "[34;1m" # blue

# OS_COMMANDS_DB - was already pruned in a previous step, keeping that change.
OS_COMMANDS_DB = [
	"COLOR F0", # 0: Set console color (Windows)
	"Title"     # 1: Set console title (Windows)
]


# Basic XMPP stanza related string constants (original names kept)
sBase = (
	"chat", "groupchat", "normal", "available", "unavailable", "subscribe",
	"answer", "error", "result", "set", "get", "jid", "nick",
	"dispatch", "request", "received", "ping", "time", "query"
)

aRoles = (
	"affiliation", "outcast", "none", "member", "admin", "owner",
	"role", "visitor", "participant", "moderator"
)

sList = ("chat", "away", "xa", "dnd")

aDesc = {"owner": 3, "moderator": 3, "admin": 2, "participant": 1, "member": 1}

sCodesDesc = {"301": "has-been-banned", "303": "nick-changed", "307": "has-been-kicked", "407": "members-only"}
sCodes = sorted(sCodesDesc.keys())

eCodesDesc = {
	"302": "redirect", "400": "unexpected-request", "401": "not-authorized",
	"402": "payment-required", "403": "forbidden", "404": "remote-server-not-found",
	"405": "not-allowed", "406": "not-acceptable", "407": "subscription-required",
	"409": "conflict", "500": "undefined-condition", "501": "feature-not-implemented",
	"503": "service-unavailable", "504": "remote-server-timeout"
}
eCodes = sorted(eCodesDesc.keys())

IqXEPs = (
	xmpp.NS_VERSION, xmpp.NS_PING, xmpp.NS_TIME, xmpp.NS_URN_TIME,
	xmpp.NS_LAST, xmpp.NS_DISCO_INFO
)

XEPs = set(IqXEPs + (
	xmpp.NS_CAPS, xmpp.NS_SASL, xmpp.NS_TLS, xmpp.NS_MUC,
	xmpp.NS_ROSTER, xmpp.NS_RECEIPTS
))

isJID = regex_compile("^.+?@[\w-]+?\.[\.\w-]+?$", 32)

VarCache = { # Keep original names for now
	"idle": 0.24, "alive": True, "errors": [],
	"action": "# %s %s &" % (os.path.basename(sys.executable), BS_CORE_PATH)
}

Info = { # Keep original names for now
	"cmd": itypes.Number(), "sess": time.time(), "msg": itypes.Number(),
	"alls": [], "cfw": itypes.Number(), "up": 1.24, "prs": itypes.Number(),
	"iq": itypes.Number(), "errors": itypes.Number(), "omsg": itypes.Number(),
	"outiq": itypes.Number()
}

# Useful features

class SelfExc(Exception): # Keep original name
	pass

# check_sqlite was removed as dead code

def current_exception_info(): # Renamed from exc_info
	exc_type, exc_value, _traceback = sys.exc_info()
	if exc_type and exc_value:
		exc_name = exc_type.__name__
		err_msg = exc_value.args[0] if exc_value.args else str(exc_value)
		return (exc_name, err_msg)
	return (None, None)

def record_exception_traceback(file_pointer=None): # Renamed from exc_info_
	try:
		print_exception_traceback(file=file_pointer or sys.stderr)
	except Exception:
		pass

# sleep alias can be removed if time.sleep is used directly
# database alias can be removed if itypes.Database is used directly

# get_exc was removed as dead code

def format_error_string(error_obj, format_template="%s - %s"): # Renamed from exc_str
	error_class_name = error_obj.__class__.__name__
	error_message = error_obj.args[0] if error_obj.args else str(error_obj)
	return format_template % (error_class_name, error_message)

# apply_function was removed as dead code (renamed from apply)

def colorize_text(text, color_code): # Renamed from text_color
	if COLORS_ENABLED and color_code:
		text = f"{color_code}{text}{COLOR_NONE}"
	return text

def Print(text_to_print, color_code=None): # Keep original name, ensure `print` is function
	try:
		print(colorize_text(text_to_print, color_code))
	except Exception:
		pass

def interruptible_sleep(duration_seconds): # Renamed from try_sleep
	try:
		time.sleep(duration_seconds)
	except KeyboardInterrupt:
		os._exit(0) # Consider a more graceful shutdown
	except: # Catching bare except is bad practice
		pass

def Exit(message_text, exit_code, sleep_duration): # Keep original name
	Print(message_text, COLOR_RED)
	interruptible_sleep(sleep_duration)
	if exit_code: # Assuming exit_code non-zero means direct exit
		os._exit(exit_code) # Use exit_code passed
	else: # Assuming exit_code zero means reload
		os.execl(sys.executable, sys.executable, BS_CORE_PATH)

# Removed: reload(sys) and sys.setdefaultencoding("utf-8") as they are Py2 specific

stdout_filepath = "stdout.tmp" # Renamed from stdout
if not sys.stdin.isatty():
	file_mode = "wb"
	if os.path.isfile(stdout_filepath):
		if os.path.getsize(stdout_filepath) >= 131072:
			file_mode = "wb"
		else:
			file_mode = "ab"
	try:
		# Use a variable name that doesn't shadow sys.stdout for the stream object
		actual_stdout_stream = open(stdout_filepath, file_mode, buffering=0)
		sys.stdout = actual_stdout_stream
		sys.stderr = actual_stdout_stream
		if COLORS_ENABLED: # Check if COLORS_ENABLED needs to be global or passed
			COLORS_ENABLED = False
	except IOError as e:
		original_stderr = sys.__stderr__
		if original_stderr:
			original_stderr.write(f"CRITICAL: Could not open log file {stdout_filepath}: {e}\n")
else:
	pass # sys.stdout is already the TTY

# Important Variables (original names kept)
static = "static/%s"
dynamic = "current/%s"
ExpsDir = "expansions"
FailDir = "exceptions"
PidFile = "sessions.db"
GenCrash = "dispatcher.crash"
SvnCache = ".svn/entries"
GenInscFile = static % ("insc.py")
GenConFile = static % ("config.ini")
ConDispFile = static % ("clients.ini")
ChatsFile = dynamic % ("chats.db")
ChatsFileBackup = dynamic % ("chats.cp")

(BsMark, BsVer, BsRev) = (2, 52, 0)

if os.access(SvnCache, os.R_OK):
	try: # Added try-except for file operations
		with open(SvnCache, "r") as CacheFile: # Use with statement
			Cache = CacheFile.readlines()
		if len(Cache) > 3:
			BsRev_str = Cache[3].strip()
			if BsRev_str.isdigit():
				BsRev = int(BsRev_str)
			else:
				BsRev = 0 # Default if not digit
	except IOError: # Catch file errors
		BsRev = 0


ProdName = "BlackSmith mark.%d" % (BsMark)
ProdVer = "%d (r.%s)" % (BsVer, str(BsRev)) # BsRev might be int or str, ensure consistent
Caps = "http://blacksmith-2.googlecode.com/svn/"
CapsVer = "%d.%d" % (BsMark, BsVer)
FullName = "HellDev's %s Ver.%s (%s)" % (ProdName, ProdVer, Caps)

BotOS, BsPid = os.name, os.getpid()
OSList = ((BotOS == "nt"), (BotOS == "posix"))

def client_config_parser(config, section): # Renamed client_config
	serv = config.get(section, "serv").lower()
	port_str = config.get(section, "port") # Keep as string first
	port = int(port_str) if port_str.isdigit() else 5222
	user = config.get(section, "user").lower()
	host = config.get(section, "host").lower()
	password = config.get(section, "pass")
	jid = "%s@%s" % (user, host)
	return (jid, (serv, port, host, user, password))

try:
	GenCon = configparser.ConfigParser() # Was ConfigParser
	GenCon.read(GenConFile)
	GenDisp, Instance = client_config_parser(GenCon, "CLIENT")
	InstancesDesc = {GenDisp: Instance}
	# Use getboolean for these config values
	ConTls = GenCon.getboolean("STATES", "TLS")
	Mserve = GenCon.getboolean("STATES", "MSERVE")
	GetExc = GenCon.getboolean("STATES", "GETEXC")
	DefLANG = GenCon.get("STATES", "LANG").upper()[0:2]
	GodName = GenCon.get("CONFIG", "ADMIN").lower()
	DefNick = GenCon.get("CONFIG", "NICK").split()[0]
	DefStatus = GenCon.get("CONFIG", "STATUS")
	GenResource = GenCon.get("CONFIG", "RESOURCE")
	IncLimit = int(GenCon.get("LIMITS", "INCOMING"))
	PrivLimit = int(GenCon.get("LIMITS", "PRIVATE"))
	ConfLimit = int(GenCon.get("LIMITS", "CHAT"))
	MaxMemory = int(GenCon.get("LIMITS", "MEMORY")) * 1024
	ConDisp = configparser.ConfigParser() # Was ConfigParser
	if os.path.isfile(ConDispFile):
		ConDisp.read(ConDispFile)
		for Block in ConDisp.sections():
			Disp, Instance_val = client_config_parser(ConDisp, Block) # Shadowing Instance
			InstancesDesc[Disp] = Instance_val
except Exception as e: # Catch specific exceptions if possible
	Exit(f"\n\nOne of the configuration files is corrupted! Error: {e}", 1, 30)

if 'Instance' in locals(): del Instance # Clean up
if 'Instance_val' in locals(): del Instance_val

MaxMemory = (32768 if (MaxMemory and MaxMemory <= 32768) else MaxMemory)

try:
	# execfile is Python 2. In Python 3, use open, read, compile, exec.
	with open(GenInscFile, "rb") as f: # Read as bytes for compile
		script_content = f.read()
	# The second argument to compile should be a filename string for tracebacks
	compiled_script = compile(script_content, GenInscFile, 'exec')
	exec(compiled_script, globals()) # Execute in current global scope
except Exception as e:
	Exit(f"\n\nError: general inscript ({GenInscFile}) is damaged! Error: {e}", 1, 30)

if OSList[0]: # Is Windows
	os.system(OS_COMMANDS_DB[0]) # COLOR F0
	os.system(f"{OS_COMMANDS_DB[1]} {FullName}") # Title

# lists & dicts (original names kept)
expansions = {}
Cmds = {}
cPrefs = ("!", "@", "#", ".", "*")
sCmds = []
Chats = {}
Guard = {}
Galist = {GodName: 8} if 'GodName' in locals() else {} # Ensure GodName exists
Roster = {"on": True}
Clients = {}
ChatsAttrs = {}
Handlers = {
	"01eh": [], "02eh": [], "03eh": [], "04eh": [], "05eh": [], "06eh": [],
	"07eh": [], "08eh": [], "09eh": [], "00si": [], "01si": [], "02si": [],
	"03si": [], "04si": []
}

Sequence = ithr.Semaphore() # Keep original

# call & execute Threads & handlers (original names kept for now)
def execute_handler(handler_instance, arg_list=(), command_name=None): # Renamed list, command
	try:
		handler_instance(*arg_list)
	except SystemExit: # Allow to propagate
		raise
	except KeyboardInterrupt: # Allow to propagate
		raise
	except SelfExc: # Custom exception, allow to propagate or handle if needed
		pass # Or collectExc(handler_instance, command_name) if SelfExc should be logged
	except Exception:
		collectExc(handler_instance, command_name)

def call_sfunctions(handler_key, arg_tuple=()): # Renamed ls, list
	if handler_key in Handlers: # Check key exists
		for inst in Handlers[handler_key]:
			execute_handler(inst, arg_tuple)

def composeTimer(sleep_interval, target_func, name=None, arg_list=(), command_log_name=None): # Renamed params
	if not name:
		name = f"iTimer-{ithr.aCounter._str()}" # Use original counter name if it exists in ithr
	timer = ithr.Timer(sleep_interval, execute_handler, (target_func, arg_list, command_log_name,))
	timer.name = name
	return timer

def composeThr(target_func, name, arg_list=(), command_log_name=None): # Renamed params
	if not name.startswith(sBase[13]): # "dispatch"
		name = f"{name}-{ithr.aCounter._str()}"
	return ithr.KThread(execute_handler, name, (target_func, arg_list, command_log_name,))

def startThr(thread_instance, retry_count=0): # Renamed thr, number
	if retry_count > 2:
		raise RuntimeError("exit") # Or a more specific error
	try:
		thread_instance.start()
	except ithr.error: # Assuming ithr.error is the specific thread error
		startThr(thread_instance, (retry_count + 1))
	except Exception as e: # Catch other potential errors
		collectExc(thread_instance.start) # Log that starting the thread failed
		# Optional: raise e or a custom error to indicate failure more strongly

def sThread_Run(thread_instance, target_func, command_log_name=None): # Renamed params
	try:
		thread_instance.start()
	except ithr.error:
		try:
			startThr(thread_instance) # Retry logic
		except RuntimeError: # If retries also fail
			try:
				# Check if _run_backup exists and is callable
				if hasattr(thread_instance, '_run_backup') and callable(getattr(thread_instance, '_run_backup')):
					thread_instance._run_backup()
				else: # If no backup, just log the failure of the original target
					collectExc(target_func, command_log_name)
			except Exception:
				collectExc(target_func, command_log_name)
	except Exception:
		collectExc(sThread_Run, command_log_name) # Error in the sThread_Run itself or initial start

def sThread(name_prefix, target_instance, arg_list=(), command_log_name=None): # Renamed params
	thread_obj = composeThr(target_instance, name_prefix, arg_list, command_log_name)
	sThread_Run(thread_obj, target_instance, command_log_name)

def call_efunctions(handler_key, arg_tuple=()): # Renamed ls, list
	if handler_key in Handlers: # Check key exists
		for inst in Handlers[handler_key]:
			sThread(handler_key, inst, arg_tuple)

# expansions & commands (original names kept)
class expansion(object):
	commands, handlers = (), ()
	def __init__(self, name):
		self.name = name
		self.path = os.path.join(ExpsDir, self.name)
		self.file = os.path.join(self.path, "code.py")
		self.isExp = os.path.isfile(self.file)
		self.insc = os.path.join(self.path, "insc.py")
		if not os.path.isfile(self.insc):
			self.insc = None
		self.cmds = []
		self.desc = {}

	def initialize_exp(self):
		expansions[self.name] = self
		if self.insc:
			try:
				self.AnsBase = AnsBase_temp # Relies on AnsBase_temp from insc
			except NameError:
				pass # AnsBase_temp might not be defined if insc is empty/different
		for cmd_config in self.commands: # Renamed ls to cmd_config
			command_handler(self, *cmd_config)
		for inst, handler_key in self.handlers: # Renamed ls to handler_key
			self.handler_register(getattr(self, inst.__name__), handler_key)

	auto_clear = None

	def dels(self, full=False):
		while self.cmds:
			cmd_name = self.cmds.pop() # Renamed cmd
			if cmd_name in Cmds:
				Cmds[cmd_name].off()
		self.clear_handlers()
		self.commands = ()
		self.handlers = ()
		if self.auto_clear:
			execute_handler(self.auto_clear)
		if full and self.name in expansions: # Was has_key
			del expansions[self.name]

	def clear_handlers(self, handler_to_clear=None): # Renamed handler
		def Del(handler_instance, handler_key_str): # Renamed inst, ls
			if handler_key_str == "03si": # System Initialization Exit
				execute_handler(handler_instance)
			self.del_handler(handler_key_str, handler_instance)
			current_handlers = self.desc[handler_key_str] # Renamed list
			current_handlers.remove(handler_instance)
			if not current_handlers:
				del self.desc[handler_key_str]

		if handler_to_clear:
			for handler_key_str, current_handlers in sorted(self.desc.items()): # Was iteritems
				for handler_instance in current_handlers:
					if handler_instance == handler_to_clear:
						Del(handler_instance, handler_key_str)
						return # Found and removed
		else: # Clear all
			# Iterate over a copy of items for safe removal during iteration
			for handler_key_str, current_handlers in list(self.desc.items()):
				for handler_instance in list(current_handlers): # Iterate over a copy of the list
					Del(handler_instance, handler_key_str)

	def initialize_all(self):
		for handler_key, handler_list in sorted(self.desc.items()): # Was iteritems
			if not handler_key.endswith("si"):
				continue
			for handler_instance in handler_list:
				if handler_key in ("00si", "02si"): # Global / Post-connect init
					execute_handler(handler_instance)
				elif handler_key == "01si": # Per-chat init
					for conf_name in list(Chats.keys()): # Was iterkeys, ensure list for Py3
						execute_handler(handler_instance, (conf_name,))

	def load(self):
		if self.name in expansions: # Was has_key
			expansions[self.name].dels()
		exp_instance = None # Initialize
		current_globals = globals().copy() # To pass for execfile simulation
		try:
			if self.insc:
				with open(self.insc, "rb") as f_insc:
					insc_content = f_insc.read()
				exec(compile(insc_content, self.insc, 'exec'), current_globals)

			with open(self.file, "rb") as f_code:
				code_content = f_code.read()
			# Pass current_globals which now includes insc's definitions
			exec(compile(code_content, self.file, 'exec'), current_globals)
			# expansion_temp should be defined in current_globals after exec
			# Ensure expansion_temp is found before calling
			exp_temp_class = current_globals.get('expansion_temp')
			if exp_temp_class:
				exp_instance = exp_temp_class(self.name)
			else:
				# This case should ideally not happen if file structure is correct
				raise NameError("expansion_temp class not found after exec")

			# Check if AnsBase_temp was defined by insc and assign if so
			if 'AnsBase_temp' in current_globals and exp_instance:
			    exp_instance.AnsBase = current_globals['AnsBase_temp']
			elif hasattr(self, 'AnsBase') and 'AnsBase_temp' in current_globals: # If self.AnsBase existed before
				self.AnsBase = current_globals['AnsBase_temp']


		except Exception:
			exc = current_exception_info() # Use new name
		else:
			exc = () # No exception
		return (exp_instance, exc)


	def add_handler(self, handler_key, handler_instance): # Renamed ls, inst
		if handler_key in Handlers and handler_instance not in Handlers[handler_key]: # Check key exists
			Handlers[handler_key].append(handler_instance)

	def del_handler(self, handler_key, handler_instance): # Renamed ls, inst
		if handler_key in Handlers and handler_instance in Handlers[handler_key]: # Check key exists
			Handlers[handler_key].remove(handler_instance)

	def handler_register(self, handler_instance, handler_key): # Renamed inst, ls
		instance_name = handler_instance.__name__ # Renamed name
		if handler_key in Handlers: # Check key exists
			for current_instance in list(Handlers[handler_key]): # Iterate copy for safe removal
				if instance_name == current_instance.__name__:
					self.del_handler(handler_key, current_instance)
		self.add_handler(handler_key, handler_instance)
		self.desc.setdefault(handler_key, []).append(handler_instance)

class Command(object):
	def __init__(self, inst, default_name, name, access, help_path, exp_instance): # Renamed params
		self.exp = exp_instance
		self.default = default_name # Was default
		self.name = name
		self.numb = itypes.Number()
		self.isAvalable = True # Keep original typo for now
		self.help = help_path # Was help
		self.handler = inst
		self.desc = set() # usage stats?
		self.access = access

	def reload(self, inst, access, help_path, exp_instance): # Renamed params
		self.exp = exp_instance
		self.isAvalable = True
		self.handler = inst
		self.help = help_path
		self.access = access

	def off(self):
		self.isAvalable = False
		self.handler = None

	def execute(self, stype, source_tuple, body_str, disp_obj): # Renamed params
		# source_tuple is (source_obj, instance_jid_str, nick_str)
		conf_name_or_jid = source_tuple[1] # instance_jid_str is conf_name for MUC, or user_jid for chat
		nick_str = source_tuple[2]

		if enough_access(conf_name_or_jid, nick_str, self.access):
			if self.isAvalable and self.handler:
				Info["cmd"].plus()
				sThread("command", self.handler, (self.exp, stype, source_tuple, body_str, disp_obj), self.name)
				self.numb.plus()
				# get_source expects (conf_name, nick) or (user_jid, None-like for nick if direct chat)
				# This needs to align with how get_source is defined and used.
				# Assuming for MUC, source_tuple[1] is conf, source_tuple[2] is nick.
				# For chat, source_tuple[1] is user_jid, source_tuple[2] might be resource or nick part of JID.
				# Let's assume get_source handles these cases.
				actual_source_jid_str = get_source(source_tuple[1], source_tuple[2])
				if actual_source_jid_str:
					self.desc.add(actual_source_jid_str)
			else:
				answer = AnsBase[19] % (self.name) # Command unavailable
		else:
			answer = AnsBase[10] # Access denied

		if 'answer' in locals(): # Check if answer was defined
			Answer(answer, stype, source_tuple, disp_obj)


def command_handler(exp_inst, handler, default_name, access, prefix=True): # Renamed params
	path_base = os.path.join(ExpsDir, exp_inst.name, default_name) # Renamed Path
	cmd_names_dict = {} # Renamed commands
	try:
		# Ensure get_file returns string, decode if bytes
		name_file_content = get_file(f"{path_base}.name")
		# Ensure content is not empty before ast.literal_eval
		if name_file_content and name_file_content.strip():
			if isinstance(name_file_content, bytes): name_file_content = name_file_content.decode("utf-8", "replace")
			cmd_names_dict = ast.literal_eval(name_file_content) # Was eval
	except Exception: # Catch parsing errors or file not found
		cmd_names_dict = {} # Default to empty if error

	lang_to_use = DefLANG if DefLANG in cmd_names_dict else "en" # Fallback to 'en' if DefLANG not found or default

	name = cmd_names_dict.get(lang_to_use, default_name) # Use .get with fallback
	# Ensure name is string, original had .decode("utf-8") on cmd_names_dict[DefLANG]
	if isinstance(name, bytes): name = name.decode("utf-8", "replace")

	help_path = f"{path_base}.{lang_to_use.lower()}"
	if lang_to_use == "en" and not os.path.exists(help_path) and DefLANG not in cmd_names_dict: # if default EN name used
	    help_path = f"{path_base}.en" # Ensure .en if that's the actual fallback file name

	if name in Cmds:
		Cmds[name].reload(handler, access, help_path, exp_inst)
	else:
		Cmds[name] = Command(handler, default_name, name, access, help_path, exp_inst)

	if not prefix and name not in sCmds:
		sCmds.append(name)
	exp_inst.cmds.append(name)


# Chats, Users & Other (original names kept)
class sUser(object):
	def __init__(self, nick, role, source, access=None):
		self.nick = nick; self.source = source; self.role = role
		self.ishere = True
		self.date = (time.time(), Yday(), strfTime(local=False))
		self.access = access
		if access is None: # Check for None specifically
			self.calc_acc()

	def aroles(self, role_tuple): # Renamed role
		if self.role != role_tuple:
			self.role = role_tuple
			return True
		return False

	def calc_acc(self):
		self.access = (aDesc.get(self.role[0], 0) + aDesc.get(self.role[1], 0))

class sConf(object):
	def __init__(self, name, disp, code=None, cPref=None, nick=None, added=False):
		self.name = name; self.disp = disp; self.nick = nick or DefNick # Use DefNick if available
		self.code = code; self.more = ""; self.desc = {}; self.IamHere = None
		self.isModer = True; self.sdate = 0; self.alist = {}; self.oCmds = []
		self.cPref = cPref;
		self.status = DefStatus if 'DefStatus' in globals() else "Online" # Use DefStatus if available
		self.state = sList[0]
		if not added: self.save()

	def load_all(self): call_sfunctions("01si", (self.name,))
	def csend(self, stanza): Sender(self.disp, stanza)
	isHere = lambda self, nick: (nick in self.desc)
	isHereTS = lambda self, nick: (self.desc[nick].ishere if self.isHere(nick) else False)
	get_user = lambda self, nick: self.desc.get(nick)
	# isHe lambda was problematic, source on sUser can be str, JID. Better to compare stripped JIDs if possible.
	# For now, keeping original simple comparison logic.
	isHe = lambda self, nick, source_str: (source_str == self.desc[nick].source if self.isHere(nick) and hasattr(self.desc[nick], 'source') else False)

	get_nicks = lambda self: list(self.desc.keys()) # Ensure list in Py3
	get_users = lambda self: list(self.desc.values()) # Ensure list in Py3

	def sorted_users(self):
		for user_nick in sorted(self.get_nicks()): # Renamed user to user_nick
			user_obj = self.get_user(user_nick) # Renamed user to user_obj
			if user_obj: yield user_obj

	def sjoined(self, nick, role, source, stanza):
		access = Galist.get(source)
		if access is None: access = self.alist.get(source)
		self.desc[nick] = sUser(nick, role, source, access)
		call_efunctions("04eh", (self.name, nick, source, role, stanza, self.disp,))

	def aroles_change(self, nick, role, stanza):
		sUser_obj = self.get_user(nick) # Renamed sUser
		if sUser_obj and sUser_obj.aroles(role): # Check sUser_obj exists
			if sUser_obj.source not in Galist and sUser_obj.source not in self.alist:
				sUser_obj.calc_acc()
			call_efunctions("07eh", (self.name, nick, role, self.disp,))
		elif sUser_obj : # if aroles didn't return True (no change) but user exists
			call_efunctions("08eh", (self.name, nick, stanza, self.disp,))

	def set_nick(self, old_nick, nick):
		if old_nick in self.desc: # Ensure old_nick exists
			self.desc[nick] = self.desc.pop(old_nick)
			self.desc[nick].nick = nick
			call_efunctions("06eh", (self.name, old_nick, nick, self.disp,))

	def sleaved(self, nick):
		if nick in self.desc: self.desc[nick].ishere = False

	def composePres(self):
		# Use original xmpp.Presence, setShow, setStatus
		stanza = xmpp.Presence(f"{self.name}/{self.nick}")
		stanza.setShow(self.state)
		stanza.setStatus(self.status)
		return caps_add(stanza)

	def join(self):
		for user_obj in self.get_users(): user_obj.ishere = False
		stanza = self.composePres()
		self.sdate = time.time()
		# Use original xmpp.Node, setNamespace, addChild, setTagData
		node = xmpp.Node("x")
		node.setNamespace(xmpp.NS_MUC)
		node.addChild("history", {"maxchars": "0"})
		if self.code: node.setTagData("password", self.code)
		stanza.addChild(node=node)
		self.csend(stanza)

	def subject(self, body_str):
		Info["omsg"].plus()
		# Use original xmpp.Message
		self.csend(xmpp.Message(self.name, "", sBase[1], body_str))

	def set_status(self, state, status_msg): self.state, self.status = (state, status_msg)

	def change_status(self, state, status_msg):
		self.set_status(state, status_msg)
		self.csend(self.composePres())

	def save_stats(self): call_sfunctions("03si", (self.name,))

	def leave(self, exit_status=None):
		self.IamHere = None; self.isModer = True; self.more = ""
		# Use original xmpp.Presence, setStatus
		stanza = xmpp.Presence(self.name, sBase[4])
		if exit_status: stanza.setStatus(exit_status)
		self.csend(stanza)

	def full_leave(self, status_msg=None):
		self.leave(status_msg)
		if self.name in Chats: del Chats[self.name]
		self.save_stats()
		self.save(False)
		call_sfunctions("04si", (self.name,))
		if self.name in ChatsAttrs: del ChatsAttrs[self.name]

	def save(self, RealSave=True):
		if initialize_file(ChatsFile):
			desc_dict = {}
			try:
				file_content = get_file(ChatsFile)
				if file_content and file_content.strip(): desc_dict = ast.literal_eval(file_content)
			except (SyntaxError, ValueError):
				desc_dict = {}

			if not RealSave:
				if self.name in desc_dict: del desc_dict[self.name]
			else:
				desc_dict[self.name] = {"disp": self.disp, sBase[12]: self.nick, "cPref": self.cPref, "code": self.code}

			desc_str = str(desc_dict)
			cat_file(ChatsFileBackup, desc_str)
			cat_file(ChatsFile, desc_str)
		else:
			delivery(f"Error saving chat data for {self.name}") # Was delivery(self.name)

	def iq_sender(self, attr_key, data_val, aff_role_key, role_val, reason_str="", handler_tuple=()):
		# Use original xmpp.Iq, setID, Node, setNamespace, addChild, setTagData
		stanza = xmpp.Iq(sBase[9], to=self.name)
		stanza.setID(f"Bs-i{Info['outiq'].plus()}")
		query = xmpp.Node(sBase[18])
		query.setNamespace(xmpp.NS_MUC_ADMIN)
		item_node = query.addChild("item", {attr_key: data_val, aff_role_key: role_val})
		if reason_str: item_node.setTagData("reason", reason_str)
		stanza.addChild(node=query)
		if not handler_tuple:
			self.csend(stanza)
		else:
			handler_func, kdesc_dict = handler_tuple
			if not handler_func:
				handler_func = handleResponse
				kdesc_dict = {"source": kdesc_dict}
			CallForResponse(self.disp, stanza, handler_func, kdesc_dict)

	def outcast(self, jid, reason="", handler=()): self.iq_sender(sBase[11], jid, aRoles[0], aRoles[1], reason, handler)
	def none(self, jid, reason="", handler=()): self.iq_sender(sBase[11], jid, aRoles[0], aRoles[2], reason, handler)
	def member(self, jid, reason="", handler=()): self.iq_sender(sBase[11], jid, aRoles[0], aRoles[3], reason, handler)
	def admin(self, jid, reason="", handler=()): self.iq_sender(sBase[11], jid, aRoles[0], aRoles[4], reason, handler)
	def owner(self, jid, reason="", handler=()): self.iq_sender(sBase[11], jid, aRoles[0], aRoles[5], reason, handler)
	def kick(self, nick, reason="", handler=()): self.iq_sender(sBase[12], nick, aRoles[6], aRoles[2], reason, handler)
	def visitor(self, nick, reason="", handler=()): self.iq_sender(sBase[12], nick, aRoles[6], aRoles[7], reason, handler)
	def participant(self, nick, reason="", handler=()): self.iq_sender(sBase[12], nick, aRoles[6], aRoles[8], reason, handler)
	def moder(self, nick, reason="", handler=()): self.iq_sender(sBase[12], nick, aRoles[6], aRoles[9], reason, handler)

def get_source(source_val, nick_val):
	if source_val in Chats:
		user_obj = Chats[source_val].get_user(nick_val)
		return getattr(user_obj, "source", None)
	return source_val

def get_access_level(source_val, nick_val):
	if source_val in Chats:
		user_obj = Chats[source_val].get_user(nick_val)
		return getattr(user_obj, "access", 0)
	# Ensure Galist is defined before use
	return Galist.get(source_val, 2) if 'Galist' in globals() else 2


enough_access = lambda conf, nick, req_access=0: (req_access <= get_access_level(conf, nick))

def robust_decode(obj_to_encode):
    if isinstance(obj_to_encode, str): return obj_to_encode
    if isinstance(obj_to_encode, bytes): return obj_to_encode.decode("utf-8", "replace")
    return str(obj_to_encode)

def delivery(body_str):
	try:
		disp_jid_str, body_str = GenDisp, robust_decode(body_str)
		if not online(disp_jid_str):
			for current_disp_jid in list(Clients.keys()): # Ensure list for Py3
				if GenDisp != current_disp_jid and online(current_disp_jid):
					disp_jid_str = current_disp_jid; break
			if not online(disp_jid_str): raise SelfExc("disconnected!")
		Info["omsg"].plus()
		# Use original xmpp.Message, GodName
		Clients[disp_jid_str].send(xmpp.Message(GodName, body_str, sBase[0]))
	except (IOError, SelfExc) as e:
		Print(f"\n\n{body_str} (Delivery Error: {e})", COLOR_YELLOW)
	except Exception:
		record_exception_traceback()

def Message(target_jid_str, body_str, disp_obj=None):
	body_str = robust_decode(body_str)
	is_chat_target = target_jid_str in Chats

	if is_chat_target:
		stype = sBase[1]
		if not disp_obj: disp_obj = Chats[target_jid_str].disp
		limit = ConfLimit
		if len(body_str) > limit:
			Chats[target_jid_str].more = body_str[limit:].strip()
			body_str = AnsBase[18] % (body_str[:limit].strip(), limit)
	else:
		stype = sBase[0]
		if not disp_obj:
			try: # JID creation can fail
				jid_stripped = xmpp.JID(target_jid_str).getStripped() if isinstance(target_jid_str, (str, bytes)) else str(target_jid_str)
			except:
				jid_stripped = str(target_jid_str)

			if jid_stripped in Chats: disp_obj = Chats[jid_stripped].disp
			else: disp_obj = GenDisp

		limit = PrivLimit
		if len(body_str) > limit:
			num_parts, total_parts = itypes.Number(), str(len(body_str) // limit + 1)
			original_body = body_str
			# body_str = "" # Not needed, we send parts
			while len(original_body) > 0:
				part_to_send = original_body[:limit]
				original_body = original_body[limit:]
				Info["omsg"].plus()
				msg_text = f"[{num_parts.plus()}/{total_parts}] {part_to_send.strip()}"
				if original_body: msg_text += "[...]"
				Sender(disp_obj, xmpp.Message(target_jid_str, msg_text, stype))
				if original_body: time.sleep(2)
			return

	Info["omsg"].plus()
	Sender(disp_obj, xmpp.Message(target_jid_str, body_str.strip(), stype))

def Answer(body_str, stype, source_tuple, disp_obj=None):
	if stype == sBase[0]:
		target_instance = source_tuple[0]
	else:
		body_str = f"{source_tuple[2]}: {robust_decode(body_str)}"
		target_instance = source_tuple[1]
	Message(target_instance, body_str, disp_obj)

def checkFlood(disp_obj):
	disp_jid_str = get_disp_str(disp_obj)
	flood_times = Guard.setdefault(disp_jid_str, [])
	flood_times.append(time.time())
	if len(flood_times) > 3:
		if flood_times[-1] - flood_times[0] < 9:
			Guard[disp_jid_str] = [flood_times.pop()]
			xmpp_raise()
		else:
			flood_times.pop(0)

def IdleClient():
	client_chat_counts = {}
	for disp_jid_str in list(Clients.keys()): # Ensure list for Py3
		if online(disp_jid_str): client_chat_counts[disp_jid_str] = 0

	for conf_obj in list(Chats.values()): # Ensure list for Py3
		disp_jid_str = conf_obj.disp
		if disp_jid_str in client_chat_counts: client_chat_counts[disp_jid_str] += 1

	if client_chat_counts:
		min_chats = min(client_chat_counts.values())
		for disp_jid_str, num_chats in client_chat_counts.items():
			if num_chats == min_chats: return disp_jid_str
	return GenDisp

ejoinTimerName = lambda conf_name: f"{ejoinTimer.__name__}-{robust_decode(conf_name)}"

def get_disp_str(disp_obj_or_jid_str):
	if isinstance(disp_obj_or_jid_str, (xmpp.Client, xmpp.dispatcher.Dispatcher)):
		# Ensure _owner and its attributes exist
		owner = getattr(disp_obj_or_jid_str, '_owner', None)
		if owner and hasattr(owner, 'User') and hasattr(owner, 'Server'):
			return f"{owner.User}@{owner.Server}"
		return "unknown_client_jid" # Fallback if structure is unexpected
	return str(disp_obj_or_jid_str)

def get_nick(chat_name_str):
	return getattr(Chats.get(chat_name_str), sBase[12], DefNick)

def online(disp_obj_or_jid_str):
	disp_jid_str = get_disp_str(disp_obj_or_jid_str)
	if disp_jid_str in Clients:
		return Clients[disp_jid_str].isConnected() # Use original isConnected
	return False

def CallForResponse(disp_obj, stanza, handler_func, kdesc_dict={}):
	if isinstance(stanza, xmpp.Iq):
		disp_jid_str = get_disp_str(disp_obj)
		if disp_jid_str in Clients:
			client_instance = Clients[disp_jid_str]
			stanza_id = stanza.getID() # Use original getID
			if not stanza_id: # xmpppy usually auto-generates if not set by user
				# If it's critical to have one and it might be missing, this is where it would be added.
				# For now, assume xmpp.py or caller handles ID generation for IQs.
				pass
			if stanza_id:
				client_instance.RespExp[stanza_id] = (handler_func, kdesc_dict)
				Sender(disp_jid_str, stanza)

def exec_bsExp(handler_func, disp_obj, iq_stanza, kdesc_dict):
	handler_func(disp_obj, iq_stanza, **kdesc_dict)

def ResponseChecker(disp_obj, iq_stanza):
	# disp_obj is the client instance here
	client_owner = getattr(disp_obj, '_owner', disp_obj) # _owner might not exist on client directly
	stanza_id = iq_stanza.getID()
	if hasattr(client_owner, 'RespExp') and stanza_id in client_owner.RespExp:
		(handler_func, kdesc_dict) = client_owner.RespExp.pop(stanza_id)
		sThread(getattr(handler_func, "__name__", "response_handler"), exec_bsExp,
				(handler_func, disp_obj, iq_stanza, kdesc_dict))
		xmpp_raise()

def handleResponse(disp_obj, stanza_obj, source_tuple):
	stype, target_desc = source_tuple[0], source_tuple[1]
	reply_text = AnsBase[4] if xmpp.isResultNode(stanza_obj) else AnsBase[7]
	# This needs a more robust way to get the original full source for Answer
	# Assuming source_tuple[1] is the chat name for groupchat, or user JID for chat
	if stype == sBase[0]: # Chat
	    # Try to construct a JID object for the first element of source_tuple for Answer
	    # The original source_tuple for Answer was (JID_obj, conf_name_str, nick_str)
	    # Here, source_tuple is (stype, source_obj_or_conf_name)
	    # This reconstruction is a guess.
	    original_sender_jid = target_desc if isinstance(target_desc, xmpp.JID) else xmpp.JID(str(target_desc))
	    Answer(reply_text, stype, (original_sender_jid, str(target_desc), ""), disp_obj)
	else: # Groupchat
	    Answer(reply_text, stype, (None, str(target_desc), "Bot"), disp_obj)


def Sender(disp_obj_or_jid_str, stanza_obj):
	try:
		actual_disp_obj = None
		if not isinstance(disp_obj_or_jid_str, (xmpp.Client, xmpp.dispatcher.Dispatcher)):
			disp_jid_str = get_disp_str(disp_obj_or_jid_str)
			if disp_jid_str not in Clients:
				raise SelfExc(f"client '{disp_jid_str}' not exists")
			actual_disp_obj = Clients[disp_jid_str]
		else:
			actual_disp_obj = disp_obj_or_jid_str

		actual_disp_obj.send(stanza_obj) # Use original send method
	except IOError:
		pass
	except SelfExc as exc:
		Print(format_error_string(exc, "\n\n%s: %s!"), COLOR_RED)
	except Exception:
		collectExc(Sender)

sUnavailable = lambda disp_obj, data_str: Sender(disp_obj, xmpp.Presence(typ=sBase[4], status=data_str))

def caps_add(node_obj):
	# Use original setTag
	node_obj.setTag("c", {"node": Caps, "ver": CapsVer}, xmpp.NS_CAPS)
	return node_obj

Yday = lambda: getattr(time.gmtime(), "tm_yday")

def sAttrs(stanza_obj):
	source_jid = stanza_obj.getFrom()
	stripped_jid_str = source_jid.getStripped() if source_jid else ""
	resource_str = source_jid.getResource() if source_jid else ""
	stanza_type = stanza_obj.getType()
	return (source_jid, stripped_jid_str.lower(), stanza_type, resource_str)

getRole = lambda node_obj: (str(node_obj.getAffiliation()), str(node_obj.getRole())) if hasattr(node_obj, 'getAffiliation') else ('none','none')


def xmpp_raise(): raise xmpp.NodeProcessed("continue")

# Connect with FS
cefile = lambda filename: sanitize_filesystem_path(filename) if 'ASCII_FILESYSTEM' in globals() and ASCII_FILESYSTEM else filename

chat_file = lambda chat_name, file_name: dynamic % (f"{chat_name}/{file_name}")

def initialize_file(filename, default_data="{}"):
	filename_processed = cefile(filename)
	if os.path.isfile(filename_processed): return True
	try:
		folder_path = os.path.dirname(filename_processed)
		if folder_path and not os.path.exists(folder_path):
			os.makedirs(folder_path, 0o755)
		cat_file(filename_processed, default_data)
	except Exception:
		return False
	return True

def del_file(filename):
	try:
		os.remove(cefile(filename))
	except OSError:
		pass

def get_file(filename):
	try:
		with open(cefile(filename), "r", encoding="utf-8") as fp:
			return fp.read()
	except FileNotFoundError:
		return "" # Return empty string if file not found


def cat_file(filename, data_to_write, open_type="w"): # Default to text write
	mode = open_type
	is_binary = "b" in mode

	with Sequence:
		try:
			with open(cefile(filename), mode, encoding=None if is_binary else "utf-8") as fp:
				if not is_binary and isinstance(data_to_write, bytes):
					fp.write(data_to_write.decode("utf-8", "replace"))
				elif is_binary and isinstance(data_to_write, str):
					fp.write(data_to_write.encode("utf-8"))
				else:
					fp.write(data_to_write)
		except Exception:
			# Log error writing file
			record_exception_traceback()


# Crashlogs
def collectDFail():
	with open(GenCrash, "a", encoding="utf-8") as fp:
		record_exception_traceback(fp)

def collectExc(inst, command_name=None):
	error_info = sys.exc_info()
	error_details_str = format_error_string(error_info[1]) if error_info[1] else "Unknown error"
	VarCache["errors"].append(error_details_str)

	instance_name = getattr(inst, "__name__", str(inst))
	num_errors = len(VarCache["errors"])

	# Ensure GetExc and GenDisp are defined
	get_exc_flag = globals().get('GetExc', False)
	gen_disp_val = globals().get('GenDisp')

	if get_exc_flag and gen_disp_val and online(gen_disp_val):
		if command_name:
			exception_msg = AnsBase[13] % (command_name, instance_name)
		else:
			exception_msg = AnsBase[14] % (instance_name)
		delivery(AnsBase[15] % exception_msg)
	else:
		Print(f"\n\nError: can't execute '{instance_name}'!", COLOR_RED)

	filename_crash = f"{FailDir}/error[{Info['cfw']._int() + 1}]{strfTime('[%H.%M.%S][%d.%m.%Y]')}.crash"
	try:
		if not os.path.exists(FailDir): os.mkdir(FailDir, 0o755)
		with open(filename_crash, "w", encoding="utf-8") as fp:
			Info["cfw"].plus()
			record_exception_traceback(fp)
	except Exception:
		record_exception_traceback()
		if get_exc_flag and gen_disp_val and online(gen_disp_val): delivery(error_details_str)
		else: Print(error_details_str, COLOR_RED)
	else:
		if get_exc_flag and gen_disp_val and online(gen_disp_val):
			if OSList[0]: delivery(AnsBase[16] % (num_errors, filename_crash))
			else: delivery(AnsBase[17] % (num_errors, filename_crash))
		else:
			Print(f"\n\nCrash file --> {filename_crash}\nError's number --> {num_errors}", COLOR_RED)

# Other functions
def load_expansions():
	Print("\n\nExpansions loading...\n", COLOR_BLUE)
	for exp_dir_name in sorted(os.listdir(ExpsDir)):
		if exp_dir_name == ".svn" or not os.path.isdir(os.path.join(ExpsDir, exp_dir_name)):
			continue
		exp_obj = expansion(exp_dir_name)
		if exp_obj.isExp:
			loaded_exp, exc_tuple = exp_obj.load()
			if loaded_exp:
				try:
					loaded_exp.initialize_exp()
				except Exception:
					exc_tuple = current_exception_info()
					loaded_exp.dels(True)
					Print(f"Can't init - {exp_dir_name}!%s" % (f"\n\t* {exc_tuple[0]}: {exc_tuple[1]}" if exc_tuple[0] else ""), COLOR_RED)
				else:
					Print(f"{exp_dir_name} - successfully loaded!", COLOR_GREEN)
			else:
				Print(f"Can't load - {exp_dir_name}!%s" % (f"\n\t* {exc_tuple[0]}: {exc_tuple[1]}" if exc_tuple[0] else ""), COLOR_RED)
		else:
			Print(f"{exp_dir_name} - isn't an expansion!", COLOR_RED)

def get_pipe(command_str):
    try:
        output_bytes = subprocess.check_output(command_str, shell=True, stderr=subprocess.STDOUT)
        # Try decoding with preferred encodings, fallback to replace
        encodings_to_try = ["utf-8", "cp866"] if OSList[0] else ["utf-8"]
        data_str = None
        for enc in encodings_to_try:
            try:
                data_str = output_bytes.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        if data_str is None: # If all decodings failed
            data_str = output_bytes.decode("utf-8", "replace")

    except subprocess.CalledProcessError as e:
        try:
            data_str = f"(Error: {e.output.decode('utf-8', 'replace')})"
        except: data_str = "(Error: subprocess error, undecodable output)"
    except Exception:
        data_str = "(...)"
    return data_str


# Web class needs urllib.request and urllib.error for Python 3
import urllib.request
import urllib.error
import urllib.parse

class Web(object):
	Opener = urllib.request.build_opener()

	def __init__(self, link, query_desc=(), data=None, headers={}):
		self.link = link
		if query_desc: self.link += self.encode(query_desc)
		self.data = data
		self.headers = headers

	encode = staticmethod(urllib.parse.urlencode)

	def add_header(self, name, header_val): self.headers[name] = header_val

	def open(self, header_tuple=()):
		data_bytes = None
		if self.data:
			if isinstance(self.data, str): data_bytes = self.data.encode('utf-8')
			elif isinstance(self.data, dict): data_bytes = self.encode(self.data).encode('utf-8') # Encode dict for POST
			else: data_bytes = self.data

		request_obj = urllib.request.Request(self.link, data=data_bytes)
		if header_tuple: self.add_header(*header_tuple)
		if self.headers:
			for header_name, header_val in self.headers.items():
				request_obj.add_header(header_name, header_val)
		return self.Opener.open(request_obj)

	def download(self, filename=None, folder=None, progress_handler=None, fb_args=None, header_tuple=()):
		fp = self.open(header_tuple)
		info_obj = fp.info()
		size_str = info_obj.get("Content-Length", -1)

		if not str(size_str).isdigit(): raise SelfExc("no info about file's size")
		size_int = int(size_str)

		if not filename:
			content_disposition = info_obj.get("Content-Disposition")
			if content_disposition:
				fn_match = regex_compile("filename=[\"']?([^\"']+)[\"']?").search(content_disposition)
				if fn_match: filename = fn_match.group(1)

		if not filename:
			filename = urllib.parse.unquote_plus(fp.url.split("/")[-1].split("?")[0].replace("%25", "%"))
			if not filename: raise SelfExc("can't get filename")

		if isinstance(filename, bytes): filename = filename.decode('utf-8', 'replace')

		if folder: filename = os.path.join(folder, filename)

		filename_fs = cefile(filename)

		block_size = 8192
		block_num = 0
		bytes_read = 0

		with open(filename_fs, "wb") as dfp:
			while VarCache["alive"]:
				if progress_handler:
					execute_handler(progress_handler, (info_obj, block_num, block_size, size_int, fb_args))
				data_chunk = fp.read(block_size)
				if not data_chunk: break
				dfp.write(data_chunk)
				block_num += 1
				bytes_read += len(data_chunk)

		if size_int >= 0 and bytes_read < size_int:
			raise SelfExc(f"file is corrupt, lost {size_int - bytes_read} bytes")

		return (filename, info_obj, size_int)

	def get_page(self, header_tuple=()): # Renamed from original lambda
		response = self.open(header_tuple)
		content_bytes = response.read()
		# Try to determine encoding from headers, default to utf-8
		content_type = response.info().get('Content-Type', '')
		charset_match = regex_compile(r"charset=([\w-]+)").search(content_type)
		encoding = charset_match.group(1) if charset_match else 'utf-8'
		try:
			return content_bytes.decode(encoding)
		except UnicodeDecodeError:
			return content_bytes.decode('utf-8', 'replace') # Fallback


def get_text(body_str, start_str, end_str, content_regex_str = "(?:.|\s)+"):
	flags = re.S | re.I
	compiled_regex = regex_compile(f"{start_str}({content_regex_str}?){end_str}", flags)
	match_obj = compiled_regex.search(body_str)
	return match_obj.group(1).strip() if match_obj else None

def sub_desc(body_str, replacements_list, sub_char=""):
	if isinstance(replacements_list, dict):
		for old, new in replacements_list.items():
			body_str = body_str.replace(old, new)
	else:
		for item in replacements_list:
			if isinstance(item, (list, tuple)):
				if len(item) > 1: body_str = body_str.replace(item[0], item[1])
				else: body_str = body_str.replace(item[0], sub_char)
			else:
				body_str = body_str.replace(item, sub_char)
	return body_str

strfTime = lambda data_format="%d.%m.%Y (%H:%M:%S)", use_local=True: \
	time.strftime(data_format, time.localtime() if use_local else time.gmtime())

def Time2Text(total_seconds):
	ext, time_units = [], [("Year", None), ("Day", 365.25), ("Hour", 24), ("Minute", 60), ("Second", 60)]
	while time_units:
		unit_name, seconds_in_unit = time_units.pop()
		if seconds_in_unit:
			num_units, total_seconds = divmod(total_seconds, seconds_in_unit)
		else:
			num_units = total_seconds
		if num_units >= 1.0:
			ext.insert(0, f"{int(num_units)} {unit_name}{'s' if num_units >= 2 else ''}")
		if not (time_units and total_seconds > 0): break
	return " ".join(ext)

def Size2Text(total_bytes):
	ext, size_units = [], list("YZEPTGMK.")
	while size_units:
		unit_prefix = size_units.pop()
		if size_units:
			num_units, total_bytes = divmod(total_bytes, 1024)
		else:
			num_units = total_bytes
		if num_units >= 1.0:
			ext.insert(0, f"{int(num_units)}{unit_prefix if unit_prefix != '.' else ''}B")
		if not (size_units and total_bytes > 0): break
	return " ".join(ext)

enumerated_list = lambda item_list: "\n".join([f"{numb}) {line}" for numb, line in enumerate(item_list, 1)])

isNumber = lambda obj: isinstance(obj, (int, float)) or (isinstance(obj, str) and obj.isdigit())

isSource = lambda jid_str: isJID.match(jid_str) is not None

def calculate_memory_usage(default_val=0):
	mem_val = default_val
	if OSList[0]: # Windows
		# This logic for Windows TASKLIST is very specific and might need adjustment
		# For now, assuming it works or returns default_val safely
		try:
			lines = get_pipe(f'TASKLIST /FI "PID eq {BsPid}" /NH /FO CSV').splitlines()
			if len(lines) > 0:
				parts = lines[0].split('","')
				if len(parts) > 4: # Memory usage is usually the 5th field (index 4)
					mem_str = parts[4].replace(' K', '').replace(',', '').replace('"', '').strip()
					if mem_str.isdigit(): mem_val = int(mem_str)
		except: pass # Ignore errors, use default
	else: # POSIX
		try:
			lines = get_pipe(f"ps -o rss -p {BsPid}").splitlines()
			if len(lines) >= 2:
				rss_val = lines[1].strip()
				if rss_val.isdigit(): mem_val = int(rss_val)
		except: pass # Ignore errors
	return mem_val if isinstance(mem_val, int) else default_val


def check_copies():
	base_cache = {"PID": BsPid, "up": Info["sess"], "alls": []}
	current_cache = base_cache.copy()
	if os.path.isfile(PidFile):
		try:
			file_content = get_file(PidFile)
			if file_content and file_content.strip(): current_cache = ast.literal_eval(file_content)
		except SyntaxError: del_file(PidFile)
		except Exception: pass
		else:
			try:
				if BsPid == current_cache.get("PID"):
					current_cache.setdefault("alls", []).append(strfTime())
				elif OSList[0]:
					subprocess.call(f'TASKKILL /PID {current_cache["PID"]} /T /f', shell=True)
					raise SelfExc()
				else:
					os.kill(current_cache["PID"], 15)
					time.sleep(2)
					os.kill(current_cache["PID"], 9); raise SelfExc()
			except Exception:
				current_cache = base_cache.copy()

	try:
		cat_file(PidFile, str(current_cache))
	except Exception: pass

	current_cache.pop("PID", None)
	Info.update(current_cache)


def join_chats():
	if initialize_file(ChatsFile):
		conference_dict = {}
		try:
			file_content = get_file(ChatsFile)
			if file_content and file_content.strip(): conference_dict = ast.literal_eval(file_content)
		except SyntaxError:
			try:
				file_content_backup = get_file(ChatsFileBackup)
				if file_content_backup and file_content_backup.strip(): conference_dict = ast.literal_eval(file_content_backup)
			except Exception: conference_dict = {}
		except Exception: conference_dict = {}

		Print(f"\n\nThere are {len(conference_dict)} rooms in the list...", COLOR_BLUE)
		for conf_name, desc_dict in conference_dict.items():
			Chats[conf_name] = chat_obj = sConf(conf_name, added=True, **desc_dict)
			chat_obj.load_all()
			if chat_obj.disp in Clients:
				chat_obj.join()
				Print(f"\n{chat_obj.disp} joined {conf_name};", COLOR_GREEN)
			else:
				Print(f"\nI'll join {conf_name} then {chat_obj.disp} would be connected...", COLOR_YELLOW)
	else:
		Print("\n\nError: unable to create the conferences-list file!", COLOR_RED)

# Presence Handler (xmppPresenceCB -> xmpp_presence_callback)
def xmpp_presence_callback(disp_obj, stanza_obj):
	Info["prs"].plus()
	source_jid, conf_name, stanza_type, nick_str = sAttrs(stanza_obj)

	# In MUC, conf_name is the MUC JID, nick_str is the occupant's nick
	# For direct presence, conf_name is the full JID, nick_str is the resource
	# Adjusting access check logic slightly:
	access_check_entity = conf_name if stanza_type == sBase[1] else source_jid.getStripped() # MUC jid or user bare jid
	access_check_nick = nick_str # For MUC, this is the nick. For direct, it's resource.

	if not enough_access(access_check_entity, access_check_nick): xmpp_raise()

	if stanza_type == sBase[5]: # subscribe
		client_owner = disp_obj._owner
		if hasattr(client_owner, 'Roster') and client_owner.Roster:
			# For subscribe, conf_name is the JID of the subscriber
			subscriber_jid_str = source_jid.getStripped() # Use bare JID for roster operations
			if enough_access(subscriber_jid_str, "", 7): # Check access of the subscriber JID
				client_owner.Roster.Authorize(subscriber_jid_str)
				client_owner.Roster.setItem(subscriber_jid_str, subscriber_jid_str, ["Admins"])
				client_owner.Roster.Subscribe(subscriber_jid_str)
			elif Roster["on"]:
				client_owner.Roster.Authorize(subscriber_jid_str)
				client_owner.Roster.setItem(subscriber_jid_str, subscriber_jid_str, ["Users"])
				client_owner.Roster.Subscribe(subscriber_jid_str)
			else:
				Sender(disp_obj, xmpp.Presence(to=subscriber_jid_str, typ=sBase[7])) # type="error"
		xmpp_raise()
	elif conf_name in Chats: # If it's a MUC presence related to a joined room
		chat_obj = Chats[conf_name]
		if stanza_type == sBase[7]: # error
			error_code = stanza_obj.getErrorCode()
			if error_code:
				if error_code == eCodes[9]:
					chat_obj.nick = f"{nick_str}."
					chat_obj.join()
				elif error_code in (eCodes[5], eCodes[12]):
					chat_obj.IamHere = False
					timer_name = ejoinTimerName(conf_name)
					if timer_name not in ithr.getNames():
						try:
							composeTimer(360, ejoinTimer, timer_name, (conf_name,)).start()
						except ithr.error:
							delivery(AnsBase[20] % (error_code, eCodesDesc.get(error_code, "Unknown Error"), conf_name))
						except Exception:
							collectExc(ithr.KThread.start) # KThread if composeTimer uses it
				elif error_code == eCodes[4]:
					chat_obj.full_leave(eCodesDesc.get(error_code, "Forbidden"))
					delivery(AnsBase[21] % (error_code, eCodesDesc.get(error_code, "Unknown Error"), conf_name))
				elif error_code in (eCodes[2], eCodes[6]):
					chat_obj.leave(eCodesDesc.get(error_code, "Auth/Allowed Error"))
					delivery(AnsBase[22] % (error_code, eCodesDesc.get(error_code, "Unknown Error"), conf_name))
		elif stanza_type in (sBase[3], None): # available or None (initial presence)
			if chat_obj.nick == nick_str: chat_obj.IamHere = True
			role_tuple = getRole(stanza_obj)
			instance_jid_str = stanza_obj.getJid()

			if not instance_jid_str:
				if chat_obj.isModer:
					chat_obj.isModer = False
					if not Mserve:
						chat_obj.change_status(AnsBase[23], sList[2])
						Message(conf_name, AnsBase[24], disp_obj)
						xmpp_raise()
				elif not Mserve: xmpp_raise()
			else:
				try: # JID creation can fail
					instance_jid_str = xmpp.JID(instance_jid_str).getStripped().lower()
				except: # If JID is malformed
					instance_jid_str = str(instance_jid_str).lower()

				if not chat_obj.isModer and chat_obj.nick == nick_str and aDesc.get(role_tuple[0], 0) > 1:
					chat_obj.isModer = True
					chat_obj.leave(AnsBase[25])
					time.sleep(0.4)
					chat_obj.join(); xmpp_raise()

			if chat_obj.isHereTS(nick_str) and chat_obj.isHe(nick_str, instance_jid_str):
				chat_obj.aroles_change(nick_str, role_tuple, stanza_obj)
			else:
				chat_obj.sjoined(nick_str, role_tuple, instance_jid_str, stanza_obj)
		elif stanza_type == sBase[4]: # unavailable
			status_code = stanza_obj.getStatusCode()
			if chat_obj.nick == nick_str and status_code in (sCodes[0], sCodes[2]):
				chat_obj.full_leave(sCodesDesc.get(status_code, "Unknown Status"))
				delivery(AnsBase[26] % (status_code, conf_name, sCodesDesc.get(status_code, "Unknown Status")))
				xmpp_raise()
			elif not Mserve and not stanza_obj.getJid(): xmpp_raise()
			elif status_code == sCodes[1]: # nick-changed (303)
				new_nick = stanza_obj.getNick()
				if chat_obj.isHere(nick_str):
					chat_obj.set_nick(nick_str, new_nick)
				else:
					instance_jid_str = stanza_obj.getJid()
					if instance_jid_str:
						try: instance_jid_str = xmpp.JID(instance_jid_str).getStripped().lower()
						except: instance_jid_str = str(instance_jid_str).lower()
					role_tuple = getRole(stanza_obj)
					if chat_obj.isHereTS(new_nick) and chat_obj.isHe(new_nick, instance_jid_str):
						chat_obj.aroles_change(new_nick, role_tuple, stanza_obj)
					else:
						chat_obj.sjoined(new_nick, role_tuple, instance_jid_str, stanza_obj)
			else:
				status_text = (stanza_obj.getReason() or stanza_obj.getStatus())
				if chat_obj.isHereTS(nick_str): chat_obj.sleaved(nick_str)
				call_efunctions("05eh", (conf_name, nick_str, status_text, status_code, disp_obj,))

		if conf_name in Chats:
			call_efunctions("02eh", (stanza_obj, disp_obj,))


# Iq Handler (xmppIqCB -> xmpp_iq_callback)
def xmpp_iq_callback(disp_obj, stanza_obj):
	Info["iq"].plus()
	ResponseChecker(disp_obj, stanza_obj)
	source_jid, instance_jid_str, stanza_type, nick_str = sAttrs(stanza_obj)

	# Similar access check adjustment as in presence
	access_check_entity_iq = instance_jid_str # For IQ, instance_jid_str is usually the target/source
	access_check_nick_iq = nick_str # Resource or empty for direct IQs
	if not enough_access(access_check_entity_iq, access_check_nick_iq): xmpp_raise()

	if stanza_type == sBase[10]: # get
		query_ns = stanza_obj.getQueryNS()
		if not query_ns:
			child_node = stanza_obj.getTag(sBase[16]) or stanza_obj.getTag(sBase[17])
			if child_node: query_ns = child_node.getNamespace()

		if query_ns in IqXEPs:
			reply_stanza = stanza_obj.buildReply(sBase[8])
			query_node_reply = reply_stanza.getTag(sBase[18])
			if not query_node_reply and query_ns : # If buildReply didn't add query (e.g. for NS_URN_TIME)
			    query_node_reply = reply_stanza.setTag(sBase[18]) # Use setTag to create if not exists
			    query_node_reply.setNamespace(query_ns)


			if query_ns == xmpp.NS_DISCO_INFO:
				query_node_reply.addChild("identity", {"category": "client", "type": "bot", "name": ProdName[:10]})
				for feature_var in XEPs:
					query_node_reply.addChild("feature", {"var": feature_var})
			elif query_ns == xmpp.NS_LAST:
				query_node_reply.setAttr("seconds", str(int(time.time() - VarCache["idle"])))
				query_node_reply.setData(VarCache["action"])
			elif query_ns == xmpp.NS_VERSION:
				query_node_reply.setTagData("name", ProdName)
				query_node_reply.setTagData("version", ProdVer)
				python_ver_str = "{0} [{1}.{2}.{3}]".format(sys.subversion[0] if hasattr(sys, 'subversion') else 'Unknown', *sys.version_info)
				os_str = ""
				if OSList[0]: # Windows
					os_str = get_pipe("Ver").strip() # Simpler command
				elif OSList[1]: # POSIX
					os_str = "{0} {2:.16} [{4}]".format(*os.uname())
				else:
					os_str = BotOS.capitalize()
				query_node_reply.setTagData("os", f"{os_str} / {python_ver_str}")
			elif query_ns == xmpp.NS_URN_TIME:
				# XEP-0202 structure
				# If query_node_reply was auto-added by buildReply, remove it if it's not the right one.
				if query_node_reply and query_node_reply.getNamespace() != xmpp.NS_URN_TIME:
				    reply_stanza.delChild(query_node_reply.getName(), namespace=query_node_reply.getNamespace())
				time_node = reply_stanza.setTag(sBase[17], namespace=xmpp.NS_URN_TIME) # <time xmlns='urn:xmpp:time'/>
				time_node.setTagData("utc", strfTime("%Y-%m-%dT%H:%M:%SZ", False))
				time_zone_offset = (time.altzone if time.daylight and hasattr(time, 'altzone') else time.timezone)
				time_node.setTagData("tzo", f"{'+' if time_zone_offset <= 0 else '-'}{abs(time_zone_offset) // 3600:02d}:{abs(time_zone_offset) // 60 % 60:02d}")
			elif query_ns == xmpp.NS_TIME:
				query_node_reply.setTagData("utc", strfTime("%Y%m%dT%H:%M:%S", False))
				tz_name = strfTime("%Z")
				query_node_reply.setTagData("tz", tz_name)
				query_node_reply.setTagData("display", time.asctime())

			Sender(disp_obj, reply_stanza)
			xmpp_raise()
	call_efunctions("03eh", (stanza_obj, disp_obj,))


# Message Handler (xmppMessageCB -> xmpp_message_callback)
Macro = Macro() # Class defined earlier

def xmpp_message_callback(disp_obj, stanza_obj):
	Info["msg"].plus()
	source_jid, instance_jid_str, stanza_type, nick_str = sAttrs(stanza_obj)

	# Adjusted access check for messages
	access_check_entity_msg = instance_jid_str # MUC jid or user bare jid
	access_check_nick_msg = nick_str # MUC nick or resource part
	if not enough_access(access_check_entity_msg, access_check_nick_msg): xmpp_raise()

	if stanza_obj.getTimestamp(): xmpp_raise()

	is_conference = (instance_jid_str in Chats)
	chat_obj = Chats.get(instance_jid_str) if is_conference else None

	if is_conference and (not Mserve and not chat_obj.isModer): xmpp_raise()
	elif not is_conference and not enough_access(source_jid.getStripped(), "", 7): # Check bare JID access for PM
		if not Roster["on"]: xmpp_raise()
		checkFlood(disp_obj)

	bot_nick_effective = (chat_obj.nick if is_conference and chat_obj else DefNick)
	if nick_str == bot_nick_effective and source_jid.getStripped() == get_disp_str(disp_obj): # Avoid self-replies more carefully
		xmpp_raise()

	body_str = stanza_obj.getBody()
	subject_str = stanza_obj.getSubject() if is_conference else None

	current_content = "" # Renamed body to current_content
	if body_str: current_content = body_str.strip()
	elif subject_str: current_content = subject_str.strip()

	if not current_content: xmpp_raise()

	if len(current_content) > IncLimit:
		current_content = f"{current_content[:IncLimit].strip()}[...] {IncLimit} symbols limit."

	if stanza_type == sBase[7]: # error
		error_code = stanza_obj.getErrorCode()
		if error_code in (eCodes[10], eCodes[7]):
			if error_code == eCodes[7] and not is_conference: xmpp_raise()
			if is_conference and error_code == eCodes[7] and chat_obj: chat_obj.join(); time.sleep(0.6)
			Message(source_jid, current_content, disp_obj) # Send to original sender JID
		xmpp_raise()

	if subject_str and is_conference :
		call_efunctions("09eh", (instance_jid_str, nick_str, subject_str, current_content, disp_obj,))
	else:
		processed_body = current_content # Renamed temp to processed_body
		is_direct_to_bot = (stanza_type == sBase[0])

		if stanza_type != sBase[1]:
			if stanza_obj.getTag(sBase[14]):
				reply_receipt = xmpp.Message(to=source_jid) # Use original to=
				reply_receipt.setTag(sBase[15], namespace=xmpp.NS_RECEIPTS).setAttr("id", stanza_obj.getID())
				reply_receipt.setID(stanza_obj.getID())
				Sender(disp_obj, reply_receipt)
			stanza_type = sBase[0]

		for prefix_char in [f"{bot_nick_effective}{key}" for key in (":", ",", ">")]:
			if processed_body.startswith(prefix_char):
				processed_body = processed_body[len(prefix_char):].lstrip()
				is_direct_to_bot = True; break

		if not processed_body: xmpp_raise()

		parts = processed_body.split(None, 1)
		command_name = parts[0].lower()
		command_args_str = parts[1] if len(parts) > 1 else ""

		if not is_direct_to_bot and is_conference and chat_obj and chat_obj.cPref and command_name not in sCmds:
			if command_name.startswith(chat_obj.cPref):
				command_name = command_name[len(chat_obj.cPref):]
			else: command_name = None
		elif is_direct_to_bot and command_name not in Cmds and (command_name, instance_jid_str) not in Macro:
			for pfx in cPrefs:
				if command_name.startswith(pfx):
					command_name = command_name[len(pfx):]
					break

		if is_conference and chat_obj and command_name in chat_obj.oCmds: xmpp_raise()

		Macro(instance_jid_str, is_conference, command_name, stanza_type, source_jid, nick_str, command_args_str, disp_obj)

		if command_name in Cmds:
			VarCache["action"] = AnsBase[27] % command_name.capitalize()
			VarCache["idle"] = time.time()
			Cmds[command_name].execute(stanza_type, (source_jid, instance_jid_str, nick_str), command_args_str, disp_obj)
		else:
			call_efunctions("01eh", (stanza_obj, is_conference, stanza_type,
									 (source_jid, instance_jid_str, nick_str),
									 current_content, is_direct_to_bot, disp_obj,))

# Connecting & Dispatching (original names kept for now)
def connect_client(inst_jid_str, attrs_tuple):
	server_addr, server_port, client_host, username, passwd = attrs_tuple

	disp_obj = xmpp.Client(client_host, port=server_port, debug=[]) # Use port=
	Print(f"\n\n'{inst_jid_str}' connecting...", COLOR_BLUE)

	connect_params = {'server': (server_addr, server_port)}
	if ConTls: # Assuming ConTls means require STARTTLS or direct TLS
	    connect_params['secure'] = 'tls' # For STARTTLS; use True for old-style SSL on different port

	try:
		if not disp_obj.connect(**connect_params):
			Print(f"\n'{inst_jid_str}' can't connect to '{server_addr.upper()}' (Port: {server_port}).\nI'll retry later...", COLOR_RED)
			return (False, None)
	except Exception as exc:
		Print(f"\n'{inst_jid_str}' can't connect to '{server_addr.upper()}' (Port: {server_port}).\n\t{format_error_string(exc)}\nI'll retry later...", COLOR_RED)
		return (False, None)

	Print(f"\n'{inst_jid_str}' was successfully connected!", COLOR_GREEN)

	Print(f"\n'{inst_jid_str}' authenticating, wait...", COLOR_BLUE)
	try:
		auth_result = disp_obj.auth(username, passwd, resource=GenResource) # resource is a kwarg
	except Exception as exc:
		Print(f"Can't authenticate '{inst_jid_str}'!\n\t{format_error_string(exc)}", COLOR_RED)
		return (False, eCodes[2])

	if auth_result == "sasl":
		Print(f"\n'{inst_jid_str}' was successfully authenticated!", COLOR_GREEN)
	elif auth_result:
		Print(f"\n'{inst_jid_str}' was authenticated, method: {auth_result}...", COLOR_YELLOW)
	else:
		error_msg = getattr(disp_obj, 'lastErr', 'Unknown error')
		error_code_val = getattr(disp_obj, 'lastErrCode', eCodes[2])
		Print(f"Can't authenticate '{inst_jid_str}'! Error: '{error_code_val}' ({error_msg})", COLOR_RED)
		return (False, error_code_val)

	try:
		disp_obj.getRoster()
	except IOError:
		if not disp_obj.isConnected(): return (False, None)
		disp_obj.Roster = None
	except Exception:
		disp_obj.Roster = None

	disp_obj.RespExp = {}
	disp_obj.RegisterHandler(xmpp.NS_PRESENCE, xmpp_presence_callback)
	disp_obj.RegisterHandler(xmpp.NS_IQ, xmpp_iq_callback)
	disp_obj.RegisterHandler(xmpp.NS_MESSAGE, xmpp_message_callback)

	Clients[inst_jid_str] = disp_obj
	Sender(disp_obj, caps_add(xmpp.Presence(show=sList[0], status=DefStatus if 'DefStatus' in globals() else "Online")))
	return (True, inst_jid_str)


def connectAndDispatch(disp_jid_str):
	if reverseDisp(disp_jid_str, False):
		time.sleep(60)
		for conf_obj in list(Chats.values()): # Ensure list for Py3
			if disp_jid_str == conf_obj.disp: conf_obj.join()
		Dispatcher(disp_jid_str)
	else:
		delivery(AnsBase[28] % (disp_jid_str))

def connect_clients():
	for inst_jid_str, attrs_tuple in list(InstancesDesc.items()): # Ensure list for Py3
		is_connected, result_val = connect_client(inst_jid_str, attrs_tuple)
		if not is_connected:
			if result_val and result_val == eCodes[2]:
				continue
			composeTimer(60, connectAndDispatch, f"{sBase[13]}-{inst_jid_str}", (inst_jid_str,)).start()


def reverseDisp(disp_jid_str, rejoin_chats_flag=True):
	iter_counter = itypes.Number()
	while 1440 > iter_counter.plus():
		if connect_client(disp_jid_str, InstancesDesc[disp_jid_str])[0]:
			if rejoin_chats_flag:
				for conf_obj in list(Chats.values()): # Ensure list for Py3
					if disp_jid_str == conf_obj.disp: conf_obj.join()
			return True
		else:
			time.sleep(60)
	return False

def Dispatcher(disp_jid_str):
	client_obj = Clients[disp_jid_str]
	error_streak_counter = itypes.Number()
	while VarCache["alive"]:
		try:
			if not client_obj.Process(1): # Use original Process
				if error_streak_counter.plus() >= 16:
					raise IOError("disconnected (process errors)!")
		except KeyboardInterrupt: break
		except SystemExit: break
		except IOError:
			if not reverseDisp(disp_jid_str):
				delivery(AnsBase[28] % (disp_jid_str))
				break
			client_obj = Clients[disp_jid_str]
			error_streak_counter = itypes.Number()
		except xmpp.Conflict:
			delivery(AnsBase[29] % get_disp_str(client_obj))
			break
		except xmpp.SystemShutdown:
			if not reverseDisp(disp_jid_str):
				delivery(AnsBase[28] % (disp_jid_str))
				break
			client_obj = Clients[disp_jid_str]
			error_streak_counter = itypes.Number()
		except xmpp.StreamError:
			pass
		except Exception:
			collectDFail()
			if Info["errors"].plus() >= len(Clients.keys()) * 8:
				sys_exit("Dispatch Errors!")

# load_mark2 & exit (original names kept)
def load_mark2():
	Print(f"\n\n{FullName}\n\n", COLOR_GREEN)
	check_copies()
	load_expansions()
	call_sfunctions("00si")
	connect_clients()
	while len(Clients.keys()) == 0:
		time.sleep(0.02)
	Print("\n\nYahoo! I am online!", COLOR_GREEN)
	join_chats()
	Print(f"\n\n{ProdName} is ready to serve!\n\n", COLOR_GREEN)
	call_sfunctions("02si")

	for disp_jid_str in list(Clients.keys()): # Ensure list for Py3
		thread_name = f"{sBase[13]}-{disp_jid_str}"
		if thread_name not in ithr.getNames():
			composeThr(Dispatcher, thread_name, (disp_jid_str,)).start()

	while VarCache["alive"]:
		time.sleep(180)
		active_dispatch_threads = 0
		for thread_name_val in ithr.getNames():
			if thread_name_val.startswith(sBase[13]):
				active_dispatch_threads += 1
		if not active_dispatch_threads and Clients:
			sys_exit("All of the clients now fallen!")

		gc.collect()
		if 'MaxMemory' in globals() and MaxMemory and MaxMemory <= calculate_memory_usage():
			sys_exit("Memory leak...")

def sys_exit(exit_desc_str="Suicide!"):
	VarCache["alive"] = False
	Print(f"\n\n{exit_desc_str}", COLOR_RED)
	ithr.killAllThreads()
	for disp_jid_str in list(Clients.keys()): # Ensure list for Py3
		if online(disp_jid_str):
			sUnavailable(disp_jid_str, exit_desc_str)
	call_sfunctions("03si")
	Exit("\n\nReloading...\n\nPress Ctrl+C to exit", 0, 30)

if __name__ == "__main__":
	try:
		load_mark2()
	except KeyboardInterrupt:
		sys_exit("Interrupt (Ctrl+C)")
	except SystemExit:
		sys_exit("Got ~SIGTERM")
	except Exception:
		collectExc(load_mark2)
		sys_exit("Critical Fail!")
