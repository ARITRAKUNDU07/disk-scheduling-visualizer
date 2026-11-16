# OSRM Demonstration Screenshots & Verification Checklist

This directory contains the checklist and reference metadata for capturing documentation screenshots across the terminal CLI and local web dashboard.

---

## Required Screenshot Capture Checklist

| Index | Target Screen / Component | Description | Mode | File Target |
| :---: | :--- | :--- | :---: | :--- |
| [ ] 01 | **Dashboard Overview** | Executive overview with 4 Peak Glow cards (Disk, CPU, Pages, Deadlock) | Web | `screenshots/01_dashboard.png` |
| [ ] 02 | **Disk Scheduling Studio** | Flagship view showing console, large Canvas Glow Card, and live step trace table | Web | `screenshots/02_disk_studio.png` |
| [ ] 03 | **Disk Compare All Row** | Row of 6 compact Glow Cards (FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK) with winner badge | Web | `screenshots/03_disk_compare.png` |
| [ ] 04 | **Classical Disk Space-Time** | Collapsible space-time diagram (x = Cylinder, y = Time ↓) | Web | `screenshots/04_disk_spacetime.png` |
| [ ] 05 | **CPU Scheduling & Gantt** | Process editor table, latency matrix, and Canvas Gantt chart with time ticks | Web | `screenshots/05_cpu_gantt.png` |
| [ ] 06 | **CPU Multi-Algorithm Compare** | Comparative row of 5 CPU algorithms highlighting SJF minimal waiting time | Web | `screenshots/06_cpu_compare.png` |
| [ ] 07 | **Page Frame Residency Timeline** | Memory allocation timeline with emerald Hit cells and soft rose Fault cells | Web | `screenshots/07_page_matrix.png` |
| [ ] 08 | **Belady's Anomaly Sandbox** | Side-by-side comparison of 3 frames (9 faults) vs 4 frames (10 faults) | Web | `screenshots/08_belady_anomaly.png` |
| [ ] 09 | **Banker's Safe State Sequence** | Allocation/Max matrices, Need matrix, and animated safe execution sequence chips | Web | `screenshots/09_banker_safe.png` |
| [ ] 10 | **Banker's Resource Request Sandbox**| Ad-hoc dynamic resource request showing GRANTED verdict with safe sequence | Web | `screenshots/10_banker_request.png` |
| [ ] 11 | **Banker's Unsafe State Alert** | Rose-accented Glow Card and warning banner indicating potential deadlock hazard | Web | `screenshots/11_banker_unsafe.png` |
| [ ] 12 | **Defensive Error Toast** | Glass error toast notification triggered by boundary input validation | Web | `screenshots/12_error_toast.png` |
| [ ] 13 | **Interactive Terminal CLI** | ANSI color main menu with interactive numbered submenus | CLI | `screenshots/13_cli_menu.png` |
| [ ] 14 | **CLI Tabular Execution Output** | Disk or CPU step-by-step trace formatted cleanly in ASCII table | CLI | `screenshots/14_cli_trace.png` |
| [ ] 15 | **Automated Test Suite Execution** | Terminal output showing `run_tests.sh` passing all 55 assertions | CLI/Bash | `screenshots/15_test_run.png` |
| [ ] 16 | **Host Telemetry & Log Summary** | Side-by-side output of `sysinfo.sh` and `collect_logs.sh` in the tools view | Web/CLI | `screenshots/16_diagnostics.png` |

---

## How to Capture on WSL2 / Ubuntu
1. Launch Web Dashboard:
   ```bash
   ./run.sh web
   ```
2. Navigate to `http://127.0.0.1:8080` in your Windows browser.
3. Use Windows Snipping Tool (`Win + Shift + S`) or browser developer tools screenshot utility (`Ctrl + Shift + P` -> `Capture full size screenshot`).
4. Save images directly into this `screenshots/` directory matching the filenames above.
