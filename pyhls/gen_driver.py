import json
import os
import re
from sys_utils import *

def gen_driver_control(dir_path):
    code = '''
#include <cstring>
#include <iostream>
#include <cstdlib>
#include <vector>

// XRT includes
#include "experimental/xrt_bo.h"
#include "experimental/xrt_device.h"
#include "experimental/xrt_kernel.h"
#include "experimental/xrt_ip.h"
#include "experimental/xrt_xclbin.h"

#define DATA_SIZE 1024

int main(int argc, char **argv) {
  std::string xclbin_file_name = argv[1];
  
  unsigned int device_index = 0;
  std::cout << "Open the device" << device_index << std::endl;
  auto device = xrt::device(device_index);
  
  std::cout << "Load the xclbin " << xclbin_file_name << std::endl;
  auto uuid = device.load_xclbin(xclbin_file_name);

  uint64_t buf_addr;
  {
    auto krnl0 = xrt::kernel(device, uuid, "packet_processing");
    size_t vector_size_bytes = sizeof(unsigned int) * DATA_SIZE;
    auto bo0 = xrt::bo(device, vector_size_bytes, krnl0.group_id(0));
    auto bo0_map = bo0.map<unsigned int *>();
    std::fill(bo0_map, bo0_map + DATA_SIZE, 0x0);
    buf_addr = bo0.address();
    bo0.sync(XCL_BO_SYNC_BO_TO_DEVICE);
  }

  {
    std::cout << "Instantiate IPs ..." << std::endl;
    auto ip0 = xrt::ip(device, uuid, "packet_processing");
  
    unsigned int A_OFFSET = 0x10;
    ip0.write_register(A_OFFSET, buf_addr[0]);
    ip0.write_register(A_OFFSET + 4, buf_addr[0] >> 32);
  
    unsigned int IP_START = 0x01;
    unsigned int IP_DONE = 0x02;
    unsigned int IP_IDLE = 0x04;
  
    unsigned int axi_ctrl = 0x81;//0x01;   // 0x81
    size_t USER_OFFSET = 0x00;
    ip0.write_register(USER_OFFSET, axi_ctrl);

    // Write your desired control plane according the following example
    unsigned int MEMCTRL_OFFSET = 0x10;
    unsigned int CTRL_OFFSET = 0x1C;
    unsigned int FLAG_OFFSET = 0x24;
    int mode = 3;

    if (mode == 0) {
      unsigned int flag = 0x00;      
      ip0.write_register(FLAG_OFFSET, flag);
    } 
    else if (mode == 1) {
      unsigned int flag = 0x01;      
      ip0.write_register(FLAG_OFFSET, flag);
    }
    else if (mode == 2) {
      unsigned int ctrl = 0x0201; // Insert two entries
      ip0.write_register(CTRL_OFFSET, ctrl);

      // First entry
      bo0_map[0] = 0x81999998;
      bo0_map[1] = 0xB66F5135;
      bo0_map[2] = 0xD1D38FF5;
      bo0.sync(XCL_BO_SYNC_BO_TO_DEVICE);

      // Second entry
      bo0_map[0] = 0x81FFF998;
      bo0_map[1] = 0xB66FAAAA;
      bo0_map[2] = 0xD1D111F5;
      bo0.sync(XCL_BO_SYNC_BO_TO_DEVICE);

      unsigned int flag = 0x02; // Insert the entries into the second table      
      ip0.write_register(FLAG_OFFSET, flag);
    }
  }

  std::cout << "Finished" << std::endl;
  return 0;
}
'''
    with open(f'{dir_path}/host.cpp', 'w') as f:
        f.write(code)


def generate_driver(build_dir):
    dir_path = f'{build_dir}/driver'
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)
    gen_driver_control(dir_path)
    
