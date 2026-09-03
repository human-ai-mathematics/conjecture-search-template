---
type: brief
target: q:example
---

# Problem brief

<!-- This is the worked example's brief, pointing at the seed node q:example. Rewrite
     it for this repository's real target — do not delete it and start a sustained
     search without one. The sections below are the ones an agent needs before it can
     attack a conjecture honestly; each says what belongs in it. -->

The harness remembers, validates and certifies. It does not supply mathematical
pressure. That is this file's job: it is the one document that knows what the target
actually says, how it usually fails, and what would count as finishing.

It is a mutable, single-writer document owned by the orchestrator (`brief` concurrency
key). It carries no claim status: the statement itself lives in `modules/` under its
`\label`, and its logical state lives in [`ledger.yaml`](ledger.yaml).

## The exact statement

State the target with every quantifier, in this repository's normalization. Name the
ledger node and its manuscript anchor. Where a definition is doing real work — a
convention, a sign, a scaling — name the `kind: definition` node it rests on.

> `q:example`: placeholder for the question this repository is organized around. Replace
> it with a precise statement someone could prove or refute.

## The exact negation

Write the logical negation, with quantifier order intact, before anyone attacks it. A
single witness refutes a universal claim; failure of a dimension-free or uniform constant
generally requires a certified family with the relevant divergence (`CLAUDE.md`
constraint 11). Say which of the two shapes a refutation of *this* target must have.

## What counts as complete

Two lists, both explicit.

**A complete proof** must establish exactly the statement above, with no extra
hypotheses. Name the weakenings that do *not* count — a special case, a bounded-parameter
version, a result conditional on an open antecedent — so that partial progress is
recorded as partial rather than presented as the answer.

**A complete refutation** must negate the exact quantified statement, through a certified
dossier, with `refuted_by` naming proved refuters.

## Edge cases and audit tests

The problem-specific checks a reviewer must run — the degenerate instances, the boundary
conventions, the places where this particular statement's authors did not look. For the
worked example, the checkable trap is stated at `obs:example`: agreement across a finite
battery constrains nothing about the instances not tried.

A generic instruction to be rigorous is worth much less than a list of the five things
that actually go wrong in this problem. Add to this list every time a review catches
something.

## Traps and circular reductions

Reductions that land on a lemma of the same strength as the target, equivalences known in
the literature, and any route that would quietly assume the conclusion. A route that ends
at an equivalent-strength lemma is not close to done: record it here so the next agent
recognizes it in a new disguise.

## Initial families and their reopening criteria

The approach families worth starting from, and what would make each one blocked or
reopened. The live version of that state is [`portfolio.yaml`](portfolio.yaml); this
section is the reasoning behind the initial seeding, not a second copy of it.

## Budget policy

What the search does when it does not succeed. The honest outcome — unresolved, with
certified advances and exact remaining gaps — must be permitted and reportable. Elapsed
time is not a measure of search quality: it says nothing about approach exhaustion,
duplicated work, or novelty. Terminate on saturation of the portfolio, not on a clock.
