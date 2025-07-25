#!/usr/bin/python
# coding: utf-8

# BlackSmith's core mark.2
# BlackSmith.py

# Code © (2010-2013) by WitcherGeralt [alkorgun@gmail.com]

# imports

from types import NoneType, InstanceType, GeneratorType
from traceback import print_exc as exc_info__
from random import shuffle, randrange, choice
from re import compile as compile__

import sys, os, gc, time, shutil, ConfigParser

BsCore = getattr(sys.modules["__main__"], "__file__", None)
if BsCore:
	BsCore = os.path.abspath(BsCore)
	BsRoot = os.path.dirname(BsCore)
	if BsRoot:
		os.chdir(BsRoot)
else:
	BsRoot = os.getcwd()

from enconf import *

import xmpp, ithr, itypes

# Cache & Statistics

eColors = xmpp.debug.colors_enabled # Unix colors

color0 = chr(27) + "[0m" # none
color1 = chr(27) + "[33m" # yellow
color2 = chr(27) + "[31;1m" # red
color3 = chr(27) + "[32m" # green
color4 = chr(27) + "[34;1m" # blue

cmdsDb = [
	"ps -o rss -p %d", # 0
	'TASKLIST /FI "PID eq %d"', # 1
	"COLOR F0", # 2
	"Title", # 3
	"TASKKILL /PID %d /T /f", # 4
	"Ver", # 5
	'sh -c "%s" 2>&1' # 6
]

sBase = (
	"chat", # 0
	"groupchat", # 1
	"normal", # 2
	"available", # 3
	"unavailable", # 4
	"subscribe", # 5
	"answer", # 6
	"error", # 7
	"result", # 8
	"set", # 9
	"get", # 10
	"jid", # 11
	"nick", # 12
	"dispatch", # 13
	"request", # 14
	"received", # 15
	"ping", # 16
	"time", # 17
	"query" # 18
)

aRoles = (
	"affiliation", # 0
	"outcast", # 1
	"none", # 2
	"member", # 3
	"admin", # 4
	"owner", # 5
	"role", # 6
	"visitor", # 7
	"participant", # 8
	"moderator" # 9
)

sList = (
	"chat", # готов поболтать
	"away", # отошел
	"xa", # не беспокоить
	"dnd" # недоступен
)

aDesc = {
	"owner": 3,
	"moderator": 3,
	"admin": 2,
	"participant": 1,
	"member": 1
}

sCodesDesc = {
	"301": "has-been-banned", # 0
	"303": "nick-changed", # 1
	"307": "has-been-kicked", # 2
	"407": "members-only" # 3
}

sCodes = sorted(sCodesDesc.keys())

eCodesDesc = {
	"302": "redirect", # 0
	"400": "unexpected-request", # 1
	"401": "not-authorized", # 2
	"402": "payment-required", # 3
	"403": "forbidden", # 4
	"404": "remote-server-not-found", # 5
	"405": "not-allowed", # 6
	"406": "not-acceptable", # 7
	"407": "subscription-required", # 8
	"409": "conflict", # 9
	"500": "undefined-condition", # 10
	"501": "feature-not-implemented", # 11
	"503": "service-unavailable", # 12
	"504": "remote-server-timeout" # 13
}

eCodes = sorted(eCodesDesc.keys())

IqXEPs = (
	xmpp.NS_VERSION, # 0
	xmpp.NS_PING, # 1
	xmpp.NS_TIME, # 2
	xmpp.NS_URN_TIME, # 3
	xmpp.NS_LAST, # 4
	xmpp.NS_DISCO_INFO # 5
)

XEPs = set(IqXEPs + (
	xmpp.NS_CAPS,
	xmpp.NS_SASL,
	xmpp.NS_TLS,
	xmpp.NS_MUC,
	xmpp.NS_ROSTER,
	xmpp.NS_RECEIPTS
))

isJID = compile__("^.+?@[\w-]+?\.[\.\w-]+?$", 32)

VarCache = {
	"idle": 0.24,
	"alive": True,
	"errors": [],
	"action": "# %s %s &" % (os.path.basename(sys.executable), BsCore)
}

Info = {
	"cmd": itypes.Number(),		"sess": time.time(),
	"msg": itypes.Number(),		"alls": [],
	"cfw": itypes.Number(),		"up": 1.24,
	"prs": itypes.Number(),		"iq": itypes.Number(),
	"errors": itypes.Number(),
	"omsg": itypes.Number(),	"outiq": itypes.Number()
}

# Useful features

class SelfExc(Exception):
	pass

def check_sqlite():
	if not itypes.sqlite3:
		raise SelfExc("py-sqlite3 required")

def exc_info():
	exc, err, tb = sys.exc_info()
	if exc and err:
		exc = exc.__name__
		if err.args:
			err = err[0]
	return (exc, err)

def exc_info_(fp = None):
	try:
		exc_info__(None, fp)
	except Exception:
		pass

sleep, database = time.sleep, itypes.Database

def get_exc():
	try:
		exc = ithr.get_exc()
	except Exception:
		exc = "(...)"
	return exc

exc_str = lambda err, data = "%s - %s": data % (err.__class__.__name__, err[0] if err.args else None)

def apply(instance, args = (), kwargs = {}):
	try:
		data = instance(*args, **kwargs)
	except Exception:
		data = None
	return data

def text_color(text, color):
	if eColors and color:
		text = color + text + color0
	return text

def Print(text, color = None):
	try:
		print text_color(text, color)
	except Exception:
		pass

def try_sleep(slp):
	try:
		sleep(slp)
	except KeyboardInterrupt:
		os._exit(0)
	except:
		pass

def Exit(text, exit, slp):
	Print(text, color2); try_sleep(slp)
	if exit:
		os._exit(0)
	else:
		os.execl(sys.executable, sys.executable, BsCore)

try:
	reload(sys)
	sys.setdefaultencoding("utf-8")
except:
	Print("\n\nError: can't set default encoding!", color2)

stdout = "stdout.tmp"
if not sys.stdin.isatty():
	if os.path.isfile(stdout):
		if os.path.getsize(stdout) >= 131072:
			stdout = open(stdout, "wb", 0)
		else:
			stdout = open(stdout, "ab", 0)
	else:
		stdout = open(stdout, "wb", 0)
	sys.stdout = stdout
	sys.stderr = stdout
	if eColors:
		eColors = not eColors
else:
	stdout = sys.stdout

# Important Variables

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
	Cache = open(SvnCache).readlines()
	if len(Cache) > 3:
		BsRev = Cache[3].strip()
		if BsRev.isdigit():
			BsRev = int(BsRev)
		else:
			BsRev = 0

