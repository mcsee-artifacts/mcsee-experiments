#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <unistd.h>
#include <fcntl.h>

#include "client.hpp"
#include "protocol.hpp"
#include "../utils.hpp"

namespace trigger {

client::client() {
    // Check all required FIFOs exist.
    if (!utils::is_fifo(FIFO_WORKLOAD2RUNNER) ||
        !utils::is_fifo(FIFO_TRIGGER2WORKLOAD) ||
        !utils::is_fifo(FIFO_WORKLOAD2TRIGGER)) {
        _printf("the required FIFOs do not exist");
    }
}

client::~client() {
    if (fd_trigger2workload >= 0) {
        close(fd_trigger2workload);
    }
    if (fd_workload2trigger >= 0) {
        close(fd_workload2trigger);
    }
}

// NOLINTNEXTLINE(readability-convert-member-functions-to-static)
void client::send_ready_to_runner() {
    _printf("signaling READY to runner script");

    int fd = open(FIFO_WORKLOAD2RUNNER, O_WRONLY);
    if (fd < 0) {
        _printf("ERROR: failed opening the workload2runner FIFO.");
        exit(EXIT_FAILURE);
    }

    auto cmd = workload_runner_cmds::WORKLOAD_READY;
    (void)write(fd, &cmd, sizeof(cmd));
    close(fd);
}

void client::wait_for_ready_from_trigger() {
    // Open FIFO if not already open.
    if (fd_trigger2workload < 0) {
        fd_trigger2workload = open(FIFO_TRIGGER2WORKLOAD,
                                   O_RDONLY | O_NONBLOCK);
        if (fd_trigger2workload < 0) {
            _printf("ERROR: failed opening the trigger2workload FIFO.");
            perror("open");
            exit(EXIT_FAILURE);
        }
    }

    auto cmd = trigger_workload_cmds::INVALID;
    do {
        usleep(500'000); // 500 ms
        (void)read(fd_trigger2workload, &cmd, sizeof(cmd));
    } while (cmd != trigger_workload_cmds::TRIGGER_READY);
}

void client::open_fifo_to_trigger() {
    if (fd_workload2trigger > 0) {
        close(fd_workload2trigger);
        fd_workload2trigger = -1;
    }

    fd_workload2trigger = open(FIFO_WORKLOAD2TRIGGER, O_WRONLY);
    if (fd_workload2trigger < 0) {
        _printf("ERROR: Failed opening the workload2trigger FIFO.");
        perror("open");
        exit(EXIT_FAILURE);
    }

    _printf("Successfully opened the workload2trigger FIFO, ready to send trigger commands.");
}

}
