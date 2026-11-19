---
---

Worked example of a synthesis checkpoint: the orchestrator's reassessment of the portfolio
after a researcher's reply, written while the target is still unresolved. It is a fixture in
`example/`, not history. A real search writes one when the plan is reassessed, not after
every reply; here the plan changes, but "no change to the plan" would be as valid a
conclusion if this record said what was learned.

## Question examined

After [`2026-09-02-example-exploration.md`](2026-09-02-example-exploration.md), which route
of the portfolio bears on `conj:example`, and which mission is worth making next? The
routes are `ap:example-finite-battery` and `ap:example-roundoff-bound`; the target is still
`open`.

## What we learned

- **An obligation removed.** Before the exploration, reading the battery's output as
  evidence about `conj:example` required telling a near-equality from a violation, that is,
  `cand:example-identity-stability`. The witness `cand:example-constant-witness` is exact and
  checked by hand, so a refutation through it needs no floating-point bound: the target no
  longer waits on `ap:example-roundoff-bound`.
- **A useful result that settles nothing yet.** `cand:example-constant-witness` is
  *established* by hand, not certified. Until it is a node with a reviewed dossier, the
  target stays `open`.
- **An objective accomplished.** `ap:example-finite-battery` did what it set out to do: it
  decided that the run checks the identity at `prop:example`, not the target, and its domain
  yielded the witness. Nothing is left for it to try.

## What resists

- `cand:example-identity-stability` is open, and only `ap:example-roundoff-bound` rests on
  it. It no longer bears on the target.
- On the target, nothing beyond the ordinary channel: the witness has to become a node,
  receive a dossier, and pass an independent review.

## Proposed next step

**Mission.** A `researcher` on the `refute` lens, for `conj:example`: propose the manuscript
claim and ledger node `prop:example-refuter` for the vector $(1,1)$, and write its dossier.
Possible outcomes, and what each would teach:

- the dossier holds and a fresh reviewer passes it: `conj:example` can move to `refuted`
  through `refuted_by`, and the search ends;
- the witness fails a hypothesis of `conj:example` on a closer reading (say, the range of
  $n$): the brief's account of where the target is weakest is wrong, and the box
  $[-2,2]^4$ has to be read again;
- the reviewer finds that the dossier does not negate the exact quantified statement: the
  brief's negation needs repair before any further refutation attempt.

**Set aside.** `ap:example-roundoff-bound` stays `blocked` on
`cand:example-identity-stability`: an exact witness makes it unnecessary for the target, and
nothing else in this search needs it. `ap:example-finite-battery` closes with the refuter's
checkpoint, once the witness it found has been promoted.

**Reading path** for a fresh session:

1. [`../program/brief.md`](../program/brief.md) — the exact negation and what counts as a
   refutation;
2. [`2026-09-02-example-exploration.md`](2026-09-02-example-exploration.md) — the witness
   and the stability candidate;
3. [`../program/portfolio.yaml`](../program/portfolio.yaml) — the two routes and the
   blocker.