ProdName = "BlackSmith mark.%d" % (BsMark)
ProdVer = "%d (r.%s)" % (BsVer, BsRev)
Caps = "http://blacksmith-2.googlecode.com/svn/"
CapsVer = "%d.%d" % (BsMark, BsVer)
FullName = "HellDev's %s Ver.%s (%s)" % (ProdName, ProdVer, Caps)

BotOS, BsPid = os.name, os.getpid()

OSList = ((BotOS == "nt"), (BotOS == "posix"))

def client_config(config, section):
	serv = config.get(section, "serv").lower()
	port = config.get(section, "port")
	if not port.isdigit():
		port = 5222
	user = config.get(section, "user").lower()
	host = config.get(section, "host").lower()
	password = config.get(section, "pass")
	jid = "%s@%s" % (user, host)
	return (jid, (serv, port, host, user, password))

try:
	GenCon = ConfigParser.ConfigParser()
	GenCon.read(GenConFile)
	GenDisp, Instance = client_config(GenCon, "CLIENT")
	InstancesDesc = {GenDisp: Instance}
	ConTls = eval(GenCon.get("STATES", "TLS"))
	Mserve = eval(GenCon.get("STATES", "MSERVE"))
	GetExc = eval(GenCon.get("STATES", "GETEXC"))
	DefLANG = GenCon.get("STATES", "LANG").upper()[0:2]
	GodName = GenCon.get("CONFIG", "ADMIN").lower()
	DefNick = GenCon.get("CONFIG", "NICK").split()[0]
	DefStatus = GenCon.get("CONFIG", "STATUS")
	GenResource = GenCon.get("CONFIG", "RESOURCE")
	IncLimit = int(GenCon.get("LIMITS", "INCOMING"))
	PrivLimit = int(GenCon.get("LIMITS", "PRIVATE"))
	ConfLimit = int(GenCon.get("LIMITS", "CHAT"))
	MaxMemory = int(GenCon.get("LIMITS", "MEMORY"))*1024
	ConDisp = ConfigParser.ConfigParser()
	if os.path.isfile(ConDispFile):
		ConDisp.read(ConDispFile)
		for Block in ConDisp.sections():
			Disp, Instance = client_config(ConDisp, Block)
			InstancesDesc[Disp] = Instance
except:
	Exit("\n\nOne of the configuration files is corrupted!", 1, 30)

del Instance

MaxMemory = (32768 if (MaxMemory and MaxMemory <= 32768) else MaxMemory)

try:
	execfile(GenInscFile)
except:
	Exit("\n\nError: general inscript is damaged!", 1, 30)

if OSList[0]:
	os.system(cmdsDb[2])
	os.system("%s %s" % (cmdsDb[3], FullName))

# lists & dicts

expansions = {}
Cmds = {}
cPrefs = ("!", "@", "#", ".", "*")
sCmds = []
Chats = {}
Guard = {}
Galist = {GodName: 8}
Roster = {"on": True}
Clients = {}
ChatsAttrs = {}
Handlers = {
	"01eh": [], "02eh": [],
	"03eh": [], "04eh": [],
	"05eh": [], "06eh": [],
	"07eh": [], "08eh": [],
	"09eh": [], "00si": [],
	"01si": [], "02si": [],
	"03si": [], "04si": []
}

Sequence = ithr.Semaphore()

# call & execute Threads & handlers

def execute_handler(handler_instance, list = (), command = None):
	try:
		handler_instance(*list)
	except SystemExit:
		pass
	except KeyboardInterrupt:
		pass
	except SelfExc:
		pass
	except Exception:
		collectExc(handler_instance, command)

def call_sfunctions(ls, list = ()):
	for inst in Handlers[ls]:
		execute_handler(inst, list)

def composeTimer(sleep, handler, name = None, list = (), command = None):
	if not name:
		name = "iTimer-%s" % (ithr.aCounter._str())
	timer = ithr.Timer(sleep, execute_handler, (handler, list, command,))
	timer.name = name
	return timer

def composeThr(handler, name, list = (), command = None):
	if not name.startswith(sBase[13]):
		name = "%s-%s" % (name, ithr.aCounter._str())
	return ithr.KThread(execute_handler, name, (handler, list, command,))

def startThr(thr, number = 0):
	if number > 2:
		raise RuntimeError("exit")
	try:
		thr.start()
	except ithr.error:
		startThr(thr, (number + 1))
	except Exception:
		collectExc(thr.start)

def sThread_Run(thr, handler, command = None):
	try:
		thr.start()
	except ithr.error:
		try:
			startThr(thr)
		except RuntimeError:
			try:
				thr._run_backup()
			except Exception:
				collectExc(handler, command)
	except Exception:
		collectExc(sThread_Run, command)

def sThread(name, inst, list = (), command = None):
	sThread_Run(composeThr(inst, name, list, command), inst, command)

def call_efunctions(ls, list = ()):
	for inst in Handlers[ls]:
		sThread(ls, inst, list)

# expansions & commands

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
		expansions[self.name] = (self)
		if self.insc:
			try:
				self.AnsBase = AnsBase_temp
			except NameError:
				pass
		for ls in self.commands:
			command_handler(self, *ls)
		for inst, ls in self.handlers:
			self.handler_register(getattr(self, inst.__name__), ls)

	auto_clear = None

	def dels(self, full = False):
		while self.cmds:
			cmd = self.cmds.pop()
			if cmd in Cmds:
				Cmds[cmd].off()
		self.clear_handlers()
		self.commands = ()
		self.handlers = ()
		if self.auto_clear:
			execute_handler(self.auto_clear)
		if full and expansions.has_key(self.name):
			del expansions[self.name]

	def clear_handlers(self, handler = None):

		def Del(inst, ls):
			if ls == "03si":
				execute_handler(inst)
			self.del_handler(ls, inst)
			list = self.desc[ls]
			list.remove(inst)
			if not list:
				del self.desc[ls]

		if handler:
			for ls, list in sorted(self.desc.items()):
				for inst in list:
					if inst == handler:
						handler = Del(inst, ls)
						break
				if not handler:
					break
		else:
			for ls, list in sorted(self.desc.items()):
				for inst in list:
					Del(inst, ls)

	def initialize_all(self):
		for ls, list in sorted(self.desc.items()):
			if not ls.endswith("si"):
				continue
			for inst in list:
				if ls in ("00si", "02si"):
					execute_handler(inst)
				elif ls == "01si":
					for conf in Chats.keys():
						execute_handler(inst, (conf,))

	def load(self):
		if expansions.has_key(self.name):
			expansions[self.name].dels()
		try:
			if self.insc:
				execfile(self.insc, globals())
			execfile(self.file, globals())
			exp_inst = expansion_temp(self.name)
		except Exception:
			exp = (None, exc_info())
		else:
			exp = (exp_inst, ())
		return exp

	def add_handler(self, ls, inst):
		if inst not in Handlers[ls]:
			Handlers[ls].append(inst)

	def del_handler(self, ls, inst):
		if inst in Handlers[ls]:
			Handlers[ls].remove(inst)

	def handler_register(self, inst, ls):
		name = inst.__name__
		for instance in Handlers[ls]:
			if name == instance.__name__:
				self.del_handler(ls, instance)
		self.add_handler(ls, inst)
		self.desc.setdefault(ls, []).append(inst)

