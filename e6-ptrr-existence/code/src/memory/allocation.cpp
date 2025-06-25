#include "allocation.hpp"
#include "pagemap.hpp"
#include "../utils.hpp"
#include "../../lib/ptedit_header.h"

#include <fcntl.h>
#include <random>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <unistd.h>

constexpr size_t GB = (1ULL << 30);

constexpr size_t SUPERPAGE_SHIFT = 30;
constexpr size_t SUPERPAGE_MASK = (1ULL << SUPERPAGE_SHIFT) - 1;

allocation::~allocation() {
    if (allocation_ptr) {
        munmap(allocation_ptr, allocation_size);
    }
}

bool allocation::allocate(size_t num_superpages) {
    allocation_size = num_superpages * GB;
    int prot = PROT_READ | PROT_WRITE;
    int flags = MAP_PRIVATE | MAP_ANONYMOUS | MAP_POPULATE | MAP_HUGETLB | (30 << MAP_HUGE_SHIFT);
    allocation_ptr = mmap(nullptr, allocation_size, prot, flags, -1, 0);
    if (allocation_ptr == MAP_FAILED) {
        perror("mmap");
        return false;
    }

    if (mlock(allocation_ptr, allocation_size) < 0) {
        perror("mlock");
        return false;
    }

    // Populate virt_phys_mappings.
    auto virt_base = (uint64_t)allocation_ptr;
    for (size_t offset = 0; offset < allocation_size; offset += GB) {
        auto virt = virt_base + offset;
        auto phys = pagemap::vaddr2paddr(virt);
        virt_phys_mappings.emplace_back((volatile char*)virt, phys);
    }

    return true;
}

uint64_t allocation::virt_to_phys(volatile char* virt) {
    auto virt_page_base = (volatile char*)((uint64_t)virt & ~SUPERPAGE_MASK);
    auto offset = (uint64_t)virt & SUPERPAGE_MASK;
    for (auto& pair : virt_phys_mappings) {
        if (pair.first == virt_page_base) {
            return pair.second | offset;
        }
    }

    return 0;
}

volatile char* allocation::phys_to_virt(uint64_t phys) {
    auto phys_page_base = phys & ~SUPERPAGE_MASK;
    auto offset = phys & SUPERPAGE_MASK;
    for (auto& pair : virt_phys_mappings) {
        if (pair.second == phys_page_base) {
            return (volatile char*)((uint64_t)pair.first | offset);
        }
    }

    return nullptr;
}

volatile char* allocation::get_rand_addr() {
    static std::random_device random_device;
    static std::default_random_engine generator(random_device());
    static std::uniform_int_distribution<uint64_t> distribution(0, this->allocation_size - 1);

    return (volatile char*)((uint64_t)allocation_ptr + distribution(generator));
}

static void ptedit_flush(void* p) {
    asm volatile("DC CIVAC, %0" :: "r"(p));
    asm volatile("DSB ISH");
    asm volatile("ISB");
}

void allocation::set_uncached() {
    if (ptedit_init()) {
        _printf("Error: Could not initialize PTEditor.\n");
        exit(1);
    }

    int uc_mt = ptedit_find_first_mt(PTEDIT_MT_UC);
    if (uc_mt == -1) {
        _printf("No UC MT available!\n");
        exit(1);
    }

    for (auto& pair : virt_phys_mappings) {
        void* base = (void*)pair.first;
        auto entry = ptedit_resolve(base, 0);
        // ptedit_print_entry_t(entry);
        auto mt = ptedit_extract_mt_huge(entry.pud);
        _printf("Mapping is %s", ptedit_mt_to_string(ptedit_get_mt(mt)));
        entry.pud = ptedit_apply_mt_huge(entry.pud, uc_mt);
        entry.valid = PTEDIT_VALID_MASK_PUD;
        ptedit_update(base, 0, &entry);
        _printf("%p should now be uncachable.", base);
        entry = ptedit_resolve(base, 0);
        mt = ptedit_extract_mt_huge(entry.pud);
        _printf("Mapping is %s", ptedit_mt_to_string(ptedit_get_mt(mt)));
        // ptedit_print_entry_t(entry);
    }

    _printf("Mapping is now fully uncachable!");
}
