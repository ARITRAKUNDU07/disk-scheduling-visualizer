#!/usr/bin/env bash
# ==============================================================================
# collect_logs.sh - Aggregates & Analyzes OSRM Activity Log
# Summarizes log event counts by module, error tallies, and recent events.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/logs/activity.log"

echo "=================================================================="
echo "               OSRM AUDIT LOG SUMMARY REPORT                      "
echo "=================================================================="

if [ ! -f "${LOG_FILE}" ]; then
    echo "Notice: Activity log does not exist yet at ${LOG_FILE}."
    echo "Run a simulation or launch the server to generate activity."
    exit 0
fi

TOTAL_LINES=$(wc -l < "${LOG_FILE}" || echo 0)
echo "Log File Path : ${LOG_FILE}"
echo "Total Records : ${TOTAL_LINES}"
echo ""

echo "--- [1] EVENT COUNTS BY SEVERITY LEVEL ---"
echo "INFO    : $(grep -c " | INFO" "${LOG_FILE}" 2>/dev/null || true)"
echo "WARNING : $(grep -c " | WARNING" "${LOG_FILE}" 2>/dev/null || true)"
echo "ERROR   : $(grep -c " | ERROR" "${LOG_FILE}" 2>/dev/null || true)"
echo "DEBUG   : $(grep -c " | DEBUG" "${LOG_FILE}" 2>/dev/null || true)"
echo ""

echo "--- [2] EVENT COUNTS BY MODULE ---"
echo "API Server       : $(grep -c -E "server|api" "${LOG_FILE}" 2>/dev/null || true)"
echo "Disk Scheduling  : $(grep -c -E "disk|Disk" "${LOG_FILE}" 2>/dev/null || true)"
echo "CPU Scheduling   : $(grep -c -E "cpu|CPU" "${LOG_FILE}" 2>/dev/null || true)"
echo "Page Replacement : $(grep -c -E "pages|Pages" "${LOG_FILE}" 2>/dev/null || true)"
echo "Deadlock Banker  : $(grep -c -E "deadlock|Deadlock" "${LOG_FILE}" 2>/dev/null || true)"
echo "Bash Bridge      : $(grep -c -E "bash_bridge" "${LOG_FILE}" 2>/dev/null || true)"
echo "Reports          : $(grep -c -E "report" "${LOG_FILE}" 2>/dev/null || true)"
echo ""

echo "--- [3] LAST 10 AUDIT LOG ENTRIES ---"
if [ "${TOTAL_LINES}" -gt 0 ]; then
    tail -n 10 "${LOG_FILE}"
else
    echo "(Log file is empty)"
fi
echo "=================================================================="