class Command(object):

	def __init__(self, inst, default, name, access, help, exp):
		self.exp = exp
		self.default = default
		self.name = name
		self.numb = itypes.Number()
		self.isAvalable = True
		self.help = help
		self.handler = inst
		self.desc = set()
		self.access = access

	def reload(self, inst, access, help, exp):
		self.exp = exp
		self.isAvalable = True
		self.handler = inst
		self.help = help
		self.access = access

	def off(self):
		self.isAvalable = False
		self.handler = None

	def execute(self, stype, source, body, disp):
		if enough_access(source[1], source[2], self.access):
			if self.isAvalable and self.handler:
				Info["cmd"].plus()
				sThread("command", self.handler, (self.exp, stype, source, body, disp), self.name)
				self.numb.plus()
				source = get_source(source[1], source[2])
				if source:
					self.desc.add(source)
			else:
				answer = AnsBase[19] % (self.name)
		else:
			answer = AnsBase[10]
		if locals().has_key(sBase[6]):
			Answer(answer, stype, source, disp)

def command_handler(exp_inst, handler, default, access, prefix = True):
	Path = os.path.join(ExpsDir, exp_inst.name, default)
	try:
		commands = eval(get_file("%s.name" % Path).decode("utf-8"))
	except Exception:
		commands = {}
	if commands.has_key(DefLANG):
		name = commands[DefLANG].decode("utf-8")
		help = "%s.%s" % (Path, DefLANG.lower())
	else:
		name = default
		help = "%s.en" % (Path)
	if name in Cmds:
		Cmds[name].reload(handler, access, help, exp_inst)
	else:
		Cmds[name] = Command(handler, default, name, access, help, exp_inst)
	if not prefix and name not in sCmds:
		sCmds.append(name)
	exp_inst.cmds.append(name)

# Chats, Users & Other

class sUser(object):

	def __init__(self, nick, role, source, access = None):
		self.nick = nick
		self.source = source
		self.role = role
		self.ishere = True
		self.date = (time.time(), Yday(), strfTime(local = False))
		self.access = access
		if not access and access != 0:
			self.calc_acc()

	def aroles(self, role):
		if self.role != role:
			self.role = role
			return True
		return False

	def calc_acc(self):
		self.access = (aDesc.get(self.role[0], 0) + aDesc.get(self.role[1], 0))

class sConf(object):

	def __init__(self, name, disp, code = None, cPref = None, nick = DefNick, added = False):
		self.name = name
		self.disp = disp
		self.nick = nick
		self.code = code
		self.more = ""
		self.desc = {}
		self.IamHere = None
		self.isModer = True
		self.sdate = 0
		self.alist = {}
		self.oCmds = []
		self.cPref = cPref
		self.status = DefStatus
		self.state = sList[0]
		if not added:
			self.save()

	def load_all(self):
		call_sfunctions("01si", (self.name,))

	def csend(self, stanza):
		Sender(self.disp, stanza)

	isHere = lambda self, nick: (nick in self.desc)

	isHereTS = lambda self, nick: (self.desc[nick].ishere if self.isHere(nick) else False)

	get_user = lambda self, nick: self.desc.get(nick)

	isHe = lambda self, nick, source: (source == self.desc[nick].source)

	get_nicks = lambda self: self.desc.keys()

	get_users = lambda self: self.desc.values()

	def sorted_users(self):
		for user in sorted(self.get_nicks()):
			user = self.get_user(user)
			if user:
				yield user

	def sjoined(self, nick, role, source, stanza):
		access = Galist.get(source, None)
		if not access and access != 0:
			access = self.alist.get(source, None)
		self.desc[nick] = sUser(nick, role, source, access)
		call_efunctions("04eh", (self.name, nick, source, role, stanza, self.disp,))

	def aroles_change(self, nick, role, stanza):
		sUser = self.get_user(nick)
		if sUser.aroles(role):
			if not Galist.has_key(sUser.source):
				if not self.alist.has_key(sUser.source):
					sUser.calc_acc()
			call_efunctions("07eh", (self.name, nick, role, self.disp,))
		else:
			call_efunctions("08eh", (self.name, nick, stanza, self.disp,))

	def set_nick(self, old_nick, nick):
		self.desc[nick] = self.desc.pop(old_nick)
		self.desc[nick].nick = nick
		call_efunctions("06eh", (self.name, old_nick, nick, self.disp,))

	def sleaved(self, nick):
		self.desc[nick].ishere = False

	def composePres(self):
		stanza = xmpp.Presence("%s/%s" % (self.name, self.nick))
		stanza.setShow(self.state)
		stanza.setStatus(self.status)
		return caps_add(stanza)

	def join(self):
		for sUser in self.get_users():
			sUser.ishere = False
		stanza = self.composePres()
		self.sdate = time.time()
		node = xmpp.Node("x")
		node.setNamespace(xmpp.NS_MUC)
		node.addChild("history", {"maxchars": "0"})
		if self.code:
			node.setTagData("password", self.code)
		stanza.addChild(node = node)
		self.csend(stanza)

	def subject(self, body):
		Info["omsg"].plus()
		self.csend(xmpp.Message(self.name, "", sBase[1], body))

	def set_status(self, state, status):
		self.state, self.status = (state, status)

	def change_status(self, state, status):
		self.set_status(state, status)
		self.csend(self.composePres())

	def save_stats(self):
		call_sfunctions("03si", (self.name,))

	def leave(self, exit_status = None):
		self.IamHere = None
		self.isModer = True
		self.more = ""
		stanza = xmpp.Presence(self.name, sBase[4])
		if exit_status:
			stanza.setStatus(exit_status)
		self.csend(stanza)

	def full_leave(self, status = None):
		self.leave(status)
		del Chats[self.name]
		self.save_stats()
		self.save(False)
		call_sfunctions("04si", (self.name,))
		if ChatsAttrs.has_key(self.name):
			del ChatsAttrs[self.name]

	def save(self, RealSave = True):
		if initialize_file(ChatsFile):
			desc = eval(get_file(ChatsFile))
			if not RealSave:
				if self.name in desc:
					del desc[self.name]
			else:
				desc[self.name] = {"disp": self.disp, sBase[12]: self.nick, "cPref": self.cPref, "code": self.code}
			desc = str(desc)
			cat_file(ChatsFileBackup, desc)
			cat_file(ChatsFile, desc)
		else:
			delivery(self.name)

	def iq_sender(self, attr, data, afrls, role, reason = str(), handler = None):
		stanza = xmpp.Iq(sBase[9], to = self.name)
		stanza.setID("Bs-i%d" % Info["outiq"].plus())
		query = xmpp.Node(sBase[18])
		query.setNamespace(xmpp.NS_MUC_ADMIN)
		arole = query.addChild("item", {attr: data, afrls: role})
		if reason:
			arole.setTagData("reason", reason)
		stanza.addChild(node = query)
		if not handler:
			self.csend(stanza)
		else:
			handler, kdesc = handler
			if not handler:
				handler = handleResponse
				kdesc = {"source": kdesc}
			CallForResponse(self.disp, stanza, handler, kdesc)

	def outcast(self, jid, reason = str(), handler = ()):
		self.iq_sender(sBase[11], jid, aRoles[0], aRoles[1], reason, handler)

	def none(self, jid, reason = str(), handler = ()):
		self.iq_sender(sBase[11], jid, aRoles[0], aRoles[2], reason, handler)

	def member(self, jid, reason = str(), handler = ()):
		self.iq_sender(sBase[11], jid, aRoles[0], aRoles[3], reason, handler)

	def admin(self, jid, reason = str(), handler = ()):
		self.iq_sender(sBase[11], jid, aRoles[0], aRoles[4], reason, handler)

	def owner(self, jid, reason = str(), handler = ()):
		self.iq_sender(sBase[11], jid, aRoles[0], aRoles[5], reason, handler)

	def kick(self, nick, reason = str(), handler = ()):
		self.iq_sender(sBase[12], nick, aRoles[6], aRoles[2], reason, handler)

	def visitor(self, nick, reason = str(), handler = ()):
		self.iq_sender(sBase[12], nick, aRoles[6], aRoles[7], reason, handler)

	def participant(self, nick, reason = str(), handler = ()):
		self.iq_sender(sBase[12], nick, aRoles[6], aRoles[8], reason, handler)

	def moder(self, nick, reason = str(), handler = ()):
		self.iq_sender(sBase[12], nick, aRoles[6], aRoles[9], reason, handler)

