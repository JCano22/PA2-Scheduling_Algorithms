#!/usr/bin/env python3
"""
Experiment 2 analysis: MLFQ average response time vs first-level quantum.

Reads the rows written by exp2.sh and prints one table for the report
(every other quantum plus the best one) and saves it, along with a full
20-row version, to results/exp2_table.md.

"Jobs to Q2" is how many of the 4 jobs did not finish within their level-1
quantum and moved to the FCFS queue (switches - 4, since each job is dispatched
once in level 1 and once more if demoted):
  4 of 4 -> almost FCFS-only (level 1 barely runs anything)
  0 of 4 -> RR-only (every job finishes in level 1, so level 2 is never used)

Usage:  python3 exp2_analyze.py [results/exp2_results.csv]
"""
import csv
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

IN_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("results/exp2_results.csv")
OUT_PATH = IN_PATH.with_name("exp2_table.md")
JOBS = 4


def t_critical(n):
    """Approximate two-sided 95% t value for n samples (2.045 at n = 30)."""
    df = n - 1
    return 1.96 + 2.4 / df if df > 0 else math.nan


def load(path):
    """Group runs by (algo, quantum). SJF rows (quantum 0) are the baseline."""
    runs = defaultdict(list)
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            runs[(row["algo"], int(row["quantum"]))].append(row)
    return runs


def summarize(runs):
    sjf = runs[("SJF", 0)]
    baseline_total = statistics.fmean(float(r["total_us"]) for r in sjf)
    # overheads smaller than 3 std of the baseline can't be told apart from noise
    noise = 3 * statistics.stdev(float(r["total_us"]) for r in sjf)

    stats = {}
    for (algo, q), rows in runs.items():
        if algo != "MLFQ":
            continue
        avg_rt = [float(r["avg_rt"]) for r in rows]
        mean = statistics.fmean(avg_rt)
        sd = statistics.stdev(avg_rt)
        switches = statistics.fmean(float(r["switches"]) for r in rows)
        overhead = statistics.fmean(float(r["total_us"]) for r in rows) - baseline_total
        stats[q] = {"n": len(rows), "mean": mean, "sd": sd, "cv": sd / mean * 100,
                    "ci": t_critical(len(rows)) * sd / math.sqrt(len(rows)),
                    "switches": switches, "demoted": switches - JOBS,
                    "overhead_ms": overhead / 1000 if overhead > noise else None}
    return stats, len(sjf), baseline_total, noise


def fmt(value, digits=0):
    return "—" if value is None else f"{value:,.{digits}f}"


def table(stats, quanta, best):
    lines = ["| Quantum (µs) | Avg RT (µs) | Std (µs) | CV % | Jobs to Q2 | Switches | Overhead (ms) |",
             "|---:|---:|---:|---:|---:|---:|---:|"]
    for q in quanta:
        s = stats[q]
        overhead = "≈ 0" if s["overhead_ms"] is None else fmt(s["overhead_ms"], 1)
        cells = [fmt(q), fmt(s["mean"], 1), fmt(s["sd"], 1), fmt(s["cv"], 1),
                 f"{s['demoted']:.1f} of {JOBS}", fmt(s["switches"], 1), overhead]
        if q == best:
            cells[:2] = [f"**{c}**" for c in cells[:2]]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main():
    runs = load(IN_PATH)
    stats, sjf_runs, baseline_total, noise = summarize(runs)
    quanta = sorted(stats)
    best = min(quanta, key=lambda q: stats[q]["mean"])
    trials = min(s["n"] for s in stats.values())

    # every other quantum, always keeping the best one and the sample's ~1000 µs
    compact = sorted(set(quanta[::2]) | {best, min(quanta, key=lambda q: abs(q - 1000))})

    # quanta whose 95% CI overlaps the best one's: statistically tied with it
    b = stats[best]
    tied = [q for q in quanta if q != best and stats[q]["mean"] - stats[q]["ci"] <= b["mean"] + b["ci"]]

    # where MLFQ turns into one of its single-queue extremes
    all_demoted = [q for q in quanta if stats[q]["demoted"] >= JOBS - 0.05]
    none_demoted = [q for q in quanta if stats[q]["demoted"] <= 0.05]

    caption = (f"**Table 2.** MLFQ average response time vs. first-level quantum "
               f"(default workloads, {trials} trials per quantum, random order per trial). "
               f"Jobs to Q2 = jobs that did not finish in their level-1 quantum (mean). "
               f"Overhead = MLFQ total time − SJF total time (no-preemption baseline, "
               f"{sjf_runs} runs, mean {baseline_total / 1000:,.1f} ms); ≈ 0 = below the "
               f"baseline's noise (3 std = {noise / 1000:.0f} ms). At large quanta the extra "
               f"time is idle sleep after a job finishes mid-slice, not switching cost.")
    notes = [
        f"- Best quantum: **{best} µs**, avg RT {b['mean']:.1f} ± {b['ci']:.1f} µs (95% CI), "
        f"{b['demoted']:.1f} of {JOBS} jobs moved to Q2.",
        f"- Statistically tied with best (overlapping 95% CI): "
        f"{', '.join(f'{q} µs' for q in tied) if tied else 'none'}.",
        f"- All jobs moved to Q2 (level 1 is just one tiny RR pass, then FCFS): "
        f"q ≤ {max(all_demoted)} µs." if all_demoted else "- No quantum sent every job to Q2.",
        f"- No jobs moved to Q2 (RR-only, one pass): q ≥ {min(none_demoted)} µs."
        if none_demoted else "- Every quantum sent at least one job to Q2.",
        f"- CV range: {min(s['cv'] for s in stats.values()):.1f}% – "
        f"{max(s['cv'] for s in stats.values()):.1f}% "
        f"(highest at q = {max(quanta, key=lambda q: stats[q]['cv'])} µs).",
    ]

    report = "\n\n".join([
        caption, table(stats, compact, best), "\n".join(notes),
        "### All quanta", table(stats, quanta, best),
    ])
    OUT_PATH.write_text(report + "\n")
    print(report)
    print(f"\nSaved {OUT_PATH}", file=sys.stderr)


if __name__ == "__main__":
    main()
