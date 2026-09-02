# Collapse the numerics harness to one check lane and one target function

**Date.** 2026-09-02

Amends, and does not rewrite, [`2026-09-01-template-baseline.md`](2026-09-01-template-baseline.md).
Invariant 6 ("a fresh clone is green") stands; this record shrinks what has to be green.

## Problem

`experiments/` shipped ~500 lines across eight modules and two test files to support one worked
example target. Three kinds of surplus had accumulated, none of them load-bearing:

- **Two check lanes for one question.** `numerics check` walked the registry, spawned an
  independent `SeedSequence` stream per target, and called a target-owned `selftest(rng)` that
  returned `list[(label, ok)]`; `pytest` then tested the harness contract separately. Both answer
  "does this implementation still reproduce its closed-form anchors". The cost was not the 42
  lines of `selftest.py` — it was that **every target had to expose two functions**, keep its
  anchors in the second one, and be run twice, and that `scripts/check.sh` and the `numerics`
  role each had to name both lanes in the right order.
- **A duplicated comparison vocabulary.** `compare_exact` and `compare_directional` were
  identical apart from one string literal, and had the opposite argument order from `matches`
  (`(claim, instance, …)` versus `(instance, claim, …)`) — a silent field swap waiting to happen
  in a target nobody would diff. `compare_exact` and `convergence_ok` had no caller at all, and
  `TargetSpec.default_profile` was dead because argparse hardcodes `"standard"`.
- **Four modules for the artifact spine.** `contract.py`, `provenance.py`, `run.py`, and
  `comparison.py` totalled 190 lines with a single dependency chain through all of them.

## Chosen invariants

11. **A target exposes exactly one function.** `run_records(seed, **cfg) -> RunResult`. Its
    closed-form anchors go in the artifact as `matches(...)` calibration records, where a reader
    of `research/runs/` can see them, rather than in a private selftest that leaves no trace.
12. **`pytest` is the only check lane.** The suite is parametrized over `REGISTRY`: it runs every
    registered target and fails if any target records no calibration, or records one whose
    outcome is `mismatch`. Coverage of the calibration anchors is preserved and now cannot be
    skipped by forgetting to write a `selftest`.
13. **One comparison entry point.** `compare(instance, claim, *, bound, value, evidence, …)`
    with keyword-only values and a validated `evidence` label, plus `matches(...)` for a
    calibration against a closed form. The evidence class stays an explicit, checked argument;
    passing `evidence="proved"` raises.

## Migration boundary

The **artifact format is unchanged** — same `_provenance` header, same schema version 1, same
record and `run-summary` lines, byte-compatible with artifacts written before this change. No
file under `research/runs/` is migrated or reinterpreted. Provenance was deliberately left
untouched: the versioned envelope, exclusive-create writes, git commit stamp, and
`STAMPED_PACKAGES` environment block are what `CLAUDE.md` constraint 2 actually rests on.

Removed: `numerics/selftest.py`, the `numerics check` subcommand, the target-side `selftest(rng)`
contract, `compare_exact`, `compare_directional`, `calibration_ok`, `convergence_ok`,
`TargetSpec.default_profile`, and the unused `slow` pytest marker. Merged: `provenance.py` +
`run.py` → `artifact.py`; `comparison.py` → `contract.py`; the two test files →
`tests/test_numerics.py`. The package is now 6 files and ~250 lines; `experiments/README.md` is
78 lines, from 100.

## Compatibility

`CLAUDE.md` constraints 1–7 are unchanged and none becomes `Reserved`; invariants 11–13 continue
the decision records' own numbering. `scripts/check.sh` and `.claude/agents/numerics.md` (with
its regenerated Codex adapter) drop their `numerics check` step. A repository built from an
earlier copy of the template keeps its `selftest`-based targets working only if it also keeps its
own copy of `selftest.py`; it should not be migrated merely for uniformity.

## Validation

`./scripts/check.sh` green: ledger checker at 0 errors, agent checker at 10 roles with regenerated
Codex adapters, the checker tests, the numerics suite at 10 passed, and a full `latexmk` build.
A `numerics run example` artifact was diffed against the pre-change format and matches field for
field.
