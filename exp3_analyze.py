#!/usr/bin/env python3
"""
Experiment 3 analysis: average response time and overhead of each algorithm.

Reads the rows written by exp3.sh, prints a summary table and a per-process
response time table, and saves both to results/exp3<case>_table.md.

Usage:  python3 exp3_analyze.py a            # reads results/exp3a_results.csv
        python3 exp3_analyze.py b [file.csv]
"""
import csv
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ORDER = ["RR", "SJF", "FCFS", "MLFQ"]   # row order in the tables

if len(sys.argv) < 2 or sys.argv[1] not in ("a", "b"):
    sys.exit("usage: python3 exp3_analyze.py a|b [results.csv]")
CASE = sys.argv[1]
IN_PATH = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(f"results/exp3{CASE}_results.csv")
OUT_PATH = IN_PATH.with_name(f"exp3{CASE}_table.md")


def t_critical(n):
    """Approximate two-sided 95% t value for n samples (2.045 at n = 30)."""
    df = n - 1
    return 1.96 + 2.4 / df if df > 0 else math.nan


def load(path):
    runs = defaultdict(list)
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            runs[row["algo"]].append(row)
    return runs


def mean_of(rows, col):
    return statistics.fmean(float(r[col]) for r in rows)


def summarize(runs):
    sjf = runs["SJF"]
    baseline_total = mean_of(sjf, "total_us")
    baseline_switches = mean_of(sjf, "switches")
    # overheads smaller than 3 std of the baseline can't be told apart from noise
    noise = 3 * statistics.stdev(float(r["total_us"]) for r in sjf)

    stats = {}
    for algo, rows in runs.items():
        avg_rt = [float(r["avg_rt"]) for r in rows]
        mean = statistics.fmean(avg_rt)
        sd = statistics.stdev(avg_rt)
        switches = mean_of(rows, "switches")
        overhead = mean_of(rows, "total_us") - baseline_total
        measurable = algo != "SJF" and overhead > noise
        extra_switches = switches - baseline_switches
        stats[algo] = {
            "n": len(rows), "quantum": int(rows[0]["quantum"]),
            "mean": mean, "sd": sd, "cv": sd / mean * 100 if mean else math.nan,
            "ci": t_critical(len(rows)) * sd / math.sqrt(len(rows)),
            "rt": [mean_of(rows, f"rt{i}") for i in range(1, 5)],
            "switches": switches,
            "overhead_ms": overhead / 1000 if measurable else None,
            "per_switch": overhead / extra_switches if measurable and extra_switches > 0 else None,
        }
    return stats, baseline_total, noise


def fmt(value, digits=0):
    return "—" if value is None else f"{value:,.{digits}f}"


def label(algo, s):
    return f"{algo} (q = {s['quantum']} µs)" if s["quantum"] else algo


def main():
    runs = load(IN_PATH)
    stats, baseline_total, noise = summarize(runs)
    algos = [a for a in ORDER if a in stats]
    best = min(algos, key=lambda a: stats[a]["mean"])
    trials = min(s["n"] for s in stats.values())
    first = next(iter(runs.values()))[0]
    workloads = [int(first[f"w{i}"]) for i in range(1, 5)]

    summary = ["| Algorithm | Avg RT (µs) | Std (µs) | CV % | Switches | Overhead (ms) | Per switch (µs) |",
               "|---|---:|---:|---:|---:|---:|---:|"]
    for algo in algos:
        s = stats[algo]
        if algo == "SJF":
            overhead = "baseline"
        else:
            overhead = "≈ 0" if s["overhead_ms"] is None else fmt(s["overhead_ms"], 1)
        cells = [label(algo, s), fmt(s["mean"], 1), fmt(s["sd"], 1), fmt(s["cv"], 1),
                 fmt(s["switches"]), overhead, fmt(s["per_switch"], 1)]
        if algo == best:
            cells[:2] = [f"**{c}**" for c in cells[:2]]
        summary.append("| " + " | ".join(cells) + " |")

    per_process = ["| Algorithm | " + " | ".join(f"P{i + 1} ({w:,})" for i, w in enumerate(workloads))
                   + " | Average |",
                   "|---|" + "---:|" * 5]
    for algo in algos:
        s = stats[algo]
        per_process.append("| " + " | ".join([label(algo, s)] + [fmt(v, 1) for v in s["rt"]]
                                             + [fmt(s["mean"], 1)]) + " |")

    caption = (f"**Table.** Case 3{CASE}: average response time by algorithm "
               f"(workloads {', '.join(f'{w:,}' for w in workloads)}; {trials} trials each, "
               f"random order per trial). Overhead = total time − SJF total time "
               f"(mean {baseline_total / 1000:,.1f} ms); ≈ 0 = below the baseline's noise "
               f"(3 std = {noise / 1000:.0f} ms). Per switch = overhead ÷ extra switches.")
    b = stats[best]
    notes = [f"- Best: **{label(best, b)}**, avg RT {b['mean']:,.1f} ± {b['ci']:,.1f} µs (95% CI)."]
    for algo in algos:
        if algo != best:
            notes.append(f"- {label(algo, stats[algo])}: {stats[algo]['mean'] / b['mean']:,.0f}× "
                         f"the best average response time.")
    if "MLFQ" not in stats:
        notes.append("- MLFQ not included (no MLFQ rows in the data).")

    report = "\n\n".join([caption, "\n".join(summary), "\n".join(notes),
                          f"### Mean response time per process (µs), Case 3{CASE}",
                          "\n".join(per_process)])
    OUT_PATH.write_text(report + "\n")
    print(report)
    print(f"\nSaved {OUT_PATH}", file=sys.stderr)


if __name__ == "__main__":
    main()
