#!/bin/bash
# Experiment 1: best time quantum for Round Robin (default workloads).
#
# Each trial runs SJF once (no-preemption baseline for overhead) and RR once at
# every quantum. Trials are the outer loop so slow periods on the machine are
# spread across all quanta instead of hitting only a few.
#
# Usage:  ./exp1.sh                 # 30 trials -> results/exp1_results.csv
#         TRIALS=2 ./exp1.sh        # quick test
#         OUT=path.csv ./exp1.sh    # different output file

TRIALS=${TRIALS:-30}
OUT=${OUT:-results/exp1_results.csv}

# doubling from 1 us (smallest usleep value) past the longest job (~410 ms)
QUANTA="1 2 4 8 16 32 64 128 256 512 1024 2048 4096 8192 16384 32768 65536 131072 262144 524288"

cd "$(dirname "$0")" || exit 1

if [ -e "$OUT" ]; then
    echo "$OUT already exists; move or delete it first." >&2
    exit 1
fi

mkdir -p build "$(dirname "$OUT")"
cc -O0 -Wall -o build/rr rr.c || exit 1
cc -O0 -Wall -o build/sjf sjf.c || exit 1

echo "trial,algo,quantum,w1,w2,w3,w4,rt1,rt2,rt3,rt4,avg_rt,tt1,tt2,tt3,tt4,et1,et2,et3,et4,total_us,switches,overhead_us" > "$OUT"

start=$SECONDS
for trial in $(seq 1 "$TRIALS"); do
    ./build/sjf | sed "s/^/$trial,/" >> "$OUT"
    for q in $QUANTA; do
        ./build/rr "$q" | sed "s/^/$trial,/" >> "$OUT"
    done
    echo "trial $trial/$TRIALS done ($((SECONDS - start))s elapsed)" >&2
done

echo "Wrote $OUT" >&2
