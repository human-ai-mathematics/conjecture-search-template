---
type: brief
target: {{TARGET_NODE}}
---

# Problem brief

<!-- UNWRITTEN — this brief is still the scaffold. Rewrite every section below for
     your target: they are the ones an agent needs before it can attack a conjecture
     honestly, and `python3 scripts/check.py ready` fails while these instructions are
     still here. A filled-in instance of every section is in
     example/research/program/brief.md. -->

The harness remembers, validates and certifies. It does not supply mathematical
pressure. That is this file's job: it is the one document that knows how the target
usually fails, what would count as finishing, and which disguises a dead route wears.

It is a mutable, single-writer document owned by the orchestrator (`brief` concurrency
key), and it owns none of the mathematics. Three things, three homes:

| what | where |
|---|---|
| the canonical quantified target | `modules/`, under the target node's `\label` |
| its identity, status, provenance and relations | [`ledger.yaml`](ledger.yaml) |
| its negation, completion criteria, edge cases, traps and search policy | this file |

## The target

Name the ledger node and its manuscript anchor, then quote the manuscript statement
verbatim below, so an agent gets the exact quantifiers without a second hop. The
blockquote is a **copy, not a source**: if it and the manuscript disagree, the manuscript
is right and the copy is a defect, which is what the `reviewer`'s `sync` lens checks
(`CLAUDE.md` constraint 7). Never sharpen the statement here — sharpen it in `modules/`
and re-copy.

Where a definition is doing real work — a convention, a sign, a scaling — name the
`kind: definition` node it rests on.

> **Target** `{{TARGET_NODE}}`, stated at `\label{{{TARGET_NODE}}}` in
> [`../../modules/`](../../modules/). Replace this blockquote with the manuscript
> statement, copied verbatim.

## The exact negation

Write the logical negation, with quantifier order intact, before anyone attacks it. A
single witness refutes a universal claim; failure of a dimension-free or uniform constant
generally requires a certified family with the relevant divergence (`CLAUDE.md`
constraint 10). Say which of the two shapes a refutation of *this* target must have.

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
conventions, the places where this particular statement's authors did not look.

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
reopened. The live version of that state is `portfolio.yaml`, once the portfolio gate
opens; this section is the reasoning behind the initial seeding, not a second copy of it.

## Budget policy

What the search does when it does not succeed. The honest outcome — unresolved, with
certified advances and exact remaining gaps — must be permitted and reportable. Elapsed
time is not a measure of search quality: it says nothing about approach exhaustion,
duplicated work, or novelty. Terminate on saturation of the portfolio, not on a clock.
