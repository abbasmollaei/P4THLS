import json
import os
from sys_utils import *

def get_includes(headers, metadata):
    code_h = "\n".join([f'#include "{header_name.capitalize()}Header.h"' for header_name in list(headers.keys())])
    code_m = "\n".join([f'#include "{meta_name.capitalize()}.h"' for meta_name in list(metadata.keys())])
    return f'{code_h}\n{code_m}\n\n'


def get_enum(headers):
    header_names = headers.keys()
    header_count = len(header_names)
    enum_type = "short" if header_count <= 16 else "int"
    code = f"enum HeaderValidFlag : {enum_type} {{\n"
    for i, item in enumerate(header_names):
        value = 1 << i
        if "short" in enum_type:
            code += f"\tH_{item.upper()} = 0x{value:04X}"
        else:
            code += f"\tH_{item.upper()} = 0x{value:08X}"
        if i != header_count - 1:
            code += ",\n"
        else:
            code += "\n"
    code += "};\n\n"
    return code


def get_struct(headers, metadata):
    header_names = headers.keys()
    meta_names = metadata.keys()
    valid_type = "short" if len(header_names) <= 16 else "int"
    ctor = '\tPacket() : valid(0) {}\n'
    cctor = '\tPacket(const Packet &copy) :\n'
    cctor += "\n".join([f'\t\t{header}(copy.{header}),' for header in header_names]) + '\n'
    cctor += "\n".join([f'\t\t{meta}(copy.{meta}),' for meta in meta_names]) + '\n'
    cctor += '\t\tvalid(copy.valid) {}\n\n'
    members = "\n".join([f'\t{header.capitalize()}Header {header};' for header in header_names]) + '\n'
    members += "\n".join([f'\t{meta.capitalize()} {meta};' for meta in meta_names]) + '\n'
    members += f'\t{valid_type} valid;\n'
    valid_funcs = '''
	void setValid(HeaderValidFlag flag)
	{
		valid |= flag;
	}

	void setInvalid(HeaderValidFlag flag)
	{
		valid &= ~flag;
	}

	bool isValid(HeaderValidFlag flag)
	{
		return (valid & flag) != 0;
	}'''

    code = 'struct Packet {\n' + ctor + cctor + members + valid_funcs + '\n};\n'
    return code


# Converting extracted info into C++-compatible format
def gen_cpp_code(dir_path):

    headers = retrieve_object('headers')
    metadata = retrieve_object('metadata')
    code_inc = get_includes(headers, metadata)
    code_enum = get_enum(headers)
    code_struct = get_struct(headers, metadata)
    
#    for header_name, fields in headers.items():
#        header_struct_name = f'{header_name.capitalize()}Header'
#        ctor_code = f"\t{header_struct_name}() {{}}\n"
#        x1 = ",\n".join([f"\t\t{field_name}(other.{field_name})" for field_name, _ in list(fields.items())])
#        copy_ctor_code = f"\t{header_struct_name}(const {header_struct_name} &other) :\n" + x1 + " {}\n" 
#        fields_code = "\n".join([f"\tap_uint<{bitwidth}> {field_name};" for field_name, bitwidth in list(fields.items())])
#        serialize_code = generate_serialize_function(header_struct_name, list(headers[header_name].items()))
#        deserialize_code = generate_deserialize_function(header_struct_name, list(headers[header_name].items()))
    code = "#ifndef PACKET_H\n" + \
           "#define PACKET_H\n\n" + \
           code_inc + code_enum + code_struct + \
           "\n#endif // PACKET_H\n"

    with open(f'{dir_path}/Packet.h', 'w') as f:
        f.write(code)


def generate_packet(build_dir):
    dir_path = f'{build_dir}/header'
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)
    gen_cpp_code(dir_path)

    
