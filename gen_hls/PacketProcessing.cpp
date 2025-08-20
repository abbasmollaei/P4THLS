#include "PacketProcessing.h"
#include "parser/PacketParser.h"
#include "deparser/PacketDeparser.h"
#include "ingress/IngressProcessing.h"
#include <iostream>

void packet_processing(
                        hls::stream<axi_chunk> &in0,
                        hls::stream<axi_chunk> &in1,                        hls::stream<axi_chunk> &out0,
                        hls::stream<axi_chunk> &out1,                        unsigned int *memCtrl,
                        const unsigned int ctrl,
                        const unsigned int flag) {
#pragma HLS INTERFACE m_axi port=memCtrl offset=slave bundle=gmem0#pragma HLS INTERFACE axis port=in0
#pragma HLS INTERFACE axis port=in1
#pragma HLS INTERFACE axis port=out0
#pragma HLS INTERFACE axis port=out1
#pragma HLS INTERFACE s_axilite port=return
#pragma HLS DATAFLOW

	hls::stream<Packet> buff_pkt_in("buff_pkt_in");
	hls::stream<Packet> buff_pkt_out("buff_pkt_out");

#pragma HLS STREAM variable=buff_pkt_in depth=16
#pragma HLS STREAM variable=buff_pkt_out depth=16
	packet_parser(in0, in1, buff_pkt_in);
	ingress_processing(buff_pkt_in, buff_pkt_out, memCtrl, ctrl, flag);
	packet_deparser(out0, out1, buff_pkt_out);
}
