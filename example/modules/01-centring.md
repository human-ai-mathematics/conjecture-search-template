(sec:centring)=
# What centring removes

The sum of squares drops by exactly $n$ times the squared mean.

:::{prf:proposition}
:label: prop:example
Let $a_1,\dots,a_n \in \R$ and let $\bar a = n^{-1}\sum_{i=1}^n a_i$. Then
$\sum_{i=1}^n (a_i - \bar a)^2 = \sum_{i=1}^n a_i^2 - n \bar a^2$.
:::

**Idea of the proof.** Expand each square. The cross terms add up to
$-2\bar a \sum_i a_i = -2n\bar a^2$, because $\sum_i a_i = n\bar a$ is the definition of
the mean. The constant terms add up to $+n\bar a^2$, and the two combine into
$-n\bar a^2$:

$$
\sum_i (a_i - \bar a)^2
= \sum_i a_i^2 - 2\bar a \sum_i a_i + n\bar a^2
= \sum_i a_i^2 - 2n\bar a^2 + n\bar a^2 .
$$

Since the loss $n\bar a^2$ is nonnegative, centring can only lower the sum of squares.

:::{prf:proposition}
:label: prop:upper-constant
Let $a_1,\dots,a_n \in \R$ with $n \ge 1$. Then
$\sum_{i=1}^n (a_i - \bar a)^2 \le \sum_{i=1}^n a_i^2$, with equality if and only if
$\bar a = 0$.
:::

**Idea of the proof.** By [](#prop:example) the difference between the two sides is
exactly $n\bar a^2$, which is nonnegative and vanishes only when the mean does.

This settles one side of the question. On its own it does not decide the other: a lower
bound $\sum_i (a_i - \bar a)^2 \ge c \sum_i a_i^2$ holds trivially for $c \le 0$, and
fails for $c > 1$ on any vector with a nonzero mean, but the bound says nothing of a
constant $0 < c \le 1$, such as the one half of [](#conj:example).
[](#sec:refutation) shows that no such constant exists.
