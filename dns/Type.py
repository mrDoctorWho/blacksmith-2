# -*- encoding: utf-8 -*-
"""
$Id: Type.py,v 1.6.2.3 2011/03/16 20:06:39 customdesigned Exp $

This file is part of the pydns project.
Homepage: http://pydns.sourceforge.net

This code is covered by the standard Python License. See LICENSE for details.

TYPE values (section 3.2.2).
"""

RECORD_TYPE_A = 1           # a host address
RECORD_TYPE_NS = 2          # an authoritative name server
RECORD_TYPE_MD = 3          # a mail destination (Obsolete - use MX)
RECORD_TYPE_MF = 4          # a mail forwarder (Obsolete - use MX)
RECORD_TYPE_CNAME = 5       # the canonical name for an alias
RECORD_TYPE_SOA = 6         # marks the start of a zone of authority
RECORD_TYPE_MB = 7          # a mailbox domain name (EXPERIMENTAL)
RECORD_TYPE_MG = 8          # a mail group member (EXPERIMENTAL)
RECORD_TYPE_MR = 9          # a mail rename domain name (EXPERIMENTAL)
RECORD_TYPE_NULL = 10       # a null RR (EXPERIMENTAL)
RECORD_TYPE_WKS = 11        # a well known service description
RECORD_TYPE_PTR = 12        # a domain name pointer
RECORD_TYPE_HINFO = 13      # host information
RECORD_TYPE_MINFO = 14      # mailbox or mail list information
RECORD_TYPE_MX = 15         # mail exchange
RECORD_TYPE_TXT = 16        # text strings
RECORD_TYPE_AAAA = 28       # IPv6 AAAA records (RFC 1886)
RECORD_TYPE_SRV = 33        # dns RR for specifying the location of services (RFC 2782)
RECORD_TYPE_SPF = 99        # TXT RR for Sender Policy Framework

# Additional TYPE values from host.c source
# These seem less standard, will prefix them as well for consistency for now.
RECORD_TYPE_UNAME = 110
RECORD_TYPE_MP = 240

# QTYPE values (section 3.2.3) - Query Types
QUERY_TYPE_AXFR = 252      # A request for a transfer of an entire zone
QUERY_TYPE_MAILB = 253     # A request for mailbox-related records (MB, MG or MR)
QUERY_TYPE_MAILA = 254     # A request for mail agent RRs (Obsolete - see MX)
QUERY_TYPE_ANY = 255       # A request for all records

# Construct reverse mapping dictionary
__all__ = [
    'RECORD_TYPE_A', 'RECORD_TYPE_NS', 'RECORD_TYPE_MD', 'RECORD_TYPE_MF',
    'RECORD_TYPE_CNAME', 'RECORD_TYPE_SOA', 'RECORD_TYPE_MB', 'RECORD_TYPE_MG',
    'RECORD_TYPE_MR', 'RECORD_TYPE_NULL', 'RECORD_TYPE_WKS', 'RECORD_TYPE_PTR',
    'RECORD_TYPE_HINFO', 'RECORD_TYPE_MINFO', 'RECORD_TYPE_MX', 'RECORD_TYPE_TXT',
    'RECORD_TYPE_AAAA', 'RECORD_TYPE_SRV', 'RECORD_TYPE_SPF',
    'RECORD_TYPE_UNAME', 'RECORD_TYPE_MP',
    'QUERY_TYPE_AXFR', 'QUERY_TYPE_MAILB', 'QUERY_TYPE_MAILA', 'QUERY_TYPE_ANY'
]

RECORD_TYPE_MAP = {} # Renamed typemap
for name_val in __all__:
    # Ensure we only map actual type constants by checking prefix
    if name_val.startswith("RECORD_TYPE_") or name_val.startswith("QUERY_TYPE_"):
        RECORD_TYPE_MAP[globals()[name_val]] = name_val

def get_type_string(type_code): # Renamed typestr and type
    if type_code in RECORD_TYPE_MAP:
        return RECORD_TYPE_MAP[type_code]
    return repr(type_code)

#
# $Log: Type.py,v $
# Revision 1.6.2.3  2011/03/16 20:06:39  customdesigned
# Refer to explicit LICENSE file.
#
# Revision 1.6.2.2  2009/06/09 18:39:06  customdesigned
# Built-in SPF support.
#
# Revision 1.6.2.1  2007/05/22 20:20:39  customdesigned
# Mark utf-8 encoding.
#
# Revision 1.6  2002/03/19 12:41:33  anthonybaxter
# tabnannied and reindented everything. 4 space indent, no tabs.
# yay.
#
# Revision 1.5  2002/03/19 12:26:13  anthonybaxter
# death to leading tabs.
#
# Revision 1.4  2001/08/09 09:08:55  anthonybaxter
# added identifying header to top of each file.
#
# Revision 1.3  2001/07/19 07:38:28  anthony
# added type code for SRV. From Michael Strcder.
#
# Revision 1.2  2001/07/19 06:57:07  anthony
# cvs keywords added.
#
#
