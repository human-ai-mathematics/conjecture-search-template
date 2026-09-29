---
title: The problem
numbering: false
relies-on:
  conj:example: {status: refuted, fingerprint: 6540a530455e2293a95ae5526312720c5cb8be9a13c7ac0bb519e67f3839dafd}
  prop:upper-constant: {status: proved, fingerprint: bf6de1113cb252456f59daaca4010bc0569f5496cda9b8aa92eddb84d66dc04b}
checked: 2026-09-29
---

% stamp: written by check.py --stamp; do not edit
*Last checked against the research record: 2026-09-29.*
% end stamp

## The question

Centring a list of numbers — subtracting its mean — is the first step of almost every
statistical computation. It changes the sum of squares, and it is natural to ask by how
much. Can centring destroy most of a vector's energy, or does a fixed fraction always
survive? The conjecture this project examined proposed the fraction one half:

:::{embed} #conj:example
:::

## An example by hand

Take $a = (1, 2, 3)$. The mean is $\bar a = 2$, the centred vector is $(-1, 0, 1)$, and

$$
\sum_i (a_i - \bar a)^2 = 2, \qquad \sum_i a_i^2 = 14 .
$$

Only $2/14 = 1/7$ of the sum of squares survives, already less than one half. The loss is
$12 = 3 \cdot 2^2 = n \bar a^2$: that is no accident, see [Theorem A](#site:thm-identity).

## What was known at the start

Centring never *increases* the sum of squares ([Theorem B](#site:thm-upper)). So a
fraction larger than $1$ is impossible, and every fraction $c \le 1$ was a priori possible.
The question was whether some $c > 0$ works for every vector.

## Where to look

The loss is $n \bar a^2$, which is large when the mean is large compared with the spread
of the entries. It is largest, relative to $\sum_i a_i^2$, for a constant vector
$a = (t, \dots, t)$: then the centred vector is zero and everything is lost. That is where
the conjecture breaks ([Results](results.md)).
