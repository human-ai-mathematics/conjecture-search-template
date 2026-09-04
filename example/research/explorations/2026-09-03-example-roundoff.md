---
type: exploration
date: "2026-09-03"
approach: ap:example-roundoff-bound
outcome: directional
nodes:
  - prop:example
---

# Roundoff route blocked on an analytic estimate

The numerical residual alone cannot provide the forward-error bound this route needs. The
route therefore stops on a precise candidate statement rather than treating a small observed
error as a proof.

## Handoff

```yaml
portfolio_delta:
  approach: ap:example-roundoff-bound
  state: blocked
  blocker: cand:example-identity-stability
  reopen_if: cand:example-identity-stability is proved, or another explicit error bound is supplied.
```
