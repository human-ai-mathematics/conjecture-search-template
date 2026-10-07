# SPECIFICATION.md — repository contract

This file is the whole contract. No client loads it on its own, so every session that edits
the repository reads it first, and every agent file in [`.claude/agents/`](.claude/agents/)
and [`.codex/agents/`](.codex/agents/) tells its agent to. The two directories define the
same three roles, for Claude Code and for Codex: a change to a role is made in both.
[`example/`](example/README.md) is one complete search, worth reading once alongside it;
[`templates/`](templates/) holds an empty copy of each file genre.

## Scope

This is a harness for **sustained conjecture search**: proving or refuting one hard statement,
over many sessions and several agents at once, without losing what the search has learned.
Theory building, classification and computer-assisted proof are outside what it is tuned
for. The manuscript under `modules/` is what a mathematician reads: fixed statements in
prose written for a reader, brought up to date at milestones (*Manuscript*).

> Ledger = what is mathematically claimed. Portfolio = what the search is doing.
> Checkpoints = what the search learned.

## Principles

Everything below serves six guarantees; when a case is not covered, decide by them.
The formats define what the checker enforces; the workflow recommends how to organize
work while preserving these guarantees.

- **Record what must survive.** Exploration is free: a quick computation, a guess or a
witness checked by hand needs no file and no ceremony. Record what a later session or
another agent will rely on.
- **A status is earned, never predicted.** A claim becomes `proved` or `refuted` only
through a certified proof or refutation — or, for an established result, its references.
Numerical output, a green check or a count of failed attempts moves nothing.
- **Certification is independent or human.** A proof is certified by an independent review or
by the explicit acceptance of a named human, who may also have proposed and proved the result;
an agent never certifies its own work. A certification covers only the versions examined:
fingerprints detect changes; an editorial note carries the certification over an edit that
leaves the mathematics unchanged, and a re-review examines any other (*Review*).
- **Each part has a responsible writer.** The *Layout* table assigns shared content to
its writer. Roles write their own records and propose changes outside their write surface
as exact edits for the responsible writer. Statements and surrounding prose have different
writers even when they share a file.
- **Every statement has a canonical version.** A ledger node's statement lives in the
manuscript; a candidate's lives in the checkpoint that proposed it. The ledger and portfolio
point to these by id. A dossier restates what it proves, possibly more strongly; a review
checks that the manuscript claim follows. The brief's exact negation is an attack tool,
not a second canonical statement. Likewise, a status has one authority, the ledger, and the
prose must agree with it.
- **Preserve the research record.** Reviews and checkpoints are append-only: a correction
is a new dated file identifying the earlier file and the conclusions it corrects. This
keeps the reasoning behind decisions readable in the tree. Current state — manuscript,
ledger, brief and portfolio — is updated rather than treated as an archive.

Independence, mathematical correctness and append-only history are obligations, not properties a
green check establishes. The checker validates identities and rejects a review naming its reviewer
as an author; it does not establish actual independence, nor compare archives with earlier commits
to enforce append-only.

Human contributors may propose, write, check and accept their own results, through `accepted_by`
rather than a review. The role assignments below organize agents, not human participation. Human
acceptance must be explicit and attributed; an agent must not infer it from authorship or a proposed
theorem. The dossier, canonical statement and fingerprints still record exactly what was accepted.

## Layout


| content                                                                | location                                         | writer       |
| ---------------------------------------------------------------------- | ------------------------------------------------ | ------------ |
| canonical statements: the labelled `prf:` directives of the manuscript | `modules/*.md`                                   | orchestrator |
| the manuscript's prose, its headings and its split into files          | `modules/*.md`, `modules/` entries of `myst.yml` | `writer`     |
| claim state and logical edges                                          | `research/program/ledger.yaml`                   | orchestrator |
| target, negation, completion criteria, traps, neighbourhood            | `research/program/brief.md` (optional)           | orchestrator |
| routes and blockers                                                    | `research/program/portfolio.yaml` (optional)     | orchestrator |
| bibliography                                                           | `references.bib`                                 | orchestrator |
| checkpoints and candidate statements                                   | `research/explorations/*.md` (append-only)       | any role     |
| computation scripts and their output                                   | `research/runs/`                                 | any role     |
| shared computation code                                                | `research/lib/` (optional)                       | any role     |
| proof and refutation dossiers                                          | `solutions/*.md`                                 | `researcher` |
| independent reviews and editorial notes                                | `research/reviews/*.md` (append-only)            | `reviewer`   |
| the introduction to the full proofs                                    | `proofs.md`                                      | orchestrator |


