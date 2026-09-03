# Enforcing the three planes: routes out of the ledger, checkpoints into the portfolio

**Date.** 2026-09-03

Adopts the consistency pass recommended in
[`../research/reviews/2026-09-03-modular-search-portfolio-followup-audit.md`](../research/reviews/2026-09-03-modular-search-portfolio-followup-audit.md).
Amends, and does not rewrite,
[`2026-09-03-modular-search-portfolio.md`](2026-09-03-modular-search-portfolio.md); its
invariants 11–19 stand, and this record continues their numbering.

## Problem

The redesign adopted the right architecture and then left seven places where the previous
one still showed through. The audit found them; all seven were confirmed in the code.

- **Two homes for coordination.** `CLAUDE.md` constraint 12 says approach families and route
  states never enter the ledger. The ledger schema nevertheless defined per-node `route` as
  "coordination ownership", and forty lines of validator enforced it. Used by zero nodes.
- **A portfolio state change could have no explanation.** "Checkpoints = why the portfolio
  changed" was a slogan: checkpoint references resolved by filesystem existence, so
  `research/explorations/README.md` would have satisfied one. Nothing required a `blocked`,
  `completed` or `duplicate` route to carry a checkpoint at all, and nothing compared a
  checkpoint's `approach:` against the route listing it.
- **A closed family could hold queued work,** because the straggler check looked only for
  `active`. And `saturation_checkpoint` was the wrong name for a `parked` family, which is a
  budget decision rather than a claim that a mechanism is exhausted.
- **The exact target had two owners.** The brief disclaimed the statement in one paragraph
  and asked the author to state it with every quantifier two paragraphs later.
- **A broken ledger passed the portfolio plane.** Target resolution was guarded on the node
  set being non-empty, and every ledger failure empties it, so `--plane portfolio` reported
  clean while the core error was filtered out. The blocker check was unguarded and fired
  spuriously — the asymmetry ran the wrong way in both directions.
- **Lens text was 69 of 150 lines of `researcher.md`** and 43 of 103 of `reviewer.md`,
  loaded on every invocation regardless of the one lens assigned.
- **`references.bib` still named `status: imported` and `check_ledger.py`,** and two live
  documents disagreed about whether the roster was four roles or seven.

## Chosen invariants

20. **Coordination is not a claim, in both directions.** Constraint 12 already forbade route
    state in the ledger; the ledger now enforces it against itself. `route` and
    `meta.route_policy` are retired and rejected *by name*, with prose pointing at the
    portfolio, so a ledger inherited from an earlier copy of this template is told where the
    state went rather than merely told the field is unknown.

21. **Every portfolio state change carries the record that explains it.** A `blocked`,
    `completed` or `duplicate` route names at least one checkpoint. Every `checkpoints:`
    entry and every `closure_checkpoint` resolves through the *parsed checkpoint index*, not
    the filesystem. A referenced record declaring `approach:` must name the route that lists
    it — and, for a closure, an approach in the closing family.

22. **The back-link is deliberately not required.** A checkpoint naming `approach: ap:x` need
    not already appear in `ap:x`'s `checkpoints:`. A `researcher` writes the checkpoint and
    only the `synthesizer` writes the portfolio, so requiring it would make a red checker the
    normal state between those two steps and would pressure agents to edit an append-only
    file. Invariant 21 buys the agreement without the deadlock, and a pre-portfolio record
    stays attachable from the portfolio side.

23. **A family is closed or it is not.** `saturated` says the mechanism is worked out;
    `parked` says only that nobody is working it. Both owe a `closure_checkpoint` — renamed
    from `saturation_checkpoint`, which was honest for one state and false for the other —
    and a `reopen_if`, and both reject `queued` as well as `active` children. A queued route
    is planned live work, so a family holding one has not closed.

24. **The target has one owner and may be quoted.** Manuscript: the canonical quantified
    statement. Ledger: identity, status, provenance, relations. Brief: the negation,
    completion criteria, edge cases, traps, search policy. The brief may quote its target
    verbatim as a *marked copy* — constraint 8 now says a marked quotation is not a second
    home — and the `reviewer`'s `sync` lens checks the copy still agrees. The claim graph is
    therefore the first gate a sustained search crosses, and `CLAUDE.md`'s table is reordered
    to say so.

25. **A missing dependency is an error, not an absence of errors.** When the claim graph is
    unavailable or empty, the portfolio plane says so in one error and skips the resolutions
    that depend on it, rather than silently omitting the target check while the blocker check
    fires against nodes that merely failed to load. `--plane` restricts presentation; it never
    turns an unresolved reference into a passing validation.

