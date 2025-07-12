"""
$Id: win32dns.py,v 1.3.2.1 2007/05/22 20:26:49 customdesigned Exp $

Extract a list of TCP/IP name servers from the registry 0.1
    0.1 Strobl 2001-07-19
Usage:
    RegistryResolve() returns a list of ip numbers (dotted quads), by
    scouring the registry for addresses of name servers.

Tested on Windows NT4 Server SP6a, Windows 2000 Pro SP2 and
Whistler Pro (XP) Build 2462 and Windows ME
... all having a different registry layout wrt name servers :-/

Todo:

  Program doesn't check whether an interface is up or down.

(c) 2001 Copyright by Wolfgang Strobl ws@mystrobl.de,
        License analog to the current Python license.
"""

import re
import winreg

def binary_ip_to_list_of_strings(binary_ip_data): # Renamed binipdisplay, s
    """
    Convert a binary array of ip adresses to a python list of strings.
    """
    if len(binary_ip_data) % 4: # Each IPv4 address is 4 bytes
        raise EnvironmentError("Binary IP data length is not a multiple of 4")

    ip_address_list = [] # Renamed ol
    for i in range(len(binary_ip_data) // 4): # Use integer division
        start_index = i * 4
        single_ip_bytes = binary_ip_data[start_index : start_index + 4] # Renamed s1

        byte_string_parts = [] # Renamed ip
        for byte_val in single_ip_bytes: # Renamed j
            byte_string_parts.append(str(byte_val)) # ord() is not needed for bytes iteration in Py3
        ip_address_list.append('.'.join(byte_string_parts))
    return ip_address_list

def ip_string_to_list(ip_addresses_string): # Renamed stringdisplay, s
    '''
    Convert "d.d.d.d,d.d.d.d" or "d.d.d.d d.d.d.d" to ["d.d.d.d","d.d.d.d"].
    '''
    # Using re.split to handle both space and comma as delimiters
    return [ip_str for ip_str in re.split(r"[ ,]+", ip_addresses_string) if ip_str]

def get_windows_nameservers_from_registry(): # Renamed RegistryResolve
    name_servers_list = [] # Renamed nameservers
    registry_connection = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE) # Renamed x

    try:
        # Path for NT/2000/XP
        tcpip_parameters_key = winreg.OpenKey(registry_connection,
                                           r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters") # Renamed y
    except EnvironmentError:
        # Windows ME, perhaps?
        try:
            mcp_key = winreg.OpenKey(registry_connection, r"SYSTEM\CurrentControlSet\Services\VxD\MSTCP") # Renamed y
            name_server_string, _ = winreg.QueryValueEx(mcp_key, 'NameServer') # Renamed nameserver, dummytype
            if name_server_string and not any(ns in name_server_string for ns in name_servers_list): # More robust check
                name_servers_list.extend(ip_string_to_list(name_server_string))
            winreg.CloseKey(mcp_key)
        except EnvironmentError:
            pass # Could not open MSTCP key either
        winreg.CloseKey(registry_connection) # Close outer connection
        return name_servers_list

    try:
        # Try DHCP configured NameServer first
        dhcp_name_server_string, _ = winreg.QueryValueEx(tcpip_parameters_key, "DhcpNameServer") # Renamed nameserver
        if dhcp_name_server_string: # If not empty
             name_servers_list.extend(ip_string_to_list(dhcp_name_server_string))
    except EnvironmentError: # DhcpNameServer not found, try static NameServer
        try:
            name_server_string, _ = winreg.QueryValueEx(tcpip_parameters_key, "NameServer") # Renamed nameserver
            if name_server_string: # If not empty
                name_servers_list.extend(ip_string_to_list(name_server_string))
        except EnvironmentError:
            pass # Static NameServer also not found

    winreg.CloseKey(tcpip_parameters_key)

    # For Win2k: iterate over DNSRegisteredAdapters
    try:
        dns_adapters_key = winreg.OpenKey(registry_connection, r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\DNSRegisteredAdapters") # Renamed y
        for i in range(1000): # Max 1000 adapters, arbitrary limit from original
            try:
                adapter_subkey_name = winreg.EnumKey(dns_adapters_key, i) # Renamed n
                adapter_key = winreg.OpenKey(dns_adapters_key, adapter_subkey_name) # Renamed z
                try:
                    # Original code had dnscount, dnscounttype - these seem unused if DNSServerAddresses is read directly.
                    # Assuming DNSServerAddresses is the binary data.
                    dns_server_addresses_binary, _ = winreg.QueryValueEx(adapter_key, 'DNSServerAddresses') # Renamed dnsvalues, dnsvaluestype
                    name_servers_list.extend(binary_ip_to_list_of_strings(dns_server_addresses_binary)) # Use new name
                except EnvironmentError:
                    pass # DNSServerAddresses not found for this adapter
                finally:
                    winreg.CloseKey(adapter_key)
            except EnvironmentError: # No more adapter subkeys
                break
        winreg.CloseKey(dns_adapters_key)
    except EnvironmentError:
        pass # DNSRegisteredAdapters key not found

    # For Whistler (XP) and later: iterate over Interfaces
    try:
        interfaces_key = winreg.OpenKey(registry_connection, r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces") # Renamed y
        for i in range(1000): # Max 1000 interfaces
            try:
                interface_subkey_name = winreg.EnumKey(interfaces_key, i) # Renamed n
                interface_key = winreg.OpenKey(interfaces_key, interface_subkey_name) # Renamed z
                try:
                    # Check both NameServer (static) and DhcpNameServer (dynamic) for each interface
                    for reg_value_name in ("NameServer", "DhcpNameServer"):
                        try:
                            name_server_string, _ = winreg.QueryValueEx(interface_key, reg_value_name) # Renamed nameserver, dummytype
                            if name_server_string: # If not empty or None
                                parsed_ips = ip_string_to_list(name_server_string)
                                for ip_addr in parsed_ips:
                                    if ip_addr and ip_addr not in name_servers_list: # Avoid duplicates
                                        name_servers_list.append(ip_addr)
                        except EnvironmentError:
                            pass # Value not found for this interface
                finally:
                    winreg.CloseKey(interface_key)
            except EnvironmentError: # No more interface subkeys
                break
        winreg.CloseKey(interfaces_key)
    except EnvironmentError:
        pass # Interfaces key not found

    winreg.CloseKey(registry_connection)

    # Remove empty strings and duplicates, preserving order as much as possible
    final_list = []
    for ip in name_servers_list:
        if ip and ip not in final_list:
            final_list.append(ip)
    return final_list

if __name__ == "__main__":
    print("Name servers:", get_windows_nameservers_from_registry()) # Use new name

#
# $Log: win32dns.py,v $
# Revision 1.3.2.1  2007/05/22 20:26:49  customdesigned
# Fix win32 nameserver discovery.
#
# Revision 1.3  2002/05/06 06:15:31  anthonybaxter
# apparently some versions of windows return servers as unicode
# string with space sep, rather than strings with comma sep.
# *sigh*
#
# Revision 1.2  2002/03/19 12:41:33  anthonybaxter
# tabnannied and reindented everything. 4 space indent, no tabs.
# yay.
#
# Revision 1.1  2001/08/09 09:22:28  anthonybaxter
# added what I hope is win32 resolver lookup support. I'll need to try
# and figure out how to get the CVS checkout onto my windows machine to
# make sure it works (wow, doing something other than games on the
# windows machine :)
#
# Code from Wolfgang.Strobl@gmd.de
# win32dns.py from
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66260
#
# Really, ParseResolvConf() should be renamed "FindNameServers" or
# some such.
#
#
