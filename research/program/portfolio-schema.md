# Portfolio schema

This is the field contract for `portfolio.yaml` and for the front matter of `brief.md`.
Both are gated and absent by default — the scaffolds are
[`templates/portfolio.yaml`](../../templates/portfolio.yaml) and
[`templates/brief.md`](../../templates/brief.md), and filled-in instances are in
[`example/`](../../example/README.md). [`../../scripts/check.py`](../../scripts/check.py) is
the executable validator; [`../../CLAUDE.md`](../../CLAUDE.md) owns policy.

The governing separation:

> Ledger = what is mathematically claimed. Portfolio = what the search is doing.
> Checkpoints = why the portfolio changed.

Nothing in this file is a mathematical claim. A route has no truth value, an approach
family is not a theorem, and "saturated" is a judgment about effort rather than a fact
about mathematics. That is why none of it may enter the ledger, and why the portfolio
never restates a statement: it names a `cand:` id or a ledger node id and stops
(`CLAUDE.md` constraint 11).

## Activation

Both files are optional and absent by default. A repository with one target and one live
route coordinates itself; a portfolio that describes a search nobody is running is
overhead. Create the brief when a sustained search starts, and the portfolio when several
routes, agents, or sessions are in flight at once.

The two are not independent in both directions. **A portfolio requires a brief**: several
coordinated routes *are* a sustained search, and a search with no statement of what would
finish it is a search nobody can call off. The converse is not required — a brief with one
live route needs no portfolio.

## `brief.md`

```yaml
---
type: brief
target: q:main-conjecture
---
```

`target` must resolve to a ledger node of a claim-bearing kind — a `definition` is fixed by
decision and an `obstruction` is a fence the search reads, so neither is something a search
resolves — and must agree with `portfolio.yaml`'s `target` when both exist. The body is prose; the sections the template ships are what an agent
needs before it can attack the problem honestly — the exact negation, what counts as a
complete proof and a complete refutation, edge cases, known equivalent-strength traps,
the initial families, the blocked/reopen criteria, and a budget policy that permits an
honest unresolved outcome.

The brief does **not** own the target. The canonical quantified statement lives in
`modules/` under the node's `\label`; the brief names the node, may quote that statement
verbatim as a marked copy, and never sharpens it in place.

## `portfolio.yaml`

```yaml
target: q:main-conjecture

families:
  - id: fam:transport
    mechanism: Construct a transport or coupling argument.
    state: saturated
    closure_checkpoint: research/explorations/2026-09-03-transport-synthesis.md
    reopen_if: A construction avoiding cand:transport-compatibility is found.

approaches:
  - id: ap:transport-gluing
    family: fam:transport
    objective: Glue local transport maps across the overlap into one global map.
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
| `closure_checkpoint` | The checkpoint that closed the family. Required iff not `active`, forbidden otherwise, and must resolve to a parsed checkpoint. |
| `reopen_if` | The condition under which the family reopens. Same rule. |

`saturated` claims the mechanism is worked out. `parked` claims only that nobody is
working it — a budget or prioritization decision. The field is named for closure rather
than saturation so that it reads honestly for both.

A closed family holds no `active` **or** `queued` approach: a queued route is planned live
work, so either the family is not closed, or the route is not queued. Say which.

Saturation is a `synthesizer` judgment. The checker can insist that a declaration carries
its synthesis and its reopening condition; it cannot infer mathematical exhaustion from
attempt counts, and neither can elapsed time.

### Approaches

| field | requirement / meaning |
|---|---|
| `id` | `ap:<slug>`, unique. |
| `family` | The family this route belongs to. Required, and must resolve. |
| `objective` | One sentence: what *this* route tries. Required. |
| `parent` | The approach this one grew out of, in the same family. Optional, acyclic. |
| `state` | `queued`, `active`, `blocked`, `completed`, or `duplicate`. |
| `blocker` | The exact `cand:` id or ledger node id the route is stuck on. Required iff `blocked`. |
| `reopen_if` | What would unstick it. Same rule. |
| `related` | `{to, relation}` entries; `relation` is `overlaps`, `duplicates`, or `refines`. |
| `checkpoints` | Repo-relative `research/explorations/` records produced by this route. Required for `blocked`, `completed` and `duplicate`. |

A family says what *mechanism* it tries; `objective` says what this one route tries within
it. Without it a queued route was an id, a family and nothing else, legible only by reading
its slug — and two agents cannot notice they are duplicating a route neither can read. It
is coordination text: it names an intention, never a claim, and a route that needs to state
mathematics is a route whose missing lemma belongs in a checkpoint as a `cand:`.

`parent` defines the tree, so siblings and descendants are derived rather than stored. A
descendant that leaves its parent's family is not a child: it is a new route with a
`refines` relation.

The five states, precisely:

| state | means |
|---|---|
| `queued` | planned live work nobody has started |
| `active` | being worked now |
| `blocked` | stopped on a named `cand:` or node, with the condition that would reopen it |
| `completed` | **this route's objective is finished** — the mechanism was carried out and there is nothing left to try along it. It says nothing about the target's status: a route can complete and settle nothing. |
| `duplicate` | the same idea as another route, which it names through a `duplicates` relation |

When the target's own status becomes `proved` or `refuted`, no route may remain `active` or
`queued`. The search has its answer; closing the routes it settled is one `synthesizer` edit,
and leaving them open is how a portfolio starts describing a search nobody is running.

A blocker must resolve to a ledger node or a **live** candidate. If a route is important
enough to be formally blocked, its missing lemma is important enough to be stated precisely
— as a candidate in the checkpoint that found it, or as a ledger node. The portfolio does
not copy that statement.

When a candidate is promoted to a node, the routes blocked on it move with it: a `blocker`
naming a promoted candidate is an error that names the node to point at instead. Promotion
is one act — manuscript statement, ledger node, `promotes:` in the checkpoint, blockers
repointed — and this is the part of it the checker can see.

An approach in state `duplicate` must say what it duplicates, and two approaches joined
by a `duplicates` relation may not both be `active`. Whether two routes are *really* the
same idea is a judgment; that they are not both being worked at once is checkable.

## Every state change owes its checkpoint

*Checkpoints = why the portfolio changed.* That sentence is enforced, not merely stated:

1. A `blocked`, `completed` or `duplicate` approach names at least one checkpoint. A route
   does not stop without a reason the next agent can read.
2. Every `checkpoints:` entry and every `closure_checkpoint` resolves through the parsed
   checkpoint index, not merely to a file that exists. `research/explorations/README.md`
   is a file in the right directory and is not a checkpoint.
3. Every referenced record declares `approach:` and names the approach that lists it —
   or, for a `closure_checkpoint`, an approach in the closing family.

The reverse is deliberately **not** required: a checkpoint naming `approach: ap:x` need not
already appear in `ap:x`'s `checkpoints:`. A researcher writes the checkpoint and only the
`synthesizer` writes the portfolio, so requiring the back-link would make a red checker the
normal state between those two steps. Rule 3 gives the agreement without the deadlock.

## Boundary

The portfolio holds no statements, no proofs, no status, and no second copy of the
dependency graph. It is not a place to record a result: a finding that survives its
attempt goes to a checkpoint, and a finding that earns reuse goes to the manuscript and
the ledger.

## Verify

```bash
python3 scripts/check.py --lane portfolio
python3 scripts/check.py portfolio          # the live search
```
