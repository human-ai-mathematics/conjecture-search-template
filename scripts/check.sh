#!/usr/bin/env bash
# Every validator in this repository, in the order that fails fastest.
#
# Structure first — scripts/check.py, every lane at once (cheap, and the thing
# most edits touch) — then the numerical harness, then the document and every
# dossier the ledger currently certifies. A green run establishes structure only:
# it says nothing about whether a proof is correct (CLAUDE.md constraint 4).
#
# While iterating on one lane, run it directly instead:
#   python3 scripts/check.py --lane portfolio
#
# `check.py ready` and `check.py publish-ready` are deliberately NOT run here. They
# ask whether the repository has been instantiated, and a freshly cloned template
# must stay green on this script while correctly failing those.
#
#   ./scripts/check.sh            # everything available
#   ./scripts/check.sh --fast     # skip the LaTeX build
#   ./scripts/check.sh --strict   # a missing tool is a failure, not a skip
set -uo pipefail

cd "$(dirname "$0")/.."
FAST=0
STRICT=0
for argument in "$@"; do
  case "$argument" in
    --fast) FAST=1 ;;
    --strict) STRICT=1 ;;
    -h|--help) sed -n '2,18p' "$0"; exit 0 ;;
    *) printf 'unknown option: %s\n' "$argument" >&2; exit 2 ;;
  esac
done
STATUS=0
SKIPPED=()

# PyYAML is the checker's one dependency, declared in the root pyproject.toml. Use the
# interpreter that already has it; fall back to uv, which reads that manifest, so a fresh
# clone bootstraps itself instead of printing an install hint and stopping.
PY=(python3)
if ! python3 -c 'import yaml' >/dev/null 2>&1 && command -v uv >/dev/null 2>&1; then
  PY=(uv run --quiet --project . python)
fi

run() {
  local label="$1"; shift
  printf '\n=== %s ===\n' "$label"
  if "$@"; then
    return 0
  fi
  printf '!!! FAILED: %s\n' "$label"
  STATUS=1
}

# A suite that did not run has not passed. Without --strict it is recorded and named in
# the summary; with it, an absent tool fails the run outright.
skip() {
  local label="$1" reason="$2"
  if [ "$STRICT" -eq 1 ]; then
    printf '\n=== %s ===\n!!! FAILED: %s — %s (--strict)\n' "$label" "$label" "$reason"
    STATUS=1
  else
    printf '\n=== %s === SKIPPED: %s\n' "$label" "$reason"
    SKIPPED+=("$label: $reason")
  fi
}

run "structure"       "${PY[@]}" scripts/check.py
run "worked example"  "${PY[@]}" scripts/check.py --root example
run "checker tests"   "${PY[@]}" -m unittest discover -s scripts/tests -p 'test_*.py'

# The site is a derived view and not a validator, so this asks only whether it still
# builds — the exporter refuses a tree that does not validate, and the two runs above
# have already said whether this one does. A build here catches the case that matters:
# a derivation that no longer survives the shape of the current repository.
run "site"            "${PY[@]}" scripts/site.py --out build/site
if command -v node >/dev/null 2>&1; then
  # A syntax error in the frontend is a blank page, and nothing else would notice.
  run "site frontend" node --check site/site.js
else
  skip "site frontend" "node not installed"
fi

if command -v uv >/dev/null 2>&1; then
  run "numerics"      sh -c 'cd experiments && uv run pytest -q'
else
  skip "numerics" "uv not installed"
fi

if [ "$FAST" -eq 0 ]; then
  if command -v latexmk >/dev/null 2>&1; then
    run "document"    latexmk -pdf -outdir=build main.tex
    # Standalone compilation is part of the proof definition of done (solutions/README.md).
    # main.tex subfiles the modules, never the dossiers, so each dossier is built explicitly.
    for tree in . example; do
      while read -r dossier; do
        [ -n "$dossier" ] || continue
        [ -f "$tree/$dossier" ] || continue
        run "dossier $tree/$dossier" \
          latexmk -pdf -cd -outdir="$PWD/build" "$tree/$dossier"
      done < <("${PY[@]}" scripts/check.py dossiers --root "$tree" 2>/dev/null)
    done
  else
    skip "document" "latexmk not installed"
  fi
fi

printf '\n'
if [ "$STATUS" -ne 0 ]; then
  echo "one or more checks FAILED"
elif [ "$FAST" -eq 1 ]; then
  if [ "${#SKIPPED[@]}" -eq 0 ]; then
    echo "all fast checks passed (structure only — see CLAUDE.md constraint 4)"
  else
    echo "all AVAILABLE fast checks passed (structure only — see CLAUDE.md constraint 4)"
  fi
  echo "document and dossier builds were omitted by --fast."
  if [ "${#SKIPPED[@]}" -ne 0 ]; then
    echo "Other unavailable checks:"
    for entry in "${SKIPPED[@]}"; do
      printf '  %s\n' "$entry"
    done
    echo "run with --strict to make a missing tool a failure."
  fi
  echo "run without --fast for complete verification."
elif [ "${#SKIPPED[@]}" -eq 0 ]; then
  echo "all checks passed (structure only — see CLAUDE.md constraint 4)"
else
  echo "all AVAILABLE checks passed (structure only — see CLAUDE.md constraint 4)"
  echo "this was not a complete verification. Skipped:"
  for entry in "${SKIPPED[@]}"; do
    printf '  %s\n' "$entry"
  done
  echo "run with --strict to make a missing tool a failure."
fi
exit "$STATUS"
