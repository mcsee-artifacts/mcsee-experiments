#include <array>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <memory>
#include <stdexcept>
#include <sys/resource.h>
#include <sys/stat.h>
#include <unistd.h>

#include "utils.hpp"

void utils::set_cpu_affinity(int core_id) {
    // assign this process to one of the system's (P)erformance cores
    cpu_set_t mask;
    CPU_ZERO(&mask);
    CPU_SET(core_id, &mask);
    if (sched_setaffinity(0, sizeof(cpu_set_t), &mask) == -1) {
        printf("[-] could not set CPU affinity:\n");
        perror("sched_setaffinity");
        exit(EXIT_FAILURE);
    }
}

void utils::set_cpu_priority() {
    // give this process the highest CPU priority, so it does get interrupted less frequently by the scheduler
    if (setpriority(PRIO_PROCESS, 0, PRIO_MIN) != 0) {
        printf("[-] setpriority failed\n");
        exit(EXIT_FAILURE);
    }
}

double utils::sdm(const uint64_t* data, size_t start, size_t end) {
    // compute the mean for data[start]...data[end]
    double mean = 0;
    for (size_t i = start; i < end; ++i)
        mean += (double)data[i];
    mean = mean / ((double)(end - start));
    // compute the sum of deviations, i.e., sum over (data[i]-mean)^2 for all i
    double deviation = 0;
    for (size_t i = start; i < end; ++i)
        deviation += std::pow((double)data[i] - mean, 2);
    return deviation;
}

void utils::check_runas_sudo() {
    // check if program is run with root privileges
    if (getuid()) {
        printf("[-] program needs to be run with sudo!\n");
        exit(EXIT_FAILURE);
    }
}

void utils::empty_signalhandler(int) { }

bool utils::is_fifo(const char* path) {
    struct stat stat_buf {};
    if (stat(path, &stat_buf) < 0) {
        _printf("could not stat path '%s'", path);
        perror("stat");
        exit(EXIT_FAILURE);
    }

    return S_ISFIFO(stat_buf.st_mode) != 0;
}
