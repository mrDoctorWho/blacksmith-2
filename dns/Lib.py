# -*- encoding: utf-8 -*-
"""
$Id: Lib.py,v 1.11.2.8 2011/03/16 20:06:39 customdesigned Exp $

This file is part of the pydns project.
Homepage: http://pydns.sourceforge.net

This code is covered by the standard Python License. See LICENSE for details.

Library code. Largely this is packers and unpackers for various types.
"""

from . import Type as RecordType # Renamed Type to RecordType for clarity with python type
from . import Class as DnsClass # Renamed Class to DnsClass
from . import Opcode
from . import Status
import dns # This might refer to the pydns package itself or a global dns module
import string # string.splitfields and string.joinfields are deprecated.

from .Base import DNSError # DNSError is an exception, name is fine.

# These globals are already PEP 8 compliant
LABEL_UTF8 = False
LABEL_ENCODING = 'idna'

class UnpackError(DNSError):
    pass

class PackError(DNSError):
    pass

# Low-level 16 and 32 bit integer packing and unpacking

from struct import pack as struct_pack
from struct import unpack as struct_unpack
from socket import inet_ntoa, inet_aton

def pack_16_bit_int(number_val): # Renamed pack16bit, n
    return struct_pack('!H', number_val)

def pack_32_bit_int(number_val): # Renamed pack32bit, n
    return struct_pack('!L', number_val)

def unpack_16_bit_int(byte_string): # Renamed unpack16bit, s
    return struct_unpack('!H', byte_string)[0]

def unpack_32_bit_int(byte_string): # Renamed unpack32bit, s
    return struct_unpack('!L', byte_string)[0]

def ipv4_address_to_binary(address_str): # Renamed addr2bin, addr
    # inet_aton expects a string, struct_unpack returns a tuple
    return struct_unpack('!I', inet_aton(address_str))[0] # Changed 'l' to 'I' for unsigned

def binary_to_ipv4_address(binary_int): # Renamed bin2addr, n
    # struct_pack expects an int, inet_ntoa expects bytes
    return inet_ntoa(struct_pack('!I', binary_int)) # Changed 'L' to 'I' for unsigned

# Packing class

