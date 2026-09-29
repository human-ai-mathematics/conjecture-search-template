---
title: "Refutation: the centred sum of squares can vanish"
ledger-node: prop:example-refuter
---

% The worked example's refutation dossier. A refuter is an ordinary proved node with an
% ordinary dossier. What makes it a refutation is the ledger edge: conj:example carries
% refuted_by: [prop:example-refuter], and nothing about that edge lives here.

**What is being negated.** [](#conj:example) asserts, for *every* finite real sequence with
$n \ge 2$, that $\sum_i (a_i - \bar a)^2 \ge \tfrac12 \sum_i a_i^2$. The statement is
universally quantified over sequences, so a single admissible instance on which it fails
negates it exactly. No family and no limiting argument is
required, because the claimed inequality is not uniform in any parameter beyond the
sequence itself.

:::{prf:theorem} Form of the refuter
:label: thm:sol-prop-example-refuter
Let $a = (1,1)$, so $n = 2$. Then $\sum_{i=1}^2 (a_i - \bar a)^2 = 0$ while
$\tfrac12 \sum_{i=1}^2 a_i^2 = 1$. In particular
$\sum_{i=1}^2 (a_i - \bar a)^2 < \tfrac12 \sum_{i=1}^2 a_i^2$.
:::

:::{prf:proof}
The sequence is admissible: it is real and has $n = 2 \ge 2$. Its mean is
$\bar a = \tfrac12(1 + 1) = 1$, so $a_i - \bar a = 0$ for $i = 1,2$ and
$\sum_{i=1}^2 (a_i - \bar a)^2 = 0$. Independently, $\sum_{i=1}^2 a_i^2 = 1 + 1 = 2$, so
$\tfrac12\sum_{i=1}^2 a_i^2 = 1$. Since $0 < 1$, the asserted inequality fails at $a$. Every
quantity here is an exact rational computed in closed form; no numerical evaluation enters
the argument.

The same conclusion follows from [](#prop:example), which gives
$\sum_i (a_i - \bar a)^2 = \sum_i a_i^2 - n\bar a^2 = 2 - 2 = 0$; the direct computation
above is recorded so the dossier stands alone.
:::

**Fences respected.** [](#prop:example-refuter) has no `bounded_by`, but its target's fence
[](#prop:upper-constant) must hold at the witness, and does: $0 \le 2$. The fence's gap
$n\bar a^2$ here equals $\sum_i a_i^2 = 2$, its largest possible value — by
[](#prop:example) the gap never exceeds $\sum_i a_i^2$, with equality exactly on constant
vectors. The witness sits where the fence says the target is weakest.
