"""
$Id: Opcode.py,v 1.6.2.1 2011/03/16 20:06:39 customdesigned Exp $

This file is part of the pydns project.
Homepage: http://pydns.sourceforge.net

This code is covered by the standard Python License. See LICENSE for details.

Opcode values in message header. RFC 1035, 1996, 2136.
"""

OPCODE_QUERY = 0
OPCODE_IQUERY = 1
OPCODE_STATUS = 2
OPCODE_NOTIFY = 4
OPCODE_UPDATE = 5

# Construct reverse mapping dictionary
# Consider replacing dir() and eval() with a more explicit approach if possible,
# but for now, just renaming for PEP 8.
# _names variable is problematic as dir() on its own captures too much.
# Assuming it meant to capture the globals defined above.
__all__ = ['OPCODE_QUERY', 'OPCODE_IQUERY', 'OPCODE_STATUS', 'OPCODE_NOTIFY', 'OPCODE_UPDATE']

OPCODE_MAP = {}
for name_val in __all__: # Iterate over explicitly defined opcodes
    if name_val.startswith("OPCODE_"): # Ensure it's one of our constants
        OPCODE_MAP[globals()[name_val]] = name_val # Use globals() to get value

def get_opcode_string(opcode_val): # Renamed opcodestr and opcode
    if opcode_val in OPCODE_MAP:
        return OPCODE_MAP[opcode_val]
    return repr(opcode_val)

#
# $Log: Opcode.py,v $
# Revision 1.6.2.1  2011/03/16 20:06:39  customdesigned
# Refer to explicit LICENSE file.
#
# Revision 1.6  2002/04/23 10:51:43  anthonybaxter
# Added UPDATE, NOTIFY.
#
# Revision 1.5  2002/03/19 12:41:33  anthonybaxter
# tabnannied and reindented everything. 4 space indent, no tabs.
# yay.
#
# Revision 1.4  2002/03/19 12:26:13  anthonybaxter
# death to leading tabs.
#
# Revision 1.3  2001/08/09 09:08:55  anthonybaxter
# added identifying header to top of each file.
#
# Revision 1.2  2001/07/19 06:57:07  anthony
# cvs keywords added.
#
#
