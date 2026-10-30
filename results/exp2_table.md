**Table 2.** MLFQ average response time vs. first-level quantum (default workloads, 30 trials per quantum, random order per trial). Jobs to Q2 = jobs that did not finish in their level-1 quantum (mean). Overhead = MLFQ total time − SJF total time (no-preemption baseline, 30 runs, mean 571.6 ms); ≈ 0 = below the baseline's noise (3 std = 30 ms). At large quanta the extra time is idle sleep after a job finishes mid-slice, not switching cost.

| Quantum (µs) | Avg RT (µs) | Std (µs) | CV % | Jobs to Q2 | Switches | Overhead (ms) |
|---:|---:|---:|---:|---:|---:|---:|
| **1** | **26.3** | 9.3 | 35.4 | 4.0 of 4 | 8.0 | ≈ 0 |
| 4 | 33.4 | 4.8 | 14.4 | 4.0 of 4 | 8.0 | ≈ 0 |
| 16 | 59.0 | 12.6 | 21.3 | 4.0 of 4 | 8.0 | ≈ 0 |
| 64 | 149.0 | 13.4 | 9.0 | 4.0 of 4 | 8.0 | ≈ 0 |
| 256 | 507.6 | 6.4 | 1.3 | 4.0 of 4 | 8.0 | ≈ 0 |
| 1,024 | 1,952.9 | 11.5 | 0.6 | 4.0 of 4 | 8.0 | ≈ 0 |
| 4,096 | 7,695.4 | 71.0 | 0.9 | 4.0 of 4 | 8.0 | ≈ 0 |
| 16,384 | 30,633.8 | 551.1 | 1.8 | 3.0 of 4 | 7.0 | ≈ 0 |
| 65,536 | 105,733.8 | 583.2 | 0.6 | 2.0 of 4 | 6.0 | 113.4 |
| 262,144 | 400,355.8 | 708.4 | 0.2 | 1.0 of 4 | 5.0 | 686.7 |

- Best quantum: **1 µs**, avg RT 26.3 ± 3.5 µs (95% CI), 4.0 of 4 jobs moved to Q2.
- Statistically tied with best (overlapping 95% CI): 2 µs.
- All jobs moved to Q2 (level 1 is just one tiny RR pass, then FCFS): q ≤ 4096 µs.
- No jobs moved to Q2 (RR-only, one pass): q ≥ 524288 µs.
- CV range: 0.0% – 76.9% (highest at q = 128 µs).

### All quanta

| Quantum (µs) | Avg RT (µs) | Std (µs) | CV % | Jobs to Q2 | Switches | Overhead (ms) |
|---:|---:|---:|---:|---:|---:|---:|
| **1** | **26.3** | 9.3 | 35.4 | 4.0 of 4 | 8.0 | ≈ 0 |
| 2 | 27.5 | 9.6 | 34.8 | 4.0 of 4 | 8.0 | ≈ 0 |
| 4 | 33.4 | 4.8 | 14.4 | 4.0 of 4 | 8.0 | ≈ 0 |
| 8 | 41.0 | 9.3 | 22.6 | 4.0 of 4 | 8.0 | ≈ 0 |
| 16 | 59.0 | 12.6 | 21.3 | 4.0 of 4 | 8.0 | ≈ 0 |
| 32 | 84.9 | 7.3 | 8.6 | 4.0 of 4 | 8.0 | ≈ 0 |
| 64 | 149.0 | 13.4 | 9.0 | 4.0 of 4 | 8.0 | ≈ 0 |
| 128 | 310.9 | 239.2 | 76.9 | 4.0 of 4 | 8.0 | ≈ 0 |
| 256 | 507.6 | 6.4 | 1.3 | 4.0 of 4 | 8.0 | ≈ 0 |
| 512 | 989.4 | 8.2 | 0.8 | 4.0 of 4 | 8.0 | ≈ 0 |
| 1,024 | 1,952.9 | 11.5 | 0.6 | 4.0 of 4 | 8.0 | ≈ 0 |
| 2,048 | 3,877.3 | 22.6 | 0.6 | 4.0 of 4 | 8.0 | ≈ 0 |
| 4,096 | 7,695.4 | 71.0 | 0.9 | 4.0 of 4 | 8.0 | ≈ 0 |
| 8,192 | 15,313.1 | 291.3 | 1.9 | 3.0 of 4 | 7.0 | ≈ 0 |
| 16,384 | 30,633.8 | 551.1 | 1.8 | 3.0 of 4 | 7.0 | ≈ 0 |
| 32,768 | 56,682.7 | 24.5 | 0.0 | 2.0 of 4 | 6.0 | 40.4 |
| 65,536 | 105,733.8 | 583.2 | 0.6 | 2.0 of 4 | 6.0 | 113.4 |
| 131,072 | 204,100.0 | 205.9 | 0.1 | 1.0 of 4 | 5.0 | 294.8 |
| 262,144 | 400,355.8 | 708.4 | 0.2 | 1.0 of 4 | 5.0 | 686.7 |
| 524,288 | 793,688.4 | 394.4 | 0.0 | 0.0 of 4 | 4.0 | 1,543.8 |
