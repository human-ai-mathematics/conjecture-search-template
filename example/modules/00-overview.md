% The worked example's module. Every labelled claim directive here is a node in
% example/research/program/ledger.yaml with the same id; the heading label is
% structural. It holds a proved statement with a dossier, a proved fence, an open
% conjecture under an open fence, and a conjecture refuted by a proved refuter.

(sec:overview)=
# Orientation

+++ {"part": "abstract"}

A fixture: one complete search, from a precise conjecture to a certified refutation, with
one instance of every file genre the harness validates.

+++

## A proved statement

:::{prf:proposition}
:label: prop:example
Let $a_1,\dots,a_n \in \R$ and let $\bar a = n^{-1}\sum_{i=1}^n a_i$. Then
$\sum_{i=1}^n (a_i - \bar a)^2 = \sum_{i=1}^n a_i^2 - n \bar a^2$.
:::

Its proof is the dossier `solutions/prop-example.md`, certified by a review under
`research/reviews/`.

## A proved fence

A fence is an ordinary claim other nodes cite in `bounded_by`. Once proved it binds: a
statement that violates it is wrong by construction. State both halves: what it rules out
and what it leaves open.

:::{prf:proposition}
:label: prop:upper-constant
Let $a_1,\dots,a_n \in \R$ with $n \ge 1$. Then
$\sum_{i=1}^n (a_i - \bar a)^2 \le \sum_{i=1}^n a_i^2$, with equality if and only if
$\bar a = 0$.
:::

*Rules out.* Every lower bound $\sum_i (a_i - \bar a)^2 \ge c \sum_i a_i^2$ with $c > 1$:
any nonzero centred vector violates it.

*Leaves open.* Every constant $c \le 1$ — in particular the $\tfrac12$ of
[](#conj:example), which this fence bounds.

## An open conjecture under an open fence

An open fence is a plausible barrier: it guides the work on the claims it bounds and rules
nothing out until it is proved. Status records what has been established, never what is
expected: both claims below are almost certainly easy, and stay `open` until a dossier is
certified.

:::{prf:conjecture}
:label: conj:weighted-upper
Fix weights $w_1,\dots,w_n > 0$ with $\sum_{i=1}^n w_i = 1$ and write
$\bar a_w = \sum_{i=1}^n w_i a_i$. Then
$\sum_{i=1}^n w_i (a_i - \bar a_w)^2 \le \sum_{i=1}^n w_i a_i^2$ for all real
$a_1,\dots,a_n$.
:::

:::{prf:conjecture}
:label: conj:weighted-example
[](#prop:example) survives weighting. With $w$ and $\bar a_w$ as in
[](#conj:weighted-upper),

$$
\sum_{i=1}^n w_i (a_i - \bar a_w)^2 = \sum_{i=1}^n w_i a_i^2 - \bar a_w^2
$$

for all real $a_1,\dots,a_n$.
:::

## A refuted conjecture — the worked search's target

The refuter is a proved node of its own, named in the target's `refuted_by` and never in its
`depends_on`.

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
