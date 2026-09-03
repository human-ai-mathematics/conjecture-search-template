# solutions/ — the proof output plane

Where the `researcher` writes **proofs** of the open targets: self-contained,
standalone-compilable, human-checkable `.tex` files — **separate from the manuscript**
(`../modules/`). This is the analytic-proof channel paired with the refinement and
stress-testing work in `research/`.

A solution file is an artifact a newly `proved` ledger node points to (via a `proofs:` record).
The ledger records the *claim and its state*; this directory holds the *proof an
independent reviewer can check*. Every internally proved node must carry a certified dossier;
narrative provenance and numerical artifacts are not alternatives. Literature-provenance nodes
instead carry their source classification and references.

Definitions use the shared non-proof status `defined`; a ledger-worthy observation uses its
precise mathematical kind, while expository remarks remain prose. Literature results are
classified according to their actual role. Reclassification is not proof certification.

## Why separate from the manuscript

- **Human review boundary.** A reviewer reads one self-contained file and its one-file PDF, not
  a diff against the whole book.
- **Clear provenance.** Agent-authored, dated, revertible; lifting a checked solution into the
  manuscript remains an explicit project-owner decision.
- **Liftable.** Each file is a `subfiles` document, so once accepted it drops into `main.tex`
  with a single `\subfile{solutions/<id>}` line — no rewrite.

## Certification modes

A proof is only as trustworthy as its check. Every solution declares its level in the header:

| `checked_by` | meaning | ledger effect |
|---|---|---|
| `none`  | drafted, unreviewed dossier header only | **no ledger value** — not a proof yet |
| `agent` | a distinct agent audited the complete natural-language proof and left a persisted report | yes (agent-certified) |
| `human` | a human read and accepts the natural-language argument | yes (human-certified) |

There is no machine mode. `mode: lean` shipped as a placeholder that checked only whether a
file with a `.lean` suffix sat beside the dossier — it never ran the kernel, an empty file
satisfied it, and it could nonetheless support `status: proved`. A mode that certifies
nothing must not sit at the top of a certification ladder, so it is retired and rejected by
name. Restore it when `check.py` invokes Lean with pinned tooling.

Agent certification is deliberately explicit rather than being recorded as human review. It
requires a repo-local `review:` report whose front matter names distinct author(s) and reviewer.
The report uses the structured contract in
[`../research/reviews/README.md`](../research/reviews/README.md): its immutable historical scope
must contain every current node and dossier pointing to it. The report body states the
mathematical findings, corrections, and exclusions.

Human certification requires `proofs[].accepted_by`. A proved implication remains
`status: proved` even when an antecedent is open: antecedents go in `assumes`, conclusions in
`implies`, and only proof dependencies in `depends_on`.

## The audit header

Two of its fields are parsed and checked: `ledger-node`, which must name the node whose
`proofs[]` record points here, and `checked_by`, which must be `none`, `agent` or `human`.
A value ends at the first run of two or more spaces, so the gloss to its right is ignored.
The rest of the header — `refines`, `bounded_by`, author, date — is for a human reader.

The header does **not** repeat the reviewer's identity or the review path. The ledger's
`proofs[].review` owns the path and the review's own front matter owns the identities; a
third copy would have no owner to keep it true, which is how the previous header drifted.

## Refutation is the same channel

A refutation ends where a proof ends: in a certified dossier under `solutions/`. What makes
one a refutation is a ledger edge, not anything about the file.

1. The witness or divergent family is a **candidate** in a checkpoint — never a result
   (`CLAUDE.md` constraint 2), whatever its arithmetic says.
2. The statement it establishes becomes a **refuter node** with a manuscript statement, and
   the checkpoint recording that promotion retires the candidate in the same act.
3. The refuter gets an ordinary dossier here, and an ordinary independent review.
4. Only then does the target become `status: refuted`, naming the now-proved refuter in
   `refuted_by`.

The refuter does not appear in the target's `depends_on`: that field records facts a proof
used, and a refuted statement has no proof. A single witness discharges a universal claim;
a dimension-free or uniform constant generally needs a certified family with the relevant
divergence (constraint 11). The worked instance is
[`../example/solutions/prop-example-refuter.tex`](../example/solutions/prop-example-refuter.tex).

Numerics never appear on this ladder: they may guide intuition or suggest a counterexample, but
they do not validate a claim, justify a proof step, or certify a dossier. Every proof must stand
independently of numerical outcomes, as required by [`../CLAUDE.md`](../CLAUDE.md).

## Writing a solution

1. Copy `TEMPLATE.tex` to `solutions/<ledger-id>.tex` (replace `:` with `-`). Closely coupled
   nodes may share one target-level dossier if its header and theorem labels enumerate every
   covered ledger id explicitly.
2. Fill the audit header (`ledger-node`, `refines`, `bounded_by`, `checked_by: none`,
   author, and date).
3. State the **refined** theorem and prove it. Use `\ref`/
   `\cite` freely — they resolve when lifted into `main.tex` and show `??` standalone (expected).
4. Compile standalone:
   ```bash
   cd solutions
   latexmk -pdf -outdir=../build <id>.tex
   ```
5. Propose a ledger `proofs` record naming the artifact and `mode: agent|human`. For an agent
   audit add `review`; for human acceptance add `accepted_by`. Only the orchestrator applies it.

## Definition of done (a proof contribution)

1. `solutions/<id>.tex` exists, compiles standalone, audit header complete.
2. The theorem matches the manuscript statement(s) it `refines`, and
   respects every `bounded_by` obstruction.
3. The ledger node has a complete `proofs:` record; `python3 scripts/check.py`
   returns 0 errors.
4. The proof record uses `mode: agent` (independent named agent plus persisted report) or
   `mode: human` (named acceptance). There is no third mode.
