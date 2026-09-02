# Agent roles and execution contract

The Markdown files in this directory are the canonical role definitions for this repository.
`../../CLAUDE.md` is normative and wins on any conflict.

Claude Code reads the Markdown files directly. Codex does not: project-scoped Codex agents are
standalone TOML files. `python3 scripts/check_agents.py --write-codex` generates
`../../.codex/agents/*.toml` from these canonical Markdown bodies, and
`python3 scripts/check_agents.py` rejects missing or stale adapters. Do not hand-edit a generated
TOML file.

Each role file is self-describing. Its frontmatter carries `name`, `description`, `tools`,
`read_only`, and `reasoning` (`high` or `ultra`), and the checker derives the roster from the
files on disk. Adding a role is one new file plus one row in the table below; there is no list of
role names to keep in sync anywhere else.

## The orchestrator is the main session

The orchestrator is not a spawnable role. It owns every single-file merge point:

- `research/program/ledger.yaml`;
- `references.bib`;
- any route or target control document under `research/program/`;
- accepted manuscript statement changes; and
- application of proposed deltas returned by roles.

No role writes those files. A role proposes an exact delta; the orchestrator resolves contention,
applies accepted changes atomically, and runs the relevant validators.

## Shared handoff envelope

Every role keeps its role-specific report, then ends with this compact envelope:

```yaml
outcome: complete | revise | blocked | no-change
artifacts:
  - <repo-relative path, or none>
proposed_deltas:
  - <exact proposal, or none>
next_role: <role name, orchestrator, or none>
next_prompt: |
  <complete instructions for the next role, or empty>
```

`next_prompt` is an instruction, not a summary. The orchestrator passes it verbatim. A downstream
role must not be launched from an inferred or softened version of a finding.

For a proof review, `outcome: complete` means the certifying report passed; `revise` means the
prover receives the reviewer's exact repair instructions; `blocked` means no certification delta
is applicable. Prose containing words such as "pass" or "done" never controls a transition.

## Concurrency keys

Parallel work is allowed only when concurrency keys differ. Cardinality is enforced by the
orchestrator, not by a role saying "singleton" about itself.

| key | owner / rule |
|---|---|
| `ledger` | orchestrator only |
| `bibliography` | orchestrator only; literature scouts propose entries |
| `manuscript` | orchestrator only; `latex-sync` audits and proposes patches |
| `instances` | one `synthesizer` |
| `numerics-code` | one `numerics` whenever `experiments/numerics/**` changes |
| `numerics-run:<target>:<profile>:<seed>` | parallel only for distinct stable runs |
| `solution:<dossier>` | one `prover`; its reviewer uses a distinct agent identity |
| `review:<dossier>` | one cold `proof-checker` at a time |
| `exploration:<path>` | exclusive create-only path |

Add a key here whenever this repository grows a new single-writer file — a route control
document, a gating table, a second registry.

Every role that creates an exploration receives a run id from the orchestrator and uses
`research/explorations/YYYY-MM-DD-<role>-<scope>-<run-id>.md`. If no run id was supplied, choose a
collision-resistant suffix and verify that the path does not exist. Never overwrite an earlier
record.

Each exploration opens with the front matter specified in `research/explorations/README.md` and
validated by `check_ledger.py`: what it engaged, what it produced, and which `research/runs/`
artifacts it cites. A tentative statement is recorded there as a `cand:` candidate and nowhere
else (`CLAUDE.md` constraint 8); promoting one to a ledger node is
the orchestrator's act, like any other ledger edit.

## Roster

| role | writes | cardinality |
|---|---|---|
| [`scout`](scout.md) | nothing | N, parallel |
| [`numerics`](numerics.md) | `experiments/numerics/`, generated runs, one new exploration | singleton for code; N for distinct stable runs |
| [`prover`](prover.md) | one dossier; one new exploration | 1 per dossier |
| [`refutation-seeker`](refutation-seeker.md) | one new exploration | N, one lens each |
| [`proof-checker`](proof-checker.md) | one new review | 1 cold reviewer per dossier |
| [`synthesizer`](synthesizer.md) | `research/instances.md`; one new exploration | **singleton** |
| [`latex-sync`](latex-sync.md) | nothing; patch proposal only | 1 |
| [`janitor`](janitor.md) | nothing; proposal only | 1 |
| [`proof-miner`](proof-miner.md) | one new exploration | N |
| [`literature-scout`](literature-scout.md) | one new exploration | N; bibliography remains single-writer |

Author and reviewer never coincide. A `prover` cannot write `research/reviews/`, and a
`proof-checker` cannot write `solutions/`. When the runtime permits it, launch the proof checker
without the prover's conversation history: the reviewer reconstructs the proof from repository
artifacts, not from the author's account of the work.

### Adding a program-specific role

The ten roles above are the backbone: they are about proving, checking, refuting, mining,
scouting, computing and tidying, and none of them mentions this repository's mathematics. A
program usually wants one or two roles of its own — a prober for a particular gate, a refiner for
a particular family of statements. Write it as a new `.md` file here, add a row above, then:

```bash
python3 scripts/check_agents.py --write-codex
python3 scripts/check_agents.py
```

## Transitions

Use `scout` for unfamiliar, ambiguous, or broad assignments; it is not a mandatory tax when the
exact node and artifacts are already known.

```text
Explore:  scout -> refutation-seeker -> numerics (when requested)
                                    \-> prover
External: literature-scout -> orchestrator
Mining:   proof-miner -> synthesizer | prover
Proof:    prover -> proof-checker -> pass: orchestrator
                                \-> revise: prover (verbatim next_prompt)
Refute:   refutation-seeker -> prover proves refuter -> proof-checker -> orchestrator
Memory:   parallel findings -> synthesizer -> orchestrator
Sync:     latex-sync -> orchestrator
Hygiene:  janitor -> orchestrator
```

A numerical result never skips the proof path. An exact `numerics` witness is still handed to a
`prover`, independently certified by a `proof-checker`, and only then used by the orchestrator as
`refuted_by` provenance.

## Where to fan out, where to converge

Fan out across read-only scouting, independent gates in different routes, refutation lenses, and
independent literature/mining questions. Do not fan out writes to a shared file. `numerics`
package edits, bibliography edits, instance curation, manuscript promotion, and ledger edits
converge through their keys above.

The `synthesizer` owns the mathematical merge barriers declared as program constraints in
`CLAUDE.md`. The live frontier is derived with `python3 scripts/check_ledger.py status`; no role
maintains a second copy.

## Validation

After changing a role or adapter:

```bash
python3 scripts/check_agents.py
```

Regenerate Codex adapters deliberately after reviewing the canonical Markdown change:

```bash
python3 scripts/check_agents.py --write-codex
python3 scripts/check_agents.py
```
