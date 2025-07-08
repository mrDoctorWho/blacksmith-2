"""
Module "fb2"
fb2.py

Copyright (2011-2013) Al Korgun (alkorgun@gmail.com)

Distributed under the GNU GPLv3.
"""

import re # Changed from from re import compile as compile__
import time # Changed from from time import asctime
import html.entities

# __all__ will be updated based on final public API after renaming
__all__ = [
	# "HTML_ENTITIES_STANDARD_MAP", # Not directly re-exporting html.entities itself
	"HTML_ENTITY_DEFINITIONS_MAP",
	# "REGEX_COMPILE_FUNCTION", # Not re-exporting re.compile
	# "TIME_ASCTIME_FORMATTER", # Not re-exporting time.asctime
	"get_xml_encoding",
	"strip_tags_and_substitute_entities",
	"substitute_fb2_titles",
	"get_text_between_tags", # Renamed get_text
	"replace_patterns_in_string", # Renamed sub_desc
	"parse_fb2_data", # Renamed get_data
	"create_fb2_document" # Renamed make
]

__version__ = "0.1.8"

HTML_ENTITY_DEFINITIONS_MAP = {} # Renamed edefs

for entity_name, code_point in html.entities.name2codepoint.items(): # Renamed Name, Numb
	HTML_ENTITY_DEFINITIONS_MAP[entity_name] = chr(code_point)

del entity_name, code_point # Clean up loop variables

HTML_ENTITY_DEFINITIONS_MAP["&apos;"] = chr(39)

REGEX_STRIP_TAGS = re.compile("<[^<>]+?>") # Renamed compile_st
REGEX_HTML_ENTITIES = re.compile("&(#?[xX]?(?:[0-9a-fA-F]+|\w{1,8}));") # Renamed compile_ehtmls
REGEX_SECTION_TITLE = re.compile("<title>((?:.|\s)+?)</title>", 16) # Renamed compile_stitle
REGEX_SUBTITLE = re.compile("<subtitle>((?:.|\s)+?)</subtitle>", 16) # Renamed compile_subtitle

def substitute_fb2_titles(data_string): # Renamed sub_titles, data
	if "<title>" in data_string: # More direct check than count
		def title_replacer(match_obj): # Renamed st, co
		    title_content = match_obj.group(1).strip()
		    # Replace newlines in title content with " - "
		    processed_title = replace_patterns_in_string(REGEX_STRIP_TAGS.sub("", title_content), {chr(10): " - "})
		    return f"\n\n(*t)\t{processed_title}\n\n"
		data_string = REGEX_SECTION_TITLE.sub(title_replacer, data_string)
	if "<subtitle>" in data_string:
		def subtitle_replacer(match_obj): # Renamed st, co
		    subtitle_content = match_obj.group(1).strip()
		    processed_subtitle = replace_patterns_in_string(REGEX_STRIP_TAGS.sub("", subtitle_content), {chr(10): " - "})
		    return f"\n\n(*sbt)\t{processed_subtitle}\n\n"
		data_string = REGEX_SUBTITLE.sub(subtitle_replacer, data_string)
	return data_string

def substitute_html_entities(data_string): # Renamed sub_ehtmls, data
	if "&" in data_string: # Check if there are any ampersands first
		def entity_substitution_callback(match_obj): # Renamed e_sb, co
			entity_key = match_obj.group(1) # Renamed co
			if entity_key.startswith("#"): # Numeric character reference
				if entity_key[1].lower() == 'x': # Hexadecimal
					char_code_str, base_val = entity_key[2:], 16 # Renamed Char, c06
				else: # Decimal
					char_code_str, base_val = entity_key[1:], 10
				try:
					num_val = int(char_code_str, base_val) # Renamed Numb
					# Ensure it's a valid Unicode code point (basic check)
					if not (-1 < num_val < 0x110000): num_val = 0xFFFD # Replacement char
					return chr(num_val) # Renamed Char
				except ValueError: # Not a valid number in that base
					return HTML_ENTITY_DEFINITIONS_MAP.get(char_code_str, f"&{entity_key};") # Keep original if invalid num
			else: # Named entity
				return HTML_ENTITY_DEFINITIONS_MAP.get(entity_key, f"&{entity_key};") # Renamed Char

		data_string = REGEX_HTML_ENTITIES.sub(entity_substitution_callback, data_string)
	return data_string

