# {{REPO_TITLE}}

<!-- Replace this paragraph: what mathematical object this repository studies, what
     question it is organized around, and what a reader should expect to find proved
     versus open. Keep it honest — the ledger, not this file, is the source of truth. -->

This repository contains a LaTeX manuscript together with a harness for **sustained conjecture
search**: proving or refuting one hard statement, over many sessions and several agents, while
keeping track of what is claimed, what the search is doing, and why.

## The shape of the repository

Three domains. Everything else is a detail of one of them:

> **Mathematical state** — what is claimed. **Search state** — what the search is doing.
> **Durable evidence** — why either changed.

| domain | source of truth |
|---|---|
| mathematical state | statements in [`modules/`](modules/); logical state and graph edges in [`research/program/ledger.yaml`](research/program/ledger.yaml); proofs in [`solutions/`](solutions/) |
| search state | [`research/program/brief.md`](research/program/brief.md) — what would finish it; [`research/program/portfolio.yaml`](research/program/portfolio.yaml) — families, routes, blockers |
| durable evidence | checkpoints and candidates in [`research/explorations/`](research/explorations/); reviews in [`research/reviews/`](research/reviews/); run artifacts in [`research/runs/`](research/runs/); harness decisions in [`decisions/`](decisions/) |

Said as one rule:

> Ledger = what is mathematically claimed. Portfolio = what the search is doing.
> Checkpoints = why the portfolio changed.

The coupling [`scripts/check.py`](scripts/check.py) enforces, and the reason a statement cannot
drift from its recorded status without something going red:

> Every claim-bearing theorem-environment `\label` in `modules/` is exactly one ledger node,
> whose `kind` is that environment. A `\section` or equation label is structural and is not a
> node.

A statement that has not earned a node yet is a *candidate*, and it lives in the front matter
of the checkpoint that proposed it — never in a registry of its own ([`CLAUDE.md`](CLAUDE.md)
constraint 8).

Gates activate structurally, not by a mode flag: a repository with no portfolio has no
portfolio rules, and the checker validates only what exists. The gates are listed in
[`CLAUDE.md`](CLAUDE.md); `AGENTS.md` is a symlink to it, so Claude Code and Codex receive the
same contract. Agent roles and their write permissions are in
[`.claude/agents/`](.claude/agents/README.md); the strategies they are pointed at are in
[`.claude/lenses/`](.claude/lenses/README.md).

A worked instance of every artifact genre — nodes, a dossier, a review, checkpoints, a
portfolio, a run artifact, a proof and a refutation — is in [`example/`](example/README.md). It
is a fixture to copy from, not this repository's history, and the live planes ship empty.

## Verify

```bash
./scripts/check.sh                        # everything, in the order that fails fastest
./scripts/check.sh --fast                 # skip the LaTeX build

python3 scripts/check.py                  # 0 errors required after any ledger edit
python3 scripts/check.py --lane core      # core|proofs|checkpoints|portfolio|numerics|roles
python3 scripts/check.py ready            # is this repository instantiated, or still a template?
python3 scripts/check.py status           # the live frontier
python3 scripts/check.py portfolio        # the live search
python3 scripts/check.py checkpoints      # current heads of durable memory
python3 scripts/check.py node <id>        # one node: deps, consumers, fences
python3 scripts/check.py candidates       # statements proposed but not yet nodes
python3 scripts/check.py --root example   # the worked example, kept green as a fixture
python3 scripts/check.py --write-codex    # regenerate the Codex role adapters
```

A *lane* is a partition of the checker, not one of the three domains above and not one of
`CLAUDE.md`'s gates. Nothing lines the three up.

A green check establishes structure only. It says nothing about whether a proof is correct
(`CLAUDE.md` constraint 4). It also says nothing about whether the repository has been
instantiated — a fresh clone is correctly green and correctly *not ready*.

## Build

Requires a TeX Live install with `latexmk`, `biber`, `subfiles`, `biblatex`.

```bash
latexmk -pdf -outdir=build main.tex          # the whole document → build/main.pdf
```

Individual modules and solution dossiers also compile standalone; unresolved cross-references to
other modules are expected in standalone builds.

