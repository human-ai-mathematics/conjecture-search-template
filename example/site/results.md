---
title: Results
numbering:
  equation: false
relies-on:
  prop:example: {status: proved, fingerprint: ea79eae68f7d2f1c5075b59892ece18383fc7cfbc4e38f1004beb0134c785e9a}
  prop:upper-constant: {status: proved, fingerprint: bf6de1113cb252456f59daaca4010bc0569f5496cda9b8aa92eddb84d66dc04b}
  prop:example-refuter: {status: proved, fingerprint: 1727ada4df69f811df0368d801df02c87a64533cb3429555cf7c021185a56495}
  conj:example: {status: refuted, fingerprint: 6540a530455e2293a95ae5526312720c5cb8be9a13c7ac0bb519e67f3839dafd}
checked: 2026-09-29
---

% stamp: written by check.py --stamp; do not edit
*Last checked against the research record: 2026-09-29.*
% end stamp

Throughout, $a_1,\dots,a_n$ are real numbers, $n \ge 1$, and
$\bar a = \frac1n\sum_{i=1}^n a_i$ is their mean.

## Main results

:::{prf:theorem} The centring identity
:label: site:thm-identity
:enumerator: A
$$
\sum_{i=1}^n (a_i - \bar a)^2 = \sum_{i=1}^n a_i^2 - n\,\bar a^2 .
$$
:::

**Idea of the proof.** Expand each square. The cross terms add up to
$-2\bar a \sum_i a_i = -2n\bar a^2$, because $\sum_i a_i = n\bar a$ is the definition of
the mean. The constant terms add up to $+n\bar a^2$, and the two combine into
$-n\bar a^2$.

:::{dropdown} The computation in one line
$$
\sum_i (a_i - \bar a)^2
= \sum_i a_i^2 - 2\bar a \sum_i a_i + n\bar a^2
= \sum_i a_i^2 - 2n\bar a^2 + n\bar a^2 .
$$
:::

[Full proof →](#thm:sol-prop-example) · [Precise statement →](#prop:example)

:::{prf:theorem} Centring never increases the sum of squares
:label: site:thm-upper
:enumerator: B
$$
\sum_{i=1}^n (a_i - \bar a)^2 \le \sum_{i=1}^n a_i^2 ,
$$
with equality if and only if $\bar a = 0$.
:::

**Idea of the proof.** By [Theorem A](#site:thm-identity) the difference between the two
sides is exactly $n\bar a^2$, which is nonnegative and vanishes only when the mean does.

[Full proof →](#thm:sol-prop-upper-constant) · [Precise statement →](#prop:upper-constant)

## Counterexample

:::{prf:theorem} No fixed fraction survives centring
:label: site:thm-counterexample
:enumerator: C
For $a = (1,1)$, the centred sum of squares is $0$, while $\tfrac12\sum_i a_i^2 = 1$.
Hence the inequality $\sum_i (a_i - \bar a)^2 \ge \tfrac12 \sum_i a_i^2$ fails, and the
conjecture [](#conj:example) is false.
:::

**Idea of the proof.** The vector is constant, so it equals its mean and centring sends it
to zero. The same happens to every nonzero constant vector, so no fraction $c > 0$ can
replace $\tfrac12$. By [Theorem A](#site:thm-identity), constant vectors are exactly the
vectors where the loss $n\bar a^2$ equals the whole of $\sum_i a_i^2$: the counterexample
sits where the bound is weakest.

**What it teaches.** A lower bound on the centred sum must depend on the spread of the
vector, not only on its size. Any corrected conjecture has to exclude constant vectors,
for instance by assuming $\bar a = 0$, and then it becomes trivial by Theorem A.

[Full proof →](#thm:sol-prop-example-refuter) · [Precise statement →](#prop:example-refuter)
