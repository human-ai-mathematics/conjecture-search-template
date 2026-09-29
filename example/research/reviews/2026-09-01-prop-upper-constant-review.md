---
verdict: pass
authors:
  - researcher, claude-opus-5-5, 2026-09-01
reviewer: reviewer, claude-opus-5-5, 2026-09-01
fingerprints:
  solutions/prop-upper-constant.md: f7920a658a1f4d81895651679f365bfdaca8ddc5bb6866b2a2e0f74061ffbf16
  prop:upper-constant: bf6de1113cb252456f59daaca4010bc0569f5496cda9b8aa92eddb84d66dc04b
  prop:example: ea79eae68f7d2f1c5075b59892ece18383fc7cfbc4e38f1004beb0134c785e9a
---

Worked example of a review certifying a fence. A fence is certified like any other node;
nothing here depends on the fact that `conj:example` cites it in `bounded_by`.

## Findings

The dossier theorem agrees with the manuscript statement at `prop:upper-constant`: the
inequality, its direction, the hypothesis $n \ge 1$ and the equality case $\bar a = 0$. It
states the gap $n\bar a^2$ explicitly, which is the same statement in sharper form.

The proof uses `prop:example`, which is proved and listed in `depends_on`. From the
identity, the gap is $n\bar a^2$; nonnegativity and the equality case follow because
$n \ge 1$ and a real square vanishes only at $0$. No hypothesis is used unstated.

## Corrections

None.

## Exclusions

This report certifies the fence, not its use. Whether `conj:example`'s constant
$\tfrac12$ respects it is a question about `conj:example`, and nothing here bears on
`conj:weighted-upper`, the weighted analogue, which remains open.
