#!/usr/bin/env python3
import argparse
from collections import Counter
import csv
from dataclasses import dataclass
import multiprocessing
import os
from pathlib import Path
import sys
from typing import Optional


BG_BITS = 3
BK_BITS = 2
ROW_BITS = 16
SUBCHANNEL_LSB = 6


legacy_data_fmt = False


def bit(idx: int):
    return 1 << idx


def bits_set(value: int):
    return [idx for idx in range(63, -1, -1) if (value & bit(idx)) > 0]


@dataclass
class ExpIteration:
    name: str
    virt: int
    phys: int
    dram: int
    principal_dram: int
    most_activated: int  # address bits encoded with concat_bg_bk_row()

    def bits_flipped(self) -> list[int]:
        return bits_set(self.dram ^ self.principal_dram)


def read_exp_cfg(exp_dir: Path, iter_name: str):
    csv_path = exp_dir / iter_name / "exp_cfg.csv"

    with csv_path.open("r") as f:
        reader = csv.DictReader(f)
        addrs = list(reader)

    if len(addrs) != 1:
        print(f"[{iter_name}] 'exp_cfg.csv' does not contain exactly one accessed address (it contains {len(addrs)}")
        sys.exit(1)

    virt = int(addrs[0]["virt_addr"], 16)
    phys = int(addrs[0]["phys_addr"], 16)
    dram = int(addrs[0]["dram_addr"], 16)
    if legacy_data_fmt:
        principal_dram = 0
    else:
        principal_dram = int(addrs[0]["dram_principal"], 16)
    return virt, phys, dram, principal_dram


def addr_bits_to_str(addr_bits: tuple) -> str:
    return f"bg={addr_bits[0]:03b} bk={addr_bits[1]:02b} row={addr_bits[2]:016b}"


# Returns a list of all ACT commands. An ACT command is formatted as the concatenated bits of <bg, bk, row>.
def get_acts_from_trace(trace_file: Path) -> list[int]:
    with trace_file.open("r") as f:
        reader = csv.DictReader(f)

        acts = []
        for line in reader:
            if line["cmd"] != "act":
                continue
            bg = int(line["bg"], 2)
            bk = int(line["bk"], 2)
            row = int(line["row"], 2)
            bits = concat_bg_bk_row(bg, bk, row)
            acts.append(bits)
            assert split_bg_bk_row(bits) == (bg, bk, row), "Check that concat-split is a NOP."
    return acts


def concat_bg_bk_row(bg: int, bk: int, row: int) -> int:
    return (((bg << BK_BITS) | bk) << ROW_BITS) | row


def split_bg_bk_row(bits: int) -> tuple[int, int, int]:
    bg = (bits >> (BK_BITS + ROW_BITS)) & ((1 << BG_BITS) - 1)
    bk = (bits >> (ROW_BITS)) & ((1 << BK_BITS) - 1)
    row = bits & ((1 << ROW_BITS) - 1)
    return bg, bk, row


def get_addr_data_for_iter(exp_dir: Path, iter_name: str, min_margin: int) -> Optional[ExpIteration]:
    # STEP 1: Parse exp_csv.csv.
    virt, phys, dram, principal_dram = read_exp_cfg(exp_dir, iter_name)

    print(f"[{iter_name}] Loaded 'exp_cfg.csv'. Bit flips at bits", *bits_set(dram ^ principal_dram))

    # STEP 2: Parse trace files.
    acts = []
    iter_dir = exp_dir / "data" / "decoded" / iter_name
    if not iter_dir.is_dir():
      return None
    for trace_file in iter_dir.iterdir():
        trace_acts = get_acts_from_trace(trace_file)
        acts += trace_acts
    print(f"[{iter_name}] Loaded {len(acts)} activations.")

    # STEP 3: Find most accessed addresses.
    # List of (act, count) tuples sorted in descending order of counts.
    counts = Counter(acts).most_common()

    # STEP 4: Check data quality.
    if not counts or counts[0][1] < 100:
        print(f"[{iter_name}] Error: Most accessed <bg,bk> has ({counts[0][1] if counts else 0}) less than 100 accesses. Discarding...")
        return None

    margin = counts[0][1] / counts[1][1] if len(counts) > 1 else float("+inf")
    print(f"[{iter_name}] Ratio between most and second most accessed <bg,bk>: {margin:.2f}")
    if margin < min_margin:
        print(f"[{iter_name}] Ratio is less than {min_margin}. Discarding...")
        return None

    most_activated = counts[0][0]
    return ExpIteration(iter_name, virt, phys, dram, principal_dram, most_activated)


