# CLAUDE.md — repository contract

`AGENTS.md` is a symlink to this file, so Claude Code and Codex receive the same instructions.
This is the root contract for work entering the repository. Scoped contracts may add narrower
requirements: [`research/ledger-schema.md`](research/ledger-schema.md) for the ledger,
[`solutions/README.md`](solutions/README.md) for proofs,
[`experiments/README.md`](experiments/README.md) for numerical work, and
[`.claude/agents/`](.claude/agents/README.md) for role permissions. They never override this file.
Use [`research/README.md`](research/README.md) to locate each plane's source of truth; other
READMEs are navigation maps.

## Universal workflow

### Mathematical contribution

1. Sharpen or confirm a target, or supply a standalone proof dossier.
2. When a claim changes, update its manuscript statement and ledger state, provenance, and edges
   together.
3. After a ledger edit, leave `python3 scripts/check_ledger.py` at 0 errors.
4. Record the attempt, **including dead ends**, in a new
   `research/explorations/YYYY-MM-DD-slug.md`; promote genuinely reusable findings to
   `research/knowledge/`.

### Proof contribution

Follow [`solutions/README.md`](solutions/README.md). An author never certifies their own proof;
`checked_by: agent` requires a persisted review naming distinct author(s) and reviewer.

### Harness or repository contribution

Record the rationale and validation in a new `research/decisions/YYYY-MM-DD-slug.md`. Do not
invent a mathematical attempt; harness work does not by itself change mathematical status.

## Hard constraints

These are the universal constraints. They are numbered, and append-only records cite the numbers,
so **do not renumber them** — a constraint that stops applying becomes `**Reserved.**` and keeps
its slot. Constraints specific to this repository's mathematics go in the next section, numbered
`P1, P2, …`, so that a fork can drop them without disturbing this list.

1. **A ledger is a single-file write-contention point.** This repository has exactly one program
   ledger, `research/program/ledger.yaml`. Funnel every ledger edit through one orchestrator.
   Role definitions may narrow write access; no spawned role writes the ledger.
2. **No private Monte Carlo.** Every numerical research observation flows through the `numerics`
   harness into a provenance-stamped artifact. Numerical output certifies no claim, proof step,
   or dossier. Exact arithmetic or an analytic witness it emits remains a candidate until checked
   independently in the proof or refutation workflow.
3. **The research battery is shared.** Use `research/knowledge/instances.md`. Anyone may propose
   an adversarial instance; only the `synthesizer` curates the registry. Passing a finite battery
   changes no claim or proof status.
4. **`check_ledger.py` is necessary, not sufficient.** A green check establishes structure only.
   Semantic agreement among manuscript, ledger, and dossier, and the correctness of a proof,
   require independent review.
5. **Respect `bounded_by`.** A statement violating a known obstruction is wrong by construction.
   Check its fences before proving it or spending a numerical run.
6. **A certified conditional implication stays `conditional`.** Make its assumption an explicit
   hypothesis. It becomes `proved` only after that assumption is discharged, for every
   certification mode, including Lean.
7. **`research/explorations/` and `research/decisions/` are append-only.** Add dated files; never
   rewrite or delete their history.

## Program constraints

Constraints that depend on this repository's mathematics. Use them for merge barriers — a
comparison exactly one agent may hold — and for anything a fork of this template would not
inherit. Same rule: numbered, cited, never renumbered.

<!-- Delete this comment and add constraints as the program grows. A merge
     barrier states the objects compared, what is and is not proved between
     them, and who holds the comparison. Name the same owner in
     .claude/agents/synthesizer.md. -->

*(none yet)*

## Global convention

Write Markdown mathematics in LaTeX `$...$`.

## Verify

```bash
./scripts/check.sh                # everything below, in order
python3 scripts/check_ledger.py   # 0 errors required after any ledger edit
python3 scripts/check_ledger.py status
python3 scripts/check_agents.py
```