The brief and the portfolio are optional. Create the brief when a sustained search starts, and the
portfolio with its first route: every route lives there, and nowhere else. The checker validates
only what exists, so a fresh clone is green. An afternoon of speculative work may leave no file at
all: something is recorded when it must survive the session or coordinate someone else.

## Formats

Write mathematics in LaTeX `$...$`. The manuscript and the dossiers are MyST Markdown: a claim is a
`prf:<kind>` directive carrying a `:label:`, and a cross-reference is `[](#<label>)`. Dated records
— checkpoints and reviews — are named `<YYYY-MM-DD>-<slug>.md`, and the filename orders them. The
identities inside a review carry their own dates (*Review*).
Every record — a dossier, a checkpoint, a review, the brief, the portfolio, a docstring in
`research/lib/` — points at the manuscript by label (`[](#thm:x)`, `[](#sec:x)`, or the bare id
outside MyST), never by a module's file name: modules are renumbered, and a dated record keeps
its stale path for good.

### Ledger — `research/program/ledger.yaml`

```yaml
nodes:
  - id: conj:main
    status: open
```

The ledger holds only what the manuscript cannot: each claim's status and its edges. The
statement, its kind (the `prf:` directive) and its file are read from the manuscript.


| field        | meaning                                                                                                                                                                   |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`         | Stable id, and **the manuscript anchor**: `:label: <id>` in `modules/`. Required.                                                                                         |
| `status`     | `open`, `proved`, `refuted`, or `defined` (for, and only for, a `prf:definition`). It records what is established, never what is expected. Required.                      |
| `depends_on` | Claims used in the proof — the acyclic proof DAG. A proved node may not inherit an open or refuted dependency, transitively.                                              |
| `assumes`    | Antecedents of a proved implication. Truth and applicability are separate: the implication stays `proved` while an antecedent is open, which `depends_on` would forbid.   |
| `bounded_by` | Fences. A proved fence binds: a statement violating it is wrong by construction. An open one is a plausible method barrier: it guides work and fences nothing.            |
| `references` | BibTeX keys in `references.bib`, making this a result imported from the literature. An *established* result needs no proof record to be `proved`; see *Imported results*. |
| `proofs`     | Certification records; required for a proved node without `references`.                                                                                                   |
| `refuted_by` | Proved refuters; required for, and only valid with, `status: refuted`.                                                                                                    |


Relation fields are lists of node ids. An open question is a `prf:conjecture` in the
direction the search tries to establish. A fixed normalization — a sign, a scaling, which
constant absorbs what — is a `prf:definition` that every claim resting on it names in
`depends_on`; there is no separate notation file. The ledger holds no attempt history,
numerical output or search state.

Dependencies belong to statements, not to individual proof records. The shared DAG does
not certify that two proofs are mathematically independent. Each dossier and its review
must identify the results actually used and any claimed exclusions. In particular, a
lemma derived from the target cannot supply an independent proof of that target. Never
delete a genuine dependency to bypass a cycle; a proof needing a different representation
requires a separate framework change.

**The anchor invariant.** Every labelled claim directive in `modules/` — `prf:theorem`,
`proposition`, `lemma`, `corollary`, `conjecture`, `assumption`, `definition` or `example` — is
exactly one ledger node. A label on a heading (`(sec:x)=`), an equation or a `prf:remark` is
structural and is not a node. The checker reads the manuscript through `myst build --site`, so an
unknown directive, an unresolved cross-reference, a duplicate label and any MyST error are errors.
It also fingerprints each claim: the SHA-256 of its statement as MyST parsed it, blind to line
wrapping, spacing, numbering, a cross-reference's rendered text and the page its target lives on — a
link to a section (`[](#sec:x)`) is one, so renaming the heading lifts nothing — a proof nested in
the claim, and the displayed status. Its label and its file do not enter either, so moving a
statement to another module lifts nothing. Any other edit — a symbol, a word, a hypothesis, the
kind, the title — changes it.

### Brief — `research/program/brief.md`

Front matter `target: <node id>`. The body, copied from [`templates/brief.md`](templates/brief.md),
gives what an agent needs before attacking the target honestly: where the statement is vulnerable,
its exact negation, what counts as a complete proof and refutation, edge cases, traps and circular
reductions, the neighbouring statements worth examining (by id), and a budget policy that permits an
honest unresolved outcome. It never copies a statement, and it lists no route: routes live in the
portfolio. Rules specific to this program — say, a comparison only one agent may hold at a time — go
under its traps.

### Portfolio — `research/program/portfolio.yaml`

```yaml
approaches:
  - id: ap:transport-gluing
    objective: Glue local transport maps across the overlap into one global map.
    state: blocked                  # active | blocked | closed
    blocker: cand:transport-compatibility
    next: Test compatibility on two overlapping balls, where both maps are explicit.
```

Every route lives here, from the first one. A `blocked` route names its `blocker`: a node id or a
live candidate id. It reopens when the blocker is settled — the checker flags a route whose blocker
node is `proved` or `refuted`, or whose candidate is closed. Add `reopen_if` only when something
else would reopen it. `next`, optional, is the discriminating test the route would run next — what a
resumed session starts from; the summary prints it with the latest checkpoint that names the route.
`closed` means the objective is finished or abandoned; it says nothing about the target, and a route
never becomes a node. A proved target may retain active routes towards alternative proofs
or stronger statements: their objectives and next tests must say what remains to obtain.
A refuted target leaves no route `active` in its proof search; a corrected formulation must
become a different target. A checkpoint records why a route changed state, distinguishing
an accomplished objective from an abandoned one or a proved impossibility. A proof of the
target alone neither refutes another route's premises nor closes that route.

### Checkpoint — `research/explorations/<date>-<slug>.md`

A checkpoint is the memory of what was learned. Write one when something must outlive the session: a
candidate born or ended, an observation worth keeping, a dead end the next agent would repeat, a
route changing state, a run someone may reuse. One checkpoint may cover several small explorations.
The body, copied from [`templates/checkpoint.md`](templates/checkpoint.md), names nodes, routes and
blockers by id under four headings:

- **Question examined** — what the work tried to understand.
- **What we learned** — each item marked *established* (an argument written out, not
certified), *observed* (computation or examples) or *intuition*.
- **What resists** — the precise obstacle, or the limit of the method.
- **Proposed next step** — the next action, and what it would decide.

An *established* result is not a certified one: no ledger node inherits it through `depends_on`, and
a dossier reproves it rather than citing it, until it becomes a node with its own certified dossier.
An observation — *this relaxation destroys the information about the equality cases* — is kept as it
is: a candidate is created only once a statement precise enough to prove or refute emerges.

```yaml
---
artifacts: [research/runs/2026-09-02-sweep.jsonl]
candidates:
  - id: cand:key-bound
    statement: >-
      A precise statement someone could later prove or refute.
closes: [cand:old-guess]    # earlier candidates this one ends
---
```

Every field is optional. A **candidate** is a tentative statement: no manuscript anchor, no
status, no certification, and its `statement:` is the only copy. Candidate ids are unique
across the log and never a node id. `closes:` ends a candidate an earlier checkpoint
proposed — never the same one or a later one — because it died, or because it was
**promoted**: given a manuscript `:label:` and a ledger node, which the closing checkpoint
names. A statement ready to be a node on its first appearance — an exact witness, checked
by hand — skips the candidate stage and is proposed directly as a manuscript claim.

### Run — `research/runs/<date>-<slug>.py`

Exploratory computation is free: a `python -c`, a scratch script, a notebook, kept nowhere.
A computation becomes a **run** once something that must survive rests on it — a checkpoint
cites it, a route is chosen or closed because of it. A run is a committed, seeded script, run
with `uv run`, copied from [`templates/run.py`](templates/run.py). Its output lands next to it
as `<date>-<slug>.jsonl`, whose first line — written by the template's `provenance()` — holds the
seed, the parameters, the git commit, flagged `dirty` if the tree had uncommitted changes, and
the library versions; a checkpoint cites it under `artifacts:`. A run guides the choice of route
and suggests statements; it proves nothing. An exact witness it finds is checked by hand
before it becomes a claim, and the check, not the run, goes in the dossier.

Let the tooling grow only as the search needs it:

1. **A plain script**, standard library only.
2. **Dependencies declared in the script** (PEP 723), once it needs numpy or mpmath:
  `# /// script` / `# dependencies = ["numpy>=2", "mpmath"]` / `# ///` at its top.
3. **A package,** `research/lib/`, once two scripts share code: its own `pyproject.toml`
  and committed `uv.lock`, kept apart from the checker's, and unit tests — a bug in a  
   shared oracle contaminates every run that used it. Scripts stay the entry points and  
   import it; the lock at the recorded commit gives the library versions.

### Proof records and dossiers

A **dossier** is a standalone MyST page `solutions/<ledger-id>.md` (`:` replaced by `-`), copied
from [`templates/solution.md`](templates/solution.md). Its front matter carries `ledger-node:` — the
node id, or a list of ids — a `title`, and a `numbering` prefix so that its statements read Theorem
3.1, Lemma 3.2, … (set it before the first review: any later edit lifts the certification); never
its own certification. It opens with an **Overview**, the steps and what each contributes, and may
fold a routine computation into a `:class: dropdown` proof, still written in full. It states the
theorem in a `prf:theorem`, possibly sharper than the manuscript statement it cites, and proves it
in a `prf:proof`; every step stands analytically, and each step the author could not close is a
`prf:remark` naming what remains. It may cite certified nodes instead of reproving them; it never
contains numerical output.

```yaml
proofs:
  - artifact: solutions/thm-main.md
    review: research/reviews/2026-09-02-thm-main-review.md
  - artifact: solutions/thm-main-second-proof.md
    accepted_by: A. Referee, human, 2026-09-10
    fingerprints:                   # printed by: uv run scripts/check.py --fingerprint <dossier>
      solutions/thm-main-second-proof.md: <sha256>
      thm:main: <sha256>
```

A **proof record** names a dossier and exactly one of `review` — an independent review with
`verdict: pass` — or `accepted_by`, a named human's attestation, which carries its own
`fingerprints`. `accepted_by` is a human's identity (*Review* below), and may be the
proof author's. This channel requires no separate reviewer or review report. A node may carry several
independent proofs. A dossier no `proofs[]` record names is an uncertified draft; the summary lists
it as one.

**Fingerprints** pin a certification to what it saw. They map the dossier's path to its
SHA-256, and each statement the proof is checked against to its fingerprint: the node's own,
every `depends_on` and `assumes`, and every target that names the node in `refuted_by`.
`uv run scripts/check.py --fingerprint <dossier>` prints exactly that block, from the tree as
it stands; run it on the version you read, just before recording the verdict. Once a
dossier or one of those statements changes, the certification lapses until a new review or
acceptance. A result imported on `references` alone has no fingerprint; its manuscript
statement is the `sync` lens's to check.

**Imported results.** A result is *established* when the field already relies on it:
published in a refereed venue, or an older preprint widely cited and used with no known
gap. Age alone is not the test — adoption is. An established result is `proved` on its
`references` alone. Any other preprint stays `open` until it takes the ordinary channel: a
dossier that states the result as this repository uses it and proves it by pointing at the
source (theorem and version), an independent review that checks both the source's proof
and that the stated result follows from it, and a `proofs` record. The checker cannot tell
the two cases apart; the reviewer's `sync` lens does.

**Refutation.** A target becomes `refuted` by naming, in `refuted_by`, a proved refuter node — an
ordinary claim with a manuscript statement and a certified dossier. Its review or human acceptance
also checks that the refuter negates the target's exact quantified statement: one witness refutes a
universal claim; the failure of a uniform or dimension-free constant generally needs a certified
divergent family. The refuter never enters the target's `depends_on`, which records facts a proof
used.

### Review — `research/reviews/<date>-<slug>.md`

```yaml
---
verdict: revise          # pass | revise
authors:
  - researcher, claude-opus-5-5, 2026-09-02   # <who>, <model or human>, <YYYY-MM-DD>
reviewer: reviewer, claude-opus-5-5, 2026-09-03
fingerprints:            # the versions read: uv run scripts/check.py --fingerprint <dossier>
  solutions/thm-main.md: <sha256>
  thm:main: <sha256>
  lem:key-bound: <sha256>
---
```

**Independence is a fresh context, not a different name.** An agent reviewer is a `reviewer`
sub-agent launched without any conversation history — never a fork of the session, never the session
that wrote or directed the dossier — and given repository paths and a mission, including any repair
handoff, rather than the authoring conversation. The launch must actually provide that fresh
context; see *Orchestration* and the README for practical guidance. `authors` and `reviewer` record
who wrote and who read, each as an **identity** `<who>, <model or human>, <YYYY-MM-DD>`: an agent's
role, model and date, such as `reviewer, claude-opus-5-5, 2026-09-03` (`unknown` when the model was
not recorded), or a human's name, `human` and date, such as `A. Referee, human, 2026-09-10`. The
checker verifies the form, and that the reviewer's `<who>` is no author's; these fields record
independence, they never create it. The site shows the reviewer next to each proved statement, so
that a reader tells an agent's review from a human's.

Only `pass` certifies, and only the versions it read: once a fingerprint no longer matches, the
checker reports a stale certification and fails validation until a new review passes it or an
editorial note carries it over. It does not remove the proof record or change the ledger status
automatically. The body states **Findings**, **Corrections** (or "None") and **Exclusions** — nearby
claims not certified. A repaired proof gets a new report; if a later review invalidates a passing
one, the orchestrator removes the certification and both reports stay.

A dossier's fingerprint is the SHA-256 of its text without `%` comment lines, blind to
spacing and line wrapping; a fingerprint recorded as the SHA-256 of the file's bytes, before
this rule, is still accepted.

**An editorial note** carries a certification over an edit that leaves the mathematics
unchanged — a renamed term, a typo, a stale path or cross-reference, a sentence reworded.
It is a new file in `research/reviews/`, copied from
[`templates/editorial.md`](templates/editorial.md):

```yaml
---
verdict: editorial
amends: [research/reviews/2026-09-03-thm-main.md]   # the pass reports it carries over
authors:                                             # who made the edit
  - orchestrator, claude-opus-5-5, 2026-09-20
reviewer: reviewer, claude-sonnet-5-5, 2026-09-20
changes:                 # each edited item, from the certified version to the new one
  thm:main: {from: <sha256>, to: <sha256>}
---
```

A fresh `reviewer` reads only the diff, `check.py --diff`, and answers one question: does any
statement, formula, hypothesis, quantifier, constant or step of proof change? If none does, it
writes the note, whose body gives each item's diff and why the mathematics is unchanged; if
one does, or if it cannot tell, there is no note and the change takes a re-review. Editing an
earlier report's fingerprints is never an alternative. One note may amend several reports
(*Grouped reviews*); the proof records keep naming the `pass` reports, so the site still
shows who checked the mathematics. The checker applies the notes oldest first, and a `from`
that is not what the amended report certifies is an error. A human acceptance is carried
over by its acceptor, who records the new fingerprints in the ledger.

**A re-review** restores a lapsed certification without starting over. It retains the earlier
certification's conclusions for unchanged, unaffected parts and checks the changes and their
consequences, against a historical baseline verified to match the earlier report's fingerprints.
It reviews in full when that baseline cannot be verified, the argument's structure changes, or the
impact cannot be delimited; the number of earlier re-reviews does not matter. Recomputing
fingerprints without examining the change never restores a certification. The mission gives a
fresh reviewer the previous `pass` report, a candidate revision and the checker's lines naming what
changed; how it proceeds and what its report records is in
[`reviewer.md`](.claude/agents/reviewer.md).

**Grouped reviews.** One mission may examine a shared change once for every dossier it affects
(`check.py --impact` gives the groups). A common `pass` report concludes explicitly for each dossier
and fingerprints exactly the certified scope; a dossier that fails gets a separate `revise` report.
The worked example's README illustrates a short re-review and a grouped one.

### Manuscript — `modules/*.md`

The manuscript is the one text a reader reads: a mathematician who has never seen this
repository should understand the work from it alone. It is split in two by authority.

- **The statements are fixed.** The content of a labelled claim directive, its title
argument included (`:::{prf:theorem} Title`), is the statement; the orchestrator writes
it, and its `:label:` is its ledger id.
- **Everything else is prose**, the `writer`'s: headings, motivation, examples worked by
hand, the idea of each proof, remarks, the order of sections and the split into files,
with the matching `toc:` entries of `myst.yml`. It may be rewritten freely; the writer
proposes a new or reworded statement as a delta, never edits one.

Four rules keep the two apart:

1. **The ledger is authoritative for status.** [`scripts/status.mjs`](scripts/status.mjs), a MyST
  plugin, reads the ledger at build time and shows each statement's status next to its title: *Not
   settled here* (the ledger's `open`: not established in this project, which says nothing of the
   literature), *Preprint, not yet checked here* (an open theorem, lemma, proposition or corollary
   on `references`: a source's result that is neither established nor certified here, see *Imported
   results*), *Proved* (linking to its dossier) followed by who certified it — *agent review (model,
   date)*, *reviewed by* a human, or *accepted by* a human; *Proved (from a preprint)* when the node
   also has `references`, a source's result checked here — *Established in the literature* (a proved
   node on `references` alone), or *Refuted by* its refuter, then the statement's label. Prose may
   say "we prove" or describe a refutation when it agrees with the ledger and points to the relevant
   claim (`[](#conj:main)`). An `open` status alone never establishes that a problem is open in the
   literature. After a status change, update affected prose; the reviewer's `sync` lens checks
   contradictions and unsupported assertions. The checker does not read these assertions for
   mathematical meaning.
