"""Headless Static Chart Generator for Simulation Reports.

Uses Matplotlib configured with the non-interactive 'Agg' backend to generate
clean, professional PNG plots saved directly into output/charts/.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import matplotlib
# Enforce headless rendering backend for WSL2 / server execution
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHARTS_DIR = PROJECT_ROOT / "output" / "charts"


def _ensure_charts_dir() -> Path:
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    return CHARTS_DIR


def plot_disk_comparison(
    comparison_results: Dict[str, Any],
    filename: str = "disk_comparison.png",
) -> Path:
    """Generate a high-contrast bar chart comparing disk scheduling head movements."""
    _ensure_charts_dir()
    output_path = CHARTS_DIR / filename

    algorithms = list(comparison_results.keys())
    movements = [comparison_results[alg]["total_movement"] for alg in algorithms]

    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)

    # Accent color mapping
    colors = ["#4f8ef7" if m != min(movements) else "#2ec99a" for m in movements]
    bars = ax.bar(algorithms, movements, color=colors, edgecolor="#ffffff", linewidth=0.8, width=0.55)

    ax.set_title("Disk Scheduling Comparison - Total Head Movement (Cylinders)", fontsize=13, pad=15, fontweight="bold", color="#f0f4fc")
    ax.set_xlabel("Algorithm", fontsize=11, labelpad=10, color="#acc1e7")
    ax.set_ylabel("Total Head Travel (Cylinders)", fontsize=11, labelpad=10, color="#acc1e7")
    ax.grid(axis="y", linestyle="--", alpha=0.25, color="#6496e2")

    for bar, val in zip(bars, movements):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + (max(movements) * 0.02),
            f"{val}",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
            color="#ffffff"
        )

    plt.tight_layout()
    plt.savefig(str(output_path), facecolor="#08101a")
    plt.close(fig)
    return output_path


def plot_cpu_comparison(
    comparison_results: Dict[str, Any],
    filename: str = "cpu_comparison.png",
) -> Path:
    """Generate comparative grouped bar chart for CPU turnaround and waiting times."""
    _ensure_charts_dir()
    output_path = CHARTS_DIR / filename

    algorithms = list(comparison_results.keys())
    waiting_times = [comparison_results[alg]["avg_waiting"] for alg in algorithms]
    turnaround_times = [comparison_results[alg]["avg_turnaround"] for alg in algorithms]

    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)

    import numpy as np
    x = np.arange(len(algorithms))
    width = 0.35

    rects1 = ax.bar(x - width/2, waiting_times, width, label="Avg Waiting Time", color="#8a6df2", edgecolor="#ffffff", linewidth=0.6)
    rects2 = ax.bar(x + width/2, turnaround_times, width, label="Avg Turnaround Time", color="#4f8ef7", edgecolor="#ffffff", linewidth=0.6)

    ax.set_title("CPU Scheduling Comparison - Latency Metrics", fontsize=13, pad=15, fontweight="bold", color="#f0f4fc")
    ax.set_xlabel("Algorithm", fontsize=11, labelpad=10, color="#acc1e7")
    ax.set_ylabel("Time Units", fontsize=11, labelpad=10, color="#acc1e7")
    ax.set_xticks(x)
    ax.set_xticklabels(algorithms, fontsize=10)
    ax.legend(frameon=True, facecolor="#142240", edgecolor="#ffffff", fontsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.25, color="#6496e2")

    plt.tight_layout()
    plt.savefig(str(output_path), facecolor="#08101a")
    plt.close(fig)
    return output_path


def plot_page_comparison(
    comparison_results: Dict[str, Any],
    filename: str = "pages_comparison.png",
) -> Path:
    """Generate comparative bar chart for Page Replacement fault and hit counts."""
    _ensure_charts_dir()
    output_path = CHARTS_DIR / filename

    algorithms = list(comparison_results.keys())
    faults = [comparison_results[alg]["total_faults"] for alg in algorithms]
    hits = [comparison_results[alg]["total_hits"] for alg in algorithms]

    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)

    import numpy as np
    x = np.arange(len(algorithms))
    width = 0.35

    ax.bar(x - width/2, faults, width, label="Page Faults", color="#f08a8a", edgecolor="#ffffff", linewidth=0.6)
    ax.bar(x + width/2, hits, width, label="Page Hits", color="#2ec99a", edgecolor="#ffffff", linewidth=0.6)

    ax.set_title("Page Replacement Comparison - Faults vs. Hits", fontsize=13, pad=15, fontweight="bold", color="#f0f4fc")
    ax.set_xlabel("Algorithm", fontsize=11, labelpad=10, color="#acc1e7")
    ax.set_ylabel("Reference Count", fontsize=11, labelpad=10, color="#acc1e7")
    ax.set_xticks(x)
    ax.set_xticklabels(algorithms, fontsize=10)
    ax.legend(frameon=True, facecolor="#142240", edgecolor="#ffffff", fontsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.25, color="#6496e2")

    plt.tight_layout()
    plt.savefig(str(output_path), facecolor="#08101a")
    plt.close(fig)
    return output_path
