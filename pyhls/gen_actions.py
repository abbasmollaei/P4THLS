import json
import os
import re
from sys_utils import *

# Function to extract the action definition by name, preserving indentation
def extract_action_definition(p4_code, action_name, action_args):
    if action_name == 'NoAction':
        return 'void NoAction() { \n}'
    # Define a regex pattern to capture the action definition, allowing for excess spaces and preserving indentation
    pattern1 = rf'action\s+{action_name}\s*\(.*?\)\s*\{{(.*?)\}}'
    # Use re.DOTALL to match across multiple lines and preserve indentation
    match = re.search(pattern1, p4_code, re.DOTALL)
    if match:
        # The full action definition, including the header and body
        action_header = 'Packet &pkt'
        for arg_name, arg_width in action_args.items():
            action_header = f'{action_header}, ap_uint<{arg_width}> {arg_name}'
        action_header = f'void {action_name}({action_header}) {{'
        action_body = f'\t{match.group(1).strip()}'  # Keep the body indented as it is
        action_body = re.sub(r'\n\s*\n+', '\n', action_body)
        action_code = f'{action_header}\n{action_body}\n}}'
        
        pattern2 = r'bit<(\d+)>'
        action_code = re.sub(pattern2, r'ap_uint<\1>', action_code)
        return action_code
    else:
        return ''


# def get_action_code_block(p4_json, action_name):
#     """Retrieve the code block for a given action from the P4 JSON."""
#     # Iterate through all actions in the P4 JSON
#     for action in p4_json.get("actions", []):
#         if action.get("name") == action_name:
#             return action.get("primitives", [])
#     return []

def replace_headers_variable(hdr_name, action_code):
    # This ensures only the structure accesses like 'hdr.' or 'hdr[' are replaced
    # Word boundaries ensure that we are replacing the variable only when used correctly
    pattern = rf'\b{hdr_name}\b(?=\s*[\.\[])'  # Matches 'hdr.' or 'hdr['
    # Perform the substitution safely
    modified_code = re.sub(pattern, 'pkt', action_code)
    return modified_code


def replace_setValid(action_code):
    # Define the regex pattern to match pkt.xxx.setValid();
    pattern = r'pkt\.(\w+)\.setValid\(\);'
    # Replace with pkt.setValid(H_XXX);
    def replacer(match):
        header_type = match.group(1)  # Extract xxx
        capitalized_header = header_type.upper()  # Convert to uppercase
        return f'pkt.setValid(H_{capitalized_header});'

    # Perform the substitution using the regex pattern and replacer function
    updated_code = re.sub(pattern, replacer, action_code)
    return updated_code


def replace_setInvalid(action_code):
    # Define the regex pattern to match pkt.xxx.setInvalid();
    pattern = r'pkt\.(\w+)\.setInvalid\(\);'
    # Replace with pkt.setInvalid(H_XXX);
    def replacer(match):
        header_type = match.group(1)  # Extract xxx
        capitalized_header = header_type.upper()  # Convert to uppercase
        return f'pkt.setInvalid(H_{capitalized_header});'

    # Perform the substitution using the regex pattern and replacer function
    updated_code = re.sub(pattern, replacer, action_code)
    return updated_code


def get_headers_variable_name(p4src):
    header_var_pattern = r'inout\s+headers\s+(\w+)'  # Looks for 'inout headers hdr'
    header_var_match = re.search(header_var_pattern, p4src)
    if not header_var_match:
        return ''
    hdr_name = header_var_match.group(1)
    return hdr_name


def extract_actions(p4src, json):
    actions_with_code = {}
    control_name = 'ingress'
    hdr_name = get_headers_variable_name(p4src)
    actions = json.get("actions", [])
    actions_json = {}
    action_id = 0
    # Find the control block with the name 'control_name'
    for control in json.get("pipelines", []):
        if control.get("name") == control_name:
            # Iterate over the tables in the control block
            for table in control.get("tables", []):
                # Get the actions defined for the table
                for action_name in table.get("actions", []):
                    if action_name in actions_with_code:
                        continue
                    for action in actions:
                        if action_name == action.get('name'):
                            # Unify the Nop and NoAction
                            parts = action_name.split('.')
                            action_abs_name = parts[-1]
                            if action_abs_name in ['Nop', 'NoAction']:
                                action_name = re.sub(r'(\w*\.)?(Nop)', r'\1NoAction', action_name)
                                action_abs_name = 'NoAction'
                                if action_abs_name in actions_with_code:
                                    break

                            action_args = {ht['name']: ht['bitwidth'] for ht in action['runtime_data']}
                            code_step1 = extract_action_definition(p4src, action_abs_name, action_args)
                            if code_step1:
                                code_step2 = replace_headers_variable(hdr_name, code_step1)
                                code_step3 = replace_setValid(code_step2)
                                code_step4 = replace_setInvalid(code_step3)
                                actions_with_code[action_name] = code_step4
                                total_width = sum(action_args.values())
                                actions_json[action_abs_name] = {'id': action_id, 'total_width': total_width, 'args': action_args}
                                action_id += 1
                            break

    store_object(actions_json, 'actions')
    return actions_with_code


def gen_actions_code(actions, dir_path):
    s_begin = '''#ifndef ACTIONS_H
#define ACTIONS_H

#include "../header/Packet.h"
    '''
    s_end = '#endif // ACTIONS_H'
    s_body = ''
    for name, body in actions.items():
        if body:
            s_body += f'{body}\n'
    code = f'{s_begin}\n{s_body}\n{s_end}'
    with open(f'{dir_path}/Actions.h', 'w') as f:
        f.write(code)
    return


def generate_actions(p4src, json, build_dir):
    dir_path = f'{build_dir}/ingress'
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)
    actions = extract_actions(p4src, json)
    gen_actions_code(actions, dir_path)
    
