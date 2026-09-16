---
type: exploration
date: "2026-09-02"
approach: ap:example-finite-battery
nodes:
  - conj:example
  - prop:example
outcome: candidate
artifacts:
  - research/runs/2026-09-02T092336.680787Z-example.jsonl
candidates:
  - id: cand:example-constant-witness
    statement: >-
      The vector $a = (1,1)$ satisfies $\sum_i (a_i - \bar a)^2 = 0$ and
      $\tfrac{1}{2}\sum_i a_i^2 = 1$, so it violates the inequality of
      \texttt{conj:example}.
  - id: cand:example-identity-stability
    statement: >-
      Evaluated in floating point on a vector of $n$ entries, the two sides of
      $\sum_i (a_i-\bar a)^2 = \sum_i a_i^2 - n\bar a^2$ differ by at most
      $C n \varepsilon \sum_i a_i^2$ for an absolute constant $C$.
---

Worked example of a dated exploration, kept so the template ships one of each artifact
genre. It records no search anyone ran: it is a fixture in `example/`, not history, and
copying from it is the point (`CLAUDE.md` constraint 6).

This is the first record of the example's search. The target is `conj:example`; the brief
is [`../program/brief.md`](../program/brief.md).

## What was tried

`ap:example-finite-battery`, the first route: run the available identity battery, decide
whether it bears on `conj:example`, and inspect its enumerated domain for candidate
witnesses to the conjecture.

## How

`cd experiments && uv run python -m numerics run example --seed 20260902`, recorded in the
artifact cited above. Three observations: a calibration of the two sides of the identity at
`prop:example` against each other on a sampled vector, an exhaustive pass over the 625
integer vectors in $[-2,2]^4$, and a directional bound on the sample mean.

## Outcome

**The run did not test the target.** The `example` numerics target implements the *identity*
at `prop:example`, not the inequality at `conj:example`, so its `outcome: consistent` and
its `witness_found: false` are statements about a proved node and say nothing whatever
about the conjecture. Worth writing down plainly, because a run that answers a question
nobody asked is easy to file as evidence for the question that was asked.

Two things did come out of it.

**A witness, found by reading the domain rather than the output.** The enumerated box
$[-2,2]^4$ contains the constant vectors, and on any constant vector the left side of
`conj:example` is $0$ while the right side is positive. $a = (1,1)$ is the smallest case.
That is an observation about the inequality, made by hand; the run neither produced it nor
certifies it, which is exactly what `CLAUDE.md` constraint 2 says a run can never do. It is
recorded above as `cand:example-constant-witness`.

**A question about the arithmetic.** The calibration residual was $\sim 10^{-16}$ relative,
and nothing in this repository says what it should be as $n$ grows. Until something does, a
near-equality reported by a run cannot be told apart from a violation. That is
`cand:example-identity-stability`, and it is what blocks `ap:example-roundoff-bound`.

## Why these are candidates and not nodes

Neither has a manuscript statement, nothing depends on either, and nobody has proved
either. A candidate is a statement worth not losing, which is all it ever is (`CLAUDE.md`
constraint 7). `cand:example-constant-witness` is about to earn a `:label:`, a node and a
dossier — see [`2026-09-03-example-refuter.md`](2026-09-03-example-refuter.md), which
promotes it. `cand:example-identity-stability` is still live, and this file stays exactly
as it is either way.

Note what did *not* happen here: no ledger status moved. A witness is not a refutation.
