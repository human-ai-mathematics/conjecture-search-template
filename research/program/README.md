# Program control plane

This directory owns the logical state of the repository's program: what is claimed, what each claim
depends on, and which proof shapes are fenced. Statements themselves live in
[`../../modules/`](../../modules/).

Rename nothing: the directory is `program/` in every repository built from this template, so the
validators need no configuration to find it. The program's *name* is `meta.program` in
[`ledger.yaml`](ledger.yaml), and that is the only place it is written down.

## Files

| question | source |
|---|---|
| What is the target and each claim's status? | [`ledger.yaml`](ledger.yaml) |
| What ledger fields are valid? | [`ledger-schema.md`](ledger-schema.md) |
| Which proof shapes are fenced or suspect? | Proved obstruction nodes via `bounded_by`; open ones via `heuristic_barriers` |
| Which conventions do claims rest on? | `kind: definition` nodes with `status: defined`, and `depends_on` |
| What has been attempted? | [`../explorations/`](../explorations/) |
| What can be computed numerically? | [`../../experiments/README.md`](../../experiments/README.md) |
| Where are proofs and reviews? | [`../../solutions/`](../../solutions/), [`../reviews/`](../reviews/) |

A fixed normalization — a sign, a scaling, a log base, which constant absorbs what — is a node like
any other: `kind: definition`, `status: defined`, stated in `../../modules/` under its `\label`,
with every claim that rests on it naming it in `depends_on`. `status: defined` is not an unresolved
premise; what it buys is that `check_ledger.py
node <id>` *derives* which claims a convention holds up. Do not keep a second list of conventions
anywhere — changing one is a mathematical edit, and the ledger is where that is visible.

A statement enters this ledger when it is precise, stable, and worth reusing or tracking on the
frontier. Until then it is a candidate: it
lives in the `candidates:` front matter of the exploration that proposed it, has no `\label`,
no status and no certification, and is listed by `python3 scripts/check_ledger.py candidates`
(`CLAUDE.md` constraint 8). Promotion is the act of giving it a manuscript statement and a node
here — nothing is copied from one registry to another, because there is no other registry.

The ledger and manuscript are authoritative. Any navigation document you add here — route briefs,
target briefs, a gating table — is a mutable handoff and carries no claim status and no duplicate
dependency graph. When you add one, give it a concurrency key in
[`../../.claude/agents/README.md`](../../.claude/agents/README.md): it becomes a single-writer file.

## Workflow

1. Select a node from the ledger.
2. Read its manuscript anchor, `depends_on` closure, `assumes`/`implies`, and both classes of
   obstruction in full.
3. Record the attempt in a new dated exploration. Send numerical work through `numerics` and treat
   it as directional.
4. Send accepted manuscript and ledger changes through the orchestrator.
5. Certify proofs through a standalone dossier and independent review.

Literature provenance requires a publication class and BibTeX references. A proved implication
remains proved when an antecedent is open; `assumes` records that applicability blocker.

## Verify

```bash
python3 scripts/check_ledger.py
python3 scripts/check_ledger.py status
python3 scripts/check_ledger.py candidates
```

The checker validates structure, not mathematical correctness.