def get_source(source, nick):
	if source in Chats:
		source = getattr(Chats[source].get_user(nick), "source", None)
	return source

def get_access(source, nick):
	if source in Chats:
		access = getattr(Chats[source].get_user(nick), "access", 0)
	else:
		access = Galist.get(source, 2)
	return access

enough_access = lambda conf, nick, access = 0: (access <= get_access(conf, nick))

object_encode = lambda obj: (obj if isinstance(obj, unicode) else str(obj).decode("utf-8", "replace"))

def delivery(body):
	try:
		Disp, body = GenDisp, object_encode(body)
		if not online(Disp):
			for disp in Clients.keys():
				if GenDisp != disp and online(disp):
					Disp = disp
					break
			if not online(Disp):
				raise SelfExc("disconnected!")
		Info["omsg"].plus()
		Clients[Disp].send(xmpp.Message(GodName, body, sBase[0]))
	except IOError:
		Print("\n\n%s" % (body), color1)
	except SelfExc:
		Print("\n\n%s" % (body), color1)
	except Exception:
		exc_info_()

def Message(inst, body, disp = None):
	body = object_encode(body)
	if inst in Chats:
		stype = sBase[1]
		if not disp:
			disp = Chats[inst].disp
		if len(body) > ConfLimit:
			Chats[inst].more = body[ConfLimit:].strip()
			body = AnsBase[18] % (body[:ConfLimit].strip(), ConfLimit)
	else:
		stype = sBase[0]
		if not disp:
			if isinstance(inst, xmpp.JID):
				chat = inst.getStripped()
			else:
				chat = (inst.split(chr(47)))[0].lower()
			if chat in Chats:
				disp = Chats[chat].disp
			else:
				disp = GenDisp
		if len(body) > PrivLimit:
			Number, all = itypes.Number(), str(len(body) / PrivLimit + 1)
			while len(body) > PrivLimit:
				Info["omsg"].plus()
				Sender(disp, xmpp.Message(inst, "[%d/%s] %s[...]" % (Number.plus(), all, body[:PrivLimit].strip()), stype))
				body = body[PrivLimit:].strip()
				sleep(2)
			body = "[%d/%s] %s" % (Number.plus(), all, body)
	Info["omsg"].plus()
	Sender(disp, xmpp.Message(inst, body.strip(), stype))

def Answer(body, stype, source, disp = None):
	if stype == sBase[0]:
		instance = source[0]
	else:
		body = "%s: %s" % (source[2], object_encode(body))
		instance = source[1]
	Message(instance, body, disp)

def checkFlood(disp):
	disp = get_disp(disp)
	if disp in Guard:
		desc = Guard[disp]
	else:
		desc = Guard[disp] = []
	desc.append(time.time())
	if len(desc) > 3:
		if desc[-1] - desc[0] < 9:
			Guard[disp] = [desc.pop()]
			xmpp_raise()
		else:
			desc.pop(0)

def IdleClient():
	cls = dict()
	for disp in Clients.keys():
		if online(disp):
			cls[disp] = 0
	for conf in Chats.itervalues():
		disp = conf.disp
		if disp in cls:
			cls[disp] += 1
	if cls:
		idle = min(cls.values())
		for disp, chats in cls.items():
			if chats == idle:
				return disp
	return GenDisp

def ejoinTimer(conf):
	if conf in Chats:
		Chats[conf].join()

ejoinTimerName = lambda conf: "%s-%s" % (ejoinTimer.__name__, conf.decode("utf-8"))

get_disp = lambda disp: "%s@%s" % (disp._owner.User, disp._owner.Server) if isinstance(disp, (xmpp.Client, xmpp.dispatcher.Dispatcher)) else disp

get_nick = lambda chat: getattr(Chats.get(chat), sBase[12], DefNick)

def online(disp):
	disp = get_disp(disp)
	if disp in Clients:
		return Clients[disp].isConnected()
	return False

def CallForResponse(disp, stanza, handler, kdesc = {}):
	if isinstance(stanza, xmpp.Iq):
		disp = get_disp(disp)
		if disp in Clients:
			ID = stanza.getID()
			if not ID:
				xmpp.dispatcher.ID += 1
				ID = str(xmpp.dispatcher.ID)
				stanza.setID(ID)
			Clients[disp].RespExp[ID] = (handler, kdesc)
			Sender(disp, stanza)

