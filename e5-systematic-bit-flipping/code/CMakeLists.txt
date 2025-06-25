cmake_minimum_required(VERSION 3.22)

project(scope-systematic-bit-flipping)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_FLAGS "-O2 -Wall -Wextra -Wno-unused-result -Wno-unused-function -Wno-strict-aliasing")

add_executable(experiment
    src/experiment.cpp
    src/memory/address_generator.cpp
    src/memory/allocation.cpp
    src/memory/pagemap.cpp
    src/trigger/client.cpp
    src/trigger/trigger_main.cpp
    src/utils.cpp
    src/workload.cpp
)

target_link_libraries(experiment pthread ftd2xx rt)
