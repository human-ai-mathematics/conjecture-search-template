#!/usr/bin/env bash
# Every validator: this repository, the worked example, the checker's own tests.
# A green run establishes structure only, never that a proof is correct.
set -uo pipefail
cd "$(dirname "$0")/.."
[ -x node_modules/.bin/myst ] || npm ci --no-audit --no-fund >/dev/null || exit 1
STATUS=0
run() { printf '\n=== %s ===\n' "$1"; shift; "$@" || { echo "!!! FAILED"; STATUS=1; }; }
run "structure"      uv run scripts/check.py
run "worked example" uv run scripts/check.py --root example
run "checker tests"  uv run python -m unittest discover -s scripts/tests -p 'test_*.py'
exit "$STATUS"
