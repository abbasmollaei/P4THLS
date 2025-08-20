import json
import os
import re
import math
from sys_utils import *

#def get_headers_variable_name(p4src):
#    header_var_pattern = r'inout\s+headers\s+(\w+)'  # Looks for 'inout headers hdr'
#    header_var_match = re.search(header_var_pattern, p4src)
#    if not header_var_match:
#        return ''
#    hdr_name = header_var_match.group(1)
#    return hdr_name
#
#
#def replace_headers_variable(hdr_name, action_code):
#    # This ensures only the structure accesses like 'hdr.' or 'hdr[' are replaced
#    # Word boundaries ensure that we are replacing the variable only when used correctly
#    pattern = rf'\b{hdr_name}\b(?=\s*[\.\[])'  # Matches 'hdr.' or 'hdr['
#    # Perform the substitution safely
#    modified_code = re.sub(pattern, 'pkt', action_code)
#    return modified_code


def extract_table_params(table_blocks):

    # Regex patterns
    key_pattern = re.compile(r'key\s*=\s*\{([^}]+)\}')
    actions_pattern = re.compile(r'actions\s*=\s*\{([^}]+)\}')
    size_pattern = re.compile(r'size\s*=\s*(\d+)')
    default_action_pattern = re.compile(r'default_action\s*=\s*([^\s;]+)')

    extracted_params = []
    
    for table_name, block in table_blocks:
        # Extract the key
        key_match = key_pattern.search(block)
        key = key_match.group(1).strip().split('\n') if key_match else []

        # Extract the actions
        actions_match = actions_pattern.search(block)
        actions = actions_match.group(1).strip().split('\n') if actions_match else []

        # Extract the size
        size_match = size_pattern.search(block)
        size = size_match.group(1) if size_match else None

        # Extract the default_action
        default_action_match = default_action_pattern.search(block)
        default_action = default_action_match.group(1) if default_action_match else None

        # Clean up the extracted strings
        key = [line.strip().replace(";", "") for line in key]
        actions = [line.strip().replace(";", "") for line in actions]
        
        # Store extracted values
        extracted_params.append({
            'table_name': table_name,
            'key': key,
            'actions': actions,
            'size': size,
            'default_action': default_action
        })
    
    return extracted_params


def extract_tables(p4_code):
    """
    Finds and extracts all table blocks, including those with nested braces.
    Returns a list of tuples (table_name, table_body).
    """
    # hdr_name = get_headers_variable_name(p4_code)

    table_blocks = []
    table_start_pattern = re.compile(r'table\s+(\w+)\s*{')
    
    index = 0
    while index < len(p4_code):
        # Search for the next table start
        match = table_start_pattern.search(p4_code, index)
        if not match:
            break
        
        table_name = match.group(1)
        open_brace_index = match.end() - 1
        close_brace_index = find_matching_brace(p4_code, open_brace_index)
        
        # Extract the table body, which includes everything between the opening and closing braces
        table_body = p4_code[open_brace_index + 1: close_brace_index].strip()
        #table_body = replace_headers_variable(hdr_name, table_body)
        table_blocks.append((table_name, table_body))
        
        # Move index past the current table block
        index = close_brace_index + 1
    
    return table_blocks

#def find_matching_brace(code, open_brace_index):
#    """
#    Finds the index of the matching closing brace for the opening brace at open_brace_index.
#    Handles nested braces.
#    """
#    stack = []
#    for i in range(open_brace_index, len(code)):
#        if code[i] == '{':
#            stack.append('{')
#        elif code[i] == '}':
#            stack.pop()
#            if not stack:
#                return i
#    return -1  # No matching brace found (shouldn't happen if the input is valid)
#

def extract_fields_and_actions(table_body):
    """
    Extract match fields and actions from the table body.
    """
    field_pattern = re.compile(r'key\s*=\s*{([^}]+)}')
    action_pattern = re.compile(r'actions\s*=\s*{([^}]+)}')
    
    fields = []
    actions = []
    
    fields_match = field_pattern.search(table_body)
    actions_match = action_pattern.search(table_body)

    if fields_match:
        fields = [field.strip() for field in fields_match.group(1).split(';') if field.strip()]
    
    if actions_match:
        actions = [action.strip() for action in actions_match.group(1).split(';') if action.strip()]
    
    return fields, actions