def exec_bsExp(instance, disp, iq, kdesc):
	instance(disp, iq, **kdesc)

def ResponseChecker(disp, iq):
	Disp, ID = disp._owner, iq.getID()
	if ID in Disp.RespExp:
		(handler, kdesc) = Disp.RespExp.pop(ID)
		sThread(getattr(handler, "__name__"), exec_bsExp, (handler, disp, iq, kdesc))
		xmpp_raise()

def handleResponse(disp, stanza, source):
	stype, source = source[:2]
	Answer(AnsBase[4 if xmpp.isResultNode(stanza) else 7], stype, source, disp)

def Sender(disp, stanza):
	try:
		if not isinstance(disp, InstanceType):
			if disp not in Clients:
				raise SelfExc("client '%s' not exists" % (disp))
			disp = Clients[disp]
		disp.send(stanza)
	except IOError:
		pass
	except SelfExc as exc:
		Print(exc_str(exc, "\n\n%s: %s!"), color2)
	except Exeption:
		collectExc(Sender)

sUnavailable = lambda disp, data: Sender(disp, xmpp.Presence(typ = sBase[4], status = data))

def caps_add(node):
	node.setTag("c", {"node": Caps, "ver": CapsVer}, xmpp.NS_CAPS)
	return node

Yday = lambda: getattr(time.gmtime(), "tm_yday")

def sAttrs(stanza):
	source = stanza.getFrom()
	instance = source.getStripped()
	resource = source.getResource()
	stype = stanza.getType()
	return (source, instance.lower(),
					stype, resource)

getRole = lambda node: (str(node.getAffiliation()), str(node.getRole()))

def xmpp_raise():
	raise xmpp.NodeProcessed("continue")

# Connect with FS

chat_file = lambda chat, name: dynamic % ("%s/%s") % (chat, name)

def initialize_file(filename, data = "{}"):
	filename = cefile(filename)
	if os.path.isfile(filename):
		return True
	try:
		folder = os.path.dirname(filename)
		if folder and not os.path.exists(folder):
			os.makedirs(folder, 0755)
		cat_file(filename, data)
	except Exception:
		return False
	return True

def del_file(filename):
	apply(os.remove, (cefile(filename),))

def get_file(filename):
	with open(cefile(filename), "r") as fp:
		return fp.read()

def cat_file(filename, data, otype = "wb"):
	with Sequence:
		with open(cefile(filename), otype) as fp:
			fp.write(data)

# Crashlogs

def collectDFail():
	with open(GenCrash, "ab") as fp:
		exc_info_(fp)

def collectExc(inst, command = None):
	error = get_exc()
	VarCache["errors"].append(error)
	inst, number = getattr(inst, "__name__") or str(inst), len(VarCache["errors"])
	if GetExc and online(GenDisp):
		if command:
			exception = AnsBase[13] % (command, inst)
		else:
			exception = AnsBase[14] % (inst)
		delivery(AnsBase[15] % exception)
	else:
		Print("\n\nError: can't execute '%s'!" % (inst), color2)
	filename = "%s/error[%d]%s.crash" % (FailDir, int(Info["cfw"]) + 1, strfTime("[%H.%M.%S][%d.%m.%Y]"))
	try:
		if not os.path.exists(FailDir):
			os.mkdir(FailDir, 0755)
		with open(filename, "wb") as fp:
			Info["cfw"].plus()
			exc_info_(fp)
	except Exception:
		exc_info_()
		if GetExc and online(GenDisp):
			delivery(error)
		else:
			Print(error, color2)
	else:
		if GetExc and online(GenDisp):
			if OSList[0]:
				delivery(AnsBase[16] % (number, filename))
			else:
				delivery(AnsBase[17] % (number, filename))
		else:
			Print("\n\nCrash file --> %s\nError's number --> %d" % (filename, number), color2)

# Other functions

def load_expansions():
	Print("\n\nExpansions loading...\n", color4)
	for expDir in sorted(os.listdir(ExpsDir)):
		if (".svn" == expDir) or not os.path.isdir(os.path.join(ExpsDir, expDir)):
			continue
		exp = expansion(expDir)
		if exp.isExp:
			exp, exc = exp.load()
			if exp:
				try:
					exp.initialize_exp()
				except Exception:
					exc = exc_info()
					exp.dels(True)
					Print("Can't init - %s!%s" % (expDir, "\n\t* %s: %s" % exc), color2)
				else:
					Print("%s - successfully loaded!" % (expDir), color3)
			else:
				Print("Can't load - %s!%s" % (expDir, "\n\t* %s: %s" % exc), color2)
		else:
			Print("%s - isn't an expansion!" % (expDir), color2)

def get_pipe(command):
	try:
		with os.popen(command) as pipe:
			data = pipe.read()
		if OSList[0]:
			data = data.decode("cp866")
	except Exception:
		data = "(...)"
	return data

class Web(object):

	import urllib as One, urllib2 as Two

	Opener = Two.build_opener()

	def __init__(self, link, qudesc = (), data = None, headers = {}):
		self.link = link
		if qudesc:
			self.link += self.encode(qudesc)
		self.data = data
		self.headers = headers

	encode = staticmethod(One.urlencode)

	def add_header(self, name, header):
		self.headers[name] = header

	def open(self, header = ()):
		dest = self.Two.Request(self.link, self.data)
		if header:
			self.add_header(*header)
		if self.headers:
			for header, desc in self.headers.iteritems():
				dest.add_header(header, desc)
		return self.Opener.open(dest)

	def download(self, filename = None, folder = None, handler = None, fb = None, header = ()):
		fp = self.open(header)
		info = fp.info()
		size = info.get("Content-Length", -1)
		if not isNumber(size):
			raise SelfExc("no info about file's size")
		size = int(size)
		if not filename:
			disp = info.get("Content-Disposition")
			if disp:
				comp = compile__("filename=[\"']+?(.+?)[\"']+?")
				disp = comp.search(disp)
				if disp:
					filename = (disp.group(1)).decode("utf-8")
		if not filename:
			filename = self.One.unquote_plus(fp.url.split("/")[-1].split("?")[0].replace("%25", "%"))
			if not filename:
				raise SelfExc("can't get filename")
		if folder:
			filename = os.path.join(folder, filename)
		if AsciiSys:
			filename = filename.encode("utf-8")
		blockSize = 8192
		blockNumb = 0
		read = 0
		with open(filename, "wb") as dfp:
			while VarCache["alive"]:
				if handler:
					execute_handler(handler, (info, blockNumb, blockSize, size, fb))
				data = fp.read(blockSize)
				if not data:
					break
				dfp.write(data)
				blockNumb += 1
				read += len(data)
		if size >= 0 and read < size:
			raise SelfExc("file is corrupt, lost %d bytes" % (size - read))
		if AsciiSys:
			filename = filename.decode("utf-8")
		return (filename, info, size)

	get_page = lambda self, header = (): self.open(header).read()

