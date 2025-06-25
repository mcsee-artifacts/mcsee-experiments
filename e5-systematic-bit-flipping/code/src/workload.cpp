#include <cassert>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <random>
#include <sstream>
#include <sys/mman.h>

#include "memory/address_generator.hpp"
#include "memory/allocation.hpp"
#include "trigger/client.hpp"
#include "utils.hpp"
#include "workload.hpp"

struct addr {
    volatile char* virt;
    uint64_t phys;
    uint64_t dram;
    // The DRAM address of the corresponding principal address. If this is a principal address, it is equal to
    // this->dram.
    uint64_t principal_dram;
};

inline uint64_t func_apply(uint64_t func, uint64_t addr) {
    return __builtin_parityll(func & addr);
}

int workload::run(
    size_t num_superpages,
    size_t num_random_addrs,
    bool use_good_addr,
    bool use_uncached_memory,
    int64_t dram_offset,
    std::vector<memory::function_constraint> const& constraints
) {
    _printf("running workload");
    _printf("    %zu superpages", num_superpages);
    _printf("    %zu random (principal) addresses", num_random_addrs);
    if (use_good_addr) {
        _printf("    using (not entirely random) addresses which allow for many bit flips");
    }
    if (use_uncached_memory) {
        _printf("    using uncached memory");
    }
    _printf("    DRAM offset of 0x%lx (%zu MiB)", dram_offset, dram_offset >> 20);

    for (auto& constraint : constraints) {
        _printf("    function constraint: 0x%010lx = %d", (uint64_t)constraint.func(), (int)constraint.value());
    }

    allocation allocation;
    if (!allocation.allocate(num_superpages)) {
        _printf("could not allocate memory block");
        return 1;
    }

    if (use_uncached_memory) {
        _printf("setting allocation to use uncached memory");
        allocation.set_uncached();
    }

    memory::address_generator generator(allocation, dram_offset);
    std::vector<addr> addrs;

    for (size_t i = 0; i < num_random_addrs; i++) {
        // Choose principal address.
        auto virt_principal = use_good_addr
                              ? generator.get_good_addr(constraints, 256)
                              : generator.get_random_addr(constraints);
        auto phys_principal = allocation.virt_to_phys(virt_principal);
        auto dram_principal = phys_principal - dram_offset;

        // For reliability reasons, put the principal address twice.
        addrs.push_back({ virt_principal, phys_principal, dram_principal, dram_principal });
        addrs.push_back({ virt_principal, phys_principal, dram_principal, dram_principal });

        for (size_t bit = 6; bit < 8 * sizeof(void*); bit++) {
            auto dram_flipped = dram_principal ^ BIT_SET(bit);

            assert(constraints.size() <= 1 && "FIXME: This logic currently only supports one constraint.");
            if (!constraints.empty() && (BIT_SET(bit) & constraints.front().func())) {
                auto constraint_lsb = LSb(constraints.front().func());
                if (bit == constraint_lsb) {
                    _printf("trying to change bit %zu, which is LSB of a constraint (0x%010lx = %d), skipping...",
                            bit, (uint64_t)constraints.front().func(), (int)constraints.front().value());
                    continue;
                }
                // If we want to keep a function (i.e., the subchannel function) fixed, we will additionally flip the
                // LSB of that function, in addition to `bit`.
                dram_flipped ^= BIT_SET(constraint_lsb);
            }
            auto phys_flipped = dram_flipped + dram_offset;
            auto virt_flipped = allocation.phys_to_virt(phys_flipped);
            if (!virt_flipped) {
                _printf("flipping bit %d lead outside of allocation, skipping...", bit);
                continue;
            }
            addrs.push_back({ virt_flipped, phys_flipped, dram_flipped, dram_principal });
        }
    }

    _printf("accessing a total of %zu addresses, for %zu principal addresses", addrs.size(), num_random_addrs);

    // Checking the distribution of bits for all addresses.
    std::vector<size_t> bit_one_counts(64, 0);
    assert(bit_one_counts.size() == 64);
    for (auto& addr: addrs) {
        for (size_t i = 0; i < 8 * sizeof(void*); i++) {
            bit_one_counts[i] += (addr.dram & BIT_SET(i)) > 0;
        }
    }
    for (size_t i = 0; i < bit_one_counts.size(); i++) {
        double percentage = 100.0 * bit_one_counts[i] / addrs.size();
        _printf("bit %2zu: %4zu / %4zu (%5.2f%%)", i, bit_one_counts[i], addrs.size(), percentage);
    }

    // Shuffling accesses to throw off possible prefetching.
    std::random_device rd;
    std::default_random_engine engine(rd());
    // Shuffle addresses in sections of 512 addresses.
    for (size_t off = 0; off < addrs.size(); off += 512) {
        auto win_begin = off;
        auto win_end = std::min(off + 512, addrs.size());
        std::shuffle(addrs.begin() + win_begin, addrs.begin() + win_end, engine);
    }

    constexpr size_t NUM_ACCESSES_PER_ITER = 12'000'000;
    constexpr size_t NUM_TRIGGERS_TOTAL = 3;

    auto trigger_modulo = NUM_ACCESSES_PER_ITER / NUM_TRIGGERS_TOTAL;

    // Now, we are ready.
    trigger::client trigger_client;
    trigger_client.send_ready_to_runner();

    for (auto& addr : addrs) {
        // Start of an iteration.
        trigger_client.wait_for_ready_from_trigger();
        trigger_client.open_fifo_to_trigger();

        usleep(500'000);

        // Write the address we are going to access to the 'exp_cfg.csv'. We are
        // only accessing one address per iteration.
        // Cast addresses to void* such that they are output properly by the
        // ostream.
        std::ofstream ofs_exp_cfg;
        ofs_exp_cfg.open("exp_cfg.csv", std::ios::out);
        ofs_exp_cfg << "virt_addr,phys_addr,dram_addr,dram_principal\n";
        ofs_exp_cfg << std::hex
                    << (void*)addr.virt << ","
                    << (void*)addr.phys << ","
                    << (void*)addr.dram << ","
                    << (void*)addr.principal_dram << "\n";
        ofs_exp_cfg.close();

        // Cache this address in a local variable. This is required such that there is no pointer-chasing to obtain the
        // address inside the loop, because this would lead to as many accesses to the storage location of the pointer
        // as to the pointer itself, which would make measurement data unusable.
        // Note that caching may prevent this from reaching the memory bus, but better be safe than sorry.
        auto* access_addr = addr.virt;

        _printf("starting acquisition");
        (void)system("./decoder/venv/bin/python3 ./decoder/acquire.py --start");

        for (size_t j = 0; j < NUM_ACCESSES_PER_ITER; j++) {
            *access_addr;
            clflushopt(access_addr);
            mfence();

            if (j % trigger_modulo == 0) {
                // Trigger every so often.
                trigger_client.send_trigger();
            }
        }

        _printf("stopped acquisition");
        (void)system("./decoder/venv/bin/python3 ./decoder/acquire.py --stop");

        // tell the trigger that there are no more triggers coming
        trigger_client.send_finished();
    }

    _printf("workload completed! terminating...");
    return 0;
}
