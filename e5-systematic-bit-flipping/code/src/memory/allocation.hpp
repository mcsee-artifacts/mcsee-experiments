#include <cstdint>
#include <cstdlib>
#include <utility>
#include <vector>

#pragma once

class allocation {
public:
    allocation() = default;
    ~allocation();

    bool allocate(size_t num_superpages);

    // The functions return 0 (nullptr) if the address falls outside this allocation mapping.
    uint64_t virt_to_phys(volatile char* virt);
    volatile char* phys_to_virt(uint64_t phys);

    volatile char* get_rand_addr();

    void set_uncached();

private:
    void* allocation_ptr{nullptr};
    size_t allocation_size{0};

    std::vector<std::pair<volatile char*, uint64_t>> virt_phys_mappings;
};
