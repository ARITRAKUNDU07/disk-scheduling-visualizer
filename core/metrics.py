"""Analytical Metrics Calculation and Performance Analysis Engine for OSRM.

Provides standardized formulas for response times, turnaround ratios, hit rates,
seek delays, and automated comparative narrative generation across algorithms.
"""

from typing import Any, Dict, List, Optional, Tuple


def calculate_cpu_metrics(
    processes: List[Dict[str, Any]],
    completion_times: Dict[str, float],
    first_response_times: Dict[str, float],
    total_time: float,
) -> Tuple[List[Dict[str, Any]], float, float, float, float, float]:
    """Compute per-process and aggregate CPU scheduling performance indicators.

    Returns:
        (process_metrics, avg_turnaround, avg_waiting, avg_response, cpu_utilization, throughput)
    """
    total_turnaround = 0.0
    total_waiting = 0.0
    total_response = 0.0
    total_burst = 0.0

    metrics_list: List[Dict[str, Any]] = []

    for p in processes:
        pid = p["pid"]
        arrival = float(p["arrival"])
        burst = float(p["burst"])
        total_burst += burst

        completion = float(completion_times.get(pid, 0.0))
        turnaround = completion - arrival
        waiting = turnaround - burst
        first_resp = float(first_response_times.get(pid, arrival))
        response = first_resp - arrival

        # Guard against minor floating point rounding issues
        turnaround = max(0.0, round(turnaround, 4))
        waiting = max(0.0, round(waiting, 4))
        response = max(0.0, round(response, 4))

        total_turnaround += turnaround
        total_waiting += waiting
        total_response += response

        metrics_list.append({
            "pid": pid,
            "arrival": arrival,
            "burst": burst,
            "priority": p.get("priority", 0),
            "completion": round(completion, 4),
            "turnaround": turnaround,
            "waiting": waiting,
            "response": response,
        })

    n = max(1, len(processes))
    avg_turnaround = round(total_turnaround / n, 2)
    avg_waiting = round(total_waiting / n, 2)
    avg_response = round(total_response / n, 2)

    # CPU Utilization and throughput
    effective_total_time = max(total_time, total_burst)
    cpu_utilization = round((total_burst / effective_total_time) * 100.0, 2) if effective_total_time > 0 else 100.0
    throughput = round(len(processes) / effective_total_time, 4) if effective_total_time > 0 else 0.0

    return metrics_list, avg_turnaround, avg_waiting, avg_response, cpu_utilization, throughput


def generate_disk_analysis(results: Dict[str, Any]) -> str:
    """Generate in-depth qualitative analysis comparing disk scheduling algorithms."""
    # Find algorithm with minimum head movement
    sorted_algs = sorted(results.items(), key=lambda kv: kv[1]["total_movement"])
    best_alg, best_res = sorted_algs[0]
    worst_alg, worst_res = sorted_algs[-1]

    analysis_lines = [
        f"**Benchmark Summary:** Under this workload, **{best_alg}** demonstrated optimal efficiency with only "
        f"{best_res['total_movement']} cylinder movements ({best_res['seek_time_ms']:.1f} ms seek delay), "
        f"representing a {((worst_res['total_movement'] - best_res['total_movement']) / max(1, worst_res['total_movement']) * 100):.1f}% "
        f"reduction compared to {worst_alg} ({worst_res['total_movement']} cylinders).",
        "",
        "- **SSTF Starvation Risk:** While SSTF minimizes immediate seek times, it exhibits susceptibility to starvation "
        "if an incoming stream of requests clusters near the current cylinder head, indefinitely deferring peripheral cylinders.",
        "- **SCAN / C-SCAN Uniformity:** SCAN provides bounded response times by traversing bidirectional sweeps. "
        "C-SCAN enhances fairness by strictly servicing in one direction; its return jump carries the head back without servicing, "
        "ensuring uniform wait-time variance across both outer and inner tracks.",
        "- **LOOK / C-LOOK Efficiency:** LOOK and C-LOOK eliminate redundant head travel to track extremes (0 and max cylinder) "
        "by reversing or jumping immediately after servicing the outermost pending request in the active queue direction."
    ]

    return "\n".join(analysis_lines)


def generate_cpu_analysis(results: Dict[str, Any]) -> str:
    """Generate qualitative analysis comparing CPU scheduling algorithms."""
    sorted_algs = sorted(results.items(), key=lambda kv: kv[1]["avg_waiting"])
    best_alg, best_res = sorted_algs[0]

    analysis_lines = [
        f"**CPU Scheduling Insights:** **{best_alg}** achieved the lowest average waiting time of {best_res['avg_waiting']:.2f} time units.",
        "",
        "- **SJF / SRTF Optimality:** Shortest Job First provably minimizes average waiting time for batch systems, though "
        "preemptive Shortest Remaining Time First (SRTF) can introduce context-switching overhead.",
        "- **Round Robin Fairness:** Round Robin eliminates process starvation and guarantees predictable response latency. "
        "The choice of time quantum is critical: too small causes excessive context switches; too large degenerates to FCFS.",
        "- **Priority Scheduling:** Non-preemptive priority honors process urgency but requires an aging mechanism in production "
        "to prevent low-priority process starvation."
    ]

    return "\n".join(analysis_lines)


def generate_page_analysis(results: Dict[str, Any]) -> str:
    """Generate qualitative analysis comparing page replacement algorithms."""
    sorted_algs = sorted(results.items(), key=lambda kv: kv[1]["total_faults"])
    best_alg, best_res = sorted_algs[0]

    analysis_lines = [
        f"**Virtual Memory Insights:** **{best_alg}** generated the fewest page faults ({best_res['total_faults']} faults, "
        f"{best_res['hit_ratio'] * 100:.1f}% hit ratio).",
        "",
        "- **Optimal (MIN) Benchmark:** Belady's Optimal algorithm provides the theoretical minimum fault count by inspecting "
        "future memory references, serving as a standard upper-bound benchmark for practical algorithms.",
        "- **LRU Approximation:** Least Recently Used leverages temporal locality by assuming recently accessed pages are "
        "likely to be accessed again soon. It never suffers from Belady's Anomaly.",
        "- **FIFO Vulnerability:** First-In, First-Out replaces the oldest resident page without considering frequency or recency, "
        "making it susceptible to Belady's Anomaly where allocating additional frames can increase total page faults."
    ]

    return "\n".join(analysis_lines)
