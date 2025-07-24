## Experiments

We list in the following the experiments of our papers (see Artifacts Appendix), identified by their experiment ID, and provide the respective section in the paper, references to figures and tables with results, and the folder name where to find the experiment.

| **ID**                               | **Section**                               | **Reference** | **Folder Name** (experiments/)                                          |
|--------------------------------------|-------------------------------------------|---------------|-------------------------------------------------------------------------|
| E1 (RFM values)                      | 6.1 (RFM on DDR5 Devices)                 | Tbl. 7        | [e1-rfm-values](./e1-rfm-values/)                           |
| E2 (Sledgehammer: ACT Throughput)    | 5.1 (Sledgehammer: Activation Throughput) | Fig. 7        | [e2-sledgehammer](./e2-sledgehammer/)                       |
| E3 (Sledgehammer: access reordering) | 5.1 (Sledgehammer: Activation Throughput) | Fig. 8        | [e2-sledgehammer](./e2-sledgehammer/)                       |
| E4 (Rowpress: row-open time)         | 5.2 (RowPress: Row-Open Time)             | Fig. 9        | [e4-rowpress](./e4-rowpress/)                               |
| E5 (Systematic bit flipping)         | 6.2 (DRAM Addressing Functions)           | Tbl. 3        | [e5-systematic-bit-flipping](./e5-systematic-bit-flipping/) |
| E6 (Existence of pTRR)               | 6.3 (RFM on Memory Controllers)           | Fig. 10       | [e6-ptrr-existence](./e6-ptrr-existence/)                   |
| E7 (pTRR probability)                | 6.4 (Reverse Engineering Intel's pTRR)    | Fig. 11       | [e7-ptrr-probability](./e7-ptrr-probability/)               |
| E8 (pTRR attack-bypass time)         | 6.4 (Reverse Engineering Intel's pTRR)    | Fig. 12       | [e8-ptrr-attack-bypass-time](./e8-ptrr-attack-bypass-time/) |


### Plotting Dependencies

Before generating any plots, create a new Python virtual environment and install the packages listed in the [`requirements.txt`](./requirements.txt) file:

```
python3 -m venv venv \
   && source venv/bin/activate \
   && pip install -r requirements.txt
```

### Reproducing figures

We provide a single script [reproduce-figures.sh](./reproduce-figures.sh) that regenerates the figures from our paper and saves them in the [`figures/`](./figures/) directory. 

The script assumes that you have the unpacked and decompressed mcsee-data archive available and that your folder structure looks as follows:
```
mcsee-artifacts-workspace/
├── comsec-group
│   ├── LICENSE
│   └── README.md
├── mcsee-artifacts-github
│   ├── ddr4-decoder
│   ├── ddr5-decoder
│   ├── ddr5-udimm-interposer-pcb
│   ├── mcsee-experiments
│   ├── spd-decoder
│   └── xmldig2csv-converter
└── mcsee-data
    ├── e1-rfm-values
    │   └── spd-decoder-output
    ├── e2-sledgehammer
    │   ├── decoded
    │   └── raw
    ├── e4-rowpress
    │   ├── decoded
    │   ├── pickled
    │   └── raw
    ├── e5-systematic-bit-flipping
    │   ├── amd_zen4
    │   └── intel_raptor_lake
    ├── e6-ptrr-existence
    │   └── 20240414_044124_ee-tik-cn120_DIMM=519_overnight_run_intelptrr_remake
    ├── prepare_data.sh
    └── README.md
```
This structure can automatically be created by following the "Quickstart" instructions in the [`README`](https://github.com/mcsee-artifacts/.github/blob/main/profile/README.md) of the mcsee-artifacts organization.

Run the script with 
```
chmod +x reproduce-figures.sh
./reproduce-figures.sh
```