class BasePacker: # Renamed Packer
    """
    Packer base class. supports basic byte/16bit/32bit/addr/string/name.
    """
    def __init__(self):
        self.buffer = b'' # Renamed buf, ensure it's bytes
        self.index = {}

    def get_buffer(self): # Renamed getbuf
        return self.buffer

    def add_byte(self, char_val): # Renamed addbyte, c
        if isinstance(char_val, str): # Ensure it's bytes
            char_val = char_val.encode('latin-1') # Or appropriate encoding if known
        if len(char_val) != 1:
            raise TypeError('one byte expected')
        self.buffer += char_val

    def add_bytes(self, byte_sequence): # Renamed addbytes, bytes
        self.buffer += byte_sequence

    def add_16_bit_int(self, number_val): # Renamed add16bit, n
        self.buffer += pack_16_bit_int(number_val)

    def add_32_bit_int(self, number_val): # Renamed add32bit, n
        self.buffer += pack_32_bit_int(number_val)

    def add_ipv4_address(self, address_str): # Renamed addaddr, addr
        binary_ip = ipv4_address_to_binary(address_str) # Use new name
        self.buffer += pack_32_bit_int(binary_ip) # Use new name

    def add_string(self, string_val): # Renamed addstring, s
        # DNS strings are length-prefixed byte strings
        if isinstance(string_val, str): # Ensure it's bytes
            # Assuming latin-1 for DNS strings if not specified, could be utf-8 for TXT
            try:
                byte_string = string_val.encode('latin-1')
            except UnicodeEncodeError:
                 byte_string = string_val.encode('utf-8') # Fallback for wider chars
        else:
            byte_string = string_val

        if len(byte_string) > 255:
            raise ValueError("Can't encode string of length %s (> 255)" % len(byte_string))
        self.add_byte(bytes([len(byte_string)])) # Length as a single byte
        self.add_bytes(byte_string)

    def add_domain_name(self, domain_name_str): # Renamed addname, name
        # Domain name packing (section 4.1.4)
        # The original code used string.splitfields and string.joinfields, which are deprecated.
        # Using simple split('.') and '.'.join()
        labels_list = []
        if domain_name_str == '': # Handle root domain case (single null byte)
             pass # Will be handled by adding a null byte at the end if no pointer
        else:
            for label_part in domain_name_str.split('.'): # Renamed list, label
                if not label_part:
                    raise PackError('empty label in domain name')
                labels_list.append(label_part)

        keys_to_index = [] # Renamed keys
        pointer_offset = None # Renamed pointer

        # Iterate backwards to check for existing pointers for suffixes
        for i in range(len(labels_list)):
            # Create suffix like "ISI.ARPA", then "F.ISI.ARPA"
            current_key = '.'.join(labels_list[i:]).upper()
            keys_to_index.append(current_key) # Store in original order for later indexing
            if current_key in self.index:
                pointer_offset = self.index[current_key]
                labels_list = labels_list[:i] # Truncate labels to pack, rest will be pointer
                break

        temp_buffer = b'' # Renamed buf
        current_buffer_offset = len(self.buffer) # Renamed offset
        new_index_entries = [] # Renamed index

        encoding_to_use = 'utf-8' if LABEL_UTF8 else LABEL_ENCODING # Renamed enc

        for i, label_text in enumerate(labels_list): # Renamed j, label
            try:
                encoded_label = label_text.encode(encoding_to_use)
            except UnicodeEncodeError:
                if not LABEL_UTF8: # If not explicitly UTF-8 and encoding fails, this is an issue
                    raise PackError(f"Cannot encode label '{label_text}' with '{encoding_to_use}'")
                # Fallback for UTF-8 if needed (though encode('utf-8') should handle it)
                if not label_text.startswith('\\ufeff'): # This seems like a specific pydns workaround
                    label_text = '\\ufeff' + label_text
                encoded_label = label_text.encode(encoding_to_use) # Should be 'utf-8' here

            label_length = len(encoded_label) # Renamed n
            if label_length > 63:
                raise PackError('label too long')

            # Check if pointer would be too large (max 14 bits for offset in pointer)
            if current_buffer_offset + len(temp_buffer) < 0x3FFF:
                 # keys_to_index was built from full name, so use original index i
                if i < len(keys_to_index): # ensure key exists
                    new_index_entries.append((keys_to_index[i], current_buffer_offset + len(temp_buffer)))
            else:
                print_colored('dns.Lib.BasePacker.add_domain_name: warning: pointer too big', COLOR_YELLOW) # Use print_colored

            temp_buffer += bytes([label_length]) + encoded_label # Length byte + label

        if pointer_offset is not None:
            temp_buffer += pack_16_bit_int(pointer_offset | 0xC000) # Use new name
        else:
            temp_buffer += b'\0' # Root label or end of non-compressed name

        self.buffer += temp_buffer
        for key, value in new_index_entries:
            self.index[key] = value

    def dump(self):
        indexed_keys = list(self.index.keys()) # Renamed keys
        indexed_keys.sort()
        print_colored('-' * 40, COLOR_BLUE) # Use print_colored
        for key_val in indexed_keys: # Renamed key
            print_colored('%20s %3d' % (key_val, self.index[key_val]), COLOR_BLUE)
        print_colored('-' * 40, COLOR_BLUE)
        is_space_needed = True # Renamed space
        for i in range(0, len(self.buffer) + 1, 2): # Iterate over buffer
            # The original `self.buf[i:i+2] == '**'` seems like a placeholder or debug marker,
            # which is not standard for DNS packing. Assuming it's for specific debug output.
            # For now, I'll keep a similar structure if such markers were intended.
            # If these are not actual DNS wire format markers, this part might need removal/rethinking.
            # For now, interpreting `**` as a special sequence in the buffer.
            if self.buffer[i:i+2] == b'**': # Compare with bytes
                if not is_space_needed:
                    print()
                is_space_needed = True
                continue
            is_space_needed = False
            print_colored('%4d' % i, end=' ', color_code_val=COLOR_GREEN) # Use print_colored
            for char_code in self.buffer[i:i+2]: # Iterate over bytes directly
                # chr(char_code) will work for ASCII range, for others it depends on encoding context
                char_repr = chr(char_code) if 32 < char_code < 127 else str(char_code)
                print_colored(' %s' % char_repr, end=' ', color_code_val=COLOR_GREEN)
            print()
        print_colored('-' * 40, COLOR_BLUE)

# Unpacking class

