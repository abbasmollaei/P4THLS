#ifndef SHARED_H
#define SHARED_H

#include <ap_axi_sdata.h>

typedef ap_axiu<64,1,1,1> axi_chunk;

const int BW = 128;
const int BB = BW / 8;
const ap_uint<BB> ONES = (ap_uint<BB+1>(1) << BB) - 1;

const int maxPacketBytes = 128;constexpr int nbInputPorts = 2;
constexpr int nbInputPorts = 2;

#define BRAM

constexpr int TS_Ip_firewallTable = 1024;
constexpr int TS_Udp_port_firewallTable = 1024;

constexpr int MS_Ip_firewallTable = 64;
constexpr int MS_Udp_port_firewallTable = 32;

constexpr int AS_Ip_firewallTable = 3;
constexpr int AS_Udp_port_firewallTable = 19;

enum MatchActionTableType : int {
	TYPE_Ip_firewallTable = 0,
	TYPE_Udp_port_firewallTable = 1,
	TABLE_COUNT = 2
};

template<int MS, int AS>
struct LookupEntry : public LookupEntryBase {
	LookupEntry(ap_uint<MS> ikey, ap_uint<AS> ivalue, bool ivalid) :
		key(ikey),
		value(ivalue),
		valid(ivalid) {	}
	LookupEntry() {}
	ap_uint<MS> key;
	ap_uint<AS> value;
	bool valid;
};
    
#endif // SHARED_H
