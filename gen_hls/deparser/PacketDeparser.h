#ifndef PACKET_DEPARSER_H
#define PACKET_DEPARSER_H

#include "SubDeparser.h"
    
void packet_deparser(
                      hls::stream<axi_chunk> &out0,
                      hls::stream<axi_chunk> &out1,
                      hls::stream<Packet> &qpkt)
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
            if (egress_port == 1)
                out1.write(chunk);
            else
                out0.write(chunk);
		}
	}
}

#endif // PACKET_DEPARSER_H
    