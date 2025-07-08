"""
$Id: Base.py,v 1.12.2.15~ 2013/12/05 00:00:00 alkorgun Exp $

This file is part of the pydns project.
Homepage: http://pydns.sourceforge.net

This code is covered by the standard Python License.  See LICENSE for details.

    Base functionality. Request and Response classes, that sort of thing.
"""

import asyncore
import os
import select
import socket
import time
from . import Type
from . import Class
from . import Opcode
#
# This random generator is used for transaction ids and port selection.  This
# is important to prevent spurious results from lost packets, and malicious
# cache poisoning.  This doesn't matter if you are behind a caching nameserver
# or your app is a primary dns server only. To install your own generator,
# replace dns.Base.random.  SystemRandom uses /dev/urandom or similar source.
#
try:
    from random import SystemRandom
    RANDOM_GENERATOR = SystemRandom()
except:
    import random as RANDOM_GENERATOR

class DNSError(Exception):
    pass

# Lib uses DNSError, so import after defining.
from . import Lib

DEFAULT_DNS_SETTINGS = {
    'protocol': 'udp',
    'port': 53,
    'qtype': Type.A, # Will be RECORD_TYPE_A after Type.py is refactored
    'opcode': Opcode.OPCODE_QUERY, # Will be Opcode.OPCODE_QUERY after Opcode.py is refactored
    'rd': 1,
    'timing': 1,
    'timeout': 30,
    'server_rotate': 0
}

DEFAULT_DNS_SETTINGS['server'] = []

def parse_resolv_conf(resolve_file_path="/etc/resolv.conf"): # Renamed
    """
    Parses the /etc/resolv.conf file and sets defaults for name servers.
    """
    if os.path.isfile(resolve_file_path):
        with open(resolve_file_path) as f_lines: # Use with statement
            lines_read = f_lines.readlines()
        for line_content in lines_read: # Renamed line
            line_content = line_content.strip()
            if not line_content or line_content[0] == ';' or line_content[0] == '#':
                continue
            fields_in_line = line_content.split() # Renamed fields
            if len(fields_in_line) < 2:
                continue
            if fields_in_line[0] == 'domain' and len(fields_in_line) > 1:
                DEFAULT_DNS_SETTINGS['domain'] = fields_in_line[1]
            if fields_in_line[0] == 'search':
                pass
            if fields_in_line[0] == 'options':
                pass
            if fields_in_line[0] == 'sortlist':
                pass
            if fields_in_line[0] == 'nameserver':
                DEFAULT_DNS_SETTINGS['server'].append(fields_in_line[1])

def discover_name_servers(): # Renamed
    import sys
    if sys.platform in ('win32', 'nt'):
        from . import win32dns # This module might need similar refactoring
        DEFAULT_DNS_SETTINGS['server'] = win32dns.RegistryResolve()
    else:
        return parse_resolv_conf()

