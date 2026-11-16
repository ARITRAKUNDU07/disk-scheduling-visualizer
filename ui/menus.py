"""Terminal CLI Menu and Text-Based Interface for OSRM.

Provides interactive ANSI-colored terminal navigation, tabular step visualizers,
and ASCII charts for all resource management subsystems. Calls the pure core algorithms
and catches validation exceptions gracefully.
"""

from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

from core.bash_bridge import run_script
from core.cpu_scheduling import CPU_ALGORITHMS, compare_all_cpu, run_cpu_simulation
from core.deadlock import evaluate_resource_request, evaluate_safety
from core.disk_scheduling import DISK_ALGORITHMS, compare_all_disk, run_disk_simulation
from core.logger import log_event
from core.page_replacement import PAGE_ALGORITHMS, compare_all_pages, demonstrate_belady, run_page_simulation
from core.report import generate_full_report, parse_sample_dataset
from core.validators import OSRMError

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ANSI Colors
CLR_RESET = "\033[0m"
CLR_BOLD = "\033[1m"
CLR_BLUE = "\033[94m"
CLR_CYAN = "\033[96m"
CLR_GREEN = "\033[92m"
CLR_YELLOW = "\033[93m"
CLR_RED = "\033[91m"
CLR_MAGENTA = "\033[95m"


def print_header(title: str) -> None:
    print(f"\n{CLR_BOLD}{CLR_BLUE}=================================================================={CLR_RESET}")
    print(f"{CLR_BOLD}{CLR_CYAN}  {title.center(62)}{CLR_RESET}")
    print(f"{CLR_BOLD}{CLR_BLUE}=================================================================={CLR_RESET}")


def get_input(prompt: str, default: Optional[str] = None) -> str:
    """Prompt user for input with EOF and Ctrl+C guards."""
    try:
        suffix = f" [{default}]" if default else ""
        raw = input(f"{CLR_BOLD}{prompt}{suffix}: {CLR_RESET}").strip()
        if not raw and default is not None:
            return default
        return raw
    except (KeyboardInterrupt, EOFError):
        print(f"\n{CLR_YELLOW}[Operation cancelled by user]{CLR_RESET}")
        return ""


# -----------------------------------------------------------------------------
# Disk Scheduling Menu
# -----------------------------------------------------------------------------