def process_group(iterations: list[ExpIteration]) -> Optional[tuple[list, list]]:
    # Find the principal iteration (where .dram == .principal_dram).
    principal_idx = None
    if principal_idx is None:
        for i in range(len(iterations)):
            if iterations[i].dram == iterations[i].principal_dram:
                principal_idx = i
                break

    if principal_idx is None:
        print("[-] Principal iteration has been discarded, throwing away group...")
        return None

    iter_principal = iterations[principal_idx]
    print(f"[+] Principal address is 0x{iter_principal.dram:010x}")
    iters_flipped = [iterations[i] for i in range(len(iterations)) if i != principal_idx]

    contributors = [set() for _ in range(64)]
    contributor_bits_analyzed = []

    for iter in iters_flipped:
        # STEP 6: Check which bit(s) changed in the DRAM address (the contributor bit(s)).
        bits_flipped_dram_addr = iter.bits_flipped()

        if len(bits_flipped_dram_addr) != 1:
            if len(bits_flipped_dram_addr) == 2 and \
                    SUBCHANNEL_LSB in bits_flipped_dram_addr:
                bits_flipped_dram_addr.remove(SUBCHANNEL_LSB)
            else:
                print(f"[-] Error ({iter.name}): Not exactly one bit flipped with respect to "
                        "principal address. This shouldn't happen.")
                continue
        bit_contributor = bits_flipped_dram_addr[0]
        contributor_bits_analyzed.append(bit_contributor)

        # STEP 7: Check which bits the contributor contributed to, and store them in the list.
        bits_flipped_addr_bits = bits_set(iter_principal.most_activated ^ iter.most_activated)
        for bit_flipped in bits_flipped_addr_bits:
            contributors[bit_flipped].add(bit_contributor)

    contributor_bits_analyzed.sort(reverse=True)
    return contributors, contributor_bits_analyzed


def find_constraint_function(results: list) -> None:
    # Compute the union of all bits analyzed that keep us in the visible space.
    # Its complement is the bits that change the constraint function.
    all_bits_analyzed = set()
    for _, bits_analyzed in results:
        all_bits_analyzed.update(bits_analyzed)
    constraint_complement = 0
    for b in all_bits_analyzed:
        constraint_complement |= bit(b)

    print(f"Constraint function complement is 0x{constraint_complement:010x}")
    print("    >", *bits_set(constraint_complement))

    constraint = constraint_complement ^ 0xffffffff_ffffffff
    print(f"Constraint function is 0x{constraint:010x}")
    print("    >", *bits_set(constraint))

    NUM_BITS = 35
    constraint_limited = constraint & ((1 << NUM_BITS) - 1)
    print(f"Limited to {NUM_BITS} bits: 0x{constraint_limited:010x}")
    print("    >", *bits_set(constraint_limited))
    contributors_analyzed = set()


def get_addr_function_map() -> list[str]:
    addr_function_map = []
    for bit in range(ROW_BITS):
        addr_function_map.append(f"row{bit:02d}")
    for bit in range(BK_BITS):
        addr_function_map.append(f"bk{bit:01d}")
    for bit in range(BG_BITS):
        addr_function_map.append(f"bg{bit:01d}")
    return addr_function_map


