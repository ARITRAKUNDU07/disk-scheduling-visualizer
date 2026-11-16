#!/usr/bin/env bash
# ==============================================================================
# setup.sh - Initial Environment Setup for OSRM
# Ensures directories exist, verifies Python 3, and installs dependencies.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=================================================================="
echo "          OS RESOURCE MANAGER SIMULATOR (OSRM) SETUP              "
echo "=================================================================="

# 1. Ensure required directory structures exist
echo "[1/3] Ensuring required directories..."
mkdir -p "${SCRIPT_DIR}/logs"
mkdir -p "${SCRIPT_DIR}/output/charts"
mkdir -p "${SCRIPT_DIR}/output/traces"
mkdir -p "${SCRIPT_DIR}/output/reports"
mkdir -p "${SCRIPT_DIR}/data"
echo "      Directories verified."

# 2. Check Python 3 availability
echo "[2/3] Checking Python interpreter..."
PYTHON_BIN=""
if python3 --version >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif python --version >/dev/null 2>&1; then
    PYTHON_BIN="python"
elif py -3 --version >/dev/null 2>&1; then
    PYTHON_BIN="py"
else
    echo "Error: Python 3 is required but was not found on PATH." >&2
    exit 1
fi
PY_VER=$("${PYTHON_BIN}" --version 2>&1)
echo "      Found: ${PY_VER}"

# 3. Check and install matplotlib for static report charts
echo "[3/3] Checking Python dependencies (matplotlib)..."
if "${PYTHON_BIN}" -c "import matplotlib" >/dev/null 2>&1; then
    echo "      matplotlib is already installed and available."
else
    echo "      Installing matplotlib..."
    if "${PYTHON_BIN}" -m pip install matplotlib --break-system-packages 2>/dev/null; then
        echo "      Successfully installed matplotlib."
    elif "${PYTHON_BIN}" -m pip install matplotlib; then
        echo "      Successfully installed matplotlib."
    else
        echo "Warning: pip install failed. Please manually install matplotlib if reports require PNG figures." >&2
    fi
fi

echo "=================================================================="
echo "Setup completed successfully! Run './run.sh' to launch OSRM."
echo "=================================================================="