2. **A writer's pass changes no statement.** `check.py --statements` prints every statement with its
  fingerprint; the orchestrator runs it before and after, and the two outputs must match. Unlike a
   certification, it also guards an open conjecture.
3. **No harness vocabulary in displayed prose.** Fence, ledger, route, checkpoint, candidate,
  dossier: a reader does not need them. Notes for agents go in `%` comments, which MyST does not
   render.
4. **Computations are evidence, and say so.** A reported computation never reads as proof.

How the prose is written is in [`writer.md`](.claude/agents/writer.md).

**Full proofs.** The table of contents lists the manuscript, then `proofs.md` and the dossiers under
*Full proofs*; a proved statement links to its dossier. Only certified dossiers are published: the
`pages` workflow removes every draft (`check.py --drafts`) before it checks and builds. Read
locally, the table of contents shows the drafts too.

**Contributions.** A reader names a statement by the label displayed next to it. Once
`project.github` in `myst.yml` names the repository, the plugin adds links that open an issue form
of [`.github/ISSUE_TEMPLATE/`](.github/ISSUE_TEMPLATE/) with that label in its `statement` field:
*Idea* and *Counterexample* on an open statement, *Correction* on any other. Conversation goes to
GitHub Discussions, if the repository uses them: the forms of
[`.github/DISCUSSION_TEMPLATE/`](.github/DISCUSSION_TEMPLATE/) serve the categories *Q&A*, *Ideas*
and *Literature*, which are created by hand in the repository settings, as is *Announcements*. An
issue or a discussion moves nothing: the orchestrator turns what it brings into a mission, a delta
or a correction, and a named human's acceptance of a proof is recorded as `accepted_by`.

