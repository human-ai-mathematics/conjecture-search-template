# {{REPO_TITLE}}

<!-- Replace this paragraph: what mathematical object this repository studies, what
     question it is organized around, and what a reader should expect to find proved
     versus open. Keep it honest — the ledger, not this file, is the source of truth. -->

This repository contains a MyST Markdown manuscript, with its mathematics in LaTeX, together
with a harness for **sustained conjecture search**: proving or refuting one hard statement, over
many sessions and several agents, while keeping track of what is claimed, what the search is
doing, and why.

Template releases and migration-relevant changes are tracked in [`CHANGELOG.md`](CHANGELOG.md)
and use matching semantic-version Git tags.

## The shape of the repository

Three domains. Everything else is a detail of one of them:

> **Mathematical state** — what is claimed. **Search state** — what the search is doing.
> **Durable evidence** — why either changed.

| domain | source of truth |
|---|---|
| mathematical state | statements in [`modules/`](modules/); logical state and graph edges in [`research/program/ledger.yaml`](research/program/ledger.yaml); proofs in [`solutions/`](solutions/) |
| search state | `research/program/brief.md` — what would finish it; `research/program/portfolio.yaml` — families, routes, blockers. Both are gated: absent until the work opens them ([scaffolds](templates/README.md), [worked](example/research/program/brief.md)) |
| durable evidence | checkpoints and candidates in [`research/explorations/`](research/explorations/); reviews in [`research/reviews/`](research/reviews/); run artifacts in [`research/runs/`](research/runs/) |

Said as one rule:

> Ledger = what is mathematically claimed. Portfolio = what the search is doing.
> Checkpoints = why the portfolio changed.

The coupling [`scripts/check.py`](scripts/check.py) enforces, and the reason a statement cannot
drift from its recorded status without something going red:

> Every labelled claim directive (`prf:theorem`, `prf:conjecture`, …) in `modules/` is exactly
> one ledger node, whose `kind` is that directive. A heading or equation label is structural
> and is not a node.

A statement that has not earned a node yet is a *candidate*, and it lives in the front matter
of the checkpoint that proposed it — never in a registry of its own ([`CLAUDE.md`](CLAUDE.md)
constraint 7).

Gates activate structurally, not by a mode flag: a repository with no portfolio has no
portfolio rules, and the checker validates only what exists. The gates are listed in
[`CLAUDE.md`](CLAUDE.md); `AGENTS.md` is a symlink to it, so Claude Code and Codex receive the
same contract. Agent roles and their write permissions are in
[`.claude/agents/`](.claude/agents/README.md); the strategies they are pointed at are in
[`.claude/lenses/`](.claude/lenses/README.md).

A worked instance of every artifact genre — nodes, a dossier, a review, checkpoints, a
portfolio, a run artifact, a proof and a refutation — is in [`example/`](example/README.md). It
is a fixture to copy from, not this repository's history, and the live search starts empty.

## Verify

```bash
./scripts/check.sh                        # everything available, fastest failure first
./scripts/check.sh --fast                 # skip the PDF build
./scripts/check.sh --strict               # a missing tool is a failure, not a skip

python3 scripts/check.py                  # 0 errors required after any ledger edit
python3 scripts/check.py --lane core      # core|proofs|checkpoints|portfolio|numerics|roles|docs
python3 scripts/check.py ready            # can a search start here?
python3 scripts/check.py publish-ready    # is the manuscript fit to show?
python3 scripts/check.py status           # the live frontier
python3 scripts/check.py portfolio        # the live search
python3 scripts/check.py checkpoints      # current heads of durable memory
python3 scripts/check.py node <id>        # one node: deps, consumers, fences
python3 scripts/check.py candidates       # statements proposed but not yet nodes
python3 scripts/check.py --root example   # the worked example, kept green as a fixture
python3 scripts/new.py agents             # restamp roles from agents/profiles.yaml
```

`check.py` writes nothing the repository tracks: it reads the manuscript by running `myst
build --site`, whose output lands in the gitignored `_build/`. Writing is
[`scripts/new.py`](templates/README.md): its scaffolds never overwrite hand-authored files,
while `new.py agents` deliberately replaces generated role frontmatter and adapters. It never
touches the ledger.

Two toolchains are needed: PyYAML, declared in [`pyproject.toml`](pyproject.toml), and MyST,
pinned in [`package.json`](package.json) (Node.js 18 or later, with npm):

```bash
pip install pyyaml                 # or let check.sh use 'uv run', which reads the manifest
npm ci                             # MyST, at the pinned version, with its patch applied
```

The first `check.py` run in a fresh clone downloads MyST's site theme into `_build/`; later
runs work offline.

A *lane* is a partition of the checker, not one of the three domains above and not one of
`CLAUDE.md`'s gates. Nothing lines the three up.

A green check establishes structure only. It says nothing about whether a proof is correct
(`CLAUDE.md` constraint 4). It also says nothing about whether the repository has been
instantiated — a fresh clone is correctly green and correctly *not ready*.

## Build

