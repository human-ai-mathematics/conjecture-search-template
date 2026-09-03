# Portfolio schema

This is the field contract for [`portfolio.yaml`](portfolio.yaml) and for the front
matter of [`brief.md`](brief.md). [`../../scripts/check.py`](../../scripts/check.py) is
the executable validator; [`../../CLAUDE.md`](../../CLAUDE.md) owns policy.

The governing separation:

> Ledger = what is mathematically claimed. Portfolio = what the search is doing.
> Checkpoints = why the portfolio changed.

Nothing in this file is a mathematical claim. A route has no truth value, an approach
family is not a theorem, and "saturated" is a judgment about effort rather than a fact
about mathematics. That is why none of it may enter the ledger, and why the portfolio
never restates a statement: it names a `cand:` id or a ledger node id and stops
(`CLAUDE.md` constraint 12).

## Activation

Both files are optional and absent by default. A repository with one target and one live
route coordinates itself; a portfolio that describes a search nobody is running is
overhead. Create the brief when a sustained search starts, and the portfolio when several
routes, agents, or sessions are in flight at once.

## `brief.md`

```yaml
---
type: brief
target: q:main-conjecture
---
```

`target` must resolve to a ledger node, and must agree with `portfolio.yaml`'s `target`
when both exist. The body is prose; the sections the template ships are what an agent
needs before it can attack the problem honestly — the exact statement and its negation,
what counts as a complete proof and a complete refutation, edge cases, known
equivalent-strength traps, the initial families, the blocked/reopen criteria, and a
budget policy that permits an honest unresolved outcome.

## `portfolio.yaml`

```yaml
target: q:main-conjecture

families:
  - id: fam:transport
    mechanism: Construct a transport or coupling argument.
    state: saturated
    saturation_checkpoint: research/explorations/2026-09-03-transport-synthesis.md
    reopen_if: A construction avoiding cand:transport-compatibility is found.

approaches:
  - id: ap:transport-gluing
    family: fam:transport
    parent: ap:transport-local
    state: blocked
    blocker: cand:transport-compatibility
    reopen_if: The blocker is proved, weakened, or bypassed by a new mechanism.
    related:
      - to: ap:localization-patching
        relation: overlaps
    checkpoints:
      - research/explorations/2026-09-03-transport-gluing.md
```

### Document

| field | requirement |
|---|---|
| `target` | The ledger node this search is aimed at. Required. |
| `families` | Approach families. Optional list. |
| `approaches` | Individual routes. Optional list. |

### Families

| field | requirement / meaning |
|---|---|
| `id` | `fam:<slug>`, unique. Namespaced so it can never be mistaken for a node or candidate id. |
| `mechanism` | One or two sentences: what this family actually tries. Required. |
| `state` | `active`, `saturated`, or `parked`. |
| `saturation_checkpoint` | The checkpoint that closed the family. Required iff not `active`, forbidden otherwise. |
| `reopen_if` | The condition under which the family reopens. Same rule. |

A closed family may have no `active` approach: either the route is still running, in
which case the family is not closed, or it is not, in which case say so.

Saturation is a `synthesizer` judgment. The checker can insist that a declaration carries
its synthesis and its reopening condition; it cannot infer mathematical exhaustion from
attempt counts, and neither can elapsed time.

### Approaches

| field | requirement / meaning |
|---|---|
| `id` | `ap:<slug>`, unique. |
| `family` | The family this route belongs to. Required, and must resolve. |
| `parent` | The approach this one grew out of, in the same family. Optional, acyclic. |
| `state` | `queued`, `active`, `blocked`, `completed`, or `duplicate`. |
| `blocker` | The exact `cand:` id or ledger node id the route is stuck on. Required iff `blocked`. |
| `reopen_if` | What would unstick it. Same rule. |
| `related` | `{to, relation}` entries; `relation` is `overlaps`, `duplicates`, or `refines`. |
| `checkpoints` | Repo-relative `research/explorations/` records produced by this route. |

`parent` defines the tree, so siblings and descendants are derived rather than stored. A
descendant that leaves its parent's family is not a child: it is a new route with a
`refines` relation.

A blocker must resolve. If a route is important enough to be formally blocked, its
missing lemma is important enough to be stated precisely — as a candidate in the
checkpoint that found it, or as a ledger node. The portfolio does not copy that
statement.

An approach in state `duplicate` must say what it duplicates, and two approaches joined
by a `duplicates` relation may not both be `active`. Whether two routes are *really* the
same idea is a judgment; that they are not both being worked at once is checkable.

## Boundary

The portfolio holds no statements, no proofs, no status, and no second copy of the
dependency graph. It is not a place to record a result: a finding that survives its
attempt goes to a checkpoint, and a finding that earns reuse goes to the manuscript and
the ledger.

## Verify

```bash
python3 scripts/check.py --plane portfolio
python3 scripts/check.py portfolio          # the live search
```
