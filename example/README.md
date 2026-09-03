# example/ — the worked example

One instance of every artifact genre this harness validates, arranged exactly as a real
repository arranges them. It is a **fixture, not history**: nothing here records a search
anyone ran, so `CLAUDE.md` constraint 7 does not apply to it and you may edit or delete
any of it freely.

Copy from it. Do not build on it.

```bash
python3 scripts/check.py --root example      # kept green by scripts/check.sh
```

## What is in it

| genre | file |
|---|---|
| manuscript module | [`modules/00-overview.tex`](modules/00-overview.tex) |
| claim graph | [`research/program/ledger.yaml`](research/program/ledger.yaml) |
| problem brief | [`research/program/brief.md`](research/program/brief.md) |
| search portfolio | [`research/program/portfolio.yaml`](research/program/portfolio.yaml) |
| proof dossier | [`solutions/prop-example.tex`](solutions/prop-example.tex) |
| proof review | [`research/reviews/2026-09-01-prop-example-proof-review.md`](research/reviews/2026-09-01-prop-example-proof-review.md) |
| checkpoints | [`research/explorations/`](research/explorations/) |
| run artifact | [`research/runs/`](research/runs/) |

The brief keeps its instructional skeleton on purpose: being the document you copy and
fill in is what it is for. `python3 scripts/check.py ready` therefore reports this tree as
*not instantiated*, which is correct — it is a template's example, not a program.

## Where it came from

Everything here was at the repository root until
[`decisions/2026-09-03-harness-consistency-and-readiness.md`](../decisions/2026-09-03-harness-consistency-and-readiness.md)
moved it, so that a new repository starts with empty live planes instead of being told to
delete append-only records. Records written before that date still cite the old paths:

| was | is |
|---|---|
| `modules/00-overview.tex` | `example/modules/00-overview.tex` |
| the three nodes of `research/program/ledger.yaml` | `example/research/program/ledger.yaml` |
| `research/program/brief.md` | `example/research/program/brief.md` |
| `research/program/portfolio.yaml` | `example/research/program/portfolio.yaml` |
| `solutions/prop-example.tex` | `example/solutions/prop-example.tex` |
| `research/reviews/2026-09-01-prop-example-proof-review.md` | `example/research/reviews/…` |
| `research/explorations/2026-09-02-example-exploration.md` | `example/research/explorations/…` |
| `research/explorations/2026-09-03-example-dedup.md` | `example/research/explorations/…` |
| `research/runs/2026-09-02T092336.680787Z-example.jsonl` | `example/research/runs/…` |

## Three things it does differently, and why

- **It has no `.claude/`.** The roles lane skips a tree with no `.claude/agents/`, which is
  what keeps this fixture cheap. Adding one without a matching `.codex/` would turn it red.
- **It must stay a top-level sibling** of `research/` and `modules/`. Nested inside either,
  its ledger would trip the one-ledger rule and its checkpoints and run artifact would be
  swept into the live planes.
- **Its `.tex` files name `../../main.tex`** as the `subfiles` master, not the `../main.tex`
  that [`../solutions/TEMPLATE.tex`](../solutions/TEMPLATE.tex) teaches, because they sit one
  level deeper. Use `../main.tex` in a real repository.

`experiments/numerics/targets/example.py` deliberately stayed at the repository root: it is
reference code the numerics test suite exercises, not a research record. Running
`numerics run example` therefore writes into the root `research/runs/`, not into this tree's.
