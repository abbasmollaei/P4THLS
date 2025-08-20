#ifndef METADATA_H
#define METADATA_H

#include "BaseHeader.h"

struct Metadata {
	Metadata() {}
	Metadata(const Metadata &other) :
		port(other.port),
		_padding_0(other._padding_0) {}

	ap_uint<9> port;
	ap_uint<7> _padding_0;
};

void serialize(unsigned char* d, Metadata &hdr) {
#pragma HLS INLINE
    d[0] = hdr.port.range(8, 1).to_uchar();
    d[1] =  (hdr.port.range(0, 0).to_uchar() & 0x1);
    d[1] |= (hdr._padding_0.to_uchar() & 0x7F);
}

void deserialize(unsigned char* d, Metadata &hdr) {
#pragma HLS INLINE
    hdr.port.range(8, 1) = d[0];
    hdr.port.range(0, 0) = (d[1] >> 7) & 0x1;
    hdr._padding_0 = (d[1] & 0x7F);
}

#endif // METADATA_H
