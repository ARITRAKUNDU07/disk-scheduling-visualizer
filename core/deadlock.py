"""Banker's Deadlock Avoidance Subsystem for OSRM.

Implements pure deterministic routines for:
- Calculation of Need Matrix (Need = Max - Allocation)
- Safety Algorithm (Detects Safe/Unsafe states and builds safe sequences)
- Resource Request Algorithm (Evaluates hypothetical state transitions with rollback)

Returns structured dataclasses with step-by-step vector evolutions and narrative rationales.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from core.serialization import to_dict
from core.validators import validate_deadlock_input, validate_request_input


@dataclass
class SafetyStep:
    """Represents one process allocation check and release cycle during safety evaluation."""
    step: int
    pid: str
    work_before: List[int]
    need: List[int]
    allocation: List[int]
    work_after: List[int]

    def to_dict(self) -> Dict[str, Any]:
        return to_dict(self)


@dataclass
class SafetyResult:
    """Consolidated outcome of the Banker's safety state test."""
    is_safe: bool
    safe_sequence: List[str]
    steps: List[SafetyStep]
    need_matrix: Dict[str, List[int]]
    available_history: List[List[int]]
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return to_dict(self)


@dataclass
class RequestResult:
    """Evaluation result for an ad-hoc process resource request."""
    granted: bool
    reason: str
    safety_after_allocation: Optional[SafetyResult]
    hypothetical_available: Optional[List[int]] = None
    hypothetical_allocation: Optional[Dict[str, List[int]]] = None
    hypothetical_need: Optional[Dict[str, List[int]]] = None

    def to_dict(self) -> Dict[str, Any]:
        return to_dict(self)


# -----------------------------------------------------------------------------
# Banker's Implementations
# -----------------------------------------------------------------------------

def compute_need_matrix(
    allocation: Dict[str, List[int]],
    max_matrix: Dict[str, List[int]]
) -> Dict[str, List[int]]:
    """Compute Need = Max - Allocation for all processes."""
    need: Dict[str, List[int]] = {}
    for pid in allocation.keys():
        need[pid] = [
            max_matrix[pid][j] - allocation[pid][j]
            for j in range(len(allocation[pid]))
        ]
    return need


def evaluate_safety(
    available: List[int],
    allocation: Dict[str, List[int]],
    max_matrix: Dict[str, List[int]],
) -> SafetyResult:
    """Execute the standard Banker's safety algorithm."""
    clean_avail, clean_alloc, clean_max, num_res = validate_deadlock_input(
        available, allocation, max_matrix
    )

    need = compute_need_matrix(clean_alloc, clean_max)
    work = list(clean_avail)
    finish: Dict[str, bool] = {pid: False for pid in clean_alloc.keys()}
    safe_seq: List[str] = []
    steps: List[SafetyStep] = []
    avail_history: List[List[int]] = [list(work)]

    step_counter = 1
    pids = list(clean_alloc.keys())
    curr_idx = 0

    while len(safe_seq) < len(pids):
        found = False
        for offset in range(len(pids)):
            idx = (curr_idx + offset) % len(pids)
            pid = pids[idx]
            if not finish[pid]:
                # Check if Need[pid][j] <= Work[j] for all j
                can_satisfy = all(need[pid][j] <= work[j] for j in range(num_res))
                if can_satisfy:
                    work_before = list(work)
                    for j in range(num_res):
                        work[j] += clean_alloc[pid][j]
                    work_after = list(work)

                    finish[pid] = True
                    safe_seq.append(pid)
                    avail_history.append(list(work_after))

                    steps.append(SafetyStep(
                        step=step_counter,
                        pid=pid,
                        work_before=work_before,
                        need=need[pid],
                        allocation=clean_alloc[pid],
                        work_after=work_after
                    ))
                    step_counter += 1
                    found = True
                    curr_idx = (idx + 1) % len(pids)
                    break

        if not found:
            # Deadlock / Unsafe detected
            blocked_procs = [pid for pid, is_done in finish.items() if not is_done]
            reason = (
                f"UNSAFE state: Work vector {work} cannot satisfy the remaining requirements "
                f"of pending processes: {', '.join(blocked_procs)}. Deadlock could occur."
            )
            return SafetyResult(
                is_safe=False,
                safe_sequence=[],
                steps=steps,
                need_matrix=need,
                available_history=avail_history,
                reason=reason
            )

    reason = f"SAFE state: A valid execution order exists: {' -> '.join(safe_seq)}."
    return SafetyResult(
        is_safe=True,
        safe_sequence=safe_seq,
        steps=steps,
        need_matrix=need,
        available_history=avail_history,
        reason=reason
    )


def evaluate_resource_request(
    available: List[int],
    allocation: Dict[str, List[int]],
    max_matrix: Dict[str, List[int]],
    pid: str,
    request: List[int],
) -> RequestResult:
    """Evaluate a dynamic resource request using Banker's Algorithm with rollback guarantees."""
    clean_avail, clean_alloc, clean_max, pid_clean, req_clean = validate_request_input(
        available, allocation, max_matrix, pid, request
    )

    num_res = len(clean_avail)
    need = compute_need_matrix(clean_alloc, clean_max)

    # Condition 1: Request <= Need (Already guaranteed by validator)
    for j in range(num_res):
        if req_clean[j] > need[pid_clean][j]:
            return RequestResult(
                granted=False,
                reason=(
                    f"DENIED: Process '{pid_clean}' requested {req_clean[j]} of resource R{j}, "
                    f"which exceeds its declared remaining need of {need[pid_clean][j]}."
                ),
                safety_after_allocation=None
            )

    # Condition 2: Request <= Available
    for j in range(num_res):
        if req_clean[j] > clean_avail[j]:
            return RequestResult(
                granted=False,
                reason=(
                    f"WAIT REQUIRED: Process '{pid_clean}' requested {req_clean[j]} of resource R{j}, "
                    f"but only {clean_avail[j]} units are currently available."
                ),
                safety_after_allocation=None
            )

    # Condition 3: Pretend to allocate and test safety
    hypo_avail = list(clean_avail)
    hypo_alloc = {p: list(row) for p, row in clean_alloc.items()}
    hypo_max = {p: list(row) for p, row in clean_max.items()}

    for j in range(num_res):
        hypo_avail[j] -= req_clean[j]
        hypo_alloc[pid_clean][j] += req_clean[j]

    hypo_need = compute_need_matrix(hypo_alloc, hypo_max)
    safety_check = evaluate_safety(hypo_avail, hypo_alloc, hypo_max)

    if safety_check.is_safe:
        return RequestResult(
            granted=True,
            reason=(
                f"GRANTED: Request can be safely allocated immediately. "
                f"Resulting safe sequence: {' -> '.join(safety_check.safe_sequence)}."
            ),
            safety_after_allocation=safety_check,
            hypothetical_available=hypo_avail,
            hypothetical_allocation=hypo_alloc,
            hypothetical_need=hypo_need
        )
    else:
        return RequestResult(
            granted=False,
            reason=(
                f"DENIED: Granting request would transition system into an UNSAFE state. "
                f"Request was rejected and state rolled back."
            ),
            safety_after_allocation=safety_check,
            hypothetical_available=clean_avail,
            hypothetical_allocation=clean_alloc,
            hypothetical_need=need
        )