strip_tags_and_substitute_entities = lambda data_string: substitute_html_entities(REGEX_STRIP_TAGS.sub("", data_string)).strip() # Renamed sub_all

def get_text_between_tags(data_string, start_tag_pattern, end_tag_pattern, content_pattern = "(?:.|\s)+"): # Renamed get_text, data, s0,s1,s2
	regex_object = re.compile(f"{start_tag_pattern}({content_pattern}?){end_tag_pattern}", re.DOTALL | re.IGNORECASE) # Use re.DOTALL for s, 16 is re.I
	match_object = regex_object.search(data_string) # Renamed data to match_object for clarity
	if match_object:
		return match_object.group(1).strip() # Renamed data
	return None

get_xml_encoding = lambda data_string: get_text_between_tags(data_string, 'encoding="', '"\?') # Renamed get_enc, data

def replace_patterns_in_string(data_string, replacements_list_or_dict, default_substitution_str = ""): # Renamed sub_desc, data, ls, sub
	if isinstance(replacements_list_or_dict, dict):
		for pattern_to_find, replacement_str in replacements_list_or_dict.items(): # Renamed x, z
			data_string = data_string.replace(pattern_to_find, replacement_str)
	else: # Assuming it's a list of patterns or (pattern, replacement) tuples
		for item in replacements_list_or_dict: # Renamed x
			if isinstance(item, (list, tuple)):
				if len(item) > 1:
					data_string = data_string.replace(item[0], item[1])
				else: # Single item in tuple/list, replace with default_substitution_str
					data_string = data_string.replace(item[0], default_substitution_str)
			else: # Item is a string, replace with default_substitution_str
				data_string = data_string.replace(item, default_substitution_str)
	return data_string

