import json
import os

def gen_subdeparser_code(json, dir_path):
    code = ''
    order = json['deparsers'][0]['order']
    for node in order:
        code += f'    if (pkt.isValid(H_{node.upper()})) {{\n'
        code += f'        serialize(&d[count], pkt.{node});\n'
        code += f'        count += H_{node.upper()}_SIZE;\n'
        code +=  '    }\n'

    s_begin = '''#ifndef SUB_DEPARSER_H
#define SUB_DEPARSER_H

#include "../common/Shared.h"
#include "../header/Packet.h"

int do_deparser(unsigned char *d, Packet &pkt)
{
#pragma HLS INLINE
	int count = 0;
    '''
    s_end = '\treturn count;\n}\n\n#endif // SUB_DEPARSER_H'
    code = f'{s_begin}\n{code}\n{s_end}'

    with open(f'{dir_path}/SubDeparser.h', 'w') as f:
        f.write(code)
    return


def gen_main_deparser_code(json, dir_path, outport):
    code = '''#ifndef PACKET_DEPARSER_H
#define PACKET_DEPARSER_H

#include "SubDeparser.h"
    '''
    code += '''
void packet_deparser(
'''
    code += "\n".join([f'{" " * 22}hls::stream<axi_chunk> &out{i},' for i in range(outport)])
    code += f'\n{" " * 22}' + '''hls::stream<Packet> &qpkt)
{
#pragma HLS PIPELINE II=1
#if defined(__SYNTHESIS__)
	if (!qpkt.empty()) {
#else
	while (!qpkt.empty()) {
#endif
		Packet pkt;
#pragma HLS ARRAY_PARTITION variable=pkt.payload.data type=complete dim=0
		qpkt.read(pkt);
		const int &egress_port = pkt.standardmetadata.egress_port;
		unsigned char d[maxPacketBytes] = {0};
#pragma HLS ARRAY_PARTITION variable=d type=complete dim=0
		int count = do_deparser(d, pkt);
		if (count < 64) {
		    count = 64;
		}
		const int chunk_count = (count + BB - 1) / BB;
		DS_1: for (int n = 0; n < chunk_count; n ++) {
#pragma HLS LOOP_TRIPCOUNT min=PACKET_SIZE/BB max=PACKET_SIZE/BB avg=PACKET_SIZE/BB
//#pragma HLS LOOP_FLATTEN
			axi_chunk chunk;
			DS_2: for (int i = 0; i < BB; i ++) {
#pragma HLS UNROLL factor=BB
				chunk.data.range(i * 8 + 7, i * 8) = d[n * BB + i];
			}
			chunk.last = (n + 1) == chunk_count;
			chunk.keep = chunk.last ? ap_uint<BB>((ap_uint<BB+1>(1) << count) - 1) : ONES;
			count -= BB;
'''

    lines = []
    for i in reversed(range(outport)):
        if i == outport - 1:
            lines.append(f"{' ' * 12}if (egress_port == {i})")
        elif i > 0:
            lines.append(f"{' ' * 12}else if (egress_port == {i})")
        else:
            lines.append(f"{' ' * 12}else")
        lines.append(f"{' ' * 16}out{i}.write(chunk);")

    code += "\n".join(lines)

    code += '''
		}
	}
}

#endif // PACKET_DEPARSER_H
    '''
    with open(f'{dir_path}/PacketDeparser.h', 'w') as f:
        f.write(code)
    return


def generate_deparser(json, build_dir, outport):
    dir_path = f'{build_dir}/deparser'
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)
    gen_subdeparser_code(json, dir_path)
    gen_main_deparser_code(json, dir_path, outport)
    
