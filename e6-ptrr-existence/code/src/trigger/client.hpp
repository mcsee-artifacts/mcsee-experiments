#include <cassert>
#include <unistd.h>
#include "protocol.hpp"

#pragma once

namespace trigger {

/*
 * Wrapper for FIFO communication for the workload. Communicates with the
 * trigger process and the runner script via FIFOs.
 */
class client {
public:
    client();
    ~client();

    /*
     * Signals to the runner script that the workload has finished
     * initialization and it can enter the main experiment iteration loop, where
     * the trigger process is started.
     */
    void send_ready_to_runner();

    void wait_for_ready_from_trigger();

    void open_fifo_to_trigger();

    void send_trigger() { // NOLINT(readability-make-member-function-const)
        assert(fd_workload2trigger > 0);
        auto cmd = workload_trigger_cmds::SEND_TRIGGER;
        (void)write(fd_workload2trigger, &cmd, sizeof(cmd));
    }

    void send_finished() { // NOLINT(readability-make-member-function-const)
        assert(fd_workload2trigger > 0);
        auto cmd = workload_trigger_cmds::FINISHED_ITERATION;
        (void)write(fd_workload2trigger, &cmd, sizeof(cmd));
    }

private:
    int fd_trigger2workload { -1 };
    int fd_workload2trigger { -1 };
};

}
