#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fcntl.h>
#include <ftd2xx.h>
#include <unistd.h>

#include "trigger_main.hpp"
#include "protocol.hpp"
#include "../utils.hpp"

static int connect_ftdi_dev(FT_HANDLE& ftHandle) {
    char* pcBufLD[2];
    char cBufLD[1][64];

    pcBufLD[0] = cBufLD[0];
    pcBufLD[1] = nullptr;
    memset(cBufLD, 0, sizeof(cBufLD));

    FT_STATUS ftStatus;
    int iNumDevs = 0;
    ftStatus = FT_ListDevices(
            pcBufLD, // a ptr to an array of ptrs to buffers to contain the appropriate strings
            &iNumDevs, //  ptr to a DWORD location to store the number of currently connected devices
            FT_LIST_ALL | FT_OPEN_BY_SERIAL_NUMBER);
    if (ftStatus != FT_OK) {
        printf("Error: FT_ListDevices(%d)\n", (int)ftStatus);
        return EXIT_FAILURE;
    }

    if ((ftStatus = FT_OpenEx(cBufLD[0], FT_OPEN_BY_SERIAL_NUMBER,
                              &ftHandle)) != FT_OK) {
        printf("Error FT_OpenEx(%d), device %d serial number \"%s\"\n"
               "Use lsmod to check if ftdi_sio (and usbserial) are present.\n"
               "If so, unload them using rmmod, as they conflict with ftd2xx.\n",
               (int)ftStatus, 0, cBufLD[0]);
        return EXIT_FAILURE;
    }

    return EXIT_SUCCESS;
}

static void disconnect_ftdi_dev(FT_HANDLE& ftHandle) {
    FT_Close(ftHandle);
}

static void toggle_rts(const FT_HANDLE& ftHandle) {
    FT_ClrRts(ftHandle);
    usleep(100);
    FT_SetRts(ftHandle);
}

int trigger::trigger_main() {
    // Check the required FIFOs exist.
    if (!utils::is_fifo(FIFO_TRIGGER2WORKLOAD)
        || !utils::is_fifo(FIFO_WORKLOAD2TRIGGER)) {
        _printf("the required FIFOs do not exist");
        return 1;
    }

    // Turn of buffering of STDOUT.
    setbuf(stdout, nullptr);

    // Make sure this process runs on another core than the workload, and does
    // not get rescheduled.
    // See output of `lscpu  --all --extended` for CPU IDs.
    utils::set_cpu_affinity(3);
    utils::set_cpu_priority();

    // Set up FTDI device used for triggering.
    FT_HANDLE ftHandle;
    auto ret = connect_ftdi_dev(ftHandle);
    if (ret != 0) {
        _printf("[-] could not connect to FTDI device!");
        return 1;
    }

    // Open trigger-to-workload FIFO.
    int fd_trigger2workload;
    fd_trigger2workload = open(FIFO_TRIGGER2WORKLOAD, O_WRONLY);
    if (fd_trigger2workload < 0) {
        _printf("[-] failed opening the trigger2workload FIFO.");
        return 1;
    }

    _printf("opened trigger2workload for writing successfully.");

    // Give start command to workload.
    usleep(500);
    auto write_cmd = trigger_workload_cmds::TRIGGER_READY;
    (void)write(fd_trigger2workload, &write_cmd, sizeof(write_cmd));
    close(fd_trigger2workload);

    // Open workload-to-trigger FIFO. This is how the workload will send us
    // the instruction to trigger.
    int fd_workload2trigger;
    fd_workload2trigger = open(FIFO_WORKLOAD2TRIGGER, O_RDONLY);
    if (fd_workload2trigger < 0) {
        _printf("ERROR: trigger failed opening the workload2trigger fifo.");
        return 1;
    }

    // This is to avoid interleaved printf.
    usleep(rand() % 300); // NOLINT(cert-msc50-cpp)
    _printf("trigger successfully opened the workload2trigger FIFO");

    // Respond to commands from workload.
    workload_trigger_cmds read_cmd;
    while (true) {
        // Blocking read from FIFO.
        (void)read(fd_workload2trigger, &read_cmd, sizeof(read_cmd));

        switch (read_cmd) {
            case workload_trigger_cmds::SEND_TRIGGER:
                // Toggle the voltage.
                toggle_rts(ftHandle);
                break;
            case workload_trigger_cmds::FINISHED_ITERATION:
                // The workload signals that the current iteration has ended. Return
                // from this function (and terminate the process). The runner script
                // will start another trigger process for the next iteration.
                goto out;
            default:
                _printf("Received invalid command on workload2trigger FIFO: 0x%02x",
                        (uint8_t)read_cmd);
        }
    }

out:
    // Give the scope a bit of time to make sure the last command has been
    // received.
    usleep(700);

    // Clean up.
    close(fd_workload2trigger);
    disconnect_ftdi_dev(ftHandle);

    return 0;
}
