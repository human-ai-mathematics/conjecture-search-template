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
  - solutions/thm-example.md
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

## Audit currency is per subject

`python3 scripts/check.py checkpoints` prints the current audit heads — every `type: audit`
report nothing later supersedes. That list is only as honest as its curation, and two
unrelated audits are not competing versions of one document: an audit of the numerics
harness does not go stale because someone later audited the roles.

So: when you write an audit that replaces an earlier reading **of the same subject**, name
that earlier report in `supersedes:`. When your subject is new, name nothing. Neither
record is ever edited or deleted; supersession only ever changes which one to read first.

An audit that says "a further pass is still needed" and is never superseded will keep
showing up as current long after that pass happened, which is a curation failure rather
than a checker one — nothing can infer it.

## Audit front matter

A non-certifying report uses only:

```yaml
---
type: audit
date: "YYYY-MM-DD"
supersedes:
  - research/reviews/YYYY-MM-DD-earlier-audit.md
---
```

Its outcome, participants, and scope remain ordinary prose because they have no mechanical
proof-certification effect.

`supersedes` is optional and lists earlier audits this report replaces as the current
reading. Nothing is rewritten or deleted: an audit whose findings a later schema change
overtook stays exactly as it is, and the reader is simply pointed at the record that succeeded
it. It is the same relation checkpoints use (`research/explorations/README.md`), and it is
available only to audits — a proof review is a certification event, not a summary, and uses
`follows_up` instead.

Two audits dated the same day are not ordered by their filenames, so a same-day supersession
is accepted in either direction and the relation is verified acyclic instead. `date:` also
accepts a UTC timestamp `YYYY-MM-DDTHH:MM:SSZ`, whose date part must still match the filename
prefix; use one when two reports on one day really do need an order.

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
python3 scripts/check.py --lane proofs
python3 scripts/check.py checkpoints    # also lists superseded audits
```
