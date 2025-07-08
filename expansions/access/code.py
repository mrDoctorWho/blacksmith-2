# coding: utf-8

#  BlackSmith mark.2
# exp_name = "access" # /code.py v.x3
#  Id: 20~3c
#  Code © (2011) by WitcherGeralt [alkorgun@gmail.com]

import ast

class expansion_temp(expansion):

	def __init__(self, name):
		expansion.__init__(self, name)

	AccessFile = dynamic % ("access.db")
	ChatAccessFile = "access.db"

	accessDesc = (
		"Visitor", # 0
		"Participant", # 1
		"Member", # 2
		"Moder", # 3
		"Member/Moder", # 4
		"Admin", # 5
		"Owner", # 6
		"Chief", # 7
		"God" # 8
	)

	def get_acc(self, access):
		if access > 8:
			access = "%d (Gandalf)" % (access)
		elif access < 0:
			access = "%d (f7u12)" % (access)
		else:
			access = "%d (%s)" % (access, self.accessDesc[access])
		return access

	def command_get_access(self, stype, source, body, disp):
		if not body:
			answer = self.AnsBase[0] % self.get_acc(get_access(source[1], source[2]))
		elif source[1] in Chats:
			if Chats[source[1]].isHere(body):
				answer = self.AnsBase[1] % (body, self.get_acc(get_access(source[1], body)))
			elif body in Galist:
				answer = self.AnsBase[1] % (body, self.get_acc(Galist.get(body, 0)))
			elif body in Chats[source[1]].alist:
				answer = self.AnsBase[1] % (body, str(Chats[source[1]].alist.get(body, 0)))
			else:
				answer = self.AnsBase[2] % (body)
		elif body in Galist:
			answer = self.AnsBase[1] % (body, self.get_acc(Galist.get(body, 0)))
		else:
			answer = self.AnsBase[2] % (body)
		Answer(answer, stype, source, disp)

	def command_get_galist(self, stype, source, body, disp):
		if Galist:
			ls = sorted([(acc, user) for user, acc in Galist.items()], reverse = True)
			if stype == sBase[1]:
				answer = AnsBase[11]
			Message(source[0], self.AnsBase[5] + enumerated_list("%s - %d" % (user, acc) for acc, user in ls), disp)
		else:
			answer = self.AnsBase[3]
		if sBase[6] in locals():
			Answer(answer, stype, source, disp)

	def command_get_lalist(self, stype, source, body, disp):
		if source[1] in Chats:
			if Chats[source[1]].alist:
				ls = sorted([(acc, user) for user, acc in Chats[source[1]].alist.items()], reverse = True)
				if stype == sBase[1]:
					answer = AnsBase[11]
				Message(source[0], self.AnsBase[5] + enumerated_list("%s - %d" % (user, acc) for acc, user in ls), disp)
			else:
				answer = self.AnsBase[4]
		else:
			answer = AnsBase[0]
		if sBase[6] in locals():
			Answer(answer, stype, source, disp)

	def command_set_access(self, stype, source, body, disp):

		def set_access(instance, access = None):
			if access != None:
				Galist[instance] = access
			else:
				del Galist[instance]
			cat_file(self.AccessFile, str(Galist))
			for conf in list(Chats.keys()):
				for sUser in Chats[conf].get_users():
					if sUser.source and sUser.source == instance:
						if access == None:
							access = Chats[conf].alist.get(instance, None)
						if access != None:
							sUser.access = access
						else:
							sUser.calc_acc()

		if body:
			body = body.split(None, 1)
			if len(body) == 2:
				Nick = body.pop(1)
				if source[1] in Chats:
					if Chats[source[1]].isHere(Nick):
						instance = get_source(source[1], Nick)
				if "instance" not in locals():
					instance = (Nick.split())[0].lower()
					if not isSource(instance):
						instance = None
				if instance:
					access = body.pop(0)
					if access == chr(33):
						if instance in Galist:
							set_access(instance)
							answer = AnsBase[4]
						else:
							answer = self.AnsBase[6] % (Nick)
					elif isNumber(access):
						access = int(access)
						if access in range(-1, 9):
							set_access(instance, access)
							answer = AnsBase[4]
						else:
							answer = self.AnsBase[7]
					else:
						answer = AnsBase[30]
				else:
					answer = self.AnsBase[10] % (Nick)
			else:
				answer = AnsBase[2]
		else:
			answer = AnsBase[1]
		Answer(answer, stype, source, disp)

	def command_set_local_access(self, stype, source, body, disp):

		def set_access(conf, instance, access = None):
			if access != None:
				Chats[conf].alist[instance] = access
			else:
				del Chats[conf].alist[instance]
			cat_file(chat_file(conf, self.ChatAccessFile), str(Chats[conf].alist))
			for sUser in Chats[conf].get_users():
				if sUser.source and sUser.source == instance:
					if access == None:
						access = Galist.get(instance, None)
					if access != None:
						sUser.access = access
					else:
						sUser.calc_acc()

		if source[1] in Chats:
			if body:
				body = body.split(None, 1)
				if len(body) == 2:
					Nick = body.pop(1)
					if Chats[source[1]].isHere(Nick):
						instance = get_source(source[1], Nick)
					else:
						instance = (Nick.split())[0].lower()
						if not isSource(instance):
							instance = None
					if instance:
						access = body.pop(0)
						if access == chr(33):
							if instance in Chats[source[1]].alist:
								set_access(source[1], instance)
								answer = AnsBase[4]
							else:
								answer = self.AnsBase[6] % (Nick)
						elif instance not in Galist:
							if isNumber(access):
								access = int(access)
								if access in range(7):
									set_access(source[1], instance, access)
									answer = AnsBase[4]
								else:
									answer = self.AnsBase[8]
							else:
								answer = AnsBase[30]
						else:
							answer = self.AnsBase[9] % (Nick)
					else:
						answer = self.AnsBase[10] % (Nick)
				else:
					answer = AnsBase[2]
			else:
				answer = AnsBase[1]
		else:
			answer = AnsBase[0]
		Answer(answer, stype, source, disp)

	def load_acclist(self):
		if initialize_file(self.AccessFile): # Ensures file exists, possibly creating with default "{}"
			file_content = get_file(self.AccessFile)
			if file_content:
				try:
					evaluated_content = ast.literal_eval(file_content)
					if isinstance(evaluated_content, dict):
						Galist.update(evaluated_content)
					else:
						Print(f"Error: Access file {self.AccessFile} has invalid format. Expected a dict.", COLOR_RED)
				except (ValueError, SyntaxError) as e:
					Print(f"Error loading access file {self.AccessFile}: {e}. Not updating Galist.", COLOR_RED)
			# If file is empty or unparseable, Galist remains as is (presumably empty or from previous state)

	def load_local_acclist(self, conf):
		filename = chat_file(conf, self.ChatAccessFile)
		if initialize_file(filename): # Ensures file exists, possibly creating with default "{}"
			file_content = get_file(filename)
			if file_content:
				try:
					evaluated_content = ast.literal_eval(file_content)
					if isinstance(evaluated_content, dict):
						Chats[conf].alist.update(evaluated_content)
					else:
						Print(f"Error: Local access file {filename} for chat {conf} has invalid format. Expected a dict.", COLOR_RED)
				except (ValueError, SyntaxError) as e:
					Print(f"Error loading local access file {filename} for chat {conf}: {e}. Not updating alist.", COLOR_RED)
			# If file is empty or unparseable, alist remains as is

	commands = (
		(command_get_access, "access", 1,),
		(command_get_galist, "acclist", 7,),
		(command_get_lalist, "acclist2", 4,),
		(command_set_access, "gaccess", 8,),
		(command_set_local_access, "laccess", 6,)
	)

	handlers = (
		(load_acclist, "00si"),
		(load_local_acclist, "01si")
	)
