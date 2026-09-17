---
title: "Conjecture search harness: technical specification"
short_title: Specification
exports:
  - format: pdf+tex
    template: ../templates/latex
    output: _build/exports/specification.pdf
---

```{raw} latex
\tableofcontents
```

:::{note} Descriptive, not normative
This document describes the harness in one place for a human reader. It governs nothing.
Every rule it restates has exactly one owning file, named at the end of the section that
restates it, and **the owning file wins on any conflict**. The contract is
[`CLAUDE.md`](../CLAUDE.md).

It was written against commit `a68aa39` (the `Unreleased` section of
[`CHANGELOG.md`](../CHANGELOG.md), after `v0.1.0`). A disagreement between this document
and an owning file is a defect in this document unless shown otherwise.
:::

(spec-about)=
# About this document

## Why it exists

The harness keeps each rule in exactly one file, the file that owns the artifact the rule
is about: ledger fields in the ledger schema, checkpoint fields in the checkpoint README,
role permissions in the role files, and so on. That arrangement serves agents well, because
a role loads only the file for the task in front of it. It serves a human badly, because
nothing tells the whole story in order: about fifty Markdown files, roughly 25,000 words,
and a checker of about 9,000 lines of Python.

This document is that story, told once, with excerpts from the real files. It adds no
rules.

## How to read it

