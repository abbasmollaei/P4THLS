#ifndef IP_FIREWALL_TABLE_H
#define IP_FIREWALL_TABLE_H

#include "MatchActionTable.h"

#include "../ingress/Actions.h"

class Ip_firewallTable {
public:
	Ip_firewallTable() {}
	~Ip_firewallTable() {}
	ap_uint<64> get_matchkey(Packet &pkt) const {
		ap_uint<64> key;
		key.range(31, 0) = pkt.ipv4.srcAddr;
		key.range(63, 32) = pkt.ipv4.dstAddr;
		return key;
	}
	bool apply(const unsigned int *memPtr, Packet &pkt) {
		const ap_uint<64> key = get_matchkey(pkt);
		ap_uint<3> value;
		bool found = impl.search_entry(memPtr, key, value);
		if (found) {
			action_id = value.range(2, 1);
			switch (action_id) {
			case 0: allow_ip(pkt); break; // pkt
			case 1: drop(pkt); break; // pkt
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
            ap_uint<96> entry(0);
			entry.range(31, 0) = memCtrl[i * 3 + 0];
			entry.range(63, 32) = memCtrl[i * 3 + 1];
			entry.range(95, 64) = memCtrl[i * 3 + 2];
			if (func_type & 0x01) {
				impl.insert_entry(entry.range(66, 3), entry.range(2, 0));
			} else if (func_type & 0x02) {
				impl.delete_entry(entry.range(66, 3), entry.range(2, 0));
			}
		}
	}
	MatchActionTable<TS_Ip_firewallTable, MS_Ip_firewallTable, AS_Ip_firewallTable, TYPE_Ip_firewallTable> impl;
};

#endif // IP_FIREWALL_TABLE_H
