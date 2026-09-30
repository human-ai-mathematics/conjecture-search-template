# Goal

**A template that gives AI-driven research on a mathematical conjecture a simple, clear
structure — so that what the search establishes can be trusted, and mathematicians can
read it, check it and take part without learning the machinery.**

This file says *why* the template exists and how to judge a change to it.
[`SPECIFICATION.md`](SPECIFICATION.md) says *what the rules are*;
[`README.md`](README.md) says *how to run it*.

## The problem

AI agents can now produce a large volume of mathematical work on a hard question: proof
attempts, reductions, numerical experiments, candidate counterexamples. Left unstructured,
that volume works against the research:

- what was learned is lost between sessions, and dead ends are explored again;
- a plausible argument, a numerical trend or an agent's confidence is mistaken for a result;
- a mathematician facing the output cannot tell what is proved, what is open, and where
  they could help.

## Three aims

1. **Organize the search.** One target statement, a portfolio of routes, missions with an
   expected result, and dated checkpoints — so that several agents over many sessions work
   as one search, and an obstacle found once, or a route set aside, is never rediscovered.
2. **Make every status trustworthy.** A claim is `proved` or `refuted` only through a
   certification that someone other than its author has made — an independent review or a
   named human — and that certification is tied to the exact text it saw. Evidence guides
   the search; it never moves a status.
3. **Open the research to mathematicians.** The manuscript reads like a paper written for
   someone who has never seen the repository: the question, worked examples, what is
   settled and what is not, the idea of each proof, where to start. A mathematician
   contributes through a plain issue — a counterexample, an idea, a correction — and their
   acceptance of a proof counts as a certification.

## What success looks like

- A mathematician who has never seen the repository can, from the published site alone,
  say within minutes what the question is, what is established, what remains open, and
  where they could contribute.
- Every `proved` or `refuted` status can be traced to a certified dossier or to the
  literature, and editing what was certified visibly lifts the certification.
- A new session or agent can resume the search from the checker's summary and the latest
  checkpoints, without re-reading the whole history.
- A failed route leaves behind the obstacle that stopped it; a negative result is a result.
- A new program is instantiated from the template in an hour, and a fresh clone passes the
  check.

## Out of scope

- **Theory building and classification.** The template is tuned for proving or refuting
  one hard statement, not for developing a field.
- **Formal verification.** Certification is review-based; a formal proof may support a
  review but is not what the template checks.
- **Replacing mathematical judgment.** The checker validates structure only. Which route
  to pursue, and whether a proof is right, remain decisions made by a reader.

## Judging a change to the template

A change should make the search more reliable, the record more trustworthy, or
participation easier — without costing the other two. Simplicity is part of the goal:
every file, field and rule must earn its place, and a rule that can be removed without
losing a guarantee should be. When the needs of an agent and of a human reader conflict
over the manuscript, the reader wins.

## A template, adapted by each program

This is a template: each program instantiated from it studies its own question, and may
adapt the template to what that question needs — its macros and normalizations, the traps
and rules specific to its field in the brief, the kinds of computation it runs, how its
manuscript is organized, even a genre of file the template does not have.

What a program should keep are the guarantees that make its results readable and
trustworthy to someone outside it: a status earned only through independent certification,
one home for each statement, a record that is not rewritten, and a manuscript written for
a mathematician. A program that departs from one of them says so, and why, in its brief.
An adaptation that proves useful beyond one program is worth bringing back to the template.

In an instantiated repository, the program's own goal lives in the brief and the
manuscript's overview; this file describes the template itself.
