#!/usr/bin/env python3
import argparse
import glob
import statistics
from collections import defaultdict
from statistics import mean, median
import sys
import os

"""
This script calculates the distance between consecutive ACT commands to the same row in a DDR4 memory trace.
It assumes decoded trace files (`--data-path <directory>`) as provided in the mcsee-data archive under e2-sledgehammer/decoded/.
"""


def calculate_act2act_distance(act2actidxs):
    # print("#Rows: ", len(act2actidxs.keys()))
    distances = []
    for row, vals in act2actidxs.items():
        if len(vals) < 15:
            continue
        for cur, next in zip(vals, vals[1:]):
            if next-cur < 0:
                print(cur, next)
                exit(0)
            distances.append(next-cur)
        # calculate the standard deviation
        std = statistics.stdev(distances)
        # print(row, f"min={min(distances)}", f"max={max(distances)}", f"median={median(distances)}", f"avg={mean(distances):.3f}", f"std={std}", distances, sep=', ')

    return distances


def extract_actidxs_per_row(file: str, target_rows: list, nbanks: int):
    row2actidx = defaultdict(list)
    act_counter = 0
    print(f"Processing file: {file}")
    with open(file, "r") as f:
        for line in f.readlines():
            parts = line.split(' ')
            ts = parts[0]
            cmd = parts[1]
            if ts != "ERROR:" and cmd == "ACT":
                act_counter += 1
                try:
                    kv_pairs = {kv.split('=')[0]: int(kv.split('=')[1],2) for kv in parts[2:]}
                except:
                    print("ERROR in kv_pairs: ", parts)
                    exit(0)
                key = '_'.join([str(x) for x in kv_pairs.values()])
                if key in target_rows:
                    row2actidx[key].append(act_counter)

    # print(row2actidx)

    f_dist = open("act2act_distances_per_bank.txt", "a")

    resultperrow = dict()
    for row, actidxs in row2actidx.items():
        # calculate difference between two consecutive actidxs
        result = []
        for cur, next in zip(actidxs, actidxs[1:]):
            dist = next-cur
            # if dist < 17 or dist > 23:
            result.append(dist)
        print(row, result)
        resultperrow[row] = result
        # print(f"Row {row} has {len(actidxs)} accesses. Distances: {result}")

    f_dist.write(str(nbanks) + ", ")
    f_dist.write(",".join(str(x) for result in resultperrow.values() for x in result))
    f_dist.write("\n")

    sum_other_values = 0
    for row, distances in resultperrow.items():
        # get the most frequent value in the distances list
        most_frequent = max(set(distances), key=distances.count)
        # print("row: ", row, "most frequent distance: ", most_frequent)
        # print how many times a value other than the most frequent value occurs
        # other_values = [x for x in distances if x != most_frequent]
        other_values = [x for x in distances if x < 0.9*most_frequent or x > 1.1*most_frequent]
        print("row=", row, "most_frequent=", most_frequent, "other values=", len(other_values))
        sum_other_values += len(other_values)
    print("avg_other_values=", sum_other_values/len(resultperrow))

    f_dist.close()

    exit(0)
    return row2actidx


def detect_most_activated_rows(file: str):
    bg_bk_row__actcnt = defaultdict(int)
    with open(file, "r") as f:
        for line in f.readlines():
            parts = line.split(' ')
            ts = parts[0]
            cmd = parts[1]
            if ts != "ERROR:" and cmd == "ACT":
                try:
                    kv_pairs = {kv.split('=')[0]: int(kv.split('=')[1],2) for kv in parts[2:]}
                    key = '_'.join([str(x) for x in kv_pairs.values()])
                    bg_bk_row__actcnt[key] += 1
                except:
                    print("ERROR in kv_pairs: ", parts)
                    exit(0)
    # sort bg_bk_row__actcnt by value
    average = sum(bg_bk_row__actcnt.values()) / len(bg_bk_row__actcnt)
    sorted_bg_bk_row__actcnt = dict(sorted(bg_bk_row__actcnt.items(), key=lambda item: item[1], reverse=True))
    filtered_bg_bk_row__actcnt = {
        k: v for k, v in sorted_bg_bk_row__actcnt.items() if v > average
    }

    print("Row ACT Counts:")
    for i, (k, count) in enumerate(sorted_bg_bk_row__actcnt.items()):
        bg, bk, row = k.split('_')
        print(f"{i+1:4d}\t{count:>5} x ({bg},{bk},{row})   {'→ ✔︎' if k in filtered_bg_bk_row__actcnt else ''}")

    # print(bg_bk_row__actcnt)
    print(f"[i] Reduced {len(sorted_bg_bk_row__actcnt)} to {len(filtered_bg_bk_row__actcnt)} rows by average {average}.")

    return list(filtered_bg_bk_row__actcnt.keys())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Process number of banks and path to decoded trace files.")
    parser.add_argument('--nbanks', type=int, required=False, help='Number of banks (integer)')
    parser.add_argument('--data-path', type=str, required=True,
                        help='Path to the decoded trace files as found in the mcsee-data archive under e2-sledgehammer/decoded/')

    args = parser.parse_args()

    DATA_PATH = args.data_path

    # Check if DATA_PATH contains any CSV files
    csv_files = glob.glob(os.path.join(DATA_PATH, '**', '*.csv'), recursive=True)
    if not csv_files:
        print(f"ERROR: No CSV files found in directory '{DATA_PATH}'. Please provide a valid path containing decoded trace CSV files.")
        sys.exit(1)

    banks = []
    if args.nbanks:
        banks = [args.nbanks]
    else:
        banks = [x for x in range (1,17)]

    print(f"Number of banks: {args.nbanks}")

    outfile = open("result.txt", "w")


    for bk in banks:
        all_results = []
        all_target_rows = set()
        for file in glob.glob(f"{DATA_PATH}/**/*nbanks={bk}-*_cmd.csv", recursive=True):
            target_rows = detect_most_activated_rows(file)
            all_target_rows = all_target_rows.union(target_rows)
            row2actidx = extract_actidxs_per_row(file, target_rows, bk)
            distances = calculate_act2act_distance(row2actidx)
            all_results += distances

        _min = min(all_results)
        _max = max(all_results)
        _median = median(all_results)
        _avg = mean(all_results)
        # print(f"nbanks={bk}, min={_min}, max={_max}, median={_median}, avg={_avg:.3f}, std={statistics.stdev(all_results)}")
        outfile.write(f"nbanks={bk}, min={_min}, max={_max}, median={_median}, avg={_avg:.3f}, std={statistics.stdev(all_results):.3f}, nrows={len(all_target_rows)}, N={len(all_results)} \n")
        outfile.flush()

    outfile.close()
