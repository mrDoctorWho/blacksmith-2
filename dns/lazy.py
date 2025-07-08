# $Id: lazy.py,v 1.5.2.4 2011/03/19 22:15:01 customdesigned Exp $
#
# This file is part of the pydns project.
# Homepage: http://pydns.sourceforge.net
#
# This code is covered by the standard Python License. See LICENSE for details.
#

# routines for lazy people.
from . import Base # dns.Base will be used, so its members need to be qualified.
# Type and other constants are usually imported from their respective modules directly if needed.

from .Base import DNSError # DNSError is an exception, name is fine.

def reverse_lookup_single(ip_address_string): # Renamed revlookup, name
    """
    Convenience routine for doing a reverse lookup of an address.
    Returns the first (often shortest) PTR record found, or None.
    """
    ptr_records = reverse_lookup_all(ip_address_string) # Use new name
    if not ptr_records:
        return None
    return ptr_records[0]

def reverse_lookup_all(ip_address_string): # Renamed revlookupall, name
    """
    Convenience routine for doing a reverse lookup of an address.
    Returns a sorted list of all PTR records found.
    """
    # FIXME: check for IPv6 (original comment)
    address_parts = ip_address_string.split('.') # Renamed a
    address_parts.reverse()
    reversed_domain_string = '.'.join(address_parts) + '.in-addr.arpa' # Renamed b
    # Type.PTR would be better if Type was imported and refactored to RECORD_TYPE_PTR
    return sorted(dns_lookup(reversed_domain_string, qtype='ptr'), key=str.__len__) # Use new name

def dns_lookup(query_name, query_type_str): # Renamed dnslookup, name, qtype
    """
    Convenience routine to return just answer data for any query type.
    """
    # Uses renamed globals from Base.py
    if not Base.DEFAULT_DNS_SETTINGS['server']: # Check if server list is empty
        Base.discover_name_servers()

    # Uses renamed DnsQuery from Base.py
    dns_query_obj = Base.DnsQuery(name=query_name, qtype=query_type_str) # Renamed result
    query_result = dns_query_obj.send_request() # Renamed req

    if query_result.header['status'] != 'NOERROR': # NOERROR should ideally be a constant like Status.STATUS_NO_ERROR
        raise DNSError("dns query status: %s" % query_result.header['status'])
    # Original logic to retry with next server if server_rotate is on and no answers
    elif not query_result.answers and Base.DEFAULT_DNS_SETTINGS.get('server_rotate'):
        # This retry logic might be problematic if the server list is exhausted or if the first server gave a valid empty answer.
        # For now, preserving original behavior.
        dns_query_obj_retry = Base.DnsQuery(name=query_name, qtype=query_type_str)
        query_result = dns_query_obj_retry.send_request()

    if query_result.header['status'] != 'NOERROR':
        raise DNSError("dns query status: %s" % query_result.header['status'])
    return [answer_data_dict['data'] for answer_data_dict in query_result.answers] # Renamed x

def mx_lookup(domain_name_str): # Renamed mxlookup, name
    """
    Convenience routine for doing an MX lookup of a name. returns a
    sorted list of (preference, mail exchanger) records.
    """
    # Type.MX would be better
    return sorted(dns_lookup(domain_name_str, qtype='mx')) # Use new name

#
# $Log: lazy.py,v $
# Revision 1.5.2.4  2011/03/19 22:15:01  customdesigned
# Added rotation of name servers - SF Patch ID: 2795929
#
# Revision 1.5.2.3  2011/03/16 20:06:24  customdesigned
# Expand convenience methods.
#
# Revision 1.5.2.2  2011/03/08 21:06:42  customdesigned
# Address sourceforge patch requests 2981978, 2795932 to add revlookupall
# and raise DNSError instead of IndexError on server fail.
#
# Revision 1.5.2.1  2007/05/22 20:23:38  customdesigned
# Lazy call to DiscoverNameServers.
#
# Revision 1.5  2002/05/06 06:14:38  anthonybaxter
# reformat, move import to top of file.
#
# Revision 1.4  2002/03/19 12:41:33  anthonybaxter
# tabnannied and reindented everything. 4 space indent, no tabs.
# yay.
#
# Revision 1.3  2001/08/09 09:08:55  anthonybaxter
# added identifying header to top of each file.
#
# Revision 1.2  2001/07/19 06:57:07  anthony
# cvs keywords added.
#
#