**Publication is a human act.** A person reads the manuscript as a reader would before dispatching
the `pages` workflow by hand; no agent dispatches it. A green check says the structure holds, never
that the prose is well written or faithful.

## Verify

```bash
./scripts/check.sh                        # check.py, the worked example, and the unit tests
uv run scripts/check.py                   # full: manuscript included; before any status change
uv run scripts/check.py --fast            # research state only, no MyST build; seconds
uv run scripts/check.py --impact          # affected certifications grouped by changed item
uv run scripts/check.py --diff            # the same, each with its diff since certified
uv run scripts/check.py --root example    # the worked example, kept green as a fixture
uv run scripts/check.py --fingerprint solutions/thm-main.md   # a certification's fingerprints
uv run scripts/check.py --drafts          # the draft dossiers, left out of the published site
uv run scripts/check.py --statements      # before and after a writer's pass: must not change
```

A green check establishes structure only. Whether a dossier implies the canonical
manuscript claim, its dependencies support its steps, and its proof is correct is the
reviewer's job. Fingerprints cover direct `depends_on` and `assumes` statements, not a
recursive hash of the dependency graph. Structural dependency checks are separate.

`check.py` prints each error as a `FAIL` line, then a summary: nodes by status, routes by
state with their `next` test and latest checkpoint, live candidates, draft dossiers and the
latest checkpoint. `--impact` replaces the summary and repeated fingerprint-mismatch
messages with groups headed by the changed statement id or dossier path. Each row names
an affected node, its dossier and the review path or human acceptance to renew. This is
scope for a grouped mission, not a mathematical impact assessment or a diff. Other errors
remain visible and the exit code is unchanged (1 if validation fails). Missing fingerprints
remain ordinary errors; they do not establish that text changed. Only certifications
currently named in proof records are compared. `--impact --fast` checks dossiers only and
labels the report as incomplete for statements; do not use it to clear a manuscript edit.
No report is saved and no Git history is searched. `--diff` adds, under each changed item,
its diff from Git: for a dossier, since the latest commit whose version has the recorded
fingerprint (a verified baseline); for a statement, the text of its labelled directive since
the commit that first recorded the fingerprint (a baseline not re-fingerprinted, enough for
an editorial note; a re-review verifies its own).

