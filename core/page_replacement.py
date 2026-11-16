"""Page Replacement Algorithms Subsystem for OSRM.

Implements pure deterministic algorithms for:
- FIFO (First-In, First-Out)
- LRU (Least Recently Used)
- Optimal (Belady's Optimal / MIN Algorithm)
- Belady's Anomaly Analysis and Demonstration Engine

Returns step-by-step frame residency matrices, page fault indicators, replaced pages,
and hit/fault efficiency ratios.
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

from core.serialization import to_dict
from core.validators import validate_page_input


@dataclass
class PageStep:
    """Individual memory reference access event."""
    step: int
    page: int
    frames: List[Optional[int]]
    is_fault: bool
    replaced_page: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return to_dict(self)


@dataclass
class PageResult:
    """Consolidated outcome of a page replacement algorithm simulation."""
    algorithm: str
    frames_count: int
    reference_string: List[int]
    steps: List[PageStep]
    total_faults: int
    total_hits: int
    fault_ratio: float
    hit_ratio: float

    def to_dict(self) -> Dict[str, Any]:
        return to_dict(self)


# -----------------------------------------------------------------------------
# Page Replacement Implementations
# -----------------------------------------------------------------------------

def run_fifo_pages(reference: List[int], frames: int) -> PageResult:
    """First-In, First-Out (FIFO) Page Replacement."""
    allocated_frames: List[Optional[int]] = [None] * frames
    fifo_queue: List[int] = []  # tracks insertion order
    steps: List[PageStep] = []
    faults = 0
    hits = 0

    for idx, page in enumerate(reference, start=1):
        if page in allocated_frames:
            hits += 1
            steps.append(PageStep(
                step=idx,
                page=page,
                frames=list(allocated_frames),
                is_fault=False,
                replaced_page=None
            ))
        else:
            faults += 1
            replaced = None
            if None in allocated_frames:
                # Fill first unoccupied frame
                empty_idx = allocated_frames.index(None)
                allocated_frames[empty_idx] = page
                fifo_queue.append(page)
            else:
                # Evict oldest resident page
                oldest_page = fifo_queue.pop(0)
                replaced = oldest_page
                frame_idx = allocated_frames.index(oldest_page)
                allocated_frames[frame_idx] = page
                fifo_queue.append(page)

            steps.append(PageStep(
                step=idx,
                page=page,
                frames=list(allocated_frames),
                is_fault=True,
                replaced_page=replaced
            ))

    total_refs = max(1, len(reference))
    fault_ratio = round(faults / total_refs, 4)
    hit_ratio = round(hits / total_refs, 4)

    return PageResult(
        algorithm="FIFO",
        frames_count=frames,
        reference_string=reference,
        steps=steps,
        total_faults=faults,
        total_hits=hits,
        fault_ratio=fault_ratio,
        hit_ratio=hit_ratio
    )


def run_lru_pages(reference: List[int], frames: int) -> PageResult:
    """Least Recently Used (LRU) Page Replacement."""
    allocated_frames: List[Optional[int]] = [None] * frames
    last_access: Dict[int, int] = {}  # page -> step_index
    steps: List[PageStep] = []
    faults = 0
    hits = 0

    for idx, page in enumerate(reference, start=1):
        if page in allocated_frames:
            hits += 1
            last_access[page] = idx
            steps.append(PageStep(
                step=idx,
                page=page,
                frames=list(allocated_frames),
                is_fault=False,
                replaced_page=None
            ))
        else:
            faults += 1
            replaced = None
            if None in allocated_frames:
                empty_idx = allocated_frames.index(None)
                allocated_frames[empty_idx] = page
            else:
                # Evict resident page with lowest last_access step
                resident_pages = [p for p in allocated_frames if p is not None]
                lru_page = min(resident_pages, key=lambda p: last_access.get(p, -1))
                replaced = lru_page
                frame_idx = allocated_frames.index(lru_page)
                allocated_frames[frame_idx] = page

            last_access[page] = idx
            steps.append(PageStep(
                step=idx,
                page=page,
                frames=list(allocated_frames),
                is_fault=True,
                replaced_page=replaced
            ))

    total_refs = max(1, len(reference))
    fault_ratio = round(faults / total_refs, 4)
    hit_ratio = round(hits / total_refs, 4)

    return PageResult(
        algorithm="LRU",
        frames_count=frames,
        reference_string=reference,
        steps=steps,
        total_faults=faults,
        total_hits=hits,
        fault_ratio=fault_ratio,
        hit_ratio=hit_ratio
    )


def run_optimal_pages(reference: List[int], frames: int) -> PageResult:
    """Optimal (Belady's MIN) Page Replacement."""
    allocated_frames: List[Optional[int]] = [None] * frames
    steps: List[PageStep] = []
    faults = 0
    hits = 0
    n = len(reference)

    for idx, page in enumerate(reference, start=1):
        if page in allocated_frames:
            hits += 1
            steps.append(PageStep(
                step=idx,
                page=page,
                frames=list(allocated_frames),
                is_fault=False,
                replaced_page=None
            ))
        else:
            faults += 1
            replaced = None
            if None in allocated_frames:
                empty_idx = allocated_frames.index(None)
                allocated_frames[empty_idx] = page
            else:
                # Find page that will not be referenced for the longest time
                resident_pages = [p for p in allocated_frames if p is not None]
                future_sub = reference[idx:]  # remaining accesses after current step

                furthest_page = resident_pages[0]
                furthest_distance = -1

                for p in resident_pages:
                    if p not in future_sub:
                        # Page never accessed again; perfect candidate to evict
                        furthest_page = p
                        furthest_distance = float("inf")
                        break
                    else:
                        first_next_idx = future_sub.index(p)
                        if first_next_idx > furthest_distance:
                            furthest_distance = first_next_idx
                            furthest_page = p

                replaced = furthest_page
                frame_idx = allocated_frames.index(furthest_page)
                allocated_frames[frame_idx] = page

            steps.append(PageStep(
                step=idx,
                page=page,
                frames=list(allocated_frames),
                is_fault=True,
                replaced_page=replaced
            ))

    total_refs = max(1, len(reference))
    fault_ratio = round(faults / total_refs, 4)
    hit_ratio = round(hits / total_refs, 4)

    return PageResult(
        algorithm="Optimal",
        frames_count=frames,
        reference_string=reference,
        steps=steps,
        total_faults=faults,
        total_hits=hits,
        fault_ratio=fault_ratio,
        hit_ratio=hit_ratio
    )


PAGE_ALGORITHMS: Dict[str, Callable[[List[int], int], PageResult]] = {
    "FIFO": run_fifo_pages,
    "LRU": run_lru_pages,
    "Optimal": run_optimal_pages,
}


def run_page_simulation(
    reference: List[int],
    frames: int,
    algorithm: str = "FIFO",
) -> PageResult:
    """Execute single page replacement simulation with parameter validation."""
    clean_ref, clean_f = validate_page_input(
        reference, frames, algorithm, list(PAGE_ALGORITHMS.keys())
    )
    solver = PAGE_ALGORITHMS[algorithm]
    return solver(clean_ref, clean_f)


def compare_all_pages(reference: List[int], frames: int) -> Dict[str, Any]:
    """Execute FIFO, LRU, and Optimal on identical reference sequence and compare."""
    clean_ref, clean_f = validate_page_input(reference, frames)

    results: Dict[str, Any] = {}
    best_faults = float("inf")
    best_algorithms: List[str] = []

    for name, solver in PAGE_ALGORITHMS.items():
        res = solver(clean_ref, clean_f)
        res_dict = res.to_dict()
        results[name] = res_dict

        if res.total_faults < best_faults:
            best_faults = res.total_faults
            best_algorithms = [name]
        elif res.total_faults == best_faults:
            best_algorithms.append(name)

    from core.metrics import generate_page_analysis
    analysis_text = generate_page_analysis(results)

    return {
        "results": results,
        "best_algorithms": best_algorithms,
        "best_faults": best_faults,
        "analysis": analysis_text,
    }


def demonstrate_belady() -> Dict[str, Any]:
    """Demonstrate Belady's Anomaly using the standard verified benchmark string.

    Benchmark string: 1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5
    - FIFO with 3 frames: 9 page faults
    - FIFO with 4 frames: 10 page faults (Anomalous increase!)
    """
    belady_string = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]
    res_3 = run_fifo_pages(belady_string, 3)
    res_4 = run_fifo_pages(belady_string, 4)

    return {
        "reference_string": belady_string,
        "frames_3_result": res_3.to_dict(),
        "frames_4_result": res_4.to_dict(),
        "faults_3_frames": res_3.total_faults,
        "faults_4_frames": res_4.total_faults,
        "is_anomaly_demonstrated": res_4.total_faults > res_3.total_faults,
        "explanation": (
            f"Under FIFO replacement with reference string {belady_string}, allocating 3 frames results in "
            f"{res_3.total_faults} page faults, whereas increasing physical memory to 4 frames results in "
            f"{res_4.total_faults} page faults. This demonstrates Belady's Anomaly: allocating additional page frames "
            f"counter-intuitively increases total page faults under FIFO because FIFO is not a stack algorithm."
        )
    }
