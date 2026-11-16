"""API Route Dispatcher and Endpoint Handlers for OSRM.

Routes incoming HTTP requests to core algorithms, handles schema validation,
translates custom domain exceptions to HTTP 400 JSON errors, and interfaces
with the Bash automation bridge.
"""

from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple

from core.bash_bridge import run_script
from core.cpu_scheduling import CPU_ALGORITHMS, compare_all_cpu, run_cpu_simulation
from core.deadlock import evaluate_resource_request, evaluate_safety
from core.disk_scheduling import DISK_ALGORITHMS, compare_all_disk, run_disk_simulation
from core.logger import log_event
from core.page_replacement import PAGE_ALGORITHMS, compare_all_pages, demonstrate_belady, run_page_simulation
from core.report import generate_full_report, parse_sample_dataset
from core.serialization import to_dict
from core.validators import OSRMError

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def get_meta() -> Dict[str, Any]:
    """Retrieve metadata on available algorithms, default configurations, and limits."""
    return {
        "modules": {
            "disk": {
                "algorithms": list(DISK_ALGORITHMS.keys()),
                "default_algorithm": "FCFS",
                "defaults": {
                    "head": 53,
                    "size": 200,
                    "direction": "left",
                    "ms_per_cyl": 1.0,
                    "count_jump": True,
                },
                "limits": {
                    "max_cylinders": 1000000,
                    "max_requests": 500,
                }
            },
            "cpu": {
                "algorithms": list(CPU_ALGORITHMS.keys()),
                "default_algorithm": "FCFS",
                "defaults": {
                    "quantum": 4.0,
                },
                "limits": {
                    "max_processes": 100,
                }
            },
            "pages": {
                "algorithms": list(PAGE_ALGORITHMS.keys()),
                "default_algorithm": "FIFO",
                "defaults": {
                    "frames": 3,
                },
                "limits": {
                    "max_frames": 100,
                    "max_references": 1000,
                }
            },
            "deadlock": {
                "algorithms": ["Banker's Safety", "Resource Request"],
                "limits": {
                    "max_resources": 20,
                    "max_processes": 50,
                }
            }
        }
    }


def get_samples(module: str) -> Dict[str, Any]:
    """Retrieve parsed sample and large datasets for a specific subsystem."""
    mod_clean = module.strip().lower()
    valid_modules = ("disk", "cpu", "pages", "banker", "deadlock")
    if mod_clean == "deadlock":
        mod_clean = "banker"

    if mod_clean not in ("disk", "cpu", "pages", "banker"):
        raise OSRMError(f"Unknown sample module '{module}'. Valid: disk, cpu, pages, banker.", field="module")

    data_dir = PROJECT_ROOT / "data"
    sample_file = data_dir / f"sample_{mod_clean}.txt"
    large_file = data_dir / f"large_{mod_clean}.txt"

    sample_data = parse_sample_dataset(sample_file) if sample_file.exists() else {}
    large_data = parse_sample_dataset(large_file) if large_file.exists() else {}

    return {
        "module": mod_clean,
        "sample": sample_data,
        "large": large_data,
    }


def get_summary() -> Dict[str, Any]:
    """Return executive best-algorithm headlines across all modules using sample datasets."""
    data_dir = PROJECT_ROOT / "data"

    # Disk summary
    disk_data = parse_sample_dataset(data_dir / "sample_disk.txt")
    disk_comp = compare_all_disk(
        requests=disk_data["requests"],
        head=disk_data["head"],
        size=disk_data["size"],
        direction=disk_data.get("direction", "left"),
        count_jump=True,
        ms_per_cyl=disk_data.get("ms_per_cyl", 1.0)
    )
    best_disk_alg = disk_comp["best_algorithms"][0]
    best_disk_res = disk_comp["results"][best_disk_alg]

    # CPU summary
    cpu_data = parse_sample_dataset(data_dir / "sample_cpu.txt")
    cpu_comp = compare_all_cpu(
        processes=cpu_data["processes"],
        quantum=cpu_data.get("quantum", 4.0)
    )
    best_cpu_alg = cpu_comp["best_algorithms"][0]
    best_cpu_res = cpu_comp["results"][best_cpu_alg]

    # Pages summary
    pages_data = parse_sample_dataset(data_dir / "sample_pages.txt")
    pages_comp = compare_all_pages(
        reference=pages_data["reference"],
        frames=pages_data["frames"]
    )
    best_pages_alg = pages_comp["best_algorithms"][0]
    best_pages_res = pages_comp["results"][best_pages_alg]

    # Deadlock summary
    banker_data = parse_sample_dataset(data_dir / "sample_banker.txt")
    deadlock_res = evaluate_safety(
        available=banker_data["available"],
        allocation=banker_data["allocation"],
        max_matrix=banker_data["max"]
    )

    return {
        "disk": {
            "best_algorithm": best_disk_alg,
            "headline_value": best_disk_res["total_movement"],
            "unit": "cyl",
            "caption": f"Avg seek {best_disk_res['avg_seek']} · Seek time {best_disk_res['seek_time_ms']} ms",
            "all_movements": {k: v["total_movement"] for k, v in disk_comp["results"].items()},
            "sequence": best_disk_res["sequence"],
        },
        "cpu": {
            "best_algorithm": best_cpu_alg,
            "headline_value": best_cpu_res["avg_waiting"],
            "unit": "units",
            "caption": f"Avg turnaround {best_cpu_res['avg_turnaround']} · Util {best_cpu_res['cpu_utilization']}%",
            "all_waiting": {k: v["avg_waiting"] for k, v in cpu_comp["results"].items()},
            "gantt": best_cpu_res["gantt"],
        },
        "pages": {
            "best_algorithm": best_pages_alg,
            "headline_value": best_pages_res["total_faults"],
            "unit": "faults",
            "caption": f"Hit ratio {best_pages_res['hit_ratio']*100:.1f}% ({best_pages_res['total_hits']} hits)",
            "all_faults": {k: v["total_faults"] for k, v in pages_comp["results"].items()},
        },
        "deadlock": {
            "is_safe": deadlock_res.is_safe,
            "headline_value": "SAFE" if deadlock_res.is_safe else "UNSAFE",
            "unit": "state",
            "caption": f"Sequence: {' -> '.join(deadlock_res.safe_sequence)}",
            "safe_sequence": deadlock_res.safe_sequence,
            "available": banker_data["available"],
        }
    }