`--fast` skips the MyST build, and with it the manuscript anchors and the
statement fingerprints; dossier fingerprints are still compared. The full check writes
nothing the repository tracks; the MyST build lands in the gitignored `_build/`, and
concurrent checks of one tree take turns on it. It needs uv, which provisions PyYAML from
`pyproject.toml`, and MyST, pinned in `package.json` and installed with `npm ci`. CI runs
`check.sh` — the full check — on pull requests and on pushes to `main`; the `pages` workflow
removes the drafts, then runs the full check before it builds anything.

## Workflow

```text
target statement + ledger node  →  brief  →  routes in the portfolio
      →  missions (a question, an expected result, a starting lens)
      →  checkpoints when something is learned  →  orchestrator's decision on the routes
      →  dossier + independent review  →  ledger transition
```

The **orchestrator** is the main session. It evaluates proposed deltas, applies the accepted ones to
the files it writes, and checks afterwards: `uv run scripts/check.py --fast` after an edit to
research state, the full `uv run scripts/check.py` after a manuscript edit and before any status
change.

It also carries the search's scientific judgment. After the researchers report, it
decides which route to pursue and why, which to set aside and on what known obstacle, and
whether to reformulate the target or examine a neighbouring statement. It evaluates each
reply's route deltas, removes duplicate routes, and closes a route whose objective is
finished or abandoned — a judgment recorded in a checkpoint, never inferred from attempt
counts or elapsed time. One checkpoint may synthesize several small explorations; it keeps,
for each route set aside, the obstacle that stopped it, so the next agent does not rerun it.

