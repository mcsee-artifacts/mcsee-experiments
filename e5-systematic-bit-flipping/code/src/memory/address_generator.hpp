#include <cstdint>
#include <cstdlib>

#include "allocation.hpp"
#include "function.hpp"

#pragma once

namespace memory {

class address_generator {
public:
    address_generator(allocation& allocation, int64_t dram_offset)
        : m_allocation(allocation), m_dram_offset(dram_offset) {
    }

    [[nodiscard]] uint64_t virt_to_dram(volatile char* virt) const {
        auto phys = m_allocation.virt_to_phys(virt);
        return phys - m_dram_offset;
    }

    [[nodiscard]] volatile char* dram_to_virt(uint64_t dram) const {
        auto phys = dram + m_dram_offset;
        return m_allocation.phys_to_virt(phys);
    }

    // Picks a random virtual address that satisfies the given constraints.
    [[nodiscard]] volatile char* get_random_addr(std::vector<function_constraint> const& constraints) const;

    // Picks a "random" virtual address that allows bit flips in as many positions as possible without moving outside
    // the allocation, while satisfying the given constraints.
    [[nodiscard]] volatile char* get_good_addr(
        std::vector<function_constraint> const& constraints,
        size_t num_iterations = 256) const;

private:
    allocation& m_allocation;
    int64_t m_dram_offset { 0 };
};

}