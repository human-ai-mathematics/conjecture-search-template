# CLAUDE.md — repository contract

`AGENTS.md` is a symlink to this file, so Claude Code and Codex receive the same instructions. This
is the root contract for work entering the repository. Scoped contracts may add narrower
requirements: [`research/program/ledger-schema.md`](research/program/ledger-schema.md) for the
ledger, [`solutions/README.md`](solutions/README.md) for proofs,
[`experiments/README.md`](experiments/README.md) for numerical work, and
[`.claude/agents/`](.claude/agents/README.md) for role permissions. They never override this file.
Use [`research/README.md`](research/README.md) to locate each plane's source of truth; other READMEs
are navigation maps.

## Universal workflow

### Mathematical contribution

1. Sharpen or confirm a target, or supply a standalone proof dossier.
2. When a claim changes, update its manuscript statement and ledger state, provenance, and edges
   together.
3. After a ledger edit, leave `python3 scripts/check_ledger.py` at 0 errors.
4. Record the attempt, **including dead ends**, in a new
   `research/explorations/YYYY-MM-DD-slug.md`, with the validated front matter in
   [`research/explorations/README.md`](research/explorations/README.md): what it engaged, what
   it produced, which run artifacts it cites. A finding reusable enough to be cited elsewhere
   earns a ledger node and a manuscript statement, not a second home in a side registry.
5. A statement not yet stable enough for the manuscript and ledger is a **candidate**: it goes
   in that exploration's `candidates:` list and nowhere else (constraint 8).

### Proof contribution

Follow [`solutions/README.md`](solutions/README.md). An author never certifies their own proof;
`proofs[].mode: agent` requires a persisted review naming distinct author(s) and reviewer.

### Harness or repository contribution

Record the rationale and validation in a new `decisions/YYYY-MM-DD-slug.md`. Do not
invent a mathematical attempt; harness work does not by itself change mathematical status.

## Hard constraints

These are the universal constraints. They are numbered, and append-only records cite the numbers,
so **do not renumber them** — a constraint that stops applying becomes `**Reserved.**` and keeps
its slot. Constraints specific to this repository's mathematics go in the next section, numbered
`P1, P2, …`, so that a fork can drop them without disturbing this list.

1. **A ledger is a single-file write-contention point.** This repository has exactly one program
   ledger, `research/program/ledger.yaml`. Funnel every ledger edit through one orchestrator.
   Role definitions may narrow write access; no spawned role writes the ledger.
2. **Numerical work must be public and reproducible.** All numerical experiments must be executed
   through the `numerics` harness into a provenance-stamped artifact. Numerical output certifies no
   claim, proof step, or dossier. Exact arithmetic or an analytic witness it emits remains a
   candidate until checked independently in the proof or refutation workflow.
3. **The research battery is shared.** Use `research/instances.md`. Anyone may propose
   an adversarial instance; only the `synthesizer` curates the registry. Passing a finite battery
   changes no claim or proof status.
4. **`check_ledger.py` is necessary, not sufficient.** A green check establishes structure only.
   Semantic agreement among manuscript, ledger, and dossier, and the correctness of a proof,
   require independent review.
5. **Respect established fences.** `bounded_by` may name only a proved obstruction. A statement
   violating one is wrong by construction. Put plausible but unproved method barriers in
   `heuristic_barriers`; they guide work but do not logically fence a claim.
6. **Reserved.**
7. **`research/explorations/` and `decisions/` are append-only.** Add dated files; never
   rewrite or delete their history.
8. **A candidate statement is not a ledger node.** A tentative statement lives in
   the `candidates:` front matter of the exploration that proposed it, under a `cand:<slug>`
   id, and carries no manuscript anchor, no status, and no certification. It is killed by a
   later exploration naming it in `retires:`. Once it is precise, stable, and worth reusing or
   tracking on the research frontier, promote it by adding a `\label` in `modules/` and a ledger
   node, at which point it is subject to every constraint above.
   `python3 scripts/check_ledger.py candidates` lists the live ones. There is no other place a
   statement may be written down.
9. **Truth and applicability are separate.** A proved implication remains `proved` when its
   antecedent is open. Put antecedents in `assumes`, conclusions in `implies`, and only claims
   actually used to prove the implication in `depends_on`. Never encode an antecedent as a proof
   dependency merely to make a conditional status propagate.
10. **Proof provenance is plural.** An internally proved node has one or more `proofs` records.
    Each record names its dossier and independent certification mode, so alternative proofs can
    coexist. A dossier may reuse certified dependency nodes instead of reproving them.
11. **Quantifiers govern refutation.** A refutation dossier must negate the exact quantified
    statement. A single witness refutes a universal claim; failure of a dimension-free or
    uniform constant generally requires a certified family with the relevant divergence.

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
python3 scripts/check_ledger.py candidates
python3 scripts/check_agents.py
```
