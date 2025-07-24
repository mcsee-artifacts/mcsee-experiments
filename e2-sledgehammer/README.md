# E2/E3: Sledgehammer

## Preparation

Obtain a copy of our modified fork of [Sledgehammer](https://github.com/mcsee-artifacts/sledgehammer). This fork of Sledgehammer:
- implements the Coffee Lake DRAM functions (see `main.c`),
- uses 1 GB superpages (see `USE_1GB` and `USE_THP` in `params.h`),
- exposes a compile-time parameter `-DNUM_BANKS=x` to make the number of banks to be hammered configurable, and
- hammers the banks in an endless loop to make the acquisition by McSee easier.

## Execution

Run Sledgehammer for a specific `NUM_BANKS` while capturing three traces of each 1 ms with McSee.

The result should be similar as the `XMLdig` files we provide in `mcsee-data/e2-sledgehammer/raw.tar.zst`. For convenience, we also provide the decoded files in `mcsee-data/e2-sledgehammer/decoded.tar.zst`.

## Analysis

> [!IMPORTANT]
> If you want to use the existing data, you must unpack first the `decoded.tar.zst` archive (located at `e2-sledgehammer/` in the mcsee-data repository) with
> ```
> zstd -d decoded.tar.zst --stdout | tar -xvf -
> ```

For the analysis of the activation throughput with the provided data, run:

```bash
python3 analysis/activation_throughput.py ${MCSEE_DATA}$/e2-sledgehammer/decoded/
```

where `${MCSEE_DATA}` is the path to the McSee data repository.

This will create the `sledgehammer-nbanks=X--00000_actspertrefi.pkl` files that serve as input for the plotting script.

For the analysis of the act-to-act distance, run:

```
python3 analysis/act2act_distance.py
```

This will create a file like the one in `../plotting/act2act_distances_per_bank.csv`, which serves as input for the plotting script.

> [!NOTE]
> Instead of using our [DDR4 decoder](https://github.com/mcsee-artifacts/ddr4-decoder) supporting a more complete DDR4 command set, our analysis uses a simpler decoder that is integrated in the [`process.py`](analysis/process.py) script.

## Results

The plots of the paper can be regenerated using the scripts in the `plotting/` directory:
- `activation_throughput/plot.py` generates Fig. 7
- `act2act_distances/plot.py` generates Fig. 8
