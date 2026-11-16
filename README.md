# OS Resource Manager Simulator (`osrm`)

**Course:** Operating Systems Laboratory (ENSC-351), B.Tech Semester V  
**Target Platform:** Ubuntu 24.04 LTS on WSL2, Bash 5+, Python 3.10+, VS Code  
**Project Classification:** Flagship Integrated Capstone Application  
**Primary Theoretical Reference:** Silberschatz, Galvin, Gagne, *Operating System Concepts*, 10th Edition  

---

## 1. Project Overview & Identity

The **OS Resource Manager Simulator (`osrm`)** is an integrated, dual-interface software engineering application designed to model, analyze, and benchmark the four core resource-management pillars of modern operating systems:

1. **Disk Head Scheduling:** FCFS, SSTF, SCAN, C-SCAN, LOOK, and C-LOOK with return jump tracking.
2. **CPU Scheduling:** FCFS, Shortest Job First (Non-Preemptive), Shortest Remaining Time First (Preemptive), Round Robin (configurable quantum), and Non-Preemptive Priority.
3. **Virtual Memory Page Replacement:** FIFO, Least Recently Used (LRU), Belady's Optimal (MIN), and an empirical demonstration of Belady's Anomaly.
4. **Deadlock Handling:** Dijkstra's Banker's Algorithm featuring safety state discovery and dynamic resource request evaluation with rollback.

### Dual-Interface Architecture:
Unlike typical disconnected academic scripts, OSRM operates as **one integrated application**:
- **Peak Glow Web Dashboard:** An ultra-high fidelity cybernetic analytics interface rendered with vanilla HTML5, CSS custom properties, and the Canvas 2D API. Features zero-framework offline rendering, real-time Gaussian potential field synthesis, halo light spill, and comet-drawn vector trajectories.
- **Interactive Terminal CLI:** A robust, ANSI-colored terminal menu system with tabular ASCII traces and submenus, invoking the exact same core algorithms and validation layers.

---

## 2. Key Features

- **Strict Standard Library Web Server:** Built on `http.server.ThreadingHTTPServer`. Zero external web frameworks (no Flask, Django, or FastAPI), ensuring instant execution on any clean Linux system.
- **Pure Front-End Visualizer:** The browser contains zero algorithmic logic; it exclusively renders JSON returned by the Python API.
- **100% Offline Capable:** Zero external CDN links, zero Google Fonts, and zero npm/node packages.
- **Analytical Precision:** Verified against exact textbook benchmarks (e.g., Disk benchmarks: 640 / 236 / 236 / 208 / 382 / 322 cylinders).
- **Bash Automation Bridge:** Secure subprocess wrapper orchestrating host scripts (`sysinfo.sh`, `collect_logs.sh`, `run_tests.sh`) to provide host-simulator telemetry parity.
- **Automated Verification:** 55 comprehensive unit and API tests executed via `run_tests.sh`.
- **Publication-Ready Reports:** Automatic generation of Markdown reports with Matplotlib static PNG figures (`output/reports/`).

---

## 3. Environment & Requirements

- **Operating System:** Ubuntu 24.04 LTS (Native Linux or WSL2 on Windows 10/11)
- **Interpreter:** Python 3.10 or higher (standard library)
- **Shell:** GNU Bash 5.0+
- **Python Libraries:**
  - `matplotlib` (used with headless `Agg` backend for static report figures)
  - `numpy` (automatically installed as a matplotlib dependency)
- **Browser:** Any modern Chromium, Firefox, or Edge browser (for Web mode)

---

## 4. Setup & Installation (Ubuntu 24.04 WSL2)

Open your WSL2 terminal (`wsl` or Ubuntu terminal) and run:

```bash
# 1. Clone repository and navigate to root directory
git clone https://github.com/your-username/osrm.git
cd osrm

# 2. Grant executable permissions to all shell automation scripts
chmod +x *.sh

# 3. Run automated setup script
./setup.sh
```

`setup.sh` will:
- Verify directory structures (`logs/`, `output/charts/`, `output/traces/`, `output/reports/`).
- Verify Python 3 interpreter availability.
- Install `matplotlib` (using `--break-system-packages` if required under Ubuntu 24.04).

---

## 5. How to Run

OSRM provides a universal launcher `./run.sh` that supports both interactive mode selection and direct flags.

### 5.1 Launching the Web Dashboard (Recommended)

```bash
./run.sh web
```
*Or directly via Python:*
```bash
python3 main.py --web --port 8080
```