def analyze_results(results: list[tuple[list, list]]) -> None:
    if not results:
        print("[-] Error: No result group was usable. Exiting...")
        sys.exit(1)

    contributors = [ {} for _ in range(ROW_BITS + BK_BITS + BG_BITS) ]
    # Counts how many time each contributor bit is found.
    contributor_bit_counts = {}

    for group_contributors, bits_analyzed in results:
        print("[+] Analyzing group...")
        for addr_func_bit, contributor_bits in enumerate(group_contributors):
            for bit in contributor_bits:
                contributors[addr_func_bit][bit] = contributors[addr_func_bit].get(bit, 0) + 1
        for bit in bits_analyzed:
            contributor_bit_counts[bit] = contributor_bit_counts.get(bit, 0) + 1

    # Convert counts to percentages with help of `contributor_bit_counts`.
    contributor_percentages = [ { bit: 100 * count / max(1, contributor_bit_counts[bit]) for bit, count in x.items() } for x in contributors ]

    addr_function_map = get_addr_function_map()
    for b, contribs_for_func in enumerate(contributor_percentages):
        print(f"{addr_function_map[b]:>5s}:", end=" ")
        contribs_sorted = sorted(contribs_for_func.items(), key=lambda x: x[0], reverse=True)
        for contrib, percentage in contribs_sorted:
            print(f"{contrib:2d} ({percentage:3.0f}%/{contributor_bit_counts[contrib]:2d})", end=" ")
        print()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--legacy-data-fmt",
            help="use legacy data format (one iteration group, first iteration is principal)",
            action="store_true")
    parser.add_argument("--margin", type=int, default=10)
    parser.add_argument("--find-constraint",
            help="find the constraint function (e.g., subchannel) by checking which bitflips retain visibility of ACTs",
            action="store_true")
    parser.add_argument("exp_dirs", nargs='+')
    args = parser.parse_args()
    legacy_data_fmt = args.legacy_data_fmt

    iter_data = []
    for exp_dir in args.exp_dirs:
        exp_dir = Path(exp_dir)
        iter_names = [iter_dir.name for iter_dir in exp_dir.iterdir()
                      if iter_dir.name.startswith("it")]
        iter_names.sort()
        print(f"Processing {len(iter_names)} iterations in '{exp_dir}'...")

        with multiprocessing.Pool(min(os.cpu_count(), 64)) as pool:
            # FIRST PART: Read ACTs from trace files, decide on most accessed address per iteration (or drop it if the
            #             margin is not sufficiently large).
            iter_data += pool.starmap(get_addr_data_for_iter, ((exp_dir, iter_name, args.margin) for iter_name in iter_names))

    if not iter_data:
        print(f"[-] Error: No iteration data in the following experiment directories:")
        for exp_dir in args.exp_dirs:
            print(f"    - '{exp_dir}'")
        sys.exit(1)

    if legacy_data_fmt:
        # Set principal DRAM address for all iterations, as this is not part of 'exp_cfg.csv' for the legacy format.
        if not iter_data[0]:
            print(f"[-] Error (legacy-data-fmt): Principal iteration has been discarded. Exiting...")
            sys.exit(1)
        principal_dram = iter_data[0].dram
        for iteration in iter_data:
            if iteration is not None:
                iteration.principal_dram = principal_dram

    iter_data = [data for data in iter_data if data]
    print(f"Loaded data for {len(iter_data)} usable iterations from {len(args.exp_dirs)} experiments.")

    # Group experiments by their principal address.
    iterations_by_principal = {}
    for iteration in iter_data:
        if iteration is None:
            continue
        if not iteration.principal_dram in iterations_by_principal:
            iterations_by_principal[iteration.principal_dram] = []
        iterations_by_principal[iteration.principal_dram].append(iteration)

    # Process the data.
    with multiprocessing.Pool(min(os.cpu_count(), 64)) as pool:
        results = pool.map(process_group, iterations_by_principal.values())

    # Results is a list of (contributors, bits analyzed).
    total_results = len(results)
    # Filter out 'None' results.
    results = [result for result in results if result is not None]
    good_results = len(results)
    print(f"[+] {good_results} / {total_results} groups were usable.")

    if args.find_constraint:
        find_constraint_function(results)
        sys.exit(0)

    analyze_results(results)
