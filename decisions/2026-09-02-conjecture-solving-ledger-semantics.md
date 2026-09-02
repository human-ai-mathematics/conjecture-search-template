# Conjecture-solving ledger semantics

Date: 2026-09-02

## Problem

The earlier schema mixed a claim's truth, its origin, and whether a conditional theorem could
currently be applied. It also treated plausible barriers like proved obstructions and allowed only
one proof artifact per node. Those choices obscure the actual frontier in long conjecture-solving
programs.

## Decision

- Logical status is only `open`, `proved`, `refuted`, or `defined`; origin is the independent
  `provenance: internal | literature` field.
- A proved implication uses `assumes` for antecedents and `implies` for conclusions. Its
  `depends_on` contains only facts needed to prove the implication. Open antecedents block
  applicability, not truth.
- `bounded_by` contains only proved obstructions. Open method barriers use
  `heuristic_barriers`.
- Internal proof provenance is a list of `proofs` records, permitting modular and alternative
  dossiers with independent certification.
- Refutation work must negate the exact quantifiers of the target.
- Lean remains a documented future certification mode; no larger Lean integration is added now.

The design is conjecture-agnostic. No field or role depends on KLS or any other example problem.

## Compatibility

Old `conditional` and `imported` statuses and singular `solution`/`checked_by` fields are rejected
with migration hints. This is an intentional template schema break. The worked example, canonical
role files, generated Codex adapters, and documentation were migrated together.

## Validation

- `python3 -m unittest discover -s scripts/tests -p 'test_check_ledger.py'`
- `python3 scripts/check_ledger.py`
- `python3 scripts/check_agents.py`
- `./scripts/check.sh`

All four passed after the migration.
