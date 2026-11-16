"""Input Validation and Custom Exceptions for OSRM.

Defines custom domain exceptions with field-level attribution and comprehensive
defensive validators for disk, CPU, memory, and deadlock subsystems.
"""

from typing import Any, Dict, List, Optional, Tuple, Union


class OSRMError(Exception):
    """Base exception class for all OSRM simulation errors."""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.field = field or "unknown"

    def to_dict(self) -> Dict[str, str]:
        """Convert exception to dictionary representation for API serialization."""
        return {"error": self.message, "field": self.field}


class InvalidInputError(OSRMError):
    """Raised when an input value violates type constraints or expected syntax."""
    pass


class OutOfRangeError(OSRMError):
    """Raised when an input value falls outside valid operational bounds."""
    pass


class EmptyInputError(OSRMError):
    """Raised when a mandatory collection, list, or queue is empty."""
    pass


class FileFormatError(OSRMError):
    """Raised when a dataset file fails schema parsing or contains corrupted lines."""
    pass


# -----------------------------------------------------------------------------
# Disk Scheduling Validators
# -----------------------------------------------------------------------------

def validate_disk_input(
    requests: Any,
    head: Any,
    size: Any,
    direction: Any = "left",
    ms_per_cyl: Any = 1.0,
    algorithm: Optional[str] = None,
    allowed_algorithms: Optional[List[str]] = None,
) -> Tuple[List[int], int, int, str, float]:
    """Validate and sanitize parameters for disk scheduling simulations.

    Returns:
        Tuple of (clean_requests, clean_head, clean_size, clean_direction, clean_ms_per_cyl)
    Raises:
        InvalidInputError, OutOfRangeError, EmptyInputError
    """
    # 1. Disk Size
    if not isinstance(size, (int, float)) or isinstance(size, bool):
        try:
            size = int(size)
        except (ValueError, TypeError):
            raise InvalidInputError("Disk size must be a positive integer.", field="size")
    size = int(size)
    if size < 2 or size > 1_000_000:
        raise OutOfRangeError("Disk size must be between 2 and 1,000,000 cylinders.", field="size")

    # 2. Initial Head Position
    if not isinstance(head, (int, float)) or isinstance(head, bool):
        try:
            head = int(head)
        except (ValueError, TypeError):
            raise InvalidInputError("Initial head position must be an integer.", field="head")
    head = int(head)
    if head < 0 or head >= size:
        raise OutOfRangeError(f"Initial head position ({head}) must be between 0 and {size - 1}.", field="head")

    # 3. Direction
    if not isinstance(direction, str):
        raise InvalidInputError("Direction must be a string ('left' or 'right').", field="direction")
    direction_clean = direction.strip().lower()
    if direction_clean not in ("left", "right"):
        raise InvalidInputError("Direction must be either 'left' or 'right'.", field="direction")

    # 4. Milliseconds per cylinder
    if not isinstance(ms_per_cyl, (int, float)) or isinstance(ms_per_cyl, bool):
        try:
            ms_per_cyl = float(ms_per_cyl)
        except (ValueError, TypeError):
            raise InvalidInputError("ms_per_cyl must be a positive numeric value.", field="ms_per_cyl")
    ms_per_cyl = float(ms_per_cyl)
    if ms_per_cyl <= 0.0 or ms_per_cyl > 1000.0:
        raise OutOfRangeError("ms_per_cyl must be greater than 0 and at most 1000 ms.", field="ms_per_cyl")

    # 5. Request Queue
    if requests is None:
        raise EmptyInputError("Request queue cannot be null.", field="requests")

    if isinstance(requests, str):
        # Allow comma/space delimited strings
        parts = [p.strip() for p in requests.replace(" ", ",").split(",") if p.strip()]
        cleaned_reqs: List[int] = []
        for p in parts:
            try:
                cleaned_reqs.append(int(p))
            except ValueError:
                raise InvalidInputError(f"Invalid cylinder value in queue: '{p}'. Must be integer.", field="requests")
        requests = cleaned_reqs

    if not isinstance(requests, list):
        raise InvalidInputError("Requests must be a list of integers.", field="requests")

    if len(requests) == 0:
        raise EmptyInputError("Request queue cannot be empty.", field="requests")

    if len(requests) > 500:
        raise OutOfRangeError("Request queue length cannot exceed 500 cylinders.", field="requests")

    sanitized_requests: List[int] = []
    for idx, r in enumerate(requests):
        if not isinstance(r, (int, float)) or isinstance(r, bool):
            try:
                r = int(r)
            except (ValueError, TypeError):
                raise InvalidInputError(f"Request at index {idx} ('{r}') must be an integer.", field="requests")
        r_int = int(r)
        if r_int < 0 or r_int >= size:
            raise OutOfRangeError(
                f"Request cylinder {r_int} at index {idx} is out of bounds (disk size: 0..{size - 1}).",
                field="requests"
            )
        sanitized_requests.append(r_int)

    # 6. Algorithm (if specified)
    if algorithm is not None and allowed_algorithms:
        if algorithm not in allowed_algorithms:
            raise InvalidInputError(
                f"Unknown algorithm '{algorithm}'. Must be one of: {', '.join(allowed_algorithms)}.",
                field="algorithm"
            )

    return sanitized_requests, head, size, direction_clean, ms_per_cyl