def get_text(body, s0, s2, s1 = "(?:.|\s)+"):
	comp = compile__("%s(%s?)%s" % (s0, s1, s2), 16)
	body = comp.search(body)
	if body:
		body = (body.group(1)).strip()
	return body

def sub_desc(body, ls, sub = str()):
	if isinstance(ls, dict):
		for x, z in ls.items():
			body = body.replace(x, z)
	else:
		for x in ls:
			if isinstance(x, (list, tuple)):
				if len(x) > 1:
					body = body.replace(*x[:2])
				else:
					body = body.replace(x[0], sub)
			else:
				body = body.replace(x, sub)
	return body

strfTime = lambda data = "%d.%m.%Y (%H:%M:%S)", local = True: time.strftime(data, time.localtime() if local else time.gmtime())

def Time2Text(Time):
	ext, ls = [], [("Year", None), ("Day", 365.25), ("Hour", 24), ("Minute", 60), ("Second", 60)]
	while ls:
		lr = ls.pop()
		if lr[1]:
			(Time, Rest) = divmod(Time, lr[1])
		else:
			Rest = Time
		if Rest >= 1.0:
			ext.insert(0, "%d %s%s" % (Rest, lr[0], ("s" if Rest >= 2 else "")))
		if not (ls and Time):
			return str.join(chr(32), ext)

def Size2Text(Size):
	ext, ls = [], list("YZEPTGMK.")
	while ls:
		lr = ls.pop()
		if ls:
			(Size, Rest) = divmod(Size, 1024)
		else:
			Rest = Size
		if Rest >= 1.0:
			ext.insert(0, "%d%sB" % (Rest, (lr if lr != "." else "")))
		if not (ls and Size):
			return str.join(chr(32), ext)

enumerated_list = lambda ls: str.join(chr(10), ["%d) %s" % (numb, line) for numb, line in enumerate(ls, 1)])

isNumber = lambda obj: (not apply(int, (obj,)) is None)

isSource = lambda jid: isJID.match(jid)

def calculate(numb = int()):
	if OSList[0]:
		lines = get_pipe(cmdsDb[1] % (BsPid)).splitlines()
		if len(lines) >= 3:
			list = lines[3].split()
			if len(list) > 5:
				numb = (list[4] + list[5])
	else:
		lines = get_pipe(cmdsDb[0] % (BsPid)).splitlines()
		if len(lines) >= 2:
			numb = lines[1].strip()
	return (0 if not isNumber(numb) else int(numb))

def check_copies():
	cache = base = {"PID": BsPid, "up": Info["sess"], "alls": []}
	if os.path.isfile(PidFile):
		try:
			cache = eval(get_file(PidFile))
		except SyntaxError:
			del_file(PidFile)
		except Exception:
			pass
		else:
			try:
				if BsPid == cache["PID"]:
					cache["alls"].append(strfTime())
				elif OSList[0]:
					get_pipe(cmdsDb[4] % (cache["PID"])); raise SelfExc()
				else:
					os.kill(cache["PID"], 15)
					sleep(2)
					os.kill(cache["PID"], 9); raise SelfExc()
			except Exception:
				cache = base
	apply(cat_file, (PidFile, str(cache)))
	del cache["PID"]; Info.update(cache)

def join_chats():
	if initialize_file(ChatsFile):
		try:
			try:
				confs = eval(get_file(ChatsFile))
			except SyntaxError:
				confs = eval(get_file(ChatsFileBackup))
		except Exception:
			confs = {}
		Print("\n\nThere are %d rooms in the list..." % len(confs.keys()), color4)
		for conf, desc in confs.iteritems():
			Chats[conf] = Chat = sConf(conf, added = True, **desc)
			Chat.load_all()
			if Chat.disp in Clients:
				Chat.join()
				Print("\n%s joined %s;" % (Chat.disp, conf), color3)
			else:
				Print("\nI'll join %s then %s would be connected..." % (conf, Chat.disp), color1)
	else:
		Print("\n\nError: unable to create the conferences-list file!", color2)

# Presence Handler

def xmppPresenceCB(disp, stanza):
	Info["prs"].plus()
	(source, conf, stype, nick) = sAttrs(stanza)
	if not enough_access(conf, nick):
		xmpp_raise()
	if stype == sBase[5]:
		disp = disp._owner
		if disp.Roster:
			if enough_access(conf, nick, 7):
				disp.Roster.Authorize(conf)
				disp.Roster.setItem(conf, conf, ["Admins"])
				disp.Roster.Subscribe(conf)
			elif Roster["on"]:
				disp.Roster.Authorize(conf)
				disp.Roster.setItem(conf, conf, ["Users"])
				disp.Roster.Subscribe(conf)
			else:
				Sender(disp, xmpp.Presence(conf, sBase[7]))
		xmpp_raise()
	elif conf in Chats:
		Chat = Chats[conf]
		if stype == sBase[7]:
			ecode = stanza.getErrorCode()
			if ecode:
				if ecode == eCodes[9]:
					Chat.nick = "%s." % (nick)
					Chat.join()
				elif ecode in (eCodes[5], eCodes[12]):
					Chat.IamHere = False
					TimerName = ejoinTimerName(conf)
					if TimerName not in ithr.getNames():
						try:
							composeTimer(360, ejoinTimer, TimerName, (conf,)).start()
						except ithr.error:
							delivery(AnsBase[20] % (ecode, eCodesDesc[ecode], conf))
						except Exception:
							collectExc(ithr.Thread.start)
				elif ecode == eCodes[4]:
					Chat.full_leave(eCodesDesc[ecode])
					delivery(AnsBase[21] % (ecode, eCodesDesc[ecode], conf))
				elif ecode in (eCodes[2], eCodes[6]):
					Chat.leave(eCodesDesc[ecode])
					delivery(AnsBase[22] % (ecode, eCodesDesc[ecode], conf))
		elif stype in (sBase[3], None):
			if Chat.nick == nick:
				Chat.IamHere = True
			role = getRole(stanza)
			inst = stanza.getJid()
			if not inst:
				if Chat.isModer:
					Chat.isModer = False
					if not Mserve:
						Chat.change_status(AnsBase[23], sList[2])
						Message(conf, AnsBase[24], disp)
						xmpp_raise()
				elif not Mserve:
					xmpp_raise()
			else:
				inst = (inst.split(chr(47)))[0].lower()
				if not Chat.isModer and Chat.nick == nick and aDesc.get(role[0], 0) > 1:
					Chat.isModer = True
					Chat.leave(AnsBase[25])
					sleep(0.4)
					Chat.join(); xmpp_raise()
			if Chat.isHereTS(nick) and Chat.isHe(nick, inst):
				Chat.aroles_change(nick, role, stanza)
			else:
				Chat.sjoined(nick, role, inst, stanza)
		elif stype == sBase[4]:
			scode = stanza.getStatusCode()
			if Chat.nick == nick and scode in (sCodes[0], sCodes[2]):
				Chat.full_leave(sCodesDesc[scode])
				delivery(AnsBase[26] % (scode, conf, sCodesDesc[scode]))
				xmpp_raise()
			elif not Mserve and not stanza.getJid():
				xmpp_raise()
			elif scode == sCodes[1]:
				Nick = stanza.getNick()
				if Chat.isHere(nick):
					Chat.set_nick(nick, Nick)
				else:
					inst = stanza.getJid()
					if inst:
						inst = (inst.split(chr(47)))[0].lower()
					role = getRole(stanza)
					if Chat.isHereTS(Nick) and Chat.isHe(Nick, inst):
						Chat.aroles_change(Nick, role, stanza)
					else:
						Chat.sjoined(Nick, role, inst, stanza)
			else:
				Status = (stanza.getReason() or stanza.getStatus())
				if Chat.isHereTS(nick):
					Chat.sleaved(nick)
				call_efunctions("05eh", (conf, nick, Status, scode, disp,))
		if conf in Chats:
			call_efunctions("02eh", (stanza, disp,))

