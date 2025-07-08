# coding: utf-8

#  BlackSmith mark.2
# exp_name = "roster_control" # /code.py v.x4
#  Id: 23~4c
#  Code © (2011-2013) by WitcherGeralt [alkorgun@gmail.com]

import ast

class expansion_temp(expansion):

	def __init__(self, name):
		expansion.__init__(self, name)

	RosterFile = dynamic % ("roster.db")

	def command_roster(self, stype, source, body, disp):
		cls = sorted(Clients.keys())
		if body:
			body = body.split()
			arg0 = (body.pop(0)).lower()
			if arg0 in cls:
				Name = arg0
			elif isNumber(arg0):
				Number = (int(arg0) - 1)
				if -1 < Number < len(cls):
					Name = cls[Number]
				else:
					Name = None
			else:
				Name = None
			if Name:
				if body:
					arg0 = body.pop(0)
					if body:
						arg2 = (body.pop(0)).lower()
						if (chr(46) in arg2):
							Roster = getattr(Clients[Name], "Roster")
							if Roster:
								if arg0 == "+":
									Roster.Authorize(arg2)
									Roster.Subscribe(arg2)
									if body:
										Nick = body.pop(0)
										if body and (body.pop(0)).lower() in ("admin", "админ".decode("utf-8")):
											Roster.setItem(arg2, Nick, ["Admins"])
										else:
											Roster.setItem(arg2, Nick, ["Users"])
									else:
										Roster.setItem(arg2, (arg2.split("@"))[0], ["Users"])
									answer = AnsBase[4]
								elif arg0 == "-":
									if arg2 in list(Clients[Name].Roster.keys()):
										Roster.Unauthorize(arg2)
										Roster.Unsubscribe(arg2)
										Roster.delItem(arg2)
										answer = AnsBase[4]
									else:
										answer = self.AnsBase[0]
								else:
									answer = AnsBase[2]
							else:
								answer = AnsBase[7]
						else:
							answer = AnsBase[2]
					else:
						answer = AnsBase[2]
				else:
					Roster = getattr(Clients[Name], "Roster")
					if Roster:
						jids = list(Roster.keys())
						for jid in jids:
							if ("@conference." in jid):
								jids.remove(jid)
					if Roster and jids:
						Groups = {None: []}
						for jid in jids:
							Name = Roster.getName(jid)
							Grps = Roster.getGroups(jid)
							if Grps:
								Gp = sorted(Grps)[0]
								if Gp not in Groups:
									Groups[Gp] = []
							else:
								Gp = None
							Groups[Gp].append((jid, Name))
						ls = ["[Group] [#] [JID] (Nick)"]
						Gp = Groups.pop(None)
						for Gp, Items in (sorted(Groups.items()) + [("No Group", Gp)]):
							if Items:
								Numb = itypes.Number()
								ls.append(Gp + ":")
								for jid, Name in sorted(Items):
									if jid in (Name, None):
										ls.append("\t%d) %s" % (Numb.plus(), jid))
									else:
										ls.append("\t%d) %s - %s" % (Numb.plus(), jid, Name))
						answer = str.join(chr(10), ls)
					else:
						answer = self.AnsBase[1]
			else:
				answer = self.AnsBase[2]
		else:
			answer = enumerated_list(cls)
		if sBase[6] in locals():
			Answer(answer, stype, source, disp)

	def command_roster_state(self, stype, source, body, disp):
		if body:
			body = (body.split())[0].lower()
			if body in ("on", "1", "вкл".decode("utf-8")):
				if not Roster["on"]:
					Roster["on"] = True
					cat_file(self.RosterFile, str(True))
					answer = AnsBase[4]
				else:
					answer = self.AnsBase[3]
			elif body in ("off", "0", "выкл".decode("utf-8")):
				if Roster["on"]:
					Roster["on"] = False
					cat_file(self.RosterFile, str(False))
					answer = AnsBase[4]
				else:
					answer = self.AnsBase[4]
			else:
				answer = AnsBase[2]
		else:
			answer = (self.AnsBase[3] if Roster["on"] else self.AnsBase[4])
		Answer(answer, stype, source, disp)

	def init_roster_state(self):
		# Default to True, as per original initialize_file(..., str(True))
		roster_on_state = True
		if initialize_file(self.RosterFile, str(roster_on_state)):
			file_content = get_file(self.RosterFile)
			if file_content:
				try:
					evaluated_content = ast.literal_eval(file_content)
					if isinstance(evaluated_content, bool):
						roster_on_state = evaluated_content
					else:
						Print(f"Error: Roster file {self.RosterFile} has invalid format. Expected a boolean. Using default: {roster_on_state}.", COLOR_RED)
				except (ValueError, SyntaxError) as e:
					Print(f"Error loading roster file {self.RosterFile}: {e}. Using default: {roster_on_state}.", COLOR_RED)
			# If file is empty, it will also use the default roster_on_state initialized above.
			Roster["on"] = roster_on_state


	commands = (
		(command_roster, "roster", 7,),
		(command_roster_state, "roster2", 7,)
	)

	handlers = ((init_roster_state, "00si"),)
