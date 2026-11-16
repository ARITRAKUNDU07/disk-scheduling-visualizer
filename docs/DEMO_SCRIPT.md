# OSRM Capstone Project: Demonstration Script & Viva Defense

**Course:** Operating Systems Laboratory (ENSC-351), B.Tech Semester V  
**Project:** OS Resource Manager Simulator (`osrm`)

---

## 1. Five-Minute Live Demonstration Flow

### [0:00 - 0:45] Introduction & Architectural Overview
- **Action:** Open terminal in Ubuntu 24.04 WSL2.
- **Narrative:**
  > "Good morning, evaluators. I am presenting the OS Resource Manager Simulator (`osrm`), an integrated capstone application engineered for ENSC-351. Unlike disjointed scripts, OSRM is built as a single unified system: a pure Python 3 algorithmic core serving both an ANSI terminal CLI and a hardware-accelerated local web dashboard. All algorithms, validations, and metrics are centralized in `core/`."
- **Terminal Execution:**
  ```bash
  ./run_tests.sh
  ```
- **Key Observation:** Highlight all 55 tests passing in < 1 second. Point out that all textbook benchmarks are mathematically verified.

---

### [0:45 - 2:00] Flagship Module: Disk Head Scheduling Studio
- **Action:** Launch the web dashboard:
  ```bash
  ./run.sh web
  ```
  Dashboard opens automatically in browser (`http://127.0.0.1:8080`).
- **Narrative:**
  > "Navigating to the Disk Scheduling Studio. Notice the 'Peak Glow' UI: 100% offline HTML5 Canvas with real-time vector compositing, Gaussian glow fields, and no external npm/React dependencies. The browser never computes algorithms; it purely visualizes JSON returned by our Python standard library server."
- **Actions on Screen:**
  1. Click **'Run'** on the default benchmark queue (`[98, 183, 37, 122, 14, 124, 65, 67]`, Head `53`).
  2. Observe the animated blue comet line and the total movement count-up (`640 cyl` for FCFS).
  3. Click **'Compare All'**: 6 individual Glow Cards render concurrently. Point out that **LOOK (208 cyl)** and **SSTF (236 cyl)** achieve significant seek reductions over FCFS (640 cyl).
  4. Toggle **'Space-Time'** view to inspect the classical physical cylinder-vs-time diagram.
  5. Click **'Playback'** to demonstrate real-time step highlighting in the synchronized trace table.

---

### [2:00 - 3:00] CPU Scheduling & Gantt Visualizer
- **Action:** Switch to **CPU Scheduling** tab.
- **Narrative:**
  > "In the CPU Studio, we evaluate FCFS, Non-Preemptive SJF, Preemptive SRTF, Round Robin, and Priority. On the textbook workload $P_1(24), P_2(3), P_3(3)$, SJF drops average waiting time from 17.0 units down to 3.0 units."
- **Actions on Screen:**
  1. Click **'Run'** for FCFS -> Average waiting 17.0.
  2. Switch dropdown pill to **'SJF'** -> Line morphs and average waiting re-tweens to 3.0.
  3. Switch to **'Round Robin'** with $q=4$ -> Average waiting becomes 5.67 units.
  4. Point out the native Canvas Gantt chart with color-coded process blocks and time stamps.

---

### [3:00 - 3:45] Virtual Memory & Belady's Anomaly Sandbox
- **Action:** Switch to **Page Replacement** tab.
- **Narrative:**
  > "Here we simulate FIFO, LRU, and Belady's Optimal replacement across virtual memory references. The step table highlights Hits in soft emerald glass and Faults in soft rose glass."
- **Actions on Screen:**
  1. Click **'Belady Anomaly'**:
  2. The system evaluates reference string `[1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]`.
  3. Point out: **3 frames = 9 faults**, while **4 frames = 10 faults**. Explain why: FIFO is not a stack algorithm, so increasing allocated memory can degrade hit rate.

---

### [3:45 - 4:30] Deadlock Avoidance (Banker's Algorithm) & Dynamic Requests
- **Action:** Switch to **Deadlock Banker** tab.
- **Actions on Screen:**
  1. Click **'Evaluate Safety'**: Safe sequence `P1 -> P3 -> P4 -> P0 -> P2` animates as sequence chips.
  2. In the Request Sandbox, test $P_1$ requesting `[1, 0, 2]` -> **GRANTED** (Safe sequence established).
  3. Test $P_0$ requesting `[0, 4, 0]` -> **DENIED / WAIT REQUIRED** (Exceeds available resources).
  4. Highlight that invalid or unsafe states are safely rejected with automatic rollback.

---

### [4:30 - 5:00] Host Diagnostics, Report Generation & CLI Menu
- **Actions on Screen:**
  1. Switch to **Tools & Diagnostics** tab -> Click **'Generate Report'**.
  2. Show the generated Markdown report preview with embedded Matplotlib PNG charts saved in `output/reports/`.
  3. Click **'Refresh Host Telemetry'** -> Point out real Linux kernel and memory metrics from `sysinfo.sh`.
  4. Switch back to terminal and show `./run.sh cli` running the full ANSI terminal menu.