def menu_disk_scheduling() -> None:
    data_dir = PROJECT_ROOT / "data"
    sample = parse_sample_dataset(data_dir / "sample_disk.txt")
    requests = sample["requests"]
    head = sample["head"]
    size = sample["size"]
    direction = sample.get("direction", "left")
    count_jump = True
    ms_per_cyl = sample.get("ms_per_cyl", 1.0)

    while True:
        print_header("DISK SCHEDULING STUDIO")
        print(f"Current State: Head={head}, Cylinders=0..{size-1}, Dir={direction.upper()}, Rate={ms_per_cyl}ms")
        print(f"Queue ({len(requests)}): {requests}")
        print("------------------------------------------------------------------")
        print(" 1. Run Single Algorithm")
        print(" 2. Compare All 6 Algorithms (FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK)")
        print(" 3. Load Sample Benchmark Dataset (8 requests)")
        print(" 4. Load Large Benchmark Dataset (16 requests)")
        print(" 5. Manual Parameter Input")
        print(" 6. Toggle Return Jump Counting (Currently: " + ("ON" if count_jump else "OFF") + ")")
        print(" 0. Back to Main Menu")
        print("------------------------------------------------------------------")
        choice = get_input("Select Option", "1")

        if choice == "0":
            break
        elif choice == "1":
            print("\nAvailable Algorithms:")
            algs = list(DISK_ALGORITHMS.keys())
            for idx, a in enumerate(algs, 1):
                print(f"  {idx}. {a}")
            a_idx = get_input("Choose Algorithm [1-6]", "1")
            try:
                selected_alg = algs[int(a_idx) - 1]
                res = run_disk_simulation(
                    requests, head, size, direction, selected_alg, count_jump, ms_per_cyl
                )
                print(f"\n{CLR_BOLD}{CLR_GREEN}>>> RESULTS FOR {selected_alg} <<<{CLR_RESET}")
                print(f"Service Sequence : {' -> '.join(str(c) for c in res.sequence)}")
                print(f"Total Movement   : {res.total_movement} cylinders")
                print(f"Average Seek     : {res.avg_seek} cylinders")
                print(f"Seek Time Delay  : {res.seek_time_ms} ms")
                print("\nStep-by-step Trace:")
                for st in res.trace:
                    print(f"  {st}")
                log_event("cli_disk", f"Ran {selected_alg}: total={res.total_movement}")
            except (ValueError, IndexError, OSRMError) as exc:
                print(f"{CLR_RED}Error: {getattr(exc, 'message', str(exc))}{CLR_RESET}")
            get_input("\nPress Enter to continue")

        elif choice == "2":
            try:
                comp = compare_all_disk(requests, head, size, direction, count_jump, ms_per_cyl)
                print(f"\n{CLR_BOLD}{CLR_GREEN}=== DISK SCHEDULING COMPARISON MATRIX ==={CLR_RESET}")
                print(f"{'Algorithm':<10} | {'Movement (cyl)':<15} | {'Avg Seek':<10} | {'Seek Time':<12}")
                print("-" * 55)
                for alg, res in comp["results"].items():
                    is_best = alg in comp["best_algorithms"]
                    star = f" {CLR_GREEN}★ BEST{CLR_RESET}" if is_best else ""
                    print(f"{alg:<10} | {res['total_movement']:<15} | {res['avg_seek']:<10} | {res['seek_time_ms']} ms{star}")
                print("-" * 55)
                print(f"\n{CLR_CYAN}{comp['analysis']}{CLR_RESET}")
                log_event("cli_disk", f"Compared all: best={comp['best_algorithms']}")
            except OSRMError as exc:
                print(f"{CLR_RED}Error: {exc.message}{CLR_RESET}")
            get_input("\nPress Enter to continue")

        elif choice == "3":
            sample = parse_sample_dataset(data_dir / "sample_disk.txt")
            requests, head, size = sample["requests"], sample["head"], sample["size"]
            direction = sample.get("direction", "left")
            print(f"{CLR_GREEN}Loaded Sample Dataset.{CLR_RESET}")

        elif choice == "4":
            large = parse_sample_dataset(data_dir / "large_disk.txt")
            requests, head, size = large["requests"], large["head"], large["size"]
            direction = large.get("direction", "right")
            print(f"{CLR_GREEN}Loaded Large Dataset.{CLR_RESET}")

        elif choice == "5":
            q_str = get_input("Enter cylinder requests (comma separated)", ",".join(str(x) for x in requests))
            h_str = get_input("Enter initial head position", str(head))
            s_str = get_input("Enter disk size (total cylinders)", str(size))
            d_str = get_input("Enter initial direction (left/right)", direction)
            try:
                reqs = [int(x.strip()) for x in q_str.split(",") if x.strip()]
                head = int(h_str)
                size = int(s_str)
                direction = d_str.strip().lower()
                requests = reqs
                print(f"{CLR_GREEN}Parameters updated successfully.{CLR_RESET}")
            except ValueError:
                print(f"{CLR_RED}Invalid numeric entry. Parameters unchanged.{CLR_RESET}")

        elif choice == "6":
            count_jump = not count_jump
            print(f"Count return jump is now: {count_jump}")


# -----------------------------------------------------------------------------
# CPU Scheduling Menu
# -----------------------------------------------------------------------------