# -----------------------------------------------------------------------------
# CPU Scheduling Validators
# -----------------------------------------------------------------------------

def validate_cpu_input(
    processes: Any,
    quantum: Any = None,
    algorithm: Optional[str] = None,
    allowed_algorithms: Optional[List[str]] = None,
) -> Tuple[List[Dict[str, Any]], Optional[float]]:
    """Validate and sanitize parameters for CPU scheduling simulations.

    Returns:
        Tuple of (clean_processes, clean_quantum)
    Raises:
        InvalidInputError, OutOfRangeError, EmptyInputError
    """
    if processes is None or not isinstance(processes, list):
        raise InvalidInputError("Processes must be provided as a list.", field="processes")

    if len(processes) == 0:
        raise EmptyInputError("Process list cannot be empty.", field="processes")

    if len(processes) > 100:
        raise OutOfRangeError("Number of processes cannot exceed 100.", field="processes")

    clean_processes: List[Dict[str, Any]] = []
    seen_pids = set()

    for idx, p in enumerate(processes):
        if not isinstance(p, dict):
            raise InvalidInputError(f"Process item at index {idx} must be a dictionary/object.", field="processes")

        pid = p.get("pid")
        if pid is None or str(pid).strip() == "":
            raise InvalidInputError(f"Process at index {idx} is missing a valid 'pid'.", field="pid")
        pid_str = str(pid).strip()
        if pid_str in seen_pids:
            raise InvalidInputError(f"Duplicate PID detected: '{pid_str}'. PIDs must be unique.", field="pid")
        seen_pids.add(pid_str)

        # Arrival Time
        arrival = p.get("arrival", 0)
        try:
            arrival_val = float(arrival)
        except (ValueError, TypeError):
            raise InvalidInputError(f"Arrival time for process '{pid_str}' must be numeric.", field="arrival")
        if arrival_val < 0:
            raise OutOfRangeError(f"Arrival time for process '{pid_str}' cannot be negative.", field="arrival")

        # Burst Time
        burst = p.get("burst")
        if burst is None:
            raise InvalidInputError(f"Burst time missing for process '{pid_str}'.", field="burst")
        try:
            burst_val = float(burst)
        except (ValueError, TypeError):
            raise InvalidInputError(f"Burst time for process '{pid_str}' must be numeric.", field="burst")
        if burst_val <= 0:
            raise OutOfRangeError(f"Burst time for process '{pid_str}' must be greater than 0.", field="burst")

        # Priority (lower number = higher priority, or standard integer)
        priority = p.get("priority", 0)
        try:
            priority_val = int(priority)
        except (ValueError, TypeError):
            raise InvalidInputError(f"Priority for process '{pid_str}' must be an integer.", field="priority")
        if priority_val < 0:
            raise OutOfRangeError(f"Priority for process '{pid_str}' cannot be negative.", field="priority")

        clean_processes.append({
            "pid": pid_str,
            "arrival": arrival_val,
            "burst": burst_val,
            "priority": priority_val
        })

    # Validate Quantum if Round Robin
    clean_quantum = None
    if quantum is not None:
        try:
            clean_quantum = float(quantum)
        except (ValueError, TypeError):
            raise InvalidInputError("Time quantum must be a positive number.", field="quantum")
        if clean_quantum <= 0:
            raise OutOfRangeError("Time quantum must be strictly greater than 0.", field="quantum")

    if algorithm == "Round Robin" and clean_quantum is None:
        raise InvalidInputError("Round Robin algorithm requires a valid positive time quantum.", field="quantum")

    if algorithm is not None and allowed_algorithms:
        if algorithm not in allowed_algorithms:
            raise InvalidInputError(
                f"Unknown CPU algorithm '{algorithm}'. Must be one of: {', '.join(allowed_algorithms)}.",
                field="algorithm"
            )

    return clean_processes, clean_quantum


