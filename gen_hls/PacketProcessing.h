#ifndef PACKET_PROCESSING_H
#define PACKET_PROCESSING_H

#include "common/Shared.h"
#include <hls_stream.h>

void packet_processing(
                        hls::stream<axi_chunk> &in0,
                        hls::stream<axi_chunk> &in1,                        hls::stream<axi_chunk> &out0,
                        hls::stream<axi_chunk> &out1,                        unsigned int *memCtrl,
                        const unsigned int ctrl,
                        const unsigned int flag);

#endif // PACKET_PROCESSING_H
