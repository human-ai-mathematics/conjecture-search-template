# solutions/ — the proof output plane

Where agents write **proofs** of the open targets: self-contained, standalone-compilable,
human-checkable `.tex` files — **separate from the manuscript** (`../modules/`). This is the
analytic-proof channel paired with the refinement and stress-testing work in `research/`.

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

| dossier header | meaning | ledger effect |
|---|---|---|
| `none`  | drafted, unreviewed dossier header only | **no ledger value** — not a proof yet |
| `agent` | a distinct agent audited the complete natural-language proof and left a persisted report | yes (agent-certified) |
| `human` | a human read and accepts the natural-language argument | yes (human-certified) |
| `lean`  | a compiling Lean proof sits beside it (`<id>.lean`) | yes (machine-certified) |

Agent certification is deliberately explicit rather than being recorded as human review. It
requires a repo-local `review:` report whose front matter names distinct author(s) and reviewer.
The report uses the structured contract in
[`../research/reviews/README.md`](../research/reviews/README.md): its immutable historical scope
must contain every current node and dossier pointing to it. The report body states the
mathematical findings, corrections, and exclusions.

Human certification requires `proofs[].accepted_by`. Lean is a future integration; the current
placeholder requires an adjacent `<solution-stem>.lean` file. A proved implication remains
`status: proved` even when an antecedent is open: antecedents go in `assumes`, conclusions in
`implies`, and only proof dependencies in `depends_on`.

Numerics never appear on this ladder: they may guide intuition or suggest a counterexample, but
they do not validate a claim, justify a proof step, or certify a dossier. Every proof must stand
independently of numerical outcomes, as required by [`../CLAUDE.md`](../CLAUDE.md).

## Writing a solution

1. Copy `TEMPLATE.tex` to `solutions/<ledger-id>.tex` (replace `:` with `-`). Closely coupled
   nodes may share one target-level dossier if its header and theorem labels enumerate every
   covered ledger id explicitly.
2. Fill the audit header (ledger node, `refines`, `bounded_by`, `checked_by`, separate
   author/reviewer identities, review path, and date).
3. State the **refined** theorem and prove it. Use `\ref`/
   `\cite` freely — they resolve when lifted into `main.tex` and show `??` standalone (expected).
4. Compile standalone:
   ```bash
   cd solutions
   latexmk -pdf -outdir=../build <id>.tex
   ```
5. Propose a ledger `proofs` record naming the artifact and `mode: agent|human|lean`. For an agent
   audit add `review`; for human acceptance add `accepted_by`. Only the orchestrator applies it.

## Definition of done (a proof contribution)

1. `solutions/<id>.tex` exists, compiles standalone, audit header complete.
2. The theorem matches the manuscript statement(s) it `refines`, and
   respects every `bounded_by` obstruction.
3. The ledger node has a complete `proofs:` record; `python3 scripts/check_ledger.py`
   returns 0 errors.
4. The proof record uses `mode: agent` (independent named agent plus persisted report),
   `mode: human` (named acceptance), or the deferred `mode: lean` integration.