def get_key_width(key_param):
    key_width = 0
    headers = retrieve_object('headers')
    for param in key_param:
        key_match = param.split(':')[0]
        if key_match:
            l = key_match.split('.')
            hdr = l[-2].strip()
            field = l[-1].strip()
            # TODO: Fix metadata
            if 'meta' in hdr:
                continue
            w = headers.get(hdr).get(field)
            if w:
                key_width += w

    return key_width


def gen_matchkey_code(key_param):
    key_width = 0
    body_code = ''
    headers = retrieve_object('headers')
    for param in key_param:
        l = param.split('.')
        hdr = l[-2].strip()
        field = l[-1].strip()
        # TODO: Fix metadata
        if 'meta' in hdr.lower():
            continue
        w = headers[hdr][field]
        if w:
            key_width += w
            body_code += f'\t\tkey.range({key_width-1}, {key_width-w}) = pkt.{hdr}.{field};\n'

    header_code = f'\tap_uint<{key_width}> get_matchkey(Packet &pkt) const {{\n'
    body_code = f'\t\tap_uint<{key_width}> key;\n' + body_code
    tail_code = '\t\treturn key;\n\t}\n'
    code = header_code + body_code + tail_code
    return code, key_width


def gen_apply_code(table_param, actions_json, key_width):
    value_width_offset = math.ceil(math.log2(len(actions_json))) + 1
    max_value_width = 0
    default_action = table_param['default_action']
    default_call = ''
    switch_code = '\t\t\tswitch (action_id) {\n'
    action_names = table_param['actions']
    for action_name, action_info in actions_json.items():
        if action_name in action_names:
            total_width = action_info['total_width']
            if max_value_width < total_width:
                max_value_width = total_width
            idx = value_width_offset
            comment = ''
            args = ''
            if action_name != 'NoAction':
                comment = '// pkt'
                for arg_name, arg_width in action_info.get('args', []).items():
                    args += f', value.range({arg_width+idx-1}, {idx})'
                    comment += f', {arg_name}'
                    idx += arg_width 
                args = f'pkt{args}' 
            action_call_code = f'\t\t\tcase {action_info["id"]}: {action_name}({args}); break; {comment}\n'
            switch_code += action_call_code
            if default_action == action_name:
                default_call = f'\t\t\t{default_action}({args}); {comment}\n'
    max_value_width += value_width_offset
    header_code = '\tbool apply(const unsigned int *memPtr, Packet &pkt) {\n'
    action_id = f'\t\t\taction_id = value.range({value_width_offset-1}, {1});\n'
    switch_code += f'\t\t\tdefault: break;\n\t\t\t}}\n'
    if_code = f'\t\tif (found) {{\n{action_id}{switch_code}\t\t}}'
    else_code = f' else {{\n{default_call}\t\t}}\n'
    body_code = f'\t\tconst ap_uint<{key_width}> key = get_matchkey(pkt);\n'
    body_code += f'\t\tap_uint<{max_value_width}> value;\n'
    body_code += f'\t\tbool found = impl.search_entry(memPtr, key, value);\n'
    body_code += if_code + else_code
    tail_code = '\t\treturn found;\n\t}\n'
    code = header_code + body_code + tail_code
    return code, max_value_width


def gen_update_code(key_width, value_width):
    code = '''
    void update_table(unsigned int *memCtrl, unsigned int &ctrl) {
		const unsigned char func_type = static_cast<unsigned char>(ctrl & 0x0FF);
		const short entry_count = static_cast<short>((ctrl >> 8) & 0x0FFFF);
		for (int i = 0; i < entry_count; i ++) {
            '''
    nb_words = math.ceil((key_width + value_width) / 32);
    code += f'ap_uint<{32 * nb_words}> entry(0);\n\t\t\t'
    lines = []
    for j in range(nb_words):
        high = (j + 1) * 32 - 1
        low = j * 32
        lines.append(f'entry.range({high}, {low}) = memCtrl[i * {nb_words} + {j}];')

    code += '\n\t\t\t'.join(lines)
    code += '\n\t\t\tif (func_type & 0x01) {\n'
    code += f'\t\t\t\timpl.insert_entry(entry.range({key_width+value_width-1}, {value_width}), entry.range({value_width-1}, 0));\n'
    code += '\t\t\t} else if (func_type & 0x02) {\n'
    code += f'\t\t\t\timpl.delete_entry(entry.range({key_width+value_width-1}, {value_width}), entry.range({value_width-1}, 0));\n'
    code += '\t\t\t}\n\t\t}\n\t}\n'

    return code


