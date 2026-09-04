# Maintaining the roster

For whoever changes the roles, not for a role executing a task. The contract an agent
loads at run time is [`README.md`](README.md); this file is how that roster is built,
extended, tuned, and kept in sync across the two clients.

`../../CLAUDE.md` is normative and wins on any conflict.

## How a role is defined

Each role file in this directory is an ordinary Claude Code subagent definition, in
[Claude Code's published schema](https://code.claude.com/docs/en/sub-agents): front
matter carrying `name`, `description`, `tools`, `model`, `effort` and `color`, then the
body that is the role's contract. Nothing in the frontmatter is invented here, and
`scripts/check.py` derives the roster from the files on disk rather than from a list.

Two of those fields — `model` and `effort` — are **generated**, from
[`profiles.yaml`](profiles.yaml). The body below the frontmatter is canonical prose and
is never rewritten; the frontmatter block is stamped from the table.

Claude Code reads the Markdown files directly. Codex does not: project-scoped Codex
agents are standalone TOML files. `python3 scripts/new.py agents` regenerates
both — the frontmatter here and `../../.codex/agents/*.toml` from these canonical bodies
— and `python3 scripts/check.py --lane roles` rejects either one when it drifts. Do not
hand-edit a generated TOML file, and do not hand-edit `model` or `effort`.

## Model and effort live in one table

[`profiles.yaml`](profiles.yaml) is the only place in the repository that names a model
or an effort. It holds **tiers** (one resource level, resolved for each client), the
client-neutral role facts `read_only` and `color`, and **profiles** — a role → tier
assignment, one of which is `active`.

A tier is per client because the two clients reach a resource level differently: Claude
differentiates by model, Codex by effort on a single model. The effort scales are
validated separately, because Codex's has one rung above Claude's ceiling. An empty
client block means inherit from the parent session, which Claude spells `model: inherit`
and Codex spells by omitting the key; a tier inherits on both clients or on neither, so
that a tier name cannot mean two different things depending on who is running.

**A tier names a resource level; a profile names the occasion.** The shipped profiles are
`campaign` (the sustained attack), `survey` (a cheaper sweep, every role one rung down)
and `session` (pin nothing and follow the operator's own model and effort). The two
vocabularies are kept disjoint and the checker enforces it: a profile that takes a tier's
name makes every assignment line using that word a tautology, and leaves a reader unable
to tell which layer a bare word belongs to.

Generating both artifacts is what makes a profile mean the same thing on both clients.
Their native knobs do not agree: Claude resolves frontmatter *above*
`CLAUDE_CODE_SUBAGENT_MODEL`, while Codex resolves its `[agents]` defaults *above* the
agent file. Leaning on those would make one switch override the roles and the other be
overridden by them. It is also why nothing in this repository sets them.

To retune, there are three moves and no fourth:

```bash
# redefine a tier -- every role at that tier moves, on both clients at once
# add a tier      -- then assign it to one role in a profile
# switch active:  -- the whole roster shifts to another profile's assignment
$EDITOR .claude/agents/profiles.yaml
python3 scripts/new.py agents
python3 scripts/check.py --lane roles
```

A variant is a named tier, never a scattered per-role override, so that a checkpoint can
cite the configuration it was produced under. Switching `active:` is a diff, which is the
point: the profile a result was produced under stays in the history. For a throwaway
probe that should leave no trace, Claude Code's `--agents <json>` flag overrides these
files for one session without touching them.

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
`.claude/agents/`, restamps it from the active profile, and regenerates its Codex
adapter; from that moment it is an ordinary role in every respect, validated like the
four above. Every profile already assigns the packs a tier, which is why installing one
is still a single command. Deleting the file uninstalls it, and
`python3 scripts/new.py agents` removes the orphaned adapter.

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
`python3 scripts/new.py agents` regenerates it in full if that changes. What is never allowed is an
adapter that disagrees with the Markdown it came from.

`read_only` has different enforcement strength on the two clients. Codex receives a real
`sandbox_mode = "read-only"`. Claude receives no cross-client sandbox equivalent: the checker
rejects explicit `Edit` and `Write` tools, while `Bash` remains available under the role's
read-only command contract. The table records the intended boundary without pretending that
prose and a runtime sandbox are the same control.

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
write it as a new `.md` file here, give it a `roles:` entry and a tier in every profile
in [`profiles.yaml`](profiles.yaml), add a row to the roster above, then:

```bash
python3 scripts/new.py agents
python3 scripts/check.py --lane roles
```

The profile entry is not optional and there is no implicit default tier: a role whose
model and effort nobody chose is a role nobody costed.

Every role body must contain the literal string `.claude/agents/README.md`, because that
is the contract it executes under; the checker enforces it.

## Validation

```bash
python3 scripts/check.py --lane roles       # after changing a role, lens, or profile
python3 scripts/new.py agents               # restamp both clients, deliberately
```

Regenerate in the same commit as the change, or the roles lane reports a stale artifact.
The former `check.py --write-agents` and `--write-codex` flags now stop with the migration
command rather than writing from the validator.