**A mission** is a question and the result expected from it, not a node and a lens:

> Study the conjecture in dimension two. Look for the equality cases and decide whether the
> mechanism behind them can survive in arbitrary dimension. Report the obstacles and the
> formulations they suggest.

It names the target or route by id and a starting lens — `prove`, `refute`, `mine` or
`construct` — as a posture, not a boundary: the researcher may change direction when the
work calls for it, and says so first in its report, with the reason. A solved special
case, a useful reduction, an essential hypothesis identified or a precise obstacle is a
research result, and a mission may ask for one.

**Early critique.** An idea need not be finished to be attacked. A mission may hand a
researcher an uncertain reduction or a half-built argument: *find where it loses
information, and propose a case that shows it.* The critic is a different agent from the
idea's author; its answer goes in a checkpoint and carries no verdict. Certification stays
the reviewer's alone, on a stabilized dossier, before any move to `proved` or `refuted`.

**The target and its neighbourhood.** One target orients the search. The brief may list a
few neighbouring statements — nodes or candidates, by id — worth examining because they
bear on it: a special case, a weakening, a reformulation. A refuted target stays closed; a
corrected version is a new statement with a new id, and the checkpoint that proposes it
says which failure it answers.

A recommended session follows this loop; the certification and write-surface requirements
still apply when the work calls for a different sequence:

