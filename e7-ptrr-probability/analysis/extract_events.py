#!/usr/bin/env python3
import csv
import json
import sys
from pathlib import Path

data_dir = Path(sys.argv[1])

block_files = []

for it_dir in (data_dir / "data/blocks").iterdir():
    if not it_dir.is_dir():
        continue
    for trace_dir in it_dir.iterdir():
        if not trace_dir.is_dir():
            continue
        for block_file in trace_dir.iterdir():
            if not block_file.is_file():
                continue
            block_files.append(block_file)
block_files.sort()
print(f"[+] Found {len(block_files)} block traces in '{data_dir}'.")

out_file = data_dir / "data/mitigation_events.json"
json_data = []

total_acts = 0
num_events = 0

for i, block_file in enumerate(block_files):
    print(block_file)
    with block_file.open("r") as f:
        reader = csv.DictReader(f)
        cmds = list(reader)

    t_start = float(cmds[0]["timestamp_sec"]) * 1e9

    timestamps_and_rows = []

    for cmd in cmds:
        if cmd["cmd"] == "act":
            row = int(cmd["row"], 2)
            timestamp = float(cmd["timestamp_sec"]) * 1e9 - t_start
            timestamp = round(timestamp)
            timestamps_and_rows.append((timestamp, row))

    event_idxs = []

    for j in range(len(timestamps_and_rows) - 2):
        rows = [row for _, row in timestamps_and_rows[j:j+3]]
        rows.sort()
        if rows[1] == rows[0] + 1 and rows[2] == rows[0] + 2:
            if not event_idxs or j - event_idxs[-1] >= 2:
                event_idxs.append(j)

    duration = timestamps_and_rows[-1][0]

    data_for_block = []
    for j in event_idxs:
        rows = [row for _, row in timestamps_and_rows[j:j+3]]
        data_for_block.append({
            "timestamp_ns": timestamps_and_rows[j][0],
            "act_number": j,
            "rows": rows
        })
    json_data.append({
        "file": str(block_file),
        "duration_ns": duration,
        "num_acts": len(timestamps_and_rows),
        "events": data_for_block
    })

    total_acts += len(timestamps_and_rows)
    num_events += len(data_for_block)

    print(f"[+] Extracted {len(data_for_block)} mitigation events from block '{block_file}'.")

with out_file.open("w") as f:
    json.dump(json_data, f, indent=4)
print(f"[+] Write mitigation event data to '{out_file}'.")
print(f"[+] Summary: Found {num_events} mitigation events, analyzing {total_acts} ACTs.")
