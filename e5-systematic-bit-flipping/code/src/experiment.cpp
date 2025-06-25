#include "../lib/argparse.hpp"
#include "memory/function.hpp"
#include "trigger/trigger_main.hpp"
#include "utils.hpp"
#include "workload.hpp"

int main(int argc, char** argv) {
    argparse::ArgumentParser program("experiment");

    program.add_argument("--trigger")
        .help("run the trigger instead of the workload")
        .default_value(false)
        .implicit_value(true);

    program.add_argument("--superpages")
        .help("number of 1 GiB superpages to allocate")
        .scan<'i', size_t>();

    program.add_argument("--good-addr")
        .help("use principal addresses which allow for as many bit flips as possible "
              "(may make choice of principal addresses very non-random)")
        .default_value(false)
        .implicit_value(true);

    program.add_argument("--uncached-mem")
        .help("use uncached memory")
        .default_value(false)
        .implicit_value(true);

    program.add_argument("--num")
        .help("number of randomly picked addresses")
        .default_value((size_t)1)
        .scan<'i', size_t>();

    program.add_argument("--offset")
        .help("DRAM offset in MiB (dram_addr=physical_addr-offset)")
        .default_value((int64_t)0)
        .scan<'i', int64_t>();

    program.add_argument("--keep-fixed")
        .help("flips additional bits to keep this function fixed\n"
              "format: 0x12345678=1 (or =0)")
        .default_value("");

    // Parse arguments, or print help if that fails.
    try {
        program.parse_args(argc, argv);
    } catch (std::runtime_error const& err) {
        std::cerr << err.what() << std::endl;
        std::cerr << program;
        return 1;
    }

    // If ran in trigger mode, just run the trigger.
    if (program["--trigger"] == true) {
        return trigger::trigger_main();
    }

    // Check for required arguments (which are only required if --trigger is not given).
    if (!program.present<size_t>("--superpages")) {
        std::cerr
                << "ERROR: --superpages argument is required if --trigger is not given.\n";
        return 1;
    }

    auto num_superpages = program.get<size_t>("--superpages");
    auto num_addrs = program.get<size_t>("--num");
    auto use_good_addr = program["--good-addr"] == true;
    auto use_uncached_memory = program["--uncached-mem"] == true;
    // Convert offset from MiB to bytes.
    auto dram_offset = program.get<int64_t>("--offset") * (1 << 20);

    std::vector<memory::function_constraint> constraints;
    auto keep_fixed_str = program.get<std::string>("--keep-fixed");
    if (!keep_fixed_str.empty()) {
        auto equals_pos = keep_fixed_str.find("=", 0);
        if (equals_pos == std::string::npos) {
            std::cerr << "ERROR: supplied --keep-fixed argument without '='\n";
            return 1;
        }

        auto func_str = keep_fixed_str.substr(0, equals_pos);
        auto value_str = keep_fixed_str.substr(equals_pos + 1);

        if (!(value_str == "0" || value_str == "1")) {
            std::cerr << "ERROR: supplied --keep-fixed value that isn't '0' or '1'\n";
        }
        auto constraint_value = value_str[0] - '0';
        assert(constraint_value == 0 || constraint_value == 1);

        uint64_t constraint_func;
        try {
            constraint_func = std::stoull(func_str, nullptr, 16);
        } catch (std::invalid_argument const&) {
            std::cerr << "ERROR: supplied invalid --keep-fixed function\n";
            return 1;
        }
        constraints.emplace_back(constraint_func, constraint_value);
    }

    return workload::run(
        num_superpages,
        num_addrs,
        use_good_addr,
        use_uncached_memory,
        dram_offset,
        constraints
    );
}