The server binds strictly to loopback interface `127.0.0.1:8080`.
The launcher attempts to open your Windows default browser automatically via `wslview` or `explorer.exe`.  
You can also open your Windows browser manually and navigate to:
```
http://127.0.0.1:8080
```

### 5.2 Launching the Terminal CLI Menu

```bash
./run.sh cli
```
*Or directly via Python:*
```bash
python3 main.py --cli
```

### 5.3 Interactive Launcher Menu

```bash
./run.sh
```
Prompts the user to select either Web Dashboard, Terminal Menu, or Test Suite.

---

## 6. Directory Structure

```
osrm/
├── main.py                      # Primary application entry point (--cli, --web, --port N)
├── run.sh                       # Universal bash launcher (./run.sh web|cli|test)
├── setup.sh                     # Automated folder setup & dependency installation
├── serve.sh                     # Web server launcher with automatic browser opening
├── run_tests.sh                 # Test discovery runner; tees output to output/test_results.txt
├── collect_logs.sh              # Bash log summarizer (counts by module/severity, recent events)
├── sysinfo.sh                   # Real Linux host telemetry (uname, free, df, lscpu, ps)
├── README.md                    # Root project documentation
├── core/                        # Centralized simulation engine (pure Python 3)
│   ├── __init__.py
│   ├── cpu_scheduling.py        # FCFS, SJF, SRTF, Round Robin, Priority
│   ├── disk_scheduling.py       # FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK
│   ├── page_replacement.py      # FIFO, LRU, Optimal, Belady's Anomaly
│   ├── deadlock.py              # Banker's Safety & Resource Request algorithms
│   ├── metrics.py               # Analytical metrics calculation & comparison text
│   ├── validators.py            # Defensive validators & custom domain exceptions
│   ├── logger.py                # Centralized audit logger (logs/activity.log)
│   ├── bash_bridge.py           # Secure subprocess wrapper for shell scripts
│   ├── report.py                # Academic Markdown report builder & trace recorder
│   └── serialization.py         # Dataclass to JSON-safe dictionary helpers
├── ui/                          # Presentation helpers
│   ├── __init__.py
│   ├── menus.py                 # Interactive terminal ANSI color submenus
│   └── charts.py                # Headless Matplotlib PNG plot generation (Agg backend)
├── web/                         # Local Web Application
│   ├── __init__.py
│   ├── server.py                # ThreadingHTTPServer, path guard, 1 MB limit
│   ├── api.py                   # REST routing table mapping /api/* to core/
│   └── static/                  # Static front-end assets (100% offline)
│       ├── index.html           # Single-page application shell
│       ├── css/
│       │   └── theme.css        # Peak Glow design tokens & glass styles
│       └── js/
│           ├── app.js           # ES Module router, state, & noise grain generator
│           ├── api.js           # Asynchronous fetch wrappers & toast notifications
│           ├── glowcard.js      # Reusable 540:696 Canvas Glow Card component
│           ├── charts.js        # Canvas Gantt, Classical Disk, & Frame Matrix
│           ├── ui.js            # Segmented controls, drawer, count-up helpers
│           └── views/           # Modular view controllers
│               ├── dashboard.js # Executive overview with 4 Glow Cards
│               ├── disk.js      # Flagship Disk Scheduling Studio
│               ├── cpu.js       # CPU Scheduling Studio & Gantt visualizer
│               ├── pages.js     # Page Replacement Studio & Belady sandbox
│               ├── deadlock.js  # Banker's Deadlock Avoidance Studio
│               └── tools.js     # Diagnostics, log auditor, & report previews
├── data/                        # Benchmark workload datasets
│   ├── sample_disk.txt          # Silberschatz 8-request benchmark
│   ├── large_disk.txt           # 16-request multi-region workload
│   ├── sample_cpu.txt           # Silberschatz 3-process benchmark
│   ├── large_cpu.txt            # 12-process mixed workload
│   ├── sample_pages.txt         # Silberschatz 20-reference stream
│   ├── large_pages.txt          # 30-reference stream
│   ├── sample_banker.txt        # Silberschatz 5x3 allocation matrices
│   └── large_banker.txt         # 6x4 allocation matrices
├── tests/                       # Comprehensive verification suite
│   ├── test_disk.py             # Disk scheduling assertions
│   ├── test_cpu.py              # CPU scheduling assertions
│   ├── test_pages.py            # Page replacement & Belady assertions
│   ├── test_deadlock.py         # Banker's safety & request assertions
│   ├── test_validators.py       # Defensive bounds & type checks
│   └── test_api.py              # Live multi-threaded HTTP endpoint assertions
├── logs/
│   └── activity.log             # Structured audit trail
├── output/
│   ├── charts/                  # Generated Matplotlib PNG plots
│   ├── traces/                  # Serialized execution step traces
│   └── reports/                 # Markdown laboratory reports
├── docs/
│   ├── README.md                # Documentation mirror
│   ├── ARCHITECTURE.md          # ASCII diagrams & design principles
│   ├── UI_DESIGN.md             # Peak Glow UI design specification
│   ├── REPORT.md                # Academic laboratory report & theory
│   ├── TEST_CASES.md            # Empirical test case matrix (55 tests)
│   └── DEMO_SCRIPT.md           # 5-minute presentation script & 10 viva Q&A
└── screenshots/
    └── README.md                # Demonstration screenshot checklist
```