# -----------------------------------------------------------------------------
# Page Replacement Validators
# -----------------------------------------------------------------------------

def validate_page_input(
    reference: Any,
    frames: Any,
    algorithm: Optional[str] = None,
    allowed_algorithms: Optional[List[str]] = None,
) -> Tuple[List[int], int]:
    """Validate and sanitize parameters for page replacement simulations.

    Returns:
        Tuple of (clean_reference, clean_frames)
    Raises:
        InvalidInputError, OutOfRangeError, EmptyInputError
    """
    # 1. Frames
    if not isinstance(frames, (int, float)) or isinstance(frames, bool):
        try:
            frames = int(frames)
        except (ValueError, TypeError):
            raise InvalidInputError("Number of frames must be an integer.", field="frames")
    frames = int(frames)
    if frames < 1 or frames > 100:
        raise OutOfRangeError("Number of page frames must be between 1 and 100.", field="frames")

    # 2. Reference string
    if reference is None:
        raise EmptyInputError("Reference string cannot be null.", field="reference")

    if isinstance(reference, str):
        parts = [p.strip() for p in reference.replace(" ", ",").split(",") if p.strip()]
        cleaned_ref: List[int] = []
        for p in parts:
            try:
                cleaned_ref.append(int(p))
            except ValueError:
                raise InvalidInputError(f"Invalid page number '{p}' in reference string.", field="reference")
        reference = cleaned_ref

    if not isinstance(reference, list):
        raise InvalidInputError("Reference string must be a list of integers.", field="reference")

    if len(reference) == 0:
        raise EmptyInputError("Reference string cannot be empty.", field="reference")

    if len(reference) > 1000:
        raise OutOfRangeError("Reference string length cannot exceed 1000 page accesses.", field="reference")

    clean_ref: List[int] = []
    for idx, page in enumerate(reference):
        if not isinstance(page, (int, float)) or isinstance(page, bool):
            try:
                page = int(page)
            except (ValueError, TypeError):
                raise InvalidInputError(f"Page at index {idx} ('{page}') must be an integer.", field="reference")
        page_int = int(page)
        if page_int < 0:
            raise OutOfRangeError(f"Page number at index {idx} cannot be negative ({page_int}).", field="reference")
        clean_ref.append(page_int)

    if algorithm is not None and allowed_algorithms:
        if algorithm not in allowed_algorithms:
            raise InvalidInputError(
                f"Unknown page algorithm '{algorithm}'. Must be one of: {', '.join(allowed_algorithms)}.",
                field="algorithm"
            )

    return clean_ref, frames


# -----------------------------------------------------------------------------
# Deadlock (Banker's) Validators
# -----------------------------------------------------------------------------

