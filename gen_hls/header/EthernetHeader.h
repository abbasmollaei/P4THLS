#ifndef ETHERNET_HEADER_H
#define ETHERNET_HEADER_H

#include "BaseHeader.h"

#define H_ETHERNET_SIZE 14

struct EthernetHeader {
	EthernetHeader() {}
	EthernetHeader(const EthernetHeader &other) :
		dstAddr(other.dstAddr),
		srcAddr(other.srcAddr),
		etherType(other.etherType) {}

	ap_uint<48> dstAddr;
	ap_uint<48> srcAddr;
	ap_uint<16> etherType;
};

void serialize(unsigned char* d, EthernetHeader &hdr) {
#pragma HLS INLINE
    d[0] = static_cast<unsigned char>(hdr.dstAddr.range(47, 40).to_uint());
    d[1] = static_cast<unsigned char>(hdr.dstAddr.range(39, 32).to_uint());
    d[2] = static_cast<unsigned char>(hdr.dstAddr.range(31, 24).to_uint());
    d[3] = static_cast<unsigned char>(hdr.dstAddr.range(23, 16).to_uint());
    d[4] = static_cast<unsigned char>(hdr.dstAddr.range(15, 8).to_uint());
    d[5] =  static_cast<unsigned char>(hdr.dstAddr.range(7, 0).to_uint());
    d[6] = static_cast<unsigned char>(hdr.srcAddr.range(47, 40).to_uint());
    d[7] = static_cast<unsigned char>(hdr.srcAddr.range(39, 32).to_uint());
    d[8] = static_cast<unsigned char>(hdr.srcAddr.range(31, 24).to_uint());
    d[9] = static_cast<unsigned char>(hdr.srcAddr.range(23, 16).to_uint());
    d[10] = static_cast<unsigned char>(hdr.srcAddr.range(15, 8).to_uint());
    d[11] =  static_cast<unsigned char>(hdr.srcAddr.range(7, 0).to_uint());
    d[12] = static_cast<unsigned char>(hdr.etherType.range(15, 8).to_uint());
    d[13] =  static_cast<unsigned char>(hdr.etherType.range(7, 0).to_uint());
}

void deserialize(unsigned char* d, EthernetHeader &hdr) {
#pragma HLS INLINE
    hdr.dstAddr.range(47, 40) = d[0];
    hdr.dstAddr.range(39, 32) = d[1];
    hdr.dstAddr.range(31, 24) = d[2];
    hdr.dstAddr.range(23, 16) = d[3];
    hdr.dstAddr.range(15, 8) = d[4];
    hdr.dstAddr.range(7, 0) = d[5];
    hdr.srcAddr.range(47, 40) = d[6];
    hdr.srcAddr.range(39, 32) = d[7];
    hdr.srcAddr.range(31, 24) = d[8];
    hdr.srcAddr.range(23, 16) = d[9];
    hdr.srcAddr.range(15, 8) = d[10];
    hdr.srcAddr.range(7, 0) = d[11];
    hdr.etherType.range(15, 8) = d[12];
    hdr.etherType.range(7, 0) = d[13];
}

#endif // ETHERNET_HEADER_H
