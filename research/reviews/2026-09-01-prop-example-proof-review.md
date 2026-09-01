---
type: proof-review
date: "2026-09-01"
verdict: pass
authors:
  - /root/template_author
reviewer: /root/template_reviewer
nodes:
  - prop:example
solutions:
  - solutions/prop-example.tex
---

Worked example of a certifying review, kept so the template ships one of each
artifact genre. Delete it together with `solutions/prop-example.tex` and the
`prop:example` node.

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
nothing about `q:example`, which remains open, and reviewing a proof is not a
check of the surrounding exposition.
