---
type: audit
date: "2026-09-03"
supersedes:
  - research/reviews/2026-09-02-mathematical-research-modes-audit.md
---

# What the research-modes audit no longer describes

## Scope

This is the migration pass that
[`2026-09-03-simple-modular-search-portfolio-analysis.md`](2026-09-03-simple-modular-search-portfolio-analysis.md)
called for: one record that says which parts of an earlier operational summary the repository
has since overtaken, so that a reader meeting the archive for the first time is not misled by
a document that was accurate when it was written.

It certifies no proof and changes no mathematical status. It is also the first use of the
`supersedes:` relation on an audit, adopted in
[`../../decisions/2026-09-03-modular-search-portfolio.md`](../../decisions/2026-09-03-modular-search-portfolio.md).

## What is stale, and what replaced it

The superseded audit reported three things about the harness that are no longer true.

1. **`conditional` and `imported` mix orthogonal ledger concepts.** Correct at the time, and
   already fixed by
   [`../../decisions/2026-09-02-conjecture-solving-ledger-semantics.md`](../../decisions/2026-09-02-conjecture-solving-ledger-semantics.md).
   The schema now separates `status` from `provenance`, separates truth from applicability
   with `assumes`/`implies`, and rejects both old status values by name.

2. **The template supports only one active proof per node.** Also fixed by that decision:
   `proofs` is a list, and `CLAUDE.md` constraint 10 makes proof provenance explicitly plural.

3. **The harness records attempts but does not manage a search portfolio.** Fixed by the
   decision this audit accompanies: `research/program/portfolio.yaml` records approach
   families, route states, exact blockers, reopening conditions, and duplication, and
   `research/program/brief.md` carries the problem-specific pressure the generic roles cannot
   supply.

## What still stands

The superseded audit's wider observation — that this harness is tuned for proving and refuting
a conjecture, and is weaker for theory building, classification, algorithms, exposition, and
first-class proof certificates — remains accurate. It is no longer a criticism to be answered
but a declared boundary: `CLAUDE.md` now opens by saying so.

Its remark that process independence is not epistemic independence also stands. Distinct
author and reviewer identities and a cold review context reduce self-review and anchoring;
they do not make two instances of one model independent, and a major result still warrants
human review or genuine formal certification.

## Exclusions

Nothing here revisits any proof. The superseded record is preserved unchanged, as required by
`CLAUDE.md` constraint 7; `python3 scripts/check.py checkpoints` lists it as superseded.
