#!/bin/bash

silent_pushd() {
   pushd "$1" > /dev/null
}

silent_popd() {
   popd > /dev/null
}

check_status() {
   if [ $? -eq 0 ]; then
      echo " OK"
   else
      echo "FAILED!"
   fi
}

# Check if inside a Python virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
   echo "Error: You are not inside a Python virtual environment."
   echo "Please activate your venv before running this script."
   exit 1
fi

# Check if requirements.txt exists
if [[ ! -f "requirements.txt" ]]; then
   echo "Error: requirements.txt not found in the current directory."
   exit 1
fi

# Install required packages
echo "[>] Installing Python packages.."
pip install -r requirements.txt > /dev/null 2>&1

DATA=$(realpath "$(pwd)/../../mcsee-data")
echo "[>] Using data directory: $DATA"
OUTPUT=$(pwd)/figures
echo "[>] Output directory for figures: $OUTPUT"

# Remove all pdf and txt files from the output directory
if [[ -d "$OUTPUT" ]]; then
    echo "[>] Cleaning up old figures in $OUTPUT..."
    rm -f "$OUTPUT"/*.pdf "$OUTPUT"/*.txt
fi

# E1 (RFM values)	- Generating Tbl. 7
silent_pushd e1-rfm-values
echo -n "[>] Generating table for E1 (RFM values)..."
python3 analyze.py ${DATA}/e1-rfm-values/spd-decoder-output > $OUTPUT/table-7.txt
check_status
silent_popd

# E2 (Sledgehammer)	- Generating Fig. 7
silent_pushd e2-sledgehammer/plotting/activation_throughput
echo -n "[>] Generating figure for E2 (Sledgehammer: ACT Throughput)..."
python3 plot.py > /dev/null
check_status
mv sledgehammer_plot.pdf $OUTPUT/figure-7.pdf
silent_popd

# E3 (Sledgehammer)	- Generating Fig. 8
silent_pushd e2-sledgehammer/plotting/act2act_distances
echo -n "[>] Generating figure for E3 (Sledgehammer: access reordering)..."
python3 plot.py --data-path "${DATA}/e2-sledgehammer/decoded/" > /dev/null
check_status
mv sledgehammer_act2actdistances.pdf $OUTPUT/figure-8.pdf
silent_popd

# E4 (Rowpress) - Generating Fig. 9
echo -n "[>] Generating figure for E4 (Rowpress: row-open time)..."
silent_pushd e4-rowpress/plotting
python3 plot.py > /dev/null
check_status
mv rowpress_cols_vs_tAggON.pdf $OUTPUT/figure-9.pdf
silent_popd

# E6 (Existence of pTRR) - Generating Fig. 10
echo -n "[>] Generating figure for E6 (Existence of pTRR)..."
silent_pushd e6-ptrr-existence/plotting
python3 plot_single.py block_002.csv > /dev/null
check_status
echo "    NOTE: The broken x-axis and styling of the plot were done manually post-plot generation."
mv plot_rfm_intel_ptrr_full.pdf $OUTPUT/figure-10.pdf
silent_popd 

# E7 (pTRR probability) - Generating Fig. 11
echo -n "[>] Generating figure for E7 (pTRR probability)..."
silent_pushd e7-ptrr-probability/plotting
python3 plot_determine_probability.py ${DATA}/e6-ptrr-existence/20240414_044124_ee-tik-cn120_DIMM=519_overnight_run_intelptrr_remake/data/mitigation_events.json
check_status
mv plot_intel_ptrr_distribution_128iters_2aggs_8kacts_new.pdf $OUTPUT/figure-11.pdf
silent_popd

# E8 (pTRR attack-bypass time) - Generating Fig. 12
echo -n "[>] Generating figure for E8 (pTRR attack-bypass time)..."
silent_pushd e8-ptrr-attack-bypass-time
python3 calculate_prob.py > /dev/null
check_status
echo "    NOTE: The script for E8 is ported from the original MATLAB code and the plot style may be slightly different."
mv plot_atk_success_rate.pdf $OUTPUT/figure-12.pdf
silent_popd