---

# Instantiating this template

<!-- Delete everything below this line once the checklist is done. -->

Six steps, none of which deletes a record. The live planes ship empty and the worked example
lives in [`example/`](example/README.md), so instantiating this template is copying and
filling in — never removing history. Nothing needs renaming: `research/program/` is the control
directory in every repository built from this template, so no validator needs configuration to
find it.

`python3 scripts/check.py ready` is the checklist in executable form. Run it now: it will list
every one of these steps that is still outstanding, and it exits 0 when you are done.

1. **Name the program.** In [`research/program/ledger.yaml`](research/program/ledger.yaml), set
   `meta.program` to this program's id and `meta.scope` to one sentence naming the class of
   objects its nodes range over. That id is the only place the program's name is written down; it
   prefixes every checker message.

2. **Name the repository.** Replace `{{REPO_TITLE}}` above and the placeholders in
   [`main.tex`](main.tex) (title, subtitle, author, abstract).

3. **State the target and give it a node.** Write the question this repository is organized
   around in [`modules/`](modules/), inside the theorem environment matching its kind, under a
   `\label`. Add a ledger node with that id, that `kind`, and a one-line `summary`. Copy
   [`example/modules/00-overview.tex`](example/modules/00-overview.tex) and
   [`example/research/program/ledger.yaml`](example/research/program/ledger.yaml) for the shape.
   This is the first gate a sustained search crosses, because the brief and the portfolio both
   have to resolve to it.

4. **Write the problem brief.** Copy
   [`example/research/program/brief.md`](example/research/program/brief.md) to
   `research/program/brief.md` and fill it in. It is the one document that supplies mathematical
   pressure: the exact target and its negation, what counts as a complete proof and a complete
   refutation, the edge cases a reviewer must check, the equivalent-strength traps, and a budget
   policy that permits an honest unresolved outcome. The harness remembers and certifies; the
   brief is what makes the search sharp. Do not start a sustained search without one.

5. **Add program constraints, if any.** [`CLAUDE.md`](CLAUDE.md) ships twelve universal hard
   constraints. Anything specific to this repository's mathematics goes in the *Program
   constraints* section as `P1, P2, …` — kept separate so that a fork can drop them without
   leaving a `Reserved` hole in the universal list. Merge barriers belong here, and the
   `synthesizer` role should name the same owner.

6. **Trim and extend the roster.** [`.claude/agents/`](.claude/agents/README.md) ships four
   core roles — `scout`, `researcher`, `reviewer`, `synthesizer` — and three optional
   specialists, `numerics`, `literature-scout` and `janitor`. Delete the specialists you will
   not use. Prefer a new assignment *lens* in [`.claude/lenses/`](.claude/lenses/README.md) to
   a new role; [`.claude/agents/MAINTAINING.md`](.claude/agents/MAINTAINING.md) is the guide.
   Either way, finish with
   `python3 scripts/check.py --write-codex && python3 scripts/check.py --lane roles`, which
   also deletes the adapter of a role you removed.

Then `./scripts/check.sh` and `python3 scripts/check.py ready` should both pass, and you can
delete this section.

**Optional, when the work asks for it.** Create
[`research/program/portfolio.yaml`](research/program/portfolio.yaml) when several routes, agents
or sessions are in flight — copy
[`example/research/program/portfolio.yaml`](example/research/program/portfolio.yaml). Keep or
delete `experiments/numerics/targets/example.py` as you like: it is reference code the numerics
test suite exercises, not a research record. `example/` itself can stay indefinitely; it is
checked separately and touches nothing.

## What to fill in as the program grows

These ship as skeletons on purpose — a wrong entry is worse than an empty table:

- [`preamble.tex`](preamble.tex) — add macros to the *program macros* block; the
  core block above it stays diffable against the template. A macro standing for a fixed
  normalization needs a `kind: definition` node, not just a macro.
- [`references.bib`](references.bib) — empty. A node with `provenance: literature` needs keys here
  first.
- [`research/instances.md`](research/instances.md) — the shared adversarial battery; instances
  enter only through the `synthesizer`.
