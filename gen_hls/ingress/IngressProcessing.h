#ifndef INGRESS_PROCESSING_H
#define INGRESS_PROCESSING_H

#include "../common/Shared.h"
#include "../header/Packet.h"
#include "../table/Table.h"

void ingress_control(Packet &pkt, unsigned int *memPtr, unsigned int flag)
{
#pragma HLS PIPELINE
	static Ip_firewallTable ip_firewall;
	static Udp_port_firewallTable udp_port_firewall;

#if defined(URAM)
#pragma HLS bind_storage variable=ip_firewall.impl.lookup type=ram_2p impl=uram
#pragma HLS bind_storage variable=udp_port_firewall.impl.lookup type=ram_2p impl=uram
#elif defined(BRAM)
#pragma HLS bind_storage variable=ip_firewall.impl.lookup type=ram_2p impl=bram
#pragma HLS bind_storage variable=udp_port_firewall.impl.lookup type=ram_2p impl=bram
#else
#pragma HLS bind_storage variable=ip_firewall.impl.lookup type=ram_2p impl=lutram
#pragma HLS bind_storage variable=udp_port_firewall.impl.lookup type=ram_2p impl=lutram
#endif

    if (flag != 0) {
		if (flag & (0 << 0x01)) ip_firewall.update_table(memCtrl, ctrl);
		if (flag & (0 << 0x01)) udp_port_firewall.update_table(memCtrl, ctrl);
    else {
	if (pkt.isValid(H_UDP)) {
	    ip_firewall.apply(memPtr, pkt);
	    if (ip_allowed) {
	        udp_port_firewall.apply(memPtr, pkt);
	    }
	}
    }
}

void ingress_processing(hls::stream<Packet> &qpkt1, 
                        hls::stream<Packet> &qpkt2, 
                        unsigned int *memCtrl, 
                        unsigned int ctrl, 
                        unsigned int flag)
{
#pragma HLS PIPELINE
	if (!qpkt1.empty()) {
		Packet pkt;
		qpkt1.read(pkt);

		ingress_control(pkt, memCtrl, ctrl, flag);
        
        if (pkt.standardmetadata.drop == 0)
		    qpkt2.write(pkt);
	}
}
    
#endif // INGRESS_PROCESSING_H
