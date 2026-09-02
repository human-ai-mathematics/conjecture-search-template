# Independent reviews

This directory holds persisted review provenance. Reports have one of two explicit types:

| `type` | purpose | may certify `proofs[].mode: agent`? |
|---|---|---|
| `proof-review` | Independent review of one or more standalone proof dossiers | yes |
| `audit` | Historical, diagnostic, editorial, literature, or control-plane review | no |

The distinction is structural. A sentence such as “pass” inside an `audit` has no proof value.

## Proof-review front matter

Every certifying report starts with YAML front matter:

```yaml
---
type: proof-review
date: "YYYY-MM-DD"
verdict: pass
authors:
  - /root/proof_author
reviewer: /root/independent_reviewer
nodes:
  - thm:example
solutions:
  - solutions/thm-example.tex
---
```

`date` is quoted and matches the filename prefix. `verdict` is exactly `pass`; partial, held, or
failed work is an `audit` until a new follow-up proof review passes. `authors`, `nodes`, and
`solutions` are non-empty lists without duplicates. One report has one reviewer, but it may cover
multiple authors, nodes, and dossiers.

The front matter declares the immutable historical scope, not search terms. It is canonical for
the proof authors and reviewer. Every currently agent-certified ledger node pointing to the report
must occur in `nodes`, and its active dossier must occur in `solutions`. The report may retain
extra formerly active nodes/dossiers, and an old passing report may remain unreferenced after a
later downgrade. This preserves history without forcing stale certification into current state.

The checker rejects active certifications outside the declared scope, reports outside this
directory, self-review, and attempts to use an `audit` as proof provenance.

A repaired proof may add the optional repo-relative pointer:

```yaml
follows_up: research/reviews/YYYY-MM-DD-earlier-audit.md
```

Never rewrite an earlier verdict after a repair. Preserve it and write a new report.
If a later audit invalidates an earlier passing proof, remove the node's active certification or
downgrade its status as appropriate and retain both reports; the old proof review remains a
historical event, not current authority.

## Audit front matter

A non-certifying report uses only:

```yaml
---
type: audit
date: "YYYY-MM-DD"
---
```

Its outcome, participants, and scope remain ordinary prose because they have no mechanical
proof-certification effect.

## Report body

The mathematical body is intentionally free-form. Prefer the smallest useful structure:

1. **Findings** — the independent mathematical checks and reasoning.
2. **Corrections** — changes required and rechecked, or “None.”
3. **Exclusions** — nearby claims not certified.

Do not repeat the machine-readable node list in a verdict sentence merely for validation. Review
reports are proof provenance, never numerical evidence; computation may expose a defect but cannot
certify an analytic step.

Validate the archive and every active certification pointer with:

```bash
python3 scripts/check_ledger.py
```
