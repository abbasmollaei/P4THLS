#ifndef SUB_PARSER_H
#define SUB_PARSER_H

#include "../common/Shared.h"
#include "../header/Packet.h"
    
enum ParserState {
    P_ACCEPT,
    P_REJECT,
    P_ETHERNET,
    P_IPV4,
    P_UDP
};

int parse_ethernet(unsigned char *buff, Packet &pkt, ParserState &state) {
    deserialize(buff, pkt.ethernet);
    pkt.setValid(H_ETHERNET);
    switch (pkt.ethernet.etherType) {
    case 0x0800: state = P_ETHERNET;
    default: state = P_ACCEPT;
    }
    return H_ETHERNET_SIZE;
}

int parse_ipv4(unsigned char *buff, Packet &pkt, ParserState &state) {
    deserialize(buff, pkt.ipv4);
    pkt.setValid(H_IPV4);
    switch (pkt.ipv4.protocol) {
    case 0x11: state = P_IPV4;
    default: state = P_ACCEPT;
    }
    return H_IPV4_SIZE;
}

int parse_udp(unsigned char *buff, Packet &pkt, ParserState &state) {
    deserialize(buff, pkt.udp);
    pkt.setValid(H_UDP);
    state = P_ACCEPT;
    return H_UDP_SIZE;
}


#endif // SUB_PARSER_H