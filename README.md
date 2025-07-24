## Experiments

We list in the following the experiments of our papers (see Artifacts Appendix), identified by their experiment ID, and provide the respective section in the paper, references to figures and tables with results, and the folder name where to find the experiment.

| **ID**                               | **Section**                               | **Reference** | **Folder Name** (experiments/)                                          |
|--------------------------------------|-------------------------------------------|---------------|-------------------------------------------------------------------------|
| E1 (RFM values)                      | 6.1 (RFM on DDR5 Devices)                 | Tbl. 7        | [e1-rfm-values](./e1-rfm-values/)                           |
| E2 (Sledgehammer: ACT Throughput)    | 5.1 (Sledgehammer: Activation Throughput) | Fig. 7        | [e2-sledgehammer](./e2-sledgehammer/)                       |
| E3 (Sledgehammer: access reordering) | 5.1 (Sledgehammer: Activation Throughput) | Fig. 8        | [e2-sledgehammer](./e2-sledgehammer/)                       |
| E4 (Rowpress: row-open time)         | 5.2 (RowPress: Row-Open Time)             | Fig. 8        | [e4-rowpress](./e4-rowpress/)                               |
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
