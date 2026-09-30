---
target: conj:example
---

# Problem brief

## The target

`conj:example`, stated in [`../../modules/02-refutation.md`](../../modules/02-refutation.md).
It is not the identity `prop:example`, which is proved; it asserts a **uniform constant**
$\tfrac12$, and the constant is where it is vulnerable.

It is bounded by the proved fence `prop:upper-constant`, which rules out every constant
above $1$ and leaves $\tfrac12$ open — so the fence alone decides nothing. What it gives is
a direction: the gap between the two sums is exactly $n\bar a^2$, so the target fails
exactly where $n\bar a^2 > \tfrac12 \sum_i a_i^2$. By `prop:example` that gap is largest,
equal to $\sum_i a_i^2$, on constant vectors: a refutation attempt should start there.

## The exact negation

$$\exists\, n \ge 2,\ \exists\, a \in \mathbb{R}^n : \quad
\sum_{i=1}^n (a_i - \bar a)^2 < \tfrac{1}{2}\sum_{i=1}^n a_i^2 .$$

The target is universal and its constant is fixed, so **one instance suffices**; no
divergent family is needed.

## What counts as complete

**A complete proof** establishes the inequality for every $n \ge 2$ and every real vector,
with $\tfrac12$ intact. The centred case $\bar a = 0$, a constant depending on $n$, and any
finite numerical battery do not count.

**A complete refutation** exhibits a specific vector, verified by exact arithmetic, and
reaches `status: refuted` through a proved, independently reviewed refuter node.

## Edge cases and audit tests

1. **Constant vectors** $a = (t,\dots,t)$, $t \ne 0$: left side $0$, right side
   $\tfrac{nt^2}{2}$. This is the whole failure.
2. **The zero vector** gives $0 \ge 0$, which holds: not a counterexample.
3. **$n = 2$**, the case a proof attempt most likely generalized from.
4. **Scaling.** Both sides are homogeneous of degree 2; no proof may draw strength from a
   normalization.
5. **Floating point.** A near-equality from a run is inconclusive, which is why
   `cand:example-identity-stability` exists.

## Traps and circular reductions

- **Centring first** makes the statement trivially true and throws away every vector that
  breaks it.
- **Re-deriving the identity** $\sum (a_i - \bar a)^2 = \sum a_i^2 - n\bar a^2$ lands on the
  settled `prop:example` and says nothing about the constant.

## Neighbourhood

- `conj:weighted-example` — the weighted form of the identity `prop:example`, open. It
  would locate the failure for weighted vectors the way `prop:example` does here; no route
  in this search needs it.

A refuted `conj:example` stays closed. Constant vectors kill every positive constant, so
any corrected version changes more than the constant; it would be a new statement with a
new id, proposed in a checkpoint that says which failure it answers.

## Budget policy

An unresolved outcome with certified advances is permitted. Here the budget was one run —
what a target refuted by a two-entry vector deserves.
