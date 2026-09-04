# Program state

This directory owns two things that must not be confused: the **logical state** of the
program — what is claimed, what each claim depends on, which proof shapes are fenced — and the
**search state** — which routes are alive, blocked, or worked out. Statements themselves live
in [`../../modules/`](../../modules/).

Rename nothing: the directory is `program/` in every repository built from this template, so
the validator needs no configuration to find it. The program's *name* is `meta.program` in
[`ledger.yaml`](ledger.yaml), and that is the only place it is written down.

## Files

| question | source |
|---|---|
| Which node is the target, and what would finish it? | `brief.md` — gated; [scaffold](../../templates/brief.md), [worked](../../example/research/program/brief.md) |
| What does a filled-in one of any of these look like? | [`../../example/`](../../example/README.md) |
| What exactly does the target say? | [`../../modules/`](../../modules/), at its `\label` |
| What is each claim's status? | [`ledger.yaml`](ledger.yaml) |
| What ledger fields are valid? | [`ledger-schema.md`](ledger-schema.md) |
| Which routes are alive, blocked, duplicated, saturated? | `portfolio.yaml` — gated; [scaffold](../../templates/portfolio.yaml), [worked](../../example/research/program/portfolio.yaml) |
| What portfolio and brief fields are valid? | [`portfolio-schema.md`](portfolio-schema.md) |
| Which proof shapes are fenced or suspect? | Proved obstruction nodes via `bounded_by`; open ones via `heuristic_barriers` |
| Which conventions do claims rest on? | `kind: definition` nodes with `status: defined`, and `depends_on` |
| What has been attempted? | [`../explorations/`](../explorations/) |
| What can be computed numerically? | [`../../experiments/README.md`](../../experiments/README.md) |
| Where are proofs and reviews? | [`../../solutions/`](../../solutions/), [`../reviews/`](../reviews/) |

`brief.md` and `portfolio.yaml` are optional and activated by the work: the brief when a
sustained search starts, the portfolio when several routes, agents, or sessions are in flight.
An absent file is not a gap, and the checker validates only what exists. The one dependency
between them runs one way: a portfolio requires a brief, because several coordinated routes
*are* a sustained search; a brief needs no portfolio.

A fixed normalization — a sign, a scaling, a log base, which constant absorbs what — is a node
like any other: `kind: definition`, `status: defined`, stated in `../../modules/` under its
`\label`, with every claim that rests on it naming it in `depends_on`. `status: defined` is not
an unresolved premise; what it buys is that `check.py node <id>` *derives* which claims a
convention holds up. Do not keep a second list of conventions anywhere — changing one is a
mathematical edit, and the ledger is where that is visible.

A statement enters the ledger when it is precise, stable, and worth reusing or tracking on the
frontier. Until then it is a candidate: it lives in the `candidates:` front matter of the
checkpoint that proposed it, has no `\label`, no status and no certification, and is listed by
`python3 scripts/check.py candidates` (`CLAUDE.md` constraint 7). Promotion gives it a
manuscript statement and a node here — nothing is copied from one registry to another, because
there is no other registry — and it is a single act: the checkpoint recording it through
`promotes:` is what ends the candidate, and any route blocked on it moves to the node.

## Proving and refuting end in the same place

A refutation is not a shortcut past certification. The witness is a candidate; the statement it
establishes becomes a refuter node with its own manuscript statement and its own dossier; that
dossier is independently reviewed like any other; and only then does the target become
`status: refuted`, naming the proved refuter in `refuted_by`. The refuter never enters the
target's `depends_on` — that field records facts a proof used, and a refuted statement has no
proof. Quantifiers decide what suffices: one witness for a universal claim, generally a
certified divergent family for a uniform or dimension-free constant (constraint 10).

## Two writers, two stores

The ledger and manuscript are authoritative for mathematics, and the orchestrator is their sole
writer. The portfolio is authoritative for coordination, and the `synthesizer` is its sole
writer. Neither may hold the other's content: no route state in the ledger, no statement in the
portfolio (`CLAUDE.md` constraint 11).

Any further navigation document you add here is a mutable handoff carrying no claim status and
no duplicate dependency graph. When you add one, give it a concurrency key in
[`../../.claude/agents/README.md`](../../.claude/agents/README.md): it becomes a single-writer
file.

## Workflow

1. Read `brief.md`, then select a node from the ledger or an approach from the portfolio.
2. Read the node's manuscript anchor, `depends_on` closure, `assumes`/`implies`, and both
   classes of obstruction in full.
3. Record a checkpoint when the result is durable. Send numerical work through `numerics` and
   treat it as directional.
4. Propose the route's new state through the handoff's `portfolio_delta`.
5. Send accepted manuscript and ledger changes through the orchestrator.
6. Certify proofs through a standalone dossier and independent review.

Literature provenance requires a publication class and BibTeX references. A proved implication
remains proved when an antecedent is open; `assumes` records that applicability blocker.

## Verify

```bash
python3 scripts/check.py
python3 scripts/check.py ready
python3 scripts/check.py status
python3 scripts/check.py portfolio
python3 scripts/check.py candidates
```

The checker validates structure, not mathematical correctness.
