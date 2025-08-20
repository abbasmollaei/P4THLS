#ifndef UDP_PORT_FIREWALL_TABLE_H
#define UDP_PORT_FIREWALL_TABLE_H

#include "MatchActionTable.h"

#include "../ingress/Actions.h"

class Udp_port_firewallTable {
public:
	Udp_port_firewallTable() {}
	~Udp_port_firewallTable() {}
	ap_uint<32> get_matchkey(Packet &pkt) const {
		ap_uint<32> key;
		key.range(15, 0) = pkt.udp.srcPort;
		key.range(31, 16) = pkt.udp.dstPort;
		return key;
	}
	bool apply(const unsigned int *memPtr, Packet &pkt) {
		const ap_uint<32> key = get_matchkey(pkt);
		ap_uint<19> value;
		bool found = impl.search_entry(memPtr, key, value);
		if (found) {
			action_id = value.range(2, 1);
			switch (action_id) {
			case 1: drop(pkt); break; // pkt
			case 2: forward(pkt, value.range(18, 3)); break; // pkt, port
			default: break;
			}
		} else {
			drop(pkt); // pkt
		}
		return found;
	}

    void update_table(unsigned int *memCtrl, unsigned int &ctrl) {
		const unsigned char func_type = static_cast<unsigned char>(ctrl & 0x0FF);
		const short entry_count = static_cast<short>((ctrl >> 8) & 0x0FFFF);
		for (int i = 0; i < entry_count; i ++) {
            ap_uint<64> entry(0);
			entry.range(31, 0) = memCtrl[i * 2 + 0];
			entry.range(63, 32) = memCtrl[i * 2 + 1];
			if (func_type & 0x01) {
				impl.insert_entry(entry.range(50, 19), entry.range(18, 0));
			} else if (func_type & 0x02) {
				impl.delete_entry(entry.range(50, 19), entry.range(18, 0));
			}
		}
	}
	MatchActionTable<TS_Udp_port_firewallTable, MS_Udp_port_firewallTable, AS_Udp_port_firewallTable, TYPE_Udp_port_firewallTable> impl;
};

#endif // UDP_PORT_FIREWALL_TABLE_H
