#include <array>
#include <cstring>
#include <random>

#include "memory/allocation.hpp"
#include "memory/dram_address.hpp"
#include "program/program.hpp"
#include "trigger/client.hpp"
#include "utils.hpp"
#include "workload.hpp"


int workload::run() {
    constexpr size_t num_superpages = 1;

    allocation* mem = nullptr;
    while (!mem) {
        mem = new allocation();
        if (!mem->allocate(num_superpages)) {
            _printf("could not allocate memory block");
            return 1;
        }
        auto mem_ptr_phys = mem->virt_to_phys((volatile char*)mem->ptr());
        _printf("Allocation phys ptr is %p.", (void*)mem_ptr_phys);
        if (mem_ptr_phys >= GB(16)) {
            _printf("Allocation was outside 16 GiB. Retrying...");
            mem = nullptr;
        }
    }
    
    size_t SUB = __builtin_parityll(mem->virt_to_phys((volatile char*)mem->ptr()) & 0xc3200);
    _printf("Chosen subchannel is %zu", SUB);

    dram_address::initialize(std::move(*mem));

    trigger::client trigger_client;
    trigger_client.send_ready_to_runner();

    constexpr size_t NUM_ITERS = 512;
    constexpr size_t NUM_AGGRS = 2;
    constexpr size_t NUM_TOTAL_ACCESSES = 8192;

    constexpr size_t num_pattern_iterations = NUM_TOTAL_ACCESSES / NUM_AGGRS;
    _printf("aggressors         = %zu", NUM_AGGRS);
    _printf("total accesses     = %zu", NUM_TOTAL_ACCESSES);
    _printf("pattern iterations = %zu", num_pattern_iterations);

    for (size_t i = 0; i < NUM_ITERS; i++) {
        // START PROGRAM GENERATION
        _printf("Generating program...");

        srand(time(nullptr));

        program::program prog;

        std::vector<size_t> aggressors;
        size_t last_aggr_row = 128;
        while (aggressors.size() < NUM_AGGRS) {
            aggressors.push_back(last_aggr_row + 8 + (rand() % 8));
            last_aggr_row = aggressors.back();
        }
        std::random_device rd;
        std::default_random_engine gen(rd());
        std::shuffle(aggressors.begin(), aggressors.end(), gen);

        for (size_t i = 0; i < num_pattern_iterations; i++) {
            for (auto row : aggressors) {
                auto* addr_virt = dram_address(SUB, 0, 0, 0, row, row).to_virt();
                prog.add_instruction(program::instruction::read(addr_virt));
                prog.add_instruction(program::instruction::clflush(addr_virt));
                prog.add_instruction(program::instruction::mfence());
            }
        }
        // END PROGRAM GENERATION

        _printf("Program built.");

        trigger_client.wait_for_ready_from_trigger();
        trigger_client.open_fifo_to_trigger();

        constexpr size_t NUM_CAPTURES = 4;
        constexpr size_t NUM_EXECS = 256;
        constexpr size_t TRIGGER_ITER = 64;

        // This generates NUM_CAPTURES * (NUM_EXECS/TRIGGER_ITER) captures in total.
        // => 2048 * (256/64) = 8192 captures

        // Note that with such small amount of microseconds slept, there is a significant overhead.
        constexpr long BETWEEN_ITERS_SLEEP_US = 20;
        constexpr long AFTER_EXEC_SLEEP_US = 20'000'000;

        _printf("Writing program to file.");
        prog.write_to_file("program.txt");

        _printf("Starting acquisition.");
        sleep(5);
        (void)system("./decoder/venv/bin/python3 ./decoder/acquire.py --start");

        for (size_t i = 0; i < NUM_CAPTURES; i++) {
            _printf("Execution round %zu...", i);
            for (size_t j = 0; j < NUM_EXECS; j++) {
                if (j == TRIGGER_ITER) {
                    trigger_client.send_trigger();
                }
                usleep(BETWEEN_ITERS_SLEEP_US);
                prog.execute();
            }
            usleep(AFTER_EXEC_SLEEP_US);
        }

        (void)system("./decoder/venv/bin/python3 ./decoder/acquire.py --stop");
        _printf("Stopped acquisition.");

        trigger_client.send_finished();
    }

    _printf("Workload completed!");
    return 0;
}
