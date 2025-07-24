#!/usr/bin/env python3

import os
import re
import sys
import csv
import pickle
import argparse
import tqdm

import matplotlib.pyplot as plt
import numpy as np

from collections import defaultdict


pressed_bg = "bg=01"
pressed_bk = "bk=11"
pressed_row = [ "ra=101000000111", "ra=101001010001" ]

# pressed_bg = "bg=01"
# pressed_bk = "bk=11"
# pressed_row = [ "ra=101100111011" ]

def debug_print(msg, debug):
    if debug:
        print(msg)

def remove_dups(filename: str, new_filename: str, threshold: int = 4, debug=False):
    # Only read file once, store lines in memory for tqdm
    with open(filename, newline='\n') as f:
        lines = f.readlines()
    total_lines = len(lines)
    reader = csv.DictReader(lines, delimiter=',')
    outfile = open(new_filename, 'w')
    debug_print(f"reader.fieldnames {reader.fieldnames}", debug)
    outfile.write(','.join(reader.fieldnames) + '\n')
    counter = 0
    candidate = None
    row_last = None
    for row in tqdm.tqdm(reader, total=total_lines-1, desc=f"remove_dups: {os.path.basename(filename)}"):
        row_current = {k: v for k, v in row.items() if k != 'Time' and k != 'clk'}
        if all(v == '0' for v in row_current.values()):
            continue
        if row_last == row_current:
            counter += 1
        else:
            if counter >= threshold and candidate is not None:
                outfile.write(','.join(candidate.values()) + '\n')
            candidate = row
            counter = 0
        row_last = row_current
    outfile.close()

def parse_commands(filename: str, new_filename: str, debug=False):
    debug_print("[DEBUG] Entering parse_commands", debug)
    debug_print(f"[DEBUG] Input filename: {filename}", debug)
    debug_print(f"[DEBUG] Output filename: {new_filename}", debug)
    # Count lines for tqdm
    with open(filename, newline='\n') as f:
        total_lines = sum(1 for _ in f)
    outfile = open(new_filename, 'w')
    last_act_per_bgbk = defaultdict(str)
    last_act_per_bgbk_row = defaultdict(str)
    tras_durations = list()

    last_was_read = False
    count_consec_reads = 0
    max_consec_reads = 0
    
    debug_print(f"[DEBUG] Opening file: {filename}", debug)
    with open(filename, newline='\n') as f:
        reader = csv.DictReader(f, delimiter=',')
        ts_last = float(0.0)
        counter = 0
        candidate = None
        for i, row in enumerate(tqdm.tqdm(reader, total=total_lines-1, desc=f"parse_commands: {os.path.basename(filename)}")):
            if i == 1:
                debug_print(f"[DEBUG] Skipping row {i}", debug)
                continue
            row['Time'] = float(row['Time'])

            # REF: ACT=H, A16=L, A15=H, A14=H
            if row['act'] == '0' and row['a16'] == '1' and row['a15'] == '0' and row['a14'] == '1':
                debug_print(f"[DEBUG] REF detected at row {i}, Time={row['Time']}", debug)
                outfile.write(f"{float(row['Time']):.12E} REF\n")
                last_act_per_bgbk.clear()
                last_was_read = False
            
            # PRE: ACT=H, A16=L, A15=H, A14=L, A10=L
            elif row['act'] == '0' and row['a16'] == '1' and row['a15'] == '1' and row['a14'] == '0':
                bg = f"bg={row['bg1']}{row['bg0']}"
                bk = f"bk={row['ba1']}{row['ba0']}"
                entry = last_act_per_bgbk[f"{bg}_{bk}"]
                entry_row = last_act_per_bgbk_row[f"{bg}_{bk}"]
                debug_print(f"[DEBUG] PRE detected at row {i}, Time={row['Time']}, BG={bg}, BK={bk}, entry={entry}, entry_row={entry_row}", debug)
                if entry != '':
                    t_start = float(last_act_per_bgbk[f"{bg}_{bk}"])
                    t_end = float(row['Time'])
                    t_ns = (t_end-t_start if t_end > t_start else t_start-t_end)*10**9
                    debug_print(f"[DEBUG] tRAS duration calculated: {t_ns} ns", debug)
                    if t_ns < 31.8:
                        debug_print(f"[WARNING] tRAS duration is too short: {t_ns}", debug)
                        outfile.write(f"WARNING: tRAS duration is too short: {t_ns}\n") 
                    elif t_ns > (9*7800):
                        debug_print(f"[WARNING] tRAS duration is too long: {t_ns}", debug)
                        outfile.write(f"WARNING: tRAS duration is too long: {t_ns}\n")
                    outfile.write(f"{float(row['Time']):.12E} PRE {bg} {bk} since={t_ns:.3f}ns\n")
                    if t_ns > 0 and bg == pressed_bg and bk == pressed_bk and entry_row in pressed_row:
                        debug_print(f"[DEBUG] Appending tRAS duration: {t_ns} ns", debug)
                        tras_durations.append(t_ns)
                else:
                    debug_print(f"[DEBUG] No prior ACT for PRE at BG={bg}, BK={bk}", debug)
                    outfile.write(f"{float(row['Time']):.12E} PRE {bg} {bk}\n")
                last_act_per_bgbk[f"{bg}_{bk}"] = ""
                last_act_per_bgbk_row[f"{bg}_{bk}"] = ""
                last_was_read = False

            # ACT: ACT=L
            elif row['act'] == '1':
                bg = f"bg={row['bg1']}{row['bg0']}"
                bk = f"bk={row['ba1']}{row['ba0']}"
                ra = f"ra={row['a16']}{row['a15']}{row['a14']}{row['a13']}{row['a7']}{row['a6']}{row['a5']}{row['a4']}{row['a3']}{row['a2']}{row['a1']}{row['a0']}"
                debug_print(f"[DEBUG] ACT detected at row {i}, Time={row['Time']}, BG={bg}, BK={bk}, RA={ra}", debug)
                outfile.write(f"{float(row['Time']):.12E} ACT {bg} {bk} {ra}\n")
                entry = last_act_per_bgbk[f"{bg}_{bk}"]
                if entry == "":
                    debug_print(f"[DEBUG] Storing ACT time for BG={bg}, BK={bk}", debug)
                    last_act_per_bgbk[f"{bg}_{bk}"] = row['Time']
                    last_act_per_bgbk_row[f"{bg}_{bk}"] = ra
                else:
                    debug_print(f"[ERROR] ACT without prior PRE for BG={bg}, BK={bk}", debug)
                    outfile.write(f"ERROR: ACT without prior PRE for {bg} {bk}\n")
                last_was_read = False

            # RD: ACT_n=H, A16=H, A15=L, A14=H, BA, BG (A10=L)
            elif row['act'] == '0' and row['a16'] == '0' and row['a15'] == '0' and row['a14'] == '1':
                bg = f"bg={row['bg1']}{row['bg0']}"
                bk = f"bk={row['ba1']}{row['ba0']}"
                col = f"col={row['a7']}{row['a6']}{row['a5']}{row['a4']}{row['a3']}{row['a2']}{row['a1']}{row['a0']}"
                debug_print(f"[DEBUG] RD detected at row {i}, Time={row['Time']}, BG={bg}, BK={bk}, COL={col}", debug)
                outfile.write(f"{float(row['Time']):.12E} RD  {bg} {bk} {col}\n")
                if last_was_read:
                    count_consec_reads += 1
                    debug_print(f"[DEBUG] Consecutive read detected. Count: {count_consec_reads}", debug)
                else:
                    debug_print(f"[DEBUG] New read sequence. Previous consecutive reads: {count_consec_reads}", debug)
                    max_consec_reads = max(max_consec_reads, count_consec_reads)
                    count_consec_reads = 0
                last_was_read = True
            
            ts_last = float(row['Time'])
    
    debug_print(f"[DEBUG] Max. Consecutive Reads: {max_consec_reads}", debug)
    outfile.close()
    debug_print(f"[DEBUG] Exiting parse_commands. tRAS durations collected: {len(tras_durations)}", debug)
    return tras_durations

