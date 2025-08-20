# /*
# Copyright (C) 2023, Advanced Micro Devices, Inc. All rights reserved.
# SPDX-License-Identifier: X11
# */

ECHO=@echo

.PHONY: help all gen_ip pack_hls pack_kernel build_hw host run clean

help:
	$(ECHO) "Makefile Usage:"
	$(ECHO) "  make gen_ip"
	$(ECHO) "      Command to generate the IPs used in this design"
	$(ECHO) ""
	$(ECHO) "  make pack_kernel"
	$(ECHO) "      Command to pack the RTL design into Vitis kernel"
	$(ECHO) ""
	$(ECHO) "  make build_hw"
	$(ECHO) "      Command to build xclbin files for Alveo platform"
	$(ECHO) ""
	$(ECHO) "  make clean"
	$(ECHO) "      Command to remove all the generated files."


# Target hardware setting, uncomment appropriate lines 
VPP      := $(XILINX_VITIS)/bin/v++
BOARD    := u280
PLATFORM ?= xilinx_u280_gen3x16_xdma_1_202211_1
PART     := xcu280-fsvh2892-2l-e
TARGET   := hw
LANE     := 4

PROJ_NAME    := UdpFirewall
TOP_FUNCTION := packet_processing
HLS_XO       := p4hls_krnl.xo
CONNECTIVITY := connectivity_x$(LANE).cfg

VPP_HLS_OPTS   := --platform $(PLATFORM) -t $(TARGET) -s -g --kernel_frequency 250
VPP_VITIS_OPTS := --platform $(PLATFORM) -t $(TARGET) -s -g --link --optimize 3 --kernel_frequency 250
XCLBIN         := $(PROJ_NAME)_x$(LANE).xclbin

CXXFLAGS += -g -std=c++17 -I$(XILINX_XRT)/include
LFLAGS   := -L$(XILINX_XRT)/lib -lxilinxopencl -pthread -lrt -lxrt_coreutil
HOST_EXE := host.exe

KERNEL_SRC := src/PacketProcessing.cpp \
	src/PacketProcessing.h \
	src/header/BaseHeader.h \
	src/header/ScalarsHeader.h \
	src/header/Standardmetadata.h \
	src/header/UdpHeader.h \
	src/header/Packet.h \
	src/header/Metadata.h \
	src/header/EthernetHeader.h \
	src/header/Ipv4Header.h \
	src/parser/PacketParser.h \
	src/parser/SubParser.h \
	src/deparser/SubDeparser.h \
	src/deparser/PacketDeparser.h \
	src/ingress/MemoryInterface.h \
	src/ingress/IngressProcessing.h \
	src/ingress/Actions.h \
	src/table/MatchActionTable.h \
	src/table/Udp_port_firewallTable.h \
	src/table/Table.h \
	src/table/Ip_firewallTable.h \
	src/common/Shared.h
	
HOST_SRC := host/host.cpp


all: gen_ip pack_hls pack_kernel build_hw host run

gen_ip:
	rm -rf ip_generation; 
	mkdir ip_generation; 
	vivado -mode batch -source ./gen_ip_x$(LANE).tcl -tclargs $(PART) $(BOARD)

pack_hls: $(KERNEL_SRC)
	$(VPP) $(VPP_HLS_OPTS) -c -k $(TOP_FUNCTION) -o $(HLS_XO) $+
	
pack_kernel:
	rm -rf vivado_pack_krnl_project
	mkdir vivado_pack_krnl_project
	cd vivado_pack_krnl_project; vivado -mode batch -source ../pack_eth_x$(LANE)_kernel.tcl -tclargs $(PART); vivado -mode batch -source ../pack_data_fifo_kernel.tcl -tclargs $(PART)

build_hw:
	$(VPP) $(VPP_VITIS_OPTS) --config $(CONNECTIVITY) -o $(XCLBIN) ethernet_krnl_axis_x$(LANE).xo data_fifo_krnl.xo $(HLS_XO)

host: $(HOST_SRC)
	g++ $(CXXFLAGS) -o $@ $+ $(LFLAGS)
	@echo 'Compiled Host Executable: $(HOST_EXE)'

run:
	./$(HOST_EXE) $(XCLBIN)

clean:
	$(RM) -rf ip_generation vivado_pack_krnl_project
	$(RM) -rf *.xml *.xo *.xclbin *.xclbin.info *.xclbin.link_summary *.jou *.log _x 
	$(RM) $(HOST_EXE) *.o
	

