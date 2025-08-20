#ifndef ACTIONS_H
#define ACTIONS_H

#include "../header/Packet.h"
    
void allow_ip(Packet &pkt) {
	ip_allowed = true;
}
void drop(Packet &pkt) {
	standard_metadata.drop = 1;
}
void forward(Packet &pkt, ap_uint<16> port) {
	pkt.udp.dstPort = port;
}

#endif // ACTIONS_H