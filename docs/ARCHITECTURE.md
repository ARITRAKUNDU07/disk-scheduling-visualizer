# System Architecture & Technical Specification

**OS Resource Manager Simulator (`osrm`)**  
**Course:** Operating Systems Laboratory (ENSC-351), B.Tech Semester V  
**Target Platform:** Ubuntu 24.04 LTS (WSL2 / Native Linux), Python 3.10+, Bash 5+

---

## 1. High-Level Architectural Diagram

```
+-----------------------------------------------------------------------------------+
|                                 USER INTERFACES                                   |
|                                                                                   |
|   +------------------------------------+   +----------------------------------+   |
|   |          Web Dashboard             |   |        Interactive Terminal      |   |
|   |  - Vanilla HTML5 / CSS3 / ES-Mod   |   |        - Pure Python curses/ANSI |   |
|   |  - Peak Glow 540:696 Canvas UI     |   |        - Interactive Submenus    |   |
|   |  - Real-time Glow & Trajectory     |   |        - Formatted ASCII Tables  |   |
|   |  - Zero client-side computation    |   |        - Direct Core Invocation  |   |
|   +-----------------+------------------+   +-----------------+----------------+   |
+---------------------|----------------------------------------|--------------------+
                      | JSON over HTTP (port 8080/opt)         | Direct Python Call
                      v                                        |
+-------------------------------------------------+            |
|                  WEB LAYER                      |            |
|  - web/server.py: ThreadingHTTPServer (stdlib)  |            |
|  - web/api.py: REST Route Dispatcher & Security |            |
|  - Strict path traversal guard & no-store cache |            |
|  - Static asset streaming with MIME resolution  |            |
+---------------------+---------------------------+            |
                      |                                        |
                      +-------------------+--------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                                CORE SUBSYSTEM                                     |
|                                                                                   |
|  +------------------------+  +------------------------+  +---------------------+  |
|  |   Disk Scheduling      |  |     CPU Scheduling     |  |  Page Replacement   |  |
|  | - FCFS, SSTF, SCAN,    |  | - FCFS, SJF (NP),      |  | - FIFO, LRU,        |  |
|  |   C-SCAN, LOOK, C-LOOK |  |   SRTF (Preemptive),   |  |   Optimal (MIN)     |  |
|  | - Return jump tracking |  |   Round Robin, Priority|  | - Belady's Anomaly  |  |
|  +------------------------+  +------------------------+  +---------------------+  |
|  +------------------------+  +------------------------+  +---------------------+  |
|  |   Deadlock Avoidance   |  |     Input Validation   |  |  Metrics Engine     |  |
|  | - Banker's Safety      |  | - Bounds, types, empty |  | - Turnaround, wait, |  |
|  | - Resource Request     |  | - Custom exceptions    |  |   fault ratio, seek |  |
|  +------------------------+  +------------------------+  +---------------------+  |
|  +------------------------+  +------------------------+  +---------------------+  |
|  |   Structured Logging   |  |     Report Builder     |  |  Serialization      |  |
|  | - logs/activity.log    |  | - Markdown Generator   |  | - Dataclass->Dict   |  |
|  | - Standard audit trail |  | - Matplotlib Agg PNGs  |  | - Dynamic metadata  |  |
|  +------------------------+  +------------------------+  +---------------------+  |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                             BASH AUTOMATION BRIDGE                                |
|  - core/bash_bridge.py: Subprocess isolation, strict argument sanitization        |
|  - Whitelisted scripts: sysinfo.sh, collect_logs.sh, run_tests.sh, serve.sh       |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                            OPERATING SYSTEM & UTILITIES                           |
|  - GNU Linux Kernel / WSL2 Subsystem                                              |
|  - `uname`, `free`, `df`, `lscpu`, `ps aux`, `awk`, `grep`                        |
|  - Local File System: data/, logs/, output/charts, output/traces, output/reports  |
+-----------------------------------------------------------------------------------+
```

---

## 2. Layered Responsibilities

| Layer | Files | Key Responsibilities |
| :--- | :--- | :--- |
| **Presentation (Web)** | `web/static/` | Pure rendering of JSON structures. Contains zero simulation logic. Glow Card Canvas rendering, interactive Gantt blocks, responsive step tables, and toast notifications. |
| **Presentation (CLI)** | `ui/menus.py` | Terminal-based ANSI color menu with interactive submenus, paginated data loading, tabular ASCII output, and real-time execution. |
| **API & Routing** | `web/server.py`, `web/api.py` | HTTP verb dispatch, JSON payload decoding (capped at 1 MB), strict origin binding (`127.0.0.1`), security header injection, path sanitization. |
| **Core Algorithms** | `core/*_scheduling.py`, `core/page_replacement.py`, `core/deadlock.py` | Deterministic, pure mathematical implementations of operating system resource allocation models without I/O side effects. |
| **Support Infrastructure** | `core/validators.py`, `core/logger.py`, `core/serialization.py` | Multi-stage defensive input checking, audit-trail logging with millisecond timestamps, schema validation, and dataclass transformation. |
| **Analytics & Reporting** | `core/report.py`, `ui/charts.py`, `core/metrics.py` | Aggregates multi-algorithm runs into analytical markdown summaries and renders headless Matplotlib static PNG figures. |
| **OS Automation** | `core/bash_bridge.py`, `*.sh` | Secure orchestration of host commands for system telemetry, log reduction, test discovery, and server bootstrapping. |

---

## 3. Data Structures & Dataclass Contract

All algorithm routines return immutable dataclasses decorated with serialization helpers (`to_dict()`) ensuring 100% JSON safety:

