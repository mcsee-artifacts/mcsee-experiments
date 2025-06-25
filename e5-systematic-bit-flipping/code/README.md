# scope-systematic-bit-flipping

This repository implements a workload that systematically flips bits in a specific "principal address" to completely reconstruct the address bits contributing to each addressing function.

> [!NOTE] 
> This approach assumes the address offset (offset between physical and DRAM/linear addresses) is known, as this is used as an input to the experiment. This can be determined, e.g., using a *DRAMA*-like tool.


For each principal address (of which there are as many as specified using the `--num` command line parameter), each bit in the linear/DRAM address is flipped individually. For each address (i.e., the principal and around 30 with a single flipped bit each), the virtual address is computed, and the address is put into a pool. In each iteration of the scope experiment, one of the addresses from the pool is "hammered" (i.e., accessed repeatedly). The accessed {virtual,physical,linear/DRAM} addresses are also saved to a metadata file, `exp_cfg.csv`.

## Usage

We require running the binary twice, once in trigger mode and once in workload mode. The trigger mode 
- To run the binary in trigger mode, run `sudo ./experiment --trigger`. 
- For running the binary in workload mode, see `./experiment --help`.

```
Usage: experiment [--help] [--version] [--trigger] [--superpages VAR] [--good-addr] [--uncached-mem] [--num VAR] [--offset VAR] [--keep-fixed VAR]

Optional arguments:
  -h, --help    	shows help message and exits
  -v, --version 	prints version information and exits
  --trigger     	run the trigger instead of the workload
  --superpages  	number of 1 GiB superpages to allocate
  --good-addr   	use principal addresses which allow for as many bit flips as possible
                  (may make choice of principal addresses very non-random)
  --uncached-mem	use uncached memory
  --num         	number of randomly picked addresses [default: 1]
  --offset      	DRAM offset in MiB (dram_addr=physical_addr-offset) [default: 0]
  --keep-fixed  	flips additional bits to keep this function fixed
```

## Analysis

The analysis script (`./scripts/analyze_experiment.py`) performs the following analysis:

It checks what bits in the different bits of the DRAM address (as seen by the scope) flipped whenever an individual address bit was flipped, allowing reconstruction of which address bits influence what bit of the bank group, bank, or row address.

## Automation

The experiment is automated by the `runner.sh` bash script. It requires some setup on the oscilloscope, the experiment machine, and the decoding server to work.

### Experiment machine
* Dependencies installed as explained following.
* `python3-venv` installed with your package manager, e.g., `apt` on Ubuntu.
* [`ddr5-decoder`](../../../mcsee-platform/ddr5-decoder/) checked out on the experiment machine.
* SSH public key access to the oscilloscope and the Research headnode.
* Passwordless `sudo` set up (to avoid `sudo` timeouts while running the experiment).

#### Dependencies

* [argparse.hpp](https://github.com/p-ranav/argparse) for argument parsing.  This library is header-only and vendored in the `lib/` subdirectory.
* [lib2ftd2xx](https://ftdichip.com/drivers/d2xx-drivers/) for low-level interaction with the FTDI device. This library has to be installed on the system where the code is to be run. A script is available to automatically install the library (`scripts/install_ftd2xx.sh`).
* [PTEditor](https://github.com/misc0110/PTEditor) for setting memory as uncached. This has to be installed on the system, and the kernel module needs to be loaded.

### Research headnode
- The oscilloscope's RAM disk mounted at `/mnt/scope-ramdisk`.
- This can be skipped if the oscilloscope can directly write data to a network-accessible data drive that the decoding host can reach.

### Decoding host
* [`ddr5-decoder`](../../../mcsee-platform/ddr5-decoder/) repository checked out and set up (with `venv` in `decoder/`).
* [`xmldig2csv-converter`](../../../mcsee-platform/xmldig2csv-converter/) repository checked out and set up.