def menu_cpu_scheduling() -> None:
    data_dir = PROJECT_ROOT / "data"
    sample = parse_sample_dataset(data_dir / "sample_cpu.txt")
    processes = sample["processes"]
    quantum = sample.get("quantum", 4.0)

    while True:
        print_header("CPU SCHEDULING STUDIO")
        print(f"Processes ({len(processes)}):")
        print(f"{'PID':<6} | {'Arrival':<8} | {'Burst':<8} | {'Priority':<8}")
        print("-" * 36)
        for p in processes:
            print(f"{p['pid']:<6} | {p['arrival']:<8} | {p['burst']:<8} | {p.get('priority', 0):<8}")
        print(f"Time Quantum: {quantum}")
        print("------------------------------------------------------------------")
        print(" 1. Run Single Algorithm")
        print(" 2. Compare All Algorithms (FCFS, SJF, SRTF, Round Robin, Priority)")
        print(" 3. Load Sample Benchmark Dataset (P1, P2, P3)")
        print(" 4. Load Large Benchmark Dataset (12 processes)")
        print(" 5. Manual Process Input")
        print(" 0. Back to Main Menu")
        print("------------------------------------------------------------------")
        choice = get_input("Select Option", "1")

        if choice == "0":
            break
        elif choice == "1":
            algs = list(CPU_ALGORITHMS.keys())
            for idx, a in enumerate(algs, 1):
                print(f"  {idx}. {a}")
            a_idx = get_input("Choose Algorithm [1-5]", "1")
            try:
                selected_alg = algs[int(a_idx) - 1]
                res = run_cpu_simulation(processes, selected_alg, quantum)
                print(f"\n{CLR_BOLD}{CLR_GREEN}>>> RESULTS FOR {selected_alg} <<<{CLR_RESET}")
                print(f"Avg Waiting Time    : {res.avg_waiting}")
                print(f"Avg Turnaround Time : {res.avg_turnaround}")
                print(f"Avg Response Time   : {res.avg_response}")
                print(f"CPU Utilization     : {res.cpu_utilization}%")
                print(f"Throughput          : {res.throughput} proc/unit\n")
                print("Gantt Chart Timeline:")
                print(res.ascii_gantt)
                print(f"\n{'PID':<6} | {'Arrival':<8} | {'Burst':<8} | {'Completion':<11} | {'Turnaround':<11} | {'Waiting':<8}")
                print("-" * 65)
                for m in res.process_metrics:
                    print(f"{m.pid:<6} | {m.arrival:<8} | {m.burst:<8} | {m.completion:<11} | {m.turnaround:<11} | {m.waiting:<8}")
                log_event("cli_cpu", f"Ran {selected_alg}: avg_wt={res.avg_waiting}")
            except (ValueError, IndexError, OSRMError) as exc:
                print(f"{CLR_RED}Error: {getattr(exc, 'message', str(exc))}{CLR_RESET}")
            get_input("\nPress Enter to continue")

        elif choice == "2":
            try:
                comp = compare_all_cpu(processes, quantum)
                print(f"\n{CLR_BOLD}{CLR_GREEN}=== CPU SCHEDULING COMPARISON MATRIX ==={CLR_RESET}")
                print(f"{'Algorithm':<14} | {'Avg Waiting':<12} | {'Avg Turnaround':<15} | {'CPU Util':<10}")
                print("-" * 58)
                for alg, res in comp["results"].items():
                    is_best = alg in comp["best_algorithms"]
                    star = f" {CLR_GREEN}★ BEST{CLR_RESET}" if is_best else ""
                    print(f"{alg:<14} | {res['avg_waiting']:<12} | {res['avg_turnaround']:<15} | {res['cpu_utilization']}%{star}")
                print("-" * 58)
                print(f"\n{CLR_CYAN}{comp['analysis']}{CLR_RESET}")
                log_event("cli_cpu", f"Compared all: best={comp['best_algorithms']}")
            except OSRMError as exc:
                print(f"{CLR_RED}Error: {exc.message}{CLR_RESET}")
            get_input("\nPress Enter to continue")

        elif choice == "3":
            sample = parse_sample_dataset(data_dir / "sample_cpu.txt")
            processes = sample["processes"]
            quantum = sample.get("quantum", 4.0)
            print(f"{CLR_GREEN}Loaded Sample Dataset.{CLR_RESET}")

        elif choice == "4":
            large = parse_sample_dataset(data_dir / "large_cpu.txt")
            processes = large["processes"]
            quantum = large.get("quantum", 5.0)
            print(f"{CLR_GREEN}Loaded Large Dataset.{CLR_RESET}")

        elif choice == "5":
            n_str = get_input("Number of processes to enter", "3")
            try:
                num = int(n_str)
                new_procs = []
                for i in range(num):
                    line = get_input(f"Process {i+1} format (pid,arrival,burst,priority)", f"P{i+1},0,5,1")
                    parts = [p.strip() for p in line.split(",")]
                    new_procs.append({
                        "pid": parts[0],
                        "arrival": float(parts[1]),
                        "burst": float(parts[2]),
                        "priority": int(parts[3]) if len(parts) > 3 else 0
                    })
                q_str = get_input("Enter time quantum", "4.0")
                quantum = float(q_str)
                processes = new_procs
                print(f"{CLR_GREEN}Processes updated successfully.{CLR_RESET}")
            except (ValueError, IndexError):
                print(f"{CLR_RED}Invalid format entered. Resetting to defaults.{CLR_RESET}")


