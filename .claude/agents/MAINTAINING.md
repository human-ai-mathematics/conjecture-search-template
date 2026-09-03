# Maintaining the roster

For whoever changes the roles, not for a role executing a task. The contract an agent
loads at run time is [`README.md`](README.md); this file is how that roster is built,
extended, and kept in sync with the Codex adapters.

`../../CLAUDE.md` is normative and wins on any conflict.

## How a role is defined

Each role file in this directory is self-describing. Its front matter carries `name`,
`description`, `tools`, `read_only`, and `reasoning` (`high` or `ultra`), and
`scripts/check.py` derives the roster from the files on disk. There is no list of role
names to keep in sync anywhere else — adding a role is one new file plus one row in the
table below.

Claude Code reads the Markdown files directly. Codex does not: project-scoped Codex
agents are standalone TOML files. `python3 scripts/check.py --write-codex` generates
`../../.codex/agents/*.toml` from these canonical Markdown bodies, and
`python3 scripts/check.py --lane roles` rejects a missing or stale adapter. Do not
hand-edit a generated TOML file.

## Four core roles, and specialists

Conjecture search needs four things: orientation, attack, independent check, and
convergence. Those are `scout`, `researcher`, `reviewer`, and `synthesizer`.

Proving, refuting, mining an existing proof, and building a construction are **assignment
lenses** for the `researcher`, not separate role contracts — they share a write surface, a
set of prohibitions, and a handoff. Certifying a dossier and auditing manuscript/ledger
agreement are likewise the two lenses of the `reviewer`. Each lens is one file in
[`../lenses/`](../lenses/README.md), named by the orchestrator in the assignment and
loaded on its own: a role that surveys several lenses at once produces a shallow pass on
all of them, and one that *reads* several pays for strategies it was not asked to run.

Three further roles are **capability packs**, activated by the work: `numerics` when there
is something to compute, `literature-scout` when there is something to import, `janitor`
when the repository needs tidying. They ship uninstalled, in [`../../packs/`](../../packs/),
because a role that is present is a role an orchestrator can reach for — and a fresh clone
that has computed nothing should not carry a numerics specialist, an unused Codex adapter
for it, and a validator walking both.

## Roster

| role | lenses | writes | cardinality |
|---|---|---|---|
| [`scout`](scout.md) | — | nothing | N, parallel |
| [`researcher`](researcher.md) | [`prove`](../lenses/prove.md), [`refute`](../lenses/refute.md), [`mine`](../lenses/mine.md), [`construct`](../lenses/construct.md) | one dossier; one new checkpoint | 1 per dossier; N across distinct lenses and targets |
| [`reviewer`](reviewer.md) | [`certify`](../lenses/certify.md), [`sync`](../lenses/sync.md) | one new review | 1 cold reviewer per dossier |
| [`synthesizer`](synthesizer.md) | — | `portfolio.yaml`, `research/instances.md`; one new checkpoint | **singleton** |

## Capability packs

Not installed by default. `python3 scripts/new.py role <pack>` copies one into
`.claude/agents/` and regenerates its Codex adapter; from that moment it is an ordinary
role in every respect, validated like the four above. Deleting the file uninstalls it, and
`python3 scripts/check.py --write-codex` removes the orphaned adapter.

| pack | install when | writes | cardinality |
|---|---|---|---|
| [`numerics`](../../packs/numerics/numerics.md) | there is something to compute | `experiments/numerics/`, generated runs, one new checkpoint | singleton for code; N for distinct stable runs |
| [`literature-scout`](../../packs/literature-scout/literature-scout.md) | there is something to import | one new checkpoint | N; bibliography remains single-writer |
| [`janitor`](../../packs/janitor/janitor.md) | the repository needs tidying | nothing; proposal only | 1 |

The roster above links each pack by path, so installing one needs no edit here. The
`numerics` *harness* under `experiments/` is a separate question and stays where it is:
its lane already validates only the run artifacts that exist, so an unused harness costs
nothing.

## Cross-client adapters are optional too

`.codex/` exists so Codex can read roles it cannot parse from Markdown. A repository
driven only by Claude Code may delete the whole tree and the roles lane will not complain;
`--write-codex` regenerates it in full if that changes. What is never allowed is an
adapter that disagrees with the Markdown it came from.

## Transitions

Use `scout` for unfamiliar, ambiguous, or broad assignments; it is not a mandatory tax
when the exact node and artifacts are already known.

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

Proving and refuting are the same path with the roles in a different order, and neither
skips the certification gate. A numerical result never skips it either: an exact
`numerics` witness is handed to a `researcher`, who states it as a refuter node and proves
it in a dossier; a `reviewer` certifies that dossier; and only then does the orchestrator
record it as `refuted_by` provenance. The full contract is in
[`../lenses/refute.md`](../lenses/refute.md).

## Where to fan out, where to converge

Fan out across read-only scouting, independent approaches in different families,
refutation lenses, and independent literature/mining questions. Do not fan out writes to a
shared file. `numerics` package edits, bibliography edits, instance curation, portfolio
curation, manuscript promotion, and ledger edits converge through the concurrency keys in
[`README.md`](README.md).

The `synthesizer` owns the search portfolio and the mathematical merge barriers declared
as program constraints in `CLAUDE.md`. The live frontier is derived with
`python3 scripts/check.py status` and the live search with
`python3 scripts/check.py portfolio`; no role maintains a second copy of either.

## Adding a program-specific role

Four core roles carry the search — orienting, attacking, checking, converging — and three
optional specialists carry computing, importing and tidying. None of the seven mentions
this repository's mathematics, which is why the roster is the same in every repository
built from this template.

Prefer a new **lens** to a new role. A lens costs one file in
[`../lenses/`](../lenses/README.md) and no permissions; a role costs a contract, a
generated adapter, a roster row, and a concurrency key. When a program genuinely wants its
own — a prober for a particular gate, a refiner for a particular family of statements —
write it as a new `.md` file here, add a row to the roster above, then:

```bash
python3 scripts/check.py --write-codex
python3 scripts/check.py --lane roles
```

Every role body must contain the literal string `.claude/agents/README.md`, because that
is the contract it executes under; the checker enforces it.

## Validation

```bash
python3 scripts/check.py --lane roles      # after changing a role, lens or adapter
python3 scripts/check.py --write-codex     # regenerate adapters, deliberately
```

Regenerate the Codex adapters in the same commit as the Markdown change, or the roles lane
reports a stale adapter.
