#!/usr/bin/env bash
# ==============================================================================
# run.sh - Universal Launcher for OSRM
# Usage:
#   ./run.sh         -> Prompts user to select CLI terminal menu or Web dashboard
#   ./run.sh web     -> Boots the Web Dashboard directly
#   ./run.sh cli     -> Boots the Terminal CLI Menu directly
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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

MODE="${1:-}"

if [ -z "${MODE}" ]; then
    echo "=================================================================="
    echo "          OS RESOURCE MANAGER SIMULATOR (OSRM)                    "
    echo "   Operating Systems Laboratory (ENSC-351), B.Tech Semester V     "
    echo "=================================================================="
    echo "Select user interface mode:"
    echo "  [1] Web Dashboard (Peak Glow Themed Browser UI)"
    echo "  [2] Interactive Terminal Menu (CLI mode)"
    echo "  [0] Exit"
    echo "=================================================================="
    read -rp "Enter choice [1-2, default=1]: " CHOICE
    CHOICE="${CHOICE:-1}"

    case "${CHOICE}" in
        1|w|web|Web)
            MODE="web"
            ;;
        2|c|cli|CLI)
            MODE="cli"
            ;;
        0|q|quit|exit)
            echo "Exiting."
            exit 0
            ;;
        *)
            echo "Invalid choice. Defaulting to Web Dashboard."
            MODE="web"
            ;;
    esac
fi

case "${MODE}" in
    web|--web)
        exec "${SCRIPT_DIR}/serve.sh" 8080
        ;;
    cli|--cli)
        exec "${PYTHON_BIN}" "${SCRIPT_DIR}/main.py" --cli
        ;;
    test|--test)
        exec "${SCRIPT_DIR}/run_tests.sh"
        ;;
    *)
        echo "Usage: $0 [web|cli|test]"
        exit 1
        ;;
esac
