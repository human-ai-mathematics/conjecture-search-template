# A search portfolio, checkpoint memory, and a checker split by plane

**Date.** 2026-09-03

Adopts the design recommended, but not adopted, in
[`../research/reviews/2026-09-03-simple-modular-search-portfolio-analysis.md`](../research/reviews/2026-09-03-simple-modular-search-portfolio-analysis.md),
which in turn rests on
[`../research/reviews/2026-09-02-template-vs-raw-prompt-analysis.md`](../research/reviews/2026-09-02-template-vs-raw-prompt-analysis.md).
Amends, and does not rewrite,
[`2026-09-01-template-baseline.md`](2026-09-01-template-baseline.md),
[`2026-09-02-collapse-side-registries.md`](2026-09-02-collapse-side-registries.md), and
[`2026-09-02-conjecture-solving-ledger-semantics.md`](2026-09-02-conjecture-solving-ledger-semantics.md);
their invariants 1–10 stand.

## Problem

Three defects, all diagnosed in the two audits above.

- **The overhead was uniform rather than proportional.** The root contract required a new
  exploration for every nontrivial attempt, dead ends included. A ten-minute speculative
  calculation paid the same recording tax as a reusable obstruction, and a large parallel
  search accumulated records without revealing which approach families were still alive.

- **The attempt log was not a portfolio.** The exploration envelope recorded nodes, outcome,
  candidates and artifacts. It recorded nothing about the *search*: the mathematical family of
  an approach, its parent, its overlap with another route, its exact blocker, or the condition
  that would justify reopening it. A synthesizer had to reconstruct the search topology from
  prose. For a large parallel conjecture search this was the most important missing feature —
  and it is exactly what a strong conjecture-specific prompt asks for.

- **`check_ledger.py` had outgrown its name.** 1,230 lines validating the ledger, proof
  records, reviews, explorations, candidates and artifact references behind one entry point
  called "ledger", with a 1,214-line test file to match. Nothing validated run artifacts at
  all.

Underneath all three: the repository never said out loud what it was for. A harness that
declares itself general owes a plane to every research mode; one that declares itself a
conjecture-search harness owes exactly the planes a conjecture search uses.

## Chosen invariants

Continuing the decision records' own numbering, which is separate from `CLAUDE.md`'s
constraints.

11. **The scope is sustained conjecture search.** Proving or refuting one hard statement, over
    many sessions and several agents. Theory building, classification, algorithms, exposition,
    and first-class proof certificates are declared out of scope rather than half-served.
    `CLAUDE.md` opens with this; the superseded modes audit's criticism becomes a boundary.

12. **Three planes, one sentence.** *Ledger = what is mathematically claimed. Portfolio = what
    the search is doing. Checkpoints = why the portfolio changed.* Every subsequent rule is a
    consequence.

13. **Layers activate structurally, not by a mode flag.** Brief, portfolio, checkpoints, claim
    graph, certification — each is created when the work needs it, and a layer whose files are
    absent has no rules to obey. `check.py` validates only the planes that exist, so an early
    repository pays for nothing. This is deliberately not a set of configured profiles: a
    profile spreads conditional rules through every contract, while an absent file spreads
    nothing.

14. **The portfolio is search state and holds no mathematics.** `CLAUDE.md` constraint 12.
    Single writer (the `synthesizer`); coordination state only; blockers named by `cand:` id or
    ledger node and never restated; a blocked route owes an exact blocker and a reopening
    condition; a closed family owes a synthesis checkpoint, a reopening condition, and no
    surviving active child; two routes related by `duplicates` may not both be active. The
    ledger rejects `approach` and `family` as obsolete fields, so the prohibition holds in both
    directions.

15. **Saturation is a judgment with a price, never an inference.** A validator can insist that
    a declaration carries its synthesis and its reopening condition. It cannot infer
    mathematical exhaustion from attempt counts, and neither can elapsed time. The checker
    checks the paperwork; the `synthesizer` makes the call.

16. **Durable memory is one file per durable search event, not per attempt.** Six triggers, in
    `research/explorations/README.md`. A speculative calculation that dies in ten minutes needs
    no file; a dead end plausible or expensive enough that the next agent would repeat it does.
    The directory keeps its name; its records are checkpoints.

17. **Supersession is presentation; retirement is content.** `retires:` kills a tentative
    *statement*; `supersedes:` says a later *record* should be read first. Neither deletes
    anything, and supersession only ever points backwards in time, which is what makes it
    acyclic without a graph walk. Available to checkpoints and to non-certifying audits — the
    two genres that go stale — and not to proof reviews or decisions, which are events.

18. **Four core roles, with lenses instead of near-duplicate contracts.** `scout`,
    `researcher`, `reviewer`, `synthesizer`, plus the specialists `numerics`,
    `literature-scout`, `janitor`. Proving, refuting, mining and constructing are assignment
    lenses on one `researcher`; certifying and manuscript/ledger sync are the two lenses of one
    `reviewer`. Author and reviewer separation survives as a hard write-surface split and is
    itself under test.

19. **One checker, six planes, errors tagged by the plane that raised them.**
    `scripts/check.py` over a `scripts/checks/` package. `--plane` scopes what is reported while
    diagnosing one plane; the default lane reports everything. The planes reference each other
    — a checkpoint names an approach, a route blocks on a candidate — so the analysis is one
    pass and the *reporting* is what splits.

