#!/usr/bin/env bash
# Every validator in this repository, in the order that fails fastest.
#
# Structure first — scripts/check.py, every lane at once (cheap, and the thing
# most edits touch) — then the numerical harness, then the PDF of the manuscript
# and of every dossier, in the repository and in example/. A green run establishes
# structure only: it says nothing about whether a proof is correct (CLAUDE.md
# constraint 4).
#
# While iterating on one lane, run it directly instead:
#   python3 scripts/check.py --lane portfolio
#
# `check.py ready` and `check.py publish-ready` are deliberately NOT run here. They
# ask whether the repository has been instantiated, and a freshly cloned template
# must stay green on this script while correctly failing those.
#
#   ./scripts/check.sh            # everything available
#   ./scripts/check.sh --fast     # skip the PDF build
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

# PyYAML is the checker's Python dependency, declared in the root pyproject.toml. Use the
# interpreter that already has it; fall back to uv, which reads that manifest, so a fresh
# clone bootstraps itself instead of printing an install hint and stopping.
PY=(python3)
if ! python3 -c 'import yaml' >/dev/null 2>&1 && command -v uv >/dev/null 2>&1; then
  PY=(uv run --quiet --project . python)
fi

# MyST is required, not optional: scripts/check.py reads the manuscript through it, so
# without it there is no structure check to run. package.json pins it; install it the
# way uv installs PyYAML above, and fail rather than skip when that is impossible.
MYST=node_modules/.bin/myst
if [ ! -x "$MYST" ] && command -v npm >/dev/null 2>&1; then
  printf '=== installing MyST (npm ci) ===\n'
  npm ci --no-audit --no-fund >/dev/null
fi
if [ ! -x "$MYST" ]; then
  printf '!!! FAILED: MyST is required and could not be installed; install Node.js with npm, then run npm ci\n'
  exit 1
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

if command -v uv >/dev/null 2>&1; then
  run "numerics"      sh -c 'cd experiments && uv run pytest -q'
else
  skip "numerics" "uv not installed"
fi

# Build every PDF export of one MyST tree — the manuscript and each dossier — and fail
# on what `myst build --pdf` does not: it exits 0 when pdflatex fails, and its LaTeX
# serializer silently drops any directive it has no environment for. So read each
# LaTeX log for an error, and require every claim label the manuscript lane found to
# reach the exported manuscript as a \label.
pdf() {
  local tree="$1"
  rm -rf "$tree/_build/exports"
  (cd "$tree" && "$OLDPWD/$MYST" build --pdf >/dev/null 2>&1) || return 1
  "${PY[@]}" - "$tree" <<'PY'
import re, sys
from pathlib import Path
sys.path.insert(0, "scripts")
from checks import manuscript

tree = Path(sys.argv[1])
exports = tree / "_build/exports"
failed = False
for log in sorted(exports.glob("*_pdf_logs/*.log")):
    if log.name.endswith(".shell.log"):
        continue
    errors = [line for line in log.read_text(errors="replace").splitlines()
              if re.match(r"^\./.*\.tex:\d+: ", line)]
    if errors:
        failed = True
        print(f"{log}: LaTeX errors:", *errors[:5], sep="\n  ")
labels = manuscript.read(tree / "_build/site/content", [])
exported = "\n".join(path.read_text() for path in exports.glob("manuscript_pdf_tex/*.tex"))
for label, entry in sorted(labels.items()):
    if entry["kind"] and f"\\label{{{label}}}" not in exported:
        failed = True
        print(f"{entry['file']}: prf:{entry['kind']} '{label}' is missing from the PDF")
sys.exit(1 if failed else 0)
PY
}

if [ "$FAST" -eq 0 ]; then
  if command -v latexmk >/dev/null 2>&1 && command -v pdflatex >/dev/null 2>&1; then
    # Standalone PDFs are part of the proof definition of done (solutions/README.md).
    run "pdf"           pdf .
    run "example pdf"   pdf example
  else
    skip "pdf" "latexmk or pdflatex not installed"
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
  echo "PDF builds were omitted by --fast."
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
