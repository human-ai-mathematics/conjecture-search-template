---
type: exploration
date: "2026-09-03"
approach: ap:example-exhaustive-search
outcome: directional
nodes:
  - q:example
---

Worked example of the second thing a checkpoint does: explain a *search* change rather than
a mathematical one. It is also the template's only record carrying `approach:`. Delete it
with the rest of the worked example — see the list in the root `README.md`.

## What was tried

`ap:example-exhaustive-search` was queued as a fresh route: enumerate the integer vectors
in a box and check the identity at `prop:example` on each. Before spending anything on it,
the existing routes were read.

## How

`python3 scripts/check.py portfolio`, then the checkpoint already attached to
`ap:example-finite-battery`, `research/explorations/2026-09-02-example-exploration.md`. That
route had already run exactly this enumeration — 625 vectors in $[-2,2]^4$ — through the
`example` numerics target, and recorded it in a provenance-stamped artifact.

## Outcome

The route is a duplicate, not a refinement: it proposes the same mechanism on the same
objects, differing only in the box. It is marked `duplicate` against
`ap:example-finite-battery` and is not being worked.

Widening the box is not a new route either. `obs:example` fences the whole family:
agreement across any finite battery constrains nothing about the instances not tried, so a
larger enumeration buys a larger silence.

## Why this is durable

The judgment cost something to reach — it required reading another route's artifact — and
without a record the next agent queues the same idea under a third name. That is the third
of the six triggers in [`README.md`](README.md): a checkpoint is owed when work blocks,
reopens, duplicates, or saturates a portfolio approach.

Nothing here is a mathematical claim, and no candidate is proposed. Deduplication is search
state; the portfolio holds the resulting relation and this file holds the reason
(`CLAUDE.md` constraint 12).