def parse_fb2_data(fb2_content_string): # Renamed get_data, data
	# Normalize line endings and common tags to newlines for easier processing
	processed_content = replace_patterns_in_string(fb2_content_string,
	                                             ["\r\n", "\r", ("<p>", "\n"), ("</p>", "\n"), ("<v>", "\n"), ("<empty-line/>", "\n\n")])
	# Remove any remaining <p attributes...> tags, replacing with newline
	paragraph_tag_with_attributes_regex = re.compile("<p.*?>")
	processed_content = paragraph_tag_with_attributes_regex.sub("\n", processed_content).strip()

	description_data = None # Renamed desc
	description_xml_str = get_text_between_tags(processed_content, "<description>", "</description>")

	if description_xml_str:
		author_str = None # Renamed author
		creator_xml_str = get_text_between_tags(description_xml_str, "<author>", "</author>") # Renamed creator
		if creator_xml_str:
			name_parts_tags = ("first-name", "middle-name", "last-name") # Renamed tl
			author_name_parts = [] # Renamed ls
			for tag_name_part in name_parts_tags: # Renamed tn
				name_part_text = get_text_between_tags(creator_xml_str, f"<{tag_name_part}>", f"</{tag_name_part}>") # Renamed td
				if name_part_text:
					author_name_parts.append(name_part_text)
			if author_name_parts:
			    author_str = strip_tags_and_substitute_entities(" ".join(author_name_parts)) # Use new name

		cover_image_data = None # Renamed coverD
		binary_cover_match = re.search("<binary.+?content-type=\"image/(.+?)\".*?>((?:.|\s)+?)</binary>", processed_content, re.IGNORECASE | re.DOTALL) # Use re.search
		if binary_cover_match:
			cover_image_data = binary_cover_match.groups() # (image_type, base64_data)

		genre_str = get_text_between_tags(description_xml_str, "<genre>", "</genre>") # Renamed genre
		annotation_text = get_text_between_tags(description_xml_str, "<annotation>", "</annotation>") # Renamed annt
		book_title_str = get_text_between_tags(description_xml_str, "<book-title>", "</book-title>") # Renamed name
		date_str = get_text_between_tags(description_xml_str, "<date>", "</date>") # Renamed date

		publication_year = None # Renamed date (numeric)
		if date_str:
			date_parts = date_str.split(".") # Renamed ls
			try:
				publication_year = int(date_parts[-1])
			except (ValueError, IndexError):
				publication_year = None

		sequence_name, sequence_number = None, None # Renamed seq1, seq2
		sequence_xml_str = get_text_between_tags(description_xml_str, "<sequence", "/>") # Renamed sequence
		if sequence_xml_str:
			sequence_name = get_text_between_tags(sequence_xml_str, 'name="', '"')
			number_str = get_text_between_tags(sequence_xml_str, 'number="', '"')
			if number_str:
				number_parts = number_str.split(".") # Renamed ls
				try:
					sequence_number = int(number_parts[-1])
				except (ValueError, IndexError):
					sequence_number = None

		if sequence_name: sequence_name = strip_tags_and_substitute_entities(sequence_name)
		if book_title_str: book_title_str = strip_tags_and_substitute_entities(book_title_str)
		if annotation_text: annotation_text = strip_tags_and_substitute_entities(annotation_text)
		if genre_str: genre_str = strip_tags_and_substitute_entities(genre_str)

		description_data = (book_title_str, author_str, publication_year, genre_str, sequence_name, sequence_number, cover_image_data, annotation_text)

	body_content_str = get_text_between_tags(processed_content, "<body.*?>", "</body>") # Renamed body
	if body_content_str:
		section_content_regex = re.compile("<section.*?>((?:.|\s)+?)</section>", re.IGNORECASE | re.DOTALL) # Renamed comp

		body_text_parts = [] # Renamed ls
		sections_found = section_content_regex.findall(body_content_str) # Renamed sections
		if sections_found:
			for section_html_content in sections_found: # Renamed body (loop var)
				body_text_parts.append(substitute_fb2_titles(section_html_content.strip())) # Use new name
			body_content_str = strip_tags_and_substitute_entities("\n".join(body_text_parts))
		else: # No sections, process body as a whole
		    body_content_str = strip_tags_and_substitute_entities(substitute_fb2_titles(body_content_str))

	return (description_data, body_content_str)


