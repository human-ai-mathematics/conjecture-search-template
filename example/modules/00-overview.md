
% The worked example's module. Every labelled claim directive here — prf:theorem,
% prf:conjecture, and the other six ledger kinds — is a node in this example's ledger,
% example/research/program/ledger.yaml, with a matching `kind`. The heading label below
% is structural and is not a node. The shape worth copying: an open barrier that fences
% the search, an open conjecture, a proved statement carrying a dossier, and a
% conjecture refuted by a proved refuter.

(sec:overview)=
# Orientation

+++ {"part": "abstract"}

A fixture: one complete search, from a precise conjecture to a certified refutation, with
one instance of every artifact genre the harness validates.

+++

Replace this module. It exists so that a freshly cloned template is green under every
validator, and so that each artifact genre has one worked example to copy.

A convention this program fixes — a sign, a scaling, a log base, which constant absorbs
what — is stated here in a `prf:definition` directive under its own `:label:` and carries
a ledger node with `kind: definition` and `status: defined`. Claims resting on it name it
in `depends_on`, so changing it is a mathematical edit the checker can see. There is no
separate notation or normalization file: a second list would be a copy of the dependency
graph that nothing keeps honest.

## A fence

A fence is a statement the search reads *before* a proof is attempted or a numerical run
is spent (`CLAUDE.md` constraint 5). It is not a kind of node: it is an ordinary claim,
written in the directive matching its mathematical form, that other nodes cite. A proved
one bounds them through `bounded_by`, and a statement violating it is wrong by
construction; an open one only warns, through `heuristic_barriers`. It is stated here,
rather than in a registry of its own, because a fence is only useful next to the
mathematics it fences.

State both halves. A fence that records only what it rules out, or only that something
is hard, fences nothing: the escape routes are what the next agent reads.

:::{prf:conjecture} A barrier on numerical evidence
:label: conj:finite-battery
*Rules out.* Establishing a universal statement from a finite battery of instances.
Agreement across every instance tried constrains nothing about the untried ones, so no
run — however large — discharges a universal claim.

*Leaves open.* Refutation. One instance suffices to refute a universal statement, and an
exact arithmetic witness for such an instance is a genuine candidate — though it still
requires an independently reviewed refutation dossier before it carries logical force
(`CLAUDE.md` constraint 2).
:::

## An open conjecture

An `open` node is one nobody has discharged. It carries no proof provenance, and saying
it is "probably true" is not a ledger classification — the conjecture below is elementary
and almost certainly has a one-line proof, and it stays `open` until someone writes that
proof into a dossier and a reviewer checks it. Status records what has been established,
never what is expected. An open question is written this way too: as a conjecture, in the
direction the search is trying to establish, so that it has an exact negation.

:::{prf:conjecture}
:label: conj:weighted-example
[](#prop:example) survives weighting. Fix weights $w_1,\dots,w_n > 0$ with
$\sum_{i=1}^n w_i = 1$ and write $\bar a_w = \sum_{i=1}^n w_i a_i$. Then

$$
\sum_{i=1}^n w_i (a_i - \bar a_w)^2 = \sum_{i=1}^n w_i a_i^2 - \bar a_w^2
$$

for all real $a_1,\dots,a_n$.
:::

## A proved statement

:::{prf:proposition}
:label: prop:example
Let $a_1,\dots,a_n \in \R$ and let $\bar a = n^{-1}\sum_{i=1}^n a_i$. Then
$\sum_{i=1}^n (a_i - \bar a)^2 = \sum_{i=1}^n a_i^2 - n \bar a^2$.
:::

The proof is a standalone dossier, `solutions/prop-example.md`, certified by an
independent review under `research/reviews/`. The manuscript states the result; the
dossier is what an independent reviewer checks (`solutions/README.md`).

## A refuted conjecture — the worked search's target

This is the statement the example's problem brief and search portfolio are organized
around, and the one the routes attack. Refutation ends where proof ends: in a certified
dossier. The witness itself is not the refutation — it is a candidate until the statement
it establishes is a node of its own, proved and independently reviewed. Only then does
the target become `refuted`, naming that node in `refuted_by` and nowhere else. The
refuter is *not* a `depends_on` of what it refutes: that field records facts a proof used,
and a refuted statement has no proof.

:::{prf:conjecture}
:label: conj:example
For all real $a_1,\dots,a_n$ with $n \ge 2$,
$\sum_{i=1}^n (a_i - \bar a)^2 \ge \tfrac{1}{2}\sum_{i=1}^n a_i^2$.
:::

:::{prf:proposition}
:label: prop:example-refuter
The sequence $a = (1,1)$ satisfies $\sum_{i=1}^2 (a_i - \bar a)^2 = 0$ and
$\tfrac{1}{2}\sum_{i=1}^2 a_i^2 = 1$. Hence [](#conj:example) is false.
:::

One instance suffices because the conjecture is universally quantified over sequences. A
dimension-free or uniform constant would instead need a certified family along which the
relevant quantity diverges (`CLAUDE.md` constraint 10).