1. Run `uv run scripts/check.py` and read its summary: the target, each route with its
  `next` test and the last checkpoint that names it, the live candidates, the draft
   dossiers, and any certification an edit has lifted.
2. Pick a route of the portfolio that is not blocked.
3. Launch a `researcher` on a mission for it: the question, the expected result, a
  starting lens, and the route and target by id.
4. Evaluate and apply the handoff's `deltas`; adapt `next` to the current evidence and
   priorities. A repair mission retains every reported defect: address it or explicitly
   explain why it remains unresolved.
5. When a dossier is ready, launch a fresh `reviewer` with the `certify` lens (see
  *Review* for what fresh means).
6. Apply its verdict — a `proofs` record on `pass`, its `next` to a researcher on
  `revise` — then run the full `check.py` again.
7. Decide what the replies teach: which route to pursue, which to set aside and why,
  whether to reformulate. When a route changed state or a candidate was born or ended,
   make sure a checkpoint says why, and that the route's `next` names the test that would
   move it now.
8. If a milestone was reached — a status changed, a route closed, a statement was added —
  launch a `writer` to bring the manuscript's prose up to date (*Manuscript*): name the
   milestone and the ids it concerns. Not every session: the prose follows milestones.
   Run `uv run scripts/check.py --statements` before and after; the two outputs must be
   identical, or the writer changed a statement and its edit is reverted.

