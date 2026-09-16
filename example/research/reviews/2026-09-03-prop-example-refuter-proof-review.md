---
type: proof-review
date: "2026-09-03"
verdict: pass
authors:
  - /root/template_author
reviewer: /root/template_reviewer
nodes:
  - prop:example-refuter
solutions:
  - solutions/prop-example-refuter.md
---

# Review: `prop:example-refuter`

The worked example's refutation review. It exists so the template ships one instance of a
certified refuter, the mirror of the proof review beside it.

## Findings

The dossier states an admissible instance and computes both sides exactly. $a = (1,1)$ has
$n = 2 \ge 2$ and is real, so it lies inside the conjecture's quantifier. The mean is
$1$, the centred sum of squares is $0$, and half the sum of squares is $1$; both are exact
rational computations and neither leans on a numerical run.

The negation is the right one. `conj:example` is universally quantified over finite real
sequences with no uniformity in any further parameter, so one counterexample discharges it
and no divergent family is needed (`CLAUDE.md` constraint 10). The dossier states which
form it supplies and why the other is not required.

The appeal to `prop:example` is recorded in `depends_on` and is genuine but not load
bearing: the direct computation is complete on its own, which is what lets the dossier
stand alone.

## Corrections

None.

## Exclusions

This report certifies `prop:example-refuter` only. Setting `conj:example` to
`status: refuted` with `refuted_by: [prop:example-refuter]` is a separate ledger delta and
the orchestrator's act; this review is the evidence for it, not the act itself.
