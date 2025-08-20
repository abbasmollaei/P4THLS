#ifndef UDP_HEADER_H
#define UDP_HEADER_H

#include "BaseHeader.h"

#define H_UDP_SIZE 8

struct UdpHeader {
	UdpHeader() {}
	UdpHeader(const UdpHeader &other) :
		srcPort(other.srcPort),
		dstPort(other.dstPort),
		length(other.length),
		checksum(other.checksum) {}

	ap_uint<16> srcPort;
	ap_uint<16> dstPort;
	ap_uint<16> length;
	ap_uint<16> checksum;
};

void serialize(unsigned char* d, UdpHeader &hdr) {
#pragma HLS INLINE
    d[0] = static_cast<unsigned char>(hdr.srcPort.range(15, 8).to_uint());
    d[1] =  static_cast<unsigned char>(hdr.srcPort.range(7, 0).to_uint());
    d[2] = static_cast<unsigned char>(hdr.dstPort.range(15, 8).to_uint());
    d[3] =  static_cast<unsigned char>(hdr.dstPort.range(7, 0).to_uint());
    d[4] = static_cast<unsigned char>(hdr.length.range(15, 8).to_uint());
    d[5] =  static_cast<unsigned char>(hdr.length.range(7, 0).to_uint());
    d[6] = static_cast<unsigned char>(hdr.checksum.range(15, 8).to_uint());
    d[7] =  static_cast<unsigned char>(hdr.checksum.range(7, 0).to_uint());
}

void deserialize(unsigned char* d, UdpHeader &hdr) {
#pragma HLS INLINE
    hdr.srcPort.range(15, 8) = d[0];
    hdr.srcPort.range(7, 0) = d[1];
    hdr.dstPort.range(15, 8) = d[2];
    hdr.dstPort.range(7, 0) = d[3];
    hdr.length.range(15, 8) = d[4];
    hdr.length.range(7, 0) = d[5];
    hdr.checksum.range(15, 8) = d[6];
    hdr.checksum.range(7, 0) = d[7];
}

#endif // UDP_HEADER_H