For a first reading of about twenty minutes, read [](#spec-system), [](#spec-vocabulary)
and [](#spec-example). For everything else, each section is self-contained and can be read
when you need it.

Not every file in the repository is written for you. The table below says which are.

| file or directory | written for, and when to read it |
|---|---|
| `README.md` | humans: first contact, instantiation |
| `CLAUDE.md` (`AGENTS.md` is a symlink) | agents and humans: in doubt about a rule |
| `docs/RUNNING-A-SEARCH.md` | humans: running a search |
| `docs/SPECIFICATION.md` (this file) | humans: understanding the whole |
| `example/` | humans: seeing a finished search |
| the two `research/program/*-schema.md` | both: editing the ledger or portfolio |
| `research/*/README.md`, `solutions/README.md` | both: writing that kind of record |
| `experiments/README.md` | both: numerical work |
| `.claude/agents/`, `.claude/lenses/` | agents: role and lens contracts |
| `.claude/agents/MAINTAINING.md` | maintainers: tuning the roster |
| `packs/` | agents: optional roles, uninstalled |
| `templates/` | nobody directly: used by `scripts/new.py` |
| `.codex/` | generated: never edit by hand |

(spec-system)=
# The system in one page

## Purpose and scope

The harness supports **sustained conjecture search**: proving or refuting one hard
statement, over many sessions and several agents at once, without losing what the search
has learned.

It is deliberately not a general research harness. Theory building, classification,
algorithm design, exposition, and computer-assisted proof with first-class certificates are
out of scope. The contract asks that such work be declared out of scope rather than forced
into this machinery.

## Three domains

Everything in the repository belongs to one of three domains.

| domain | question it answers | source of truth |
|---|---|---|
| mathematical state | what is claimed? | `modules/`, `ledger.yaml`, `solutions/` |
| search state | what is the search doing? | `brief.md`, `portfolio.yaml` |
| durable evidence | why did either change? | `research/explorations/`, `reviews/`, `runs/` |

The contract states the separation as one rule:

> Ledger = what is mathematically claimed. Portfolio = what the search is doing.
> Checkpoints = why the portfolio changed.

## Two couplings the checker enforces

**The anchor invariant.** Every labelled claim directive in `modules/` (`prf:theorem`,
`prf:conjecture`, and six other kinds) is exactly one ledger node, whose `kind` is the
directive's name. A label on a heading, an equation or a remark is structural and is not a
node. A statement therefore cannot drift from its recorded status without the checker
failing.

**One statement, one home.** A statement that is not yet stable enough to be a node is a
*candidate*. It lives in the front matter of the checkpoint that proposed it, and nowhere
else, until a later checkpoint retires it or promotes it to a node.

## The life of a statement

```text
  idea, computation, or literature lead
        |
        v
  CANDIDATE   cand:<slug> in a checkpoint's front matter
        |     no label, no status, no certification
        |
        +---- retired by a later checkpoint ----> dead (the record stays)
        |
        | promoted, as one act: label + node + `promotes:` + blockers moved
        v
  LEDGER NODE  prf:<kind> with :label: <id> in modules/, node in ledger.yaml
        |      status: open   (a definition is status: defined)
        |
        | dossier in solutions/  +  independent review in research/reviews/
        v
  status: proved     proofs: [{artifact, mode, review or accepted_by}]

  A proved REFUTER node, named in refuted_by  ==>  target status: refuted
```

## Who does what

```text
                        human operator
                              |
                 ORCHESTRATOR = the main agent session
        writes: ledger.yaml, brief.md, modules/, references.bib
        applies the deltas other roles propose; runs the checker
          |              |               |                 |
        scout        researcher       reviewer        synthesizer
       (reads)     (dossiers and     (reviews)     (portfolio, instances,
                    checkpoints)                    synthesis checkpoints)

   optional packs, once installed: numerics, literature-scout, janitor
```

No spawned role writes the ledger. Only the `synthesizer` writes the portfolio. An author
never certifies their own proof.

(spec-vocabulary)=
# Vocabulary

Most of the confusion a newcomer meets is vocabulary: the harness uses ordinary words in
narrow senses, and it keeps some near-synonyms apart on purpose.

## Organization

Domain
: One of the three things the repository is organized into: mathematical state, search
  state, durable evidence.

Gate
: An optional layer that the work activates by creating its files: claim graph, problem
  brief, search portfolio, checkpoint memory, certification. A gate whose files are absent
  has no rules. See [](#spec-activation).

Capability pack
: An optional role, shipped uninstalled in `packs/`. There are three, `numerics`,
  `literature-scout` and `janitor`, and installing one is a single command.

Lane
: A partition of the checker, selected with `check.py --lane`: `core`, `proofs`,
  `checkpoints`, `portfolio`, `numerics`, `roles`, `docs`. Lanes, gates and
  domains do not line up with each other, deliberately.

Public inbox
: The GitHub issue forms under `.github/ISSUE_TEMPLATE/`. Anything arriving there changes
  nothing until it is triaged into a repository artifact by the role that owns it.

## Mathematical state

Manuscript
: The MyST Markdown files under `modules/`. The only place a node's statement is written.

Claim directive
: A MyST `prf:<kind>` block carrying a `:label:`. The eight kinds are `theorem`, `lemma`,
  `proposition`, `corollary`, `conjecture`, `definition`, `example`, `assumption`.

Ledger
: `research/program/ledger.yaml`, the claim graph: one entry (a *node*) per claim, with its
  status, provenance and relations. Exactly one per repository.

Node id
: A stable id such as `conj:main` or `lem:key`. It **is** the manuscript label.

Status
: `open`, `proved`, `refuted`, or `defined` (definitions only). A status records what has
  been established, never what is expected.

Provenance
: `internal` (proved here, needs a dossier) or `literature` (imported, needs an import
  class and BibTeX keys). Independent of status.

Summary
: A node's one-line gloss for the derived views. Not canonical: the manuscript is.

Fence
: A node other nodes cite as a limit on what can be true or provable. A *hard* fence is a
  proved node cited in `bounded_by`; an *advisory* barrier is an open node cited in
  `heuristic_barriers`. Being a fence is a role carried by those edges, not a kind.

Applicability-blocked
: A proved implication whose antecedent (in `assumes`) is still unresolved. It stays
  `proved`; it just cannot be applied yet.

Convention node
: A fixed normalization (a sign, a scaling, a log base) stated as a `prf:definition` with a
  `kind: definition`, `status: defined` node, which dependent claims list in `depends_on`.

## Certification

Dossier
: A standalone MyST proof file `solutions/<id>.md`, readable and buildable on its own.

Proof record
: An entry in a node's `proofs:` list naming a dossier and how it was certified.

Certification mode
: `agent` (an independent agent passed a persisted proof review) or `human` (a named
  person accepts the argument). There is no third mode.

Proof review
: A report `research/reviews/<date>-<slug>.md` with `type: proof-review` and
  `verdict: pass`. The only kind of report that can certify.

Audit
: A report with `type: audit`: diagnostic, partial or failed review. Certifies nothing.

Refuter
: An ordinary proved node whose statement negates a target. The target names it in
  `refuted_by`.

## Search state

Problem brief
: `research/program/brief.md`: the target node, its exact negation, what counts as done,
  edge cases, traps and budget policy.

Target
: The ledger node a search is aimed at. Named by the brief and the portfolio.

Portfolio
: `research/program/portfolio.yaml`: approach families and routes, their states and
  blockers. Written only by the `synthesizer`.

Family
: `fam:<slug>`: a mechanism of attack. State `active`, `saturated` or `parked`.

Approach, route
: `ap:<slug>`: one concrete attempt inside a family, with a one-sentence `objective`.
  State `queued`, `active`, `blocked`, `completed` or `duplicate`.

Blocker
: The exact `cand:` id or node id a blocked route is waiting on. Never restated prose.

Saturation
: A synthesizer's judgment that a family's mechanism is worked out. It costs a closure
  checkpoint and a reopening condition. `parked` means only that nobody is working it.

## Durable evidence

Checkpoint
: A dated, append-only record `research/explorations/YYYY-MM-DD-<slug>.md` of a durable
  search event, with validated front matter. (The directory keeps its historical name.)

Outcome
: What a checkpoint produced: `dead-end`, `directional`, `candidate`, `proposed`.

Candidate
: `cand:<slug>` with a canonical `statement:` in a checkpoint's `candidates:` list. Live
  until a later checkpoint names it in `retires:` or `promotes:`.

Promotion
: The single act that turns a candidate into a node. See [](#spec-candidates).

Supersession
: A later record naming an earlier one in `supersedes:`, meaning *read me instead*. Nothing
  is deleted. The records nothing supersedes are the *heads*.

Run artifact
: A provenance-stamped JSONL file under `research/runs/`, the only admissible form of
  numerical work.

Instance battery
: `research/instances.md`, the shared registry of calibration and stress instances,
  curated by the `synthesizer`.

## Agents

Orchestrator
: The main session. Not a spawnable role. Owns every single-writer file except the
  portfolio.

Role
: A spawnable agent definition in `.claude/agents/<name>.md`: `scout`, `researcher`,
  `reviewer`, `synthesizer`, plus installed packs.

Lens
: One strategy a role is pointed at, in `.claude/lenses/<name>.md`: `prove`, `refute`,
  `mine`, `construct` (researcher); `certify`, `sync` (reviewer). An assignment names one.

Handoff envelope
: The YAML block every role ends its report with: `outcome`, `artifacts`,
  `proposed_deltas`, `portfolio_delta`, `next_role`, `next_prompt`.

Concurrency key
: A named write lock (`ledger`, `portfolio`, `solution:<dossier>`, ...). Parallel work is
  allowed only on distinct keys.

Profile, tier
: In `.claude/agents/profiles.yaml`, a *tier* is a resource level (model and effort per
  client) and a *profile* assigns a tier to every role. One profile is `active`.

Adapter
: A generated `.codex/agents/<role>.toml` file that lets Codex run the same role.

(spec-map)=
# Repository map

```text
.
|-- CLAUDE.md                the contract (AGENTS.md is a symlink to it)
|-- README.md                overview and the six instantiation steps
|-- CHANGELOG.md             template releases; Unreleased section
|-- myst.yml, index.md       the manuscript's MyST project (site + PDF)
|-- references.bib           the single bibliography            [orchestrator]
|-- modules/                 the manuscript: prf: statements     [orchestrator]
|   `-- 00-overview.md       abstract and orientation
|-- solutions/               proof dossiers, one per node        [researcher]
|-- research/
|   |-- README.md            map of sources of truth
|   |-- instances.md         shared instance battery             [synthesizer]
|   |-- program/
|   |   |-- ledger.yaml      the claim graph (ships empty)       [orchestrator]
|   |   |-- ledger-schema.md field contract for the ledger
|   |   |-- brief.md         GATED: absent until a search starts [orchestrator]
|   |   |-- portfolio.yaml   GATED: absent until coordination    [synthesizer]
|   |   `-- portfolio-schema.md  field contract, brief + portfolio
|   |-- explorations/        checkpoints, append-only            [roles]
|   |-- reviews/             proof reviews and audits            [reviewer]
|   `-- runs/                numerical run artifacts             [numerics]
|-- experiments/             the numerics harness (uv project)   [numerics]
|   `-- numerics/            contract.py, artifact.py, targets/
|-- scripts/
|   |-- check.py             validator and derived views (writes nothing)
|   |-- checks/              one module per lane
|   |-- new.py               scaffolder (never writes the ledger)
|   |-- check.sh             every check in order, incl. PDF builds
|   `-- tests/               the checker's unittest suite
|-- templates/               scaffolds new.py copies; latex/ export template
|-- example/                 a complete worked search; a fixture, not history
|-- docs/                    RUNNING-A-SEARCH.md, this specification
|-- .claude/
|   |-- agents/              role contracts, profiles.yaml, MAINTAINING.md
|   `-- lenses/              one file per assignment strategy
|-- packs/                   uninstalled optional roles
|-- .codex/                  generated Codex adapters (optional)
|-- .github/                 CI workflows and the issue-form inbox
|-- package.json, patches/   pinned, patched MyST (npm ci)
`-- pyproject.toml           PyYAML, the checker's one Python dependency
```

Brackets name the single writer, where there is one. Three directories are written by
nobody by hand: `_build/` (MyST output, gitignored), `.codex/agents/` (generated), and
`research/runs/` (emitted by the numerics tool, never edited).

Owning files:

- [`README.md`](../README.md)
- [`research/README.md`](../research/README.md)
- [`templates/README.md`](../templates/README.md)

(spec-activation)=
# Activation: gates, packs and lanes

## No mode flag

Nothing in the repository switches the harness into a mode. Each optional layer is
activated by the work creating its files, and the checker validates only what exists. A
fresh clone therefore passes `python3 scripts/check.py` while
`python3 scripts/check.py ready` correctly reports it as not yet instantiated. An afternoon
of speculative work may cross no gate and leave no artifact; that is a correct outcome.

## The five gates

| gate | activate when | durable state | lane |
|---|---|---|---|
| claim graph | a statement is precise, stable, reusable | manuscript label + node | `core` |
| problem brief | a sustained search starts | `brief.md` | `portfolio` |
| search portfolio | several routes, agents or sessions | `portfolio.yaml` | `portfolio` |
| checkpoint memory | a result will affect future search | dated checkpoints | `checkpoints` |
| certification | a proof or refutation is claimed | dossier + review | `proofs` |

Two orderings are fixed; the rest are independent.

1. **The claim graph comes first.** A brief and a portfolio both name a target, and the
   target must resolve to a ledger node.
2. **A portfolio requires a brief.** Several coordinated routes *are* a sustained search,
   and a sustained search opens with a statement of what would finish it. A brief does not
   require a portfolio.

## Packs and the inbox

Numerics, literature import and repository hygiene are *capabilities*, each driven by a
role that ships uninstalled in `packs/`. The public inbox (the issue forms) is neither a
gate nor a pack: it owns no state and is nobody's job, and nothing in the checker mentions
it.

## Three questions, three commands

`check`
: Is the structure valid? Required to be green after every ledger edit. A fresh clone
  passes.

`ready`
: Can a search start here? Needs a named program, at least one node, and a written brief.
  A fresh clone fails, correctly.

`publish-ready`
: Is the manuscript fit to show? Needs a title, subtitle, author, abstract, and the
  instantiation section of `README.md` deleted. Blocks no mathematics.

Owning file: [`CLAUDE.md`](../CLAUDE.md), sections *The gates* and *Verify*.

(spec-math)=
# Mathematical state

## The manuscript

The manuscript is a MyST Markdown project configured by the root `myst.yml`. Its table of
contents is `index.md` plus every `modules/*.md` and `solutions/*.md` (except READMEs), so
a new module needs no registration. Mathematics is LaTeX inside `$...$`; macros live under
`math:` in `myst.yml`, with the template's core macros kept apart from program macros so
the file stays diffable against the template. The bibliography is `references.bib`.

A claim is a directive whose name is its kind and whose label is its node id:

```markdown
:::{prf:conjecture}
:label: conj:example
For all real $a_1,\dots,a_n$ with $n \ge 2$,
$\sum_{i=1}^n (a_i - \bar a)^2 \ge \tfrac{1}{2}\sum_{i=1}^n a_i^2$.
:::
```

Cross-references are written `[](#<label>)`. A heading label is written `(sec:x)=` on the
line before the heading, and like equation, figure, table and `prf:remark` labels it is
structural. The abstract is a `+++ {"part": "abstract"}` block at the top of
`modules/00-overview.md`.

The checker does not parse Markdown itself. It runs `myst build --site`, reads the syntax
tree MyST writes under `_build/site/content/`, and treats as a claim exactly what MyST says
is a `proof` node of a ledger kind carrying a label. Any error MyST reports, any unknown
directive or role (`prf:question` is not a kind), any unresolved cross-reference, any
duplicate label, and any two labels that collapse to the same HTML anchor (`a:b-c` and
`a-b:c` both become `#a-b-c`) is an error.

## The ledger document

```yaml
meta:
  program: example
  scope: >-
    Finite real sequences and the elementary identities they satisfy.

nodes:
  - id: prop:example
    kind: proposition
    status: proved
    provenance: internal
    file: modules/00-overview.md
    summary: "For real a_1..a_n with mean abar, sum_i (a_i - abar)^2 = ..."
    proofs:
      - artifact: solutions/prop-example.md
        mode: agent
        review: research/reviews/2026-09-01-prop-example-proof-review.md

  - id: conj:example
    kind: conjecture
    status: refuted
    provenance: internal
    file: modules/00-overview.md
    summary: "Every finite real sequence with n >= 2 has centred sum ..."
    refuted_by: [prop:example-refuter]
```

*Abridged from `example/research/program/ledger.yaml`.*

The top level holds only `meta` and `nodes`. `meta.program` names the program and prefixes
checker output; `meta.scope` says in one sentence what the nodes range over. Which agent or
route owns a node is not recorded here: that is search state.

## Node fields

`id` (required)
: Unique, non-empty. It is the manuscript label. There is no `label:` override.

`kind` (required)
: One of the eight kinds, and equal to the directive the label sits on. An open question is
  a `conjecture` written in the direction the search tries to establish, so that it has an
  exact negation.

`status` (required)
: `open`, `proved`, `refuted`, `defined`. `defined` if and only if `kind: definition`.

`provenance` (required)
: `internal` or `literature`.

`file` (required)
: The `.md` file under `modules/` that holds the label. Must exist and must be the right
  file.

`summary` (required)
: Non-empty one-line gloss. The `reviewer`'s `sync` lens treats disagreement with the
  manuscript as a defect in the summary.

`import_class`, `references` (literature only)
: `import_class` is `published`, `preprint-reviewed` or `preprint-unreviewed`;
  `references` is a non-empty list of keys present in `references.bib`. An unreviewed
  preprint cannot be `proved`. Neither field is allowed on an internal node.

`proofs` (proved only)
: One or more proof records. See [](#spec-certification).

## Relations

All relations are lists of node ids in the same ledger, and each must resolve.

`depends_on`
: Claims actually used in a proof of this node. This is the proof graph: it must be
  acyclic, and a proved node may not depend, even transitively, on an `open` or `refuted`
  node.

`assumes`
: Antecedents of an implication. A theorem "$A \Rightarrow B$" stays `proved` while $A$ is
  open; `check.py status` lists it as applicability-blocked.

`implies`
: Conclusions a proved implication advertises. Only allowed on a `proved` node.

`refines`
: Statements this node sharpens.

`bounded_by`
: Hard fences. Every entry must be a `proved` node. A statement violating one is wrong by
  construction.

`heuristic_barriers`
: Advisory barriers. Every entry must be an `open` node. They guide work; they fence
  nothing logically.

`refuted_by`
: Required on, and only allowed on, a `refuted` node. Every entry must be `proved`. A
  refuter never appears in the target's `depends_on`: that field records facts a proof
  used, and a refuted statement has no proof.

## What does not belong in the ledger

Attempt history, numerical output, route states, blockers, saturation, and roadmap links.
They belong in checkpoints, run artifacts and the portfolio. Numerical evidence never
changes a status.

Owning files:

- [`research/program/ledger-schema.md`](../research/program/ledger-schema.md)
- [`research/program/README.md`](../research/program/README.md)
- checker `scripts/checks/ledger.py` and `scripts/checks/manuscript.py`

(spec-certification)=
# Certification: dossiers, proof records and reviews

## Dossiers

A dossier is `solutions/<id>.md`, with the colon of the node id replaced by a hyphen. It is
a page of the manuscript's MyST project, so its cross-references into `modules/` resolve on
the site, and its own `exports` entry builds it as a standalone PDF, where those
cross-references print as `??` (expected).

```yaml
---
title: "Refutation: the centred sum of squares can vanish"
ledger-node: prop:example-refuter
refines: [prop:example-refuter]
bounded_by: []
author: /root/template_author
date: "2026-09-03"
exports:
  - format: pdf+tex
    template: ../templates/latex
---
```

*From `example/solutions/prop-example-refuter.md`; the example's own template path is one
level deeper.*

The header vocabulary is closed: `ledger-node`, `refines`, `bounded_by`, `author`, `date`,
plus the MyST page fields `title`, `subtitle`, `short_title`, `label`, `exports`,
`numbering`. Only `ledger-node` (an id or a list of ids) is checked semantically: it must
name the node whose proof record points at the file. The header never carries
certification; `checked_by`, `reviewer` and `review` are rejected by name.

The body states the refined theorem in a `prf:theorem`, proves it in a `prf:proof`, and
ends with one line per `bounded_by` fence explaining why the statement respects it. A step
the author could not close is flagged in a `prf:remark`. No numerical output may appear in
a dossier, not even as motivation for a step.

**A dossier that no proof record names is a draft, and that absence is the whole signal.**

## Proof records

```yaml
proofs:
  - artifact: solutions/thm-example.md
    mode: agent
    review: research/reviews/2026-09-02-example-proof-review.md
  - artifact: solutions/thm-example-second-proof.md
    mode: human
    accepted_by: <human identity>
```

| mode | requires | forbids | meaning |
|---|---|---|---|
| `agent` | `review:` | `accepted_by:` | a distinct agent passed a persisted proof review |
| `human` | `accepted_by:` | `review:` | a named person accepts the argument |

An internally proved node needs at least one record; `proofs` is allowed only on `proved`
nodes; the same artifact may not appear twice. Several records let alternative proofs
coexist, and a dossier may cite already-certified `depends_on` nodes instead of reproving
them. A literature node carries no proof record: its import class and references are its
provenance.

## Review reports

Reports live in `research/reviews/`, are append-only, and have one of two types.

```yaml
---
type: proof-review
date: "2026-09-03"
verdict: pass
authors:
  - /root/template_author
reviewer: /root/template_reviewer
nodes:
  - prop:example-refuter
solutions:
  - solutions/prop-example-refuter.md
---
```

`type: proof-review`
: Fields `type`, `date`, `verdict`, `authors`, `reviewer`, `nodes`, `solutions`, and
  optionally `follows_up` (an earlier report in `research/reviews/`). `verdict` is exactly
  `pass`. `authors`, `nodes`, `solutions` are non-empty lists without duplicates, and
  `reviewer` is distinct from every author.

`type: audit`
: Fields `type`, `date`, and optionally `supersedes`. Partial, held or failed reviews are
  audits, as are editorial, literature and control-plane reviews. The word "pass" inside an
  audit has no proof value.

In both, `date` is a quoted `YYYY-MM-DD` or UTC `YYYY-MM-DDTHH:MM:SSZ` whose date matches
the filename prefix.

A report's front matter is its immutable *historical scope*. Every node currently certified
through it must be listed in `nodes`, and its dossier in `solutions`; the report may list
more than is currently active, and an old passing report may stay in the archive after a
downgrade. A repaired proof gets a new report, pointing back with `follows_up`; an earlier
verdict is never rewritten. An audit that replaces an earlier audit *of the same subject*
names it in `supersedes`; audits on different subjects do not supersede each other.

The body is free-form, preferably **Findings**, **Corrections**, **Exclusions**.

## Refutation takes the same channel

1. The witness, or divergent family, is recorded as a **candidate** in a checkpoint.
2. The statement it establishes is promoted to a **refuter node** with its own manuscript
   statement; the promoting checkpoint ends the candidate.
3. The refuter gets an ordinary **dossier**.
4. That dossier is **independently certified** like any other, with one extra question:
   does the refuter negate the target's exact quantified statement? One witness refutes a
   universal claim; a uniform or dimension-free constant generally needs a certified family
   along which the relevant quantity diverges.
5. Only then does the orchestrator set the target to `status: refuted` with the refuter in
   `refuted_by`.

A run artifact is never a step in this chain.

## Definition of done for a proof

1. `solutions/<id>.md` exists, builds standalone, header complete.
2. Its theorem matches the manuscript statements it refines and respects every
   `bounded_by` fence.
3. The node has a complete proof record, and `python3 scripts/check.py` reports 0 errors.
4. The record is `mode: agent` with an independent persisted review, or `mode: human` with
   a named acceptance.

Owning files:

- [`solutions/README.md`](../solutions/README.md)
- [`research/reviews/README.md`](../research/reviews/README.md)
- [`research/program/ledger-schema.md`](../research/program/ledger-schema.md)
- checker `scripts/checks/proofs.py`

(spec-search)=
# Search state

## The problem brief

```yaml
---
type: brief
target: conj:main
---
```

The front matter holds exactly `type: brief` and `target`. The target must be a ledger
node, must not be a `definition` (fixed by decision, not resolved by work), must not be a
fence cited by some other node, and must equal the portfolio's target when both exist. The
brief is written by the orchestrator (`brief` concurrency key).

The body is prose, in the sections the scaffold `templates/brief.md` ships:

1. **The target**: the node, and optionally its manuscript statement quoted verbatim as a
   marked copy. The copy is never sharpened in place; the `sync` lens checks it still agrees.
2. **The exact negation**, quantifier order intact, and which shape a refutation must take.
3. **What counts as complete**: a complete proof (and the weakenings that do not count) and
   a complete refutation.
4. **Edge cases and audit tests**: the few problem-specific things that actually go wrong.
5. **Traps and circular reductions**: routes that land on a lemma of equivalent strength.
6. **Initial families and their reopening criteria**: the reasoning behind the first
   portfolio, not a copy of it.
7. **Budget policy**: an honest unresolved outcome is permitted; stop on saturation, not on
   a clock.

`check.py ready` fails while three instructional sentences from the scaffold are still in
the file, which is how a copied-but-unwritten brief is caught.

## The portfolio document

```yaml
target: conj:example

families:
  - id: fam:example-numerical
    mechanism: >-
      Use the available numerical diagnostics to probe the target ...
    state: saturated
    closure_checkpoint: research/explorations/2026-09-03-example-refuter.md
    reopen_if: >-
      The target is restated with a constant allowed to depend on n ...

approaches:
  - id: ap:example-roundoff-bound
    family: fam:example-numerical
    objective: >-
      Bound the floating-point discrepancy the battery measured ...
    parent: ap:example-finite-battery
    state: blocked
    blocker: cand:example-identity-stability
    reopen_if: >-
      cand:example-identity-stability is proved, or any explicit error bound.
    checkpoints:
      - research/explorations/2026-09-03-example-roundoff.md

  - id: ap:example-exhaustive-search
    family: fam:example-numerical
    objective: >-
      Widen the integer-vector enumeration already performed ...
    state: duplicate
    related:
      - to: ap:example-finite-battery
        relation: duplicates
    checkpoints:
      - research/explorations/2026-09-03-example-dedup.md
```

*Abridged from `example/research/program/portfolio.yaml`.*

The top level holds `target` (required), `families` and `approaches`. Nothing in the
portfolio is a mathematical claim: a route has no truth value, and the portfolio never
restates a statement. It names an id and stops.

## Families

| field | rule |
|---|---|
| `id` | `fam:<slug>`, unique |
| `mechanism` | required: what the family tries |
| `state` | `active`, `saturated`, `parked` |
| `closure_checkpoint` | required if closed, forbidden if `active` |
| `reopen_if` | required if closed, forbidden if `active` |

`saturated` claims the mechanism is worked out; `parked` claims only that nobody is working
it. A closed family may hold no `active` or `queued` route. Closing one is a synthesizer
judgment and is never inferred from attempt counts or elapsed time.

## Approaches

| field | rule |
|---|---|
| `id` | `ap:<slug>`, unique |
| `family` | required, must resolve |
| `objective` | required: one sentence, an intention, never a claim |
| `parent` | optional; same family; no cycles |
| `state` | `queued`, `active`, `blocked`, `completed`, `duplicate` |
| `blocker` | required if `blocked`, forbidden otherwise |
| `reopen_if` | required if `blocked`, forbidden otherwise |
| `related` | `{to, relation}`, relation `overlaps`, `duplicates`, `refines` |
| `checkpoints` | required if `blocked`, `completed` or `duplicate` |

| state | meaning |
|---|---|
| `queued` | planned live work nobody has started |
| `active` | being worked now |
| `blocked` | stopped on a named candidate or node, with a reopening condition |
| `completed` | this route's objective is finished; says nothing about the target |
| `duplicate` | same idea as another route, named by a `duplicates` relation |

Further rules:

- A `blocker` must be a ledger node or a **live** candidate. If it names a candidate that
  has since been promoted, the checker reports the node to point at instead.
- Two approaches joined by `duplicates` may not both be `active`.
- A route that leaves its parent's family is not a child: it is a new route with a
  `refines` relation.
- Once the target is `proved` or `refuted`, no route may remain `active` or `queued`.

## Every state change owes its checkpoint

Every path in `checkpoints:` and every `closure_checkpoint` must resolve to a record that
parses as a checkpoint, not merely to a file. That record must declare `approach:` naming
the route that lists it, or, for a closure checkpoint, a route in the closing family.

The reverse link is deliberately not required: a checkpoint naming `approach: ap:x` need
not yet appear in `ap:x`'s list. A researcher writes the checkpoint and only the
synthesizer writes the portfolio, so requiring both directions would make a red checker the
normal state between those two steps.

Owning files:

- [`research/program/portfolio-schema.md`](../research/program/portfolio-schema.md)
- [`templates/brief.md`](../templates/brief.md)
- checker `scripts/checks/portfolio.py`

(spec-evidence)=
# Durable evidence

## Checkpoints

One Markdown file under `research/explorations/` per **durable search event**, not per
attempt, named `YYYY-MM-DD-<slug>.md`. A file written by an agent role adds the role, the
scope and a run id to the name. The directory is append-only: a record is never rewritten or deleted.

A checkpoint is required when the work:

1. creates or retires a candidate statement;
2. identifies a reusable dead end or an exact blocker;
3. blocks, reopens, duplicates or saturates a portfolio approach;
4. produces a numerical or literature artifact future work may use;
5. proposes a manuscript or ledger change; or
6. synthesizes a batch of parallel work.

A speculative calculation that dies in ten minutes needs no file. A dead end needs one when
it is plausible or expensive enough that someone would repeat it.

```yaml
---
type: exploration
date: "2026-09-02"
approach: ap:example-finite-battery
nodes:
  - conj:example
  - prop:example
outcome: candidate
artifacts:
  - research/runs/2026-09-02T092336.680787Z-example.jsonl
candidates:
  - id: cand:example-identity-stability
    statement: >-
      Evaluated in floating point on a vector of $n$ entries, the two sides
      of the identity differ by at most $C n \varepsilon \sum_i a_i^2$.
---
```

*Abridged from `example/research/explorations/2026-09-02-example-exploration.md`.*

The envelope records what the work *engaged*, never what it concluded.

`type`, `date`, `outcome` (required)
: `type` is always `exploration`. `date` is a quoted ISO date or UTC timestamp matching the
  filename prefix. `outcome` is one of the four below.

`nodes`, `approach`, `candidates` (at least one)
: Node ids, which must resolve; the route `ap:<slug>`, which requires a portfolio and must
  resolve in it; candidate statements proposed here.

`artifacts`
: Paths under `research/runs/`, which must exist.

`retires`, `promotes`
: Candidates an earlier checkpoint proposed that this one kills, or turns into nodes.

`supersedes`
: Strictly earlier checkpoints this one replaces as the current reading.

| outcome | meaning |
|---|---|
| `dead-end` | the approach failed; say why |
| `directional` | evidence gathered, nothing closed |
| `candidate` | one or more candidate statements; requires `candidates:` |
| `proposed` | a concrete ledger or manuscript delta for the orchestrator |

Work that both failed and produced a candidate is `candidate`: the outcome names what the
next agent can pick up. `outcome: candidate` and a non-empty `candidates:` list require
each other.

The body is prose: what was tried, how (with the run artifact), the outcome, and why it
failed or what it unlocked, including the exact lemma that would unblock a blocked route.

## Order within a day

A filename is not a clock. Records on different days are ordered by date. Records on the
same day are ordered only if both carry a UTC timestamp; otherwise they are *unordered*, a
same-day proposal and promotion is accepted, and supersession is instead checked to be
acyclic. `python3 scripts/new.py checkpoint <slug> --timestamp` stamps a time.

## Supersession and heads

`supersedes:` says a later record should be read instead of an earlier one. It changes which
record to read first, and nothing else. `python3 scripts/check.py checkpoints` prints the
current heads, the superseded records and what replaced each. It is distinct from
`retires:`, which kills a *statement*.

(spec-candidates)=
## Candidates and promotion

```yaml
candidates:
  - id: cand:example-identity-stability
    statement: >-
      A precise statement someone could later prove or refute.
```

A candidate has only `id` (`cand:<slug>`, unique across the whole log, never equal to a
node id) and `statement`. Its statement is canonical: nothing else holds that text. It has
no manuscript anchor, no status, no certification. `python3 scripts/check.py candidates`
lists the live ones.

A candidate leaves the live list in exactly two ways, each by a *later* checkpoint:

- **Retirement.** `retires: [cand:x]`: the statement died.
- **Promotion.** One act of four parts:
  1. the statement gets a `prf:<kind>` directive with a `:label:` in `modules/`;
  2. it gets a ledger node with that id (and, if proved internally, a certified dossier);
  3. a checkpoint records the pair, which is what ends the candidate:

     ```yaml
     promotes:
       - candidate: cand:example-constant-witness
         node: prop:example-refuter
     ```
  4. every portfolio route blocked on the candidate is repointed at the node.

The checker verifies parts 3 and 4: the node must exist, the candidate must have been
proposed earlier and not already retired or promoted, and a blocker still naming a promoted
candidate is an error. The node id need not resemble the candidate id, which is why the pair
is recorded rather than inferred.

## The instance battery

`research/instances.md` holds two tables, *calibration instances* (known closed-form
answers, to check an implementation) and *stress instances* (extremal, degenerate or
adversarial). It is human-reviewed reference, not executable configuration. Anyone may
propose an instance; only the `synthesizer` adds one, because an instance chosen by the
agent whose claim it tests will be one the claim survives. Passing any finite battery
changes no status.

Owning files:

- [`research/explorations/README.md`](../research/explorations/README.md)
- [`research/instances.md`](../research/instances.md)
- checker `scripts/checks/checkpoints.py`

(spec-numerics)=
# Numerics

## Boundary

Numerical work guides the search and certifies nothing. It never changes a status, never
justifies a proof step, never appears in a dossier. Sampled, MCMC, finite-element,
quadrature, finite-grid and floating-point eigensolver values are `directional`; only
closed-form or rationally certified values are `exact`, and even an exact witness is a
candidate until a reviewed dossier states it. Every computation goes through the harness
in `experiments/` into a provenance-stamped artifact; the `numerics` pack is the one role
permitted to run it, and no other role runs ad-hoc scripts.

## Commands

```bash
cd experiments
uv run python -m numerics list                   # targets and their profiles
uv run python -m numerics run example            # a new file in research/runs/
uv run python -m numerics run example --profile full --seed 20260901
uv run pytest                                    # contract + calibration anchors
```

A run target is mandatory. A run never overwrites a file; `--out` must stay under
`research/runs/`.

## The artifact

```text
{"_provenance": {"schema_version": 1, "date": "2026-09-02",
   "target": "example", "profile": "standard", "stochastic": true,
   "config": {"seed": 20260902, "n": 2000, "grid": 2, "width": 4, ...},
   "git_commit": null, "git_dirty": null, "git_diff_sha256": null,
   "environment": {"python": "3.13.12", "numpy": "2.5.2", ...}}}
{"kind": "search", "instance": "small-integer-vectors",
 "claim": "sum_i (a_i - abar)^2 == sum_i a_i^2 - n abar^2",
 "evidence": "exact", "outcome": "consistent",
 "detail": {"domain": "all integer vectors in [-2,2]^4 (625 of them)",
            "witness": null}, "note": "..."}
{"kind": "run-summary", "target": "example", "profile": "standard", ...}
```

*Abridged and re-wrapped from `example/research/runs/`; each record is one line on disk.*

Line 1 is the `_provenance` header, then the target's records, then one `run-summary`. A
record is either an **observation**, carrying `kind`, `instance`, `claim`, `evidence`,
`outcome` and a target-owned `detail`, or **auxiliary data** carrying none of `claim`,
`evidence`, `outcome`. Half an observation is rejected.

| `evidence` | admissible `outcome` |
|---|---|
| `exact` | `contradicts`, `consistent`, `inconclusive` |
| `directional` | `contradicts`, `consistent`, `inconclusive` |
| `calibration` | `match`, `mismatch` |

`consistent` means only that the computation failed to contradict the claim over what it
covered. `contradicts` with `evidence: exact` is the one outcome worth escalating to a
refutation dossier.

The header records `git_commit`, `git_dirty` and `git_diff_sha256` (the hash of the
uncommitted diff), so a run made from an uncommitted target is still traceable. This is
provenance, not eligibility: nothing gates on it. An artifact migrated from an older schema
additionally carries `migrated_from.path` under `research/legacy-runs/` and its SHA-256.

## Writing a target

A target module under `experiments/numerics/targets/` exposes one function,
`run_records(seed: int, **cfg) -> RunResult`, and is registered with a `TargetSpec`:

```python
REGISTRY = {
    "example": TargetSpec(
        "example", example,
        "worked example target: the prop:example identity, ...", True,
        {"standard": {"n": 2_000}, "full": {"n": 50_000, "grid": 3}},
    ),
}
```

The arguments are the stable id, the module, a summary, whether it is stochastic, and its
named profiles. Every target records at least one calibration against a closed form, which
is what `pytest` checks it by. Target ids are public and permanent: renaming one breaks the
trail from old checkpoints to their evidence. Before writing a target, fix the threshold
that would count against the claim; a diagnostic with no refuting outcome is not worth
running.

| constructor | shape |
|---|---|
| `compare(instance, claim, *, bound, value, evidence)` | a value against a proposed bound |
| `matches(instance, claim, *, value, exact)` | a calibration against a closed form |
| `searched(instance, claim, *, domain, witness=None)` | a finite search; a witness contradicts |
| `observe(instance, claim, *, evidence, outcome, **detail)` | anything else |

Owning files:

- [`experiments/README.md`](../experiments/README.md)
- [`packs/numerics/numerics.md`](../packs/numerics/numerics.md)
- code `experiments/numerics/contract.py`
- checker `scripts/checks/numerics.py`

(spec-agents)=
# Agents: roles, lenses and orchestration

## The orchestrator

The orchestrator is the main agent session, driven by a human. It is not a spawnable role.
It owns every single-writer file except the portfolio: `ledger.yaml`, `brief.md`,
`references.bib`, accepted manuscript changes, and the application of every delta a role
proposes. A role proposes an exact change; the orchestrator resolves contention, applies it
atomically, and runs the checker.

## Roster

| role | lenses | writes | cardinality |
|---|---|---|---|
| `scout` | none | nothing | many, in parallel |
| `researcher` | `prove`, `refute`, `mine`, `construct` | one dossier; checkpoints | one per dossier |
| `reviewer` | `certify`, `sync` | one new review | one cold reviewer per dossier |
| `synthesizer` | none | portfolio, instances; checkpoints | singleton |

| pack | install when | writes |
|---|---|---|
| `numerics` | there is something to compute | `experiments/numerics/`, runs, checkpoints |
| `literature-scout` | there is external work to import | checkpoints (proposes nodes, BibTeX) |
| `janitor` | the repository needs tidying | nothing; proposes a change list |

**scout** reads a node, its dependencies, fences, routes and past checkpoints, and returns
pointers, never opinions. **researcher** does the mathematics on one target through one
lens. **reviewer** audits: `certify` is the gate for `mode: agent`, `sync` checks that
manuscript, summary, dossier and quoted brief agree. **synthesizer** converges parallel
work: it curates the portfolio, deduplicates routes, declares saturation, curates the
instance battery, and holds any merge barriers the program declares.

## Lenses

| lens | role | what it does |
|---|---|---|
| `prove` | researcher | builds a standalone proof dossier |
| `refute` | researcher | writes the exact negation, then hunts a witness |
| `mine` | researcher | extracts what an existing proof really buys |
| `construct` | researcher | builds an object and verifies it analytically |
| `certify` | reviewer | checks a proof step by step; may pass it |
| `sync` | reviewer | checks the texts of one claim agree |

An assignment names **one role and one lens**, and the role reads only that lens file. A
role that surveys several strategies produces a shallow pass on all of them.

## Write permissions

Paths under `research/` are written without that prefix.

| path | written by | everyone else |
|---|---|---|
| `program/ledger.yaml` | orchestrator | proposes a delta |
| `program/brief.md` | orchestrator | proposes a delta |
| `modules/` | orchestrator | proposes; `sync` proposes patches |
| `references.bib` | orchestrator | `literature-scout` proposes entries |
| `program/portfolio.yaml` | synthesizer | proposes a `portfolio_delta` |
| `instances.md` | synthesizer | proposes an instance |
| `solutions/` | researcher | never the reviewer |
| `reviews/` | reviewer | never the researcher |
| `explorations/` | researcher, synthesizer, packs | create-only, never edit |
| `experiments/`, `runs/` | numerics | nobody |
| `.claude/`, `packs/` | maintainer | generated parts via `new.py agents` |
| `.codex/agents/` | `new.py agents` only | never by hand |

The split between `solutions/` and `research/reviews/` is an epistemic control: an author
cannot certify their own work. When the runtime allows it, the reviewer is launched without
the author's conversation history and reconstructs the work from the repository alone.

## The handoff envelope

Every role ends its report with:

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

`next_prompt` is an instruction, passed on verbatim, never a softened summary. A
`portfolio_delta` names the route, its new state, and, if blocked, the exact `cand:` or node
id plus the reopening condition ("this looks hard" is not a blocker). For a proof review,
`complete` means the certifying report passed, `revise` sends the reviewer's exact repair
instructions to the researcher, and `blocked` means no certification delta applies. Words
like "pass" in prose never control a transition.

## Concurrency keys

| key | rule |
|---|---|
| `ledger`, `brief`, `manuscript`, `bibliography` | orchestrator only |
| `portfolio`, `instances` | one synthesizer |
| `numerics-code` | one `numerics` while `experiments/numerics/` changes |
| `numerics-run:<target>:<profile>:<seed>` | parallel only for distinct runs |
| `solution:<dossier>` | one researcher |
| `review:<dossier>` | one cold reviewer at a time |
| `checkpoint:<path>` | exclusive, create-only path |

Parallel work is allowed only on distinct keys, and the orchestrator enforces it. A new
single-writer file gets a new key.

## Typical transitions

```text
Explore:  scout -> researcher(refute) -> numerics (when requested)
                                      \-> researcher(prove)
External: literature-scout -> orchestrator
Mining:   researcher(mine) -> synthesizer | researcher(prove)
Proof:    researcher(prove) -> reviewer(certify) -> pass: orchestrator
                                              \-> revise: researcher
Refute:   researcher(refute) -> researcher(prove) proves the refuter
                             -> reviewer(certify) -> orchestrator
Memory:   parallel findings -> synthesizer -> orchestrator
Sync:     reviewer(sync) -> orchestrator
Hygiene:  janitor -> orchestrator
```

## Role files, profiles and adapters

A role file is an ordinary Claude Code subagent definition: front matter with `name`,
`description`, `tools`, `model`, `effort` and `color`, then a body that is its contract.
The body must mention the shared execution contract by its path, and must contain a
`## Report` section. A lens file has front matter `name` and `role`.

`model` and `effort` are never written by hand. They come from
`.claude/agents/profiles.yaml`:

```yaml
active: survey

tiers:
  heavy:
    claude: {model: fable, effort: high}
    codex: {model: gpt-5.6-sol, effort: ultra}
  standard: ...
  light: ...
  inherit:
    claude: {}
    codex: {}

roles:
  scout: {read_only: true, color: cyan}
  researcher: {read_only: false, color: blue}
  ...

profiles:
  campaign: {scout: standard, researcher: heavy, ...}
  survey:   {scout: light, researcher: standard, ...}
  session:  {scout: inherit, researcher: inherit, ...}
```

*Abridged; the file writes each profile as a block.*

A *tier* is a resource level resolved separately for Claude and Codex (an empty block means
inherit the session's setting, on both clients or on neither). A *profile* assigns a tier to
every role, including uninstalled packs, and one profile is `active`. Tier and profile names
must differ. `read_only: true` becomes a real `sandbox_mode = "read-only"` on Codex; on
Claude it forbids the `Edit` and `Write` tools.

`python3 scripts/new.py agents` stamps each role's front matter from the active profile,
refreshes installed packs from their sources in `packs/`, and regenerates
`.codex/agents/<role>.toml`. The `roles` lane rejects any file that has drifted from what
that command would produce. Retuning is therefore: edit `profiles.yaml`, run
`new.py agents`, run `check.py --lane roles`. `.codex/` may be deleted entirely by a
repository that never uses Codex.

Prefer a new lens (one file, no permissions) to a new role (a contract, an adapter, a
roster row, a profile entry, a concurrency key).

Owning files:

- [`.claude/agents/README.md`](../.claude/agents/README.md)
- [`.claude/agents/MAINTAINING.md`](../.claude/agents/MAINTAINING.md)
- [`.claude/lenses/README.md`](../.claude/lenses/README.md)
- [`packs/README.md`](../packs/README.md)
- checker `scripts/checks/roles.py`

(spec-workflows)=
# Workflows

Each workflow below is a sequence of acts on the files described above.
[`RUNNING-A-SEARCH.md`](RUNNING-A-SEARCH.md) is the operational version of the first five.

## Instantiating the template

```bash
npm ci                                    # MyST, pinned and patched
pip install pyyaml                        # or let check.sh use uv
python3 scripts/new.py module 01-target --node conj:main --kind conjecture
python3 scripts/new.py node conj:main --kind conjecture --file 01-target.md
python3 scripts/new.py brief --target conj:main
python3 scripts/check.py ready            # the checklist, executable
```

1. **State the target** in `modules/01-target.md` inside the matching `prf:` directive.
   Paste the node that `new.py node` prints under `nodes:` in the ledger, and set
   `meta.program` and `meta.scope`. The scaffolder never writes the ledger.
2. **Write the brief.** Every section; `ready` fails on the scaffold's sentences.
3. **Add program constraints**, if any, as `P1, P2, ...` in `CLAUDE.md`, including merge
   barriers owned by the synthesizer.
4. **Install packs** you need: `python3 scripts/new.py role numerics`.
5. **Repoint** `.github/ISSUE_TEMPLATE/config.yml` at the new repository.
6. **Name the manuscript**: `README.md` title, `myst.yml` title, subtitle and author, the
   abstract; delete the instantiation section. `check.py publish-ready` is the checklist.

Then `./scripts/check.sh` and `python3 scripts/check.py ready` should both pass. Create the
portfolio (`new.py portfolio --target conj:main`) only when several routes are in flight.

## A search contribution

1. Read the brief, then the node or route: manuscript statement, dependencies, both kinds
   of fence, prior checkpoints (`check.py node <id>`, `check.py portfolio`,
   `check.py checkpoints`).
2. Attack through the one assigned lens. Send any computation to `numerics`.
3. If the work is durable, write a checkpoint (`new.py checkpoint <slug> --approach ap:x`
   or `--node <id>`). Tentative statements go in its `candidates:`.
4. Return the handoff with a `portfolio_delta`. The synthesizer applies it; accepted
   ledger or manuscript changes go through the orchestrator.

## Proving a node

1. Researcher on `prove`: `new.py dossier <id>`, header, refined theorem, proof, fence
   check, `npx myst build --pdf`. Returns `next_role: reviewer`.
2. Reviewer on `certify`, launched cold: checks statement agreement, fences, hypotheses,
   dependencies, citations, every step, the build. On success writes a `proof-review` with
   `verdict: pass` and proposes the proof record; otherwise writes an `audit` and returns
   `revise` with exact repair instructions.
3. Orchestrator: adds the proof record with `mode: agent` and the review path, sets
   `status: proved`, and runs `check.py`.

## Refuting a target

1. Researcher on `refute`: writes the exact negation, finds a witness (exact, not sampled),
   records it as a candidate in a checkpoint.
2. Orchestrator promotes the candidate to a refuter node (manuscript statement, node,
   `promotes:` checkpoint, blockers repointed).
3. Researcher on `prove` writes the refuter's dossier; reviewer on `certify` certifies it,
   including that it negates the exact quantified target.
4. Orchestrator sets the target to `refuted` with `refuted_by: [<refuter>]`; the
   synthesizer closes the routes the answer settled.

## Closing a family

The synthesizer decides that a family's mechanism is worked out (`saturated`) or merely
unfunded (`parked`), writes the synthesis checkpoint (with `approach:` naming a route in the
family), sets `closure_checkpoint` and `reopen_if`, and makes sure no route in the family is
still `active` or `queued`.

## Importing literature

The `literature-scout` reads the actual source, classifies it (`published`,
`preprint-reviewed`, `preprint-unreviewed`), restates it in the repository's normalization,
checks it against the fences, and records the search (including what was *not* found) in a
checkpoint. It proposes a literature node and exact BibTeX entries; the orchestrator adds
the entry to `references.bib` first, then the node.

## Outside contributions

An issue (forms: correction, counterexample, literature lead, proof gap, route proposal) is
an inbox item. It becomes a candidate, route, node, proof record or status only by being
triaged into the artifact that holds that genre, through the role that owns it. No issue,
comment, vote or count is citable state. A proof from outside is recorded as
`mode: human` with `accepted_by`, which is an attestation, not a review.

## Changing the harness itself

Keep the contract, the documentation, the checker and its tests synchronized; add an entry
under `Unreleased` in `CHANGELOG.md` when template users are affected. Harness work does
not by itself change any mathematical status.

Owning files:

- [`CLAUDE.md`](../CLAUDE.md) *Workflow*
- [`RUNNING-A-SEARCH.md`](RUNNING-A-SEARCH.md)
- [`README.md`](../README.md)

(spec-tooling)=
# Tooling reference

## `scripts/check.py`

```bash
python3 scripts/check.py [COMMAND] [NODE_ID] [--lane LANE]... [--root PATH]
```

`COMMAND` is `check` (the default) or one of the views `ready`, `publish-ready`, `status`,
`node`, `candidates`, `portfolio`, `checkpoints`. Every invocation first analyzes the whole
tree, including a `myst build --site` of the manuscript; if any error remains in the
selected lanes it prints them, prints the summary, and exits 1 without running the view.
`--lane` restricts *reporting*, not analysis, and may be repeated. `--root` validates
another tree (`--root example`). Exit 0 means clean. The command writes nothing the
repository tracks: MyST's output lands in the gitignored `_build/`.

## What each lane checks

A lane whose files are absent contributes nothing.

**core** (`checks/ledger.py`, `checks/manuscript.py`)

- Exactly one ledger, at `research/program/ledger.yaml`; any other `ledger.yaml` under
  `research/` is an error. Top level `meta` and `nodes` only; `meta.program` non-empty.
- Node schema: unique ids, known fields, the five required fields, the kind, status and
  provenance vocabularies, `defined` exactly for definitions.
- Literature nodes: import class, non-empty references present in `references.bib`, no
  proved unreviewed preprint; no literature fields on internal nodes.
- Anchors: each node id labels a claim directive of the same kind in the declared `file`
  under `modules/`; each claim label in `modules/` has a node.
- Relations resolve; `bounded_by` names proved nodes; `heuristic_barriers` names open
  nodes; `implies` only on proved nodes.
- `depends_on` is acyclic, and no proved node inherits an open or refuted dependency.
- MyST: reported errors, unknown directives or roles, unresolved cross-references,
  duplicate labels, colliding HTML anchors.

**proofs** (`checks/proofs.py`)

- Proved internal nodes have proof records; records only on proved nodes; known fields; no
  duplicate artifact; mode rules for `review` and `accepted_by`.
- Each artifact is an existing `.md` under `solutions/` with a closed header vocabulary and
  a `ledger-node` naming the node.
- Refuted nodes have `refuted_by`, all proved; `refuted_by` only on refuted nodes.
- Every report in `research/reviews/` has valid front matter for its type, a date matching
  its filename, and, for a proof review, `verdict: pass` and a reviewer distinct from the
  authors.
- Each `mode: agent` review exists under `research/reviews/`, is a `proof-review`, and
  lists the node and dossier in its scope.

**checkpoints** (`checks/checkpoints.py`)

- Each record under `research/explorations/`: front matter, `type: exploration`, known
  fields, required fields, outcome vocabulary, date agreeing with the filename, at least one
  engagement, `candidate` outcome if and only if candidates.
- References resolve: nodes, the approach (which requires a portfolio), run artifacts.
- Candidates: well-formed ids, unique across the log, never a node id.
- Retirements and promotions: of a candidate proposed earlier (or the same untimed day),
  not by the proposing record, at most once; a promotion's node exists.
- Supersession in `research/explorations/` and among audits in `research/reviews/`: earlier
  records of the same genre only, never itself, no cycles.

**portfolio** (`checks/portfolio.py`)

- Brief: `type: brief`, only `type` and `target`, non-empty target.
- Portfolio schema: the family and approach rules of [](#spec-search).
- Cross-references: a portfolio requires a brief; the two targets agree; targets are nodes,
  not definitions, not fences; no live route once the target is resolved; blockers are
  nodes or live candidates, never promoted candidates.
- Stopped routes cite checkpoints; every cited checkpoint parses and declares the right
  approach.

**numerics** (`checks/numerics.py`)

- Each `research/runs/**/*.jsonl` is non-empty JSON objects, one per line, with at least one
  record after the header.
- The first record is `_provenance` with `schema_version: 1`, `date`, `target`, `profile`,
  `config`, `environment`, and the keys `stochastic`, `git_commit`, `git_dirty`,
  `git_diff_sha256`; no later record carries provenance.
- A migrated artifact's legacy source exists under `research/legacy-runs/` with the
  recorded SHA-256.
- Observations are all-or-nothing, with valid evidence and outcome.
- The filename ends in `-<target>.jsonl`.

**roles** (`checks/roles.py`, only when `.claude/agents/` exists)

- `profiles.yaml`: valid tiers for both clients, role facts, every profile assigning a
  defined tier to every role, tier and profile names disjoint, `active` naming a profile.
- Role files: required front matter, name matching the filename and not shadowing a
  built-in agent, a `roles:` entry, no write tools on a read-only role, the shared contract
  referenced, a `## Report` section.
- `MAINTAINING.md` links every role and nothing unknown.
- Lenses: well-formed, owned by an existing role, and referenced by that role in both
  directions.
- Front matter, installed packs and `.codex/` adapters are exactly what
  `new.py agents` renders.

**docs** (`checks/docs.py`)

- Every repository-relative Markdown link in every `.md` file resolves, and none is
  absolute.
- Exempt: `research/explorations/` and `research/reviews/` (append-only history may point
  at files that later moved), `templates/` (links written for their destination), hidden
  directories other than `.claude` and `.codex`, and any `_build/` or `node_modules/`.

## Derived views

Nothing is stored; every view is computed on demand, which is why no role may keep a
second copy of the frontier, the reverse dependency graph or the candidate list.

`status`
: Open and refuted nodes, plus proved nodes that are applicability-blocked.

`node <id>`
: The node's YAML, then derived reverse edges: `used_by`, `assumed_by`, `implied_by`
  and `refined_by`; the unresolved antecedents blocking its application; and, with a
  portfolio, the routes it blocks.

`candidates`
: Live candidates with their source, and the promoted ones with their nodes.

`portfolio`
: Families with state counts, mechanism, closure; routes with objective, blocker,
  relations and checkpoints.

`checkpoints`
: Current checkpoint heads, superseded records with their replacements, and the same for
  audits.

`ready`
: At least one node; `meta.program` not the shipped `program`; `meta.scope` not the
  shipped sentence; a brief exists and none of its scaffold sentences remain.

`publish-ready`
: No `{{REPO_TITLE}}` or instantiation section in `README.md`; no placeholder title,
  subtitle or author in `myst.yml`; no placeholder abstract in `modules/00-overview.md`.

## `scripts/new.py`

The writer. Scaffolds never overwrite an existing file, and nothing writes the ledger.

| command | writes |
|---|---|
| `brief --target <id>` | `research/program/brief.md` |
| `portfolio --target <id>` | `research/program/portfolio.yaml` |
| `checkpoint <slug> --node <id>` or `--approach <ap>` | `research/explorations/<date>-<slug>.md` |
| `dossier <id>` | `solutions/<id>.md` |
| `module <slug> --node <id> --kind <kind>` | `modules/<slug>.md` |
| `node <id> --kind <kind> [--file <f>]` | nothing: prints a node to paste |
| `role <pack>` | installs a pack, regenerates adapters |
| `agents` | restamps role front matter and `.codex/` |

`checkpoint` also takes `--timestamp`; `module` takes `--title`; all take `--root`. Node
ids must match `^[a-z][a-z0-9]*:[a-z0-9][a-z0-9-]*$`, approach ids `ap:<slug>`, slugs
`^[a-z0-9][a-z0-9-]*$`. Unfilled `{{PLACEHOLDER}}` tokens are left for you.

## `scripts/check.sh`

Runs every validator, fastest failure first, and says honestly what it skipped.

1. Installs MyST with `npm ci` if missing (fails if impossible).
2. `check.py` on the repository, then on `example/`.
3. The checker's unittest suite (`scripts/tests/`).
4. The numerics suite (`uv run pytest` in `experiments/`), skipped without `uv`.
5. Unless `--fast`: the PDF of the manuscript and of every dossier, in the repository and
   in `example/`, failing on any LaTeX error and on any claim label missing from the
   exported manuscript. Skipped without `latexmk` and `pdflatex`.

`--strict` turns every skip into a failure. `ready` and `publish-ready` are deliberately
not run.

## MyST builds

```bash
npx myst start                   # manuscript and dossiers, live in a browser
npx myst build --pdf             # _build/exports/: manuscript + one per dossier
npx myst build --html            # the static site
cd docs && npx myst build --pdf  # this specification
```

`package.json` pins `mystmd`, and `npm ci` applies `patches/mystmd+1.10.1.patch`, which
fixes two LaTeX export bugs: a dropped `prf:assumption`, and code blocks escaped as
mathematics. PDFs use the local `pdflatex` template in `templates/latex/`, so no export
downloads a template.

## Continuous integration

`check`
: On every pull request into `main`: installs PyYAML and MyST, runs `check.py`,
  `check.py --root example` and the unittest suite. No PDF, no numerics.

`site`
: On manual dispatch only: validates, builds `myst build --html`, and publishes to GitHub
  Pages, from the default branch only (Pages must first be enabled in the repository
  settings). Dispatching from another branch builds without deploying.

Owning files:

- [`scripts/check.py`](../scripts/check.py)
- [`scripts/new.py`](../scripts/new.py)
- [`scripts/check.sh`](../scripts/check.sh)
- [`templates/README.md`](../templates/README.md)

(spec-example)=
# The worked example

`example/` is one complete search, from a precise conjecture to a certified refutation,
with one instance of every artifact genre. Its mathematics is deliberately trivial so that
all attention goes to the shape. It is a fixture, not history: it may be edited freely, and
`python3 scripts/check.py --root example` keeps it green (and `ready` passes on it).

The target, `conj:example`, claims that for all real $a_1,\dots,a_n$ with $n \ge 2$,
$\sum_i (a_i - \bar a)^2 \ge \tfrac12 \sum_i a_i^2$. It is false: $a = (1,1)$ gives
$0 < 1$.

The search, in order (checkpoint files are under `research/explorations/`):

1. `modules/00-overview.md`, `ledger.yaml`: the target is stated and gets a node.
2. `research/program/brief.md`: the brief fixes the exact negation and what would finish
   it.
3. `research/program/portfolio.yaml`: the portfolio seeds one family and three routes.
4. `2026-09-02-example-exploration.md`: a numerical run does **not** test the target, and
   two candidates come out.
5. `2026-09-03-example-roundoff.md`: the roundoff route stops on the estimate it needs.
6. `2026-09-03-example-dedup.md`: a second route is recognized as a duplicate.
7. `2026-09-03-example-refuter.md`: the witness is promoted to a node; routes and family
   close.
8. `solutions/` and `research/reviews/`: the refuter gets an ordinary dossier and an
   independent review.
9. `ledger.yaml`: only now does the target become `refuted`, through `refuted_by`.

Steps 4 and 8 are the two the harness exists to keep apart: a run found nothing and
certified nothing, and a status moved only after an independent review.

What to notice in each file:

- **`ledger.yaml`** has one node per role a node can play: an open fence
  (`conj:finite-battery`, cited in `heuristic_barriers`), an open conjecture, a proved
  proposition with a proof record, and a refuted conjecture with its proved refuter.
- **`brief.md`** writes the exact negation, explains why one witness suffices here, and
  lists five concrete audit tests (constant vectors, the zero vector, $n = 2$, scaling,
  floating point).
- **`2026-09-02-example-exploration.md`** shows a run that answered the wrong question (it
  implements the identity, not the inequality), and a witness found by reading the run's
  domain rather than its output, recorded as a candidate.
- **`2026-09-03-example-refuter.md`** carries a UTC timestamp, a `promotes:` entry, and the
  five refutation steps in order.
- **`portfolio.yaml`** ends with one `completed`, one `blocked` and one `duplicate` route,
  and a `saturated` family with its closure checkpoint and reopening condition.
- `conj:weighted-example` stays open and `cand:example-identity-stability` stays live: a
  repository does not empty out when its conjecture falls.

Three deliberate differences from a real repository: `example/` has no `.claude/` (the roles
lane skips it), it must stay a top-level sibling of `research/` and `modules/` (nested, its
ledger would be a second ledger), and it is its own MyST project whose dossiers point at
`../../templates/latex`.

Owning file: [`example/README.md`](../example/README.md).

(spec-constraints)=
# The hard constraints at a glance

The contract's twelve numbered constraints, one line each. Records cite them by number, and
the numbers never change. Program-specific constraints, if any, are numbered `P1, P2, ...`
in their own section of `CLAUDE.md`. "Review" means no structural check can decide it.

| constraint, in short | checked by |
|---|---|
| **1.** One ledger, with one writer: the orchestrator. | `core` (one file); the writer by discipline |
| **2.** Numerics only through the harness; it certifies nothing. | `numerics` (artifact shape); review |
| **3.** One shared instance battery, curated by the synthesizer. | discipline |
| **4.** A green check establishes structure only. | not checkable |
| **5.** `bounded_by` names proved nodes; barriers are advisory. | `core`; violations by review |
| **6.** Explorations are append-only. | discipline; `new.py` never overwrites |
| **7.** A candidate is not a node; promotion is one act. | `checkpoints`, `portfolio` |
| **8.** Antecedents go in `assumes`, not `depends_on`. | `core` (partly); review |
| **9.** Proofs are plural records with a certification mode. | `proofs` |
| **10.** A refutation negates the exact quantified statement. | `proofs` (`refuted_by`); review |
| **11.** The portfolio is search state, with one writer. | `portfolio`; the writer by discipline |
| **12.** Outside contributions are an inbox, not state. | by construction |

Owning file: [`CLAUDE.md`](../CLAUDE.md), *Hard constraints*.

(spec-where)=
# Appendix: where is the truth?

| question | owner |
|---|---|
| What exactly does a claim say? | `modules/`, at its `:label:` |
| What is a claim's status, and what does it rest on? | `research/program/ledger.yaml` |
| What is the target, and what would finish it? | `research/program/brief.md` |
| Which routes are alive, blocked, saturated? | `research/program/portfolio.yaml` |
| What has been tried, and why did it fail? | `research/explorations/` |
| Which statements are proposed but not nodes? | `check.py candidates` |
| Where is the proof, and who checked it? | `solutions/`, `research/reviews/` |
| What did a computation return? | `research/runs/` |
| Which instances must every battery include? | `research/instances.md` |
| Which fields may a node have? | `research/program/ledger-schema.md` |
| Which fields may the portfolio or brief have? | `research/program/portfolio-schema.md` |
| Which fields may a checkpoint have? | `research/explorations/README.md` |
| Which fields may a review have? | `research/reviews/README.md` |
| Which fields may a dossier have? | `solutions/README.md` |
| How is a run artifact shaped? | `experiments/README.md` |
| Who may write which file? | `.claude/agents/README.md` |
| Which model and effort does a role use? | `.claude/agents/profiles.yaml` |
| How do I add a role or lens? | `.claude/agents/MAINTAINING.md` |
| What is universally forbidden? | `CLAUDE.md`, *Hard constraints* |
| What is forbidden in this program only? | `CLAUDE.md`, *Program constraints* |
| How do I run a search, step by step? | `docs/RUNNING-A-SEARCH.md` |
| What does a finished search look like? | `example/` |
