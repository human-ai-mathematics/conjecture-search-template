# Program control plane

This directory owns the logical state of the repository's program: what is claimed, what each
claim depends on, and which proof shapes are fenced. Statements themselves live in
[`../../modules/`](../../modules/).

Rename nothing: the directory is `program/` in every repository built from this template, so the
validators need no configuration to find it. The program's *name* is `meta.program` in
[`ledger.yaml`](ledger.yaml), and that is the only place it is written down.

## Files

| question | source |
|---|---|
| What is the target and each claim's status? | [`ledger.yaml`](ledger.yaml) |
| What ledger fields are valid? | [`../ledger-schema.md`](../ledger-schema.md) |
| Which proof shapes are fenced? | [`obstructions.md`](obstructions.md) and ledger `bounded_by` |
| What has been attempted? | [`../explorations/`](../explorations/) |
| What can be computed numerically? | [`../../experiments/README.md`](../../experiments/README.md) |
| Where are proofs and reviews? | [`../../solutions/`](../../solutions/), [`../reviews/`](../reviews/) |

The ledger and manuscript are authoritative. Any navigation document you add here — route briefs,
target briefs, a gating table — is a mutable handoff and carries no claim status and no duplicate
dependency graph. When you add one, give it a concurrency key in
[`../../.claude/agents/README.md`](../../.claude/agents/README.md): it becomes a single-writer file.

## Workflow

1. Select a node from the ledger.
2. Read its manuscript anchor, `depends_on` closure, and every `bounded_by` obstruction in full.
3. Record the attempt in a new dated exploration. Send numerical work through `numerics` and treat
   it as directional.
4. Send accepted manuscript and ledger changes through the orchestrator.
5. Certify proofs through a standalone dossier and independent review.

Imported nodes require a publication class and BibTeX references. A certified conditional
implication remains `conditional` while any blocking premise or unreviewed import remains.

## Verify

```bash
python3 scripts/check_ledger.py
python3 scripts/check_ledger.py status
```

The checker validates structure, not mathematical correctness.
