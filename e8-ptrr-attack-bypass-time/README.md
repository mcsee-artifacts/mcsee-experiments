# E8: pTRR Attack Success Rate

The MATLAB script `calculate_prob.mlx` calculates based on the pTRR probability of 0.091% (defined as `pth` in line 2) how long it would take to bypass it for a specific Rowhammer threshold. The calculation is based on previous work HiRA by Yağlikçi et al. (§9.1.2). The result is a plot as Fig. 12 in our paper.

## 📈 Running the `calculate_prob.mlx` MATLAB Script

### 🧰 Requirements

- MATLAB R2021a or newer (Live Script + plotting support)
- No external inputs or toolboxes needed

### 🔧 Inputs

This script does not take external input arguments — all parameters are set internally:

- **Rowhammer threshold range (`RTH`)**: 1,000 to 30,000 (in steps of 1,000)
- **Fixed constants**:
  - Bit flip threshold probability: `pth = 0.091 / 100 * 2`
  - Attack interval: every 32 ms (DDR5)
  - Evaluation time windows: 1 hour, 1 day, 1 week

> 💡 To customize the model (e.g., attack interval or bit flip threshold), modify the constants defined at the top of the script.

### 📤 Outputs

- A vector plot file: **`plot_atk_success_rate.pdf`** showing:
  - Success probability vs. Rowhammer threshold
  - Curves for 1 Hour, 1 Day, and 1 Week attack durations

### 🚀 How to Run

1. **Open MATLAB** and change to the script’s directory:

   `cd /path/to/script`

2. **Run the script**:

   `open('calculate_prob.mlx')`

   Then click **"Run"** in the Live Editor, or press **F5**.

3. The script will:
   - Compute attack success probabilities over increasing Rowhammer thresholds
   - Generate a high-quality publication-ready PDF plot: `plot_atk_success_rate.pdf`

### 📎 Notes

- The Y-axis of the plot shows the **probability of at least one successful attack** within the specified time window.
- The X-axis is labeled as **"Rowhammer Threshold"** (with tick labels in thousands, e.g., 5K, 10K, ...).
- The plot uses LaTeX-styled labels and exports as a vector PDF for use in papers or presentations.