class DnsQuery(object): # Renamed DnsRequest
    """
    High level DNS Query object.
    """
    def __init__(self, *name_tuple, **args_dict): # Renamed name, args
        self.completion_callback = None # Renamed donefunc
        self.is_async = None # Renamed async
        self.query_specific_defaults = {} # Renamed defaults
        self._parse_args(name_tuple, args_dict)
        self.query_specific_defaults = self.args
        self.transaction_id = 0 # Renamed tid

    def _parse_args(self, name_tuple, args_dict): # Renamed argparse
        if not name_tuple and 'name' in self.query_specific_defaults:
            args_dict['name'] = self.query_specific_defaults['name']

        # Original code had 'if isinstance(name, str):', but name is name_tuple here.
        # This logic seems to handle if a single string name is passed directly to __init__ or send_request
        if name_tuple and len(name_tuple) == 1 and name_tuple[0] and isinstance(name_tuple[0], str) :
             args_dict['name'] = name_tuple[0]
        elif name_tuple and len(name_tuple) == 1 and name_tuple[0]:
            args_dict['name'] = name_tuple[0]

        if DEFAULT_DNS_SETTINGS['server_rotate'] and isinstance(DEFAULT_DNS_SETTINGS['server'], list) and DEFAULT_DNS_SETTINGS['server']:
            DEFAULT_DNS_SETTINGS['server'] = (DEFAULT_DNS_SETTINGS['server'][1:] + DEFAULT_DNS_SETTINGS['server'][:1])

        for key, value in DEFAULT_DNS_SETTINGS.items():
            if key not in args_dict:
                if key in self.query_specific_defaults:
                    args_dict[key] = self.query_specific_defaults[key]
                else:
                    args_dict[key] = value
        if isinstance(args_dict['server'], str):
            args_dict['server'] = [args_dict['server']]
        self.args = args_dict

    def _initialize_socket(self, address_family, socket_type): # Renamed socketInit, a, b
        self.socket_obj = socket.socket(address_family, socket_type) # Renamed s

    def _process_udp_reply(self): # Renamed processUDPReply
        if self.timeout > 0:
            readable_sockets, _, _ = select.select([self.socket_obj], [], [], self.timeout) # Renamed r, w, e
            if not readable_sockets:
                raise DNSError('Timeout')
        (self.reply_data, self.reply_from_address) = self.socket_obj.recvfrom(65535) # Renamed reply, from_address
        self.time_finish_request = time.time() # Renamed time_finish
        self.args['server'] = self.current_nameserver_ip # Renamed ns
        return self._process_reply_common() # Renamed processReply

    def _read_all_tcp_data(self, file_obj, count_to_read): # Renamed _readall, f, count
      data_read = file_obj.read(count_to_read) # Renamed res
      while len(data_read) < count_to_read:
        if self.timeout > 0:
            remaining_timeout = self.time_start_request + self.timeout - time.time() # Renamed rem, time_start
            if remaining_timeout <= 0:
              raise DNSError('Timeout')
            self.socket_obj.settimeout(remaining_timeout) # Renamed s
        buffer_chunk = file_obj.read(count_to_read - len(data_read)) # Renamed buf
        if not buffer_chunk:
          raise DNSError('incomplete reply - %d of %d read' % (len(data_read), count_to_read))
        data_read += buffer_chunk
      return data_read

    def _process_tcp_reply(self): # Renamed processTCPReply
        if self.timeout > 0:
            self.socket_obj.settimeout(self.timeout) # Renamed s
        else:
            self.socket_obj.settimeout(None)

        # Ensure 'b' for binary mode with makefile in Python 3
        # And ensure it's closed properly
        with self.socket_obj.makefile('rb') as file_obj: # Renamed f
            header_data = self._read_all_tcp_data(file_obj, 2) # Renamed header
            data_length = Lib.unpack16bit(header_data) # Renamed count
            self.reply_data = self._read_all_tcp_data(file_obj, data_length) # Renamed reply

        self.time_finish_request = time.time() # Renamed time_finish
        self.args['server'] = self.current_nameserver_ip # Renamed ns
        return self._process_reply_common() # Renamed processReply

    def _process_reply_common(self): # Renamed processReply
        self.args['elapsed'] = (self.time_finish_request - self.time_start_request) * 1000 # Renamed time_finish, time_start
        unpacker_obj = Lib.Munpacker(self.reply_data) # Renamed u, reply_data
        # DnsResult will be DnsQueryResult after Lib.py is refactored
        dns_result_obj = Lib.DnsResult(unpacker_obj, self.args) # Renamed r
        dns_result_obj.args = self.args
        return dns_result_obj

    def _bind_random_source_port(self): # Renamed getSource
        """
        Pick random source port to avoid dns cache poisoning attack.
        """
        while True:
            try:
                source_port = RANDOM_GENERATOR.randint(1024, 65535)
                self.socket_obj.bind(('', source_port)) # Renamed s
                break
            except socket.error as e:
                if e.errno != 98: # Check e.errno for 'Address already in use'
                    raise

    def _connect_to_nameserver(self): # Renamed conn
        self._bind_random_source_port()
        self.socket_obj.connect((self.current_nameserver_ip, self.port)) # Renamed s, ns

    def send_request(self, *name_tuple, **args_dict): # Renamed req, name, args
        """
        Sends the DNS query.
        """
        self._parse_args(name_tuple, args_dict)

        protocol_str = self.args['protocol'] # Renamed protocol
        self.port = self.args['port']
        self.transaction_id = RANDOM_GENERATOR.randint(0, 65535)
        self.timeout = self.args['timeout']
        opcode_val = self.args['opcode']
        recursion_desired_flag = self.args['rd']
        name_servers_list = self.args['server']

        query_type_arg = self.args['qtype']
        if isinstance(query_type_arg, str):
            try:
                query_type_val = getattr(Type, query_type_arg.upper())
            except AttributeError:
                raise DNSError('unknown query type')
        else:
            query_type_val = query_type_arg

        if 'name' not in self.args:
            print_colored(str(self.args), COLOR_RED)
            raise DNSError('nothing to lookup')
        query_name_str = self.args['name']

        if query_type_val == Type.AXFR:
            print_colored('Query type AXFR, protocol forced to TCP', COLOR_YELLOW)
            protocol_str = 'tcp'

        packer_obj = Lib.Mpacker()
        packer_obj.addHeader(self.transaction_id,
            0, opcode_val, 0, 0, recursion_desired_flag, 0, 0, 0,
            1, 0, 0, 0)
        packer_obj.addQuestion(query_name_str, query_type_val, Class.CLASS_IN) # Class will be CLASS_IN
        self.request_data = packer_obj.getbuf()
        try:
            if protocol_str == 'udp':
                self._send_udp_request(name_servers_list)
            else:
                self._send_tcp_request(name_servers_list)
        except socket.error as e:
            raise DNSError(e)

        if self.is_async: # Use new name
            query_answer = None
        elif not self.response:
            raise DNSError("no working nameservers found")
        else:
            query_answer = self.response
        return query_answer

    def _send_udp_request(self, name_servers_list): # Renamed sendUDPRequest, server
        """
        Sends a UDP request.
        """
        self.response = None
        for nameserver_ip_str in name_servers_list: # Renamed ns
            try:
                if ':' in nameserver_ip_str:
                    if hasattr(socket, 'has_ipv6') and socket.has_ipv6:
                        self._initialize_socket(socket.AF_INET6, socket.SOCK_DGRAM)
                    else:
                        continue
                else:
                    self._initialize_socket(socket.AF_INET, socket.SOCK_DGRAM)

                self.current_nameserver_ip = nameserver_ip_str # Renamed ns

                try:
                    self.time_start_request = time.time() # Renamed time_start
                    self._connect_to_nameserver()
                    if not self.is_async: # Use new name
                        self.socket_obj.send(self.request_data) # Renamed s
                        dns_result = self._process_udp_reply() # Renamed r
                        while dns_result.header['id'] != self.transaction_id or self.reply_from_address[1] != self.port:
                            dns_result = self._process_udp_reply()
                        self.response = dns_result
                finally:
                    if not self.is_async: # Use new name
                        self.socket_obj.close() # Renamed s
            except socket.error:
                continue
            break

    def _send_tcp_request(self, name_servers_list): # Renamed sendTCPRequest, server
        """
        Sends a TCP request.
        """
        self.response = None
        for nameserver_ip_str in name_servers_list: # Renamed ns
            try:
                if ':' in nameserver_ip_str:
                    if hasattr(socket, 'has_ipv6') and socket.has_ipv6:
                        self._initialize_socket(socket.AF_INET6, socket.SOCK_STREAM)
                    else:
                        continue
                else:
                    self._initialize_socket(socket.AF_INET, socket.SOCK_STREAM)

                self.current_nameserver_ip = nameserver_ip_str # Renamed ns

                try:
                    self.time_start_request = time.time() # Renamed time_start
                    self._connect_to_nameserver()
                    request_buffer_tcp = Lib.pack16bit(len(self.request_data)) + self.request_data

                    self.socket_obj.setblocking(0) # Renamed s
                    try:
                        self.socket_obj.sendall(request_buffer_tcp) # Renamed s
                    except socket.error as e:
                        if e.errno != socket.errno.EWOULDBLOCK:
                            raise
                        print_colored("Warning: sendall would block, request might be incomplete (TCP)", COLOR_YELLOW)

                    self.socket_obj.setblocking(1) # Renamed s

                    dns_result = self._process_tcp_reply() # Renamed r
                    if dns_result.header['id'] == self.transaction_id:
                        self.response = dns_result
                        break
                finally:
                    self.socket_obj.close() # Renamed s
            except socket.error:
                continue