- **Concluding Sentence:**
  > "OSRM delivers verified academic accuracy, zero external front-end bloat, and unified software engineering across Python and Linux. Thank you."

---

## 2. Top 10 Viva Defense Questions & Authoritative Answers

### Q1: Why does C-SCAN report 382 cylinders on the Silberschatz benchmark while LOOK reports 208?
**Answer:** C-SCAN traverses to the physical disk boundary (cylinder 199), executes a return jump of 199 cylinders back to cylinder 0 without servicing, and then moves to cylinder 37 ($146 + 199 + 37 = 382$). LOOK restricts arm motion strictly between the highest and lowest pending cylinders ($183$ and $14$), completely avoiding travel to track bounds 0 and 199, yielding an optimal 208 cylinders.

### Q2: What is Belady's Anomaly, and why does LRU never suffer from it?
**Answer:** Belady's Anomaly is the phenomenon where increasing physical frame allocation causes an increase in total page faults. It occurs in FIFO because FIFO does not possess the **inclusion property** (the set of resident pages in $N$ frames is not necessarily a subset of $N+1$ frames). LRU is mathematically a **stack algorithm** where the $N$ most recently used pages are always a subset of the $N+1$ most recently used pages, guaranteeing immunity to Belady's Anomaly.

### Q3: Why did you choose Python's standard library `http.server` instead of Flask or FastAPI?
**Answer:** The project constraints strictly require a self-contained, reproducible university capstone that runs instantly in any bare Ubuntu 24.04 WSL2 environment without pip virtual-environment dependency hell. `http.server.ThreadingHTTPServer` delivers multi-threaded concurrency, strict loopback binding (`127.0.0.1`), sub-millisecond response latency, and zero attack surface from third-party framework vulnerabilities.

### Q4: In Round Robin CPU scheduling, how does the choice of time quantum affect system throughput?
**Answer:** If time quantum $q$ is extremely small, excessive context switching and dispatch latency dominate CPU cycles, collapsing effective throughput. If $q$ is arbitrarily large, Round Robin degenerates into FCFS, subjecting short I/O-bound processes to the convoy effect. The rule of thumb is setting $q$ such that $80\%$ of CPU bursts are shorter than $q$.

### Q5: How does the Banker's Algorithm differ from Deadlock Detection?
**Answer:** Banker's is a **deadlock avoidance** mechanism operating *a priori*: every process must declare its maximum demand upfront, and the OS preemptively blocks any resource grant that would transition the system into an unsafe state. In contrast, deadlock detection allows unconstrained allocation and runs a cycle-finding algorithm *ex post facto* to detect and recover from deadlocks after they occur.

### Q6: How does the front-end communicate with the backend, and is any simulation logic duplicated in JavaScript?
**Answer:** Communication is strictly RESTful JSON over HTTP. Zero simulation logic exists in JavaScript. The front-end is a pure visualizer: it transmits user input to `/api/*`, receives serialized dataclasses, and renders the coordinates using the Canvas 2D API. This enforces strict separation of concerns and guarantees that CLI and Web modes produce identical analytical results.

### Q7: How does your implementation prevent Directory Traversal attacks on static assets?
**Answer:** In `web/server.py`, incoming file paths are resolved using `Path.resolve()`, and strictly tested using `os.path.commonpath([STATIC_DIR, resolved_path]) == str(STATIC_DIR)`. Any request attempting to traverse outside `web/static/` via `../` immediately returns HTTP 404 or 403 Forbidden.

### Q8: What is the convoy effect in FCFS CPU scheduling?
**Answer:** The convoy effect occurs when multiple short, I/O-bound processes become queued behind a single long, CPU-bound process. The CPU remains busy while I/O devices sit idle, leading to sub-optimal hardware utilization and severely elevated average waiting times.

### Q9: Why must Matplotlib use the `Agg` backend in WSL2?
**Answer:** WSL2 runs primarily as a headless Linux server without an active X11 or Wayland display server by default. The standard GUI backends (`TkAgg`, `Qt5Agg`) fail when calling `plt.show()`. Configuring `matplotlib.use('Agg')` directs the renderer to generate raster graphics entirely in memory and save static PNG files directly to disk without requiring a display server.

### Q10: How are return jumps treated in C-SCAN and C-LOOK?
**Answer:** In physical disk drives, circular return jumps are high-speed seek operations without read/write head activation. Our simulator provides a dedicated `count_jump` configuration flag: when enabled (the textbook default), the jump distance is tallied into total seek distance; when disabled, the jump is recorded with `is_jump=True` and rendered as a distinct dashed amber segment on the Canvas without inflating productive head movement metrics.
