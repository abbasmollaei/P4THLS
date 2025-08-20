import json
import os
from sys_utils import *

def generate_serialize_function(meta_name, fields):

    def line_code(bit_mask, bit_shift, s1, s2):
        line = ""
        s3 = f"0x{bit_mask:X}"
        s4 = f"{bit_shift}"
        if (bit_mask == 0xFF) and (bit_shift == 0):
            line += f"{s1} {s2};\n"
        elif bit_mask == 0xFF:
            line += f"{s1} ({s2} << {s4});\n"
        elif bit_shift == 0:    
            line += f"{s1} ({s2} & {s3});\n"
        else:
            line += f"{s1} ({s2} & {s3}) << {s4};\n"
        return line

    serialize_code = f"void serialize(unsigned char* d, {meta_name} &hdr) {{\n"
    serialize_code += "#pragma HLS INLINE\n"

    byte_offset = 0
    bit_offset = 0
    bit_mask = 0xFF
    bit_shift = 0

    for field, bitwidth in fields:
        if bit_offset + bitwidth <= 8:
            # If the current field fits in the remaining bits of the current byte
            bit_mask = (1 << bitwidth) - 1
            bit_shift = 8 - bitwidth - bit_offset
            s1 = f"    d[{byte_offset}] = " if bitwidth == 8 else f"    d[{byte_offset}] |="
            s2 = f"hdr.{field}.to_uchar()"
            serialize_code += line_code(bit_mask, bit_shift, s1, s2)
            bit_offset += bitwidth
        else:
            # Handle fields that cross byte boundaries
            while bitwidth > 0:
                available_bits = 8 - bit_offset
                if bitwidth <= available_bits:
                    bit_mask = (1 << bitwidth) - 1
                    bit_shift = bit_offset
                    s1 = f"    d[{byte_offset}] = " if available_bits == 8 else f"    d[{byte_offset}] |="
                    s2 = f"hdr.{field}.range({bitwidth - 1}, 0).to_uchar()"
                    serialize_code += line_code(bit_mask, bit_shift, s1, s2)
                    bit_offset += bitwidth
                    bitwidth = 0
                elif bit_offset != 0:
                    bit_mask = (1 << available_bits) - 1
                    bit_shift = 0
                    s1 = f"    d[{byte_offset}] = " if available_bits == 8 else f"    d[{byte_offset}] |="
                    s2 = f"hdr.{field}.range({bitwidth - 1}, {bitwidth - available_bits}).to_uchar()"
                    serialize_code += line_code(bit_mask, bit_shift, s1, s2)
                    bit_offset = 0
                    bitwidth -= available_bits
                    byte_offset += 1
                else:
                    bit_mask = 0xFF
                    bit_shift = 0
                    s1 = f"    d[{byte_offset}] ="
                    s2 = f"hdr.{field}.range({bitwidth - 1}, {bitwidth - 8}).to_uchar()"
                    serialize_code += line_code(bit_mask, bit_shift, s1, s2)
                    bit_offset = 0
                    bitwidth -= available_bits
                    byte_offset += 1
        if bit_offset == 8:
            byte_offset += 1
            bit_offset = 0

    serialize_code += "}\n"
    return serialize_code


