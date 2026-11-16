# OS Resource Manager Simulator (osrm) - Technical Laboratory Report

**Course:** Operating Systems Laboratory (ENSC-351), B.Tech Semester V  
**Target Environment:** Ubuntu 24.04 LTS (WSL2 / Linux Kernel), Python 3.10+, Bash 5+  
**Student Project Type:** Flagship Capstone Engineering Application  
**Primary Reference:** Silberschatz, Galvin, Gagne, *Operating System Concepts*, 10th Edition.

---

## 1. Problem Statement & Objectives

Operating system resource allocators (disk head schedulers, CPU dispatchers, virtual memory page replacers, and deadlock avoidance bankers) operate within the kernel under tight performance budgets. Computer science pedagogy often suffers from isolated, disconnected scripts that obscure the shared architectural principles uniting these mechanisms.

### Core Objectives:
1. **Architectural Integration:** Build a unified simulation core in pure Python 3 where all algorithms, metrics, and logs share common defensive validation and serialization models.
2. **Dual Front-End Accessibility:** Deliver both an ANSI-colored interactive terminal interface (`ui/menus.py`) and a themed cybernetic local web dashboard (`web/static/`), both served by Python standard library without heavy external web frameworks.
3. **Mathematical Rigor:** Ensure 100% adherence to verified academic benchmarks (e.g., Silberschatz disk movement benchmarks: 640/236/236/208/382/322 cylinders; Belady's Anomaly: 9 vs. 10 faults).
4. **Host-Simulator Parity:** Provide a Bash automation bridge to retrieve live Linux host telemetry (`sysinfo.sh`, `collect_logs.sh`) and contrast simulated structures with real hardware metrics.

---

## 2. Theoretical Foundations & Algorithmic Mechanics

### 2.1 Disk Head Scheduling
The hard disk drive (HDD) arm incurs mechanical seek latency moving read/write heads between concentric tracks.
- **FCFS (First-Come, First-Served):** Pure FIFO order. Completely fair and starvation-free, but incurs severe head thrashing on scattered request queues.
- **SSTF (Shortest Seek Time First):** Greedily selects the pending cylinder closest to the current head. Minimizes immediate seek latency but risks starvation for requests located at peripheral disk tracks.
- **SCAN (Elevator Algorithm):** The arm traverses continuously in one direction servicing pending requests until reaching disk boundary (cylinder 0 or $N-1$), then reverses direction. Prevents starvation while maintaining high throughput.
- **LOOK:** An optimization over SCAN that reverses direction immediately after servicing the outermost pending request in the current direction, eliminating wasted travel to physical disk boundaries.
- **C-SCAN (Circular SCAN):** Traverses in a single direction to the disk boundary, then rapidly resets the arm to the opposite boundary via an unserviced return jump. Provides uniform wait times across all tracks.
- **C-LOOK (Circular LOOK):** Restricts C-SCAN sweeps strictly to the bounds of active requests, jumping directly from the highest requested cylinder to the lowest without traveling to physical track extremities.

#### Worked Example (Textbook Benchmark):
Queue = `[98, 183, 37, 122, 14, 124, 65, 67]`, Head = `53`, Disk = `0..199`, Direction = `Left`
- **FCFS:** $53 \to 98 (45) \to 183 (85) \to 37 (146) \to 122 (85) \to 14 (108) \to 124 (110) \to 65 (59) \to 67 (2) = \mathbf{640\text{ cyl}}$.
- **SSTF:** $53 \to 65 (12) \to 67 (2) \to 37 (30) \to 14 (23) \to 98 (84) \to 122 (24) \to 124 (2) \to 183 (59) = \mathbf{236\text{ cyl}}$.
- **LOOK (Left):** Arm moves left: $53 \to 37 (16) \to 14 (23)$ (distance $39$); reverses right: $14 \to 65 \to 67 \to 98 \to 122 \to 124 \to 183$ (distance $169$). Total = $39 + 169 = \mathbf{208\text{ cyl}}$.

---

### 2.2 CPU Scheduling
The short-term scheduler selects from ready processes in memory to allocate CPU time slices.
- **FCFS:** Non-preemptive, allocated in arrival order. Vulnerable to the *convoy effect* where short processes wait behind CPU-bound giants.
- **SJF (Shortest Job First):** Non-preemptive. Provably minimizes average waiting time for simultaneous batch workloads.
- **SRTF (Shortest Remaining Time First):** Preemptive SJF. If a newly arrived process requires less burst time than the currently executing process has remaining, the running process is preempted.
- **Round Robin (RR):** Preemptive with fixed time quantum $q$. Guarantees responsive time-sharing and eliminates process starvation.
- **Priority:** Processes are dispatched based on priority rank (lower numerical value = higher urgency).

#### Worked Example:
$P_1(0, 24), P_2(0, 3), P_3(0, 3)$:
- **FCFS:** $P_1(0..24), P_2(24..27), P_3(27..30)$. Waiting: $P_1=0, P_2=24, P_3=27$. Average Waiting = $\frac{51}{3} = \mathbf{17.0}$.
- **SJF:** $P_2(0..3), P_3(3..6), P_1(6..30)$. Waiting: $P_2=0, P_3=3, P_1=6$. Average Waiting = $\frac{9}{3} = \mathbf{3.0}$.
- **RR ($q=4$):** $P_1(0..4) \to P_2(4..7) \to P_3(7..10) \to P_1(10..30)$. Waiting: $P_1=6, P_2=4, P_3=7$. Average Waiting = $\frac{17}{3} = \mathbf{5.67}$.

---

### 2.3 Virtual Memory Page Replacement
When physical memory frames are saturated during a page fault, the replacement policy selects a resident victim page to evict.
- **FIFO:** Evicts the page resident in memory for the longest chronological time. Susceptible to **Belady's Anomaly**, where allocating more physical frames counter-intuitively increases total page faults.
- **LRU (Least Recently Used):** Approximates optimal replacement by exploiting temporal locality: evicts the page whose last memory reference occurred furthest in the past. Provably a stack algorithm immune to Belady's Anomaly.
- **Optimal (Belady's MIN):** Evicts the resident page that will not be accessed for the longest duration in future execution. Serves as the theoretical lower bound benchmark.

#### Belady's Anomaly Empirical Proof:
Reference String = `[1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]` under FIFO:
- **3 Frames Allocated:** Incurs exactly $\mathbf{9\text{ page faults}}$.
- **4 Frames Allocated:** Incurs exactly $\mathbf{10\text{ page faults}}$ ($+1$ fault despite $33\%$ increase in physical memory!).

---

### 2.4 Deadlock Avoidance (Banker's Algorithm)
Dijkstra's Banker's Algorithm dynamically tests resource allocation safety by verifying whether at least one sequence of process completions exists that satisfies all remaining declared maximum demands without deadlock.

#### Safety Algorithm:
1. Let $\text{Work} = \text{Available}$, and $\text{Finish}[i] = \text{False}$ for all processes $i$.
2. Find index $i$ such that $\text{Finish}[i] == \text{False}$ and $\text{Need}[i] \le \text{Work}$.
3. If found, simulate process completion: $\text{Work} = \text{Work} + \text{Allocation}[i]$; $\text{Finish}[i] = \text{True}$. Repeat step 2.
4. If all processes complete, the system is in a **SAFE state**; otherwise, it is in an **UNSAFE state**.

---

## 3. Comparative Results & Benchmark Summary

| Subsystem | Metric Evaluated | Benchmark Dataset | Optimal Algorithm | Worst Algorithm | Empirical Improvement |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Disk Scheduling** | Total Cylinder Head Movement | 8 Requests, Head=53, 0..199 | **LOOK (208 cyl)** | FCFS (640 cyl) | **67.5% reduction** |
| **CPU Scheduling** | Average Process Waiting Latency | P1(24), P2(3), P3(3) | **SJF (3.00 units)** | FCFS (17.00 units) | **82.4% reduction** |
| **Page Replacement** | Total Page Faults | 20 Accesses, 3 Frames | **Optimal (9 faults)** | FIFO (15 faults) | **40.0% reduction** |
| **Deadlock Banker** | Safe Execution Sequence | 5 Processes, 3 Resources | **SAFE (P1->P3->P4->P0->P2)** | Unsafe with [0,0,0] | **100% deadlock immunity** |

---

## 4. Software Architecture & Implementation Integrity

1. **Pure Standard Library Backend:** The HTTP web server uses `http.server.ThreadingHTTPServer`. It requires zero external web frameworks (no Flask, FastAPI, or Django), ensuring zero installation overhead in WSL2/Ubuntu.
2. **Defensive Validation Layer:** Custom domain exceptions (`InvalidInputError`, `OutOfRangeError`, `EmptyInputError`, `FileFormatError`) enforce field-level attribution, ensuring the server never crashes on malformed boundary payloads.
3. **Peak Glow Cybernetic UI:** Vanilla Canvas 2D API renderer with offscreen cached Gaussian potential field, halo bleed, and comet-drawn vectors. Operates 100% offline without Node.js, npm, or CDN fonts.
4. **Automated Verification:** 55 comprehensive unit and API tests verified via `run_tests.sh`.

---

## 5. Limitations & Future Scope

### Limitations:
- Simulation assumes discrete uniform track travel; modern HDDs utilize zone bit recording (ZBR) with non-uniform sector density.
- CPU scheduler models zero context-switch overhead latency.

### Future Scope:
- Integration of Multi-Level Feedback Queue (MLFQ) with dynamic priority aging.
- Extension of virtual memory models to simulate inverted page tables and translation lookaside buffers (TLBs).
- Direct eBPF Linux tracepoint integration for hardware-level kernel telemetry.

---

## 6. References
1. Silberschatz, A., Galvin, P. B., & Gagne, G. (2018). *Operating System Concepts* (10th ed.). John Wiley & Sons.
2. Tanenbaum, A. S., & Bos, H. (2015). *Modern Operating Systems* (4th ed.). Pearson.
3. Belady, L. A., Nelson, R. A., & Shedler, G. S. (1969). *An anomaly in space-time characteristics of certain programs running in a paging machine*. Communications of the ACM, 12(6), 349-353.
