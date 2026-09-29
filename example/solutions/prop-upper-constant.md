---
title: "Solution: centring never increases the sum of squares"
ledger-node: prop:upper-constant
---

% The worked example's fence dossier. A fence is proved like any other node; what makes it
% a fence is that conj:example cites it in bounded_by.

**Refined statement.** The statement of [](#prop:upper-constant) verbatim, with the gap
named exactly.

:::{prf:theorem} Form of the fence
:label: thm:sol-prop-upper-constant
Let $a_1,\dots,a_n \in \R$ with $n \ge 1$, and set $\bar a = n^{-1}\sum_{i=1}^n a_i$. Then

$$
\sum_{i=1}^n a_i^2 \;-\; \sum_{i=1}^n (a_i - \bar a)^2 \;=\; n\,\bar a^2 \;\ge\; 0 ,
$$

with equality if and only if $\bar a = 0$.
:::

:::{prf:proof}
By [](#prop:example), $\sum_{i=1}^n (a_i - \bar a)^2 = \sum_{i=1}^n a_i^2 - n\bar a^2$,
which is the displayed identity. Since $n \ge 1$ and $\bar a^2 \ge 0$, the gap $n\bar a^2$
is nonnegative, and it vanishes exactly when $\bar a = 0$. No hypothesis beyond $n \ge 1$
is used.
:::

**Fences respected.** None apply: [](#prop:upper-constant) has no `bounded_by`.
