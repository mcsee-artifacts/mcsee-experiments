#!/usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt

def main():
    # --- Load measured data ---
    cols_measured = []
    means_measured = []
    with open("results_filtered.csv") as f:
        for line in f.readlines()[1:]:
            parts    = line.strip().split(",")
            num_cols = parts[1]
            mean     = parts[4]
            if num_cols == "2":
                continue
            cols_measured.append(int(num_cols))
            means_measured.append(float(mean))

    # --- Helper to map tAggON back to #blocks ---
    def tAggON_to_num_blocks(t):
        return int(round(np.interp(t, means_measured, cols_measured)))

    # --- Raw manufacturer data (tAggON, ACmin) ---
    # This data is taken from the Rowpress characterization data.
    mfrH_raw = [(36,33221.7), (66,26842.1), (96,24056.2), (186,20345.5), (336,18335.9)]
    mfrS_raw = [(36,28832.8), (66,23560.2), (96,21307.7), (186,18083.3), (336,16316.8)]
    mfrM_raw = [(36,20402.2), (66,16377.3), (96,14525.2), (186,12287.7), (336,10828.4)]

    mfrH = [(tAggON_to_num_blocks(x), y) for x,y in mfrH_raw]
    mfrS = [(tAggON_to_num_blocks(x), y) for x,y in mfrS_raw]
    mfrM = [(tAggON_to_num_blocks(x), y) for x,y in mfrM_raw]

    # --- LaTeX-style rcParams ---
    plt.rcParams.update({
        "text.usetex": False,
        "font.family": "serif",
        "axes.labelsize": 8,
        "font.size": 8,
        "legend.fontsize": 8,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "hatch.linewidth": 0.5,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })

    # --- Figure sizing to exact LaTeX column width ---
    fig_width_pt = 229.5
    inches_per_pt = 1.0 / 72.27
    golden_mean = ((np.sqrt(5) - 1.0) / 2.0) * 0.8
    fig_w = fig_width_pt * inches_per_pt
    fig_h = fig_w * golden_mean * 1.1

    fig, ax1 = plt.subplots(figsize=(fig_w, fig_h))
    ax2 = ax1.twinx()
    marker_size = 3.5

    # --- Plot measured on ax1 ---
    ln1, = ax1.plot(
        cols_measured, means_measured,
        marker='o', linestyle='-',
        color='blue', label='Avg. tAggON [ns]',
        zorder=10, markersize=marker_size
    )

    # --- Plot manufacturer curves on ax2 ---
    ln2, = ax2.plot(*zip(*mfrH),
                    marker='s', linestyle='-',
                    color='indianred', label='Mfr. H',
                    markersize=marker_size)
    ln3, = ax2.plot(*zip(*mfrS),
                    marker='^', linestyle='-',
                    color='orangered', label='Mfr. S',
                    markersize=marker_size)
    ln4, = ax2.plot(*zip(*mfrM),
                    marker='x', linestyle='-',
                    color='brown', label='Mfr. M',
                    markersize=marker_size)

    # --- Axis descriptions above the plot ---
   #  ax1.text(-0.122, 1.05, "Avg. tAggON [ns]",
   #           transform=ax1.transAxes,
   #           color='blue', ha='left', va='bottom', fontsize=9)
    ax2.text(1.135, 1.05, r"$\mathrm{AC}_\mathrm{min}$",
             transform=ax2.transAxes,
             color='darkred', ha='right', va='bottom', fontsize=8)

    # --- Tick configuration ---
    ax1.set_xlabel("#Cache block reads per aggr. row ACT")
    ax1.set_yticks(np.arange(0, 401, 100))
    ax1.set_yticks(np.arange(0, 401, 25), minor=True)
    ax2.set_yticks(np.arange(0, 40001, 10000))
    ax2.set_yticks(np.arange(0, 40001, 5000), minor=True)

    # X-axis ticks at specified positions
    xt = [1, 16, 32, 48, 64, 80, 128]
    ax1.set_xticks(xt)
    ax1.set_xticklabels([str(x) for x in xt])

    # Color tick labels & hide minors
    ax1.tick_params(axis='y', which='major', colors='blue', direction='out')
    ax1.tick_params(axis='y', which='minor', labelleft=False, colors='blue', length=3)
    ax2.tick_params(axis='y', which='major', colors='darkred', direction='out')
    ax2.tick_params(axis='y', which='minor', labelleft=False, colors='darkred', length=3)
    major_y2 = np.arange(0, 40001, 10000)
    ax2.set_yticklabels([f"{v//1000}K" for v in major_y2], color='darkred')

    # --- Grid & border styling ---
    ax1.grid(axis='y', which='major', linestyle='--', color='gray', linewidth=0.5)
    ax1.grid(axis='x', which='both', linestyle='')
    for sp in list(ax1.spines.values()) + list(ax2.spines.values()):
        sp.set_visible(True)
        sp.set_linewidth(0.8)

    # Measured‐curve legend on ax1 (label first, then marker), just above the axes:
    leg1 = ax1.legend(
       handles=[ln1],
       labels=['Avg. tAggON [ns]'],
       loc='upper left',
       bbox_to_anchor=(-0.167, 1.21),  # x=0 (left), y=110% (above)
       frameon=False,
       edgecolor='gray',
       markerfirst=False,
       labelcolor='blue',
       fontsize=8,
    )

    # Manufacturer legend on ax2 (upper right), unchanged:
    ax2.legend(
        handles=[ln2, ln3, ln4],
        labels=['Mfr. H', 'Mfr. S', 'Mfr. M'],
        loc='upper right',
        bbox_to_anchor=(1.015, 1.025),
        frameon=True,
        edgecolor='gray',
        ncols=3,
        borderpad=0.25,
        columnspacing=0.9
    )

    plt.savefig("rowpress_cols_vs_tAggON.pdf",
                dpi=600, bbox_inches='tight')

if __name__ == "__main__":
    main()
