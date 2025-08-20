# P4THLS: Templated HLS Framework for P4-to-FPGA Compilation

**P4THLS** is a templated High-Level Synthesis (HLS) framework that translates P4 data-plane programs into synthesizable C++ modules suitable for FPGA deployment. It enables flexible and automated generation of key packet processing components—parser, match-action tables, deparser, and memory interfaces—optimized for AMD/Xilinx FPGA architectures.

## 🔧 Features

- ✅ Full packet processing pipeline (parser → match-action → deparser)
- ⚙️ Templated architecture with customizable table sizes and match types
- 📦 Unified memory interface supporting LUTRAM, BRAM, and URAM
- 🚀 Configurable AXI stream bus width and multi-port support
- 🔗 Auto-generated control-plane interface via AXI-Lite

## 📢 Availability

This framework is part of an ongoing research project. 

## 🛠️ Required Tools

To run this project, install the following tools on your Linux machine:

- [AMD Vitis 2023.2+](https://www.amd.com/en/software/vitis)
- [AMD Vitis HLS 2023.2+](https://www.amd.com/en/software/vitis)
- [Xilinx Runtime (XRT)](https://xilinx.github.io/XRT/master/html/index.html)
- [P4C Compiler](https://github.com/p4lang/p4c)
- Python 3.10+

**Note:** The scripts have been tested for AMD Alveo U280 hardware platform. So you need to install the required packages and libraries on your Linux machine to identify the Alveo FPGA cards.

## ✅ Getting Started

1. Generate the json file by compiling P4 source codes.
2. Run pyhls Python project and give the P4 code and the generated json file to it to generate the corresponding HLS-based packet processing project.
3. Use vitis scripts to generate a Vitis project to run synthesis and implementation and generate bitstream and other required files for deploying the packet processing kernel on the FPGA.

## 📬 Contact

For questions or collaboration requests, please contact mostafa.abbasmollaei@polymtl.ca.