# Iq Handler

def xmppIqCB(disp, stanza):
	Info["iq"].plus()
	ResponseChecker(disp, stanza)
	(source, inst, stype, nick) = sAttrs(stanza)
	if not enough_access(inst, nick):
		xmpp_raise()
	if stype == sBase[10]:
		ns = stanza.getQueryNS()
		if not ns:
			ns = stanza.getTag(sBase[16]) or stanza.getTag(sBase[17])
			ns = ns and ns.getNamespace()
		if ns in IqXEPs:
			answer = stanza.buildReply(sBase[8])
			if ns == xmpp.NS_DISCO_INFO:
				anode = answer.getTag(sBase[18])
				anode.addChild("identity", {"category": "client",
											"type": "bot",
											"name": ProdName[:10]})
				for feature in XEPs:
					anode.addChild("feature", {"var": feature})
			elif ns == xmpp.NS_LAST:
				anode = answer.getTag(sBase[18])
				anode.setAttr("seconds", int(time.time() - VarCache["idle"]))
				anode.setData(VarCache["action"])
			elif ns == xmpp.NS_VERSION:
				anode = answer.getTag(sBase[18])
				anode.setTagData("name", ProdName)
				anode.setTagData("version", ProdVer)
				Python = "{0} [{1}.{2}.{3}]".format(sys.subversion[0], *sys.version_info)
				if OSList[0]:
					Os = get_pipe(cmdsDb[5]).strip()
				elif OSList[1]:
					Os = "{0} {2:.16} [{4}]".format(*os.uname())
				else:
					Os = BotOS.capitalize()
				anode.setTagData("os", "%s / %s" % (Os, Python))
			elif ns == xmpp.NS_URN_TIME:
				anode = answer.addChild(sBase[17], namespace = xmpp.NS_URN_TIME)
				anode.setTagData("utc", strfTime("%Y-%m-%dT%H:%M:%SZ", False))
				TimeZone = (time.altzone if time.daylight else time.timezone)
				anode.setTagData("tzo", "%s%02d:%02d" % (((TimeZone < 0) and "+" or "-"),
											abs(TimeZone) / 3600,
											abs(TimeZone) / 60 % 60))
			elif ns == xmpp.NS_TIME:
				anode = answer.getTag(sBase[18])
				anode.setTagData("utc", strfTime("%Y%m%dT%H:%M:%S", False))
				tz = strfTime("%Z")
				if OSList[0]:
					tz = tz.decode("cp1251")
				anode.setTagData("tz", tz)
				anode.setTagData("display", time.asctime())
			Sender(disp, answer)
			xmpp_raise()
	call_efunctions("03eh", (stanza, disp,))

# Message Handler

class Macro:

	__call__, __contains__ = lambda self, *args: None, lambda self, args: False

Macro = Macro()

def xmppMessageCB(disp, stanza):
	Info["msg"].plus()
	(source, inst, stype, nick) = sAttrs(stanza)
	if not enough_access(inst, nick):
		xmpp_raise()
	if stanza.getTimestamp():
		xmpp_raise()
	isConf = (inst in Chats)
	if isConf:
		Chat = Chats[inst]
		if (not Mserve and not Chat.isModer):
			xmpp_raise()
	elif not enough_access(inst, nick, 7):
		if not Roster["on"]:
			xmpp_raise()
		checkFlood(disp)
	botNick = (Chat.nick if isConf else DefNick)
	if nick == botNick:
		xmpp_raise()
	subject = isConf and stanza.getSubject()
	body = stanza.getBody()
	if body:
		body = body.strip()
	elif subject:
		body = subject.strip()
	if not body:
		xmpp_raise()
	if len(body) > IncLimit:
		body = "%s[...] %d symbols limit." % (body[:IncLimit].strip(), IncLimit)
	if stype == sBase[7]:
		code = stanza.getErrorCode()
		if code in (eCodes[10], eCodes[7]):
			if code == eCodes[7]:
				if not isConf:
					xmpp_raise()
				Chat.join()
				sleep(0.6)
			Message(source, body)
		xmpp_raise()
	if subject:
		call_efunctions("09eh", (inst, nick, subject, body, disp,))
	else:
		temp, isToBs = body, (stype == sBase[0])
		if stype != sBase[1]:
			if (stanza.getTag(sBase[14])):
				answer = xmpp.Message(source)
				answer.setTag(sBase[15], namespace = xmpp.NS_RECEIPTS).setAttr("id", stanza.getID())
				answer.setID(stanza.getID())
				Sender(disp, answer)
			stype = sBase[0]
		for app in [(botNick + key) for key in (":", ",", ">")]:
			if temp.startswith(app):
				temp, isToBs = temp[len(app):].lstrip(), True
				break
		if not temp:
			xmpp_raise()
		temp = temp.split(None, 1)
		command = (temp.pop(0)).lower()
		temp = temp[0] if temp else ""
		if not isToBs and isConf and Chat.cPref and command not in sCmds:
			if command.startswith(Chat.cPref):
				command = command[1:]
			else:
				command = None
		elif isToBs and command not in Cmds and (command, inst) not in Macro and command.startswith(cPrefs):
			command = command[1:]
		if isConf and command in Chat.oCmds:
			xmpp_raise()
		Macro(inst, isConf, command, stype, source, nick, temp, disp)
		if command in Cmds:
			VarCache["action"] = AnsBase[27] % command.capitalize()
			VarCache["idle"] = time.time()
			Cmds[command].execute(stype, (source, inst, nick), temp, disp)
		else:
			call_efunctions("01eh", (stanza, isConf, stype, (source, inst, nick), body, isToBs, disp,))

