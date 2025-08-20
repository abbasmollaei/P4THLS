import json
import os
import re
from sys_utils import *


def gen_lookup_entry():
    code = '''
template<int MS, int AS>
struct LookupEntry : public LookupEntryBase {
	LookupEntry(ap_uint<MS> ikey, ap_uint<AS> ivalue, bool ivalid) :
		key(ikey),
		value(ivalue),
		valid(ivalid) {	}
	LookupEntry() {}
	ap_uint<MS> key;
	ap_uint<AS> value;
	bool valid;
};
    '''
    return code

def gen_const(inport, outport, bwidth, mtype):
    tables_const = retrieve_object('table_const')
    table_sizes = tables_const.get('table_size', [])
    table_key_width = tables_const.get('table_matchkey_width', [])
    table_value_width = tables_const.get('table_action_width', [])
    table_types = tables_const.get('table_types', [])
    code = f'const int BW = {bwidth};\n'
    code += f'const int BB = BW / 8;\n'
    code += 'const ap_uint<BB> ONES = (ap_uint<BB+1>(1) << BB) - 1;\n\n'
    code += 'const int maxPacketBytes = 128;'
    code += f'constexpr int nbInputPorts = {inport};\n'
    code += f'constexpr int nbInputPorts = {outport};\n\n'
    code += f'#define {mtype.upper()}\n\n'
    for key, value in table_sizes.items():
        code += f'constexpr int {key} = {value};\n'
    code += '\n'
    for key, value in table_key_width.items():
        code += f'constexpr int {key} = {value};\n'
    code += '\n'
    for key, value in table_value_width.items():
        code += f'constexpr int {key} = {value};\n'
    code += '\nenum MatchActionTableType : int {\n'
    for i in range(0, len(table_types)):
        code += f'\t{table_types[i]} = {i},\n'
    code += f'\tTABLE_COUNT = {len(table_types)}\n}};\n'

    return code


def gen_code(dir_path, inport, outport, bwidth, mtype):
    code = '#ifndef SHARED_H\n' + \
       '#define SHARED_H\n\n' + \
       '#include <ap_axi_sdata.h>\n\n' + \
       'typedef ap_axiu<64,1,1,1> axi_chunk;\n\n' + \
       gen_const(inport, outport, bwidth, mtype) + \
       gen_lookup_entry() + \
       '\n#endif // SHARED_H\n'

    with open(f'{dir_path}/Shared.h', 'w') as f:
        f.write(code)


def generate_common(build_dir, inport, outport, bwidth, mtype):
    dir_path = f'{build_dir}/common'
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)
    gen_code(dir_path, inport, outport, bwidth, mtype)
    
