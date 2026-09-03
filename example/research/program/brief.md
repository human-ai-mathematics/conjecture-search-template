---
type: brief
target: conj:example
---

# Problem brief

<!-- The worked example's brief, filled in. It is what a completed one looks like; the
     unfilled scaffold to copy is templates/brief.md, or `python3 scripts/new.py brief
     --target <node-id>`. The mathematics is deliberately elementary — the target is
     refuted by a two-entry vector — so that nothing here competes for attention with the
     shape of the document. A real brief has this shape and harder content. -->

The harness remembers, validates and certifies. It does not supply mathematical
pressure. That is this file's job: it is the one document that knows how the target
usually fails, what would count as finishing, and which disguises a dead route wears.

It is a mutable, single-writer document owned by the orchestrator (`brief` concurrency
key), and it owns none of the mathematics. Three things, three homes:

| what | where |
|---|---|
| the canonical quantified target | `modules/`, under the target node's `\label` |
| its identity, status, provenance and relations | [`ledger.yaml`](ledger.yaml) |
| its negation, completion criteria, edge cases, traps and search policy | this file |

## The target

The blockquote below is a **copy, not a source**: if it and the manuscript disagree, the
manuscript is right and the copy is a defect, which is what the `reviewer`'s `sync` lens
checks (`CLAUDE.md` constraint 8). Never sharpen the statement here — sharpen it in
`modules/` and re-copy.

> **Target** `conj:example`, stated at `\label{conj:example}` in
> [`../../modules/00-overview.tex`](../../modules/00-overview.tex):
>
> For all real $a_1,\dots,a_n$ with $n \ge 2$,
> $\sum_{i=1}^n (a_i - \bar a)^2 \ge \tfrac{1}{2}\sum_{i=1}^n a_i^2$.

Here $\bar a = n^{-1}\sum_{i=1}^n a_i$, the ordinary mean. No definition node carries that
convention in this example, because nothing else in the fixture depends on it; in a real
program a fixed normalization earns a `kind: definition` node and every claim resting on it
names that node in `depends_on`.

Note what the target is *not*. It is not about the identity at `prop:example`, which is
proved and settled. It asserts a **uniform constant** $\tfrac{1}{2}$, valid for every $n$
and every vector, and the constant is where it is vulnerable.

## The exact negation

$$\exists\, n \ge 2,\ \exists\, a_1,\dots,a_n \in \mathbb{R} : \quad
\sum_{i=1}^n (a_i - \bar a)^2 < \tfrac{1}{2}\sum_{i=1}^n a_i^2 .$$

The quantifier order decides the shape of the refutation, and here it is the easy shape:
the target is universally quantified over $n$ and over vectors, so **one instance
suffices**. There is no dimension-free constant to break along a family — the constant
$\tfrac{1}{2}$ is already fixed in the statement, so a single vector violating it settles
the matter (`CLAUDE.md` constraint 11).

Contrast the harder shape, which this fixture deliberately does not need: had the target
read "there is a constant $c > 0$, independent of $n$, such that …", refuting it would
require a certified family along which the ratio tends to zero, not one vector.

## What counts as complete

Both lists below are explicit, and writing the second one first is what made the search
short: it says a witness is enough, so the first thing worth trying is looking for one.

**A complete proof** must establish the inequality for every $n \ge 2$ and every real
vector, with the constant $\tfrac{1}{2}$ intact. These do **not** count, and must be
recorded as partial rather than presented as the answer:

- the centred case $\bar a = 0$, where the inequality reads $\sum a_i^2 \ge \tfrac{1}{2}\sum a_i^2$
  and is trivially true;
- any version with $\tfrac{1}{2}$ weakened to a constant depending on $n$;
- any version restricted to vectors with a fixed number of distinct entries;
- a numerical verification over any finite battery, which `obs:example` fences outright.

**A complete refutation** must exhibit a specific $n$ and a specific vector, verify both
sides by exact arithmetic, and reach `status: refuted` through the ordinary channel: the
witness is a candidate, the statement it establishes becomes a proved refuter node with its
own manuscript statement and dossier, that dossier is independently reviewed, and only then
does `conj:example` gain `refuted_by`. A run artifact is never a step in that chain
(constraints 2 and 11).

## Edge cases and audit tests

The five things that actually go wrong here, for a reviewer to run against any claimed
proof or refutation:

1. **Constant vectors.** $a = (t,\dots,t)$ gives $\bar a = t$ and a left side of $0$. For
   $t \ne 0$ the right side is $\tfrac{n t^2}{2} > 0$. This is the whole failure.
2. **The zero vector.** $a = (0,\dots,0)$ gives $0 \ge 0$, which *holds*. It is not a
   counterexample, and a refutation that offers it has not read the inequality.
3. **$n = 2$ exactly.** The smallest admissible case, and the one a proof attempt is most
   likely to have checked by hand and generalized from.
4. **Scaling.** Both sides are homogeneous of degree $2$, so a witness may be normalized
   freely — and equally, no proof may draw strength from a normalization.
5. **Floating point.** A near-equality reported by a numerical run is not a violation.
   `cand:example-identity-stability` exists precisely because nothing here yet bounds the
   arithmetic error, so a residual near machine epsilon must be treated as inconclusive.

Add to this list every time a review catches something.

## Traps and circular reductions

- **Centring first.** Replacing $a$ by $a - \bar a$ and then applying the inequality assumes
  what is at issue: after centring the statement is trivially true, and the reduction has
  thrown away the only vectors that break it.
- **Reading it as Cauchy–Schwarz.** $\sum (a_i - \bar a)^2 = \sum a_i^2 - n\bar a^2$ is
  `prop:example` and is proved; it says nothing about the constant, and a route that ends
  by re-deriving it has arrived back at a settled node.
- **Widening the battery.** Enumerating a larger box is the same route under a new name.
  See `ap:example-exhaustive-search`, which is marked `duplicate` for exactly this.

## Initial families and their reopening criteria

One family was seeded: `fam:example-numerical` — look at the target numerically before
committing to an analytic route, on the reasoning that a false uniform constant usually
shows itself in seconds and a true one does not.

It is now `saturated`: the search ended, and the family is closed with a reopening
condition rather than deleted. The live version of that state is
[`portfolio.yaml`](portfolio.yaml); this section is the reasoning behind the seeding, not a
second copy of it.

## Budget policy

The honest outcome — unresolved, with certified advances and exact remaining gaps — is
permitted and reportable. Terminate on saturation of the portfolio, not on a clock: elapsed
time says nothing about approach exhaustion, duplicated work, or novelty. Saturation costs
a synthesis checkpoint and a reopening condition, and is never inferred from attempt counts.

For this target the budget was one numerical run. That is not a policy anyone should copy —
it is what a target refuted by a two-entry vector deserves.