def create_fb2_document(body_content, book_title, author_name=None, publication_year=None, # Renamed params
                        genre_name=None, sequence_title=None, sequence_num=0,
                        cover_data_tuple=None, annotation_text=None, language_code="en",
                        program_used_str=f"fb2.py {__version__}", document_author_nickname=None): # Renamed User

	fb2_parts_list = ['''<?xml version="1.0" encoding="UTF-8"?>
<FictionBook xmlns:l="http://www.w3.org/1999/xlink" xmlns="http://www.gribuser.ru/xml/fictionbook/2.0">
<description>'''] # Renamed data

	fb2_parts_list.append("<title-info>")
	if genre_name:
		fb2_parts_list.append(f"<genre>{xml_escape_string(genre_name)}</genre>")
	if author_name:
		fb2_parts_list.append("<author>")
		name_components = author_name.split() # Renamed ls
		if len(name_components) == 1:
			fb2_parts_list.append(f"<last-name>{xml_escape_string(name_components.pop(0))}</last-name>")
		elif len(name_components) == 2:
			fb2_parts_list.append(f"<first-name>{xml_escape_string(name_components[0])}</first-name><last-name>{xml_escape_string(name_components[1])}</last-name>")
		else: # Assume first, last, and middle parts
			first_name_part = xml_escape_string(name_components.pop(0)) # Renamed first
			last_name_part = xml_escape_string(name_components.pop())   # Renamed last
			middle_names_str = xml_escape_string(" ".join(name_components))
			fb2_parts_list.append(f"<first-name>{first_name_part}</first-name><middle-name>{middle_names_str}</middle-name><last-name>{last_name_part}</last-name>")
		fb2_parts_list.append("</author>")
	fb2_parts_list.append(f"<book-title>{xml_escape_string(book_title)}</book-title>")
	if annotation_text:
		fb2_parts_list.append("<annotation>")
		for line_content in annotation_text.splitlines(): # Renamed line
			if line_content.strip(): # Add non-empty lines as paragraphs
				fb2_parts_list.append(f"<p>{xml_escape_string(line_content.strip())}</p>")
		fb2_parts_list.append("</annotation>")
	if publication_year:
		fb2_parts_list.append(f"<date>{str(publication_year)}</date>") # Ensure string
	if cover_data_tuple and len(cover_data_tuple) == 2: # (image_type_extension, base64_data)
		fb2_parts_list.append(f"<coverpage>\n<image l:href=\"#cover.{xml_escape_string(cover_data_tuple[0])}\"/>\n</coverpage>")
	fb2_parts_list.append(f"<lang>{language_code.lower()}</lang>")
	if sequence_title:
		if sequence_num: # Assuming sequence_num is integer or string convertible to int
			fb2_parts_list.append(f'<sequence name="{xml_escape_string(sequence_title)}" number="{str(sequence_num)}"/>')
		else:
			fb2_parts_list.append(f'<sequence name="{xml_escape_string(sequence_title)}"/>')
	fb2_parts_list.append("</title-info>")

	fb2_parts_list.append("<document-info>")
	if document_author_nickname:
		fb2_parts_list.append(f"<author>\n<nickname>{xml_escape_string(document_author_nickname)}</nickname>\n</author>")
	fb2_parts_list.append(f"<program-used>{xml_escape_string(program_used_str)}</program-used>")
	fb2_parts_list.append(f"<date value=\"{time.strftime('%Y-%m-%d')}\">{xml_escape_string(time.asctime())}</date>") # Use new time formatter
	fb2_parts_list.append("<version>2.0</version>") # FB2 version
	fb2_parts_list.append("</description>")

	fb2_parts_list.append("<body>")
	if body_content: # Ensure body_content is not None
		for line_content in body_content.splitlines(): # Renamed line
			stripped_line = line_content.strip()
			if stripped_line: # Process non-empty lines
				if stripped_line.startswith("(*t)"): # Section title
					if fb2_parts_list[-1] != "<body>": # Close previous section if not first
						fb2_parts_list.append("</section>")
					title_text = xml_escape_string(stripped_line[4:].strip())
					fb2_parts_list.append(f"<section>\n<title>\n<p>{title_text}</p>\n</title>\n<empty-line />")
				elif stripped_line.startswith("(*sbt)"): # Subtitle
					subtitle_text = xml_escape_string(stripped_line[6:].strip())
					fb2_parts_list.append(f"<subtitle>{subtitle_text}</subtitle>")
				else: # Regular paragraph
					fb2_parts_list.append(f"<p>{xml_escape_string(stripped_line)}</p>")
	if fb2_parts_list[-1] != "<body>": # Ensure last section is closed if any was opened
	    # This check might be too simple if body was empty or had no sections.
	    # A more robust way would be to track section state.
	    # For now, if last element added wasn't just "<body>", assume a section was open.
	    last_meaningful_append = next((s for s in reversed(fb2_parts_list) if s.strip()), None)
	    if last_meaningful_append and not last_meaningful_append.startswith("</section>") and not last_meaningful_append == "<body>":
	        fb2_parts_list.append("</section>")

	fb2_parts_list.append("</body>")

	if cover_data_tuple and len(cover_data_tuple) == 2:
		image_type, image_base64_data = cover_data_tuple
		fb2_parts_list.append(f'<binary content-type="image/{xml_escape_string(image_type)}" id="cover.{xml_escape_string(image_type)}">{xml_escape_string(image_base64_data)}</binary>')

	fb2_parts_list.append("</FictionBook>")
	# Original sub_desc was for removing specific markers; here we ensure clean output
	final_fb2_string = "\n".join(fb2_parts_list) # Renamed data
	# Remove any leftover (*t) or (*sbt) if they weren't processed into tags (shouldn't happen with current logic)
	final_fb2_string = final_fb2_string.replace("(*t)", "").replace("(*sbt)", "")
	return final_fb2_string
