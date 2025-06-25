#!/usr/bin/env python3
from collections import Counter
import csv
from pathlib import Path
import statistics
import sys
from termcolor import colored


def read_file(file: Path) -> list[dict]:
    with file.open("r") as f:
        reader = csv.DictReader(f, delimiter=",")
        return list(reader)


data_dir = Path(sys.argv[1])

print(f"[+] Data directory is '{data_dir}'.")

files = [f for f in (data_dir / "data/decoded/it=00000").iterdir() if f.suffix == ".csv"]
files.sort()

for file in files:
    print(f"[+] >>> {file.name}")

    # Load commands
    cmds = read_file(file)
    print(f"[+] Loaded {len(cmds)} DDRx commands.")

    # Determine most activated (bg,bk).
    acts = [cmd for cmd in cmds if cmd["cmd"] == "act"]
    print(f"[+] Loaded {len(acts)} ACTs.")

    counter = Counter((act["bg"], act["bk"]) for act in acts)
    counts = counter.most_common()
    print("[+] Most commonly activated (BG,BA) tuples:")
    for (bg, ba), count in counts[:3]:
        print(f"    ({bg},{ba}): {count}x")
    ratio = counts[0][1] / counts[1][1]
    print("[+] ({},{}) was activated {:.1f} times more often than ({},{}).".format(*counts[0][0], ratio, *counts[1][0]))

    if ratio < 10:
        print("[-] No (BG,BA) tuple was activated much more often than the other ones.")
        print(f"[-] Skipping this file ({file.name})...")
        continue

    # Filter CMDs to only consider that (BG,BA) tuple.
    most_common_bg = counts[0][0][0]
    most_common_ba = counts[0][0][1]
    cmds = list(filter(lambda cmd: (cmd["bg"] == most_common_bg or cmd["bg"] == "") and (cmd["bk"] == most_common_ba or cmd["bk"] == ""), cmds))
    print(f"[+] Ignoring commands with (BG,BA) != ({most_common_bg},{most_common_ba}), {len(cmds)} commands remain.")

    # for cmd in cmds:
    #     if cmd["cmd"] != "act":
    #         continue
    #     timestamp_ns = float(cmd["timestamp_sec"]) * 1e9
    #     print(f"{timestamp_ns:.0f} {cmd['row']}")

    # Create blocks of ACTs.
    blocks = []

    block_start = None
    block_current = None
    block_cmds = []
    for cmd in cmds:
        timestamp_ns = float(cmd["timestamp_sec"]) * 1e9
        if block_start is None:
            block_start = timestamp_ns
            block_current = timestamp_ns
            block_cmds = [cmd]
            continue
        assert block_start is not None and block_current is not None

        if cmd["cmd"] == "act":
            print(f"ACT {timestamp_ns:.1f} {cmd['row']} ({int(cmd['row'], 2) & 0x3ff})")
        elif cmd["cmd"] in ["rd", "rda", "wr", "wra"]:
            print(f"{cmd['cmd'].upper():<3s} {timestamp_ns:.1f} {cmd['col']} ({int(cmd['col'], 2)})")
        elif cmd["cmd"] == "pre_pb":
            print("PRE")

        # Check if this is close enough to be in the same block.
        if timestamp_ns - block_current >= 1000:  # 500 ns
            # Too far apart.
            blocks.append((block_start, block_current, block_cmds))
            print("BLOCK")
            block_start = timestamp_ns
            block_current = timestamp_ns
            block_cmds = [cmd]
        else:
            block_current = timestamp_ns
            block_cmds.append(cmd)
    if block_start is not None:
        blocks.append((block_start, block_current, block_cmds))


    # Remove all blocks with less than 20 ACTs, i.e., noise.
    def count_acts(block):
        return sum(cmd["cmd"] == "act" for cmd in block[2])

    blocks = [block for block in blocks if count_acts(block) >= 20]
    
    print(f"[+] Got {len(blocks)} blocks.")

    # Create statistics over # ACTs per block.
    act_counts = [sum(cmd["cmd"] == "act" for cmd in block[2]) for block in blocks]
    act_counts.sort()
    first_quartile = act_counts[len(act_counts) // 4]
    median = act_counts[len(act_counts) // 2]
    third_quartile = act_counts[3 * len(act_counts) // 4]
    print("Block statistics (# ACTs):")
    print(f"{act_counts[0]} / {first_quartile} / {median} / {third_quartile} / {act_counts[-1]}")
    print(act_counts)

    # Now, we only consider blocks with ACT counts within 5 % of the median.
    for start, end, cmds in blocks:
        acts = [cmd for cmd in cmds if cmd["cmd"] == "act"]
        if not 0.95 * median <= len(acts) <= 1.05 * median:
            continue

        # Write block to file.
        block_file = Path("block_cmds.csv")
        with block_file.open("w") as f:
            writer = csv.DictWriter(f, fieldnames=["timestamp_sec", "cmd", "bg", "bk", "row", "col"])
            writer.writeheader()
            for cmd in cmds:
                writer.writerow(cmd)

        print(f">>> {start:.1f} -> {end:.1f}: {len(acts)} ACTs")
        print(f"    {(end - start) / max(len(acts) - 1, 1):.1f} ns between ACTs")

        # Check same-row and different-row ACT spacings.
        same_row = []
        different_row = []
        for i in range(1, len(acts)):
            distance = (float(acts[i]["timestamp_sec"]) - float(acts[i-1]["timestamp_sec"])) * 1e9
            if acts[i]["row"] == acts[i-1]["row"]:
                same_row.append(distance)
            else:
                different_row.append(distance)
        if len(same_row) > 0:
            print(f"Same row: {min(same_row):.1f} / {statistics.mean(same_row):.1f} / {max(same_row):.1f} ns")
        print(f"Diff row: {min(different_row):.1f} / {statistics.mean(different_row):.1f} / {max(different_row):.1f} ns")

        rows = [int(cmd["row"], 2) & 0x3ff for cmd in acts]
        color_for_row = dict()
        for i, (row, _) in enumerate(Counter(rows).most_common(2)):
            color_for_row[row] = ["red", "green", "yellow", "magenta"][i]

        for i, row in enumerate(rows):
            if i > 0 and i % 16 == 0:
                print()
            string = f"{row:03d}"
            if row in color_for_row:
                string = colored(string, color_for_row[row])
            print(string, end=" ")
        print()
        print(Counter(rows).most_common())
