---
title: Problem 1 — Does the identity survive weighting?
numbering: false
problem: conj:weighted-example
relies-on:
  conj:weighted-example: {status: open, fingerprint: 9307d75e616a807ae3a00f0e596ab5d28414f2f9e279e8d62986122ec675450a}
  conj:weighted-upper: {status: open, fingerprint: b805a02c4433a51aebf78d7496e145d410e08a7cf9f8410366a1ad4836810afb}
checked: 2026-09-29
---

% stamp: written by check.py --stamp; do not edit
**Status: open.** *Last checked against the research record: 2026-09-29.*
% end stamp

**In one sentence.** If the plain mean is replaced by a weighted mean, is the centred sum
of squares still the sum of squares minus the squared mean?

**Statement.** Fix weights $w_1,\dots,w_n > 0$ with $\sum_i w_i = 1$, and let
$\bar a_w = \sum_i w_i a_i$ be the weighted mean of real numbers $a_1,\dots,a_n$. Show
that

$$
\sum_{i=1}^n w_i (a_i - \bar a_w)^2 = \sum_{i=1}^n w_i a_i^2 - \bar a_w^2 .
$$

The exact statement on record is [](#conj:weighted-example).

**Why it matters.** With equal weights $w_i = 1/n$ this is [Theorem A](#site:thm-identity),
divided by $n$. The weighted form is the one probability uses: for a random variable
taking the value $a_i$ with probability $w_i$, it says that the variance is the second
moment minus the squared mean. In that form it is classical. This card is open *in this
record* only: no checked proof has been written here. It is published to show what a
problem card looks like, not as a research question.

**What you need to know.** The proof of [Theorem A](#site:thm-identity), and the fact that
the weights sum to $1$.

**What we tried.** Nothing yet. The search recorded here targeted the unweighted
conjecture, and no attempt was made on this one.

**Evidence.** One case checked by hand, which is evidence and not a proof. For $n = 2$,
$w = (\tfrac13, \tfrac23)$ and $a = (0, 3)$: $\bar a_w = 2$, the left side is
$\tfrac13 \cdot 4 + \tfrac23 \cdot 1 = 2$, and the right side is $\tfrac23 \cdot 9 - 4 = 2$.

**Where to start.**
- Expand the square as in Theorem A. The step that used $\sum_i a_i = n\bar a$ now uses
  $\sum_i w_i a_i = \bar a_w$, and the constant terms use $\sum_i w_i = 1$.
- The companion inequality
  $\sum_i w_i (a_i - \bar a_w)^2 \le \sum_i w_i a_i^2$ ([](#conj:weighted-upper)) is
  also open here and follows at once from the identity.

**Contribute.** See [How to contribute](../about.md). Cite this problem as
`conj:weighted-example`.
