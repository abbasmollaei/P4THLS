import json
import os

def gen_read_stream_code():
    return '''
void read_stream(hls::stream<axi_chunk> &input, unsigned char *buff)
{
	int count = 0;
	bool last = false;
	PS_1: while (!last && !input.empty()) {
#pragma HLS LOOP_TRIPCOUNT min=512/BW max=512/BW avg=512/BW
		axi_chunk chunk;
		input.read(chunk);
		last = chunk.last;
		PS_2: for (int i = 0; i < BB; i++) {
#pragma HLS UNROLL factor=BB
            buff[count + i] = chunk.data.range(i * 8 + 7, i * 8);
        }
        count += BB;
	}

    return (count != 0);
}'''

def extract_graph(json):
    graph = {}
    states = json['parsers'][0]['parse_states']
    for state in states:
        name = state['name']
        transitions = state['transitions']
        next_states = []
        for trans in transitions:
            val = trans['value']
            nxt = trans['next_state']
            if nxt is not None:
                next_states.append(nxt)
            else:
                next_states.append('ACCEPT')
        graph[name] = next_states
    return graph


def get_level_graph(graph):
    level_graph = []
    cur_nodes = set(['start'])
    level_graph.append(cur_nodes)
    while len(cur_nodes) > 1 or 'ACCEPT' not in cur_nodes:
        level_set = set()
        for node in cur_nodes:
            if 'ACCEPT' in node:
                level_set.add('ACCEPT')
            else:
                for nxt in graph[node]:
                    level_set.add(nxt)
        level_graph.append(level_set)
        cur_nodes = level_set
    # Eliminate reapeted nodes from last to first
    seen_nodes = set()
    for i in range(len(level_graph)-1, -1, -1):
        unique_nodes = set()
        for node in level_graph[i]:
            if 'ACCEPT' in node:
                unique_nodes.add(node)
                continue
            elif node not in seen_nodes:
                unique_nodes.add(node)
                seen_nodes.add(node)
        level_graph[i] = unique_nodes

    return level_graph

def gen_states_code(enum_states):
    s = 'enum ParserState {\n'
    for i in range(len(enum_states)):
        s += f'    {enum_states[i]}'
        if i < len(enum_states)-1:
            s += f','
        s += '\n'
    s += '};\n'
    return s


def gen_subparser_code(json, dir_path):
    code = ''
    enum_states = ['P_ACCEPT', 'P_REJECT']
    states = json['parsers'][0]['parse_states']
    state_to_headers = {}
    for state in states:
        st_name = state['name']
        state_to_headers[st_name] = []
        key = state['transition_key']
        key_phrase = ''
        if key:
            key_phrase = '.'.join(key[0]['value'])
        ops = state['parser_ops'] 
        op = ops[0]
        if op['op'] in 'extract':
            header_name = op['parameters'][0]['value']
            state_to_headers[st_name].append(header_name)
            enum_states.append(f'P_{header_name.upper()}')
            transitions = state['transitions']
            next_states = ''
            only_final_edge = False
            has_final_edge = False
            for trans in transitions:
                val = trans['value']
                nxt = trans['next_state']
                if nxt is not None:
                    next_states += f'    case {val}: state = P_{header_name.upper()};\n'
                else:
                    has_final_edge = True
                    if len(transitions) > 1:
                        next_states += f'    default: state = P_ACCEPT;\n'
                    else:
                        next_states += f'    state = P_ACCEPT;\n'
                        only_final_edge = True
                        break

            parse_func =  f'int parse_{header_name}(unsigned char *buff, Packet &pkt, ParserState &state) {{\n'
            parse_func += f'    deserialize(buff, pkt.{header_name});\n'
            parse_func += f'    pkt.setValid(H_{header_name.upper()});\n'
            parse_func += f'    switch (pkt.{key_phrase}) {{\n' if not only_final_edge else ''
            parse_func += next_states
            parse_func += '    }\n' if not only_final_edge else ''
            parse_func += f'    return H_{header_name.upper()}_SIZE;\n'
            parse_func += '}\n\n'
        code += parse_func

    enum_code = gen_states_code(enum_states)

    s_begin = '''#ifndef SUB_PARSER_H
#define SUB_PARSER_H

#include "../common/Shared.h"
#include "../header/Packet.h"
    '''
    s_end = '#endif // SUB_PARSER_H'
    code = f'{s_begin}\n{enum_code}\n{code}\n{s_end}'

    with open(f'{dir_path}/SubParser.h', 'w') as f:
        f.write(code)
    return state_to_headers


def gen_fwd_parser_code(graph, state_to_headers):
    code = '''
void forward_parser(hls::stream<Packet> &qpkt, unsigned char *buff)
{
    bool accept = false;
	bool reject = false;
	ParserState state = P_START;
	Packet pkt;

	int idx = 0;
'''
    for level in graph:
        layer_code = '    switch (state) {\n'
        for node in level:
            if 'ACCEPT' not in node:
                headers = state_to_headers[node]
                if headers:
                    header = headers[0]
                    layer_code += f'    case P_{header.upper()}: idx += parse_{header}(&buff[idx], pkt, state); break;\n'
        layer_code += '    case P_ACCEPT:   accept = true;    break;\n'
        layer_code += '    case P_REJECT:   reject = true;    break;\n'
        layer_code += '    default:         state = P_REJECT; break;\n'
        layer_code += '    }\n\n'
        code += layer_code

    code += '    return accept;'
    return code


def gen_main_parser_code(json, state_to_headers, dir_path, inport):
    graph = extract_graph(json)
    level_graph = get_level_graph(graph)
    fwd_parser_code = gen_fwd_parser_code(level_graph, state_to_headers)
    read_stream_code = gen_read_stream_code()

    s_begin = '''#ifndef PACKET_PARSER_H
#define PACKET_PARSER_H

#include "SubParser.h"
    '''
    s_end = '''
void packet_parser(
'''
    s_end += "\n".join([f'{" " * 20}hls::stream<axi_chunk> &in{i},' for i in range(inport)])
    s_end += f'\n{" " * 20}' + '''hls::stream<Packet> &qpkt)
{
#pragma HLS PIPELINE II=1

    unsigned char buff[nbInputPorts][maxPacketBytes] ={{0}};
#pragma HLS ARRAY_PARTITION variable=buff type=complete dim=0

    bool valid[nbInputPorts] = {0};
#pragma HLS ARRAY_PARTITION variable=valid type=complete dim=0
'''
    s_end += "\n".join([f'    valid[{i}] = read_stream(in{i}, buff[{i}]);' for i in range(inport)])
    s_end += '''
	for (int i = 0; i < nbInputPorts; i ++) {
		if (valid[i]) {
			Packet pkt;
			forward_parser(pkt, buff[i]);
			pkt.standardmetadata.ingress_port = i;
			pkt.standardmetadata.egress_port = i;
			qpkt.write(pkt);
		}
	}
}

#endif // PACKET_PARSER_H
    '''
    code = f'{s_begin}\n{read_stream_code}\n{fwd_parser_code}\n{s_end}'
    with open(f'{dir_path}/PacketParser.h', 'w') as f:
        f.write(code)
    return


def generate_parser(json, build_dir, inport):
    dir_path = f'{build_dir}/parser'
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)
    state_to_headers = gen_subparser_code(json, dir_path)
    gen_main_parser_code(json, state_to_headers, dir_path, inport)
    