A certification the full check reports as lifted — a dossier or a statement edited since it
was fingerprinted — goes back through step 5: a new review, or a new human acceptance.
Recomputing the fingerprints without reading again forges a review.

Stop the proof search for a refuted target, or when no route is left worth running.
After a proof of the target, reassess the remaining objectives: alternative proofs and
stronger statements may justify continued work. Record that reassessment in a checkpoint
and update each continuing route's objective and next test.


| you want                                          | role                          | starting lens      |
| ------------------------------------------------- | ----------------------------- | ------------------ |
| a proof attempt                                   | `researcher`                  | `prove`            |
| a counterexample hunt                             | `researcher`                  | `refute`           |
| to learn what an existing proof really buys       | `researcher`                  | `mine`             |
| an object built to order                          | `researcher`                  | `construct`        |
| an unfinished idea attacked early                 | `researcher` (not its author) | `refute` or `mine` |
| a dossier certified                               | `reviewer`                    | `certify`          |
| manuscript/ledger/dossier/brief agreement audited | `reviewer`                    | `sync`             |
| the manuscript's prose brought up to date         | `writer`                      | —                  |


Each role ends its reply with this handoff, which the orchestrator acts on:

```yaml
files: [<repo-relative paths written or changed>]
deltas: [<exact edits to ledger, manuscript, brief, portfolio or bibliography>]
next: |
  <optional: proposed instructions for the next assignment>
```

Every field is optional, and a reply is as long as its result: a small advance is a few lines and an
empty handoff. A reply with no `deltas` and no `next` asks nothing of the orchestrator. `next` is an
instruction, not a summary. Something that blocks you is one sentence in the report; a route it
blocks is a portfolio delta naming the exact `cand:` or node id — "this looks hard" is not a
blocker. Words such as "pass" or "done" in prose never control a transition; certification follows
*Proof records and dossiers*.

### Orchestration

Keep context and agent calls proportionate to the work:

- **Read handoffs first.** Start with the checker's summary and agent replies, then read
  only the passages of dossiers, statements or sources that a decision on a route needs.
  Checking that a proof is correct, or that the files agree, is a `reviewer`'s mission,
  not the orchestrator's reading.
- **Name paths in missions.** Give the question, expected result, ids and relevant paths;
  avoid copying whole files. Ensure the agent receives its role instructions.
- **Prefer completion notifications or blocking waits to repeated polling.** Choose waits
  compatible with the client's limits and the need to communicate progress.
- **Prefer a focused session.** Start a fresh session when context becomes distracting or
  expensive; neither a task boundary nor compaction requires one automatically.
- **When certification lapses, ask for an editorial examination first.** Give a fresh
  reviewer the output of `check.py --diff` and the reports it names; a note carries them
  over if the mathematics is unchanged. Otherwise ask for a re-review: supply the previous
  `pass` report, a candidate historical revision and the checker's lines naming what
  changed; the reviewer verifies the historical baseline and decides whether a full review
  is needed (*Review*). Use `check.py --impact` to group dossiers affected by the same
  change into one mission.

An independent reviewer must have a fresh context as defined in *Review*, regardless of
how other work is organized. Client-specific launch and wait guidance is in the README's
*Running agents* section.

**Harness changes.** Keep this file, the checker, its tests, the templates and the example
in agreement. Harness work changes no mathematical status. In a program instantiated from
the template, a harness change is proposed to the template.
