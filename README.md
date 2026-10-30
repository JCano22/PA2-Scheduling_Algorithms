# CPU Scheduling Algorithms in User Space

COMPE 571 (Embedded Operating Systems), Programming Assignment 2
Jorge Cano and Manuel Villarreal Escamilla

This project implements four classic CPU scheduling algorithms (Round Robin, Shortest Job
First, First Come First Serve, and a two-level Multi-Level Feedback Queue) and compares them
by **average response time**. It also measures the cost of context switching for each one.

## How it works

Each program creates four child processes with `fork()`. Every child runs the same CPU-heavy
task (prime factorization of every number up to a given size), and that size, called the
**workload**, controls how long the child runs. By default the workloads are 100,000, 50,000,
25,000 and 10,000, so P1 is the longest job and P4 the shortest.

The parent process acts as the scheduler. Right after creating each child it pauses it, then
decides which child runs and for how long using UNIX signals:

- `kill(pid, SIGCONT)` resumes a child, and `kill(pid, SIGSTOP)` pauses it.
- `usleep(quantum)` lets a child run for one time slice (the **quantum**, in microseconds).
- `waitpid()` checks whether a child has finished.

This is a user-level scheduler: the operating system still schedules all of the processes
underneath it, so the results approximate each algorithm rather than replace the real OS
scheduler.

**Response time** is the time from when scheduling starts (all processes arrive together at
that moment) until a process runs for the first time. It is different from execution time,
which is how long the process actually spends running.

## Algorithms

| File | Algorithm | How it schedules |
|---|---|---|
| `rr.c` | Round Robin | Each unfinished process runs for one quantum at a time, in circular order, until all finish. Based on the course's sample program. |
| `sjf.c` | Shortest Job First | Sorts the processes by workload and runs each to completion, shortest first. |
| `fcfs.c` | First Come First Serve | Runs each process to completion in the order it was created (P1 to P4). |
| `mlfq.c` | Multi-Level Feedback Queue | Queue 1 gives each process one Round Robin quantum. Processes that don't finish move to queue 2, which runs them to completion in FCFS order. Processes never move back up. |

`sample_program.c` is the original Round Robin sample provided with the assignment, kept for
reference.

## Experiments

Every case was repeated **30 times**, and results report the mean and standard deviation.
Each experiment also ran SJF as a baseline: SJF runs every job once without interruption, so
the extra time another algorithm needs compared with SJF estimates its context-switch
overhead.

| Experiment | Question | Setup |
|---|---|---|
| 1 | Which quantum gives Round Robin the lowest average response time? | RR at 20 quanta doubling from 1 µs to 524,288 µs, default workloads |
| 2 | Which first-level quantum is best for MLFQ? When does MLFQ act like plain RR or plain FCFS? | MLFQ at the same 20 quanta, default workloads |
| 3a | Which algorithm has the best average response time? | All four algorithms with their best quanta, default workloads |
| 3b | Does that change when every job is the same length? | All four algorithms, all workloads set to 100,000 |

## Results

Measured on macOS (Apple Silicon), 30 trials per case. Full tables are in `results/`.

| | RR | SJF | FCFS | MLFQ |
|---|---:|---:|---:|---:|
| Best quantum (Exp 1, 2) | 2 µs | – | – | 1 µs |
| Avg response time, 3a (default workloads) | 28.4 µs | 47,801 µs | 378,399 µs | 25.5 µs |
| Avg response time, 3b (equal workloads) | 30.5 µs | 633,250 µs | 633,122 µs | 26.8 µs |
| Context switches per run, 3a | ~158,000 | 4 | 4 | 8 |

- **Smaller quanta mean faster response.** Each process waits for the turns of the processes
  ahead of it, so response time roughly doubles every time the quantum doubles. Below about
  8 µs it stops improving, because the cost of a switch is larger than the quantum itself.
- **RR and MLFQ are effectively tied for the best response time,** since MLFQ's first queue is
  Round Robin. MLFQ gets there with 8 context switches instead of RR's ~158,000.
- **Context switches cost about 9–13 µs each.** At its best quantum, RR spends about 1.5 s
  (3a) to 4.4 s (3b) on switching overhead, compared with about 0.6 s of actual work in 3a.
- **SJF beats FCFS on varied workloads,** because FCFS makes the short jobs wait behind the
  long first job. With equal workloads, the two behave identically.

## Running it

Requires macOS or Linux with `bash` and a C compiler (`cc`). The analysis scripts need
Python 3 (standard library only).

### Quick run of all experiments

```sh
bash run_all.sh                 # all experiments, 5 trials per case (about 5 minutes)
TRIALS=30 bash run_all.sh       # same trial count as our results (about 25-30 minutes)
bash run_all.sh 1 3a            # only the listed experiments (1, 2, 3a, 3b)
```

This compiles the programs, runs each experiment in a random order per trial, and prints a
table for each with the average response time, standard deviation, number of context switches
and overhead. Raw data is saved in `demo_results/`.

### Reproducing the results in `results/`

Each experiment has its own script that collects 30 trials, plus a Python script that turns
the data into tables. The shell scripts won't overwrite existing data, so move the current
CSV out of `results/` first.

```sh
./exp1.sh && python3 exp1_analyze.py              # Experiment 1 (RR quantum sweep)
./exp2.sh && python3 exp2_analyze.py              # Experiment 2 (MLFQ quantum sweep)
MLFQ_Q=1 ./exp3.sh a && python3 exp3_analyze.py a # Experiment 3a
MLFQ_Q=1 ./exp3.sh b && python3 exp3_analyze.py b # Experiment 3b
```

### Running a single program

RR and MLFQ take a quantum in microseconds. All programs accept four optional workload sizes
(defaults: 100000 50000 25000 10000).

```sh
cc -o rr rr.c && ./rr 1000 100000 50000 25000 10000
cc -o sjf sjf.c && ./sjf 100000 100000 100000 100000
```

Each program prints one CSV line:

```
algo,quantum,w1,w2,w3,w4,rt1,rt2,rt3,rt4,avg_rt,tt1,tt2,tt3,tt4,et1,et2,et3,et4,total_us,switches,overhead_us
```

`w` = workloads, `rt` = response times, `tt` = turnaround times, `et` = execution times (all
in µs, for P1 to P4), `total_us` = total run time, `switches` = number of times a process was
resumed, and `overhead_us` = time the scheduler spent between slices.

## Notes

- Exact numbers vary between machines and runs, but the trends and rankings should match.
  Linux's `usleep` has a larger minimum delay than macOS's, so the smallest quanta will behave
  differently there.
- Quanta of 1–4 µs are statistically tied, so the "best" quantum can change between runs.
- At very large quanta, part of the extra time is the scheduler sleeping after a job finishes
  partway through its time slice, not context-switch cost.
