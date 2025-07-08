"""
BlackSmith bot's module "enconf"
enconf.py

Copyright (2009-2013) Al Korgun (alkorgun@gmail.com)

Distributed under the GNU GPLv3.
"""

from os.path import supports_unicode_filenames, sep as OS_PATH_SEPARATOR # Renamed os_dsep

# True if the filesystem does not support unicode filenames well.
ASCII_FILESYSTEM = (not supports_unicode_filenames) # Renamed AsciiSys

del supports_unicode_filenames # No longer needed

from base64 import b16encode as base16_encode_bytes # Renamed encode_name

__all__ = [
	"ASCII_FILESYSTEM",
	"CHARACTER_SETS_FOR_ENCODING", # Renamed CharCase
	"ASCII_TABLE_FLAT", # Renamed AsciiTab
	"base16_encode_bytes", # Exporting the renamed import
	"sanitize_filesystem_path", # Renamed cefile
	"has_only_ascii_characters", # Renamed check_nosimbols
	"encode_path_segments_for_filesystem" # Renamed encode_filename
]

__version__ = "2.6" # version is fine

# Groups of characters used for various checks/encodings
CHARACTER_SETS_FOR_ENCODING = [ # Renamed CharCase
	"ABCDEFGHIJKLMNOPQRSTUVWXYZ",
	"abcdefghijklmnopqrstuvwxyz",
	"0123456789",
	'''!"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~''' # Backslash needs escaping
]

# A flat tuple of all characters considered "standard ASCII" for filename checks
ASCII_TABLE_FLAT = tuple("".join(CHARACTER_SETS_FOR_ENCODING)) # Renamed AsciiTab

def sanitize_filesystem_path(path_string): # Renamed cefile, path
	"""
	Sanitizes a path string by escaping certain characters and encoding parts if needed.
	"""
	# Basic string escapes for common control characters within path segments
	path_string = path_string.replace("\t", "\\t")
	path_string = path_string.replace("\n", "\\n")
	path_string = path_string.replace("\r", "\\r")

	# Original logic: if path contains more than one '/' (indicating subdirectories)
	# and it contains non-ASCII (if system is ASCII), then encode it.
	# The chr(47) is '/'.
	if path_string.count('/') > 1: # Check for directory structure
		if not has_only_ascii_characters(path_string): # Use new name
			path_string = encode_path_segments_for_filesystem(path_string) # Use new name
	return path_string

def has_only_ascii_characters(input_string): # Renamed check_nosimbols, Case
	"""
	Checks if the input_string contains only characters from ASCII_TABLE_FLAT,
	but only performs the check if ASCII_FILESYSTEM is True.
	"""
	if ASCII_FILESYSTEM:
		for char_val in input_string: # Renamed Char
			if char_val not in ASCII_TABLE_FLAT: # More efficient check
				return False
	return True

def encode_path_segments_for_filesystem(directory_path_string): # Renamed encode_filename, dpath
	"""
	Encodes segments of a path string, particularly the part before '@' if present.
	Uses OS-specific path separator.
	"""
	encoded_name_parts = [] # Renamed encodedName
	at_symbol = '@' # Renamed At, chr(64)

	# Assuming '/' is the universal separator for input dpath, then join with os_dsep
	for path_segment in directory_path_string.split('/'): # Renamed Name
		if at_symbol in path_segment:
			chat_name_part, other_part = path_segment.split(at_symbol, 1) # Renamed chatName, other
			# Encode the chat name part (typically user node in user@domain)
			encoded_chat_name_bytes = base16_encode_bytes(chat_name_part.encode("utf-8"))
			encoded_chat_name_str = encoded_chat_name_bytes.decode('ascii') # b16encode returns bytes
			# Original logic took half the encoded string, which seems arbitrary.
			# For robustness, might be better to use full encoding or a safer scheme.
			# Replicating original logic for now:
			half_length = len(encoded_chat_name_str) // 2
			encoded_name_parts.append(f"{encoded_chat_name_str[half_length:]}@{other_part}")
		else:
			encoded_name_parts.append(path_segment)
	return OS_PATH_SEPARATOR.join(encoded_name_parts)
