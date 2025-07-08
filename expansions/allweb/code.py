# coding: utf-8

#  BlackSmith mark.2
# exp_name = "allweb" # /code.py v.x28
#  Id: 26~27c
#  Code © (2011-2013) by WitcherGeralt [alkorgun@gmail.com]

from bs4 import BeautifulSoup

class expansion_temp(expansion):

	def __init__(self, name):
		expansion.__init__(self, name)

	UserAgents = UserAgents

	import html.entities
	import json # Keep json import separate

	UserAgent = ("User-Agent", "%s/%s" % (ProdName[:10], CapsVer))

	UserAgent_Moz = (UserAgent[0], "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.101 Safari/537.36".format(UserAgents.get(DefLANG, "en-US")))

	Web.Opener.addheaders = [UserAgent_Moz]

	# The following code related to manual HTML entity decoding and tag stripping
	# has been made redundant by the use of BeautifulSoup in the decodeHTML method.

	# Old edefs dictionary and setup:
	# edefs = dict()
	# for Name, Numb in html.entities.name2codepoint.items():
	# 	edefs[Name] = chr(Numb)
	# edefs["&apos;"] = chr(39)

	# Old TagsDesc for <br> replacement (now handled in decodeHTML):
	# TagsDesc = {
	# 	"<br>": "\n",
	# 	"<br />": "\n"
	# }

	# Old compiled regexes for stripping tags and entities:
	# compile_st = compile__("<[^<>]+?>")
	# compile_ehtmls = compile__("&(#?[xX]?(?:[0-9a-fA-F]+|\w{1,8}));")

	# Old sub_ehtmls method:
	# def sub_ehtmls(self, data):
	# 	# ... (implementation was here) ...
	# 	return data

	def decodeHTML(self, data):
		# Replace <br> and <br /> tags with newlines before parsing
		data = data.replace("<br>", "\n").replace("<br />", "\n")
		# Use BeautifulSoup to parse HTML and extract text content
		# html.parser is a good default, lxml could be used if installed and preferred.
		soup = BeautifulSoup(data, "html.parser")
		# soup.get_text() extracts all text, strips tags, and decodes HTML entities
		text_content = soup.get_text()
		return text_content.strip()

	def command_jc(self, stype, source, body, disp):
		if source[1] in Chats:
			if body:
				cName = body.lower()
				if "@conf" in cName: # Use in operator
					cName = (cName.split("@conf"))[0]
			else:
				cName = (source[1].split("@conf"))[0]
			# Web.get_page now returns decoded string, data.decode not needed
			# Web class in BlackSmith.py handles urllib2 -> urllib.request
			Opener = Web("http://jc.jabber.ru/search.html?", [("search", cName.encode("utf-8"))]) # cName is already string
			try:
				data = Opener.get_page(self.UserAgent)
			except urllib.error.HTTPError as exc: # Specific exception
				answer = str(exc)
			except urllib.error.URLError as exc: # Broader network errors
				answer = str(exc)
			except Exception: # Catch any other unexpected error
				answer = self.AnsBase[0]
				# Consider logging the error here: logging.exception("Unexpected error in command_jc")
			else:
				# data = data.decode("utf-8") # Should be already decoded by get_page
				comp = compile__("<li>((?:.|\s)+?)</li>", 16)
				found_list = comp.findall(data) # Renamed list to found_list
				if found_list:
					ls = []
					for numb, line in enumerate(found_list, 1):
						line = line.strip()
						ls.append("%d) %s" % (numb, line))
					answer = "\n" + self.decodeHTML("\n\n".join(ls)) # Use \n and join
				else:
					answer = self.AnsBase[5]
		else:
			answer = AnsBase[0]
		Answer(answer, stype, source, disp)

	gCache = []

	sMark = 1
	tMark = 2

	def command_google(self, stype, source, body, disp):
		if body:
			if (chr(42) != body):
				Opener = Web("http://ajax.googleapis.com/ajax/services/search/web?", [("v", "1.0"), ("q", body.encode("utf-8"))])
				try:
					data = Opener.get_page(self.UserAgent)
				except urllib.error.HTTPError as exc: # Specific exception
					answer = str(exc)
				except urllib.error.URLError as exc: # Broader network errors
					answer = str(exc)
				except Exception: # Catch any other unexpected error
					answer = self.AnsBase[0]
					# Consider logging
				else:
					try:
						data = self.json.loads(data) # data is already string
					except json.JSONDecodeError: # Specific error for JSON parsing
						answer = self.AnsBase[1]
					except Exception: # Catch any other unexpected error during parsing
						answer = self.AnsBase[1] # Or a more generic error message
						# Consider logging
					else:
						try:
							results_list = data["responseData"]["results"] # Renamed list
							desc = results_list.pop(0)
						except (TypeError, LookupError):
							answer = self.AnsBase[5]
						else:
							ls = []
							ls.append(desc.get("title", ""))
							ls.append(desc.get("content", ""))
							ls.append(desc.get("unescapedUrl", ""))
							answer = self.decodeHTML("\n".join(ls)) # Use \n and join
							if results_list:
								source_ = get_source(source[1], source[2])
								if source_:
									for cache_item in self.gCache: # Renamed ls to cache_item
										if cache_item[:2] == (source_, self.sMark):
											self.gCache.pop(self.gCache.index(cache_item))
											break
									Numb = (len(list(Clients.keys()))*8) # Ensure Clients.keys() is a list for len
									while len(self.gCache) >= Numb:
										self.gCache.pop(0)
									self.gCache.append((source_, self.sMark, results_list))
									answer += self.AnsBase[4] % len(results_list)
			else:
				source_ = get_source(source[1], source[2])
				if source_:
					results_list = [] # Renamed list
					for cache_item in self.gCache: # Renamed ls to cache_item
						if cache_item[:2] == (source_, self.sMark):
							results_list = self.gCache.pop(self.gCache.index(cache_item))[2]
							break
					if results_list:
						desc = results_list.pop(0)
						ls = []
						ls.append(desc.get("title", ""))
						ls.append(desc.get("content", ""))
						ls.append(desc.get("unescapedUrl", ""))
						answer = self.decodeHTML("\n".join(ls)) # Use \n and join
						if results_list:
							self.gCache.append((source_, self.sMark, results_list))
							answer += self.AnsBase[4] % len(results_list)
					else:
						answer = self.AnsBase[2]
				else:
					answer = self.AnsBase[3]
		else:
			answer = AnsBase[1]
		Answer(answer, stype, source, disp)

	LangMap = LangMap

	def command_google_translate(self, stype, source, body, disp):
		if body:
			if (chr(42) != body):
				body = body.split(None, 2)
				if len(body) == 3:
					lang0, langX, body = body
					if langX in self.LangMap and (lang0 in self.LangMap or lang0 == "auto"):
						desc = (("client", "bs-2"),
								("sl", lang0),
								("tl", langX),
								("text", body.encode("utf-8")))
						Opener = Web("http://translate.google.com/translate_a/t?", desc, headers = {"Accept-Charset": "utf-8"})
						try:
							data = Opener.get_page(self.UserAgent_Moz)
						except urllib.error.HTTPError as exc: # Specific exception
							answer = str(exc)
						except urllib.error.URLError as exc: # Broader network errors
							answer = str(exc)
						except Exception: # Catch any other unexpected error
							answer = self.AnsBase[0]
							# Consider logging
						else:
							try:
								data = self.json.loads(data) # data is already string
							except json.JSONDecodeError: # Specific error for JSON parsing
								answer = self.AnsBase[1]
							except Exception: # Catch any other unexpected error during parsing
								answer = self.AnsBase[1] # Or a more generic error message
								# Consider logging
							else:
								try:
									body_translated = data["sentences"][0]["trans"] # Renamed body
								except (TypeError, LookupError):
									answer = self.AnsBase[1]
								else:
									if lang0 == "auto":
										try:
											lang0 = data["src"]
										except KeyError:
											pass
									answer = "%s -> %s:\n%s" % (lang0, langX, body_translated)
									try:
										terms_list = data["dict"][0]["terms"] # Renamed list
									except LookupError:
										pass
									else:
										source_ = get_source(source[1], source[2])
										if source_:
											if body_translated in terms_list:
												terms_list.pop(terms_list.index(body_translated))
											if terms_list:
												for cache_item in self.gCache: # Renamed ls
													if cache_item[:2] == (source_, self.tMark):
														self.gCache.pop(self.gCache.index(cache_item))
														break
												Numb = (len(list(Clients.keys()))*8) # Ensure list for len
												while len(self.gCache) >= Numb:
													self.gCache.pop(0)
												self.gCache.append((source_, self.tMark, terms_list))
												answer += self.AnsBase[7] % len(terms_list)
					else:
						answer = self.AnsBase[6]
				else:
					answer = AnsBase[2]
			else:
				source_ = get_source(source[1], source[2])
				if source_:
					terms_list = [] # Renamed list
					for cache_item in self.gCache: # Renamed ls
						if cache_item[:2] == (source_, self.tMark):
							terms_list = self.gCache.pop(self.gCache.index(cache_item))[2]
							break
					if terms_list:
						answer = self.decodeHTML(terms_list.pop(0))
						if terms_list:
							self.gCache.append((source_, self.tMark, terms_list))
							answer += self.AnsBase[7] % len(terms_list)
					else:
						answer = self.AnsBase[2]
				else:
					answer = self.AnsBase[3]
		else:
			answer = self.AnsBase[8] + "\n".join(["%s - %s" % (k, l) for k, l in sorted(self.LangMap.items())]) # Use \n and join
			if stype == sBase[1]:
				Message(source[0], answer, disp)
				answer = AnsBase[11]
		Answer(answer, stype, source, disp)

	kinoHeaders = {
		"Host": "m.kinopoisk.ru",
		"Accept": "text/html",
		"Accept-Charset": "cp1251",
		"Accept-Language": "ru"
	}

	C3oP = "СЗоР"

	def command_kino(self, stype, source, body, disp):
		if body:
			ls = body.split()
			c1st = (ls.pop(0)).lower()
			if c1st in ("top250", "топ250"): # Removed decode for Python 3
				if ls:
					limit_str = ls.pop(0)
					if isNumber(limit_str): # Use isNumber from BlackSmith.py
						limit = int(limit_str)
						if limit <= 5:
							limit = 5
					else:
						limit = 5 # Default or error
				else:
					limit = None
				kinoHeaders = self.kinoHeaders.copy()
				kinoHeaders["Host"] = "www.kinopoisk.ru"
				Opener = Web("http://www.kinopoisk.ru/level/20/", headers = kinoHeaders)
				try:
					data = Opener.get_page(self.UserAgent_Moz) # Should return decoded string (cp1251 if Web.get_page handles it)
				except urllib.error.HTTPError as exc: # Specific exception
					answer = str(exc)
				except urllib.error.URLError as exc: # Broader network errors
					answer = str(exc)
				except Exception: # Catch any other unexpected error
					answer = self.AnsBase[0]
					# Consider logging
				else:
					# data = data.decode("cp1251") # Assuming get_page decodes
					text_list = get_text(data, "<tr height=25>", "</table>") # Renamed list
					if text_list:
						comp = compile__('<a href="/film/\d+?/" class="all">(.+?)</a>(?:.|\s)+' \
										'?<a href="/film/\d+?/votes/" class="continue">(.+?)</a> <span.*?>(.+?)</span>', 16)
						found_films = comp.findall(text_list) # Renamed list
					if found_films:
						ls = ["\n[#] [Name, Year] [Rating] (Votes)"]
						for Number, (Name, Numb, Count) in enumerate(found_films, 1):
							ls.append("%d) %s - %s %s" % (Number, self.sub_ehtmls(Name), Numb, sub_desc(Count, ["&nbsp;"])))
							if limit and limit <= Number:
								break
						if not limit or limit > 25:
							if stype == sBase[1]:
								Answer(AnsBase[11], stype, source, disp)
							Top250 = "\n".join(ls) # Use \n and join
							Message(source[0], Top250, disp)
						else:
							answer = "\n".join(ls) # Use \n and join
					elif self.C3oP in data: # Use in operator
						answer = self.AnsBase[-1]
					else:
						answer = self.AnsBase[1]
			elif isNumber(body): # body is already string
				Opener = Web("http://m.kinopoisk.ru/movie/%d" % int(body), headers = self.kinoHeaders.copy())
				try:
					data = Opener.get_page(self.UserAgent_Moz) # Should return decoded string
				except urllib.error.HTTPError as exc: # Specific exception
					answer = str(exc)
				except urllib.error.URLError as exc: # Broader network errors
					answer = str(exc)
				except Exception: # Catch any other unexpected error
					answer = self.AnsBase[0]
					# Consider logging
				else:
					# data = data.decode("cp1251") # Assuming get_page decodes
					rslt = get_text(data, "<p class=\"title\">", "</div>")
					if rslt:
						rslt = self.decodeHTML(rslt)
						ls = ["\->"]
						for line in rslt.splitlines():
							line = line.strip()
							if line:
								if line[0].islower():
									line = "{1}{0}".format(line[1:], line[0].upper())
								ls.append(line)
						answer = "\n".join(ls) # Use \n and join
					elif self.C3oP in data: # Use in operator
						answer = self.AnsBase[-1]
					else:
						answer = self.AnsBase[5]
			else:
				body_search = (body if "*" != c1st else body[2:].strip()) # Simplified chr(42)
				if body_search:
					body_encoded = body_search.encode("cp1251") # body_search is string
					Opener = Web("http://m.kinopoisk.ru/search/%s" % urllib.parse.quote_plus(body_encoded), headers = self.kinoHeaders.copy())
					try:
						data = Opener.get_page(self.UserAgent_Moz) # Should return decoded string
					except urllib.error.HTTPError as exc: # Specific exception
						answer = str(exc)
					except urllib.error.URLError as exc: # Broader network errors
						answer = str(exc)
					except Exception: # Catch any other unexpected error
						answer = self.AnsBase[0]
						# Consider logging
					else:
						# data = data.decode("cp1251") # Assuming get_page decodes
						comp = compile__("<a href=\"http://m.kinopoisk.ru/movie/(\d+?)/\">(.+?)</a>")
						found_films = comp.findall(data) # Renamed list
						if found_films:
							ls = ["\n[#] [Name, Year] (#id)"]
							for Number, (Numb, Name) in enumerate(found_films, 1):
								ls.append("%d) %s (#%s)" % (Number, self.sub_ehtmls(Name), Numb))
							answer = "\n".join(ls) # Use \n and join
						elif self.C3oP in data: # Use in operator
							answer = self.AnsBase[-1]
						else:
							answer = self.AnsBase[5]
				else:
					answer = AnsBase[2]
		else:
			answer = AnsBase[1]
		if sBase[6] in locals(): # Check if answer was defined
			Answer(answer, stype, source, disp)

	IMDbHeaders = {"Accept-Language": "%s,en" % UserAgents.get(DefLANG, "en-US")}

	IMDbRequest = { # imdbapi.org
		"type": "json",
#		"id": "tt", # get info by ID
#		"q": "any title", # for the search
#		"limit": str(choice(range(1, 11))), # for the search
		"plot": "none", # or "simple" or "full"
		"episode": "0", # or "1"
		"lang": UserAgents.get(DefLANG, "en-US"),
		"aka": "simple", # or "full"
		"release": "simple", # or "full"
	}

	def command_imdb(self, stype, source, body, disp):
		if body:
			ls = body.split()
			c1st = (ls.pop(0)).lower()
			if c1st in ("top250", "топ250"): # Removed decode for Python 3
				if ls:
					limit_str = ls.pop(0)
					if isNumber(limit_str): # Use isNumber from BlackSmith.py
						limit = int(limit_str)
						if limit <= 5:
							limit = 5
					else:
						limit = 5 # Default or error
				else:
					limit = None
				Opener = Web("http://m.imdb.com/chart/top_json", headers = self.IMDbHeaders)
				try:
					data = Opener.get_page(self.UserAgent_Moz) # Returns decoded string
				except urllib.error.HTTPError as exc: # Specific exception
					answer = str(exc)
				except urllib.error.URLError as exc: # Broader network errors
					answer = str(exc)
				except Exception: # Catch any other unexpected error
					answer = self.AnsBase[0]
					# Consider logging
				else:
					try:
						data_json = self.json.loads(data) # data is already string
					except json.JSONDecodeError: # Specific error for JSON parsing
						answer = self.AnsBase[1]
					except Exception: # Catch any other unexpected error during parsing
						answer = self.AnsBase[1] # Or a more generic error message
						# Consider logging
					else:
						try:
							imdb_list = data_json["list"] # Renamed data to imdb_list
						except (TypeError, LookupError):
							answer = self.AnsBase[1]
						else:
							ls = ["\n[#] [Name, Year] [Rating] (Votes)"]
							comp = compile__("([\d\.,]+).*\s([\d\.,]+)")
							try:
								assert isinstance(imdb_list, list)
								for Number, desc in enumerate(imdb_list, 1):
									Name = desc["title"]
									Year = desc["extra"]
									Numb, Count = comp.search(desc["detail"]).groups()
									ls.append("%s) %s %s - %s (%s)" % (Number, Name, Year, Numb, Count))
									if limit and limit <= Number:
										break
							except (AssertionError, TypeError, LookupError):
								answer = self.AnsBase[5]
							else:
								if not limit or limit > 25:
									if stype == sBase[1]:
										Answer(AnsBase[11], stype, source, disp)
									Top250 = "\n".join(ls) # Use \n and join
									Message(source[0], Top250, disp)
								else:
									answer = "\n".join(ls) # Use \n and join
			elif isNumber(body): # body is already str
				IMDbRequest = self.IMDbRequest.copy()
				IMDbRequest["id"] = ("tt" + body)
				IMDbRequest["plot"] = "full"
				Opener = Web("http://imdbapi.org/?", list(IMDbRequest.items()))
				try:
					data = Opener.get_page(self.UserAgent_Moz) # Returns decoded string
				except urllib.error.HTTPError as exc: # Specific exception
					answer = str(exc)
				except urllib.error.URLError as exc: # Broader network errors
					answer = str(exc)
				except Exception: # Catch any other unexpected error
					answer = self.AnsBase[0]
					# Consider logging
				else:
					try:
						data_json = self.json.loads(data) # data is already string
					except json.JSONDecodeError: # Specific error for JSON parsing
						answer = self.AnsBase[1]
					except Exception: # Catch any other unexpected error during parsing
						answer = self.AnsBase[1] # Or a more generic error message
						# Consider logging
					else:
						ls = ["\->"]
						try:
							assert isinstance(data_json, dict)
							ls.append("%s, %s, %s." % (data_json["title"], data_json["year"], " ".join(data_json.get("runtime", ("??",))))) # Use join
							ls.append(", ".join(data_json["genres"]))
							ls.append(", ".join(data_json["country"]))
							temp = data_json.get("directors")
							if temp:
								ls.append("Directors: " + ", ".join(temp[:3]))
							temp = data_json.get("writers")
							if temp:
								ls.append("Writers: " + ", ".join(temp[:3]))
							temp = data_json.get("actors")
							if temp:
								ls.append("Stars: " + ", ".join(temp[:5]))
							temp = data_json.get("plot") or data_json.get("plot_simple")
							if temp:
								ls.append(chr(171) + temp + chr(187)) # Keep chr for specific unicode points
							temp = data_json.get("rating")
							if temp:
								ls.append("IMDb rating: %s (%s)" % (temp, data_json.get("rating_count", 0)))
						except (AssertionError, TypeError, LookupError):
							answer = self.AnsBase[5]
						else:
							answer = self.sub_ehtmls("\n".join(ls)) # Use \n and join
			else:
				body_search = (body if "*" != c1st else body[2:].strip()) # Simplified chr(42)
				if body_search:
					body_encoded = body_search.encode("utf-8") # body_search is string
					IMDbRequest = self.IMDbRequest.copy()
					IMDbRequest["q"] = body_encoded # Pass bytes directly if API expects it, or string if Web handles encoding
					IMDbRequest["limit"] = "10"
					Opener = Web("http://imdbapi.org/?", list(IMDbRequest.items()))
					try:
						data = Opener.get_page(self.UserAgent_Moz) # Returns decoded string
					except urllib.error.HTTPError as exc: # Specific exception
						answer = str(exc)
					except urllib.error.URLError as exc: # Broader network errors
						answer = str(exc)
					except Exception: # Catch any other unexpected error
						answer = self.AnsBase[0]
						# Consider logging
					else:
						try:
							data_json = self.json.loads(data) # data is already string
						except json.JSONDecodeError: # Specific error for JSON parsing
							answer = self.AnsBase[1]
						except Exception: # Catch any other unexpected error during parsing
							answer = self.AnsBase[1] # Or a more generic error message
							# Consider logging
						else:
							try:
								assert isinstance(data_json, list)
								sorted_data = sorted([(desc.get("rating"), # Renamed data to sorted_data
												desc["title"],
												desc["year"],
												desc["imdb_id"][2:]) for desc in data_json], reverse = True)
							except (AssertionError, TypeError, LookupError):
								answer = self.AnsBase[5]
							else:
								ls = ["\n[#] [Name, Year] (#id)"]
								for Number, (Numb, Name, Year, ID) in enumerate(sorted_data, 1):
									ls.append("%d) %s, %s (#%s)" % (Number, Name, Year, ID))
								answer = self.sub_ehtmls("\n".join(ls)) # Use \n and join
				else:
					answer = AnsBase[2]
		else:
			answer = AnsBase[1]
		if sBase[6] in locals(): # Check if answer was defined
			Answer(answer, stype, source, disp)

	def command_python(self, stype, source, body, disp):
		Opener = Web("http://python.org/")
		try:
			data = Opener.get_page(self.UserAgent) # Returns decoded string (koi8-r if Web.get_page handles it)
		except urllib.error.HTTPError as exc: # Specific exception
			answer = str(exc)
		except urllib.error.URLError as exc: # Broader network errors
			answer = str(exc)
		except Exception: # Catch any other unexpected error
			answer = self.AnsBase[0]
			# Consider logging
		else:
			# data = data.decode("koi8-r") # Assuming get_page decodes
			data = get_text(data, "<h2 class=\"news\">", "</div>")
			if data:
				data = self.decodeHTML(data)
				ls = []
				for line in data.splitlines():
					if line.strip():
						ls.append(line)
				answer = "\n".join(ls) # Use \n and join
			else:
				answer = self.AnsBase[1]
		Answer(answer, stype, source, disp)

	def command_url_shorten(self, stype, source, body, disp):
		if body:
			Opener = Web("http://is.gd/create.php?", [("format", "json"), ("url", body.encode("utf-8"))])
			try:
				data = Opener.get_page(self.UserAgent) # Returns decoded string
			except urllib.error.HTTPError as exc: # Specific exception
				answer = str(exc)
			except urllib.error.URLError as exc: # Broader network errors
				answer = str(exc)
			except Exception: # Catch any other unexpected error
				answer = self.AnsBase[0]
				# Consider logging
			else:
				try:
					data_json = self.json.loads(data) # data is already string
				except json.JSONDecodeError: # Specific error for JSON parsing
					answer = self.AnsBase[1]
				except Exception: # Catch any other unexpected error during parsing
					answer = self.AnsBase[1] # Or a more generic error message
					# Consider logging
				else:
					try:
						answer = data_json["shorturl"]
					except KeyError:
						try:
							answer = data_json["errormessage"]
						except KeyError:
							answer = self.AnsBase[1]
		else:
			answer = AnsBase[1]
		Answer(answer, stype, source, disp)

	downloadLock = ithr.allocate_lock()

	def download_process(self, info, blockNumb, blockSize, size, fb):
		if not blockNumb:
			Print("\n")
			Print(str(info), color3)
		elif size >= blockSize:
			fb[3] += blockSize
			if not fb[4]:
				fb[4] = (size / 100)
				if fb[4] in (0, 1):
					fb[4] = 2
				else:
					residue = fb[4] % blockSize
					if fb[4] == residue:
						fb[4] = 2
						while fb[4] < residue:
							fb[4] *= 2
					elif residue:
						fb[4] -= residue
			if fb[3] >= size:
				Print("Done.", color3)
			elif not fb[3] % fb[4]:
				Pcts = fb[3] / fb[4]
				if Pcts == 100:
					Pcts = 99.95
				Print("loaded - {0}%".format(Pcts), color4)
				Time = time.time()
				if Time - fb[1] >= 30:
					fb[1] = Time
					Message(fb[0], self.AnsBase[9].format(Pcts), fb[2])

	def command_download(self, stype, source, body, disp):
		if body:
			if not self.downloadLock.locked():
				with self.downloadLock:
					body = body.split()
					if len(body) == 1:
						link = body.pop()
						folder = None
						filename = None
					elif len(body) == 2:
						link, folder = body
						filename = None
					else:
						link, folder, filename = body[:3]
					if not enough_access(source[1], source[2], 8):
						folder = "Downloads"
					if filename:
						filename = os.path.basename(filename.rstrip("\\/"))
					if folder:
						folder = os.path.normpath(folder)
						if AsciiSys:
							folder = folder.encode("utf-8")
						if not os.path.isdir(folder):
							try:
								os.makedirs(folder)
							except OSError as exc: # More specific exception for os operations
								link = None
								# Consider logging.error(f"Failed to create directory {folder}: {exc}")
						if AsciiSys:
							folder = folder.decode("utf-8")
					if link:
						Message(source[0], self.AnsBase[10], disp)
						Opener = Web(link)
						try:
							# data variable here is a tuple (filename, info, size) from Opener.download
							download_data = Opener.download(filename, folder, self.download_process, [source[0], time.time(), disp, 0, 0], self.UserAgent)
						except urllib.error.HTTPError as exc: # Specific exception
							answer = str(exc)
						except SelfExc as exc:
							answer = "Error! %s." % exc.args[0].capitalize() # Access SelfExc args
						except urllib.error.URLError as exc: # Broader network errors
							answer = str(exc)
						except Exception: # Catch any other unexpected error
							answer = self.AnsBase[0]
							# Consider logging
						else:
							answer = "Done.\nPath: %s\nSize: %s" % (download_data[0], Size2Text(download_data[2])) # Use download_data
					else:
						answer = AnsBase[2]
			else:
				answer = self.AnsBase[11]
		else:
			answer = AnsBase[1]
		Answer(answer, stype, source, disp)

	PasteLangs = PasteLangs

	def command_paste(self, stype, source, body, disp):
		if body:
			args = body.split(None, 1)
			arg0 = (args.pop(0)).lower()
			if arg0 in self.PasteLangs:
				if args:
					body_content = args.pop() # Renamed body to body_content
				else:
					body_content = None
					answer = AnsBase[2]
			else:
				arg0 = "text"
				body_content = body # Original body is the content
			if body_content:
				Opener = Web("http://paste.ubuntu.com/", data = Web.encode({"poster": ProdName, "syntax": arg0, "content": body_content.encode("utf-8")}))
				try:
					fp = Opener.open(self.UserAgent)
					answer = fp.url
					fp.close()
				except urllib.error.HTTPError as exc: # Specific exception
					answer = str(exc)
				except urllib.error.URLError as exc: # Broader network errors
					answer = str(exc)
				except Exception: # Catch any other unexpected error
					answer = self.AnsBase[0]
					# Consider logging
			# This else was part of "if body:" - it should be outside if body_content is None from the start
			elif not body_content and arg0 in self.PasteLangs : # Only show usage if lang was valid but no content
				answer = AnsBase[2]
			else: # This is for when the initial "if body:" is false, or arg0 was not a lang and body was empty
				answer = self.AnsBase[8] + "\n".join(["%s - %s" % (k, l) for k, l in sorted(self.PasteLangs.items())]) # Use \n and join
				if stype == sBase[1]: # and answer was just created (usage string)
					Message(source[0], answer, disp) # Send usage via private message
					answer = AnsBase[11] # Then set this for the public reply
		else: # Initial "if body:" is false
			answer = self.AnsBase[8] + "\n".join(["%s - %s" % (k, l) for k, l in sorted(self.PasteLangs.items())])
			if stype == sBase[1]:
				Message(source[0], answer, disp)
				answer = AnsBase[11]
		Answer(answer, stype, source, disp)


	if DefLANG in ("RU", "UA"):

		def command_chuck(self, stype, source, body, disp):
			if body and isNumber(body): # body is str
				Opener = Web("http://chucknorrisfacts.ru/quote/%d" % int(body))
			else:
				Opener = Web("http://chucknorrisfacts.ru/random")
			try:
				data = Opener.get_page(self.UserAgent) # Returns decoded string
			except urllib.error.HTTPError as exc: # Specific exception
				answer = str(exc)
			except urllib.error.URLError as exc: # Broader network errors
				answer = str(exc)
			except Exception: # Catch any other unexpected error
				answer = self.AnsBase[0]
				# Consider logging
			else:
				# data = data.decode("cp1251") # Assuming get_page decodes
				comp = compile__("<a href=/quote/(\d+?)>.+?<blockquote>(.+?)</blockquote>", 16)
				match_data = comp.search(data) # Renamed data to match_data
				if match_data:
					answer = self.decodeHTML("#%s\n%s" % match_data.groups())
				else:
					answer = self.AnsBase[1]
			Answer(answer, stype, source, disp)

		def command_bash(self, stype, source, body, disp):
			if body and isNumber(body): # body is str
				Opener = Web("http://bash.im/quote/%d" % int(body))
			else:
				Opener = Web("http://bash.im/random")
			try:
				data = Opener.get_page(self.UserAgent) # Returns decoded string
			except urllib.error.HTTPError as exc: # Specific exception
				answer = str(exc)
			except urllib.error.URLError as exc: # Broader network errors
				answer = str(exc)
			except Exception: # Catch any other unexpected error
				answer = self.AnsBase[0]
				# Consider logging
			else:
				# data = data.decode("cp1251") # Assuming get_page decodes
				comp = compile__('<span id="v\d+?" class="rating">(.+?)</span>(?:.|\s)+?<a href="/quote/\d+?" class="id">#(\d+?)</a>\s*?</div>\s+?<div class="text">(.+?)</div>', 16)
				match_data = comp.search(data) # Renamed data to match_data
				if match_data:
					answer = self.decodeHTML("#{1} +[{0}]-\n{2}".format(*match_data.groups()))
				else:
					answer = self.AnsBase[1]
			Answer(answer, stype, source, disp)

	else: # Not RU or UA

		def command_chuck(self, stype, source, body, disp):
			Opener = Web("http://www.chucknorrisfacts.com/all-chuck-norris-facts?page=%d" % randrange(974))
			try:
				data = Opener.get_page(self.UserAgent) # Returns decoded string
			except urllib.error.HTTPError as exc: # Specific exception
				answer = str(exc)
			except urllib.error.URLError as exc: # Broader network errors
				answer = str(exc)
			except Exception: # Catch any other unexpected error
				answer = self.AnsBase[0]
				# Consider logging
			else:
				# data = data.decode("utf-8") # Assuming get_page decodes
				comp = compile__("<span class=\"field-content\"><a.*?>(.+?)</a></span>", 16)
				found_list = comp.findall(data) # Renamed list
				if found_list:
					answer = self.decodeHTML(choice(found_list))
				else:
					answer = self.AnsBase[1]
			Answer(answer, stype, source, disp)

		def command_bash(self, stype, source, body, disp):
			if body and isNumber(body): # body is str
				Opener = Web("http://bash.org/?%d" % int(body))
			else:
				Opener = Web("http://bash.org/?random")
			try:
				data = Opener.get_page(self.UserAgent) # Returns decoded string
			except urllib.error.HTTPError as exc: # Specific exception
				answer = str(exc)
			except urllib.error.URLError as exc: # Broader network errors
				answer = str(exc)
			except Exception: # Catch any other unexpected error
				answer = self.AnsBase[0]
				# Consider logging
			else:
				# data = data.decode("iso-8859-1") # Assuming get_page decodes
				comp = compile__('<b>#(\d+?)</b></a>\s<a.*?>\+</a>\((.+?)\)<a.*?>-</a>\s<a.*?>\[X\]</a></p><p class="qt">(.+?)</p>', 16)
				match_data = comp.search(data) # Renamed data to match_data
				if match_data:
					answer = self.decodeHTML("#%s +[%s]-\n%s" % match_data.groups())
				else:
					answer = self.AnsBase[1]
			Answer(answer, stype, source, disp)

	def command_currency(self, stype, source, body, disp):
		if body:
			ls = body.split()
			code_param = (ls.pop(0)).lower() # Renamed Code to code_param
			if code_param in ("code", "аббревиатура"): # Removed decode
				if ls:
					code_val = (ls.pop(0)).upper() # Renamed Code to code_val
					if code_val in self.CurrencyDesc:
						answer = self.CurrencyDesc[code_val] # Removed decode
					else:
						answer = self.AnsBase[1]
				else:
					answer = AnsBase[2]
			elif code_param in ("list", "список"): # Removed decode
				if stype == sBase[1]:
					Answer(AnsBase[11], stype, source, disp)
				curls_list = ["\->"] + ["%s: %s" % desc for desc in sorted(self.CurrencyDesc.items())] # Renamed Curls
				Message(source[0], "\n".join(curls_list), disp) # Use \n and join
				# answer is not set here, if stype != sBase[1], this will be an error later
				# However, keeping original logic for now.
			elif code_param in ("calc", "перевести"): # Removed decode
				if len(ls) >= 2:
					number_str = ls.pop(0) # Renamed Number
					if isNumber(number_str) and ls[0].isalpha():
						number_val = int(number_str) # Renamed Number
						code_val = (ls.pop(0)).upper() # Renamed Code
						if (code_val == "RUB"):
							answer = "%d %s" % (number_val, code_val)
						elif code_val in self.CurrencyDesc:
							Opener = Web("http://www.cbr.ru/scripts/XML_daily.asp")
							try:
								data = Opener.get_page(self.UserAgent) # Returns decoded string
							except urllib.error.HTTPError as exc: # Specific exception
								answer = str(exc)
							except urllib.error.URLError as exc: # Broader network errors
								answer = str(exc)
							except Exception: # Catch any other unexpected error
								answer = self.AnsBase[0]
								# Consider logging
							else:
								# data = data.decode("cp1251") # Assuming get_page decodes
								comp = compile__("<CharCode>%s</CharCode>\s+?<Nominal>(.+?)</Nominal>\s+?<Name>.+?</Name>\s+?<Value>(.+?)</Value>" % (code_val), 16)
								match_data = comp.search(data) # Renamed data
								if match_data:
									no_str, numb_str = match_data.groups() # Renamed No, Numb
									numb_str = numb_str.replace(",", ".") # Simplified chr(44)
									no_str = no_str.replace(",", ".")   # Simplified chr(44)
									try:
										numb_float = (number_val*(float(numb_str)/float(no_str))) # Renamed Numb
									except (ValueError, ZeroDivisionError): # Specific errors for float conversion or division by zero
										answer = AnsBase[7]
									except Exception: # Catch any other unexpected error
										answer = AnsBase[7] # Or a more generic error
										# Consider logging
									else:
										answer = "%.2f RUB" % (numb_float)
								else:
									answer = self.AnsBase[1]
						else:
							answer = AnsBase[2]
					else:
						answer = AnsBase[2]
				else:
					answer = AnsBase[2]
			elif (code_param != "rub") and code_param.isalpha():
				code_val = code_param.upper() # Renamed Code
				if code_val in self.CurrencyDesc:
					Opener = Web("http://www.cbr.ru/scripts/XML_daily.asp")
					try:
						data = Opener.get_page(self.UserAgent) # Returns decoded string
					except urllib.error.HTTPError as exc: # Specific exception
						answer = str(exc)
					except urllib.error.URLError as exc: # Broader network errors
						answer = str(exc)
					except Exception: # Catch any other unexpected error
						answer = self.AnsBase[0]
						# Consider logging
					else:
						# data = data.decode("cp1251") # Assuming get_page decodes
						comp = compile__("<CharCode>%s</CharCode>\s+?<Nominal>(.+?)</Nominal>\s+?<Name>.+?</Name>\s+?<Value>(.+?)</Value>" % (code_val), 16)
						match_data = comp.search(data) # Renamed data
						if match_data:
							no_str, numb_str = match_data.groups() # Renamed No, Numb
							answer = "%s/RUB - %s/%s" % (code_val, no_str, numb_str)
						else:
							answer = self.AnsBase[1]
				else:
					answer = AnsBase[2]
			else:
				answer = AnsBase[2]
		else: # Initial "if body:" is false
			Opener = Web("http://www.cbr.ru/scripts/XML_daily.asp")
			try:
				data = Opener.get_page(self.UserAgent) # Returns decoded string
			except urllib.error.HTTPError as exc: # Specific exception
				answer = str(exc)
			except urllib.error.URLError as exc: # Broader network errors
				answer = str(exc)
			except Exception: # Catch any other unexpected error
				answer = self.AnsBase[0]
				# Consider logging
			else:
				# data = data.decode("cp1251") # Assuming get_page decodes
				comp = compile__("<CharCode>(.+?)</CharCode>\s+?<Nominal>(.+?)</Nominal>\s+?<Name>.+?</Name>\s+?<Value>(.+?)</Value>", 16)
				found_list = comp.findall(data) # Renamed list
				if found_list:
					ls_out, number_counter = ["\->"], itypes.Number() # Renamed ls, Number
					for code_item, no_item, numb_item in sorted(found_list): # Renamed Code, No, Numb
						ls_out.append("%d) %s/RUB - %s/%s" % (number_counter.plus(), code_item, no_item, numb_item))
					if stype == sBase[1]:
						Answer(AnsBase[11], stype, source, disp)
					curls_text = "\n".join(ls_out) # Renamed Curls, use \n and join
					Message(source[0], curls_text, disp)
					# answer is not set here if stype != sBase[1]
				else:
					answer = self.AnsBase[1]
		if sBase[6] in locals(): # Check if answer was defined (it might not be if message was sent above)
			Answer(answer, stype, source, disp)

	def command_jquote(self, stype, source, body, disp):
		if body and isNumber(body): # body is str
			Opener = Web("http://jabber-quotes.ru/api/read/?id=%d" % int(body))
		else:
			Opener = Web("http://jabber-quotes.ru/api/read/?id=random")
		try:
			data = Opener.get_page(self.UserAgent) # Returns decoded string
		except urllib.error.HTTPError as exc: # Specific exception
			answer = str(exc)
		except urllib.error.URLError as exc: # Broader network errors
			answer = str(exc)
		except Exception: # Catch any other unexpected error
			answer = self.AnsBase[0]
			# Consider logging
		else:
			# data = data.decode("utf-8") # Assuming get_page decodes
			comp = compile__("<id>(\d+?)</id>\s+?<author>(.+?)</author>\s+?<quote>(.+?)</quote>", 16)
			match_data = comp.search(data) # Renamed data
			if match_data:
				numb_val, name_val, quote_val = match_data.groups() # Renamed Numb, Name, Quote
				lt = "\n\n\n" # Use \n
				answer = self.decodeHTML("Quote: #%s | by %s\n%s" % (numb_val, name_val, quote_val))
				while (lt in answer):
					answer = answer.replace(lt, lt[:2])
			else:
				answer = self.AnsBase[1]
		Answer(answer, stype, source, disp)

	def command_ithappens(self, stype, source, body, disp):
		if body and isNumber(body): # body is str
			Opener = Web("http://ithappens.ru/story/%d" % int(body))
		else:
			Opener = Web("http://ithappens.ru/random")
		try:
			data = Opener.get_page(self.UserAgent) # Returns decoded string
		except urllib.error.HTTPError as exc: # Specific exception
			answer = str(exc)
		except urllib.error.URLError as exc: # Broader network errors
			answer = str(exc)
		except Exception: # Catch any other unexpected error
			answer = self.AnsBase[0]
			# Consider logging
		else:
			# data = data.decode("cp1251") # Assuming get_page decodes
			data = get_text(data, "<div class=\"text\">", "</p>")
			if data:
				answer = self.decodeHTML(sub_desc(data, {"<p class=\"date\">": " "})) # Simplified chr(32)
			else:
				answer = self.AnsBase[1]
		Answer(answer, stype, source, disp)

	def command_gismeteo(self, stype, source, body, disp):
		if body:
			ls = body.split(None, 1)
			numb_str = ls.pop(0) # Renamed Numb
			if ls and isNumber(numb_str):
				numb_val = int(numb_str) # Renamed Numb
				city_val = ls.pop(0) # Renamed City
			else:
				numb_val = None
				city_val = body # Renamed City
			if -1 < numb_val < 13 or not numb_val : # Check numb_val
				Opener = Web("http://m.gismeteo.ru/citysearch/by_name/?", [("gis_search", city_val.encode("utf-8"))])
				try:
					data = Opener.get_page(self.UserAgent) # Returns decoded string
				except urllib.error.HTTPError as exc: # Specific exception
					answer = str(exc)
				except urllib.error.URLError as exc: # Broader network errors
					answer = str(exc)
				except Exception: # Catch any other unexpected error
					answer = self.AnsBase[0]
					# Consider logging
				else:
					# data = data.decode("utf-8") # Assuming get_page decodes
					weather_path = get_text(data, "<a href=\"/weather/", "/(1/)*?\">", "\d+") # Renamed data to weather_path
					if weather_path:
						if numb_val != None:
							weather_path = "/".join([weather_path, str(numb_val) if numb_val != 0 else "weekly"]) # Use join, simplified chr(47)
						Opener = Web("http://m.gismeteo.ru/weather/%s/" % weather_path)
						try:
							data = Opener.get_page(self.UserAgent) # Returns decoded string
						except urllib.error.HTTPError as exc: # Specific exception
							answer = str(exc)
						except urllib.error.URLError as exc: # Broader network errors
							answer = str(exc)
						except Exception: # Catch any other unexpected error
							answer = self.AnsBase[0]
							# Consider logging
						else:
							# data = data.decode("utf-8") # Assuming get_page decodes
							mark = get_text(data, "<th colspan=\"2\">", "</th>")
							if numb_val != 0:
								comp = compile__('<tr class="tbody">\s+?<th.*?>(.+?)</th>\s+?<td.+?/></td>\s+?</tr>\s+?<tr>\s+?<td.+?>(.+?)</td>\s+?</tr>\s+?<tr class="dl">\s+?<td>&nbsp;</td>\s+?<td class="clpersp"><p>(.*?)</p></td>\s+?</tr>\s+?<tr class="dl"><td class="left">(.+?)</td><td>(.+?)</td></tr>\s+?<tr class="dl"><td class="left">(.+?)</td><td>(.+?)</td></tr>\s+?<tr class="dl bottom"><td class="left">(.+?)</td><td>(.+?)</td></tr>', 16)
								found_weather_list = comp.findall(data) # Renamed list
								if found_weather_list:
									ls_out = [(self.decodeHTML(mark) if mark else "\->")] # Renamed ls
									for item_data in found_weather_list: # Renamed data to item_data
										ls_out.append("{0}:\n\t{2}, {1}\n\t{3} {4}\n\t{5} {6}\n\t{7} {8}".format(*item_data))
									ls_out.append(self.AnsBase[-2])
									answer = self.decodeHTML("\n".join(ls_out)) # Use \n and join
								else:
									answer = self.AnsBase[1]
							else: # numb_val is 0 (weekly) or None (current if not specified)
								comp = compile__('<tr class="tbody">\s+?<td class="date" colspan="3"><a.+?>(.+?)</a></td>\s+?</tr>\s+?<tr>\s+?<td rowspan="2"><a.+?/></a></td>\s+?<td class="clpersp"><p>(.*?)</p></td>\s+?</tr>\s+?<tr>\s+?<td.+?>(.+?)</td>', 16)
								found_weather_list = comp.findall(data) # Renamed list
								if found_weather_list:
									ls_out = [(self.decodeHTML(mark) if mark else "\->")] # Renamed ls
									for item_data in found_weather_list: # Renamed data to item_data
										ls_out.append("%s:\n\t%s, %s" % (item_data))
									ls_out.append(self.AnsBase[-2])
									answer = self.decodeHTML("\n".join(ls_out)) # Use \n and join
								else:
									answer = self.AnsBase[1]
					else:
						answer = self.AnsBase[5]
			else: # Invalid Numb (not -1 < Numb < 13)
				answer = AnsBase[2]
		else: # Initial "if body:" is false
			answer = AnsBase[1]
		Answer(answer, stype, source, disp)

	def command_yandex_market(self, stype, source, body, disp):
		if body:
			ls = body.split()
			c1st = (ls.pop(0)).lower()
			if isNumber(c1st): # c1st is str
				if ls:
					c2nd = ls.pop(0)
					if isNumber(c2nd): # c2nd is str
						Opener = Web("http://m.market.yandex.ru/spec.xml?hid=%d&modelid=%d" % (int(c1st), int(c2nd)))
						try:
							data = Opener.get_page(self.UserAgent_Moz) # Returns decoded string
						except urllib.error.HTTPError as exc: # Specific exception
							answer = str(exc)
						except urllib.error.URLError as exc: # Broader network errors
							answer = str(exc)
						except Exception: # Catch any other unexpected error
							answer = self.AnsBase[0]
							# Consider logging
						else:
							# data = data.decode("utf-8", "replace") # Assuming get_page decodes
							market_text = get_text(data, "<h2 class=\"b-subtitle\">", "</div>") # Renamed data
							if market_text:
								answer = self.decodeHTML(sub_desc(market_text, ("\n", ("<li>", "\n"), ("<h2 class=\"b-subtitle\">", "\n\n"), ("</h2>", "\n")))) # Simplified chr
							else:
								answer = self.AnsBase[5]
					else:
						answer = AnsBase[30]
				else:
					answer = AnsBase[2]
			else:
				body_search = (body if "*" != c1st else body[2:].strip()) # Simplified chr(42)
				if body_search:
					body_encoded = body_search.encode("utf-8") # body_search is str
					Opener = Web("http://m.market.yandex.ru/search.xml?", [("nopreciser", "1"), ("text", body_encoded)])
					try:
						data = Opener.get_page(self.UserAgent_Moz) # Returns decoded string
					except urllib.error.HTTPError as exc: # Specific exception
						answer = str(exc)
					except urllib.error.URLError as exc: # Broader network errors
						answer = str(exc)
					except Exception: # Catch any other unexpected error
						answer = self.AnsBase[0]
						# Consider logging
					else:
						# data = data.decode("utf-8", "replace") # Assuming get_page decodes
						comp = compile__("<a href=\"http://m\.market\.yandex\.ru/model\.xml\?hid=(\d+?)&amp;modelid=(\d+?)&amp;show-uid=\d+?\">(.+?)</a>", 16)
						found_items = comp.findall(data) # Renamed list
						if found_items:
							number_counter = itypes.Number() # Renamed Number
							ls_out = ["\n[#] [Model Name] (hid & modelid)"] # Renamed ls
							for hid, modelid, name in found_items:
								if not name.startswith("<img"):
									ls_out.append("%d) %s (%s %s)" % (number_counter.plus(), self.sub_ehtmls(name), hid, modelid))
							answer = "\n".join(ls_out) # Use \n and join
						else:
							answer = self.AnsBase[5]
				else:
					answer = AnsBase[2]
		else: # Initial "if body:" is false
			answer = AnsBase[1]
		Answer(answer, stype, source, disp)

	commands = (
		(command_jc, "jc", 2,),
		(command_google, "google", 2,),
		(command_google_translate, "tr", 2,),
		(command_imdb, "imdb", 2,),
		(command_python, "python", 2,),
		(command_url_shorten, "shorten", 2,),
		(command_download, "download", 7,),
		(command_paste, "paste", 2,),
		(command_chuck, "chuck", 2,),
		(command_bash, "bash", 2,)
	)

	if DefLANG in ("RU", "UA"):
		commands = commands.__add__((
			(command_kino, "kino", 2,),
			(command_currency, "currency", 2,),
			(command_jquote, "jquote", 2,),
			(command_ithappens, "ithappens", 2,),
			(command_gismeteo, "gismeteo", 2,),
			(command_yandex_market, "market", 2,)
		))
		CurrencyDesc = CurrencyDesc
	else:
		del kinoHeaders, C3oP, command_kino, command_currency, command_jquote, command_ithappens, command_gismeteo

if DefLANG in ("RU", "UA"):
	del CurrencyDesc
del UserAgents, PasteLangs, LangMap
