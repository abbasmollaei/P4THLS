#ifndef PACKET_PARSER_H
#define PACKET_PARSER_H

#include "SubParser.h"
    

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
}

void forward_parser(hls::stream<Packet> &qpkt, unsigned char *buff)
{
    bool accept = false;
	bool reject = false;
	ParserState state = P_START;
	Packet pkt;

	int idx = 0;
    switch (state) {
    case P_ETHERNET: idx += parse_ethernet(&buff[idx], pkt, state); break;
    case P_ACCEPT:   accept = true;    break;
    case P_REJECT:   reject = true;    break;
    default:         state = P_REJECT; break;
    }

    switch (state) {
    case P_IPV4: idx += parse_ipv4(&buff[idx], pkt, state); break;
    case P_ACCEPT:   accept = true;    break;
    case P_REJECT:   reject = true;    break;
    default:         state = P_REJECT; break;
    }

    switch (state) {
    case P_UDP: idx += parse_udp(&buff[idx], pkt, state); break;
    case P_ACCEPT:   accept = true;    break;
    case P_REJECT:   reject = true;    break;
    default:         state = P_REJECT; break;
    }

    switch (state) {
    case P_ACCEPT:   accept = true;    break;
    case P_REJECT:   reject = true;    break;
    default:         state = P_REJECT; break;
    }

    return accept;

void packet_parser(
                    hls::stream<axi_chunk> &in0,
                    hls::stream<axi_chunk> &in1,
                    hls::stream<Packet> &qpkt)
{
#pragma HLS PIPELINE II=1

    unsigned char buff[nbInputPorts][maxPacketBytes] ={{0}};
#pragma HLS ARRAY_PARTITION variable=buff type=complete dim=0

    bool valid[nbInputPorts] = {0};
#pragma HLS ARRAY_PARTITION variable=valid type=complete dim=0
    valid[0] = read_stream(in0, buff[0]);
    valid[1] = read_stream(in1, buff[1]);
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
    