def handle_disk_run(body: Dict[str, Any]) -> Dict[str, Any]:
    requests = body.get("requests")
    head = body.get("head")
    size = body.get("size")
    direction = body.get("direction", "left")
    algorithm = body.get("algorithm", "FCFS")
    count_jump = bool(body.get("count_jump", True))
    ms_per_cyl = body.get("ms_per_cyl", 1.0)

    res = run_disk_simulation(
        requests=requests,
        head=head,
        size=size,
        direction=direction,
        algorithm=algorithm,
        count_jump=count_jump,
        ms_per_cyl=ms_per_cyl,
    )
    return res.to_dict()


def handle_disk_compare(body: Dict[str, Any]) -> Dict[str, Any]:
    requests = body.get("requests")
    head = body.get("head")
    size = body.get("size")
    direction = body.get("direction", "left")
    count_jump = bool(body.get("count_jump", True))
    ms_per_cyl = body.get("ms_per_cyl", 1.0)

    return compare_all_disk(
        requests=requests,
        head=head,
        size=size,
        direction=direction,
        count_jump=count_jump,
        ms_per_cyl=ms_per_cyl,
    )


def handle_cpu_run(body: Dict[str, Any]) -> Dict[str, Any]:
    processes = body.get("processes")
    algorithm = body.get("algorithm", "FCFS")
    quantum = body.get("quantum", 4.0)

    res = run_cpu_simulation(processes, algorithm, quantum)
    return res.to_dict()


def handle_cpu_compare(body: Dict[str, Any]) -> Dict[str, Any]:
    processes = body.get("processes")
    quantum = body.get("quantum", 4.0)

    return compare_all_cpu(processes, quantum)


def handle_pages_run(body: Dict[str, Any]) -> Dict[str, Any]:
    reference = body.get("reference")
    frames = body.get("frames")
    algorithm = body.get("algorithm", "FIFO")

    res = run_page_simulation(reference, frames, algorithm)
    return res.to_dict()


def handle_pages_compare(body: Dict[str, Any]) -> Dict[str, Any]:
    reference = body.get("reference")
    frames = body.get("frames")

    return compare_all_pages(reference, frames)


def handle_pages_belady(body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return demonstrate_belady()


def handle_deadlock_safety(body: Dict[str, Any]) -> Dict[str, Any]:
    available = body.get("available")
    allocation = body.get("allocation")
    max_matrix = body.get("max")

    res = evaluate_safety(available, allocation, max_matrix)
    return res.to_dict()


def handle_deadlock_request(body: Dict[str, Any]) -> Dict[str, Any]:
    available = body.get("available")
    allocation = body.get("allocation")
    max_matrix = body.get("max")
    pid = body.get("pid")
    request = body.get("request")

    res = evaluate_resource_request(available, allocation, max_matrix, pid, request)
    return res.to_dict()


def handle_report_generate(body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    scale = "large"
    if body and "dataset" in body:
        scale = str(body["dataset"]).strip().lower()
    path, md = generate_full_report(scale)
    return {
        "report_path": str(path),
        "markdown": md,
        "dataset": scale,
    }


def handle_logs_summary(body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    res = run_script("collect_logs.sh")
    return {
        "stdout": res["stdout"],
        "stderr": res["stderr"],
        "return_code": res["return_code"],
        "success": res["success"],
    }


def handle_sysinfo(body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    res = run_script("sysinfo.sh")
    return {
        "stdout": res["stdout"],
        "stderr": res["stderr"],
        "return_code": res["return_code"],
        "success": res["success"],
    }


def handle_tests_run(body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    res = run_script("run_tests.sh", timeout_sec=60)
    return {
        "stdout": res["stdout"],
        "stderr": res["stderr"],
        "return_code": res["return_code"],
        "success": res["success"],
        "passed": (res["return_code"] == 0),
    }
