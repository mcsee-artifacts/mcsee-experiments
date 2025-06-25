# E7: pTRR Probability

Follow the exact same instructions as in the `README` of the [`e6-ptrr-existence`](../e6-ptrr-existence/) experiment for the preparation, execution, and analysis steps.

## Analysis

Run the `analysis/extract_events.py` script to extract the mitigation events from the `block_xxx.csv` files. Mitigation events describe when a TRR happened and which rows were involved (i.e., aggressor and victim rows). 
```bash
python3 analysis/extract_events.py ${MCSEE_DATA}/e6-ptrr-existence/20240414_044124_ee-tik-cn120_DIMM=519_overnight_run_intelptrr_remake
```
where `$MCSEE_DATA` is the path to the McSee data repository.

This will generate a file `mitigation_events.json` in the subdirectory `data/` with the pTRR events.

## Result

To regenerate Fig. 8 of the paper, run the `plot_determine_probability.py` script by passing the `mitigation_events.json` file:

```bash
python3 plotting/plot_determine_probability.py ${MCSEE_DATA}/e6-ptrr-existence/20240414_044124_ee-tik-cn120_DIMM=519_overnight_run_intelptrr_remake/data/mitigation_events.json
```
