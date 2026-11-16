"""Disk Scheduling Algorithms Subsystem for OSRM.

Implements pure deterministic routines for FCFS, SSTF, SCAN, C-SCAN, LOOK, and C-LOOK.
Returns structured dataclasses containing service sequences, step-by-step traces,
total head movement, and seek time metrics.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from core.serialization import to_dict
from core.validators import validate_disk_input


@dataclass
class DiskStep:
    """Represents a discrete head movement transition."""
    step: int
    from_cyl: int
    to_cyl: int
    distance: int
    cumulative: int
    is_jump: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return to_dict(self)


@dataclass
class DiskResult:
    """Consolidated outcome of a disk scheduling algorithm execution."""
    algorithm: str
    sequence: List[int]
    total_movement: int
    avg_seek: float
    seek_time_ms: float
    jump_index: Optional[int]
    trace: List[str]
    steps: List[DiskStep]

    def to_dict(self) -> Dict[str, Any]:
        return to_dict(self)


# -----------------------------------------------------------------------------
# Disk Scheduling Implementations
# -----------------------------------------------------------------------------

def run_fcfs(
    requests: List[int],
    head: int,
    size: int,
    direction: str = "left",
    count_jump: bool = True,
    ms_per_cyl: float = 1.0,
) -> DiskResult:
    """First-Come, First-Served (FCFS) Disk Scheduling."""
    sequence = [head]
    steps: List[DiskStep] = []
    trace: List[str] = []
    total_movement = 0
    curr = head

    for idx, target in enumerate(requests, start=1):
        dist = abs(target - curr)
        total_movement += dist
        steps.append(DiskStep(
            step=idx,
            from_cyl=curr,
            to_cyl=target,
            distance=dist,
            cumulative=total_movement,
            is_jump=False
        ))
        trace.append(f"Step {idx}: {curr} -> {target} : {dist} cylinders (Total: {total_movement})")
        curr = target
        sequence.append(target)

    n_req = max(1, len(requests))
    avg_seek = round(total_movement / n_req, 2)
    seek_time = round(total_movement * ms_per_cyl, 2)

    return DiskResult(
        algorithm="FCFS",
        sequence=sequence,
        total_movement=total_movement,
        avg_seek=avg_seek,
        seek_time_ms=seek_time,
        jump_index=None,
        trace=trace,
        steps=steps
    )


def run_sstf(
    requests: List[int],
    head: int,
    size: int,
    direction: str = "left",
    count_jump: bool = True,
    ms_per_cyl: float = 1.0,
) -> DiskResult:
    """Shortest Seek Time First (SSTF) Disk Scheduling."""
    remaining = list(requests)
    sequence = [head]
    steps: List[DiskStep] = []
    trace: List[str] = []
    total_movement = 0
    curr = head
    step_num = 1

    while remaining:
        # Find request with minimum distance to curr
        # If tie, prioritize based on direction or lower cylinder
        remaining.sort()
        best_candidate = remaining[0]
        min_dist = abs(best_candidate - curr)

        for candidate in remaining[1:]:
            d = abs(candidate - curr)
            if d < min_dist:
                min_dist = d
                best_candidate = candidate
            elif d == min_dist:
                # Tie-breaker: if moving left prefer smaller, if right prefer larger
                if direction == "left" and candidate < best_candidate:
                    best_candidate = candidate
                elif direction == "right" and candidate > best_candidate:
                    best_candidate = candidate

        remaining.remove(best_candidate)
        total_movement += min_dist
        steps.append(DiskStep(
            step=step_num,
            from_cyl=curr,
            to_cyl=best_candidate,
            distance=min_dist,
            cumulative=total_movement,
            is_jump=False
        ))
        trace.append(f"Step {step_num}: {curr} -> {best_candidate} : {min_dist} cylinders (Total: {total_movement})")
        curr = best_candidate
        sequence.append(best_candidate)
        step_num += 1

    n_req = max(1, len(requests))
    avg_seek = round(total_movement / n_req, 2)
    seek_time = round(total_movement * ms_per_cyl, 2)

    return DiskResult(
        algorithm="SSTF",
        sequence=sequence,
        total_movement=total_movement,
        avg_seek=avg_seek,
        seek_time_ms=seek_time,
        jump_index=None,
        trace=trace,
        steps=steps
    )


def run_scan(
    requests: List[int],
    head: int,
    size: int,
    direction: str = "left",
    count_jump: bool = True,
    ms_per_cyl: float = 1.0,
) -> DiskResult:
    """SCAN (Elevator) Disk Scheduling."""
    sequence = [head]
    steps: List[DiskStep] = []
    trace: List[str] = []
    total_movement = 0
    curr = head
    step_num = 1

    left_reqs = sorted([r for r in requests if r <= head], reverse=True)
    right_reqs = sorted([r for r in requests if r > head])

    plan: List[Tuple[int, bool]] = []  # (cylinder, is_endpoint)

    if direction == "left":
        for r in left_reqs:
            plan.append((r, False))
        # If there are rightward requests pending, arm must reach boundary 0 before reversing
        if right_reqs:
            if not plan or plan[-1][0] != 0:
                plan.append((0, True))
            for r in right_reqs:
                plan.append((r, False))
    else:  # right
        for r in right_reqs:
            plan.append((r, False))
        # If there are leftward requests pending, arm reaches disk end (size - 1) before reversing
        if left_reqs:
            if not plan or plan[-1][0] != size - 1:
                plan.append((size - 1, True))
            for r in reversed(left_reqs):
                plan.append((r, False))

    for target, is_boundary in plan:
        dist = abs(target - curr)
        total_movement += dist
        steps.append(DiskStep(
            step=step_num,
            from_cyl=curr,
            to_cyl=target,
            distance=dist,
            cumulative=total_movement,
            is_jump=False
        ))
        b_note = " [Boundary]" if is_boundary else ""
        trace.append(f"Step {step_num}: {curr} -> {target}{b_note} : {dist} cylinders (Total: {total_movement})")
        curr = target
        sequence.append(target)
        step_num += 1

    n_req = max(1, len(requests))
    avg_seek = round(total_movement / n_req, 2)
    seek_time = round(total_movement * ms_per_cyl, 2)

    return DiskResult(
        algorithm="SCAN",
        sequence=sequence,
        total_movement=total_movement,
        avg_seek=avg_seek,
        seek_time_ms=seek_time,
        jump_index=None,
        trace=trace,
        steps=steps
    )


def run_c_scan(
    requests: List[int],
    head: int,
    size: int,
    direction: str = "right",
    count_jump: bool = True,
    ms_per_cyl: float = 1.0,
) -> DiskResult:
    """Circular SCAN (C-SCAN) Disk Scheduling."""
    sequence = [head]
    steps: List[DiskStep] = []
    trace: List[str] = []
    total_movement = 0
    curr = head
    step_num = 1
    jump_index: Optional[int] = None

    if direction == "right":
        right_reqs = sorted([r for r in requests if r >= head])
        left_reqs = sorted([r for r in requests if r < head])

        # Move to right boundary (size - 1)
        for r in right_reqs:
            dist = abs(r - curr)
            total_movement += dist
            steps.append(DiskStep(step=step_num, from_cyl=curr, to_cyl=r, distance=dist, cumulative=total_movement))
            trace.append(f"Step {step_num}: {curr} -> {r} : {dist} cylinders (Total: {total_movement})")
            curr = r
            sequence.append(r)
            step_num += 1

        if left_reqs:
            # Go to end boundary if not already there
            if curr != size - 1:
                dist = abs((size - 1) - curr)
                total_movement += dist
                steps.append(DiskStep(step=step_num, from_cyl=curr, to_cyl=size - 1, distance=dist, cumulative=total_movement))
                trace.append(f"Step {step_num}: {curr} -> {size - 1} [Boundary] : {dist} cylinders (Total: {total_movement})")
                curr = size - 1
                sequence.append(size - 1)
                step_num += 1

            # Circular Return Jump from (size - 1) to 0
            jump_dist = size - 1
            if count_jump:
                total_movement += jump_dist
            jump_index = step_num
            steps.append(DiskStep(
                step=step_num,
                from_cyl=size - 1,
                to_cyl=0,
                distance=jump_dist if count_jump else 0,
                cumulative=total_movement,
                is_jump=True
            ))
            jump_label = f"Step {step_num}: {size - 1} -> 0 [Return Jump] : {jump_dist} cyl"
            if not count_jump:
                jump_label += " (Uncounted)"
            trace.append(f"{jump_label} (Total: {total_movement})")
            curr = 0
            sequence.append(0)
            step_num += 1

            # Service remaining left requests from 0 moving right
            for r in left_reqs:
                dist = abs(r - curr)
                total_movement += dist
                steps.append(DiskStep(step=step_num, from_cyl=curr, to_cyl=r, distance=dist, cumulative=total_movement))
                trace.append(f"Step {step_num}: {curr} -> {r} : {dist} cylinders (Total: {total_movement})")
                curr = r
                sequence.append(r)
                step_num += 1

    else:  # direction == "left"
        left_reqs = sorted([r for r in requests if r <= head], reverse=True)
        right_reqs = sorted([r for r in requests if r > head], reverse=True)

        for r in left_reqs:
            dist = abs(r - curr)
            total_movement += dist
            steps.append(DiskStep(step=step_num, from_cyl=curr, to_cyl=r, distance=dist, cumulative=total_movement))
            trace.append(f"Step {step_num}: {curr} -> {r} : {dist} cylinders (Total: {total_movement})")
            curr = r
            sequence.append(r)
            step_num += 1

        if right_reqs:
            if curr != 0:
                dist = curr
                total_movement += dist
                steps.append(DiskStep(step=step_num, from_cyl=curr, to_cyl=0, distance=dist, cumulative=total_movement))
                trace.append(f"Step {step_num}: {curr} -> 0 [Boundary] : {dist} cylinders (Total: {total_movement})")
                curr = 0
                sequence.append(0)
                step_num += 1

            jump_dist = size - 1
            if count_jump:
                total_movement += jump_dist
            jump_index = step_num
            steps.append(DiskStep(
                step=step_num,
                from_cyl=0,
                to_cyl=size - 1,
                distance=jump_dist if count_jump else 0,
                cumulative=total_movement,
                is_jump=True
            ))
            jump_label = f"Step {step_num}: 0 -> {size - 1} [Return Jump] : {jump_dist} cyl"
            if not count_jump:
                jump_label += " (Uncounted)"
            trace.append(f"{jump_label} (Total: {total_movement})")
            curr = size - 1
            sequence.append(size - 1)
            step_num += 1

            for r in right_reqs:
                dist = abs(r - curr)
                total_movement += dist
                steps.append(DiskStep(step=step_num, from_cyl=curr, to_cyl=r, distance=dist, cumulative=total_movement))
                trace.append(f"Step {step_num}: {curr} -> {r} : {dist} cylinders (Total: {total_movement})")
                curr = r
                sequence.append(r)
                step_num += 1

    n_req = max(1, len(requests))
    avg_seek = round(total_movement / n_req, 2)
    seek_time = round(total_movement * ms_per_cyl, 2)

    return DiskResult(
        algorithm="C-SCAN",
        sequence=sequence,
        total_movement=total_movement,
        avg_seek=avg_seek,
        seek_time_ms=seek_time,
        jump_index=jump_index,
        trace=trace,
        steps=steps
    )


def run_look(
    requests: List[int],
    head: int,
    size: int,
    direction: str = "left",
    count_jump: bool = True,
    ms_per_cyl: float = 1.0,
) -> DiskResult:
    """LOOK (Bounded Elevator) Disk Scheduling."""
    sequence = [head]
    steps: List[DiskStep] = []
    trace: List[str] = []
    total_movement = 0
    curr = head
    step_num = 1

    left_reqs = sorted([r for r in requests if r <= head], reverse=True)
    right_reqs = sorted([r for r in requests if r > head])

    plan: List[int] = []
    if direction == "left":
        plan.extend(left_reqs)
        plan.extend(right_reqs)
    else:
        plan.extend(right_reqs)
        plan.extend(reversed(left_reqs))

    for target in plan:
        dist = abs(target - curr)
        total_movement += dist
        steps.append(DiskStep(
            step=step_num,
            from_cyl=curr,
            to_cyl=target,
            distance=dist,
            cumulative=total_movement,
            is_jump=False
        ))
        trace.append(f"Step {step_num}: {curr} -> {target} : {dist} cylinders (Total: {total_movement})")
        curr = target
        sequence.append(target)
        step_num += 1

    n_req = max(1, len(requests))
    avg_seek = round(total_movement / n_req, 2)
    seek_time = round(total_movement * ms_per_cyl, 2)

    return DiskResult(
        algorithm="LOOK",
        sequence=sequence,
        total_movement=total_movement,
        avg_seek=avg_seek,
        seek_time_ms=seek_time,
        jump_index=None,
        trace=trace,
        steps=steps
    )


def run_c_look(
    requests: List[int],
    head: int,
    size: int,
    direction: str = "right",
    count_jump: bool = True,
    ms_per_cyl: float = 1.0,
) -> DiskResult:
    """Circular LOOK (C-LOOK) Disk Scheduling."""
    sequence = [head]
    steps: List[DiskStep] = []
    trace: List[str] = []
    total_movement = 0
    curr = head
    step_num = 1
    jump_index: Optional[int] = None

    if direction == "right":
        right_reqs = sorted([r for r in requests if r >= head])
        left_reqs = sorted([r for r in requests if r < head])

        for r in right_reqs:
            dist = abs(r - curr)
            total_movement += dist
            steps.append(DiskStep(step=step_num, from_cyl=curr, to_cyl=r, distance=dist, cumulative=total_movement))
            trace.append(f"Step {step_num}: {curr} -> {r} : {dist} cylinders (Total: {total_movement})")
            curr = r
            sequence.append(r)
            step_num += 1

        if left_reqs:
            lowest_req = left_reqs[0]
            jump_dist = abs(curr - lowest_req)
            if count_jump:
                total_movement += jump_dist
            jump_index = step_num
            steps.append(DiskStep(
                step=step_num,
                from_cyl=curr,
                to_cyl=lowest_req,
                distance=jump_dist if count_jump else 0,
                cumulative=total_movement,
                is_jump=True
            ))
            jump_label = f"Step {step_num}: {curr} -> {lowest_req} [Return Jump] : {jump_dist} cyl"
            if not count_jump:
                jump_label += " (Uncounted)"
            trace.append(f"{jump_label} (Total: {total_movement})")
            curr = lowest_req
            sequence.append(lowest_req)
            step_num += 1

            for r in left_reqs[1:]:
                dist = abs(r - curr)
                total_movement += dist
                steps.append(DiskStep(step=step_num, from_cyl=curr, to_cyl=r, distance=dist, cumulative=total_movement))
                trace.append(f"Step {step_num}: {curr} -> {r} : {dist} cylinders (Total: {total_movement})")
                curr = r
                sequence.append(r)
                step_num += 1

    else:  # direction == "left"
        left_reqs = sorted([r for r in requests if r <= head], reverse=True)
        right_reqs = sorted([r for r in requests if r > head], reverse=True)

        for r in left_reqs:
            dist = abs(r - curr)
            total_movement += dist
            steps.append(DiskStep(step=step_num, from_cyl=curr, to_cyl=r, distance=dist, cumulative=total_movement))
            trace.append(f"Step {step_num}: {curr} -> {r} : {dist} cylinders (Total: {total_movement})")
            curr = r
            sequence.append(r)
            step_num += 1

        if right_reqs:
            highest_req = right_reqs[0]
            jump_dist = abs(curr - highest_req)
            if count_jump:
                total_movement += jump_dist
            jump_index = step_num
            steps.append(DiskStep(
                step=step_num,
                from_cyl=curr,
                to_cyl=highest_req,
                distance=jump_dist if count_jump else 0,
                cumulative=total_movement,
                is_jump=True
            ))
            jump_label = f"Step {step_num}: {curr} -> {highest_req} [Return Jump] : {jump_dist} cyl"
            if not count_jump:
                jump_label += " (Uncounted)"
            trace.append(f"{jump_label} (Total: {total_movement})")
            curr = highest_req
            sequence.append(highest_req)
            step_num += 1

            for r in right_reqs[1:]:
                dist = abs(r - curr)
                total_movement += dist
                steps.append(DiskStep(step=step_num, from_cyl=curr, to_cyl=r, distance=dist, cumulative=total_movement))
                trace.append(f"Step {step_num}: {curr} -> {r} : {dist} cylinders (Total: {total_movement})")
                curr = r
                sequence.append(r)
                step_num += 1

    n_req = max(1, len(requests))
    avg_seek = round(total_movement / n_req, 2)
    seek_time = round(total_movement * ms_per_cyl, 2)

    return DiskResult(
        algorithm="C-LOOK",
        sequence=sequence,
        total_movement=total_movement,
        avg_seek=avg_seek,
        seek_time_ms=seek_time,
        jump_index=jump_index,
        trace=trace,
        steps=steps
    )


# Registry of available algorithms
DISK_ALGORITHMS: Dict[str, Callable[..., DiskResult]] = {
    "FCFS": run_fcfs,
    "SSTF": run_sstf,
    "SCAN": run_scan,
    "C-SCAN": run_c_scan,
    "LOOK": run_look,
    "C-LOOK": run_c_look,
}


def run_disk_simulation(
    requests: List[int],
    head: int,
    size: int,
    direction: str = "left",
    algorithm: str = "FCFS",
    count_jump: bool = True,
    ms_per_cyl: float = 1.0,
) -> DiskResult:
    """Execute a single validated disk scheduling simulation."""
    reqs, h, s, d, ms = validate_disk_input(
        requests, head, size, direction, ms_per_cyl, algorithm, list(DISK_ALGORITHMS.keys())
    )
    solver = DISK_ALGORITHMS[algorithm]
    return solver(
        requests=reqs,
        head=h,
        size=s,
        direction=d,
        count_jump=count_jump,
        ms_per_cyl=ms,
    )


def compare_all_disk(
    requests: List[int],
    head: int,
    size: int,
    direction: str = "left",
    count_jump: bool = True,
    ms_per_cyl: float = 1.0,
) -> Dict[str, Any]:
    """Execute all 6 disk scheduling algorithms and assemble comparison metrics."""
    reqs, h, s, d, ms = validate_disk_input(
        requests, head, size, direction, ms_per_cyl
    )

    results: Dict[str, Any] = {}
    best_movement = float("inf")
    best_algorithms: List[str] = []

    for name, solver in DISK_ALGORITHMS.items():
        res = solver(
            requests=reqs,
            head=h,
            size=s,
            direction=d,
            count_jump=count_jump,
            ms_per_cyl=ms,
        )
        res_dict = res.to_dict()
        results[name] = res_dict

        if res.total_movement < best_movement:
            best_movement = res.total_movement
            best_algorithms = [name]
        elif res.total_movement == best_movement:
            best_algorithms.append(name)

    from core.metrics import generate_disk_analysis
    analysis_text = generate_disk_analysis(results)

    return {
        "results": results,
        "best_algorithms": best_algorithms,
        "best_movement": best_movement,
        "analysis": analysis_text,
    }