class AsyncDnsQuery(DnsQuery, asyncore.dispatcher_with_send): # Renamed DnsAsyncRequest, DnsQuery
    """
    An asynchronous request object. out of date, probably broken.
    """
    def __init__(self, *name_tuple, **args_dict): # Renamed name, args
        DnsQuery.__init__(self, *name_tuple, **args_dict)

        if 'done' in args_dict and args_dict['done']:
            self.completion_callback = args_dict['done'] # Renamed donefunc
        else:
            self.completion_callback = self._show_result # Renamed showResult

        self.is_async = 1 # Renamed async

    def _connect_to_nameserver(self): # Override for async
        self._bind_random_source_port()
        self.connect((self.current_nameserver_ip, self.port)) # Renamed ns, asyncore's connect
        self.time_start_request = time.time() # Renamed time_start
        if 'start' in self.args and self.args['start']:
            asyncore.dispatcher.go(self)

    def _initialize_socket(self, address_family, socket_type): # Renamed socketInit
        self.create_socket(address_family, socket_type) # asyncore method
        asyncore.dispatcher.__init__(self)
        # self.s (now self.socket_obj) is set by create_socket via asyncore.dispatcher

    def handle_read(self):
        if self.args['protocol'] == 'udp':
            self.response = self._process_udp_reply()
            if self.completion_callback: # Use new name
                self.completion_callback(*(self,))

    def handle_connect(self): # Called by asyncore after connect()
        self.send(self.request_data)

    def handle_write(self):
        pass

    def _show_result(self, *ignored_args): # Renamed showResult, s
        if self.response:
            self.response.show()
        else:
            print_colored("Async query completed, but no response available to show.", COLOR_YELLOW)
