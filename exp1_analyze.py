#!/usr/bin/env python3
"""
Experiment 1 analysis: RR average response time and context-switch overhead vs quantum.

Reads the rows written by exp1.sh and prints one table for the report
(every other quantum plus the best one) and saves it, along with a full
20-row version, to results/exp1_table.md.

Usage:  python3 exp1_analyze.py [results/exp1_results.csv]
"""
import csv
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

IN_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("results/exp1_results.csv")
OUT_PATH = IN_PATH.with_name("exp1_table.md")


def t_critical(n):
    """Approximate two-sided 95% t value for n samples (2.045 at n = 30)."""
    df = n - 1
    return 1.96 + 2.4 / df if df > 0 else math.nan


def load(path):
    """Group runs by quantum. SJF rows (quantum 0) are the no-preemption baseline."""
    runs = defaultdict(list)
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            runs[(row["algo"], int(row["quantum"]))].append(row)
    return runs


def summarize(runs):
    sjf = runs[("SJF", 0)]
    baseline_total = statistics.fmean(float(r["total_us"]) for r in sjf)
    baseline_switches = statistics.fmean(float(r["switches"]) for r in sjf)
    # overheads smaller than 3 std of the baseline can't be told apart from noise
    noise = 3 * statistics.stdev(float(r["total_us"]) for r in sjf)

    stats = {}
    for (algo, q), rows in runs.items():
        if algo != "RR":
            continue
        avg_rt = [float(r["avg_rt"]) for r in rows]
        mean = statistics.fmean(avg_rt)
        sd = statistics.stdev(avg_rt)
        switches = statistics.fmean(float(r["switches"]) for r in rows)
        total = statistics.fmean(float(r["total_us"]) for r in rows)

        # extra wall time vs SJF doing the same work with only 4 switches
        overhead = total - baseline_total
        extra_switches = switches - baseline_switches
        # a job finishing mid-slice can leave the parent sleeping up to one quantum,
        # so idle time is at most 4q; only call it switching cost when that bound is small
        measurable = overhead > noise
        switch_dominated = measurable and 4 * q < 0.1 * overhead
        per_switch = overhead / extra_switches if switch_dominated and extra_switches > 0 else None

        stats[q] = {"n": len(rows), "mean": mean, "sd": sd, "cv": sd / mean * 100,
                    "ci": t_critical(len(rows)) * sd / math.sqrt(len(rows)),
                    "switches": switches,
                    "overhead_ms": overhead / 1000 if measurable else None,
                    "per_switch": per_switch}
    return stats, len(sjf), baseline_total, noise


def fmt(value, digits=0):
    return "—" if value is None else f"{value:,.{digits}f}"


def table(stats, quanta, best):
    lines = ["| Quantum (µs) | Avg RT (µs) | Std (µs) | CV % | Switches | Overhead (ms) | Per switch (µs) |",
             "|---:|---:|---:|---:|---:|---:|---:|"]
    for q in quanta:
        s = stats[q]
        overhead = "≈ 0" if s["overhead_ms"] is None else fmt(s["overhead_ms"], 1)
        cells = [fmt(q), fmt(s["mean"], 1), fmt(s["sd"], 1), fmt(s["cv"], 1),
                 fmt(s["switches"]), overhead, fmt(s["per_switch"], 1)]
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

    switch_costs = [s["per_switch"] for s in stats.values() if s["per_switch"] is not None]

    caption = (f"**Table 1.** RR average response time and context-switch overhead vs. quantum "
               f"(default workloads, {trials} trials per quantum). Overhead = RR total time − SJF "
               f"total time (no-preemption baseline, {sjf_runs} runs, mean "
               f"{baseline_total / 1000:,.1f} ms); ≈ 0 = below the baseline's noise "
               f"(3 std = {noise / 1000:.0f} ms). Per switch = overhead ÷ extra switches, shown "
               f"only where idle time from jobs finishing mid-slice (≤ 4 × quantum) is under 10% "
               f"of the overhead.")
    notes = [
        f"- Best quantum: **{best} µs**, avg RT {b['mean']:.1f} ± {b['ci']:.1f} µs (95% CI).",
        f"- Statistically tied with best (overlapping 95% CI): "
        f"{', '.join(f'{q} µs' for q in tied) if tied else 'none'}.",
        f"- CV range: {min(s['cv'] for s in stats.values()):.1f}% – "
        f"{max(s['cv'] for s in stats.values()):.1f}% "
        f"(highest at q = {max(quanta, key=lambda q: stats[q]['cv'])} µs).",
    ]
    if switch_costs:
        notes.append(f"- Estimated cost per context switch: "
                     f"{min(switch_costs):.1f} – {max(switch_costs):.1f} µs.")

    report = "\n\n".join([
        caption, table(stats, compact, best), "\n".join(notes),
        "### All quanta", table(stats, quanta, best),
    ])
    OUT_PATH.write_text(report + "\n")
    print(report)
    print(f"\nSaved {OUT_PATH}", file=sys.stderr)


if __name__ == "__main__":
    main()
