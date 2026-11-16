#!/usr/bin/env bash
# ==============================================================================
# run_tests.sh - Comprehensive Test Runner for OSRM
# Discovers and runs all unittest suites, tees output to output/test_results.txt,
# and emits structured PASS/FAIL exit codes.
# ==============================================================================

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "${SCRIPT_DIR}/output"
OUTPUT_FILE="${SCRIPT_DIR}/output/test_results.txt"

echo "=================================================================="
echo "          STARTING OSRM AUTOMATED VERIFICATION SUITE              "
echo "=================================================================="
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Target Directory: ${SCRIPT_DIR}"
echo ""

# Determine working python command
PYTHON_BIN=""
if python3 --version >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif python --version >/dev/null 2>&1; then
    PYTHON_BIN="python"
elif py -3 --version >/dev/null 2>&1; then
    PYTHON_BIN="py -3"
else
    echo "Error: No operational Python 3 interpreter found on PATH." >&2
    exit 1
fi

# Run test discovery and tee to output file
set +e
"${PYTHON_BIN}" -m unittest discover -s "${SCRIPT_DIR}/tests" -p "test_*.py" -v 2>&1 | tee "${OUTPUT_FILE}"
TEST_EXIT_CODE=$?
set -e

echo ""
echo "=================================================================="
if [ ${TEST_EXIT_CODE} -eq 0 ]; then
    echo "                 >>> VERIFICATION STATUS: PASS <<<                "
    echo "All unit and API verification assertions succeeded."
else
    echo "                 >>> VERIFICATION STATUS: FAIL <<<                "
    echo "One or more test assertions failed. Review ${OUTPUT_FILE}."
fi
echo "Results logged to: ${OUTPUT_FILE}"
echo "=================================================================="

exit ${TEST_EXIT_CODE}