# -----------------------------------------------------------------------------
# Page Replacement Menu
# -----------------------------------------------------------------------------

def menu_page_replacement() -> None:
    data_dir = PROJECT_ROOT / "data"
    sample = parse_sample_dataset(data_dir / "sample_pages.txt")
    reference = sample["reference"]
    frames = sample["frames"]

    while True:
        print_header("PAGE REPLACEMENT STUDIO")
        print(f"Memory Frames: {frames}")
        print(f"Reference Stream ({len(reference)}): {reference}")
        print("------------------------------------------------------------------")
        print(" 1. Run Single Algorithm (FIFO, LRU, Optimal)")
        print(" 2. Compare All Algorithms")
        print(" 3. Belady's Anomaly Demonstration")
        print(" 4. Load Sample Benchmark Dataset (20 references)")
        print(" 5. Load Large Benchmark Dataset (30 references)")
        print(" 6. Manual Reference & Frames Input")
        print(" 0. Back to Main Menu")
        print("------------------------------------------------------------------")
        choice = get_input("Select Option", "1")

        if choice == "0":
            break
        elif choice == "1":
            algs = list(PAGE_ALGORITHMS.keys())
            for idx, a in enumerate(algs, 1):
                print(f"  {idx}. {a}")
            a_idx = get_input("Choose Algorithm [1-3]", "1")
            try:
                selected_alg = algs[int(a_idx) - 1]
                res = run_page_simulation(reference, frames, selected_alg)
                print(f"\n{CLR_BOLD}{CLR_GREEN}>>> RESULTS FOR {selected_alg} <<<{CLR_RESET}")
                print(f"Total Page Faults : {res.total_faults} ({res.fault_ratio*100:.1f}%)")
                print(f"Total Page Hits   : {res.total_hits} ({res.hit_ratio*100:.1f}%)\n")
                print("Step-by-Step Frame Matrix:")
                for st in res.steps:
                    stat = f"{CLR_RED}FAULT{CLR_RESET}" if st.is_fault else f"{CLR_GREEN}HIT  {CLR_RESET}"
                    rep = f" (Evicted {st.replaced_page})" if st.replaced_page is not None else ""
                    print(f"  Step {st.step:<2}: Access Page {st.page} -> {stat}{rep:<15} | Frames: {st.frames}")
                log_event("cli_pages", f"Ran {selected_alg}: faults={res.total_faults}")
            except (ValueError, IndexError, OSRMError) as exc:
                print(f"{CLR_RED}Error: {getattr(exc, 'message', str(exc))}{CLR_RESET}")
            get_input("\nPress Enter to continue")

        elif choice == "2":
            try:
                comp = compare_all_pages(reference, frames)
                print(f"\n{CLR_BOLD}{CLR_GREEN}=== PAGE REPLACEMENT COMPARISON MATRIX ==={CLR_RESET}")
                print(f"{'Algorithm':<10} | {'Faults':<8} | {'Hits':<8} | {'Fault Ratio':<12} | {'Hit Ratio':<10}")
                print("-" * 56)
                for alg, res in comp["results"].items():
                    is_best = alg in comp["best_algorithms"]
                    star = f" {CLR_GREEN}★ BEST{CLR_RESET}" if is_best else ""
                    print(f"{alg:<10} | {res['total_faults']:<8} | {res['total_hits']:<8} | {res['fault_ratio']*100:.1f}%       | {res['hit_ratio']*100:.1f}%{star}")
                print("-" * 56)
                print(f"\n{CLR_CYAN}{comp['analysis']}{CLR_RESET}")
                log_event("cli_pages", f"Compared all: best={comp['best_algorithms']}")
            except OSRMError as exc:
                print(f"{CLR_RED}Error: {exc.message}{CLR_RESET}")
            get_input("\nPress Enter to continue")

        elif choice == "3":
            bel = demonstrate_belady()
            print(f"\n{CLR_BOLD}{CLR_YELLOW}=== BELADY'S ANOMALY DEMONSTRATION ==={CLR_RESET}")
            print(f"Reference String : {bel['reference_string']}")
            print(f"3 Frames (FIFO)  : {CLR_GREEN}{bel['faults_3_frames']} Faults{CLR_RESET}")
            print(f"4 Frames (FIFO)  : {CLR_RED}{bel['faults_4_frames']} Faults{CLR_RESET} (Increase with MORE memory!)")
            print(f"\n{CLR_CYAN}{bel['explanation']}{CLR_RESET}")
            log_event("cli_pages", "Demonstrated Belady's Anomaly")
            get_input("\nPress Enter to continue")

        elif choice == "4":
            sample = parse_sample_dataset(data_dir / "sample_pages.txt")
            reference, frames = sample["reference"], sample["frames"]
            print(f"{CLR_GREEN}Loaded Sample Dataset.{CLR_RESET}")

        elif choice == "5":
            large = parse_sample_dataset(data_dir / "large_pages.txt")
            reference, frames = large["reference"], large["frames"]
            print(f"{CLR_GREEN}Loaded Large Dataset.{CLR_RESET}")

        elif choice == "6":
            ref_str = get_input("Enter reference string (comma separated)", ",".join(str(x) for x in reference))
            f_str = get_input("Enter number of page frames", str(frames))
            try:
                reference = [int(x.strip()) for x in ref_str.split(",") if x.strip()]
                frames = int(f_str)
                print(f"{CLR_GREEN}Parameters updated successfully.{CLR_RESET}")
            except ValueError:
                print(f"{CLR_RED}Invalid numeric entry.{CLR_RESET}")


