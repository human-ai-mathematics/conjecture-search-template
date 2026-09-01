# solutions/ — the proof output plane

Where agents write **proofs** of the open targets: self-contained, standalone-compilable,
human-checkable `.tex` files — **separate from the manuscript** (`../modules/`). This is the
analytic-proof channel paired with the refinement and stress-testing work in `research/`.

A solution file is the artifact a newly `proved` ledger node points to (via its `solution:`
field). The ledger records the *claim and its state*; this directory holds the *proof an
independent reviewer or Lean can check*. Every newly `proved` node must carry a certified dossier;
narrative provenance and numerical artifacts are not alternatives to a checked proof. There is no historical
or inline-proof exception: every `status: proved` node must point to a certified dossier.

Definitions use the shared non-proof status `defined`; a ledger-worthy observation uses its
precise mathematical kind, while expository remarks remain prose. Externally imported results are
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
| `lean`  | a compiling Lean proof sits beside it (`<id>.lean`) | yes (machine-certified) |

Agent certification is deliberately explicit rather than being recorded as human review. It
requires a repo-local `review:` report whose front matter names distinct author(s) and reviewer.
The report uses the structured contract in
[`../research/reviews/README.md`](../research/reviews/README.md): its immutable historical scope
must contain every current node and dossier pointing to it. The report body states the
mathematical findings, corrections, and exclusions.

Human certification requires a named ledger `accepted_by`. Lean certification requires the
adjacent `<solution-stem>.lean` file. A dossier may certify a conditional implication while the
node remains `status: conditional`; only discharge of its assumptions permits `status: proved`.

Numerics never appear on this ladder: they may guide intuition or suggest a counterexample, but
they do not validate a claim, justify a proof step, or certify a dossier. Every proof must stand
independently of numerical outcomes, as required by [`../CLAUDE.md`](../CLAUDE.md).

## Writing a solution

1. Copy `TEMPLATE.tex` to `solutions/<ledger-id>.tex` (replace `:` with `-`). Closely coupled
   nodes may share one target-level dossier if its header and theorem labels enumerate every
   covered ledger id explicitly.
2. Fill the audit header (ledger node, `refines` label, `bounded_by`, `checked_by`, separate
   author/reviewer identities, review path, and date).
3. State the **refined** theorem and prove it. Use `\ref`/
   `\cite` freely — they resolve when lifted into `main.tex` and show `??` standalone (expected).
4. Compile standalone:
   ```bash
   cd solutions
   latexmk -pdf -outdir=../build <id>.tex
   ```
5. Wire the ledger node in `research/program/ledger.yaml`: add `solution: solutions/<id>.tex`
   and `checked_by: agent|human|lean`. For an agent audit, also add `review`; for human
   acceptance add `accepted_by`. The node may flip to `status: proved` only once these artifacts
   exist and no unresolved premise remains. A reviewed conditional implication keeps
   `status: conditional` — enforced by `scripts/check_ledger.py`.

## Definition of done (a proof contribution)

1. `solutions/<id>.tex` exists, compiles standalone, audit header complete.
2. The theorem matches the refined statement in the manuscript `\label` it `refines`, and
   respects every `bounded_by` obstruction.
3. The ledger node has `solution:` + `checked_by` set; `python3 scripts/check_ledger.py`
   returns 0 errors.
4. `checked_by: agent` (independent named agent plus persisted report), `checked_by: human`
   (a named human accepted it), or `checked_by: lean` (with `<id>.lean`).
