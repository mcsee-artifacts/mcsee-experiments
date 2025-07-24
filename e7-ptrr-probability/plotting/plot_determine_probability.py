#!/usr/bin/env python3
import json
import math
import statistics
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MultipleLocator, AutoMinorLocator

# ── LaTeX‐style settings ───────────────────────────────────────────────────────
plt.rcParams.update({
    "text.usetex": False,
    "font.family": "serif",
    "axes.labelsize": 8,
    "font.size": 8,
    "legend.fontsize": 8,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

def main():
    # ── I/O setup ──────────────────────────────────────────────────────────────
    in_file = Path(sys.argv[1])
    out_file = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("plot_intel_ptrr_distribution.pdf")

    # ── Load JSON data ─────────────────────────────────────────────────────────
    with in_file.open() as f:
        data = json.load(f)

    block_act_counts   = []
    block_event_counts = []
    for block in data:
        block_act_counts.append(block["num_acts"])
        block_event_counts.append(len(block["events"]))

    num_blocks   = len(data)
    total_events = sum(block_event_counts)
    total_acts   = sum(block_act_counts)
    p = total_events / total_acts

    # ── Compute distribution & binomial model ──────────────────────────────────
    max_events = max(block_event_counts)
    counts = np.zeros(max_events + 1, dtype=int)
    for ev in block_event_counts:
        counts[ev] += 1

    x = np.arange(len(counts))
    n = round(statistics.mean(block_act_counts))
    dist = np.array([math.comb(n, k) * (1-p)**(n-k) * p**k for k in x])

    # ── Figure sizing to 229.5 pt width, reduced margins ────────────────────────
    fig_width_pt = 229.5*1.05
    inches_per_pt = 1.0 / 72.27
    golden_mean = ((np.sqrt(5) - 1.0) / 2.0) * 0.8
    fig_w = fig_width_pt * inches_per_pt
    fig_h = fig_w * golden_mean * 1.0

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    # shrink left, bottom, top margins
    fig.subplots_adjust(left=0.12, right=0.98, bottom=0.15, top=0.88)

    # ── Plot observed counts ───────────────────────────────────────────────────
    ax.bar(x, counts, color="C0", zorder=2)

    # ── Plot expected binomial ─────────────────────────────────────────────────
    ax.plot(x, num_blocks * dist,
            color="C1", marker=".", markersize=6,
            label=f"B(8192, {p:.5f})", zorder=3)

    # ── Grid & ticks ──────────────────────────────────────────────────────────
    ax.grid(which="major", axis="y", linestyle="--", color="gray", linewidth=0.5, zorder=1)
    ax.grid(which="major", axis="x", linestyle="")

    ax.yaxis.set_major_locator(MultipleLocator(30))
    ax.yaxis.set_minor_locator(AutoMinorLocator(2))
    ax.tick_params(axis="y", which="minor", labelleft=False, length=4)

    ax.set_xlim(1, 16)
    ax.margins(x=0.025)

    ax.set_yticks([0, 30, 60, 90, 120])
    ax.set_yticklabels([str(y) for y in [0,30,60,90,120]])

    # ── Axis labels & legend ──────────────────────────────────────────────────
    ax.set_xlabel("#Mitigation Events per 8192 ACTs")

    # remove the default ylabel
    # ax.set_ylabel("#Blocks")

    # draw the y-axis label manually in the top-left
    ax.text(
        -0.105,            # a bit to the left of the y-axis ticks
        1.07,             # just above the top of the axes
        "#Blocks",
        transform=ax.transAxes,
        fontsize=8,
        ha="left",
        va="bottom"
    )

    ax.legend(ncol=1, loc="upper right", frameon=True, edgecolor="gray", borderpad=0.3)

    plt.tight_layout(pad=0.2)
    plt.savefig("plot_intel_ptrr_distribution_128iters_2aggs_8kacts_new.pdf", dpi=72)
    plt.close()

if __name__ == "__main__":
    main()
