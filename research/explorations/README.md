# explorations/ — dated checkpoints

Durable search memory. One Markdown file per **durable search event**, not per attempt:
`YYYY-MM-DD-slug.md`, or `YYYY-MM-DD-<role>-<scope>-<run-id>.md` for agent work. Append-only
(`CLAUDE.md` constraint 7): never rewrite or delete one.

The directory keeps its historical name; the records in it are *checkpoints*.

## When a checkpoint is required

Write one when the work:

- creates or retires a candidate statement;
- identifies a reusable dead end or an exact blocker;
- blocks, reopens, duplicates, or saturates a portfolio approach;
- produces a numerical or literature artifact future work may use;
- proposes a manuscript or ledger change; or
- synthesizes a batch of parallel work.

A speculative calculation that fails in ten minutes needs no file. A dead end becomes durable
when it is plausible or expensive enough that another researcher would repeat it. Recording
everything is how a log stops being read; recording nothing is how a week gets spent twice.

## Front matter

Every checkpoint opens with a machine-readable envelope, validated by
[`../../scripts/check.py`](../../scripts/check.py). It records what the work *engaged*, never
what it concluded — a conclusion is prose, and a conclusion that earns reuse becomes a ledger
node.

```yaml
---
type: exploration
date: "2026-09-02"
outcome: dead-end
approach: ap:example-finite-battery
nodes:
  - q:example
artifacts:
  - research/runs/2026-09-02T092336.680787Z-example.jsonl
supersedes:
  - research/explorations/2026-09-01-earlier-summary.md
---
```

| field | requirement | meaning |
|---|---|---|
| `type` | required | Always `exploration`. |
| `date` | required | Quoted ISO date matching the filename prefix. |
| `outcome` | required | What the work produced: see below. |
| `nodes` | one of `nodes`, `approach`, `candidates` | Ledger node ids engaged; each must resolve. |
| `approach` | one of `nodes`, `approach`, `candidates` | The `ap:` id in the portfolio this belongs to. |
| `artifacts` | optional | Repo-relative `research/runs/` artifacts cited; each must exist. |
| `candidates` | required iff `outcome: candidate` | Candidate statements proposed here. |
| `retires` | optional | Candidate ids an earlier checkpoint proposed and this one kills. |
| `supersedes` | optional | Strictly earlier checkpoints this one replaces as the current reading. |

### Outcomes

| value | meaning |
|---|---|
| `dead-end` | The approach failed. Say why, so nobody spends the week again. |
| `directional` | Evidence gathered, nothing closed. Numerical runs usually land here. |
| `candidate` | Produced one or more candidate statements worth not losing. |
| `proposed` | Produced a concrete ledger or manuscript delta for the orchestrator. |

Work that both failed and threw off a candidate is `candidate`: the outcome names what the
*next* agent can pick up.

### `approach` — the link to the portfolio

`approach` is what connects durable memory to
[`../program/portfolio.yaml`](../program/portfolio.yaml): the checkpoint says why a route's
state changed, the portfolio says what that state now is. The portfolio's `checkpoints:` list
points back, which is how a record written before the portfolio existed can still be attached
to a route without editing it.

### `retires` versus `supersedes`

They mean different things and neither deletes anything:

- `retires:` says a tentative **statement** is no longer live;
- `supersedes:` says a later **record** should be read instead of an earlier one.

`python3 scripts/check.py checkpoints` prints the current heads — every record nothing later
has superseded. The full archive stays exactly where it is. Supersession only ever points
backwards in time, which is what makes it acyclic. The same relation is available to
non-certifying `type: audit` reports in [`../reviews/`](../reviews/); proof reviews and
decision records keep their stricter semantics.

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
unique across the whole log. A candidate is **live** until some later checkpoint names it in
`retires:`; nothing is edited in place to kill one.

```bash
python3 scripts/check.py candidates   # every live candidate, with where it came from
```

This is not a registry, and it is not a second home for results. It is durable memory
answering a question about itself. A candidate is also the only admissible target of a
portfolio `blocker:` other than a ledger node: if a route is worth formally blocking, its
missing lemma is worth stating precisely.

Promote a candidate when it is precise, stable, and useful enough to reuse or track on the
frontier: it then earns a `\label` in `modules/` and a ledger node. Proved internal nodes
additionally require a certified dossier.

## Body

Record, in prose, below the front matter:

- **What** you tried — which node, which form of the statement, which construction.
- **How** — which `numerics` run and which instances; link the provenance-stamped artifact.
- **Outcome** — dead end, directional observation, candidate refutation, or analytic result;
  include the relevant numbers or the exact witness without treating a run as certification.
- **Why** it failed, or what it unlocked — and, if the route is now blocked, the exact lemma
  that would unblock it.

A dead end recorded plainly is worth as much as a success here: it is the only thing that stops
the next agent spending the same week. Say what you actually tried, not what you wish you had.

Accepted statement and ledger changes go through the orchestrator; they are not made here. A
portfolio state change is proposed through the handoff's `portfolio_delta` and applied by the
`synthesizer`. An adversarial instance worth reusing is proposed to the `synthesizer` for
[`../instances.md`](../instances.md).