26. **A lens is a file, not a section.** Each of `prove`, `refute`, `mine`, `construct`,
    `certify` and `sync` is one file in `.claude/lenses/`, loaded on its own by the role that
    declares it. A lens has no tools, no write surface and no adapter: it inherits everything
    from its role, which is what keeps the roster at four core roles without charging every
    invocation for strategies it was not asked to run. The link is checked in both
    directions — an orphan lens and a dangling declaration are both errors.

## What changed

### Added

- `.claude/lenses/` — `README.md` and six lens files. The lens bodies hold only method and
  the bullets they add to the role's `## Report`; permissions, write surface, checkpoint
  triggers and the handoff envelope stay stated once in the role contract. `construct` gains
  a report contract it never had.
- `research/explorations/2026-09-03-example-dedup.md` — the worked example the previous
  decision noted was missing: the template's first checkpoint carrying `approach:`, and the
  record that explains why `ap:example-exhaustive-search` is a duplicate.
- `scripts/checks/roles.py` — `_validate_lenses`, and `scripts/checks/common.py` gains the
  shared `APPROACH_ID_RE` that the portfolio and checkpoint planes had each defined.

### Changed

- `scripts/checks/ledger.py` — `_validate_route_policy` deleted; `route` and `route_policy`
  moved into the obsolete-field tables. `OBSOLETE_META_FIELDS` becomes a mapping so it can
  carry per-field replacement prose, and its message matches the node one.
- `scripts/checks/portfolio.py` — `check_brief` drops to envelope validation; `resolve` takes
  the checkpoint index and now owns every cross-plane reference in this plane, which is what
  makes invariant 25 a single guard.
- `scripts/checks/checkpoints.py` — `check_supersession` returns superseded → heirs instead
  of a set, so a reader is told what to read *instead*. Membership tests are unaffected.
- `scripts/checks/views.py` — `status` no longer groups by route; `checkpoints` names the
  superseding record and lists current audit heads.
- `.claude/agents/researcher.md` 150 → 85 lines, `.claude/agents/reviewer.md` 103 → 64. The
  researcher's blanket ban on numerical evidence as a *plausibility* argument is narrowed to
  the dossier, where it belongs: directional numerics exists to choose between routes.
- `CLAUDE.md` — gates table reordered, constraint 8 extended for the marked quotation.
  Constraints keep their numbers and none becomes `Reserved`.
- `research/program/brief.md`, `research/README.md`, `research/program/README.md`,
  `research/program/portfolio-schema.md`, `research/program/ledger-schema.md`,
  `research/explorations/README.md`, `.claude/agents/README.md`, `README.md`,
  `references.bib`, `.gitignore` — swept for target ownership, the roster's four-plus-three
  shape, the renamed field, and the lens directory.

### Removed

- `meta.route_policy`, per-node `route`, and their test. Nothing consumed them but a
  `status` grouping no shipped ledger used.

## Migration boundary

Append-only records are untouched. `decisions/` and `research/reviews/` still name
`check_ledger.py`, `check_agents.py`, and the five merged roles; those are historical paths
in immutable records and remain correct as written. The 2026-09-02 modes audit stays
superseded, not edited.

An inherited repository sees named errors rather than silent breakage: `route`,
`route_policy` and `saturation_checkpoint` each report their replacement. The three new
portfolio rules are the only ones that can fail a previously green repository, and each
failure names the route and the missing record.

## Compatibility

Ledger and proof semantics are untouched: no status, kind, certification mode, or review
contract changed meaning. The checkpoint envelope is unchanged — `approach:` was already
optional and still is. `check_supersession`'s return type changed from `set` to `dict`; every
call site tests membership, which behaves identically.

The renames are breaking for a portfolio that used them, which is why both are rejected by
name rather than dropped.

## Validation

`./scripts/check.sh` green: `scripts/check.py` at 0 errors across all six planes, 95 checker
tests (86 carried over, 9 new: portfolio 6, roles 3), the numerics suite, and a full
`latexmk` build.

Spot-checked by hand, each against the audit finding it closes: with `ledger.yaml` moved
away, `check.py --plane portfolio` now reports the dependency error instead of exiting 0;
`check.py checkpoints` names the record that superseded the modes audit; `check.py portfolio`
shows the dedup checkpoint on `ap:example-exhaustive-search`; and a family closed over a
`queued` route fails.
