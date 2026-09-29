---
verdict: pass
authors:
  - researcher, claude-opus-5-5, 2026-09-03
reviewer: reviewer, claude-opus-5-5, 2026-09-03
fingerprints:
  solutions/prop-example-refuter.md: 3526618e00073f21a60480962fc8a950567fccba12fae3719a753b619ed43771
  prop:example-refuter: 1727ada4df69f811df0368d801df02c87a64533cb3429555cf7c021185a56495
  prop:example: ea79eae68f7d2f1c5075b59892ece18383fc7cfbc4e38f1004beb0134c785e9a
  conj:example: 6540a530455e2293a95ae5526312720c5cb8be9a13c7ac0bb519e67f3839dafd
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
and no divergent family is needed. The dossier states which
form it supplies and why the other is not required.

The appeal to `prop:example` is recorded in `depends_on` and is genuine but not load
bearing: the direct computation is complete on its own, which is what lets the dossier
stand alone.

The fence line is correct. `conj:example` is bounded by the proved `prop:upper-constant`,
and the witness respects it ($0 \le 2$). A refuter that violated a proved fence of its
target would signal an error in one of the two, not a refutation.

## Corrections

None.

## Exclusions

This report certifies `prop:example-refuter` only. Setting `conj:example` to
`status: refuted` with `refuted_by: [prop:example-refuter]` is a separate ledger delta and
the orchestrator's act; this review is the evidence for it, not the act itself.
