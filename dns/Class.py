"""
$Id: Class.py,v 1.6.2.1 2011/03/16 20:06:39  customdesigned Exp $

This file is part of the pydns project.
Homepage: http://pydns.sourceforge.net

This code is covered by the standard Python License. See LICENSE for details.

CLASS values (section 3.2.4).
"""

CLASS_IN = 1 # the Internet
CLASS_CS = 2 # the CSNET class (Obsolete - used only for examples in
                # some obsolete RFCs)
CLASS_CH = 3 # the CHAOS class. When someone shows me python running on
                # a Symbolics Lisp machine, I'll look at implementing this.
CLASS_HS = 4 # Hesiod [Dyer 87]

# QCLASS values (section 3.2.5) - Query Class
QUERY_CLASS_ANY = 255 # any class

# Construct reverse mapping dictionary
__all__ = [
    'CLASS_IN', 'CLASS_CS', 'CLASS_CH', 'CLASS_HS', 'QUERY_CLASS_ANY'
]

CLASS_CODE_MAP = {} # Renamed classmap
for name_val in __all__:
    # Ensure we only map actual type constants by checking prefix
    if name_val.startswith("CLASS_") or name_val.startswith("QUERY_CLASS_"):
        CLASS_CODE_MAP[globals()[name_val]] = name_val

def get_class_string(class_code_val): # Renamed classstr and klass
    if class_code_val in CLASS_CODE_MAP:
        return CLASS_CODE_MAP[class_code_val]
    return repr(class_code_val)

#
# $Log: Class.py,v $
# Revision 1.6.2.1  2011/03/16 20:06:39  customdesigned
# Refer to explicit LICENSE file.
#
# Revision 1.6  2002/04/23 12:52:19  anthonybaxter
# cleanup whitespace.
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
