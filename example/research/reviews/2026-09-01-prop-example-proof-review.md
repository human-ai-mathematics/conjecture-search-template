---
verdict: pass
authors:
  - researcher, claude-opus-5-5, 2026-09-01
reviewer: reviewer, claude-opus-5-5, 2026-09-01
fingerprints:
  solutions/prop-example.md: 06fba361ea7b5930216abb73c031ee4759cb8ce75ed3793cdd991a28ba2c5d78
  prop:example: ea79eae68f7d2f1c5075b59892ece18383fc7cfbc4e38f1004beb0134c785e9a
---

Worked example of a certifying review, kept so the template ships one of each
artifact genre. Its mirror is the refutation review beside it,
`2026-09-03-prop-example-refuter-proof-review.md`: a refuter is certified through this
same channel, and only then does its target become `refuted`.

## Findings

The dossier proves the stated identity. The expansion of $\sum_i (a_i-\bar a)^2$
is termwise and complete; the substitution $\sum_i a_i = n\bar a$ is exactly the
definition of $\bar a$ and is used once, legitimately. Arithmetic on the
resulting coefficients ($-2n\bar a^2 + n\bar a^2 = -n\bar a^2$) is correct. The
hypothesis $n \ge 1$ is needed only for $\bar a$ to be defined, and the dossier
says so rather than leaving it implicit.

The theorem in the dossier matches the manuscript statement at `prop:example`
character for character, so there is no gap between what is claimed in the ledger
and what is proved here.

## Corrections

None.

## Exclusions

Nothing beyond the single identity is certified. In particular this report says
nothing about `conj:weighted-example`, which remains open, and reviewing a proof is not a
check of the surrounding exposition.
