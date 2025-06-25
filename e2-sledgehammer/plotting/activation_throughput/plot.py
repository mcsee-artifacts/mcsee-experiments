#!/usr/bin/env python3

import matplotlib.pyplot as plt
import numpy as np
import glob
import os
import pickle
import sys

# Unified LaTeX-style plot settings
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

# Set figure size to exactly 229.5 pt width
fig_width_pt = 229.5
inches_per_pt = 1.0 / 72.27
golden_mean = ((np.sqrt(5) - 1.0) / 2.0) * 0.8
fig_width = fig_width_pt * inches_per_pt
fig_height = fig_width * golden_mean

fig, ax1 = plt.subplots(figsize=(fig_width, fig_height))
ax2 = ax1.twinx()

nbanks = list(range(1, 17))
all_data_median = []
all_data_median_per_bank = []

# Generate mock data
for num_banks in nbanks:
   cur_bank = []
   for file in glob.glob("../data/pickled/sledgehammer-nbanks={num_banks}--0000?_actspertrefi.pkl"):
      with open(file, 'rb') as f:
         vals = pickle.load(f)
         for x in vals:
            cur_bank.append(int(x))
   all_data_median.append(np.mean(cur_bank))
   all_data_median_per_bank.append(np.mean(cur_bank)//num_banks)


line_color = 'tab:red'
bar_color = 'tab:blue'

# Plot left axis
p1, = ax1.plot(
    [str(x) for x in nbanks],
    all_data_median_per_bank,
    marker='o',
    markersize=3,
    linestyle='-',
    color=line_color,
    label='ACTs per tREFI / bank'
)

ax1.set_ylim(0, 150)
xticklabels = [str(x) if x % 2 == 1 else "" for x in nbanks]
ax1.set_xticks(range(len(nbanks)))
ax1.set_xticklabels(xticklabels)
ax1.set_yticks(np.arange(0, 151, 30))
ax1.set_yticks(np.arange(0, 150, 10), minor=True)
ax1.set_ymargin(0)

# ✅ Update x-axis label
ax1.set_xlabel("#Hammered Banks")

ax1.set_ylabel("")
ax1.tick_params(axis='y', colors=line_color, direction='out')
ax1.tick_params(axis='x', direction='out')

# Plot right axis bars
bars = ax2.bar(
    [str(x) for x in nbanks],
    all_data_median,
    color=bar_color,
    width=0.6,
    label='Total ACT Throughput'
)

ax2.set_ylim(0, 750)
ax2.set_ylabel("")
ax2.set_yticks(np.arange(0, 751, 150))
ax2.set_yticks(np.arange(0, 750, 50), minor=True)
ax2.set_ymargin(0)
ax2.tick_params(axis='y', colors=bar_color, direction='out')

# Manual y-axis label placement (with spacing adjustment)
# ax1.text(
#     -0.14, 1.06, "ACTs/tREFI\nper Bank",
#     transform=ax1.transAxes,
#     ha='left',
#     va='bottom',
#     fontsize=9,
#     linespacing=0.8,
#     color=line_color
# )

# ax2.text(
#     1.14, 1.06, "Total ACT\nThroughput",
#     transform=ax2.transAxes,
#     ha='right',
#     va='bottom',
#     fontsize=9,
#     linespacing=0.8,
#     color=bar_color
# )
ax2.text(
    1.14, 1.06, " \n",
    transform=ax2.transAxes,
    ha='right',
    va='bottom',
    fontsize=8,
    linespacing=0.8,
    color=bar_color
)

# Grid
ax1.grid(axis='y', which='major', linestyle='--', color='gray', linewidth=0.5)
ax1.grid(axis='x', which='both', linestyle='')  # no vertical grid
ax1.set_axisbelow(True)
ax2.set_axisbelow(False)
ax1.set_zorder(2)
ax2.set_zorder(1)
ax1.patch.set_visible(False)

# Borders
for spine in ax1.spines.values():
    spine.set_visible(True)
    spine.set_linewidth(0.8)
for spine in ax2.spines.values():
    spine.set_visible(True)
    spine.set_linewidth(0.8)

# Legend (centered above the plot, moved further up)
handles = [p1]
labels = ['ACTs/tREFI\nper bank']
fig.legend(
    handles, labels,
    loc='upper center',
    frameon=False,
    framealpha=1.0,
    edgecolor='gray',
    fontsize=8,
    ncol=1,
    bbox_to_anchor=(0.16, 1.08),
    # remove column spacing
    columnspacing=0.9,
    markerfirst=False,
    labelcolor=line_color
)
handles = [bars[0]]
labels = ['Total ACT\nThroughput']
leg = fig.legend(
    handles, labels,
    loc='upper center',
    frameon=False,
    framealpha=1.0,
    edgecolor='gray',
    fontsize=8,
    ncol=1,
    bbox_to_anchor=(0.825, 1.08),
    columnspacing=0.9,
    markerfirst=True,
    labelcolor=bar_color
)
for txt in leg.get_texts():
    txt.set_ha('right')

plt.tight_layout(pad=0.2)
plt.savefig("sledgehammer_plot.pdf", dpi=72, bbox_inches='tight', pad_inches=0.02)
# plt.show()
