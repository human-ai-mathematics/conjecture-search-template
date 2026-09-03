# Agent roles and execution contract

The Markdown files in this directory are the canonical role definitions for this repository.
`../../CLAUDE.md` is normative and wins on any conflict.

Claude Code reads the Markdown files directly. Codex does not: project-scoped Codex agents are
standalone TOML files. `python3 scripts/check.py --write-codex` generates
`../../.codex/agents/*.toml` from these canonical Markdown bodies, and
`python3 scripts/check.py --plane roles` rejects missing or stale adapters. Do not hand-edit a
generated TOML file.

Each role file is self-describing. Its frontmatter carries `name`, `description`, `tools`,
`read_only`, and `reasoning` (`high` or `ultra`), and the checker derives the roster from the
files on disk. Adding a role is one new file plus one row in the table below; there is no list of
role names to keep in sync anywhere else.

## Four core roles, and specialists

Conjecture search needs four things: orientation, attack, independent check, and convergence.
Those are `scout`, `researcher`, `reviewer`, and `synthesizer`.

Proving, refuting, mining an existing proof, and building a construction are **assignment
lenses** for the `researcher`, not separate role contracts — they share a write surface, a set
of prohibitions, and a handoff. Certifying a dossier and auditing manuscript/ledger agreement
are likewise the two lenses of the `reviewer`. Each lens is one file in
[`../lenses/`](../lenses/README.md), named by the orchestrator in the assignment and loaded on
its own: a role that surveys several lenses at once produces a shallow pass on all of them,
and one that *reads* several pays for strategies it was not asked to run.

The other three are **optional specialists**, activated by the work: `numerics` when there is
something to compute, `literature-scout` when there is something to import, `janitor` when the
repository needs tidying. A repository that does none of those should delete the ones it does
not use — `python3 scripts/check.py --write-codex` removes the orphaned adapter, and nothing
else refers to a role by name.

**Author and reviewer never coincide.** A `researcher` cannot write `research/reviews/`, and a
`reviewer` cannot write `solutions/`. That is an epistemic control, not administrative
ornament. When the runtime permits it, launch the reviewer without the author's conversation
history: the reviewer reconstructs the work from repository artifacts, not from the author's
account of it.

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

`research/program/portfolio.yaml` is the one exception: the `synthesizer` is its single writer,
because keeping the search coherent *is* that role's job. Everyone else proposes a portfolio
change through the handoff.

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

`portfolio_delta` is how parallel work stays coordinated without concurrent edits to one file.
State the approach, the state it should now be in, and — if blocked — the exact `cand:` id or
ledger node it is blocked on together with the condition that would reopen it. "This looks
hard" is not a blocker.

For a proof review, `outcome: complete` means the certifying report passed; `revise` means the
researcher receives the reviewer's exact repair instructions; `blocked` means no certification
delta is applicable. Prose containing words such as "pass" or "done" never controls a
transition.

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

Every role that creates a checkpoint receives a run id from the orchestrator and uses
`research/explorations/YYYY-MM-DD-<role>-<scope>-<run-id>.md`. If no run id was supplied,
choose a collision-resistant suffix and verify that the path does not exist. Never overwrite an
earlier record.

Each checkpoint opens with the front matter specified in `research/explorations/README.md` and
validated by `check.py`: what it engaged, which approach it belongs to, what it produced, and
which `research/runs/` artifacts it cites. A tentative statement is recorded there as a `cand:`
candidate and nowhere else (`CLAUDE.md` constraint 8); promoting one to a ledger node is the
orchestrator's act, like any other ledger edit.

## Roster

| role | lenses | writes | cardinality |
|---|---|---|---|
| [`scout`](scout.md) | — | nothing | N, parallel |
| [`researcher`](researcher.md) | [`prove`](../lenses/prove.md), [`refute`](../lenses/refute.md), [`mine`](../lenses/mine.md), [`construct`](../lenses/construct.md) | one dossier; one new checkpoint | 1 per dossier; N across distinct lenses and targets |
| [`reviewer`](reviewer.md) | [`certify`](../lenses/certify.md), [`sync`](../lenses/sync.md) | one new review | 1 cold reviewer per dossier |
| [`synthesizer`](synthesizer.md) | — | `portfolio.yaml`, `research/instances.md`; one new checkpoint | **singleton** |
| [`numerics`](numerics.md) | — | `experiments/numerics/`, generated runs, one new checkpoint | singleton for code; N for distinct stable runs |
| [`literature-scout`](literature-scout.md) | — | one new checkpoint | N; bibliography remains single-writer |
| [`janitor`](janitor.md) | — | nothing; proposal only | 1 |

### Adding a program-specific role

Four core roles carry the search — orienting, attacking, checking, converging — and three
optional specialists carry computing, importing and tidying. None of the seven mentions this
repository's mathematics, which is why the roster is the same in every repository built from
this template.

Prefer a new **lens** to a new role. A lens costs one file in [`../lenses/`](../lenses/README.md)
and no permissions; a role costs a contract, a generated adapter, a roster row, and a
concurrency key. When a program genuinely wants its own — a prober for a particular gate, a
refiner for a particular family of statements — write it as a new `.md` file here, add a row
above, then:

```bash
python3 scripts/check.py --write-codex
python3 scripts/check.py --plane roles
```

## Transitions

Use `scout` for unfamiliar, ambiguous, or broad assignments; it is not a mandatory tax when the
exact node and artifacts are already known.

```text
Explore:  scout -> researcher(refute) -> numerics (when requested)
                                     \-> researcher(prove)
External: literature-scout -> orchestrator
Mining:   researcher(mine) -> synthesizer | researcher(prove)
Proof:    researcher(prove) -> reviewer(certify) -> pass: orchestrator
                                              \-> revise: researcher (verbatim next_prompt)
Refute:   researcher(refute) -> researcher(prove) proves the refuter
                             -> reviewer(certify) -> orchestrator
Memory:   parallel findings -> synthesizer -> orchestrator
Sync:     reviewer(sync) -> orchestrator
Hygiene:  janitor -> orchestrator
```

A numerical result never skips the proof path. An exact `numerics` witness is still handed to a
`researcher`, independently certified by a `reviewer`, and only then used by the orchestrator as
`refuted_by` provenance.

## Where to fan out, where to converge

Fan out across read-only scouting, independent approaches in different families, refutation
lenses, and independent literature/mining questions. Do not fan out writes to a shared file.
`numerics` package edits, bibliography edits, instance curation, portfolio curation, manuscript
promotion, and ledger edits converge through their keys above.

The `synthesizer` owns the search portfolio and the mathematical merge barriers declared as
program constraints in `CLAUDE.md`. The live frontier is derived with
`python3 scripts/check.py status` and the live search with
`python3 scripts/check.py portfolio`; no role maintains a second copy of either.

## Validation

After changing a role or adapter:

```bash
python3 scripts/check.py --plane roles
```

Regenerate Codex adapters deliberately after reviewing the canonical Markdown change:

```bash
python3 scripts/check.py --write-codex
python3 scripts/check.py --plane roles
```
