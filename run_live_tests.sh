#!/bin/bash
# Run the full live test suite against Railway + Vercel deployments.
#
# Usage:
#   ./run_live_tests.sh               # run all tests
#   ./run_live_tests.sh test_cors     # run one module
#   ./run_live_tests.sh -x            # stop on first failure
#
# Environment variables (optional overrides):
#   OTTO_API_URL       default: https://otto-production-924c.up.railway.app
#   OTTO_FRONTEND_URL  default: https://frontend-lyart-ten-72.vercel.app

set -euo pipefail

PYTEST=~/Library/Python/3.9/bin/pytest
TESTS_DIR="$(dirname "$0")/tests/live"
ARGS="${*:--v --tb=short}"

echo "========================================"
echo "  Otto Live Test Suite"
echo "  API:      ${OTTO_API_URL:-https://otto-production-924c.up.railway.app}"
echo "  Frontend: ${OTTO_FRONTEND_URL:-https://frontend-lyart-ten-72.vercel.app}"
echo "========================================"
echo ""

# If a module name is passed (no leading -), convert to path filter
if [[ $# -gt 0 && "${1}" != -* ]]; then
  MODULE="$1"
  shift
  $PYTEST "$TESTS_DIR/test_${MODULE}.py" -v --tb=short "$@" 2>&1 | tee /tmp/otto_test_results.txt
else
  $PYTEST "$TESTS_DIR" $ARGS 2>&1 | tee /tmp/otto_test_results.txt
fi

echo ""
echo "Results saved to /tmp/otto_test_results.txt"
