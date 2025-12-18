#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PYTHON_BIN="${PYTHON_BIN:-python3}"

ARGS=()
if [[ "${1:-}" == "--live" ]]; then
  ARGS+=("--live")
  shift
fi

echo "Running full app test runner..."
echo "Python: ${PYTHON_BIN}"
echo "Runner: ${SCRIPT_DIR}/full_app_test.py"

"${PYTHON_BIN}" "${SCRIPT_DIR}/full_app_test.py" "${ARGS[@]}" "$@"