```python
# Disk Scheduling Result
@dataclass
class DiskStep:
    step: int
    from_cyl: int
    to_cyl: int
    distance: int
    cumulative: int
    is_jump: bool

@dataclass
class DiskResult:
    algorithm: str
    sequence: list[int]
    total_movement: int
    avg_seek: float
    seek_time_ms: float
    jump_index: int | None
    trace: list[str]
    steps: list[DiskStep]

# CPU Scheduling Result
@dataclass
class GanttSegment:
    pid: str
    start: float
    end: float

@dataclass
class ProcessMetrics:
    pid: str
    arrival: float
    burst: float
    priority: int
    completion: float
    turnaround: float
    waiting: float
    response: float

@dataclass
class CPUResult:
    algorithm: str
    quantum: float | None
    gantt: list[GanttSegment]
    process_metrics: list[ProcessMetrics]
    avg_turnaround: float
    avg_waiting: float
    avg_response: float
    cpu_utilization: float
    throughput: float

# Page Replacement Result
@dataclass
class PageStep:
    step: int
    page: int
    frames: list[int | None]
    is_fault: bool
    replaced_page: int | None

@dataclass
class PageResult:
    algorithm: str
    frames_count: int
    reference_string: list[int]
    steps: list[PageStep]
    total_faults: int
    total_hits: int
    fault_ratio: float
    hit_ratio: float

# Banker's Deadlock Result
@dataclass
class SafetyResult:
    is_safe: bool
    safe_sequence: list[str]
    steps: list[dict[str, any]]
    need_matrix: dict[str, list[int]]
    available_history: list[list[int]]
    reason: str

@dataclass
class RequestResult:
    granted: bool
    reason: str
    safety_after_allocation: SafetyResult | None
```

---

## 4. REST API Endpoint Specification

All endpoints communicate using standard `application/json; charset=utf-8` and require `POST` or `GET` verbs:

| Method | Endpoint | Payload Description | Success (200) Response |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/meta` | None | Module metadata, algorithm registries, parameter boundaries. |
| `GET` | `/api/samples/<module>` | URL query or path parameter (`cpu`, `disk`, `pages`, `banker`) | JSON object holding parsed `sample` and `large` benchmark data. |
| `POST` | `/api/disk/run` | `{requests, head, size, direction, algorithm, count_jump, ms_per_cyl}` | `DiskResult` JSON object. |
| `POST` | `/api/disk/compare` | `{requests, head, size, direction, count_jump, ms_per_cyl}` | Comparison matrix of 6 algorithms, best algorithm identifier, analytical notes. |
| `POST` | `/api/cpu/run` | `{processes: [{pid, arrival, burst, priority}], algorithm, quantum}` | `CPUResult` JSON object. |
| `POST` | `/api/cpu/compare` | `{processes: [{pid, arrival, burst, priority}], quantum}` | Multi-algorithm comparison object, Gantt traces, efficiency comparison. |
| `POST` | `/api/pages/run` | `{reference: [int], frames: int, algorithm: str}` | `PageResult` step matrix, hit/fault breakdown. |
| `POST` | `/api/pages/compare` | `{reference: [int], frames: int}` | Comparison of FIFO, LRU, and Optimal with hit/fault ratios. |
| `GET` | `/api/pages/belady` | None | Verified Belady's Anomaly execution comparing 3 frames vs 4 frames under FIFO. |
| `POST` | `/api/deadlock/safety` | `{available: [int], allocation: dict, max: dict}` | `SafetyResult` verification object and work step breakdown. |
| `POST` | `/api/deadlock/request` | `{available: [int], allocation: dict, max: dict, pid: str, request: [int]}` | `RequestResult` evaluation indicating granted status and safe sequence. |
| `GET` | `/api/summary` | None | Optimal algorithm statistics per subsystem on standard benchmark data. |
| `POST` | `/api/report/generate` | Optional dataset size (`sample` or `large`) | File path to newly created markdown report and raw markdown content. |
| `GET` | `/api/logs/summary` | None | Aggregated log counts by severity and module from `collect_logs.sh`. |
| `GET` | `/api/sysinfo` | None | Live host information retrieved safely via `sysinfo.sh`. |
| `POST` | `/api/tests/run` | None | Standard test discovery output and PASS/FAIL summary from `run_tests.sh`. |

---

## 5. Architectural Design Principles

1. **Standard Library Web Server Only**:
   The web server uses Python's standard `http.server.ThreadingHTTPServer`. This completely removes heavy external dependencies like Flask, Django, or FastAPI, making the project run instantly in any standard Python 3.10+ Linux/WSL2 environment without complex virtual environment setups.

2. **Decoupled Architecture with Single Source of Truth**:
   Both the interactive terminal menu (`ui/menus.py`) and the web front-end consume the exact same underlying functions in `core/`. Algorithmic calculation never differs between presentation layers.

3. **Pure Front-End Rendering**:
   The browser executes zero resource management algorithms. It functions strictly as a high-fidelity visualizer of the backend's verified JSON responses. This maintains strict separation of concerns and guarantees that all academic benchmarks remain centralized and testable.

4. **Security by Default**:
   - HTTP listener binds exclusively to loopback interface `127.0.0.1`.
   - Inbound request bodies are strictly checked and capped at 1,048,576 bytes (1 MB) to prevent memory saturation attacks.
   - All static file requests are verified against canonical base paths using `os.path.commonpath` to eliminate directory traversal (`../`).
   - Security headers injected on all HTTP responses: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Cache-Control: no-store` on API routes.
