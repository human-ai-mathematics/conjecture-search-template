---
verdict: editorial
amends:
  - research/reviews/YYYY-MM-DD-slug.md
authors:
  - orchestrator, <model>, YYYY-MM-DD
reviewer: reviewer, <model>, YYYY-MM-DD
changes:
  thm:slug: {from: <sha256 the report recorded>, to: <sha256 now>}
---

# Editorial note on `<report>`

<!-- Copy to research/reviews/YYYY-MM-DD-<slug>.md. Written only by a fresh reviewer who
     found the mathematics unchanged; anything else takes a re-review.
     Format: SPECIFICATION.md, Formats → Review, An editorial note. -->

## `thm:slug`

```diff
the diff printed by uv run scripts/check.py --diff
```

Why the mathematics is unchanged: the statement, formulas, hypotheses, quantifiers,
constants and steps read the same; only <what changed> did.