class BaseUnpacker: # Renamed Unpacker
    def __init__(self, buffer_data): # Renamed buf
        self.buffer = buffer_data
        self.offset = 0

    def get_byte(self): # Renamed getbyte
        if self.offset >= len(self.buffer):
            raise UnpackError("Ran off end of data")
        # In Python 3, indexing bytes returns an int.
        byte_val = self.buffer[self.offset] # Renamed c
        self.offset += 1
        return byte_val # Return as int

    def get_bytes(self, num_bytes): # Renamed getbytes, n
        byte_sequence = self.buffer[self.offset:(self.offset + num_bytes)] # Renamed s
        if len(byte_sequence) != num_bytes:
            raise UnpackError('not enough data left')
        self.offset += num_bytes
        return byte_sequence

    def get_16_bit_int(self): # Renamed get16bit
        return unpack_16_bit_int(self.get_bytes(2)) # Use new name

    def get_32_bit_int(self): # Renamed get32bit
        return unpack_32_bit_int(self.get_bytes(4)) # Use new name

    def get_ipv4_address(self): # Renamed getaddr
        return binary_to_ipv4_address(self.get_32_bit_int()) # Use new name

    def get_string(self): # Renamed getstring
        length = self.get_byte() # Length is a byte
        return self.get_bytes(length) # Return as bytes

    def get_domain_name(self): # Renamed getname
        # Domain name unpacking (section 4.1.4)
        first_byte = self.get_byte() # Renamed c, i

        if (first_byte & 0xC0) == 0xC0: # Pointer
            second_byte = self.get_byte() # Renamed d, j
            pointer_offset = ((first_byte << 8) | second_byte) & ~0xC000 # Renamed pointer
            saved_offset = self.offset # Renamed save_offset
            try:
                self.offset = pointer_offset
                pointed_domain_name = self.get_domain_name() # Renamed domain
            finally:
                self.offset = saved_offset
            return pointed_domain_name

        if first_byte == 0: # Root label
            return ''

        # It's a label
        label_bytes = self.get_bytes(first_byte) # Renamed domain
        # Attempt to decode based on global settings, falling back for robustness
        try:
            label_str = label_bytes.decode(LABEL_ENCODING if not LABEL_UTF8 else 'utf-8')
        except UnicodeDecodeError:
            try:
                label_str = label_bytes.decode('latin-1') # Common fallback
            except UnicodeDecodeError:
                label_str = str(label_bytes) # Last resort: raw byte string representation

        remaining_name_parts = self.get_domain_name() # Renamed remains

        if not remaining_name_parts:
            return label_str
        return label_str + '.' + remaining_name_parts


# Test program for packin/unpacking (section 4.1.4)

def test_packer(): # Renamed testpacker
    num_iterations = 2500 # Renamed N
    iteration_range = list(range(num_iterations)) # Renamed R
    import timing # This module is not standard, might be part of pydns or a local utility

    timing.start()
    for _ in iteration_range: # Renamed i
        packer_obj = BasePacker() # Renamed p
        packer_obj.add_ipv4_address('192.168.0.1')
        packer_obj.add_bytes(b'*' * 20) # Use bytes
        packer_obj.add_domain_name('f.ISI.ARPA')
        packer_obj.add_bytes(b'*' * 8)
        packer_obj.add_domain_name('Foo.F.isi.arpa')
        packer_obj.add_bytes(b'*' * 18)
        packer_obj.add_domain_name('arpa')
        packer_obj.add_bytes(b'*' * 26)
        packer_obj.add_domain_name('')
    timing.finish()
    print_colored(f"{timing.milli()} ms total for packing", COLOR_GREEN)
    if num_iterations > 0: # Avoid division by zero
      print_colored(f"{round(timing.milli() / num_iterations, 4)} ms per packing", COLOR_GREEN)

    unpacker_obj = BaseUnpacker(packer_obj.get_buffer()) # Renamed u, p
    unpacker_obj.get_ipv4_address()
    unpacker_obj.get_bytes(20)
    unpacker_obj.get_domain_name()
    unpacker_obj.get_bytes(8)
    unpacker_obj.get_domain_name()
    unpacker_obj.get_bytes(18)
    unpacker_obj.get_domain_name()
    unpacker_obj.get_bytes(26)
    unpacker_obj.get_domain_name()

    timing.start()
    for _ in iteration_range: # Renamed i
        unpacker_obj_loop = BaseUnpacker(packer_obj.get_buffer()) # Renamed u, p
        # Unpacking results are not stored in `res` in the original loop,
        # it just calls the methods.
        unpacker_obj_loop.get_ipv4_address()
        unpacker_obj_loop.get_bytes(20)
        unpacker_obj_loop.get_domain_name()
        unpacker_obj_loop.get_bytes(8)
        unpacker_obj_loop.get_domain_name()
        unpacker_obj_loop.get_bytes(18)
        unpacker_obj_loop.get_domain_name()
        unpacker_obj_loop.get_bytes(26)
        unpacker_obj_loop.get_domain_name()

    timing.finish()
    print_colored(f"{timing.milli()} ms total for unpacking", COLOR_GREEN)
    if num_iterations > 0:
        print_colored(f"{round(timing.milli() / num_iterations, 4)} ms per unpacking", COLOR_GREEN)