# Connecting & Dispatching

def connect_client(inst, attrs):
	(server, cport, host, user, password) = attrs
	disp = xmpp.Client(host, cport, None)
	Print("\n\n'%s' connecting..." % inst, color4)
	if ConTls:
		conType = (None, False)
	else:
		conType = (False, True)
	try:
		conType = disp.connect((server, cport), None, *conType)
	except Exception as exc:
		Print("\n'%s' can't connect to '%s' (Port: %s).\n\t%s\nI'll retry later..." % (inst, server.upper(), cport, exc_str(exc)), color2)
		return (False, None)
	if conType:
		conType = conType.upper()
		if ConTls and conType != "TLS":
			Print("\n'%s' was connected, but a connection isn't secure." % inst, color1)
		else:
			Print("\n'%s' was successfully connected!" % inst, color3)
		Print("\n'%s' using - '%s'" % (inst, conType), color4)
	else:
		Print("\n'%s' can't connect to '%s' (Port: %s). I'll retry later..." % (inst, server.upper(), cport), color2)
		return (False, None)
	Print("\n'%s' authenticating, wait..." % inst, color4)
	try:
		auth = disp.auth(user, password, GenResource)
	except Exception as exc:
		Print("Can't authenticate '%s'!\n\t%s" % (inst, exc_str(exc)), color2)
		return (False, eCodes[2])
	if auth == "sasl":
		Print("\n'%s' was successfully authenticated!" % inst, color3)
	elif auth:
		Print("\n'%s' was authenticated, but old authentication method used..." % inst, color1)
	else:
		error, code = disp.lastErr, disp.lastErrCode
		Print("Can't authenticate '%s'! Error: '%s' (%s)" % (inst, code, error), color2)
		return (False, code)
	try:
		disp.getRoster()
	except IOError:
		if not disp.isConnected():
			return (False, None)
		disp.Roster = None
	except Exception:
		disp.Roster = None
	disp.RespExp = {}
	disp.RegisterHandler(xmpp.NS_PRESENCE, xmppPresenceCB)
	disp.RegisterHandler(xmpp.NS_IQ, xmppIqCB)
	disp.RegisterHandler(xmpp.NS_MESSAGE, xmppMessageCB)
	Clients[inst] = disp
	Sender(disp, caps_add(xmpp.Presence(show = sList[0], status = DefStatus)))
	return (True, inst)

def connectAndDispatch(disp):
	if reverseDisp(disp, False):
		sleep(60)
		for conf in Chats.itervalues():
			if disp == conf.disp:
				conf.join()
		Dispatcher(disp)
	else:
		delivery(AnsBase[28] % (disp))

def connect_clients():
	for inst, attrs in InstancesDesc.items():
		conn = connect_client(inst, attrs)
		if not conn[0]:
			if conn[1] and conn[1] == eCodes[2]:
				continue
			composeTimer(60, connectAndDispatch, "%s-%s" % (sBase[13], inst), (inst,)).start()

def reverseDisp(disp, rejoin = True):
	iters = itypes.Number()
	while 1440 > iters.plus():
		if connect_client(disp, InstancesDesc[disp])[0]:
			if rejoin:
				for conf in Chats.itervalues():
					if disp == conf.disp:
						conf.join()
			return True
		else:
			sleep(60)

def Dispatcher(disp):
	disp = Clients[disp]
	zero = itypes.Number()
	while VarCache["alive"]:
		try:
			if not disp.iter():
				if zero.plus() >= 16:
					raise IOError("disconnected!")
		except KeyboardInterrupt:
			break
		except SystemExit:
			break
		except IOError:
			disp = get_disp(disp)
			if not reverseDisp(disp):
				delivery(AnsBase[28] % (disp))
				break
			disp = Clients[disp]
			zero = itypes.Number()
		except xmpp.Conflict:
			delivery(AnsBase[29] % get_disp(disp))
			break
		except xmpp.SystemShutdown:
			disp = get_disp(disp)
			if not reverseDisp(disp):
				delivery(AnsBase[28] % (disp))
				break
			disp = Clients[disp]
			zero = itypes.Number()
		except xmpp.StreamError:
			pass
		except Exception:
			collectDFail()
			if Info["errors"].plus() >= len(Clients.keys())*8:
				sys_exit("Dispatch Errors!")

# load_mark2 & exit

def load_mark2():
	Print("\n\n%s\n\n" % (FullName), color3)
	check_copies()
	load_expansions()
	call_sfunctions("00si")
	connect_clients()
	while len(Clients.keys()) == 0:
		sleep(0.02)
	Print("\n\nYahoo! I am online!", color3)
	join_chats()
	Print("\n\n%s is ready to serve!\n\n" % (ProdName), color3)
	call_sfunctions("02si")
	for disp in Clients.keys():
		thrName = "%s-%s" % (sBase[13], disp)
		if thrName not in ithr.getNames():
			composeThr(Dispatcher, thrName, (disp,)).start()
	while VarCache["alive"]:
		sleep(180)
		threads = 0
		for name in ithr.getNames():
			if name.startswith(sBase[13]):
				threads += 1
		if not threads:
			sys_exit("All of the clients now fallen!")
		sys.exc_clear()
		gc.collect()
		if MaxMemory and MaxMemory <= calculate():
			sys_exit("Memory leak...")

def sys_exit(exit_desclr = "Suicide!"):
	VarCache["alive"] = False
	Print("\n\n%s" % (exit_desclr), color2)
	ithr.killAllThreads()
	for disp in Clients.keys():
		if online(disp):
			sUnavailable(disp, exit_desclr)
	call_sfunctions("03si")
	Exit("\n\nReloading...\n\nPress Ctrl+C to exit", 0, 30)

if __name__ == "__main__":
	try:
		load_mark2()
	except KeyboardInterrupt:
		sys_exit("Interrupt (Ctrl+C)")
	except SystemExit:
		sys_exit("Got ~SIGTERM")
	except:
		collectExc(load_mark2)
		sys_exit("Critical Fail!")
