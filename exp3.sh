#!/bin/bash
# Experiment 3: compare RR, SJF, FCFS and MLFQ.
#   Case a: default workloads (100000 50000 25000 10000)
#   Case b: equal workloads   (100000 100000 100000 100000)
#
# Each trial runs every algorithm once, in a random order, so slow periods on
# the machine and run position don't favor any one algorithm. MLFQ is included
# only if mlfq.c exists.
#
# Usage:  ./exp3.sh a                    # 30 trials -> results/exp3a_results.csv
#         ./exp3.sh b                    # 30 trials -> results/exp3b_results.csv
#         TRIALS=2 ./exp3.sh a           # quick test
#         RR_Q=1 MLFQ_Q=64 ./exp3.sh a   # override the quanta

CASE=$1
case "$CASE" in
    a) WORKLOADS="100000 50000 25000 10000" ;;
    b) WORKLOADS="100000 100000 100000 100000" ;;
    *) echo "usage: $0 a|b" >&2; exit 1 ;;
esac

TRIALS=${TRIALS:-30}
OUT=${OUT:-results/exp3${CASE}_results.csv}
RR_Q=${RR_Q:-2}         # best quantum from Experiment 1
MLFQ_Q=${MLFQ_Q:-2}     # replace with the best quantum from Experiment 2

cd "$(dirname "$0")" || exit 1

if [ -e "$OUT" ]; then
    echo "$OUT already exists; move or delete it first." >&2
    exit 1
fi

mkdir -p build "$(dirname "$OUT")"
for prog in sjf fcfs rr; do
    cc -O0 -Wall -o "build/$prog" "$prog.c" || exit 1
done

# one line per algorithm: program and its arguments before the workloads
CONFIGS="sjf
fcfs
rr $RR_Q"
if [ -e mlfq.c ]; then
    cc -O0 -Wall -o build/mlfq mlfq.c || exit 1
    CONFIGS="$CONFIGS
mlfq $MLFQ_Q"
else
    echo "mlfq.c not found; running without MLFQ." >&2
fi

echo "trial,algo,quantum,w1,w2,w3,w4,rt1,rt2,rt3,rt4,avg_rt,tt1,tt2,tt3,tt4,et1,et2,et3,et4,total_us,switches,overhead_us" > "$OUT"

start=$SECONDS
for trial in $(seq 1 "$TRIALS"); do
    echo "$CONFIGS" | sort -R | while read -r prog args; do
        ./build/$prog $args $WORKLOADS | sed "s/^/$trial,/" >> "$OUT"
    done
    echo "trial $trial/$TRIALS done ($((SECONDS - start))s elapsed)" >&2
done

echo "Wrote $OUT" >&2
