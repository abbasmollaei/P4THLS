import json
import os
import re
import shutil

info_dir = ''

def set_info_dir(dir):
    global info_dir
    info_dir = dir


def store_object(obj, name):
    with open(f'{info_dir}/{name}.json', 'w') as f:
        json.dump(obj, f, indent=4)


def retrieve_object(name):
    with open(f'{info_dir}/{name}.json', 'r') as f:
        obj = json.load(f)
    return obj


def read_file(file_path):
    with open(file_path, 'r') as f:
        file = f.read()
    if not file:
        print('The entered source file is corrupted!')
    return file


def read_json(json_path):
    with open(json_path, 'r') as f:
        file = json.load(f)
    if not file:
        print('The entered json file is corrupted!')
    return file


def make_dir(dir):
    if not os.path.isdir(dir):
        os.makedirs(dir)
        

def copy_file(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy(src, dst)


def clean_env(dir_env):
    try:
        for root, dirs, files in os.walk(dir_env):
            print(root)
            for file in files:
                # print(f'File: {os.path.join(root, file)}')
                os.remove(os.path.join(root, file))
            for dir in dirs:
                # print(f'Dir: {os.path.join(root, dir)}')
                shutil.rmtree(os.path.join(root, dir))
    except FileNotFoundError:
        print(f"Directory '{dir}' not found.")


# code based functions
# Function to remove comments (single-line and multi-line) from the P4 code
def remove_comments(code):
    # Remove single-line comments (//) and multi-line comments (/* */)
    code = re.sub(r'//.*', '', code)  # Remove single-line comments
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)  # Remove multi-line comments
    return code


# Function to remove extra empty lines
def remove_extra_empty_lines(code):
    lines = code.splitlines()
    # Filter out lines that are empty or contain only whitespace
    cleaned_lines = [line for line in lines if line.strip() != '']
    # Join lines back together with a single newline between them
    return '\n'.join(cleaned_lines)


# Custom function to beautify code with 4-space indentation
def beautify_code(code):
    lines = code.splitlines()
    beautified_code = []
    indent_level = 0
    indent_space = '    '  # 4 spaces for each indent level

    for line in lines:
        stripped_line = line.strip()

        if stripped_line == '':
            # Skip empty lines
            continue

        # If the line starts with a closing brace, reduce the indent level first
        if stripped_line.startswith('}'):
            indent_level -= 1

        # Apply the indentation
        beautified_line = f"{indent_space * indent_level}{stripped_line}"
        beautified_code.append(beautified_line)

        # If the line ends with an opening brace, increase the indent level after applying the current indentation
        if stripped_line.endswith('{'):
            indent_level += 1

    # Join the lines back with newline characters
    return '\t' + '\n\t'.join(beautified_code)


# Function to find a matching closing brace for a given opening brace
def find_matching_brace(code, start_index):
    open_braces = 0
    for i in range(start_index, len(code)):
        if code[i] == '{':
            open_braces += 1
        elif code[i] == '}':
            open_braces -= 1
            if open_braces == 0:
                return i
    return -1