## What changed

### Added

- `research/program/brief.md` — the problem brief: exact statement and negation, what counts
  as a complete proof and a complete refutation, edge cases and audit tests, equivalent-strength
  traps, initial families, blocked/reopen criteria, and a budget policy that permits an honest
  unresolved outcome. Orchestrator-owned under a new `brief` concurrency key. The harness
  remembers and certifies; the brief is what makes the search sharp, and its absence was the
  gap the template-versus-prompt audit identified.
- `research/program/portfolio.yaml` and `research/program/portfolio-schema.md` — the search
  portfolio and its field contract, in the shape the analysis proposed. Written only by the
  `synthesizer`, under a new `portfolio` concurrency key.
- `scripts/check.py` and `scripts/checks/{common,ledger,proofs,checkpoints,portfolio,numerics,roles,views}.py`.
- A `numerics` plane: every `research/runs/*.jsonl` still parses, carries a complete
  `_provenance` header on its first line and nowhere else, records at least one observation,
  and is named after the target it recorded. Nothing checked this before.
- `research/reviews/2026-09-03-superseded-modes-audit.md`, the migration pass that marks the
  stale half of the 2026-09-02 modes audit and demonstrates audit supersession.

### Changed

- `CLAUDE.md` — new *Scope* and *The gates* sections; the workflow gains a *Search
  contribution* lane; constraint 4 renamed to `check.py`; constraint 7 gains the supersession
  sentence; constraint 8 speaks of checkpoints; **new constraint 12** for the portfolio.
  Constraints 1–11 keep their numbers and none becomes `Reserved`.
- `research/explorations/README.md` — "one file per nontrivial attempt" becomes "one file per
  durable search event", with the six triggers; the envelope gains `approach:` and
  `supersedes:`; `nodes` relaxes to "at least one of `nodes`, `approach`, `candidates`", since
  work can now legitimately engage a route rather than a node.
- `research/reviews/README.md` — `supersedes:` added to the audit envelope, with the reason it
  is refused to proof reviews.
- `.claude/agents/` — ten roles become seven. `prover`, `refutation-seeker` and `proof-miner`
  merge into `researcher`; `proof-checker` and `latex-sync` merge into `reviewer`; the
  `synthesizer` gains portfolio ownership and a curation method. The shared handoff envelope
  gains `portfolio_delta`, which is how parallel researchers propose route changes without
  concurrent edits to one file.
- Roster, concurrency keys, and transition diagram in `.claude/agents/README.md`.
- `README.md`, `research/README.md`, `research/program/README.md`,
  `research/program/ledger-schema.md`, `solutions/README.md`, `experiments/README.md`,
  `scripts/check.sh`, `main.tex`, and the `ledger.yaml` header — swept for the new entry point,
  the new vocabulary, and the sixth plane.
- The Codex adapter header now names `scripts/check.py`, and `--write-codex` deletes an adapter
  whose role is gone rather than leaving an orphan.

### Removed

- `scripts/check_ledger.py`, `scripts/check_agents.py`, and their two test files. No shims:
  every documented command changed, and a shim would have preserved the name whose scope drift
  caused the problem.
- `.claude/agents/{prover,refutation-seeker,proof-miner,proof-checker,latex-sync}.md` and their
  Codex adapters. Nothing they said is lost; it is now lens text inside `researcher.md` and
  `reviewer.md`.

## Migration boundary

Existing append-only records are unchanged, exactly as the analysis required.

- `research/explorations/2026-09-02-example-exploration.md` keeps its front matter and gains no
  `approach:` field. It is attached to a route from the other side, through
  `ap:example-finite-battery`'s `checkpoints:` list — which is how any pre-portfolio record is
  retroactively placed without editing it. The template therefore ships no worked example of
  `approach:` in a checkpoint; `research/explorations/README.md` documents the field instead.
- Decision records under `decisions/` still name `check_ledger.py` and `check_agents.py`. Those
  are historical paths in immutable records and are correct as written; the `janitor` is
  already instructed not to repair history.
- The 2026-09-02 modes audit is superseded, not edited.

A repository built from an earlier copy of this template inherits none of this and should not
be migrated merely for uniformity.

## Compatibility

`CLAUDE.md` constraint numbers 1–11 are unchanged and none becomes `Reserved`; 12 is new.
Ledger and proof semantics are untouched: no field, status, kind, certification mode, or
review contract changed meaning, and the 38 core and proof regression tests carried over
unmodified except for the checker's import path. The exploration envelope is a strict
extension — every previously valid record remains valid, and the one relaxation (`nodes` no
longer required when an approach is named) only admits records that were impossible before.

The user-facing command names all changed. That is the deliberate cost of invariant 19.

## Validation

`./scripts/check.sh` green: `scripts/check.py` at 0 errors across all six planes, 86 checker
tests (47 carried over, 39 new: portfolio 14, numerics 7, checkpoint approach/supersession 5,
CLI 5, roles 2, plus reassignments), the numerics suite and its calibration anchors, and a full
`latexmk` build of the document.

Spot-checked by hand: `check.py --plane portfolio` on a portfolio with a blocked route whose
blocker had been retired as a candidate reports it; `check.py checkpoints` lists the superseded
modes audit; `check.py node <id>` reports which approaches a node blocks.
