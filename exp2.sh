#!/bin/bash
# Experiment 2: best first-level quantum for MLFQ (default workloads).
#
# Each trial runs SJF once (no-preemption baseline for overhead) and MLFQ once
# at every quantum, in a random order per trial, so slow periods on the machine
# and run position don't favor any quantum.
#
# Usage:  ./exp2.sh                 # 30 trials -> results/exp2_results.csv
#         TRIALS=2 ./exp2.sh        # quick test
#         OUT=path.csv ./exp2.sh    # different output file

TRIALS=${TRIALS:-30}
OUT=${OUT:-results/exp2_results.csv}
WORKLOADS="100000 50000 25000 10000"

# same quanta as Experiment 1: doubling from 1 us past the longest job (~410 ms)
QUANTA="1 2 4 8 16 32 64 128 256 512 1024 2048 4096 8192 16384 32768 65536 131072 262144 524288"

cd "$(dirname "$0")" || exit 1

if [ -e "$OUT" ]; then
    echo "$OUT already exists; move or delete it first." >&2
    exit 1
fi

mkdir -p build "$(dirname "$OUT")"
cc -O0 -Wall -o build/mlfq mlfq.c || exit 1
cc -O0 -Wall -o build/sjf sjf.c || exit 1

# one line per case: program and its arguments before the workloads
CONFIGS="sjf"
for q in $QUANTA; do
    CONFIGS="$CONFIGS
mlfq $q"
done

echo "trial,algo,quantum,w1,w2,w3,w4,rt1,rt2,rt3,rt4,avg_rt,tt1,tt2,tt3,tt4,et1,et2,et3,et4,total_us,switches,overhead_us" > "$OUT"

start=$SECONDS
for trial in $(seq 1 "$TRIALS"); do
    echo "$CONFIGS" | sort -R | while read -r prog args; do
        ./build/$prog $args $WORKLOADS | sed "s/^/$trial,/" >> "$OUT"
    done
    echo "trial $trial/$TRIALS done ($((SECONDS - start))s elapsed)" >&2
done

echo "Wrote $OUT" >&2
