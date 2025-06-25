#include <cassert>

#include "address_generator.hpp"
#include "../utils.hpp"

namespace memory {

volatile char* address_generator::get_random_addr(std::vector<function_constraint> const& constraints) const {
    for (size_t i = 0; i < 1024; i++) {
        auto virt = m_allocation.get_rand_addr();
        auto dram = virt_to_dram(virt);

        bool constraints_satisfied = true;
        for (auto& constraint : constraints) {
            if (!constraint.is_satisfied_by(dram)) {
                constraints_satisfied = false;
                break;
            }
        }

        if (constraints_satisfied) {
            return virt;
        }
    }

    _printf("Could not find address satisfying constraints in 1024 iterations. Exiting...\n");
    exit(1);
}

volatile char* address_generator::get_good_addr(
    std::vector<function_constraint> const& constraints,
    size_t num_iterations
) const {
    volatile char* best_candidate = 0;
    size_t best_candidate_num_flips = 0;

    for (size_t i = 0; i < num_iterations; i++) {
        auto virt = m_allocation.get_rand_addr();
        auto dram = virt_to_dram(virt);

        // Check that all function constraints are satisfied.
        bool constraints_satisfied = true;
        for (auto& constraint : constraints) {
            if (!constraint.is_satisfied_by(dram)) {
                constraints_satisfied = false;
                break;
            }
        }
        if (!constraints_satisfied) {
            continue;
        }

        size_t num_flips = 0;
        for (size_t j = 0; j < 64; j++) {
            // Check if flipping bit `j` keeps us inside the allocation.
            auto dram_flipped = dram ^ BIT_SET(j);
            auto virt_flipped = dram_to_virt(dram_flipped);
            if (virt_flipped != nullptr) {
                num_flips++;
            }
        }

        if (num_flips > best_candidate_num_flips) {
            best_candidate = virt;
            best_candidate_num_flips = num_flips;
        }
    }

    assert(best_candidate);
    return best_candidate;
}

}
