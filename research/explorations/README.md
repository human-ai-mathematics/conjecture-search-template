# explorations/ — dated checkpoints

Durable search memory. One Markdown file per **durable search event**, not per attempt:
`YYYY-MM-DD-slug.md`, or `YYYY-MM-DD-<role>-<scope>-<run-id>.md` for agent work. Append-only
(`CLAUDE.md` constraint 6): never rewrite or delete one.

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
  - conj:example
artifacts:
  - research/runs/2026-09-02T092336.680787Z-example.jsonl
supersedes:
  - research/explorations/2026-09-01-earlier-summary.md
---
```

| field | requirement | meaning |
|---|---|---|
| `type` | required | Always `exploration`. |
| `date` | required | Quoted ISO date matching the filename prefix, or a UTC timestamp `YYYY-MM-DDTHH:MM:SSZ` whose date part does. |
| `outcome` | required | What the work produced: see below. |
| `nodes` | one of `nodes`, `approach`, `candidates` | Ledger node ids engaged; each must resolve. |
| `approach` | one of `nodes`, `approach`, `candidates` | The `ap:` id in the portfolio this belongs to. |
| `artifacts` | optional | Repo-relative `research/runs/` artifacts cited; each must exist. |
| `candidates` | required iff `outcome: candidate` | Candidate statements proposed here. |
| `retires` | optional | Candidate ids an earlier checkpoint proposed and this one kills. |
| `promotes` | optional | Candidate ids an earlier checkpoint proposed and this one turned into ledger nodes. |
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

`approach` is what connects durable memory to the search portfolio at
`../program/portfolio.yaml` (gated; [scaffold](../../templates/portfolio.yaml)): the checkpoint says why a route's
state changed, the portfolio says what that state now is. The portfolio's `checkpoints:` list
points back to that route-specific record.

The link is checked. A `blocked`, `completed` or `duplicate` route must name at least one
checkpoint; every path it names must resolve to a record here that actually parses as a
checkpoint and declares the route that lists it. A node-only checkpoint remains valid durable
memory, but it cannot explain a portfolio state change.

### `retires` versus `supersedes`

They mean different things and neither deletes anything:

- `retires:` says a tentative **statement** is no longer live because it died;
- `promotes:` says a tentative statement is no longer live because it became a node;
- `supersedes:` says a later **record** should be read instead of an earlier one.

`python3 scripts/check.py checkpoints` prints the current heads — every record nothing later
has superseded. The full archive stays exactly where it is. Supersession only ever points
backwards in time. The same relation is available to non-certifying `type: audit` reports in
[`../reviews/`](../reviews/); proof reviews keep their stricter semantics.

### Two records on the same day

A filename is not a clock, so the checker claims an order only where it has one:

- **different days** — ordered, and checked as before;
- **same day, both timestamped** — ordered by the timestamp, and checked;
- **same day, either untimed** — *unordered*. A same-day proposal and promotion is accepted,
  because it is the ordinary shape of a productive session, and supersession is instead
  verified to be acyclic directly.

Write a plain `date:` unless two records genuinely need separating; then give both a UTC
timestamp. `python3 scripts/new.py checkpoint <slug> --node <node-id>` stamps one for you;
use `--approach ap:<slug>` instead when the checkpoint is route-specific. Nothing on disk
ever needs renaming — this file's name keeps its `YYYY-MM-DD-` prefix either way, and
`CLAUDE.md` constraint 6 stands untouched.

## Candidate statements

A candidate is a tentative statement someone thought worth writing down and nothing more
(`CLAUDE.md` constraint 7). It has no manuscript anchor, no ledger node, and no status,
because it is not yet stable enough for the program graph:

```yaml
candidates:
  - id: cand:example-identity-stability
    statement: >-
      A precise statement someone could later prove or refute.
```

The candidate's `statement:` is canonical — nothing else in the repository holds that text,
which is the whole reason a candidate is allowed to carry one. Contrast a ledger node, whose
`summary:` is a gloss because `modules/` holds the statement.

Ids are namespaced `cand:<slug>` so they can never be mistaken for a node id, and they are
unique across the whole log. A candidate is **live** until some later checkpoint retires or
promotes it; nothing is edited in place to kill one.

```bash
python3 scripts/check.py candidates   # every live candidate, with where it came from
```

This is not a registry, and it is not a second home for results. It is durable memory
answering a question about itself. A candidate is also the only admissible target of a
portfolio `blocker:` other than a ledger node: if a route is worth formally blocking, its
missing lemma is worth stating precisely.

### Promotion is one act

Promote a candidate when it is precise, stable, and useful enough to reuse or track on the
frontier. Promotion is four things done together, not a node addition with paperwork to
follow:

1. the statement gets a `\label` in `modules/`, inside the claim environment matching its
   kind;
2. it gets a ledger node with that id (proved internal nodes additionally require a
   certified dossier);
3. **a checkpoint records the promotion**, which is what ends the candidate:

   ```yaml
   promotes:
     - candidate: cand:example-identity-stability
       node: lem:example-identity-stability
   ```

4. every portfolio route blocked on the candidate is repointed at the node.

Steps 3 and 4 are checked: a promoted candidate leaves `check.py candidates`, a `promotes:`
entry naming a node that does not exist is an error, and a `blocker:` still naming the
promoted candidate is an error that tells you which node to use. Without step 3 the
candidate stayed live forever and one statement had two homes, which is exactly what
`CLAUDE.md` constraint 7 exists to prevent.

The node id need not resemble the candidate id — `cand:x` normally becomes `lem:x` or
`thm:x` — which is why the promotion is recorded as a pair rather than inferred.

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
