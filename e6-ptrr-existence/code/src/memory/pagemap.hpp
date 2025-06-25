#include <cstdint>

#pragma once

class pagemap {
 public:
  static uint64_t vaddr2paddr(uint64_t vaddr);
};