# -----------------------------------------------------------------------------
# Deadlock (Banker's) Menu
# -----------------------------------------------------------------------------

def menu_deadlock() -> None:
    data_dir = PROJECT_ROOT / "data"
    sample = parse_sample_dataset(data_dir / "sample_banker.txt")
    available = sample["available"]
    allocation = sample["allocation"]
    max_matrix = sample["max"]

    while True:
        print_header("BANKER'S DEADLOCK AVOIDANCE STUDIO")
        print(f"Available Resources: {available}")
        print("Allocation Matrix:")
        for p, row in allocation.items():
            print(f"  {p}: {row}")
        print("Max Claim Matrix:")
        for p, row in max_matrix.items():
            print(f"  {p}: {row}")
        print("------------------------------------------------------------------")
        print(" 1. Run Safety State Evaluation")
        print(" 2. Test Dynamic Resource Request")
        print(" 3. Load Sample Benchmark Dataset (5 processes, 3 resources)")
        print(" 4. Load Large Benchmark Dataset (6 processes, 4 resources)")
        print(" 0. Back to Main Menu")
        print("------------------------------------------------------------------")
        choice = get_input("Select Option", "1")

        if choice == "0":
            break
        elif choice == "1":
            try:
                res = evaluate_safety(available, allocation, max_matrix)
                if res.is_safe:
                    print(f"\n{CLR_BOLD}{CLR_GREEN}>>> STATE VERIFICATION: SAFE <<<{CLR_RESET}")
                    print(f"Safe Execution Sequence: {' -> '.join(res.safe_sequence)}\n")
                    print("Step-by-step Execution Work Transitions:")
                    for s in res.steps:
                        print(f"  Step {s.step}: Process {s.pid} completes. Work before: {s.work_before} + Alloc {s.allocation} -> Work after: {s.work_after}")
                else:
                    print(f"\n{CLR_BOLD}{CLR_RED}>>> STATE VERIFICATION: UNSAFE <<<{CLR_RESET}")
                    print(f"Reason: {res.reason}")
                log_event("cli_deadlock", f"Safety checked: is_safe={res.is_safe}")
            except OSRMError as exc:
                print(f"{CLR_RED}Error: {exc.message}{CLR_RESET}")
            get_input("\nPress Enter to continue")

        elif choice == "2":
            pids = list(allocation.keys())
            pid_choice = get_input(f"Enter requesting PID ({', '.join(pids)})", pids[0])
            def_req = ",".join(str(min(1, available[i])) for i in range(len(available)))
            req_str = get_input(f"Enter requested resource vector (comma separated, length {len(available)})", def_req)
            try:
                req_vector = [int(x.strip()) for x in req_str.split(",") if x.strip()]
                req_eval = evaluate_resource_request(available, allocation, max_matrix, pid_choice, req_vector)
                if req_eval.granted:
                    print(f"\n{CLR_BOLD}{CLR_GREEN}>>> REQUEST VERDICT: GRANTED <<<{CLR_RESET}")
                    print(f"Rationale: {req_eval.reason}")
                else:
                    print(f"\n{CLR_BOLD}{CLR_RED}>>> REQUEST VERDICT: DENIED <<<{CLR_RESET}")
                    print(f"Rationale: {req_eval.reason}")
                log_event("cli_deadlock", f"Request checked for {pid_choice}: granted={req_eval.granted}")
            except (ValueError, OSRMError) as exc:
                print(f"{CLR_RED}Error: {getattr(exc, 'message', str(exc))}{CLR_RESET}")
            get_input("\nPress Enter to continue")

        elif choice == "3":
            sample = parse_sample_dataset(data_dir / "sample_banker.txt")
            available, allocation, max_matrix = sample["available"], sample["allocation"], sample["max"]
            print(f"{CLR_GREEN}Loaded Sample Dataset.{CLR_RESET}")

        elif choice == "4":
            large = parse_sample_dataset(data_dir / "large_banker.txt")
            available, allocation, max_matrix = large["available"], large["allocation"], large["max"]
            print(f"{CLR_GREEN}Loaded Large Dataset.{CLR_RESET}")