The manuscript and the dossiers are MyST Markdown, configured by [`myst.yml`](myst.yml). The PDF
goes through LaTeX (a TeX Live install with `latexmk` and `pdflatex`) and the local template in
[`templates/latex/`](templates/latex/template.yml):

```bash
npx myst start                 # read the manuscript and the dossiers, live, in a browser
npx myst build --pdf           # _build/exports/manuscript.pdf, and one PDF per dossier
npx myst build --html          # the static site the `site` workflow publishes
```

Each dossier also builds as a standalone PDF; a cross-reference from it into `modules/` prints
`??` there, which is expected, and resolves on the site.

---

# Instantiating this template

<!-- Delete everything below this line once the checklist is done. -->

Six steps, none of which deletes a record. The live search and evidence areas ship empty and
the worked example lives in [`example/`](example/README.md), so instantiating is scaffolding
and filling in — never removing history. Nothing needs renaming: `research/program/` is the
control directory in every repository built from this template.

[`docs/RUNNING-A-SEARCH.md`](docs/RUNNING-A-SEARCH.md) covers this and everything after it.
`python3 scripts/check.py ready` is the checklist in executable form: run it now, and it will
list whatever is still outstanding.

1. **Name the program and state the target.** Write the question this repository is organized
   around in [`modules/`](modules/), inside the `prf:` directive matching its kind, under a
   `:label:`. Then give it a ledger node and name the program:

   ```bash
   python3 scripts/new.py module 01-target --node conj:main --kind conjecture
   python3 scripts/new.py node conj:main --kind conjecture --file 01-target.md   # prints; you paste it
   ```

   Paste the node under `nodes:` in
   [`research/program/ledger.yaml`](research/program/ledger.yaml) and set `meta.program` and
   `meta.scope` there. The scaffolder does not write that file: it has one writer
   ([`CLAUDE.md`](CLAUDE.md) constraint 1). This is the first gate a search crosses, because
   the brief and the portfolio both have to resolve to it.

2. **Write the problem brief.**

   ```bash
   python3 scripts/new.py brief --target conj:main
   ```

   It is the one document that supplies mathematical pressure: the exact negation, what
   counts as a complete proof and a complete refutation, the edge cases a reviewer must
   check, the equivalent-strength traps, and a budget policy that permits an honest
   unresolved outcome. The harness remembers and certifies; the brief is what makes the
   search sharp. Do not start a sustained search without one — and a *scaffolded* brief is
   not a written one, which is why `ready` fails until its instructions are gone.

3. **Add program constraints, if any.** [`CLAUDE.md`](CLAUDE.md) ships twelve universal hard
   constraints. Anything specific to this repository's mathematics goes in the *Program
   constraints* section as `P1, P2, …` — kept separate so a fork can drop them without
   leaving a `Reserved` hole. Merge barriers belong here, and the `synthesizer` role should
   name the same owner.

4. **Install the capability packs you need.** [`.claude/agents/`](.claude/agents/README.md)
   ships four core roles — `scout`, `researcher`, `reviewer`, `synthesizer`. `numerics`,
   `literature-scout` and `janitor` wait in [`packs/`](packs/README.md) until asked for:

   ```bash
   python3 scripts/new.py role numerics
   ```

   Prefer a new assignment *lens* in [`.claude/lenses/`](.claude/lenses/README.md) to a new
   role; [`.claude/agents/MAINTAINING.md`](.claude/agents/MAINTAINING.md) is the guide. If
   nothing here will run under Codex, delete `.codex/` — the roles lane will not complain.

5. **Repoint the contribution links.** `.github/ISSUE_TEMPLATE/config.yml` names this
   template repository by URL, and is the only file that does. Nothing else depends on it.

6. **Name the repository and the manuscript.** Replace `{{REPO_TITLE}}` above, the
   placeholders in [`myst.yml`](myst.yml) (title, subtitle, author) and the abstract at the top
   of [`modules/00-overview.md`](modules/00-overview.md), then delete
   this section. `python3 scripts/check.py publish-ready` is the checklist for exactly this
   step — and it is deliberately *not* part of `ready`, because none of it blocks an attack
   on the target. A repository can be deep into a search and still owe an abstract.

Then `./scripts/check.sh` and `python3 scripts/check.py ready` should both pass.

**Optional, when the work asks for it.** Create the search portfolio when several routes,
agents or sessions are in flight:

```bash
python3 scripts/new.py portfolio --target conj:main
```

Keep or delete `experiments/numerics/targets/example.py` as you like: it is reference code
the numerics test suite exercises, not a research record. `example/` itself can stay
indefinitely; it is checked separately and touches nothing.

## What to fill in as the program grows

These ship as skeletons on purpose — a wrong entry is worse than an empty table:

- [`myst.yml`](myst.yml) — add macros under `math:`, below the *program macros* comment; the
  core block above it stays diffable against the template. A macro standing for a fixed
  normalization needs a `kind: definition` node, not just a macro.
- [`references.bib`](references.bib) — empty. A node with `provenance: literature` needs keys here
  first.
- [`research/instances.md`](research/instances.md) — the shared adversarial battery; instances
  enter only through the `synthesizer`.
