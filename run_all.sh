#!/bin/bash
# Runs Experiments 1, 2, 3a and 3b and prints a summary table for each.
#
# Every experiment repeats each case TRIALS times, in a random order per trial.
# SJF is run alongside each experiment as a no-preemption baseline: overhead is
# the extra total time compared with SJF ("~0" = within the baseline's noise).
# Experiment 2 and MLFQ in Experiment 3 run only if mlfq.c is present.
#
# Usage:  ./run_all.sh                 # all experiments, 5 trials (~4-6 min)
#         ./run_all.sh 1 3a            # only the listed experiments
#         TRIALS=30 ./run_all.sh       # trial count used in the report
#         RR_Q=2 MLFQ_Q=1 ./run_all.sh # quanta used in Experiment 3 (µs)
#
# Raw results are saved in demo_results/.

TRIALS=${TRIALS:-5}
RR_Q=${RR_Q:-2}       # best RR quantum from Experiment 1
MLFQ_Q=${MLFQ_Q:-1}   # best MLFQ quantum from Experiment 2
QUANTA="1 2 4 8 16 32 64 128 256 512 1024 2048 4096 8192 16384 32768 65536 131072 262144 524288"
DEFAULT_W="100000 50000 25000 10000"
EQUAL_W="100000 100000 100000 100000"
OUT=demo_results
HEADER="trial,algo,quantum,w1,w2,w3,w4,rt1,rt2,rt3,rt4,avg_rt,tt1,tt2,tt3,tt4,et1,et2,et3,et4,total_us,switches,overhead_us"

EXPERIMENTS=${*:-"1 2 3a 3b"}

cd "$(dirname "$0")" || exit 1
mkdir -p build "$OUT"

echo "Compiling..."
for prog in sjf fcfs rr; do
    cc -O0 -o "build/$prog" "$prog.c" || exit 1
done
HAVE_MLFQ=0
if [ -e mlfq.c ]; then
    cc -O0 -o build/mlfq mlfq.c || exit 1
    HAVE_MLFQ=1
else
    echo "mlfq.c not found: skipping Experiment 2 and MLFQ in Experiment 3."
fi

# run_cases <csv> <workloads> <config>...
# Each config is "<program> [quantum]". Runs every config once per trial, shuffled.
run_cases() {
    local csv=$1 workloads=$2
    shift 2
    echo "$HEADER" > "$csv"
    for trial in $(seq 1 "$TRIALS"); do
        printf '%s\n' "$@" | sort -R | while read -r prog args; do
            ./build/$prog $args $workloads | sed "s/^/$trial,/" >> "$csv"
        done
        printf '  trial %d/%d\r' "$trial" "$TRIALS"
    done
    echo
}

# summarize <csv>: one tab-separated line per (algo, quantum):
# algo, quantum, mean avg RT, std avg RT, mean switches, overhead (ms) vs SJF
summarize() {
    awk -F, '
    NR == 1 { next }
    {
        k = $2 "," $3
        n[k]++; s[k] += $12; ss[k] += $12 * $12; sw[k] += $22; tot[k] += $21
        if ($2 == "SJF") { bn++; bs += $21; bss += $21 * $21 }
    }
    END {
        bm = bs / bn
        bv = bn > 1 ? (bss - bn * bm * bm) / (bn - 1) : 0
        noise = 3 * sqrt(bv > 0 ? bv : 0)
        for (k in n) {
            split(k, p, ",")
            m = s[k] / n[k]
            v = n[k] > 1 ? (ss[k] - n[k] * m * m) / (n[k] - 1) : 0
            ov = tot[k] / n[k] - bm
            if (p[1] == "SJF") ovs = "baseline"
            else if (ov > noise) ovs = sprintf("%.1f", ov / 1000)
            else ovs = "~0"
            printf "%s\t%d\t%.1f\t%.1f\t%.0f\t%s\n", p[1], p[2], m, sqrt(v > 0 ? v : 0), sw[k] / n[k], ovs
        }
    }' "$1"
}

# sweep_table <csv> <algo>: quantum sweep for one algorithm, best quantum marked
sweep_table() {
    summarize "$1" | awk -F'\t' -v a="$2" '$1 == a' | sort -t$'\t' -k2,2n | awk -F'\t' '
    { line[NR] = $0; if (NR == 1 || $3 < best) { best = $3; bq = $2 } }
    END {
        printf "%12s %14s %12s %12s %15s\n", "Quantum(us)", "Avg RT(us)", "Std(us)", "Switches", "Overhead(ms)"
        for (i = 1; i <= NR; i++) {
            split(line[i], f, "\t")
            printf "%12d %14.1f %12.1f %12d %15s%s\n", f[2], f[3], f[4], f[5], f[6], (f[2] == bq ? "   <- lowest avg RT" : "")
        }
        printf "Best quantum: %d us (avg RT %.1f us)\n", bq, best
    }'
}

# compare_table <csv>: one row per algorithm, best average response time marked
compare_table() {
    summarize "$1" | awk -F'\t' '
    BEGIN { split("RR SJF FCFS MLFQ", order, " ") }
    { row[$1] = $0; if (best == "" || $3 < best) { best = $3; ba = $1 } }
    END {
        printf "%-10s %12s %14s %12s %12s %15s\n", "Algorithm", "Quantum(us)", "Avg RT(us)", "Std(us)", "Switches", "Overhead(ms)"
        for (i = 1; i <= 4; i++) {
            if (!(order[i] in row)) continue
            split(row[order[i]], f, "\t")
            q = f[2] > 0 ? f[2] : "-"
            printf "%-10s %12s %14.1f %12.1f %12d %15s%s\n", f[1], q, f[3], f[4], f[5], f[6], (f[1] == ba ? "   <- lowest avg RT" : "")
        }
    }'
}

exp3_configs=(sjf fcfs "rr $RR_Q")
[ "$HAVE_MLFQ" = 1 ] && exp3_configs+=("mlfq $MLFQ_Q")

echo "Trials per case: $TRIALS"
for exp in $EXPERIMENTS; do
    case $exp in
    1)
        echo
        echo "=== Experiment 1: Round Robin quantum sweep (workloads $DEFAULT_W) ==="
        configs=(sjf)
        for q in $QUANTA; do configs+=("rr $q"); done
        run_cases "$OUT/exp1.csv" "$DEFAULT_W" "${configs[@]}"
        sweep_table "$OUT/exp1.csv" RR
        ;;
    2)
        [ "$HAVE_MLFQ" = 1 ] || continue
        echo
        echo "=== Experiment 2: MLFQ first-level quantum sweep (workloads $DEFAULT_W) ==="
        configs=(sjf)
        for q in $QUANTA; do configs+=("mlfq $q"); done
        run_cases "$OUT/exp2.csv" "$DEFAULT_W" "${configs[@]}"
        sweep_table "$OUT/exp2.csv" MLFQ
        ;;
    3a)
        echo
        echo "=== Experiment 3a: all algorithms (workloads $DEFAULT_W) ==="
        run_cases "$OUT/exp3a.csv" "$DEFAULT_W" "${exp3_configs[@]}"
        compare_table "$OUT/exp3a.csv"
        ;;
    3b)
        echo
        echo "=== Experiment 3b: all algorithms (workloads $EQUAL_W) ==="
        run_cases "$OUT/exp3b.csv" "$EQUAL_W" "${exp3_configs[@]}"
        compare_table "$OUT/exp3b.csv"
        ;;
    *)
        echo "Unknown experiment '$exp' (use 1, 2, 3a, 3b)" >&2
        ;;
    esac
done

echo
echo "Raw results saved in $OUT/"
