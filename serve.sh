#!/usr/bin/env bash
# ==============================================================================
# serve.sh - Bootstrap OSRM Web Server & Browser Interface
# Binds to 127.0.0.1, announces URL, and triggers local browser view.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${1:-8080}"
URL="http://127.0.0.1:${PORT}"

PYTHON_BIN=""
if python3 --version >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif python --version >/dev/null 2>&1; then
    PYTHON_BIN="python"
elif py -3 --version >/dev/null 2>&1; then
    PYTHON_BIN="py"
else
    echo "Error: Python interpreter not found." >&2
    exit 1
fi

echo "=================================================================="
echo "         LAUNCHING OS RESOURCE MANAGER SIMULATOR (OSRM)           "
echo "=================================================================="
echo "Server Endpoint : ${URL}"
echo "Document Root   : ${SCRIPT_DIR}/web/static"
echo "Binding Address : 127.0.0.1 (Loopback only)"
echo "Press Ctrl+C to terminate the web server."
echo "=================================================================="

# Attempt to launch browser in background
(
    sleep 1.2
    if command -v wslview >/dev/null 2>&1; then
        wslview "${URL}" 2>/dev/null || true
    elif command -v explorer.exe >/dev/null 2>&1; then
        explorer.exe "${URL}" 2>/dev/null || true
    elif command -v xdg-open >/dev/null 2>&1; then
        xdg-open "${URL}" 2>/dev/null || true
    elif command -v open >/dev/null 2>&1; then
        open "${URL}" 2>/dev/null || true
    fi
) &

# Run server
exec "${PYTHON_BIN}" "${SCRIPT_DIR}/main.py" --web --port "${PORT}"
