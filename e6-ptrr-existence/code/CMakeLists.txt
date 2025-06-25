cmake_minimum_required(VERSION 3.22)

project(scope-ordering-exploration)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_FLAGS "-O2 -Wall -Wextra -Wno-unused-result -Wno-unused-function -Wno-strict-aliasing")

add_executable(experiment
    src/experiment.cpp
    src/memory/allocation.cpp
    src/memory/dram_address.cpp
    src/memory/pagemap.cpp
    src/program/instruction.cpp
    src/program/program.cpp
    src/trigger/client.cpp
    src/trigger/trigger_main.cpp
    src/utils.cpp
    src/workload.cpp
)

configure_file(src/config.hpp.in src/config.hpp)
target_include_directories(experiment PUBLIC ${CMAKE_CURRENT_BINARY_DIR}/src)

target_link_libraries(experiment pthread ftd2xx rt)
