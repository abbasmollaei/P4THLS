#ifndef IPV4_HEADER_H
#define IPV4_HEADER_H

#include "BaseHeader.h"

#define H_IPV4_SIZE 20

struct Ipv4Header {
	Ipv4Header() {}
	Ipv4Header(const Ipv4Header &other) :
		version(other.version),
		ihl(other.ihl),
		diffserv(other.diffserv),
		totalLen(other.totalLen),
		identification(other.identification),
		flags(other.flags),
		fragOffset(other.fragOffset),
		ttl(other.ttl),
		protocol(other.protocol),
		hdrChecksum(other.hdrChecksum),
		srcAddr(other.srcAddr),
		dstAddr(other.dstAddr) {}

	ap_uint<4> version;
	ap_uint<4> ihl;
	ap_uint<8> diffserv;
	ap_uint<16> totalLen;
	ap_uint<16> identification;
	ap_uint<3> flags;
	ap_uint<13> fragOffset;
	ap_uint<8> ttl;
	ap_uint<8> protocol;
	ap_uint<16> hdrChecksum;
	ap_uint<32> srcAddr;
	ap_uint<32> dstAddr;
};

void serialize(unsigned char* d, Ipv4Header &hdr) {
#pragma HLS INLINE
    d[0] |= (hdr.version.to_uchar() & 0xF) << 4;
    d[0] |= (hdr.ihl.to_uchar() & 0xF);
    d[1] =  hdr.diffserv.to_uchar();
    d[2] = static_cast<unsigned char>(hdr.totalLen.range(15, 8).to_uint());
    d[3] =  static_cast<unsigned char>(hdr.totalLen.range(7, 0).to_uint());
    d[4] = static_cast<unsigned char>(hdr.identification.range(15, 8).to_uint());
    d[5] =  static_cast<unsigned char>(hdr.identification.range(7, 0).to_uint());
    d[6] |= (hdr.flags.to_uchar() & 0x7) << 5;
    d[6] |= (static_cast<unsigned char>(hdr.fragOffset.range(12, 8).to_uint()) & 0x1F);
    d[7] =  static_cast<unsigned char>(hdr.fragOffset.range(7, 0).to_uint());
    d[8] =  hdr.ttl.to_uchar();
    d[9] =  hdr.protocol.to_uchar();
    d[10] = static_cast<unsigned char>(hdr.hdrChecksum.range(15, 8).to_uint());
    d[11] =  static_cast<unsigned char>(hdr.hdrChecksum.range(7, 0).to_uint());
    d[12] = static_cast<unsigned char>(hdr.srcAddr.range(31, 24).to_uint());
    d[13] = static_cast<unsigned char>(hdr.srcAddr.range(23, 16).to_uint());
    d[14] = static_cast<unsigned char>(hdr.srcAddr.range(15, 8).to_uint());
    d[15] =  static_cast<unsigned char>(hdr.srcAddr.range(7, 0).to_uint());
    d[16] = static_cast<unsigned char>(hdr.dstAddr.range(31, 24).to_uint());
    d[17] = static_cast<unsigned char>(hdr.dstAddr.range(23, 16).to_uint());
    d[18] = static_cast<unsigned char>(hdr.dstAddr.range(15, 8).to_uint());
    d[19] =  static_cast<unsigned char>(hdr.dstAddr.range(7, 0).to_uint());
}

void deserialize(unsigned char* d, Ipv4Header &hdr) {
#pragma HLS INLINE
    hdr.version = (d[0] >> 4) & 0xF;
    hdr.ihl = (d[0] & 0xF);
    hdr.diffserv = d[1];
    hdr.totalLen.range(15, 8) = d[2];
    hdr.totalLen.range(7, 0) = d[3];
    hdr.identification.range(15, 8) = d[4];
    hdr.identification.range(7, 0) = d[5];
    hdr.flags = (d[6] >> 5) & 0x7;
    hdr.fragOffset.range(12, 8) = d[6];
    hdr.fragOffset.range(7, 0) = d[7];
    hdr.ttl = d[8];
    hdr.protocol = d[9];
    hdr.hdrChecksum.range(15, 8) = d[10];
    hdr.hdrChecksum.range(7, 0) = d[11];
    hdr.srcAddr.range(31, 24) = d[12];
    hdr.srcAddr.range(23, 16) = d[13];
    hdr.srcAddr.range(15, 8) = d[14];
    hdr.srcAddr.range(7, 0) = d[15];
    hdr.dstAddr.range(31, 24) = d[16];
    hdr.dstAddr.range(23, 16) = d[17];
    hdr.dstAddr.range(15, 8) = d[18];
    hdr.dstAddr.range(7, 0) = d[19];
}

#endif // IPV4_HEADER_H
