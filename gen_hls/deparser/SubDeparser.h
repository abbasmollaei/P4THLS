#ifndef SUB_DEPARSER_H
#define SUB_DEPARSER_H

#include "../common/Shared.h"
#include "../header/Packet.h"

int do_deparser(unsigned char *d, Packet &pkt)
{
#pragma HLS INLINE
	int count = 0;
    
    if (pkt.isValid(H_ETHERNET)) {
        serialize(&d[count], pkt.ethernet);
        count += H_ETHERNET_SIZE;
    }
    if (pkt.isValid(H_IPV4)) {
        serialize(&d[count], pkt.ipv4);
        count += H_IPV4_SIZE;
    }
    if (pkt.isValid(H_UDP)) {
        serialize(&d[count], pkt.udp);
        count += H_UDP_SIZE;
    }

	return count;
}

#endif // SUB_DEPARSER_H