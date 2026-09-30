% Each open question is a conjecture of the manuscript, presented for a reader who might
% take it up: why it matters, what is known, where to start. Its label is its stable name.

(sec:open)=
# A question left open here

The question below is not a research problem: its answer is classical, and the hint at the
end of this section settles it. It is left unsettled in this document only to show how a
question is presented to a reader who might take it up. In a real project, this section
holds the questions whose answer is not known in the literature, and says so.

## Does the identity survive weighting?

Replace the plain mean by a weighted one: fix weights $w_1,\dots,w_n > 0$ with
$\sum_i w_i = 1$, and let $\bar a_w = \sum_i w_i a_i$. Is the weighted centred sum still
the weighted sum of squares minus the squared mean?

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

**Why it matters.** With equal weights $w_i = 1/n$ this is [](#prop:example), divided by
$n$. The weighted form is the one probability uses: for a random variable taking the value
$a_i$ with probability $w_i$, it says that the variance is the second moment minus the
squared mean. In that form it is classical, as said above.

**Evidence.** One case checked by hand, which is evidence and not a proof. For $n = 2$,
$w = (\tfrac13, \tfrac23)$ and $a = (0, 3)$: $\bar a_w = 2$, the left side is
$\tfrac13 \cdot 4 + \tfrac23 \cdot 1 = 2$, and the right side is $\tfrac23 \cdot 9 - 4 = 2$.

**Where to start.** Expand the square as in the proof of [](#prop:example). The step that
used $\sum_i a_i = n\bar a$ now uses $\sum_i w_i a_i = \bar a_w$, and the constant terms
use $\sum_i w_i = 1$. The inequality [](#conj:weighted-upper) then follows at once, as
[](#prop:upper-constant) follows from [](#prop:example).
