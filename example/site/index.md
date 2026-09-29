---
title: How much does centring cost?
numbering: false
relies-on:
  conj:example: {status: refuted, fingerprint: 6540a530455e2293a95ae5526312720c5cb8be9a13c7ac0bb519e67f3839dafd}
  prop:example: {status: proved, fingerprint: ea79eae68f7d2f1c5075b59892ece18383fc7cfbc4e38f1004beb0134c785e9a}
  prop:upper-constant: {status: proved, fingerprint: bf6de1113cb252456f59daaca4010bc0569f5496cda9b8aa92eddb84d66dc04b}
  prop:example-refuter: {status: proved, fingerprint: 1727ada4df69f811df0368d801df02c87a64533cb3429555cf7c021185a56495}
  conj:weighted-example: {status: open, fingerprint: 9307d75e616a807ae3a00f0e596ab5d28414f2f9e279e8d62986122ec675450a}
checked: 2026-09-29
---

% stamp: written by check.py --stamp; do not edit
*Last checked against the research record: 2026-09-29.*
% end stamp

Take real numbers $a_1,\dots,a_n$ and subtract their mean $\bar a$. The sum of squares can
only go down, and it goes down by exactly $n\bar a^2$:

$$
\sum_{i=1}^n (a_i - \bar a)^2 \;=\; \sum_{i=1}^n a_i^2 \;-\; n\,\bar a^2 .
$$

The question was whether a fixed fraction always survives, say
$\sum_i (a_i - \bar a)^2 \ge \tfrac12 \sum_i a_i^2$.

**Where things stand.** The identity above and the bound "centring never increases the sum
of squares" are proved. The fraction $\tfrac12$ is not: a constant vector loses everything
when it is centred, so no positive fraction survives. What remains open here is the
weighted form of the identity.

This is a demonstration project. The mathematics is deliberately elementary, so that the
shape of the site — problem, results, open questions — is what you look at.

## Where you can help

::::{grid} 1 1 2 2

:::{card} Problem 1 — Does the identity survive weighting?
:link: open/weighted-example.md
Replace the uniform mean by a weighted one. Is the centred sum still the sum of squares
minus the squared mean?
:::

::::

## Read further

- [The problem](problem.md): the question, and why constant vectors matter.
- [Results](results.md): what is proved, each with the idea of its proof.
- [About](about.md): how to contribute, and how results are checked.
