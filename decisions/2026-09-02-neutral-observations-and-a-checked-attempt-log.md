# Neutral observation records, a validated attempt log, and where a candidate lives

**Date.** 2026-09-02

Amends, and does not rewrite, [`2026-09-01-template-baseline.md`](2026-09-01-template-baseline.md),
[`2026-09-02-collapse-side-registries.md`](2026-09-02-collapse-side-registries.md), and
[`2026-09-02-simplify-numerics-harness.md`](2026-09-02-simplify-numerics-harness.md). Invariants
1–13 stand. This record answers three defects found by reading the template as a *general*
exploration harness rather than as this program's bookkeeping.

## Problem

**1. The numerics vocabulary was not domain-neutral.** `RunResult` and its records were general,
but the only shape a target could actually write in was
`Comparison(bound, value, tightness=value/bound)` with outcomes `exceeds`/`within`/`unavailable`.
That is exactly the shape of a functional inequality, and it distorts every other genre: a
combinatorial counterexample search has no bound, a verified-up-to-$N$ sweep has no `tightness`,
a Gröbner or SAT witness has neither. A fork in another area would have had to either bend its
mathematics into a bound-versus-value pair or bypass the helpers and hand-write untyped records —
and an untyped record is exactly the unlabelled number `CLAUDE.md` constraint 2 exists to prevent.

**2. The attempt log was the one plane nothing checked.** `research/reviews/` got structured
front matter with a validated scope, and it works: a certification cannot point outside its
report. `research/explorations/` — which is the *memory*, the thing that stops the next agent
re-running a dead end — was free prose. Nothing detected an exploration naming a node that does
not exist, nothing detected a cited run artifact that was never written, and nothing could
answer "has this node been attacked?" without reading every file. A memory nobody can query is
a memory that rots into a directory nobody greps.

**3. Invariant 7 left cheap statements homeless.** "Every mathematical object is a ledger node
with a manuscript statement" is right for findings, and collapsing the side registries was
right. But an exploration-heavy loop throws off many statements per hour that are worth not
losing and are not worth a `\label`, a node, and an orchestrator round-trip — most of which will
be dead by tomorrow. The design implied such a statement lives in exploration prose and never
said so, which in practice means it either gets smuggled into a node it has not earned or is
lost.

## Chosen invariants

14. **The artifact contract is `kind` + `claim` + evidence class + outcome, and nothing else.**
    Genre-specific fields — a bound and a value, a search domain and a witness, a certificate —
    live in a `detail` mapping the target owns. `compare`, `matches` and `searched` are supplied
    helpers for three common shapes; `observe(...)` is the contract itself, for a genre they do
    not fit. Outcomes are neutral across genres: `contradicts`, `consistent`, `inconclusive`,
    plus `match`/`mismatch` for a calibration. A record is either a complete observation or
    plainly auxiliary data — `RunResult.validate()` rejects the half-labelled record in between,
    which is the shape that lets an unlabelled number look like evidence.

15. **Every exploration carries validated front matter.** `type`, `date`, `outcome`
    (`dead-end`, `directional`, `candidate`, `proposed`), the ledger `nodes` it engaged, and the
    `research/runs/` `artifacts` it cites. Node ids must resolve; artifacts must exist and be
    under `research/runs/`. The envelope records what the attempt *engaged*, never what it
    concluded: a conclusion is prose, and a conclusion that earns reuse becomes a ledger node.

16. **A candidate statement is not a ledger node** (`CLAUDE.md` constraint 8). A statement
    nothing yet depends on lives in the `candidates:` list of the exploration that proposed it,
    under a `cand:<slug>` id unique across the log, with no manuscript anchor, no status and no
    certification. `outcome: candidate` and a non-empty `candidates:` require each other, so an
    attempt cannot propose one silently.

17. **A candidate is killed by a later exploration, never by an edit.** A later dated file names
    it in `retires:`; "live" is then *derived* by `check_ledger.py candidates`, exactly as the
    conditional contract and the reverse dependency graph are derived. The log stays append-only
    (constraint 7) and no file records liveness.

## Why this is not a new side registry

The obvious objection, given the record this one amends: `candidates:` looks like the
`lemmas.md` waiting room that was deleted for letting an uncertified fact acquire the appearance
of settled knowledge. Three differences make it the opposite.

- It is **inside the attempt record**, not beside it. A candidate is a fact *about an attempt* —
  this is what that hour produced — and it cannot be read without its dead end attached.
- It is **append-only and derived**. `lemmas.md` was a curated mutable file, so a statement could
  be quietly promoted by editing it. Nothing here can be edited: promotion means acquiring a
  `\label` and a node, and retirement means writing another dated file.
- It **cannot be mistaken for state**. A `cand:` id is not a node id and resolves nowhere;
  `depends_on`, `bounded_by`, `refines` and `bridges` all reject it. Nothing can be built on a
  candidate without first promoting it.

## Migration boundary

- **Artifact schema 1 → 2.** The outcome vocabulary changed (`exceeds` → `contradicts`,
  `within` → `consistent`, `unavailable` → `inconclusive`) and genre fields moved into `detail`.
  The `_provenance` header, exclusive-create writes, commit stamp and `STAMPED_PACKAGES` block
  are untouched — what constraint 2 rests on did not move. Historical artifacts are **not**
  migrated and not reinterpreted: `research/runs/` is append-only and each artifact carries the
  version it was written with.
- `Comparison` → `Observation`, with `detail` and a validated `evidence`×`outcome` pairing.
  Added: `observe(...)`, `searched(...)`, `check_observation(...)`. `compare` and `matches` keep
  their names and argument order.
- `check_ledger.py` gained `_read_exploration_metadata`, `_validate_explorations`, the
  `candidates` subcommand, and a live-candidate count in the default summary. The front-matter
  parser and the dated-record date check are now shared with the review reader rather than
  duplicated.
- The template's worked-example set grows by one exploration and the run artifact it cites, so
  every artifact genre still ships exactly one instance; both are on the instantiation
  delete-list in `README.md`.
- `experiments/numerics/targets/example.py` now records all three helper shapes against
  `prop:example`, so no helper ships without a caller and a test — the dead-code failure mode
  the previous record removed.

## Compatibility

`CLAUDE.md` constraints 1–7 are unchanged and none becomes `Reserved`; constraint 8 is new and
takes a fresh slot. Invariants 14–17 continue the decision records' own numbering. A repository
built from an earlier copy of the template inherits none of this; migrating one means writing
front matter for its existing explorations, which is a mathematical reading task, not a mechanical
one, and it should not be done merely for uniformity.

## Validation

`./scripts/check.sh` green: ledger checker at 0 errors with 1 live candidate, agent checker at 10
roles with regenerated Codex adapters, 52 checker tests (45 + 7 for the attempt log), the numerics
suite at 13 passed, and a full `latexmk` build. The seven new checker tests were written against
the failure they describe: an unparsable envelope, an unresolvable node or artifact, a candidate
list disagreeing with its outcome, a malformed or duplicated candidate id, a candidate colliding
with a ledger node, retirement of a candidate never proposed or not yet proposed, and the derived
live list.