# Pack/unpack RR toplevel format (section 3.2.1)

class ResourceRecordPacker(BasePacker): # Renamed RRpacker
    def __init__(self):
        BasePacker.__init__(self)
        self.rdata_start_offset = None # Renamed rdstart

    def add_rr_header(self, name, record_type, record_class, ttl, *rdata_length_arg): # Renamed addRRheader, type, klass, rest, rdlength
        self.add_domain_name(name)
        self.add_16_bit_int(record_type)
        self.add_16_bit_int(record_class)
        self.add_32_bit_int(ttl)

        rdata_length = 0
        if rdata_length_arg:
            if rdata_length_arg[1:]: # More than one optional arg
                raise TypeError('too many args for rdata_length')
            rdata_length = rdata_length_arg[0]

        self.add_16_bit_int(rdata_length)
        self.rdata_start_offset = len(self.buffer)

    def _patch_rdata_length(self): # Renamed patchrdlength
        # This method assumes rdata_length was initially 0 or incorrect
        # and patches it after rdata is added.
        current_rdata_length = len(self.buffer) - self.rdata_start_offset
        # Go back to where rdlength was written (2 bytes before rdata_start_offset)
        rdlength_position = self.rdata_start_offset - 2

        # Check if patching is needed (if initially set length was different)
        # original_rdlength_bytes = self.buffer[rdlength_position : self.rdata_start_offset]
        # original_rdlength = unpack_16_bit_int(original_rdlength_bytes)
        # if original_rdlength == current_rdata_length:
        #     return

        rdata_bytes = self.buffer[self.rdata_start_offset:]

        # Reconstruct buffer without old rdlength and rdata
        self.buffer = self.buffer[:rdlength_position]
        self.add_16_bit_int(current_rdata_length) # Add correct length
        self.buffer += rdata_bytes # Add rdata back

    def end_resource_record(self): # Renamed endRR
        if self.rdata_start_offset is not None:
            self._patch_rdata_length()
        self.rdata_start_offset = None

    def get_buffer(self): # Override to ensure length is patched
        if self.rdata_start_offset is not None: # If addRRheader was called but not endRR
            self._patch_rdata_length()
        return BasePacker.get_buffer(self)

    # Standard RRs (section 3.3)
    def add_cname_record(self, name, klass, ttl, canonical_name): # Renamed addCNAME, cname
        self.add_rr_header(name, RecordType.CNAME, klass, ttl) # Type will be RECORD_TYPE_CNAME
        self.add_domain_name(canonical_name)
        self.end_resource_record()

    def add_hinfo_record(self, name, klass, ttl, cpu_info, os_info): # Renamed addHINFO, cpu, os
        self.add_rr_header(name, RecordType.HINFO, klass, ttl) # Type will be RECORD_TYPE_HINFO
        self.add_string(cpu_info)
        self.add_string(os_info)
        self.end_resource_record()

    def add_mx_record(self, name, klass, ttl, preference_val, exchange_server): # Renamed addMX, preference, exchange
        self.add_rr_header(name, RecordType.MX, klass, ttl) # Type will be RECORD_TYPE_MX
        self.add_16_bit_int(preference_val)
        self.add_domain_name(exchange_server)
        self.end_resource_record()

    def add_ns_record(self, name, klass, ttl, nameserver_domain): # Renamed addNS, nsdname
        self.add_rr_header(name, RecordType.NS, klass, ttl) # Type will be RECORD_TYPE_NS
        self.add_domain_name(nameserver_domain)
        self.end_resource_record()

    def add_ptr_record(self, name, klass, ttl, pointer_domain_name): # Renamed addPTR, ptrdname
        self.add_rr_header(name, RecordType.PTR, klass, ttl) # Type will be RECORD_TYPE_PTR
        self.add_domain_name(pointer_domain_name)
        self.end_resource_record()

    def add_soa_record(self, name, klass, ttl, mname, rname, serial, refresh, retry, expire, minimum): # Renamed
        self.add_rr_header(name, RecordType.SOA, klass, ttl) # Type will be RECORD_TYPE_SOA
        self.add_domain_name(mname)
        self.add_domain_name(rname)
        self.add_32_bit_int(serial)
        self.add_32_bit_int(refresh)
        self.add_32_bit_int(retry)
        self.add_32_bit_int(expire)
        self.add_32_bit_int(minimum)
        self.end_resource_record()

    def add_txt_record(self, name, klass, ttl, text_strings_list): # Renamed addTXT, list
        self.add_rr_header(name, RecordType.TXT, klass, ttl) # Type will be RECORD_TYPE_TXT
        if isinstance(text_strings_list, str): # Handle single string case
            text_strings_list = [text_strings_list]
        for text_data_item in text_strings_list: # Renamed txtdata
            self.add_string(text_data_item) # Each string is <character-string>
        self.end_resource_record()

    # Internet specific RRs (section 3.4) -- class = IN
    def add_a_record(self, name, klass, ttl, ipv4_address): # Renamed addA, address
        self.add_rr_header(name, RecordType.A, klass, ttl) # Type will be RECORD_TYPE_A
        self.add_ipv4_address(ipv4_address)
        self.end_resource_record()

    def add_wks_record(self, name, ttl, ipv4_address, protocol_num, service_bitmap): # Renamed addWKS, address, protocol, bitmap
        self.add_rr_header(name, RecordType.WKS, DnsClass.CLASS_IN, ttl) # Type/Class will be renamed
        self.add_ipv4_address(ipv4_address)
        self.add_byte(bytes([protocol_num])) # protocol is a single byte
        self.add_bytes(service_bitmap)
        self.end_resource_record()

    def add_srv_record(self): # Renamed addSRV
        raise NotImplementedError("SRV record packing not implemented")

