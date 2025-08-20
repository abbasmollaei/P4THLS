#include <core.p4>
#include <xsa.p4>

const bit<16> TYPE_IPV4 = 0x800;
const bit<8>  TYPE_UDP  = 17;

typedef bit<9>  egressSpec_t;
typedef bit<48> macAddr_t;
typedef bit<32> ip4Addr_t;

header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16>   etherType;
}

header ipv4_t {
    bit<4>    version;
    bit<4>    ihl;
    bit<8>    diffserv;
    bit<16>   totalLen;
    bit<16>   identification;
    bit<3>    flags;
    bit<13>   fragOffset;
    bit<8>    ttl;
    bit<8>    protocol;
    bit<16>   hdrChecksum;
    ip4Addr_t srcAddr;
    ip4Addr_t dstAddr;
}

header udp_t {
    bit<16> srcPort;
    bit<16> dstPort;
    bit<16> length;
    bit<16> checksum;
}

struct headers {
    ethernet_t ethernet;
    ipv4_t     ipv4;
    udp_t      udp;
}

// User metadata structure
struct metadata {
    bit<9> port;
}

parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {
    state start {
        transition parse_ethernet;
    }

    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            TYPE_IPV4: parse_ipv4;
            default: accept;
        }
    }

    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        transition select(hdr.ipv4.protocol) {
            TYPE_UDP: parse_udp;
            default: accept;
        }
    }

    state parse_udp {
        packet.extract(hdr.udp);
        transition accept;
    }
}


control MyProcessingIngress(inout headers hdr, 
                     inout metadata meta, 
                     inout standard_metadata_t standard_metadata) {

    // User metadata structure
    bool ip_allowed = false;
    
    action drop() {
        standard_metadata.drop = 1;
    }

    action allow_ip() {
        ip_allowed = true;
    }

    action forward(bit<16> port) {
        hdr.udp.dstPort = port;
    }

    table ip_firewall {
        key = {
            hdr.ipv4.srcAddr: exact;
            hdr.ipv4.dstAddr: exact;
        }
        actions = {
            allow_ip;
            drop;
        }
        size = 32768;
        default_action = drop();
    }

    table udp_port_firewall {
        key = {
            hdr.udp.srcPort: exact;
            hdr.udp.dstPort: exact;
        }
        actions = {
            forward;
            drop;
        }
        size = 32768;
        default_action = drop();
    }

    apply {
        if (hdr.udp.isValid()) {
            ip_firewall.apply();
            if (ip_allowed) {
                udp_port_firewall.apply();
            }
        }
    }
}

control MyDeparser(packet_out packet, 
                   in headers hdr,
                   inout metadata meta, 
                   inout standard_metadata_t smeta) {
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.ipv4);
        packet.emit(hdr.udp);
    }
}

XilinxPipeline(
MyParser(),
MyProcessingIngress(),
MyDeparser()
) main;
