import json
import os
import re
import math
from sys_utils import *

def get_headers_variable_name(p4src):
    header_var_pattern = r'inout\s+headers\s+(\w+)'  # Looks for 'inout headers hdr'
    header_var_match = re.search(header_var_pattern, p4src)
    if not header_var_match:
        return ''
    hdr_name = header_var_match.group(1)
    return hdr_name

def transform_string_isvalid(input_str, headers):
    # Define a function to replace the matching substring
    def replace_match(match):
        x = match.group(1)  # Capture the 'x' part (header name)
        if x in headers:
            y = f"H_{x.upper()}"
            return f"pkt.isValid({y})"
        return match.group(0)  # Return the original string if x is not in headers

    # Regular expression to match "pkt.x.setInvalid()"
    pattern = r'pkt\.(\w+)\.isValid\(\)'
    # Use re.sub to substitute based on the match
    result = re.sub(pattern, replace_match, input_str)
    return result


def transform_string_setvalid(input_str, headers):
    # Define a function to replace the matching substring
    def replace_match(match):
        x = match.group(1)  # Capture the 'x' part (header name)
        if x in headers:
            y = f"H_{x.upper()}"
            return f"pkt.setValid({y})"
        return match.group(0)  # Return the original string if x is not in headers

    # Regular expression to match "pkt.x.setInvalid()"
    pattern = r'pkt\.(\w+)\.setValid\(\)'
    # Use re.sub to substitute based on the match
    result = re.sub(pattern, replace_match, input_str)
    return result


def transform_string_setinvalid(input_str, headers):
    # Define a function to replace the matching substring
    def replace_match(match):
        x = match.group(1)  # Capture the 'x' part (header name)
        if x in headers:
            y = f"H_{x.upper()}"
            return f"pkt.setInvalid({y})"
        return match.group(0)  # Return the original string if x is not in headers

    # Regular expression to match "pkt.x.setInvalid()"
    pattern = r'pkt\.(\w+)\.setInvalid\(\)'
    # Use re.sub to substitute based on the match
    result = re.sub(pattern, replace_match, input_str)
    return result


def reformat_apply_block(apply_code):
    # Regular expression to match 'apply()' or 'apply ()' and its variants, but only replace if no arguments are present
    apply_pattern = re.compile(r'(\b\w+\s*\.\s*apply\s*)\(\s*\)')
    # Replace with 'apply(pkt, memPtr)' for each matching 'apply()'
    reformatted_code = apply_pattern.sub(r'\1(memPtr, pkt)', apply_code)
    return reformatted_code


def get_apply_block(p4_code):
    # Remove comments from the P4 code before processing
    cleaned_code = remove_extra_empty_lines(remove_comments(p4_code))
    # Regular expression pattern for control block
    control_block_pattern = re.compile(r'control\s+(\w+)\s*\((.*?)\)\s*\{', re.DOTALL)
    # Find all control blocks
    control_blocks = control_block_pattern.finditer(cleaned_code)
    code = ''
    for match in control_blocks:
        control_name = match.group(1)
        if 'ingress' not in control_name.lower():
            continue

        control_start = match.end() -1 # Start of the control content
        control_end = find_matching_brace(cleaned_code, control_start)  # Find the matching closing brace for the control block
        if control_end != -1:
            control_content = cleaned_code[control_start:control_end]

            # Now search for the apply block inside this control block
            # Use a pattern to allow spaces/enters between "apply" and "{"
            apply_pattern = re.compile(r'apply\s*\{', re.DOTALL)
            apply_match = apply_pattern.search(control_content)
            if apply_match:
                apply_start = apply_match.end() -1 # Move past 'apply {'
                
                # Find the matching closing brace for the apply block
                apply_end = find_matching_brace(control_content, apply_start)
                if apply_end != -1:
                    apply_block = beautify_code(control_content[apply_start+1:apply_end].strip())
                    control_args = match.group(2)
                    hdr = get_headers_variable_name(control_args)
                    apply_block = apply_block.replace(f'{hdr}.', f'pkt.')
                    code = reformat_apply_block(apply_block)
                    headers = retrieve_object('headers')
                    code = transform_string_isvalid(code, headers)
                    code = transform_string_setvalid(code, headers)
                    code = transform_string_setinvalid(code, headers)
                    break
    return code


