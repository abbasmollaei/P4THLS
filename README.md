# P4THLS: Templated HLS Framework for P4-to-FPGA Compilation

**P4THLS** is a templated High-Level Synthesis (HLS) framework that translates P4 data-plane programs into synthesizable C++ modules suitable for FPGA deployment. It enables flexible and automated generation of key packet processing components—parser, match-action tables, deparser, and memory interfaces—optimized for AMD/Xilinx FPGA architectures.

## 🔧 Features

- ✅ Full packet processing pipeline (parser → match-action → deparser)
- ⚙️ Templated architecture with customizable table sizes and match types
- 📦 Unified memory interface supporting LUTRAM, BRAM, and URAM
- 🚀 Configurable AXI stream bus width and multi-port support
- 🔗 Auto-generated control-plane interface via AXI-Lite

## 📢 Availability

This framework is part of an ongoing research project. **The source code and documentation will be publicly released upon paper publication.**

## 📄 License

TBD (To be updated upon release)

## 📬 Contact

For questions or collaboration requests, please contact mostafa.abbasmollaei@polymtl.ca.
