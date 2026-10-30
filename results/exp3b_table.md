**Table.** Case 3b: average response time by algorithm (workloads 100,000, 100,000, 100,000, 100,000; 30 trials each, random order per trial). Overhead = total time − SJF total time (mean 1,686.2 ms); ≈ 0 = below the baseline's noise (3 std = 26 ms). Per switch = overhead ÷ extra switches.

| Algorithm | Avg RT (µs) | Std (µs) | CV % | Switches | Overhead (ms) | Per switch (µs) |
|---|---:|---:|---:|---:|---:|---:|
| RR (q = 2 µs) | 30.5 | 6.9 | 22.6 | 471,468 | 4,423.3 | 9.4 |
| SJF | 633,250.0 | 4,241.9 | 0.7 | 4 | baseline | — |
| FCFS | 633,121.5 | 4,640.8 | 0.7 | 4 | ≈ 0 | — |
| **MLFQ (q = 1 µs)** | **26.8** | 8.7 | 32.5 | 8 | ≈ 0 | — |

- Best: **MLFQ (q = 1 µs)**, avg RT 26.8 ± 3.3 µs (95% CI).
- RR (q = 2 µs): 1× the best average response time.
- SJF: 23,599× the best average response time.
- FCFS: 23,595× the best average response time.

### Mean response time per process (µs), Case 3b

| Algorithm | P1 (100,000) | P2 (100,000) | P3 (100,000) | P4 (100,000) | Average |
|---|---:|---:|---:|---:|---:|
| RR (q = 2 µs) | 0.0 | 22.8 | 40.9 | 58.4 | 30.5 |
| SJF | 0.0 | 423,432.1 | 844,198.9 | 1,265,368.9 | 633,250.0 |
| FCFS | 0.0 | 423,091.1 | 844,634.1 | 1,264,760.9 | 633,121.5 |
| MLFQ (q = 1 µs) | 0.1 | 20.6 | 36.0 | 50.6 | 26.8 |
