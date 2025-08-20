#ifndef SCALARS_HEADER_H
#define SCALARS_HEADER_H

#include "BaseHeader.h"

#define H_SCALARS_SIZE 1

struct ScalarsHeader {
	ScalarsHeader() {}
	ScalarsHeader(const ScalarsHeader &other) :
		ip_allowed(other.ip_allowed),
		_padding(other._padding) {}

	ap_uint<1> ip_allowed;
	ap_uint<7> _padding;
};

void serialize(unsigned char* d, ScalarsHeader &hdr) {
#pragma HLS INLINE
    d[0] |= (hdr.ip_allowed.to_uchar() & 0x1) << 7;
    d[0] |= (hdr._padding.to_uchar() & 0x7F);
}

void deserialize(unsigned char* d, ScalarsHeader &hdr) {
#pragma HLS INLINE
    hdr.ip_allowed = (d[0] >> 7) & 0x1;
    hdr._padding = (d[0] & 0x7F);
}

#endif // SCALARS_HEADER_H
