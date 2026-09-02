# explorations/ — the dated attempt log

One Markdown file per nontrivial attempt, **including dead ends**: `YYYY-MM-DD-slug.md`, or
`YYYY-MM-DD-<role>-<scope>-<run-id>.md` for agent work. This is how the next agent avoids
re-running a refuted form or a known-failing approach. Append-only (`CLAUDE.md` constraint 7):
never rewrite or delete one.

## Front matter

Every exploration opens with a machine-readable envelope, validated by
[`../../scripts/check_ledger.py`](../../scripts/check_ledger.py). It records what the attempt
*engaged*, never what it concluded — a conclusion is prose, and a conclusion that earns reuse
becomes a ledger node.

```yaml
---
type: exploration
date: "2026-09-02"
outcome: dead-end
nodes:
  - q:example
artifacts:
  - research/runs/2026-09-02T092336.680787Z-example.jsonl
---
```

| field | requirement | meaning |
|---|---|---|
| `type` | required | Always `exploration`. |
| `date` | required | Quoted ISO date matching the filename prefix. |
| `outcome` | required | What the attempt produced: see below. |
| `nodes` | required unless `candidates` is present | Ledger node ids this attempt engaged; each must resolve. |
| `artifacts` | optional | Repo-relative `research/runs/` artifacts the attempt cites; each must exist. |
| `candidates` | required iff `outcome: candidate` | Candidate statements proposed here. |
| `retires` | optional | Candidate ids an earlier exploration proposed and this one kills. |

### Outcomes

| value | meaning |
|---|---|
| `dead-end` | The approach failed. Say why, so nobody spends the week again. |
| `directional` | Evidence gathered, nothing closed. Numerical runs usually land here. |
| `candidate` | Produced one or more candidate statements worth not losing. |
| `proposed` | Produced a concrete ledger or manuscript delta for the orchestrator. |

An attempt that both failed and threw off a candidate is `candidate`: the outcome names what
the *next* agent can pick up.

## Candidate statements

A candidate is a tentative statement someone thought worth writing down and nothing more
(`CLAUDE.md` constraint 8). It has no manuscript anchor, no ledger node, and no status,
because it is not yet stable enough for the program graph:

```yaml
candidates:
  - id: cand:example-identity-stability
    statement: >-
      A precise statement someone could later prove or refute.
```

Ids are namespaced `cand:<slug>` so they can never be mistaken for a node id, and they are
unique across the whole log. A candidate is **live** until some later exploration names it in
`retires:`; nothing is edited in place to kill one.

```bash
python3 scripts/check_ledger.py candidates   # every live candidate, with where it came from
```

This is not a registry, and it is not a second home for results. It is the attempt log
answering a question about itself. Promote a candidate when it is precise, stable, and useful
enough to reuse or track on the frontier: it then earns a `\label` in `modules/` and a ledger
node. Proved internal nodes additionally require a certified dossier.

## Body

Record, in prose, below the front matter:

- **What** you tried — which node, which form of the statement, which construction.
- **How** — which `numerics` run and which instances; link the provenance-stamped artifact.
- **Outcome** — dead end, directional observation, candidate refutation, or analytic result;
  include the relevant numbers or the exact witness without treating a run as certification.
- **Why** it failed, or what it unlocked.

A dead end recorded plainly is worth as much as a success here: it is the only thing that stops
the next agent spending the same week. Say what you actually tried, not what you wish you had.

Accepted statement and ledger changes go through the orchestrator; they are not made here. An
adversarial instance worth reusing is proposed to the `synthesizer` for
[`../instances.md`](../instances.md).
