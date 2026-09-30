(sec:refutation)=
# No fixed fraction survives

The conjecture asked for one half of the sum of squares to survive centring, as soon as
there are at least two entries.

:::{prf:conjecture}
:label: conj:example
For all real $a_1,\dots,a_n$ with $n \ge 2$,
$\sum_{i=1}^n (a_i - \bar a)^2 \ge \tfrac{1}{2}\sum_{i=1}^n a_i^2$.
:::

The identity of [](#prop:example) says where to look. The loss $n\bar a^2$ is large when
the mean is large compared with the spread of the entries, and it equals the whole of
$\sum_i a_i^2$ exactly when the vector is constant. The smallest such vector already
breaks the conjecture.

:::{prf:proposition}
:label: prop:example-refuter
The sequence $a = (1,1)$ satisfies $\sum_{i=1}^2 (a_i - \bar a)^2 = 0$ and
$\tfrac{1}{2}\sum_{i=1}^2 a_i^2 = 1$. Hence [](#conj:example) is false.
:::

**Idea of the proof.** The vector is constant, so it equals its mean and centring sends it
to zero. The same happens to every nonzero constant vector, so no fraction $c > 0$ can
replace one half: the counterexample sits exactly where the bound is weakest.

**What it teaches.** A lower bound on the centred sum must depend on the spread of the
vector, not only on its size. Any corrected conjecture has to exclude constant vectors,
for instance by assuming $\bar a = 0$ — and then it becomes trivial by [](#prop:example).
