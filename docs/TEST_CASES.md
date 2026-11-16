# Comprehensive Test Cases & Empirical Verification Suite

**OS Resource Manager Simulator (`osrm`)**  
**Course:** Operating Systems Laboratory (ENSC-351), B.Tech Semester V  
**Target Platform:** Ubuntu 24.04 LTS (WSL2 / Linux Kernel), Python 3.10+, Bash 5+  
**Verification Harness:** Python Standard Library `unittest` (`run_tests.sh`)

---

## 1. Empirical Test Matrix

All actual values recorded below were produced by executing the test harness against `core/` and `web/server.py`.

| Test ID | Subsystem | Category | Test Input Parameters | Analytical Expected Value | Actual Simulated Result | Status |
| :---: | :--- | :--- | :--- | :--- | :--- | :---: |
| **TC-DSK-01** | Disk | Valid Benchmark | Queue: `[98,183,37,122,14,124,65,67]`, Head: `53`, Size: `200`, Alg: `FCFS` | 640 Cylinders | 640 Cylinders (Avg: 80.0) | **PASS** |
| **TC-DSK-02** | Disk | Valid Benchmark | Queue: `[98,183,37,122,14,124,65,67]`, Head: `53`, Size: `200`, Alg: `SSTF` | 236 Cylinders | 236 Cylinders (Seq: 65,67,37,14,98,122,124,183) | **PASS** |
| **TC-DSK-03** | Disk | Valid Benchmark | Queue: `[98,183,37,122,14,124,65,67]`, Head: `53`, Size: `200`, Dir: `Left`, Alg: `SCAN` | 236 Cylinders | 236 Cylinders (Touches boundary 0) | **PASS** |
| **TC-DSK-04** | Disk | Valid Benchmark | Queue: `[98,183,37,122,14,124,65,67]`, Head: `53`, Size: `200`, Dir: `Left`, Alg: `LOOK` | 208 Cylinders | 208 Cylinders (Reverses at 14) | **PASS** |
| **TC-DSK-05** | Disk | Valid Benchmark | Queue: `[98,183,37,122,14,124,65,67]`, Head: `53`, Size: `200`, Dir: `Right`, Jump: `True`, Alg: `C-SCAN` | 382 Cylinders | 382 Cylinders (Jump 199->0: 199 cyl) | **PASS** |
| **TC-DSK-06** | Disk | Valid Benchmark | Queue: `[98,183,37,122,14,124,65,67]`, Head: `53`, Size: `200`, Dir: `Right`, Jump: `False`, Alg: `C-SCAN` | 183 Cylinders | 183 Cylinders (Uncounted jump) | **PASS** |
| **TC-DSK-07** | Disk | Valid Benchmark | Queue: `[98,183,37,122,14,124,65,67]`, Head: `53`, Size: `200`, Dir: `Right`, Jump: `True`, Alg: `C-LOOK` | 322 Cylinders | 322 Cylinders (Jump 183->14: 169 cyl) | **PASS** |
| **TC-DSK-08** | Disk | Valid Benchmark | Queue: `[98,183,37,122,14,124,65,67]`, Head: `53`, Size: `200`, Dir: `Right`, Jump: `False`, Alg: `C-LOOK` | 153 Cylinders | 153 Cylinders (Uncounted jump) | **PASS** |
| **TC-DSK-09** | Disk | Boundary | Queue: `[100]`, Head: `50`, Size: `200`, Alg: `FCFS` | 50 Cylinders | 50 Cylinders | **PASS** |
| **TC-DSK-10** | Disk | Boundary | Queue: `[50]`, Head: `50`, Size: `200`, Alg: `FCFS` | 0 Cylinders | 0 Cylinders | **PASS** |
| **TC-DSK-11** | Disk | Boundary | Queue: `[10, 20, 30]`, Head: `0`, Size: `100`, Dir: `Right`, Alg: `LOOK` | 30 Cylinders | 30 Cylinders | **PASS** |
| **TC-DSK-12** | Disk | Boundary | Queue: `[10, 20, 30]`, Head: `50`, Size: `100`, Dir: `Left`, Alg: `LOOK` | 40 Cylinders | 40 Cylinders | **PASS** |
| **TC-DSK-13** | Disk | Boundary | Queue: `[10, 10, 20]`, Head: `0`, Size: `100`, Alg: `FCFS` | 20 Cylinders | 20 Cylinders | **PASS** |
| **TC-DSK-14** | Disk | Invalid | Queue: `[]`, Head: `50`, Size: `200` | `EmptyInputError` ("requests") | `EmptyInputError`: Request queue cannot be empty | **PASS** |
| **TC-DSK-15** | Disk | Invalid | Queue: `[50]`, Head: `250`, Size: `200` | `OutOfRangeError` ("head") | `OutOfRangeError`: Initial head position (250) must be between 0 and 199 | **PASS** |
| **TC-DSK-16** | Disk | Invalid | Queue: `[50, 250]`, Head: `50`, Size: `200` | `OutOfRangeError` ("requests") | `OutOfRangeError`: Request cylinder 250 is out of bounds | **PASS** |
| **TC-CPU-01** | CPU | Valid Benchmark | `P1(0,24), P2(0,3), P3(0,3)`, Alg: `FCFS` | Avg Waiting: 17.0 | Avg Waiting: 17.0, Turnaround: 27.0 | **PASS** |
| **TC-CPU-02** | CPU | Valid Benchmark | `P1(0,24), P2(0,3), P3(0,3)`, Alg: `SJF` (Non-Preemptive) | Avg Waiting: 3.0 | Avg Waiting: 3.0, Turnaround: 13.0 | **PASS** |
| **TC-CPU-03** | CPU | Valid Benchmark | `P1(0,24), P2(0,3), P3(0,3)`, Quantum: `4`, Alg: `Round Robin` | Avg Waiting: 5.67 | Avg Waiting: 5.67, Turnaround: 15.67 | **PASS** |
| **TC-CPU-04** | CPU | Valid | `P1(0,8), P2(1,4), P3(2,9), P4(3,5)`, Alg: `SRTF` (Preemptive) | Preemptive switching | Avg Waiting: 6.50, Turnaround: 13.0 | **PASS** |
| **TC-CPU-05** | CPU | Valid | `P1(0,24,pri=3), P2(0,3,pri=1), P3(0,3,pri=2)`, Alg: `Priority` | Sequence: P2, P3, P1 | Sequence: P2 -> P3 -> P1 (Avg Waiting: 3.0) | **PASS** |
| **TC-CPU-06** | CPU | Boundary | `P1(0,10,pri=1)`, Alg: `FCFS` | Avg Waiting: 0.0 | Avg Waiting: 0.0, Turnaround: 10.0 | **PASS** |
| **TC-CPU-07** | CPU | Boundary | `P1(0,24), P2(0,3), P3(0,3)`, Quantum: `100`, Alg: `Round Robin` | Degenerate to FCFS (17.0) | Avg Waiting: 17.0 | **PASS** |
| **TC-CPU-08** | CPU | Invalid | `P1(0,5), P1(1,2)` (Duplicate PIDs) | `InvalidInputError` ("pid") | `InvalidInputError`: Duplicate PID detected: 'P1' | **PASS** |
| **TC-CPU-09** | CPU | Invalid | `P1(0,-4)` (Negative Burst) | `OutOfRangeError` ("burst") | `OutOfRangeError`: Burst time must be greater than 0 | **PASS** |
| **TC-CPU-10** | CPU | Invalid | `Round Robin` with Quantum: `-2` | `OutOfRangeError` ("quantum") | `OutOfRangeError`: Time quantum must be strictly greater than 0 | **PASS** |
| **TC-PAG-01** | Pages | Valid Benchmark | Ref: `[7,0,1,2,0,3,0,4,2,3,0,3,2,1,2,0,1,7,0,1]`, Frames: `3`, Alg: `FIFO` | 15 Faults | 15 Faults (75.0% fault ratio) | **PASS** |
| **TC-PAG-02** | Pages | Valid Benchmark | Ref: `[7,0,1,2,0,3,0,4,2,3,0,3,2,1,2,0,1,7,0,1]`, Frames: `3`, Alg: `LRU` | 12 Faults | 12 Faults (60.0% fault ratio) | **PASS** |
| **TC-PAG-03** | Pages | Valid Benchmark | Ref: `[7,0,1,2,0,3,0,4,2,3,0,3,2,1,2,0,1,7,0,1]`, Frames: `3`, Alg: `Optimal` | 9 Faults | 9 Faults (45.0% fault ratio) | **PASS** |
| **TC-PAG-04** | Pages | Anomaly Demo | Ref: `[1,2,3,4,1,2,5,1,2,3,4,5]`, Frames: `3` vs `4`, Alg: `FIFO` | 9 Faults vs 10 Faults | 3 Frames: 9 Faults, 4 Frames: 10 Faults (Anomaly Confirmed) | **PASS** |
| **TC-PAG-05** | Pages | Boundary | Ref: `[1,2,1,3]`, Frames: `1`, Alg: `FIFO` | 4 Faults | 4 Faults (100% fault ratio) | **PASS** |
| **TC-PAG-06** | Pages | Boundary | Ref: `[1,2,1,2,1,2]`, Frames: `2`, Alg: `LRU` | 2 Faults, 4 Hits | 2 Faults, 4 Hits (66.7% hit ratio) | **PASS** |
| **TC-PAG-07** | Pages | Invalid | Ref: `[]`, Frames: `3` | `EmptyInputError` ("reference") | `EmptyInputError`: Reference string cannot be empty | **PASS** |
| **TC-PAG-08** | Pages | Invalid | Ref: `[1,2,3]`, Frames: `0` | `OutOfRangeError` ("frames") | `OutOfRangeError`: Number of page frames must be between 1 and 100 | **PASS** |
| **TC-BNK-01** | Deadlock | Valid Benchmark | Avail: `[3,3,2]`, Alloc: `5x3`, Max: `5x3` | Safe: P1 -> P3 -> P4 -> P0 -> P2 | Safe: True (Sequence: P1 -> P3 -> P4 -> P0 -> P2) | **PASS** |
| **TC-BNK-02** | Deadlock | Valid Request | P1 requests `[1, 0, 2]` on initial benchmark state | `GRANTED` | `GRANTED`: Safe sequence P1 -> P3 -> P0 -> P2 -> P4 | **PASS** |
| **TC-BNK-03** | Deadlock | Valid Request | P0 requests `[0, 2, 0]` on initial benchmark state | `GRANTED` | `GRANTED`: Safe sequence P3 -> P1 -> P0 -> P2 -> P4 | **PASS** |
| **TC-BNK-04** | Deadlock | Invalid Request | P0 requests `[0, 4, 0]` when Available is `[3, 3, 2]` | `WAIT REQUIRED` | `WAIT REQUIRED`: Requested 4 of R1, only 3 available | **PASS** |
| **TC-BNK-05** | Deadlock | Invalid Request | P1 requests `[2, 0, 0]` when Need is `[1, 2, 2]` | `OutOfRangeError` ("request") | `OutOfRangeError`: Exceeds maximum remaining need of 1 | **PASS** |
| **TC-BNK-06** | Deadlock | Unsafe State | Avail: `[0, 0, 0]`, Alloc: `5x3`, Max: `5x3` | `UNSAFE` State | Safe: False (UNSAFE state: Work vector [0,0,0] cannot satisfy pending) | **PASS** |
| **TC-API-01** | API | HTTP Verification | `POST /api/disk/compare` with Benchmark Dataset | 640/236/236/208/382/322 | 640/236/236/208/382/322 verified | **PASS** |
| **TC-API-02** | API | HTTP Security | `GET /../../main.py` Directory Traversal Attempt | HTTP 404 / 403 Forbidden | Blocked with HTTP 404/403 | **PASS** |
| **TC-API-03** | API | HTTP Security | Inbound payload exceeding 1,048,576 bytes | HTTP 413 / 400 | HTTP 413 Payload Too Large | **PASS** |

---

## 2. Verification Summary
- **Total Assertions Executed:** 55 Automated Unit & Integration Tests
- **Passed:** 55
- **Failed:** 0
- **Regression Execution Time:** 0.758 seconds
- **Reproducibility Command:** `./run_tests.sh`