def get_top_ingress_function():
    code = '''
void ingress_processing(hls::stream<Packet> &qpkt1, 
                        hls::stream<Packet> &qpkt2, 
                        unsigned int *memCtrl, 
                        unsigned int ctrl, 
                        unsigned int flag)
{
#pragma HLS PIPELINE
	if (!qpkt1.empty()) {
		Packet pkt;
		qpkt1.read(pkt);

		ingress_control(pkt, memCtrl, ctrl, flag);
        
        if (pkt.standardmetadata.drop == 0)
		    qpkt2.write(pkt);
	}
}
    '''
    return code


def get_internal_ingress_function(apply_block_code):
    tables = retrieve_object('tables')
    # tables_const = retrieve_object('table_const')
    # table_sizes = tables_const.get('table_size', [])
    # table_key_width = tables_const.get('table_matchkey_width', [])
    # table_value_width = tables_const.get('table_action_width', [])
    # table_types = tables_const.get('table_types', [])

    table_instances = []
    list_bind_uram = []
    list_bind_bram = []
    list_bind_lutram = []
    list_control_plane = []
    c = 0
    for table in tables:
        table_name = table["table_name"]
        table_struct_name = f'{table_name.capitalize()}Table'
        table_instances.append(f'static {table_struct_name} {table_name};')
        list_bind_uram.append(f'#pragma HLS bind_storage variable={table_name}.impl.lookup type=ram_2p impl=uram')
        list_bind_bram.append(f'#pragma HLS bind_storage variable={table_name}.impl.lookup type=ram_2p impl=bram')
        list_bind_lutram.append(f'#pragma HLS bind_storage variable={table_name}.impl.lookup type=ram_2p impl=lutram')
        list_control_plane.append(f'if (flag & ({c} << 0x01)) {table_name}.update_table(memCtrl, ctrl);')

    table_instances_code = '\n\t'.join(table_instances) + '\n\n'
    bind_storage_code = '#if defined(URAM)\n' + \
                        '\n'.join(list_bind_uram) + \
                        '\n#elif defined(BRAM)\n' + \
                        '\n'.join(list_bind_bram) + \
                        '\n#else\n' + \
                        '\n'.join(list_bind_lutram) + \
                        '\n#endif\n'
    control_plane_code = '\n\t\t'.join(list_control_plane)
    code = 'void ingress_control(Packet &pkt, unsigned int *memPtr, unsigned int flag)\n{\n#pragma HLS PIPELINE\n\t' + \
        table_instances_code + \
        bind_storage_code + \
        '\n    if (flag != 0) {\n\t\t' + \
        control_plane_code + \
        '\n    else {\n' + \
        apply_block_code + \
        '\n    }\n}\n'

    return code


def gen_control_code(p4src, dir_path):
    code = '#ifndef INGRESS_PROCESSING_H\n' + \
       '#define INGRESS_PROCESSING_H\n\n' + \
       '#include "../common/Shared.h"\n' + \
       '#include "../header/Packet.h"\n' + \
       '#include "../table/Table.h"\n\n' + \
       get_internal_ingress_function(get_apply_block(p4src)) + \
       get_top_ingress_function() + \
       '\n#endif // INGRESS_PROCESSING_H\n'

    with open(f'{dir_path}/IngressProcessing.h', 'w') as f:
        f.write(code)


def generate_control(p4src, json, build_dir, src_dir):
    dir_path = f'{build_dir}/ingress'
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)
    gen_control_code(p4src, dir_path)
    copy_file(f'{src_dir}/templated/MemoryInterface.h', f'{dir_path}/MemoryInterface.h')
    
