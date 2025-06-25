#include <cstdint>

#pragma once

namespace trigger {

constexpr char const* FIFO_WORKLOAD2RUNNER = "/tmp/workload2runner";
constexpr char const* FIFO_TRIGGER2WORKLOAD = "/tmp/trigger2workload";
constexpr char const* FIFO_WORKLOAD2TRIGGER = "/tmp/workload2trigger";

enum class workload_runner_cmds : uint8_t {
    INVALID = 0,
    WORKLOAD_READY = 1,
};

enum class trigger_workload_cmds : uint8_t {
    INVALID = 0,
    TRIGGER_READY = 1,
};

enum class workload_trigger_cmds : uint8_t {
    INVALID = 0,
    SEND_TRIGGER = 1,
    FINISHED_ITERATION = 2,
};

static_assert(sizeof(workload_runner_cmds) == 1);
static_assert(sizeof(trigger_workload_cmds) == 1);
static_assert(sizeof(workload_trigger_cmds) == 1);

};