---
artifacts:
  - research/runs/2026-09-02-example.jsonl
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
copying from it is the point.

This is the first record of the example's search. The target is `conj:example`; the brief
is [`../program/brief.md`](../program/brief.md).

## Question examined

`ap:example-finite-battery`, the first route: does the available identity battery bear on
`conj:example`, and does its enumerated domain hold a witness against the conjecture?

`uv run research/runs/2026-09-02-example.py`, a seeded script whose output is the
artifact cited above. Two observations: a calibration of the two sides of the identity at
`prop:example` against each other on a sampled vector, and an exhaustive pass over the 625
integer vectors in $[-2,2]^4$.

## What we learned

**Observed: the run did not test the target.** The script checks the *identity* at `prop:example`,
not the inequality at `conj:example`, so its `witness: null` is a statement about a proved
node and say nothing whatever
about the conjecture. Worth writing down plainly, because a run that answers a question
nobody asked is easy to file as evidence for the question that was asked.

Two things did come out of it.

**Established by hand, not certified: a witness, found by reading the domain rather than
the output.** The enumerated box
$[-2,2]^4$ contains the constant vectors — where the brief, reading the fence
`prop:upper-constant`, says the target is weakest — and on any constant vector the left side of
`conj:example` is $0$ while the right side is positive. $a = (1,1)$ is the smallest case.
That is an observation about the inequality, made by hand; the run neither produced it nor
certifies it, which is exactly what a run can never do. It is
recorded above as `cand:example-constant-witness`.

## What resists

**The arithmetic.** The calibration residual was at the level of rounding
on this one sample, and nothing in this repository says how large it can get as $n$ grows. Until something does, a
near-equality reported by a run cannot be told apart from a violation. That is
`cand:example-identity-stability`, and it is what blocks `ap:example-roundoff-bound`.

## Proposed next step

Promote `cand:example-constant-witness` to a refuter node with a dossier and an independent
review: that decides `conj:example`. `cand:example-identity-stability` waits; nothing in
this search needs it yet.

Neither candidate is a node: neither has a manuscript statement, nothing depends on either, and nobody has proved
either. A candidate is a statement worth not losing, which is all it ever is. `cand:example-constant-witness` is about to earn a `:label:`, a node and a
dossier — see [`2026-09-03-example-refuter.md`](2026-09-03-example-refuter.md), which
closes it. This file stays exactly as it is either way.

Note what did *not* happen here: no ledger status moved. A witness is not a refutation.
