**Table.** Case 3a: average response time by algorithm (workloads 100,000, 50,000, 25,000, 10,000; 30 trials each, random order per trial). Overhead = total time − SJF total time (mean 568.6 ms); ≈ 0 = below the baseline's noise (3 std = 15 ms). Per switch = overhead ÷ extra switches.

| Algorithm | Avg RT (µs) | Std (µs) | CV % | Switches | Overhead (ms) | Per switch (µs) |
|---|---:|---:|---:|---:|---:|---:|
| RR (q = 2 µs) | 28.4 | 7.0 | 24.6 | 158,173 | 1,477.6 | 9.3 |
| SJF | 47,800.9 | 3,092.6 | 6.5 | 4 | baseline | — |
| FCFS | 378,398.5 | 3,213.5 | 0.8 | 4 | ≈ 0 | — |
| **MLFQ (q = 1 µs)** | **25.5** | 9.1 | 35.7 | 8 | ≈ 0 | — |

- Best: **MLFQ (q = 1 µs)**, avg RT 25.5 ± 3.4 µs (95% CI).
- RR (q = 2 µs): 1× the best average response time.
- SJF: 1,877× the best average response time.
- FCFS: 14,857× the best average response time.

### Mean response time per process (µs), Case 3a

| Algorithm | P1 (100,000) | P2 (50,000) | P3 (25,000) | P4 (10,000) | Average |
|---|---:|---:|---:|---:|---:|
| RR (q = 2 µs) | 0.0 | 21.4 | 37.9 | 54.2 | 28.4 |
| SJF | 148,619.2 | 36,407.5 | 6,177.0 | 0.0 | 47,800.9 |
| FCFS | 0.0 | 420,088.0 | 531,835.2 | 561,670.7 | 378,398.5 |
| MLFQ (q = 1 µs) | 0.0 | 19.2 | 34.2 | 48.5 | 25.5 |
