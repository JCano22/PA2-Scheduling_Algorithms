# COMPE 571 – Programming Assignment 2: Scheduling Algorithms

## How to run

```sh
bash run_all.sh
```
This compiles all four programs, runs Experiments 1, 2, 3a and 3b, and prints a results table for each. It takes about 5 minutes with the default 5 trials per case.  The actual results in the report were taken using 30 trials per case instead of 5.

Option:
To run the full 30 trials do the following:
```sh
TRIALS=30 bash run_all.sh #same setup as the report (about 25-30min)
```

Notes:
- Results in the report were collected on macOS with 30 trials. Exact numbers will vary between machines and runs, but the trends and rankings should match.
- Quanta of 1–4 µs are statistically tied, so the "best" quantum may change between runs.

## Files

- **rr.c** – Round Robin scheduler based on the provided sample code. Each process runs
  for one quantum at a time in circular order until all processes finish.
- **sjf.c** – Shortest Job First scheduler. It sorts the processes by workload size and
  runs each one to completion, shortest first.
- **fcfs.c** – First Come First Serve scheduler. It runs each process to completion in the
  order the processes were created.
- **mlfq.c** – Two-level Multi-Level Feedback Queue scheduler. Each process gets one
  Round Robin quantum in the first queue, and any unfinished processes then run to
  completion in FCFS order in the second queue.
- **run_all.sh** – Script that compiles the programs and runs all experiments. It repeats
  each case several times in a random order and prints the average response time,
  standard deviation, context switches and overhead for each.

Each program can also be run on its own. RR and MLFQ take a quantum in microseconds, and all programs accept four optional workload sizes (defaults: 100000 50000 25000 10000):

```sh
cc -o rr rr.c && ./rr 1000 100000 50000 25000 10000
cc -o sjf sjf.c && ./sjf 100000 100000 100000 100000
```
Each program prints one CSV line with the per-process response times, the average response time, turnaround times, total time and number of context switches.
