"""
$Id: Status.py,v 1.7.2.1 2011/03/16 20:06:39 customdesigned Exp $

This file is part of the pydns project.
Homepage: http://pydns.sourceforge.net

This code is covered by the standard Python License. See LICENSE for details.

Status values in message header
"""

STATUS_NO_ERROR = 0 #   No Error                           [RFC 1035]
STATUS_FORMAT_ERROR = 1 #   Format Error                       [RFC 1035]
STATUS_SERVER_FAILURE = 2 #   Server Failure                     [RFC 1035]
STATUS_NX_DOMAIN = 3 #   Non-Existent Domain                [RFC 1035]
STATUS_NOT_IMPLEMENTED = 4 #   Not Implemented                    [RFC 1035]
STATUS_REFUSED = 5 #   Query Refused                      [RFC 1035]
STATUS_YX_DOMAIN = 6 #   Name Exists when it should not     [RFC 2136]
STATUS_YX_RRSET = 7 #   RR Set Exists when it should not   [RFC 2136]
STATUS_NX_RRSET = 8 #   RR Set that should exist does not  [RFC 2136]
STATUS_NOT_AUTHORITATIVE = 9 #   Server Not Authoritative for zone  [RFC 2136]
STATUS_NOT_ZONE = 10 #  Name not contained in zone         [RFC 2136]
STATUS_BAD_OPT_VERSION = 16 #  Bad OPT Version                    [RFC 2671]
STATUS_BAD_SIGNATURE = 16 #  TSIG Signature Failure             [RFC 2845] # Note: Duplicate value
STATUS_BAD_KEY = 17 #  Key not recognized                 [RFC 2845]
STATUS_BAD_TIME = 18 #  Signature out of time window       [RFC 2845]
STATUS_BAD_MODE = 19 #  Bad TKEY Mode                      [RFC 2930]
STATUS_BAD_NAME = 20 #  Duplicate key name                 [RFC 2930]
STATUS_BAD_ALGORITHM = 21 #  Algorithm not supported            [RFC 2930]

# Construct reverse mapping dictionary
__all__ = [
    'STATUS_NO_ERROR', 'STATUS_FORMAT_ERROR', 'STATUS_SERVER_FAILURE',
    'STATUS_NX_DOMAIN', 'STATUS_NOT_IMPLEMENTED', 'STATUS_REFUSED',
    'STATUS_YX_DOMAIN', 'STATUS_YX_RRSET', 'STATUS_NX_RRSET',
    'STATUS_NOT_AUTHORITATIVE', 'STATUS_NOT_ZONE', 'STATUS_BAD_OPT_VERSION',
    'STATUS_BAD_SIGNATURE', 'STATUS_BAD_KEY', 'STATUS_BAD_TIME',
    'STATUS_BAD_MODE', 'STATUS_BAD_NAME', 'STATUS_BAD_ALGORITHM'
]

STATUS_CODE_MAP = {}
# Populate carefully due to duplicate numeric values (BADVERS and BADSIG are both 16)
# The last one defined for a given number will be what repr(number) maps to.
# For a more robust mapping from number to a single canonical string, this might need adjustment.
for name_val in __all__:
    if name_val.startswith("STATUS_"):
        STATUS_CODE_MAP[globals()[name_val]] = name_val

def get_status_string(status_code_val): # Renamed statusstr and status
    if status_code_val in STATUS_CODE_MAP:
        return STATUS_CODE_MAP[status_code_val]
    return repr(status_code_val)

#
# $Log: Status.py,v $
# Revision 1.7.2.1  2011/03/16 20:06:39  customdesigned
# Refer to explicit LICENSE file.
#
# Revision 1.7  2002/04/23 12:52:19  anthonybaxter
# cleanup whitespace.
#
# Revision 1.6  2002/04/23 10:57:57  anthonybaxter
# update to complete the list of response codes.
#
# Revision 1.5  2002/03/19 12:41:33  anthonybaxter
# tabnannied and reindented everything. 4 space indent, no tabs.
# yay.
#
# Revision 1.4  2002/03/19 12:26:13  anthonybaxter
# death to leading tabs.
#
# Revision 1.3  2001/08/09 09:08:55  anthonybaxter
# added identifying header to top of each file
#
# Revision 1.2  2001/07/19 06:57:07  anthony
# cvs keywords added
#
#
