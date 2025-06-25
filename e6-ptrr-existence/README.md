# E6: pTRR Existence


## Preparation

Follow the instructions in the [`code/README.md`](./code/README.md) file to build the experiment code.

Adapt the [`code/runner.sh`](./code/runner.sh) script depending on your environment.

## Execution

Run the experiment code with the `runner.sh` script. If properly configured, the experiment code will automatically trigger the scope acquisition and take a configurable amount of captures (see [`workload.cpp`](code/src/workload.cpp), lines 81-86).

## Analysis

The following assumes that the oscilloscope traces have already been decoded using the [DDR5 decoder](https://github.com/mcsee-artifacts/ddr5-decoder). For convenience, we provide the already decoded trace files in `mcsee-data/e6-ptrr-existence`.

First, run the `analysis/split_trace_into_blocks.py` script to split the decoded trace into blocks. Each of the blocks is a hammering iteration. As we sleep between hammering iterations (see [`workload.cpp`](code/src/workload.cpp), line 101), we can use this to detect when a block finished executing. This generates a `block_xxx.csv` file per hammering iteration.

```bash
python3 analysis/split_trace_into_blocks.py ${MCSEE_DATA}/e6-ptrr/existence
```

where `${MCSEE_DATA}` is the location of the McSee data repository.

## Result

We take a random sample `plotting/block_002.csv` in which we manually identified a pTRR event to show that aggressor-adjacent rows are activated.

To regenerate Fig. 10 of the paper, run:
```bash
python3 plotting/plot_single.py plotting/block_002.csv
```
