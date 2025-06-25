#include <cstdint>
#include <cstdlib>

#include "memory/function.hpp"

#pragma once

class workload {
public:
    static int run(
        size_t num_superpages,
        size_t num_random_addrs,
        bool use_good_addr,
        bool use_uncached_memory,
        int64_t dram_offset,
        std::vector<memory::function_constraint> const& constraints
    );
};