def generate_deserialize_function(meta_name, fields):
    
    def line_code(bit_mask, bit_shift, s1, s2):
        line = ""
        s3 = f"0x{bit_mask:X}"
        s4 = f"{bit_shift}"
        if (bit_mask == 0xFF) and (bit_shift == 0):
            line += f"{s1} {s2};\n"
        elif bit_mask == 0xFF:
            line += f"{s1} ({s2} >> {s4});\n"
        elif bit_shift == 0:    
            line += f"{s1} ({s2} & {s3});\n"
        else:
            line += f"{s1} ({s2} >> {s4}) & {s3};\n"
        return line

    deserialize_code = f"void deserialize(unsigned char* d, {meta_name} &hdr) {{\n"
    deserialize_code += "#pragma HLS INLINE\n"

    byte_offset = 0
    bit_offset = 0
    bit_shift = 0
    bit_mask = 0xFF

    for field, bitwidth in fields:
        if bit_offset + bitwidth <= 8:
            # If the current field fits in the remaining bits of the current byte
            bit_shift = 8 - bitwidth - bit_offset
            bit_mask = (1 << bitwidth) - 1
            s1 = f"    hdr.{field} ="
            s2 = f"d[{byte_offset}]"
            deserialize_code += line_code(bit_mask, bit_shift, s1, s2)
            bit_offset += bitwidth
        else:
            # Handle fields that cross byte boundaries
            while bitwidth > 0:
                if bitwidth <= 8:
                    bit_shift = 8 - bitwidth - bit_offset
                    bit_mask = (1 << bitwidth) - 1
                    #deserialize_code += f"    hdr.{field}.range({bitwidth-1}, 0) = (d[{byte_offset}] >> {bit_shift}) & 0x{bit_mask:X};\n"
                    s1 = f"    hdr.{field}.range({bitwidth-1}, 0) ="
                    s2 = f"d[{byte_offset}]"
                    deserialize_code += line_code(bit_mask, bit_shift, s1, s2)
                    bit_offset = bitwidth
                    bitwidth = 0
                else:
                    #deserialize_code += f"    hdr.{field}.range({bitwidth-1}, {bitwidth-8+bit_offset}) = d[{byte_offset}];\n"
                    bit_shift = 0
                    bit_mask = 0xFF
                    s1 = f"    hdr.{field}.range({bitwidth - 1}, {bitwidth - 8 + bit_offset}) ="
                    s2 = f"d[{byte_offset}]"
                    deserialize_code += line_code(bit_mask, bit_shift, s1, s2)
                    bitwidth -= 8 - bit_offset
                    bit_offset = 0
                    byte_offset += 1
        if bit_offset == 8:
            byte_offset += 1
            bit_offset = 0

    deserialize_code += "}\n"
    return deserialize_code


# Extract packet format (metadata names and sizes)
def extract_metadata(data):
    metadata = {}
    header_types = {ht['name']: ht['fields'] for ht in data['header_types']}
    for meta in data['headers']:
        if meta['metadata'] == True:
            meta_name = meta['name']
            if 'standard' in meta_name.lower():
                continue
            fields = header_types.get(meta['header_type'], [])
            metadata[meta_name] = {field[0]: field[1] for field in fields}
    return metadata


def extract_std_metadata():
    std_metadata = {}
    std_metadata['drop'] = 1
    std_metadata['_padding'] = 7
    return std_metadata


# Converting extracted info into C++-compatible format
def gen_cpp_code(headers, dir_path):
    for meta_name, fields in headers.items():
        meta_struct_name = f'{meta_name.capitalize()}'
        ctor_code = f"\t{meta_struct_name}() {{}}\n"
        x1 = ",\n".join([f"\t\t{field_name}(other.{field_name})" for field_name, _ in list(fields.items())])
        copy_ctor_code = f"\t{meta_struct_name}(const {meta_struct_name} &other) :\n" + x1 + " {}\n" 
        fields_code = "\n".join([f"\tap_uint<{bitwidth}> {field_name};" for field_name, bitwidth in list(fields.items())])
        serialize_code = generate_serialize_function(meta_struct_name, list(headers[meta_name].items()))
        deserialize_code = generate_deserialize_function(meta_struct_name, list(headers[meta_name].items()))
        metadata_code = f"#ifndef {meta_name.upper()}_H\n" + \
           f"#define {meta_name.upper()}_H\n\n" + \
           f"#include \"BaseHeader.h\"\n\n" + \
           f"struct {meta_struct_name} {{\n" + \
           f"{ctor_code}" + f"{copy_ctor_code}" + "\n" + f"{fields_code}" + "\n};\n\n" + \
           serialize_code + "\n" + deserialize_code + "\n" + \
           f"#endif // {meta_name.upper()}_H\n"

        with open(f'{dir_path}/{meta_struct_name}.h', 'w') as f:
            f.write(metadata_code)


def generate_metadata(json, build_dir):
    dir_path = f'{build_dir}/header'
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)
    metadata = extract_metadata(json)
    metadata['standardmetadata'] = extract_std_metadata()
    gen_cpp_code(metadata, dir_path)
    store_object(metadata, 'metadata')

    