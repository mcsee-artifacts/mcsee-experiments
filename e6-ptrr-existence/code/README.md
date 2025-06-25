# Intel pTRR Experiment

The workload in this experiment hammers two same-bank rows that are a randomly chosen distance apart (more precisely, between 8 and 15 rows apart).

## Build and Run

The single binary can be built using CMake:

```sh
$ cmake -B build
$ make -j -C build
```

To run the workload, inspect the required and optional arguments with
`./build/experiment --help`, and then run the binary with the arguments wanted.
Superuser privileges are required (for translating virtual to physical addresses
using `/proc/self/pagemap`).

To run the trigger process, run
```
sudo ./build/experiment --trigger
```

## Runner Script

The processes are orchestrated by a runner script (`runner.sh`), which handles
various other tasks such as copying around/managing experiment files.

## Dependencies

The code contains following main dependencies:

* [argparse.hpp](https://github.com/p-ranav/argparse) for argument parsing.
  This library is header-only and vendored in the `lib/` subdirectory.
* [lib2ftd2xx](https://ftdichip.com/drivers/d2xx-drivers/) for low-level 
  interaction with the FTDI device. This library has to be installed on the
  system where the code is to be run.
* [PTEditor](https://github.com/misc0110/PTEditor) for setting memory as
  uncached. This has to be installed on the system, and the kernel module needs
  to be loaded.