def format_time_pretty(seconds_val): # Renamed prettyTime, seconds
    if seconds_val < 60:
        return seconds_val, "%d seconds" % (seconds_val)
    if seconds_val < 3600:
        return seconds_val, "%d minutes" % (seconds_val // 60) # Use integer division
    if seconds_val < 86400:
        return seconds_val, "%d hours" % (seconds_val // 3600)
    if seconds_val < 604800:
        return seconds_val, "%d days" % (seconds_val // 86400)
    return seconds_val, "%d weeks" % (seconds_val // 604800)


class ResourceRecordUnpacker(BaseUnpacker): # Renamed RRunpacker
    def __init__(self, buffer_data): # Renamed buf
        BaseUnpacker.__init__(self, buffer_data)
        self.rdata_end_offset = None # Renamed rdend

    def get_rr_header(self): # Renamed getRRheader
        domain_name = self.get_domain_name() # Renamed name
        record_type_code = self.get_16_bit_int() # Renamed rrtype
        class_code = self.get_16_bit_int() # Renamed klass
        ttl_val = self.get_32_bit_int() # Renamed ttl
        rdata_length_val = self.get_16_bit_int() # Renamed rdlength
        self.rdata_end_offset = self.offset + rdata_length_val
        return (domain_name, record_type_code, class_code, ttl_val, rdata_length_val)

    def end_resource_record_unpack(self): # Renamed endRR
        if self.offset != self.rdata_end_offset:
            # This might happen if rdlength was wrong or parsing stopped early
            # For robustness, one might choose to advance offset to rdend, or log warning
            # Original code raised error, so keeping that.
            raise UnpackError('end of RR data not reached, offset %d != expected_end %d' % (self.offset, self.rdata_end_offset) )

    def get_cname_rdata(self): # Renamed getCNAMEdata
        return self.get_domain_name()

    def get_hinfo_rdata(self): # Renamed getHINFOdata
        cpu_str = self.get_string().decode('latin-1', 'replace') # Strings are bytes, decode them
        os_str = self.get_string().decode('latin-1', 'replace')
        return cpu_str, os_str

    def get_mx_rdata(self): # Renamed getMXdata
        return self.get_16_bit_int(), self.get_domain_name()

    def get_ns_rdata(self): # Renamed getNSdata
        return self.get_domain_name()

    def get_ptr_rdata(self): # Renamed getPTRdata
        return self.get_domain_name()

    def get_soa_rdata(self): # Renamed getSOAdata
        mname = self.get_domain_name()
        rname = self.get_domain_name()
        serial = self.get_32_bit_int()
        refresh = self.get_32_bit_int()
        retry = self.get_32_bit_int()
        expire = self.get_32_bit_int()
        minimum = self.get_32_bit_int()
        return (mname, rname,
            ('serial', serial),
            ('refresh', format_time_pretty(refresh)), # Use new name
            ('retry', format_time_pretty(retry)),
            ('expire', format_time_pretty(expire)),
            ('minimum', format_time_pretty(minimum)))

    def get_txt_rdata(self): # Renamed getTXTdata
        strings_list = [] # Renamed list
        while self.offset < self.rdata_end_offset: # Check against rdend
            # TXT records can have multiple <character-string>s
            # Each is a length octet followed by that many bytes of text.
            # Try decoding as UTF-8 first, then latin-1 as fallback.
            text_bytes = self.get_string()
            try:
                strings_list.append(text_bytes.decode('utf-8'))
            except UnicodeDecodeError:
                strings_list.append(text_bytes.decode('latin-1', 'replace'))
        return strings_list

    get_spf_rdata = get_txt_rdata # Renamed getSPFdata

    def get_a_rdata(self): # Renamed getAdata
        return self.get_ipv4_address()

    def get_wks_rdata(self): # Renamed getWKSdata
        ipv4_address = self.get_ipv4_address() # Renamed address
        protocol_num = self.get_byte() # Renamed protocol
        service_bitmap = self.get_bytes(self.rdata_end_offset - self.offset) # Renamed bitmap
        return ipv4_address, protocol_num, service_bitmap

    def get_srv_rdata(self): # Renamed getSRVdata
        """
        _Service._Proto.Name TTL Class SRV Priority Weight Port Target.
        """
        priority_val = self.get_16_bit_int() # Renamed priority
        weight_val = self.get_16_bit_int() # Renamed weight
        port_val = self.get_16_bit_int() # Renamed port
        target_host = self.get_domain_name() # Renamed target
        return priority_val, weight_val, port_val, target_host


# Pack/unpack Message Header (section 4.1)

class HeaderPacker(BasePacker): # Renamed Hpacker
    def add_header(self, transaction_id, qr_flag, opcode_val, aa_flag, tc_flag, rd_flag, ra_flag, z_reserved, rcode_val,
              qd_count, an_count, ns_count, ar_count): # Renamed params
        self.add_16_bit_int(transaction_id)
        self.add_16_bit_int((qr_flag & 1) << 15 | (opcode_val & 0xF) << 11 | (aa_flag & 1) << 10
            | (tc_flag & 1) << 9 | (rd_flag & 1) << 8 | (ra_flag & 1) << 7
            | (z_reserved & 7) << 4 | (rcode_val & 0xF))
        self.add_16_bit_int(qd_count)
        self.add_16_bit_int(an_count)
        self.add_16_bit_int(ns_count)
        self.add_16_bit_int(ar_count)

class HeaderUnpacker(BaseUnpacker): # Renamed Hunpacker
    def get_header(self): # Renamed getHeader
        transaction_id = self.get_16_bit_int() # Renamed id
        flags_val = self.get_16_bit_int() # Renamed flags
        qr_flag, opcode_val, aa_flag, tc_flag, rd_flag, ra_flag, z_reserved, rcode_val = ( # Renamed vars
            (flags_val >> 15) & 1,
            (flags_val >> 11) & 0xF,
            (flags_val >> 10) & 1,
            (flags_val >> 9) & 1,
            (flags_val >> 8) & 1,
            (flags_val >> 7) & 1,
            (flags_val >> 4) & 7,
            (flags_val >> 0) & 0xF)
        qd_count = self.get_16_bit_int() # Renamed qdcount
        an_count = self.get_16_bit_int() # Renamed ancount
        ns_count = self.get_16_bit_int() # Renamed nscount
        ar_count = self.get_16_bit_int() # Renamed arcount
        return (transaction_id, qr_flag, opcode_val, aa_flag, tc_flag, rd_flag, ra_flag, z_reserved, rcode_val,
                  qd_count, an_count, ns_count, ar_count)


# Pack/unpack Question (section 4.1.2)

class QuestionPacker(BasePacker): # Renamed Qpacker
    def add_question(self, query_name, query_type, query_class): # Renamed qname, qtype, qclass
        self.add_domain_name(query_name)
        self.add_16_bit_int(query_type)
        self.add_16_bit_int(query_class)

class QuestionUnpacker(BaseUnpacker): # Renamed Qunpacker
    def get_question(self): # Renamed getQuestion
        return self.get_domain_name(), self.get_16_bit_int(), self.get_16_bit_int()


# Pack/unpack Message(section 4)
# NB the order of the base classes is important for __init__()!

class MessagePacker(ResourceRecordPacker, QuestionPacker, HeaderPacker): # Renamed Mpacker
    pass

class MessageUnpacker(ResourceRecordUnpacker, QuestionUnpacker, HeaderUnpacker): # Renamed Munpacker
    pass


# Routines to print an unpacker to stdout, for debugging.
# These affect the unpacker's current position!

def dump_message_details(unpacker_obj): # Renamed dumpM, u
    print_colored('HEADER:', COLOR_BLUE, end=' ')
    (transaction_id, qr_flag, opcode_val, aa_flag, tc_flag, rd_flag, ra_flag, z_reserved, rcode_val,
     qd_count, an_count, ns_count, ar_count) = unpacker_obj.get_header() # Use new name

    print_colored('id=%d,' % transaction_id, COLOR_GREEN, end=' ')
    # Use f-string for easier formatting if Python version allows (assuming 3.6+)
    header_flags_str = f"qr={qr_flag}, opcode={Opcode.get_opcode_string(opcode_val)}, aa={aa_flag}, tc={tc_flag}, rd={rd_flag}, ra={ra_flag}, z={z_reserved}, rcode={Status.get_status_string(rcode_val)}," # Use new names
    print_colored(header_flags_str, COLOR_GREEN)

    if tc_flag:
        print_colored('*** response truncated! ***', COLOR_RED)
    if rcode_val:
        print_colored('*** nonzero error code! (%s) ***' % Status.get_status_string(rcode_val), COLOR_RED) # Use new name

    print_colored(f"  qdcount={qd_count}, ancount={an_count}, nscount={ns_count}, arcount={ar_count}", COLOR_GREEN)

    for i in range(qd_count):
        print_colored('QUESTION %d:' % i, COLOR_BLUE, end=' ')
        dump_question_details(unpacker_obj) # Use new name
    for i in range(an_count):
        print_colored('ANSWER %d:' % i, COLOR_BLUE, end=' ')
        dump_resource_record_details(unpacker_obj) # Use new name
    for i in range(ns_count):
        print_colored('AUTHORITY RECORD %d:' % i, COLOR_BLUE, end=' ')
        dump_resource_record_details(unpacker_obj) # Use new name
    for i in range(ar_count):
        print_colored('ADDITIONAL RECORD %d:' % i, COLOR_BLUE, end=' ')
        dump_resource_record_details(unpacker_obj) # Use new name

class DnsQueryResult(object): # Renamed DnsResult

    def __init__(self, unpacker_obj, query_args): # Renamed u, args
        self.header = {}
        self.questions = []
        self.answers = []
        self.authority = []
        self.additional = []
        self.args = query_args
        self._store_message_data(unpacker_obj) # Renamed storeM

    def show(self):
        import time # Should be at top of file ideally
        print_colored('; <<>> PDG.py (pydns) <<>> %s %s' % (self.args.get('name', ''), RecordType.get_type_string(self.args.get('qtype',0))), COLOR_GREEN) # Use new name
        options_str = "" # Renamed opt
        if self.args.get('rd'):
            options_str += 'recurs '
        header_dict = self.header # Renamed h
        print_colored(';; options:', COLOR_BLUE, end=' ')
        print_colored(options_str, COLOR_GREEN)
        print_colored(';; got answer:', COLOR_BLUE)
        print_colored(';; ->>HEADER<<- opcode %s, status %s, id %d' %
              (Opcode.get_opcode_string(header_dict['opcode']), Status.get_status_string(header_dict['rcode']), header_dict['id']), COLOR_GREEN) # Use new names

        active_flags = [flag_name for flag_name in ('qr', 'aa', 'rd', 'ra', 'tc') if header_dict.get(flag_name)] # Renamed flags
        print_colored(';; flags: %s; Ques: %d, Ans: %d, Auth: %d, Addit: %d' % (
            ' '.join(active_flags), # Use space join
            header_dict['qdcount'], header_dict['ancount'], header_dict['nscount'], header_dict['arcount']), COLOR_GREEN)

        print_colored(';; QUESTIONS:', COLOR_BLUE)
        for question_item in self.questions: # Renamed q
            print_colored(';;      %s, type = %s, class = %s' % (question_item['qname'], question_item['qtypestr'], question_item['qclassstr']), COLOR_GREEN)
        print_colored("", COLOR_BLUE) # Empty line

        print_colored(';; ANSWERS:', COLOR_BLUE)
        for answer_item in self.answers: # Renamed a
            print_colored('%-20s    %-6s  %-6s  %s' % (answer_item['name'], repr(answer_item['ttl']), answer_item['typename'], answer_item['data']), COLOR_GREEN)
        print_colored("", COLOR_BLUE)

        print_colored(';; AUTHORITY RECORDS:', COLOR_BLUE)
        for auth_item in self.authority: # Renamed a
            print_colored('%-20s    %-6s  %-6s  %s' % (auth_item['name'], repr(auth_item['ttl']), auth_item['typename'], auth_item['data']), COLOR_GREEN)
        print_colored("", COLOR_BLUE)

        print_colored(';; ADDITIONAL RECORDS:', COLOR_BLUE)
        for add_item in self.additional: # Renamed a
            print_colored('%-20s    %-6s  %-6s  %s' % (add_item['name'], repr(add_item['ttl']), add_item['typename'], add_item['data']), COLOR_GREEN)
        print_colored("", COLOR_BLUE)

        if 'elapsed' in self.args:
            print_colored(';; Total query time: %d msec' % self.args['elapsed'], COLOR_BLUE)
        print_colored(';; To SERVER: %s' % (self.args.get('server', 'N/A')), COLOR_BLUE)
        print_colored(';; WHEN: %s' % time.ctime(time.time()), COLOR_BLUE)

    def _store_message_data(self, unpacker_obj): # Renamed storeM, u
        (self.header['id'], self.header['qr'], self.header['opcode'],
          self.header['aa'], self.header['tc'], self.header['rd'],
          self.header['ra'], self.header['z'], self.header['rcode'],
          self.header['qdcount'], self.header['ancount'],
          self.header['nscount'], self.header['arcount']) = unpacker_obj.get_header() # Use new name
        self.header['opcodestr'] = Opcode.get_opcode_string(self.header['opcode']) # Use new name
        self.header['status'] = Status.get_status_string(self.header['rcode']) # Use new name

        for _ in range(self.header['qdcount']): # Renamed i
            self.questions.append(self._store_question_data(unpacker_obj)) # Use new name
        for _ in range(self.header['ancount']):
            self.answers.append(self._store_resource_record_data(unpacker_obj)) # Use new name
        for _ in range(self.header['nscount']):
            self.authority.append(self._store_resource_record_data(unpacker_obj)) # Use new name
        for _ in range(self.header['arcount']):
            self.additional.append(self._store_resource_record_data(unpacker_obj)) # Use new name

    def _store_question_data(self, unpacker_obj): # Renamed storeQ, u
        question_dict = {} # Renamed q
        question_dict['qname'], question_dict['qtype'], question_dict['qclass'] = unpacker_obj.get_question() # Use new name
        question_dict['qtypestr'] = RecordType.get_type_string(question_dict['qtype']) # Use new name
        question_dict['qclassstr'] = DnsClass.get_class_string(question_dict['qclass']) # Use new name
        return question_dict

    def _store_resource_record_data(self, unpacker_obj): # Renamed storeRR, u
        rr_dict = {} # Renamed r
        rr_dict['name'], rr_dict['type'], rr_dict['class'], rr_dict['ttl'], rr_dict['rdlength'] = unpacker_obj.get_rr_header() # Use new name
        rr_dict['typename'] = RecordType.get_type_string(rr_dict['type']) # Use new name
        rr_dict['classstr'] = DnsClass.get_class_string(rr_dict['class']) # Use new name

        method_name_str = 'get_%s_rdata' % rr_dict['typename'].lower().replace('-', '_') # Renamed mname, handle potential hyphens in type names for method lookup
        if hasattr(unpacker_obj, method_name_str):
            rr_dict['data'] = getattr(unpacker_obj, method_name_str)()
        else:
            rr_dict['data'] = unpacker_obj.get_bytes(rr_dict['rdlength'])
        unpacker_obj.end_resource_record_unpack() # Ensure unpacker offset is correct
        return rr_dict

def dump_question_details(unpacker_obj): # Renamed dumpQ, u
    qname, qtype, qclass = unpacker_obj.get_question() # Use new name
    print_colored('qname=%s, qtype=%d(%s), qclass=%d(%s)' % (qname,
        qtype, RecordType.get_type_string(qtype), qclass, DnsClass.get_class_string(qclass)), COLOR_GREEN) # Use new names

def dump_resource_record_details(unpacker_obj): # Renamed dumpRR, u
    name, record_type, klass, ttl, rdlength = unpacker_obj.get_rr_header() # Use new names
    typename = RecordType.get_type_string(record_type) # Use new name
    class_str = DnsClass.get_class_string(klass) # Renamed ks, Use new name
    print_colored('name=%(name)s, type=%(type)d(%(typename)s), class=%(klass)d(%(class_str)s), ttl=%(ttl)s' % vars(), COLOR_GREEN) # Use new names

    method_name_str = 'get_%s_rdata' % typename.lower().replace('-', '_') # Renamed mname
    if hasattr(unpacker_obj, method_name_str):
        print_colored('  formatted rdata: %s' % str(getattr(unpacker_obj, method_name_str)()), COLOR_GREEN) # Ensure data is str for print
    else:
        print_colored('  binary rdata: %s' % unpacker_obj.get_bytes(rdlength), COLOR_GREEN) # This will print bytes repr
    unpacker_obj.end_resource_record_unpack() # Ensure unpacker offset is correct after reading data

if __name__ == "__main__":
    test_packer() # Use new name
