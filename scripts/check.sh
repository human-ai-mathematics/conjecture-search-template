#!/usr/bin/env bash
# Every validator in this repository, in the order that fails fastest.
#
# Structure first (cheap, and the thing most edits touch), then the numerical
# harness, then the document. A green run establishes structure only: it says
# nothing about whether a proof is correct (CLAUDE.md constraint 4).
#
#   ./scripts/check.sh            # everything
#   ./scripts/check.sh --fast     # skip the LaTeX build
set -uo pipefail

cd "$(dirname "$0")/.."
FAST=0
[ "${1:-}" = "--fast" ] && FAST=1
STATUS=0

run() {
  local label="$1"; shift
  printf '\n=== %s ===\n' "$label"
  if "$@"; then
    return 0
  fi
  printf '!!! FAILED: %s\n' "$label"
  STATUS=1
}

run "ledger"          python3 scripts/check_ledger.py
run "agent roles"     python3 scripts/check_agents.py
run "checker tests"   python3 -m unittest discover -s scripts/tests -p 'test_*.py'

if command -v uv >/dev/null 2>&1; then
  run "numerics tests"  sh -c 'cd experiments && uv run pytest -q'
  run "numerics check"  sh -c 'cd experiments && uv run python -m numerics check'
else
  printf '\n=== numerics === SKIPPED: uv not installed\n'
fi

if [ "$FAST" -eq 0 ]; then
  if command -v latexmk >/dev/null 2>&1; then
    run "document"      latexmk -pdf -outdir=build main.tex
  else
    printf '\n=== document === SKIPPED: latexmk not installed\n'
  fi
fi

printf '\n'
if [ "$STATUS" -eq 0 ]; then
  echo "all checks passed (structure only — see CLAUDE.md constraint 4)"
else
  echo "one or more checks FAILED"
fi
exit "$STATUS"
