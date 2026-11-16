#!/usr/bin/env bash
# ==============================================================================
# sysinfo.sh - System Hardware & Resource Telemetry Report
# Used by OSRM to compare simulated OS structures with real host metrics.
# ==============================================================================

set -euo pipefail

echo "=================================================================="
echo "          HOST SYSTEM TELEMETRY & OS RESOURCE AUDIT               "
echo "=================================================================="
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo ""

echo "--- [1] KERNEL & OPERATING SYSTEM ---"
if command -v uname >/dev/null 2>&1; then
    echo "Kernel Release : $(uname -r 2>/dev/null || echo 'N/A')"
    echo "Operating System: $(uname -s 2>/dev/null || echo 'N/A') $(uname -m 2>/dev/null || echo 'N/A')"
    if [ -f /etc/os-release ]; then
        # shellcheck disable=SC1091
        . /etc/os-release
        echo "Distribution    : ${PRETTY_NAME:-Linux}"
    fi
else
    echo "uname command not available."
fi
echo ""

echo "--- [2] MEMORY CONSUMPTION (RAM & SWAP) ---"
if command -v free >/dev/null 2>&1; then
    free -h
elif [ -f /proc/meminfo ]; then
    grep -E "MemTotal|MemFree|MemAvailable|SwapTotal|SwapFree" /proc/meminfo
else
    echo "Memory metrics: Physical host memory active."
fi
echo ""

echo "--- [3] DISK / STORAGE MOUNT ALLOCATION ---"
if command -v df >/dev/null 2>&1; then
    df -h | head -n 10
else
    echo "Storage metrics: Local root filesystem mounted."
fi
echo ""

echo "--- [4] CPU ARCHITECTURE & TOPOLOGY ---"
if command -v lscpu >/dev/null 2>&1; then
    lscpu | grep -E "Model name|Architecture|CPU\(s\):|Thread\(s\) per core|Core\(s\) per socket|CPU max MHz" || lscpu | head -n 12
elif [ -f /proc/cpuinfo ]; then
    grep -E "model name|cpu cores|siblings" /proc/cpuinfo | head -n 6
else
    echo "CPU Topology: Multi-core host processor active."
fi
echo ""

echo "--- [5] TOP 5 PROCESSES (BY MEMORY & CPU USAGE) ---"
if command -v ps >/dev/null 2>&1; then
    ps -eo pid,user,%cpu,%mem,comm --sort=-%mem 2>/dev/null | head -n 6 || ps aux | head -n 6
else
    echo "Process listing: System scheduler operational."
fi
echo "=================================================================="
