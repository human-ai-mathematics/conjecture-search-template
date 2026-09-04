# Execution contract

What every role loads before doing anything, and nothing else. Who the roles are, how to
add one, and how the Codex adapters are generated is in
[`MAINTAINING.md`](MAINTAINING.md) — a role executing a task never needs it.

`../../CLAUDE.md` is normative and wins on any conflict.

## Author and reviewer never coincide

A `researcher` cannot write `research/reviews/`, and a `reviewer` cannot write
`solutions/`. That is an epistemic control, not administrative ornament. When the runtime
permits it, launch the reviewer without the author's conversation history: the reviewer
reconstructs the work from repository artifacts, not from the author's account of it.

## The orchestrator is the main session

The orchestrator is not a spawnable role. It owns every single-file merge point except the
portfolio:

- `research/program/ledger.yaml`;
- `research/program/brief.md`;
- `references.bib`;
- accepted manuscript statement changes; and
- application of proposed deltas returned by roles.

No role writes those files. A role proposes an exact delta; the orchestrator resolves
contention, applies accepted changes atomically, and runs the relevant validators.

`research/program/portfolio.yaml` is the one exception: the `synthesizer` is its single
writer, because keeping the search coherent *is* that role's job. Everyone else proposes a
portfolio change through the handoff.

## Four roles ship; three are installed when needed

`scout`, `researcher`, `reviewer` and `synthesizer` are always present. `numerics`,
`literature-scout` and `janitor` are **capability packs** in `packs/`, installed with
`python3 scripts/new.py role <pack>`. A handoff may name one that is not installed yet —
say `next_role: numerics` for a diagnostic — and the orchestrator installs it before
dispatching. Nothing else about them differs once installed.

## Shared handoff envelope

Every role keeps its role-specific report, then ends with this compact envelope:

```yaml
outcome: complete | revise | blocked | no-change
artifacts:
  - <repo-relative path, or none>
proposed_deltas:
  - <exact proposal, or none>
portfolio_delta:
  - <approach id, new state, exact blocker and reopen condition, or none>
next_role: <role name, orchestrator, or none>
next_prompt: |
  <complete instructions for the next role, or empty>
```

`next_prompt` is an instruction, not a summary. The orchestrator passes it verbatim. A
downstream role must not be launched from an inferred or softened version of a finding.

`portfolio_delta` is how parallel work stays coordinated without concurrent edits to one
file. State the approach, the state it should now be in, and — if blocked — the exact
`cand:` id or ledger node it is blocked on together with the condition that would reopen
it. "This looks hard" is not a blocker.

For a proof review, `outcome: complete` means the certifying report passed; `revise` means
the researcher receives the reviewer's exact repair instructions; `blocked` means no
certification delta is applicable. Prose containing words such as "pass" or "done" never
controls a transition.

## Concurrency keys

Parallel work is allowed only when concurrency keys differ. Cardinality is enforced by the
orchestrator, not by a role saying "singleton" about itself.

| key | owner / rule |
|---|---|
| `ledger` | orchestrator only |
| `brief` | orchestrator only |
| `portfolio` | one `synthesizer`; every other role proposes through `portfolio_delta` |
| `bibliography` | orchestrator only; literature scouts propose entries |
| `manuscript` | orchestrator only; a `reviewer` on the `sync` lens audits and proposes patches |
| `instances` | one `synthesizer` |
| `numerics-code` | one `numerics` whenever `experiments/numerics/**` changes |
| `numerics-run:<target>:<profile>:<seed>` | parallel only for distinct stable runs |
| `solution:<dossier>` | one `researcher`; its reviewer uses a distinct agent identity |
| `review:<dossier>` | one cold `reviewer` at a time |
| `checkpoint:<path>` | exclusive create-only path |

Add a key here whenever this repository grows a new single-writer file.

## Writing a checkpoint

Every role that creates a checkpoint receives a run id from the orchestrator and uses
`research/explorations/YYYY-MM-DD-<role>-<scope>-<run-id>.md`. If no run id was supplied,
choose a collision-resistant suffix and verify that the path does not exist. Never
overwrite an earlier record.

Each checkpoint opens with the front matter specified in
`research/explorations/README.md` and validated by `check.py`: what it engaged, what it
produced, and which `research/runs/` artifacts it cites. Name the route in `approach:`
when this repository has a portfolio; when it has none, name the ledger nodes you engaged
in `nodes:`. A tentative statement is recorded there as a `cand:` candidate and nowhere
else (`CLAUDE.md` constraint 7); promoting one to a ledger node is the orchestrator's act,
and the same checkpoint that records the promotion retires the candidate through
`promotes:`.
