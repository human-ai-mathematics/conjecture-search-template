---
type: exploration
date: "2026-09-02"
nodes:
  - q:example
outcome: candidate
artifacts:
  - research/runs/2026-09-02T092336.680787Z-example.jsonl
candidates:
  - id: cand:example-identity-stability
    statement: >-
      Evaluated in floating point on a vector of $n$ entries, the two sides of
      $\sum_i (a_i-\bar a)^2 = \sum_i a_i^2 - n\bar a^2$ differ by at most
      $C n \varepsilon \sum_i a_i^2$ for an absolute constant $C$.
---

Worked example of a dated exploration, kept so the template ships one of each artifact
genre. It records no search anyone ran: it is a fixture in `example/`, not history, and
copying from it is the point (`CLAUDE.md` constraint 7).

## What was tried

Nothing was proved. The `example` numerics target was run once at seed `20260902` to see
what `q:example` looks like from the numerical side, and to check that the identity at
`prop:example` survives a finite integer family.

## How

`cd experiments && uv run python -m numerics run example --seed 20260902`, recorded in the
artifact cited above. Three observations: a calibration of the two sides of the identity
against each other on a sampled vector, an exhaustive search over the 625 integer vectors
in $[-2,2]^4$, and a directional bound on the sample mean.

## Outcome

The search returned `outcome: consistent` with no witness. That is exactly the situation
`obs:example` fences: agreement across 625 vectors constrains nothing about the vectors not
tried, so no ledger status moves and none is proposed here.

What the run did surface is a question the search cannot answer, because it is about the
arithmetic rather than the identity: the calibration residual was $\sim 10^{-16}$ relative,
and nothing in this repository says what it should be as $n$ grows. That is recorded above
as `cand:example-identity-stability`.

## Why the candidate is not a node

It has no manuscript statement, nothing depends on it, and nobody has tried to prove it. It
is a statement worth not losing, which is all a candidate ever is (`CLAUDE.md` constraint
8). If a later attempt uses it, it earns a `\label` in `modules/`, a ledger node, and a
dossier; if a later exploration kills it, that exploration names it in `retires:` and this
file stays exactly as it is.