def gen_tables_code(params, dir_path):
    actions_json = retrieve_object('actions')
    t_sizes = {}
    t_key_widths = {}
    t_value_width = {}
    t_types = []
    table_header = '\n'
    for param in params:
        table_name = param["table_name"]
        table_struct_name = f'{table_name.capitalize()}Table'
        ctor_code = f'\t{table_struct_name}() {{}}\n'
        dtor_code = f'\t~{table_struct_name}() {{}}\n'
        matchkey_code, key_width = gen_matchkey_code(param['key'])
        apply_code, value_width = gen_apply_code(param, actions_json, key_width)
        update_code = gen_update_code(key_width, value_width)
        impl_code = f'\tMatchActionTable<TS_{table_struct_name}, MS_{table_struct_name}, AS_{table_struct_name}, TYPE_{table_struct_name}> impl;'
        
        t_sizes[f'TS_{table_struct_name}'] = param["size"]
        t_key_widths[f'MS_{table_struct_name}'] = key_width
        t_value_width[f'AS_{table_struct_name}'] = value_width
        t_types.append(f'TYPE_{table_struct_name}')
        #t_sizes.append(f'constexpr int TS_{table_struct_name} = {param["size"]}')
        #t_key_widths.append(f'constexpr int MS_{table_struct_name} = {key_width}')
        #t_value_width.append(f'constexpr int AS_{table_struct_name} = {value_width}')
        #t_types.append(f'TYPE_{table_struct_name}')

        # fields_code = "\n".join([f"\tap_uint<{bitwidth}> {field_name};" for field_name, bitwidth in list(fields.items())])
        
        table_code = f'#ifndef {table_name.upper()}_TABLE_H\n' + \
           f'#define {table_name.upper()}_TABLE_H\n\n' + \
           f'#include "MatchActionTable.h"\n\n' + \
           f'#include "../ingress/Actions.h"\n\n' + \
           f'class {table_struct_name} {{\npublic:\n' + \
           ctor_code + dtor_code + matchkey_code + apply_code + update_code + impl_code + '\n};\n\n' + \
           f'#endif // {table_name.upper()}_TABLE_H\n'

        with open(f'{dir_path}/{table_struct_name}.h', 'w') as f:
            f.write(table_code)

        table_header += f'#include "{table_struct_name}.h"\n'

    table_header += '#ifndef TABLE_H\n' + \
                    '#define TABLE_H\n' + \
                    table_header + \
                    '\n#endif // TABLE_H\n'
    with open(f'{dir_path}/Table.h', 'w') as f:
            f.write(table_header)

    table_const = {
        'table_size': t_sizes,
        'table_matchkey_width': t_key_widths,
        'table_action_width': t_value_width,
        'table_types': t_types
    }
    store_object(table_const, 'table_const')


def extract_explicit_table_names(p4_code):
    tables_names = []
    table_start_pattern = re.compile(r'table\s+(\w+)\s*{')
    index = 0
    while  index < len(p4_code):
        match = table_start_pattern.search(p4_code, index)
        if not match:
            break
        index = match.end()
        matched = match.group(1).strip()
        tables_names.append(matched)
    return tables_names


def extract_table_params_v2(p4src, json):
    params = []
    table_names = extract_explicit_table_names(p4src)
    pipes = json.get('pipelines', [])
    for pipe in pipes:
        tables = pipe.get('tables', [])
        for table in tables:
            t_name = table['name'].split('.')[-1]
            if t_name not in table_names:
                continue
            t_max_size = table['max_size']
            t_action_names = [ac.split('.')[-1] for ac in table['actions']]
            t_action_ids = table['action_ids'] 
            t_actions = {ac: ac_id for ac, ac_id in zip(t_action_names, t_action_ids)}
            t_keys = []
            for key in table['key']:
                target = '.'.join(key['target'])
                t_keys.append(target)

            t_default_action = 'NoAction'
            t_default_id = table['default_entry']['action_id']
            for ac_name, ac_id in t_actions.items():
                if ac_id == t_default_id:
                    t_default_action = ac_name
            params.append({
                'table_name': t_name,
                'key': t_keys,
                'actions': t_actions,
                'size': t_max_size,
                'default_action': t_default_action
            })
    store_object(params, 'tables')
    return params


def generate_tables(p4src, json, build_dir, src_dir):
    dir_path = f'{build_dir}/table'
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)
    #tables = extract_tables(p4src)
    #params = extract_table_params(tables)
    params = extract_table_params_v2(p4src, json)
    gen_tables_code(params, dir_path)
    copy_file(f'{src_dir}/templated/MatchActionTable.h', f'{dir_path}/MatchActionTable.h')
    