def validate_deadlock_input(
    available: Any,
    allocation: Any,
    max_matrix: Any,
) -> Tuple[List[int], Dict[str, List[int]], Dict[str, List[int]], int]:
    """Validate and sanitize Banker's algorithm matrices.

    Returns:
        Tuple of (clean_available, clean_allocation, clean_max, num_resources)
    Raises:
        InvalidInputError, OutOfRangeError, EmptyInputError
    """
    if available is None or not isinstance(available, list):
        raise InvalidInputError("Available resources must be a list of integers.", field="available")

    if len(available) == 0:
        raise EmptyInputError("Available resource vector cannot be empty.", field="available")

    num_resources = len(available)
    if num_resources > 20:
        raise OutOfRangeError("Number of resource types cannot exceed 20.", field="available")

    clean_available: List[int] = []
    for idx, r in enumerate(available):
        try:
            val = int(r)
        except (ValueError, TypeError):
            raise InvalidInputError(f"Available resource at index {idx} must be an integer.", field="available")
        if val < 0:
            raise OutOfRangeError(f"Available resource count at index {idx} cannot be negative ({val}).", field="available")
        clean_available.append(val)

    # Validate Allocation & Max dictionaries
    if not isinstance(allocation, dict) or not isinstance(max_matrix, dict):
        raise InvalidInputError("Allocation and Max matrices must be dictionaries keyed by PID.", field="allocation")

    if len(allocation) == 0 or len(max_matrix) == 0:
        raise EmptyInputError("Process allocation and max matrices cannot be empty.", field="allocation")

    if set(allocation.keys()) != set(max_matrix.keys()):
        raise InvalidInputError(
            "PIDs in Allocation and Max matrices do not match.",
            field="allocation"
        )

    clean_allocation: Dict[str, List[int]] = {}
    clean_max: Dict[str, List[int]] = {}

    for pid in allocation.keys():
        alloc_row = allocation[pid]
        max_row = max_matrix[pid]

        if not isinstance(alloc_row, list) or len(alloc_row) != num_resources:
            raise InvalidInputError(
                f"Allocation row for '{pid}' must have length {num_resources}.",
                field="allocation"
            )
        if not isinstance(max_row, list) or len(max_row) != num_resources:
            raise InvalidInputError(
                f"Max row for '{pid}' must have length {num_resources}.",
                field="max"
            )

        clean_alloc_row = []
        clean_max_row = []

        for r_idx in range(num_resources):
            try:
                a_val = int(alloc_row[r_idx])
                m_val = int(max_row[r_idx])
            except (ValueError, TypeError):
                raise InvalidInputError(f"Resource values for '{pid}' must be integers.", field="allocation")

            if a_val < 0 or m_val < 0:
                raise OutOfRangeError(f"Resource values for '{pid}' cannot be negative.", field="allocation")
            if a_val > m_val:
                raise OutOfRangeError(
                    f"Process '{pid}' has allocation {a_val} exceeding max claim {m_val} for resource {r_idx}.",
                    field="allocation"
                )

            clean_alloc_row.append(a_val)
            clean_max_row.append(m_val)

        clean_allocation[pid] = clean_alloc_row
        clean_max[pid] = clean_max_row

    return clean_available, clean_allocation, clean_max, num_resources


def validate_request_input(
    available: Any,
    allocation: Any,
    max_matrix: Any,
    pid: Any,
    request: Any,
) -> Tuple[List[int], Dict[str, List[int]], Dict[str, List[int]], str, List[int]]:
    """Validate resource request payload against safety structures."""
    clean_avail, clean_alloc, clean_max, num_res = validate_deadlock_input(
        available, allocation, max_matrix
    )

    if pid is None or str(pid) not in clean_alloc:
        raise InvalidInputError(f"Process PID '{pid}' does not exist in allocation matrix.", field="pid")
    pid_str = str(pid)

    if request is None or not isinstance(request, list) or len(request) != num_res:
        raise InvalidInputError(f"Request vector must contain exactly {num_res} resource quantities.", field="request")

    clean_req: List[int] = []
    for idx, r in enumerate(request):
        try:
            val = int(r)
        except (ValueError, TypeError):
            raise InvalidInputError(f"Request amount at index {idx} must be an integer.", field="request")
        if val < 0:
            raise OutOfRangeError(f"Request amount at index {idx} cannot be negative ({val}).", field="request")
        clean_req.append(val)

    # Check if request exceeds Need = Max - Allocation
    for idx in range(num_res):
        need_val = clean_max[pid_str][idx] - clean_alloc[pid_str][idx]
        if clean_req[idx] > need_val:
            raise OutOfRangeError(
                f"Process '{pid_str}' requested {clean_req[idx]} units of resource {idx}, "
                f"which exceeds its maximum remaining need of {need_val}.",
                field="request"
            )

    return clean_avail, clean_alloc, clean_max, pid_str, clean_req
