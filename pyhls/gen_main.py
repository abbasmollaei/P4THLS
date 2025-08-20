import json
import os
import re
from sys_utils import *

def gen_prototype(nb_in, nb_out):
    blank = ' ' * 24
    code = 'void packet_processing(\n'
    code += "\n".join([f'{blank}hls::stream<axi_chunk> &in{i},' for i in range(nb_in)])
    code += "\n".join([f'{blank}hls::stream<axi_chunk> &out{i},' for i in range(nb_out)])
    code += f'{blank}unsigned int *memCtrl,\n'
    code += f'{blank}const unsigned int ctrl,\n'
    code += f'{blank}const unsigned int flag)'
    return code

def gen_main_body(nb_in, nb_out):
    code = gen_prototype(nb_in, nb_out) + ' {\n'
    code += '#pragma HLS INTERFACE m_axi port=memCtrl offset=slave bundle=gmem0'
    for i in range(0, nb_in):
        code += f'#pragma HLS INTERFACE axis port=in{i}\n'
    for i in range(0, nb_in):
        code += f'#pragma HLS INTERFACE axis port=out{i}\n'
    code += '#pragma HLS INTERFACE s_axilite port=return\n'
    code += '#pragma HLS DATAFLOW\n\n'
    code += '\thls::stream<Packet> buff_pkt_in("buff_pkt_in");\n'
    code += '\thls::stream<Packet> buff_pkt_out("buff_pkt_out");\n\n'
    code += '#pragma HLS STREAM variable=buff_pkt_in depth=16\n'
    code += '#pragma HLS STREAM variable=buff_pkt_out depth=16\n'

    ti = ", ".join([f"in{i}" for i in range(nb_in)]) + ","
    code += f'\tpacket_parser({ti} buff_pkt_in);\n'
    code += '\tingress_processing(buff_pkt_in, buff_pkt_out, memCtrl, ctrl, flag);\n'
    to = ", ".join([f"out{i}" for i in range(nb_out)]) + ","
    code += f'\tpacket_deparser({to} buff_pkt_out);\n'
    code += '}\n'
    return code


def gen_code(dir_path, nb_in, nb_out):
    code_hdr = '#ifndef PACKET_PROCESSING_H\n' + \
       '#define PACKET_PROCESSING_H\n\n' + \
       '#include "common/Shared.h"\n' + \
       '#include <hls_stream.h>\n\n' + \
       gen_prototype(nb_in, nb_out) + ';\n' + \
       '\n#endif // PACKET_PROCESSING_H\n'

    with open(f'{dir_path}/PacketProcessing.h', 'w') as f:
        f.write(code_hdr)

    code_cpp = '#include "PacketProcessing.h"\n' + \
        '#include "parser/PacketParser.h"\n' + \
        '#include "deparser/PacketDeparser.h"\n' + \
        '#include "ingress/IngressProcessing.h"\n' + \
        '#include <iostream>\n\n' + \
        gen_main_body(nb_in, nb_out)

    with open(f'{dir_path}/PacketProcessing.cpp', 'w') as f:
        f.write(code_cpp)


def generate_main(build_dir, nb_in, nb_out):
    dir_path = f'{build_dir}'
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)
    gen_code(dir_path, nb_in, nb_out)
    
