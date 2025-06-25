#!/usr/bin/env python3
import csv
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import sys
from pathlib import Path

block_file = Path(sys.argv[1])


# NUM_ROWS = 8
# fig, ax = plt.subplots(NUM_ROWS, 1, figsize=(30,20), dpi=150)
NUM_ROWS = 1
fig, ax = plt.subplots(NUM_ROWS, figsize=(10,2), dpi=300)
ax = [ax]

with block_file.open("r") as f:
    reader = csv.DictReader(f)
    cmds = list(reader)

# Print types of commands present.
cmd_types = set([cmd["cmd"] for cmd in cmds])
print(cmd_types)

# Check this is all in the same bank.
bank_groups = set([cmd["bg"] for cmd in cmds if cmd["bg"]])
assert len(bank_groups) == 1
banks = set([cmd["bk"] for cmd in cmds if cmd["bk"]])
assert len(banks) == 1
print(f"BG={list(bank_groups)[0]}, BA={list(banks)[0]}")

# Trim all commands from beginning of block until first ACT.
first_act_idx = None
last_act_idx = None
for j, cmd in enumerate(cmds):
    if cmd["cmd"] == "act" and float(cmd["timestamp_sec"])*1e6 >= 666 and first_act_idx is None:
        first_act_idx = j
        continue
    elif float(cmd["timestamp_sec"])*1e6 >= 697:
        last_act_idx = j
        break
cmds = cmds[first_act_idx:last_act_idx]

first_timestamp = float(cmds[0]["timestamp_sec"]) * 1e6
last_timestamp = float(cmds[-1]["timestamp_sec"]) * 1e6
print(f"Delta: {last_timestamp - first_timestamp:.1f} us")

# Tuples of (timestamp,row) for different commands.
classified_cmds = defaultdict(lambda: [])
act_pre_regions = []

open_row = None
last_cmd = None
last_cmd_timestamp = None

for cmd in cmds:
    if cmd["cmd"] == "act":
        open_row = int(cmd["row"], 2)
    timestamp = float(cmd["timestamp_sec"]) * 1e6
    timestamp = timestamp - first_timestamp
    key = cmd["cmd"]
    if key.startswith("pre"):
        key = "pre"

    if key.startswith("ref"):
        row = 0
    else:
        if open_row is None:
            print("Open row is None!")
            row = 1
        else:
            row = open_row
    # classified_cmds[key].append((timestamp, f"0x{row:04x}"))
    classified_cmds[key].append((timestamp, f"{row-0xf000:d}"))
    if cmd["cmd"] in ["pre_pb", "pre_sb"]:
        if last_cmd == "act":
            print(f"ACT->PRE (row = 0x{open_row:04x}): {timestamp - last_cmd_timestamp:.3f} ns")
            act_pre_regions.append((last_cmd_timestamp, timestamp))
        open_row = None

    last_cmd = key
    last_cmd_timestamp = timestamp

# t_start = float(cmds[0]["timestamp_sec"]) * 1e6
t_start = 0
# t_stop = float(cmds[-1]["timestamp_sec"]) * 1e6
t_stop = last_timestamp-first_timestamp
breaks = np.linspace(t_start, t_stop, NUM_ROWS + 1)

all_rows = set()

# Sort by rows, such that they are sorted in the plot.
# for key in ["act", "pre", "rd", "wr"]:
for key in ["act", "pre"]:
    classified_cmds[key].sort(key = lambda x: x[1])
    all_rows.update([item[1] for item in classified_cmds[key]])
    classified_cmds_new = list()
    for lst in classified_cmds[key]:
        # if lst[1] == '0x0001':
        if lst[1] == '-61439':
            continue
        classified_cmds_new.append(lst)
    
    classified_cmds[key] = classified_cmds_new

all_rows = sorted(all_rows)
all_rows = [x for x in all_rows if x != "0x0001"]

print(all_rows)

for i, (start, stop) in enumerate(zip(breaks[:-1], breaks[1:])):
    ax[i].set_xlim([start, stop])

    # HACK: Plot transparent dummy marker in the middle of the interval to
    #       ensure all DRAM rows are visible in all subplots.
    # times = np.full((len(all_rows),), (start + stop) / 2)
    # ax[i].scatter(times, all_rows, marker="", color="k")

    ax[i].xaxis.set_major_locator(ticker.MultipleLocator(2))
    # ax[i].xaxis.set_minor_locator(ticker.MultipleLocator(0.2))
    ax[i].set_axisbelow(True)
    # ax[i].grid(which="both", axis="x")
    ax[i].grid(which="both", axis="y", color="lightgray")

    ax[i].scatter(*zip(*classified_cmds["act"]), label="ACT", marker="o", s=12, zorder=99)
    ax[i].scatter(*zip(*classified_cmds["pre"]), label="PRE", marker="x", s=3, zorder=99)
    # ax[i].scatter(*zip(*classified_cmds["rd"]), label="RD", marker="o")

    # if classified_cmds["wr"]:
    #     ax[i].scatter(*zip(*classified_cmds["wr"]), label="WR", marker="o")

    # for label in ax[i].get_xticklabels():
    #     label.set_fontfamily("monospace")

    for j, (timestamp, _) in enumerate(classified_cmds["ref_ab"]):
        ax[i].axvline(timestamp, color="green", alpha=0.5, label="REFab" if j == 0 else None)
    for j, (timestamp, _) in enumerate(classified_cmds["ref_sb"]):
        ax[i].axvline(timestamp, color="green", alpha=0.5, linestyle="--", label="REFsb" if j == 0 else None)

    for start, end in act_pre_regions:
        ax[i].axvspan(start-0.2, end+0.2, color="yellow", alpha=0.2, zorder=1)

ax[-1].legend(loc='upper center', ncol=4, bbox_to_anchor=(0.5, 1.3))

ax[-1].set_xlabel("Time [us]")
# ax[-1].set_xlabel("time [us]")
ax[-1].set_ylabel("Row Index")

plt.tight_layout()
# plt.savefig("plot.png")
plt.savefig("plot_rfm_intel_ptrr_full.pdf", dpi=300)
