---
target: conj:main
---

# Problem brief

<!-- Copy to research/program/brief.md and rewrite every section for your target. Only the
     orchestrator writes it. A filled-in instance is example/research/program/brief.md. -->

The harness remembers, validates and certifies; it does not supply mathematical pressure.
This file does: it knows how the target usually fails, what would count as finishing, and
which disguises a dead route wears. It owns none of the mathematics — the statement lives in
`modules/`, its status in the ledger.

## The target

`conj:main`, stated at `:label: conj:main` in `modules/` — read it there; this file never
copies it. Say where the statement is vulnerable, and name any `definition` node it rests
on.

## The exact negation

The logical negation, quantifier order intact. Say whether a refutation needs one witness or
a certified divergent family.

## What counts as complete

**A complete proof** establishes exactly the target statement. Name the weakenings that do
*not* count — special cases, bounded-parameter versions, results conditional on an open
antecedent.

**A complete refutation** negates the exact quantified statement through a certified
dossier, with `refuted_by` naming proved refuters.

## Edge cases and audit tests

The degenerate instances, boundary conventions and blind spots a reviewer must check for
this problem. Add to this list every time a review catches something.

## Traps and circular reductions

Reductions landing on a lemma of the same strength as the target, known equivalences, and
routes that quietly assume the conclusion. Also any rule specific to this program — for
instance a comparison only one agent may hold at a time.

## Neighbourhood

A few statements near the target worth examining because they bear on it — a special case,
a weakening, a reformulation — each a ledger node or a `cand:` candidate, by id. A refuted
target stays closed; a corrected version is a new statement with a new id.

- `conj:special-case` — why settling it would inform the target.

## Routes

One line per route while one agent works at a time; move them to
`research/program/portfolio.yaml` and delete this section once several run at once.

- `ap:main-route` — active. One sentence saying what this route tries.
- `ap:other-route` — blocked on `cand:slug`. What it would try once unblocked.

## Budget policy

The honest outcome — unresolved, with certified advances and exact remaining gaps — is
permitted. Stop when no route is left worth running, not on a clock.