def write_resultfile(filename: str, tras_durations: list):
    filename_new = "results.csv"
    # If the file is empty, then write the header row
    if not os.path.isfile(filename_new) or os.stat(filename_new).st_size == 0:
        with open(filename_new, 'w') as f:
            f.write("file,num_reads,min,max,mean,median,std,variance\n")

    with open(filename_new, 'a') as f:
        regex = re.compile(r"no_aggr_acts=2-no_reads=([0-9]+)-.*")
        match = regex.search(os.path.basename(filename))
        num_reads = int(match.group(1)) if match else 0
        minv = min(tras_durations)
        maxv = max(tras_durations)
        mean = np.mean(tras_durations)
        median = np.median(tras_durations)
        std = np.std(tras_durations)
        variance = np.var(tras_durations)
        f.write(f"{filename},{num_reads},{minv},{maxv},{mean},{median},{std},{variance}\n")

def plot_histogram(tras_durations: list, filename: str):
    # generate a histogram with pyplot of the values in tras_durations
    print("#tras_durations: ", len(set(tras_durations)))

    total_duration = min(32*20, int(max(tras_durations)))  # 9x tREFI
    print(f"Total Duration: {total_duration}ns")

    counts, bin_edges = np.histogram(tras_durations, bins=320//4, density=True)

    hist_normalized = counts / counts.sum()

    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2  # Calculate bin centers for plotting
    plt.bar(bin_centers, hist_normalized, width=(bin_edges[1] - bin_edges[0]), align='center')
    plt.xlabel("tRAS Duration [ns]")
    plt.ylabel("Fraction of Observations [normalized]")
    print("filename: ", filename)
    regex = re.compile(r"no_aggr_acts=2-no_reads=([0-9]+)-.*")
    num_reads = int(regex.search(filename).group(1))
    plt.title(f"Histogram over tRAS values for {num_reads} column reads")

    # bins = np.arange(np.floor(min(tras_durations)),np.ceil(max(tras_durations)))
    # counts, bins = np.histogram(tras_durations, bins=int((max(tras_durations)-min(tras_durations)))//32, density=True)

    # myfigure = plt.figure(figsize=(14, 6))
    # rwidth=0.8
    # plt.hist(bins[:-1], bins, weights=counts, histtype='bar', rwidth=rwidth)
    # plt.stairs(counts, bins)
    # # plt.hist(bins[:-1], bins, weights=counts, density=True, histtype='bar', rwidth=rwidth)
    # plt.xticks(np.arange(0, total_duration, 32))
    # plt.xlim(0, total_duration)

    mean = np.mean(tras_durations)
    plt.axvline(mean, 0, 1, color='r', linestyle='dashed', label=f"mean ({mean:.3f}ns)", linewidth=0.6)
    median = np.median(tras_durations)
    plt.axvline(median, 0, 1, color='g', linestyle='dashed', label='median ({:.3f}ns)'.format(median), linewidth=0.6)
    plt.axvline(32, 0, 1, color='b', linestyle='dashed', label='32ns (DDR4 default)', linewidth=0.6)
    # move legend to the right side of the plot
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))

    plt.tight_layout()
    plt.savefig(filename, dpi=600)