# -----------------------------------------------------------------------------
# Main CLI Menu Loop
# -----------------------------------------------------------------------------

def run_cli_menu() -> None:
    """Main interactive terminal loop."""
    log_event("cli", "Starting OSRM Terminal Interface")

    while True:
        print_header("OS RESOURCE MANAGER SIMULATOR (OSRM)")
        print(" Operating Systems Laboratory (ENSC-351), B.Tech Semester V")
        print("------------------------------------------------------------------")
        print(" 1. CPU Scheduling (FCFS, SJF, SRTF, Round Robin, Priority)")
        print(" 2. Disk Scheduling (FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK)")
        print(" 3. Page Replacement (FIFO, LRU, Optimal, Belady's Anomaly)")
        print(" 4. Deadlock Handling (Banker's Safety & Resource Request)")
        print(" 5. Full Analysis on Sample Datasets (Consolidated Overview)")
        print(" 6. Generate Academic Markdown Report (with Matplotlib PNGs)")
        print(" 7. Activity Log Summary (Bash Script)")
        print(" 8. System Diagnostics & Host Telemetry (Bash Script)")
        print(" 9. Run Verification Test Suite (Bash Script)")
        print(" 10. Launch Web Dashboard (Browser Interface)")
        print(" 0. Exit")
        print("------------------------------------------------------------------")
        choice = get_input("Enter choice [0-10]", "1")

        if choice in ("0", "exit", "quit", "q"):
            print(f"\n{CLR_GREEN}Thank you for using OSRM Simulator. Exiting.{CLR_RESET}")
            log_event("cli", "OSRM Terminal Menu Exited")
            break

        elif choice == "1":
            menu_cpu_scheduling()
        elif choice == "2":
            menu_disk_scheduling()
        elif choice == "3":
            menu_page_replacement()
        elif choice == "4":
            menu_deadlock()
        elif choice == "5":
            print_header("FULL SUBSYSTEM ANALYSIS (SAMPLE BENCHMARKS)")
            from web.api import get_summary
            summ = get_summary()
            print(f"{CLR_BOLD}1. DISK:{CLR_RESET} Best={summ['disk']['best_algorithm']} ({summ['disk']['headline_value']} cyl) | {summ['disk']['caption']}")
            print(f"{CLR_BOLD}2. CPU :{CLR_RESET} Best={summ['cpu']['best_algorithm']} (Avg Waiting: {summ['cpu']['headline_value']}) | {summ['cpu']['caption']}")
            print(f"{CLR_BOLD}3. PAGE:{CLR_RESET} Best={summ['pages']['best_algorithm']} ({summ['pages']['headline_value']} faults) | {summ['pages']['caption']}")
            print(f"{CLR_BOLD}4. DEADLOCK:{CLR_RESET} System is {summ['deadlock']['headline_value']} | {summ['deadlock']['caption']}")
            get_input("\nPress Enter to return")

        elif choice == "6":
            scale = get_input("Select dataset scale ('sample' or 'large')", "large").strip().lower()
            if scale not in ("sample", "large"):
                scale = "large"
            print(f"Generating full report using '{scale}' dataset...")
            try:
                path, _ = generate_full_report(scale)
                print(f"{CLR_GREEN}Report compiled successfully!{CLR_RESET}")
                print(f"File location: {path}")
            except Exception as exc:
                print(f"{CLR_RED}Report generation error: {exc}{CLR_RESET}")
            get_input("\nPress Enter to return")

        elif choice == "7":
            print_header("ACTIVITY AUDIT LOG SUMMARY")
            res = run_script("collect_logs.sh")
            print(res["stdout"])
            get_input("Press Enter to return")

        elif choice == "8":
            print_header("HOST SYSTEM TELEMETRY (REAL LINUX METRICS)")
            res = run_script("sysinfo.sh")
            print(res["stdout"])
            get_input("Press Enter to return")

        elif choice == "9":
            print_header("RUNNING AUTOMATED VERIFICATION TEST SUITE")
            res = run_script("run_tests.sh", timeout_sec=60)
            print(res["stdout"])
            get_input("Press Enter to return")

        elif choice == "10":
            from web.server import run_web_server
            port_str = get_input("Enter Web Server Port", "8080")
            try:
                port = int(port_str)
                run_web_server(port=port)
            except ValueError:
                print(f"{CLR_RED}Invalid port number.{CLR_RESET}")

        else:
            print(f"{CLR_YELLOW}Invalid choice '{choice}'. Please enter a number between 0 and 10.{CLR_RESET}")
