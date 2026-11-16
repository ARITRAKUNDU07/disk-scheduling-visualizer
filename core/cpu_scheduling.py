"""CPU Scheduling Algorithms Subsystem for OSRM.

Implements pure deterministic algorithms for:
- FCFS (First-Come, First-Served)
- SJF (Shortest Job First - Non-Preemptive)
- SRTF (Shortest Remaining Time First - Preemptive)
- Round Robin (Configurable Time Quantum)
- Priority (Non-Preemptive, Lower Numerical Value = Higher Priority)

Returns structured dataclasses with Gantt charts, per-process turnaround and
waiting metrics, response times, and ASCII timeline traces.
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

from core.metrics import calculate_cpu_metrics
from core.serialization import to_dict
from core.validators import validate_cpu_input


@dataclass
class GanttSegment:
    """Discrete execution slice on the CPU."""
    pid: str
    start: float
    end: float

    def to_dict(self) -> Dict[str, Any]:
        return to_dict(self)


@dataclass
class ProcessMetrics:
    """Individual process scheduling performance metrics."""
    pid: str
    arrival: float
    burst: float
    priority: int
    completion: float
    turnaround: float
    waiting: float
    response: float

    def to_dict(self) -> Dict[str, Any]:
        return to_dict(self)


@dataclass
class CPUResult:
    """Consolidated outcome of a CPU scheduling algorithm run."""
    algorithm: str
    quantum: Optional[float]
    gantt: List[GanttSegment]
    process_metrics: List[ProcessMetrics]
    avg_turnaround: float
    avg_waiting: float
    avg_response: float
    cpu_utilization: float
    throughput: float
    ascii_gantt: str

    def to_dict(self) -> Dict[str, Any]:
        return to_dict(self)


def _render_ascii_gantt(gantt: List[GanttSegment]) -> str:
    """Generate a clean ASCII bar representing CPU execution flow."""
    if not gantt:
        return "[Empty Timeline]"

    top_bar = "|"
    mid_bar = "|"
    bot_bar = f"{gantt[0].start:g}"

    for seg in gantt:
        label = f" {seg.pid} "
        top_bar += "-" * len(label) + "|"
        mid_bar += label + "|"
        bot_bar += " " * (len(label) + 1 - len(f"{seg.end:g}")) + f"{seg.end:g}"

    return f"{top_bar}\n{mid_bar}\n{bot_bar}"


# -----------------------------------------------------------------------------
# CPU Algorithm Implementations
# -----------------------------------------------------------------------------

def run_fcfs_cpu(processes: List[Dict[str, Any]], quantum: Optional[float] = None) -> CPUResult:
    """First-Come, First-Served CPU Scheduling."""
    # Sort primarily by arrival, then by PID for stable order
    procs = sorted(processes, key=lambda p: (p["arrival"], p["pid"]))
    gantt: List[GanttSegment] = []
    completion: Dict[str, float] = {}
    first_resp: Dict[str, float] = {}
    curr_time = 0.0

    for p in procs:
        pid = p["pid"]
        arr = float(p["arrival"])
        bst = float(p["burst"])

        if curr_time < arr:
            curr_time = arr

        start_t = curr_time
        end_t = curr_time + bst
        curr_time = end_t

        gantt.append(GanttSegment(pid=pid, start=start_t, end=end_t))
        first_resp[pid] = start_t
        completion[pid] = end_t

    metrics_list, avg_ta, avg_wt, avg_rt, util, tp = calculate_cpu_metrics(
        procs, completion, first_resp, curr_time
    )

    proc_metrics = [ProcessMetrics(**m) for m in metrics_list]
    ascii_bar = _render_ascii_gantt(gantt)

    return CPUResult(
        algorithm="FCFS",
        quantum=None,
        gantt=gantt,
        process_metrics=proc_metrics,
        avg_turnaround=avg_ta,
        avg_waiting=avg_wt,
        avg_response=avg_rt,
        cpu_utilization=util,
        throughput=tp,
        ascii_gantt=ascii_bar
    )


def run_sjf_cpu(processes: List[Dict[str, Any]], quantum: Optional[float] = None) -> CPUResult:
    """Shortest Job First (Non-Preemptive) CPU Scheduling."""
    procs = [dict(p) for p in processes]
    n = len(procs)
    completed_count = 0
    curr_time = 0.0

    gantt: List[GanttSegment] = []
    completion: Dict[str, float] = {}
    first_resp: Dict[str, float] = {}
    finished = set()

    while completed_count < n:
        # Ready queue: arrived and not finished
        ready = [p for p in procs if p["arrival"] <= curr_time and p["pid"] not in finished]

        if not ready:
            # Advance time to earliest arriving uncompleted process
            uncompleted = [p for p in procs if p["pid"] not in finished]
            curr_time = min(p["arrival"] for p in uncompleted)
            continue

        # Shortest burst; tie-break by arrival, then PID
        ready.sort(key=lambda p: (p["burst"], p["arrival"], p["pid"]))
        chosen = ready[0]
        pid = chosen["pid"]

        start_t = curr_time
        end_t = curr_time + chosen["burst"]
        curr_time = end_t

        gantt.append(GanttSegment(pid=pid, start=start_t, end=end_t))
        first_resp[pid] = start_t
        completion[pid] = end_t
        finished.add(pid)
        completed_count += 1

    metrics_list, avg_ta, avg_wt, avg_rt, util, tp = calculate_cpu_metrics(
        procs, completion, first_resp, curr_time
    )

    return CPUResult(
        algorithm="SJF",
        quantum=None,
        gantt=gantt,
        process_metrics=[ProcessMetrics(**m) for m in metrics_list],
        avg_turnaround=avg_ta,
        avg_waiting=avg_wt,
        avg_response=avg_rt,
        cpu_utilization=util,
        throughput=tp,
        ascii_gantt=_render_ascii_gantt(gantt)
    )


def run_srtf_cpu(processes: List[Dict[str, Any]], quantum: Optional[float] = None) -> CPUResult:
    """Shortest Remaining Time First (Preemptive SJF) CPU Scheduling."""
    procs = [dict(p) for p in processes]
    n = len(procs)
    rem_burst = {p["pid"]: float(p["burst"]) for p in procs}
    arrival_map = {p["pid"]: float(p["arrival"]) for p in procs}

    raw_gantt: List[Tuple[str, float, float]] = []
    completion: Dict[str, float] = {}
    first_resp: Dict[str, float] = {}

    curr_time = 0.0
    completed_count = 0

    # Determine simulation discrete events
    while completed_count < n:
        ready = [
            p for p in procs
            if arrival_map[p["pid"]] <= curr_time and rem_burst[p["pid"]] > 0
        ]

        if not ready:
            uncompleted = [p for p in procs if rem_burst[p["pid"]] > 0]
            curr_time = min(arrival_map[p["pid"]] for p in uncompleted)
            continue

        # Choose process with minimum remaining burst
        ready.sort(key=lambda p: (rem_burst[p["pid"]], arrival_map[p["pid"]], p["pid"]))
        active = ready[0]
        pid = active["pid"]

        if pid not in first_resp:
            first_resp[pid] = curr_time

        # Find next event time: either active process finishes, or a future process arrives
        future_arrivals = [
            arr for arr in [p["arrival"] for p in procs]
            if arr > curr_time
        ]
        time_to_next_arrival = min(future_arrivals) - curr_time if future_arrivals else float("inf")
        step_exec = min(rem_burst[pid], time_to_next_arrival)

        start_t = curr_time
        end_t = curr_time + step_exec
        curr_time = end_t
        rem_burst[pid] -= step_exec

        # Append or merge Gantt slice
        if raw_gantt and raw_gantt[-1][0] == pid and abs(raw_gantt[-1][2] - start_t) < 1e-6:
            raw_gantt[-1] = (pid, raw_gantt[-1][1], end_t)
        else:
            raw_gantt.append((pid, start_t, end_t))

        if rem_burst[pid] <= 1e-6:
            completion[pid] = end_t
            completed_count += 1

    gantt = [GanttSegment(pid=p, start=s, end=e) for p, s, e in raw_gantt]
    metrics_list, avg_ta, avg_wt, avg_rt, util, tp = calculate_cpu_metrics(
        procs, completion, first_resp, curr_time
    )

    return CPUResult(
        algorithm="SRTF",
        quantum=None,
        gantt=gantt,
        process_metrics=[ProcessMetrics(**m) for m in metrics_list],
        avg_turnaround=avg_ta,
        avg_waiting=avg_wt,
        avg_response=avg_rt,
        cpu_utilization=util,
        throughput=tp,
        ascii_gantt=_render_ascii_gantt(gantt)
    )


def run_round_robin_cpu(processes: List[Dict[str, Any]], quantum: Optional[float] = 4.0) -> CPUResult:
    """Round Robin CPU Scheduling with Time Quantum."""
    q = float(quantum) if quantum and float(quantum) > 0 else 4.0
    procs = sorted([dict(p) for p in processes], key=lambda p: (p["arrival"], p["pid"]))
    n = len(procs)

    rem_burst = {p["pid"]: float(p["burst"]) for p in procs}
    arrival_map = {p["pid"]: float(p["arrival"]) for p in procs}

    gantt: List[GanttSegment] = []
    completion: Dict[str, float] = {}
    first_resp: Dict[str, float] = {}

    curr_time = 0.0
    ready_queue: List[str] = []
    arrived_set = set()

    def enqueue_arrived(time_limit: float):
        for p in procs:
            pid = p["pid"]
            if pid not in arrived_set and arrival_map[pid] <= time_limit:
                ready_queue.append(pid)
                arrived_set.add(pid)

    enqueue_arrived(curr_time)

    while len(completion) < n:
        if not ready_queue:
            # Advance to next arrival
            uncompleted = [p for p in procs if p["pid"] not in completion]
            curr_time = min(arrival_map[p["pid"]] for p in uncompleted)
            enqueue_arrived(curr_time)
            continue

        pid = ready_queue.pop(0)

        if pid not in first_resp:
            first_resp[pid] = curr_time

        exec_time = min(rem_burst[pid], q)
        start_t = curr_time
        end_t = curr_time + exec_time
        curr_time = end_t
        rem_burst[pid] -= exec_time

        gantt.append(GanttSegment(pid=pid, start=start_t, end=end_t))

        # Check for new arrivals while this process was executing
        enqueue_arrived(curr_time)

        if rem_burst[pid] > 1e-6:
            ready_queue.append(pid)
        else:
            completion[pid] = end_t

    metrics_list, avg_ta, avg_wt, avg_rt, util, tp = calculate_cpu_metrics(
        procs, completion, first_resp, curr_time
    )

    return CPUResult(
        algorithm="Round Robin",
        quantum=q,
        gantt=gantt,
        process_metrics=[ProcessMetrics(**m) for m in metrics_list],
        avg_turnaround=avg_ta,
        avg_waiting=avg_wt,
        avg_response=avg_rt,
        cpu_utilization=util,
        throughput=tp,
        ascii_gantt=_render_ascii_gantt(gantt)
    )


def run_priority_cpu(processes: List[Dict[str, Any]], quantum: Optional[float] = None) -> CPUResult:
    """Non-Preemptive Priority CPU Scheduling (Lower number = Higher priority)."""
    procs = [dict(p) for p in processes]
    n = len(procs)
    completed_count = 0
    curr_time = 0.0

    gantt: List[GanttSegment] = []
    completion: Dict[str, float] = {}
    first_resp: Dict[str, float] = {}
    finished = set()

    while completed_count < n:
        ready = [p for p in procs if p["arrival"] <= curr_time and p["pid"] not in finished]

        if not ready:
            uncompleted = [p for p in procs if p["pid"] not in finished]
            curr_time = min(p["arrival"] for p in uncompleted)
            continue

        # Lowest numerical priority value is prioritized
        ready.sort(key=lambda p: (p.get("priority", 0), p["arrival"], p["pid"]))
        chosen = ready[0]
        pid = chosen["pid"]

        start_t = curr_time
        end_t = curr_time + chosen["burst"]
        curr_time = end_t

        gantt.append(GanttSegment(pid=pid, start=start_t, end=end_t))
        first_resp[pid] = start_t
        completion[pid] = end_t
        finished.add(pid)
        completed_count += 1

    metrics_list, avg_ta, avg_wt, avg_rt, util, tp = calculate_cpu_metrics(
        procs, completion, first_resp, curr_time
    )

    return CPUResult(
        algorithm="Priority",
        quantum=None,
        gantt=gantt,
        process_metrics=[ProcessMetrics(**m) for m in metrics_list],
        avg_turnaround=avg_ta,
        avg_waiting=avg_wt,
        avg_response=avg_rt,
        cpu_utilization=util,
        throughput=tp,
        ascii_gantt=_render_ascii_gantt(gantt)
    )


CPU_ALGORITHMS: Dict[str, Callable[..., CPUResult]] = {
    "FCFS": run_fcfs_cpu,
    "SJF": run_sjf_cpu,
    "SRTF": run_srtf_cpu,
    "Round Robin": run_round_robin_cpu,
    "Priority": run_priority_cpu,
}


def run_cpu_simulation(
    processes: List[Dict[str, Any]],
    algorithm: str = "FCFS",
    quantum: Optional[float] = 4.0,
) -> CPUResult:
    """Execute single CPU scheduling simulation with validated parameters."""
    clean_procs, clean_q = validate_cpu_input(
        processes, quantum, algorithm, list(CPU_ALGORITHMS.keys())
    )
    solver = CPU_ALGORITHMS[algorithm]
    return solver(clean_procs, clean_q)


def compare_all_cpu(
    processes: List[Dict[str, Any]],
    quantum: Optional[float] = 4.0,
) -> Dict[str, Any]:
    """Execute all CPU algorithms on identical process dataset and compare performance."""
    clean_procs, clean_q = validate_cpu_input(processes, quantum)

    results: Dict[str, Any] = {}
    best_wt = float("inf")
    best_algorithms: List[str] = []

    for name, solver in CPU_ALGORITHMS.items():
        res = solver(clean_procs, clean_q)
        res_dict = res.to_dict()
        results[name] = res_dict

        if res.avg_waiting < best_wt:
            best_wt = res.avg_waiting
            best_algorithms = [name]
        elif res.avg_waiting == best_wt:
            best_algorithms.append(name)

    from core.metrics import generate_cpu_analysis
    analysis_text = generate_cpu_analysis(results)

    return {
        "results": results,
        "best_algorithms": best_algorithms,
        "best_waiting": best_wt,
        "analysis": analysis_text,
    }