# def remove_duplicates(filename: str, new_filename: str, threshold: int = 4):
#     last_written = None
#     outfile = open(new_filename, 'w')
#     with open(filename, newline='\n') as f:
#         reader = csv.DictReader(f, delimiter=',', )
#         # outfile.write(','.join(reader.fieldnames) + '\n')
#         candidate = None
#         row_last = None
#         counter = 0
#         for row in reader:
#             row_current = {k: v for k, v in row.items() if k != 'Time' and k != 'clk'}
#             if row_last == row_current and row_current != last_written:
#                 counter += 1
#                 if counter == 1:
#                     candidate = row
#             else:
#                 if counter >= threshold and candidate is not None:
#                     outfile.write(','.join(candidate.values()) + '\n')
#                     last_written = {k: v for k, v in candidate.items() if k != 'Time' and k != 'clk'}
#                     candidate = None
#                 counter = 0
#             row_last = row_current 
#     outfile.close() 

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process DRAM experiment CSV files.")
    parser.add_argument('--data-path', type=str, required=True, help='Path to directory containing experiment CSV files, e.g., e4-rowpress/decoded/ of the mcsee-data archive')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--plot', action='store_true', help='Enable plotting of tRAS histograms')
    args = parser.parse_args()

    filenames = [
        "no_aggr_acts=2-no_reads=1-victimrow=64--00000.csv",
        "no_aggr_acts=2-no_reads=2-victimrow=64--00000.csv",
        "no_aggr_acts=2-no_reads=4-victimrow=64--00000.csv",
        "no_aggr_acts=2-no_reads=8-victimrow=64--00000.csv",
        "no_aggr_acts=2-no_reads=16-victimrow=64--00000.csv",
        "no_aggr_acts=2-no_reads=32-victimrow=64--00000.csv",
        "no_aggr_acts=2-no_reads=48-victimrow=64--00000.csv",
        "no_aggr_acts=2-no_reads=64-victimrow=64--00000.csv",
        "no_aggr_acts=2-no_reads=80-victimrow=64--00000.csv",
        "no_aggr_acts=2-no_reads=128-victimrow=64--00000.csv"
    ]

    missing_files = []
    for fname in filenames:
        full_path = os.path.join(args.data_path, fname)
        if not os.path.isfile(full_path):
            missing_files.append(fname)

    if missing_files:
        print(f"[ERROR] Missing files in {args.data_path}:")
        for mf in missing_files:
            print(f"  {mf}")
        sys.exit(1)

    for fname in filenames:
        filename = os.path.join(args.data_path, fname)
        print(f"[>] Processing {filename}")
        file_dupfree = filename.replace(".csv", "_dupfree.csv")
        remove_dups(filename, file_dupfree, debug=args.debug)

        print(f"[>] Parsing commands from {file_dupfree}")
        file_cmd = filename.replace(".csv", "_cmd.csv")
        file_tras = filename.replace(".csv", "_tras.pkl")
        tras_durations = parse_commands(file_dupfree, file_cmd, debug=args.debug)
        with open(file_tras, 'wb') as f:
            pickle.dump(tras_durations, f)

        write_resultfile(filename, tras_durations)

        if args.plot:
            file_plot = filename.replace(".csv", "_plot.png")
            print("[>] Plotting histogram of tRAS durations")
            plot_histogram(tras_durations, file_plot)
#
