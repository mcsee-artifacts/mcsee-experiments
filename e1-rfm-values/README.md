# E1: RFM Values

The SPD data of our DDR5 UDIMMs were obtained by our SPD decoder (`dump_spd_pretty.py` script), see the accompanying [README](https://github.com/mcsee-artifacts/spd-decoder/) for details.

We provide in `mcsee-data/e1-rfm-values/spd-decoder-output` the decoded SPD data from the DDR5 DIMMs in our test pool.

## Analyzing the data

The provided script [`analyze.py`](./analyze.py) can be used to automatically generate a table-like overview of all JSON files:

```
M1.json        0,  80,  6x     0,  80,  6x     0,  80,  6x     0, RFU, RFU     0, RFU, RFU     0, RFU, RFU
M2.json        0, RFU, RFU     0, RFU, RFU     0, RFU, RFU     0, RFU, RFU     0, RFU, RFU     0, RFU, RFU
M3.json        1,  80,  4x     1,  80,  4x     1,  80,  4x     0, RFU, RFU     0, RFU, RFU     0, RFU, RFU
M4.json        1,  80,  4x     1,  80,  4x     1,  80,  4x     0, RFU, RFU     0, RFU, RFU     0, RFU, RFU
...

--- Summary Statistics ---
Total files parsed: 29
Files with non-'RFU' RAAIMT/RAAMMT values: 17
Files containing '1' for 'rfm_req': 4
```

The script prints for each SDRAM (`sdram_0`, `sdram_1`) and each ARFM level (`A`, `B`, `C`), an RFM configuration tuple (`RFM Required`, `RAAIMT`, `RAAMMT`).

Run the script as follows:
```
python3 analyze.py <path-to-JSON-directory>
```
