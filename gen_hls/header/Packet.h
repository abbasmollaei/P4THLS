#ifndef PACKET_H
#define PACKET_H

#include "ScalarsHeader.h"
#include "EthernetHeader.h"
#include "Ipv4Header.h"
#include "UdpHeader.h"
#include "Metadata.h"
#include "Standardmetadata.h"

enum HeaderValidFlag : short {
	H_SCALARS = 0x0001,
	H_ETHERNET = 0x0002,
	H_IPV4 = 0x0004,
	H_UDP = 0x0008
};

struct Packet {
	Packet() : valid(0) {}
	Packet(const Packet &copy) :
		scalars(copy.scalars),
		ethernet(copy.ethernet),
		ipv4(copy.ipv4),
		udp(copy.udp),
		metadata(copy.metadata),
		standardmetadata(copy.standardmetadata),
		valid(copy.valid) {}

	ScalarsHeader scalars;
	EthernetHeader ethernet;
	Ipv4Header ipv4;
	UdpHeader udp;
	Metadata metadata;
	Standardmetadata standardmetadata;
	short valid;

	void setValid(HeaderValidFlag flag)
	{
		valid |= flag;
	}

	void setInvalid(HeaderValidFlag flag)
	{
		valid &= ~flag;
	}

	bool isValid(HeaderValidFlag flag)
	{
		return (valid & flag) != 0;
	}
};

#endif // PACKET_H
