#!/usr/bin/env python3
from collections import Counter
import csv
from pathlib import Path
import sys


def read_file(file: Path):
    with file.open("r") as f:
        reader = csv.DictReader(f, delimiter=",")
        return list(reader)


data_dir = Path(sys.argv[1])
print(f"[+] Data directory is '{data_dir}'.")

blocks_written = 0

for it_dir in (data_dir / "data/decoded").iterdir():
    files = [f for f in it_dir.iterdir() if f.suffix == ".csv"]
    files.sort()
    print(f"[+] Found {len(files)} decoded traces in '{it_dir.name}'.")
    
    block_dir = data_dir / "data/blocks" / it_dir.name
    print(f"[+] Writing block traces for '{it_dir.name}' to '{block_dir}'.")

    for file in files:
        print(f"[+] >>> {file}")

        # Load commands
        cmds = read_file(file)
        acts = [cmd for cmd in cmds if cmd["cmd"] == "act"]
        print(f"[+] Loaded {len(cmds)} DDRx commands, including {len(acts)} ACTs.")

        # Determine most activated (BG,BA).
        counter = Counter((act["bg"], act["bk"]) for act in acts)
        counts = counter.most_common()
        print("[+] Most commonly activated (BG,BA) tuples:")
        for (bg, ba), count in counts[:3]:
            print(f"    ({bg},{ba}): {count}x")
        ratio = 0
        if len(counts) >= 1 and len(counts[0]) >= 1 and len(counts[1]) >= 1:
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

        # Create blocks of commands.
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

            # Check if this is close enough to be in the same block.
            if timestamp_ns - block_current >= 1000:  # 1000 ns
                # Too far apart.
                blocks.append((block_start, block_current, block_cmds))
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
        
        print(f"[+] Trace contains {len(blocks)} blocks.")

        # Create statistics over # ACTs per block.
        act_counts = [sum(cmd["cmd"] == "act" for cmd in block[2]) for block in blocks]
        act_counts.sort()
        first_quartile = act_counts[len(act_counts) // 4]
        median = act_counts[len(act_counts) // 2]
        third_quartile = act_counts[3 * len(act_counts) // 4]
        print("Block statistics (# ACTs):", end="")
        print(f"{act_counts[0]} / {first_quartile} / {median} / {third_quartile} / {act_counts[-1]}")

        # Now, we only consider blocks with ACT counts withing 10% of the maximum ACT count.
        for i, (start, end, cmds) in enumerate(blocks):
            acts = [cmd for cmd in cmds if cmd["cmd"] == "act"]
            if len(acts) <= act_counts[-1] * 0.9:
                continue

            # Write block to file.
            block_file = Path(block_dir / file.stem / f"block_{i:03d}.csv")
            block_file.parent.mkdir(parents=True, exist_ok=True)
            print(f"[+] Writing block with {len(cmds)} commands to {block_file.name}.")
            with block_file.open("w") as f:
                writer = csv.DictWriter(f, fieldnames=["timestamp_sec", "cmd", "bg", "bk", "row", "col"])
                writer.writeheader()
                for cmd in cmds:
                    writer.writerow(cmd)
                blocks_written += 1

print(f"[+] Extracted {blocks_written} blocks from '{data_dir.name}'.")