---

## 7. Mandatory Verification Values

All algorithms have been mathematically asserted against standard OS literature:

### 7.1 Disk Head Scheduling
**Input:** Queue = `[98, 183, 37, 122, 14, 124, 65, 67]`, Head = `53`, Disk = `0..199`
- **FCFS:** 640 cylinders
- **SSTF:** 236 cylinders
- **SCAN (direction: left):** 236 cylinders (reaches 0 before reversing)
- **LOOK (direction: left):** 208 cylinders (reverses at lowest request 14)
- **C-SCAN (direction: right, return jump counted):** 382 cylinders
- **C-LOOK (direction: right, return jump counted):** 322 cylinders

### 7.2 CPU Scheduling
**Input:** $P_1(0, 24), P_2(0, 3), P_3(0, 3)$
- **FCFS Average Waiting Time:** 17.00 time units
- **SJF (Non-Preemptive) Average Waiting Time:** 3.00 time units
- **Round Robin (Quantum = 4) Average Waiting Time:** 5.67 time units

### 7.3 Page Replacement
**Input:** Reference String = `[7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]`, Frames = `3`
- **FIFO:** 15 page faults (75.0% fault ratio)
- **LRU:** 12 page faults (60.0% fault ratio)
- **Optimal (MIN):** 9 page faults (45.0% fault ratio)
- **Belady's Anomaly:** String `[1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]` -> 3 Frames = 9 faults; 4 Frames = 10 faults.

### 7.4 Banker's Deadlock Avoidance
**Input:** Available = `[3, 3, 2]`, 5 processes, 3 resource types (Silberschatz)
- **Initial State:** Verified **SAFE**
- **Safe Execution Order:** `P1 -> P3 -> P4 -> P0 -> P2`
- **Request Test 1:** $P_1$ requests `[1, 0, 2]` -> **GRANTED**
- **Request Test 2:** $P_0$ requests `[0, 2, 0]` -> **GRANTED**

---

## 8. Verification & Test Execution

Run the complete automated verification test suite:

```bash
./run_tests.sh
```

All 55 assertions execute across unit tests and live multi-threaded API endpoints, logging results to `output/test_results.txt`:

```
Ran 55 tests in 0.758s
OK
==================================================================
                 >>> VERIFICATION STATUS: PASS <<<                
All unit and API verification assertions succeeded.
==================================================================
```

---

## 9. Design Decisions & Engineering Tradeoffs

1. **Why Python Standard Library for the Web Server?**  
   Academic grading environments frequently face dependency version mismatches. By relying exclusively on Python standard library modules (`http.server`, `json`, `threading`, `urllib`), OSRM guarantees immediate zero-configuration portability on any Linux distribution.
2. **Why Vanilla JavaScript ES Modules without React/Node.js?**  
   Modern ES modules provide native component isolation and asynchronous imports directly in modern browsers. Eliminating Node.js and build steps (webpack, Vite) ensures that the front-end remains lightweight, 100% offline, and instantly inspectable.
3. **Defensive Subprocess Execution in Bash Bridge:**  
   `core/bash_bridge.py` never uses `shell=True` with dynamic user parameters. It enforces strict whitelist matching against `ALLOWED_SCRIPTS`, sanitizes paths, and applies execution timeouts.

---

## 10. Authors & Course Information

- **Course:** Operating Systems Laboratory (ENSC-351)
- **Degree:** Bachelor of Technology (B.Tech), Semester V
- **Project Name:** OS Resource Manager Simulator (`osrm`)
- **License:** Open Academic License (MIT Compatible)
#   d i s k - s c h e d u l i n g - v i s u a l i z e r  
 