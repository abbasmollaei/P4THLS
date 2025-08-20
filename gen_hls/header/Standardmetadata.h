#ifndef STANDARDMETADATA_H
#define STANDARDMETADATA_H

#include "BaseHeader.h"

struct Standardmetadata {
	Standardmetadata() {}
	Standardmetadata(const Standardmetadata &other) :
		drop(other.drop),
		_padding(other._padding) {}

	ap_uint<1> drop;
	ap_uint<7> _padding;
};

void serialize(unsigned char* d, Standardmetadata &hdr) {
#pragma HLS INLINE
    d[0] |= (hdr.drop.to_uchar() & 0x1) << 7;
    d[0] |= (hdr._padding.to_uchar() & 0x7F);
}

void deserialize(unsigned char* d, Standardmetadata &hdr) {
#pragma HLS INLINE
    hdr.drop = (d[0] >> 7) & 0x1;
    hdr._padding = (d[0] & 0x7F);
}

#endif // STANDARDMETADATA_H
