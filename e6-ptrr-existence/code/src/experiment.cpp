#include "../lib/argparse.hpp"
#include "trigger/trigger_main.hpp"
#include "utils.hpp"
#include "workload.hpp"

int main(int argc, char** argv) {
    argparse::ArgumentParser program("experiment");

    program.add_argument("--trigger")
            .help("run the trigger instead of the workload")
            .default_value(false)
            .implicit_value(true);

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

    return workload::run();
}
