---
title: "Solution: the centred sum of squares"
ledger-node: prop:example
refines: [prop:example]
bounded_by: []
author: /root/template_author
date: "2026-09-01"
exports:
  - format: pdf+tex
    template: ../../templates/latex
---

% The worked example's proof dossier. The front matter above is its header: scripts/check.py
% reads `ledger-node`, `refines`, `bounded_by`, `author` and `date`, and nothing else of
% the harness's belongs there. The `exports` entry makes the dossier build standalone.

**Refined statement.** This is the statement of [](#prop:example) verbatim; nothing is
strengthened. A real dossier states the sharp current form and says which fence shapes it.

:::{prf:theorem} Form of Proposition 1
:label: thm:sol-prop-example
Let $a_1,\dots,a_n \in \R$ with $n \ge 1$, and set $\bar a = n^{-1}\sum_{i=1}^n a_i$. Then

$$
\sum_{i=1}^n (a_i - \bar a)^2 \;=\; \sum_{i=1}^n a_i^2 \;-\; n\,\bar a^2 .
$$
:::

:::{prf:proof}
Expand the square termwise:

$$
\sum_{i=1}^n (a_i - \bar a)^2
  = \sum_{i=1}^n a_i^2 - 2\bar a \sum_{i=1}^n a_i + n \bar a^2 .
$$

By the definition of $\bar a$ we have $\sum_{i=1}^n a_i = n \bar a$, so the middle term
equals $-2 n \bar a^2$. Hence the right-hand side is
$\sum_{i=1}^n a_i^2 - 2n\bar a^2 + n\bar a^2 = \sum_{i=1}^n a_i^2 - n\bar a^2$, which is
the claim. Every step is an identity in $\R$; no hypothesis beyond $n \ge 1$ is used, and
none is used implicitly.
:::

**Fences respected.** None apply: the statement is a finite algebraic identity, and
[](#conj:finite-battery) fences universal claims argued from finite batteries, which this
proof does not do.
