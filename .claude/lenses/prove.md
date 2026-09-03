---
name: prove
role: researcher
---

# Lens `prove` — build the dossier

You were assigned this lens and no other. Read `.claude/agents/researcher.md` for the shared
contract; everything below is what `prove` adds.

## Method

1. Read the node, its manuscript statement, its `depends_on` closure, and every `bounded_by`
   and `heuristic_barriers` node in full. Hard fences must be respected; advisory barriers
   must be addressed or explicitly set aside.
2. Run `python3 scripts/new.py dossier <ledger-id>`, or copy `templates/solution.tex`
   yourself. Fill the header: `ledger-node` naming what this discharges, `refines`,
   `bounded_by`, author identity, date. The header carries no certification, no reviewer and
   no review path — the ledger's `proofs[]` record owns the mode and the path, and the
   report's front matter owns the identities. You are not the reviewer.
3. State the refined theorem, then prove it. `\ref`/`\cite` freely; `??` standalone is
   expected.
4. Compile: `cd solutions && latexmk -pdf -outdir=../build <id>.tex`.
5. Mark every step you could not close with an explicit `\begin{remark}` naming exactly what
   remains. A gap you flag is a contribution; a gap you paper over is the failure mode this
   repository exists to catch.

## Numerical evidence

No numerical output may appear in the dossier: not as a step, not as a justification, not as
a reason a step is plausible. Every line stands or falls analytically. A run that agrees with
the theorem is not weak evidence for it — inside a proof it is no evidence at all
(`CLAUDE.md` constraint 2).

Directional numerics remains useful *outside* the dossier, and the shared contract says how.

## Report additions

- Dossier path, and whether the standalone build succeeded — paste the failing lines if not.
- The fence-by-fence check against `bounded_by`.
- Every unclosed step, and every hypothesis actually used, including any used but not stated.
- **No applicable ledger delta.** A dossier no `proofs[]` record names is an uncertified
  draft, and that absence is the only thing that says so: state the future
  `proofs[].artifact` path as a deferred artifact only.
- `next_role: reviewer`. Put the theorem, the used hypotheses, the fence check and the build
  result in `next_prompt`, so a cold reviewer can be launched from repository artifacts alone.
