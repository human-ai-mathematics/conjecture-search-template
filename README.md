# {{REPO_TITLE}}

<!-- Replace this paragraph: what mathematical object this repository studies, what
     question it is organized around, and what a reader should expect to find proved
     versus open. Keep it honest — the ledger, not this file, is the source of truth. -->

This repository contains a LaTeX manuscript together with a harness for **sustained conjecture
search**: proving or refuting one hard statement, over many sessions and several agents, while
keeping track of what is claimed, what the search is doing, and why.

## The shape of the repository

Six planes, each with one source of truth:

| plane | owns | source |
|---|---|---|
| manuscript | accepted mathematical statements | [`main.tex`](main.tex), [`modules/`](modules/) |
| ledger | logical state and graph edges | [`research/program/ledger.yaml`](research/program/ledger.yaml) |
| portfolio | live search: families, routes, blockers | [`research/program/portfolio.yaml`](research/program/portfolio.yaml) |
| proofs | standalone, independently checkable dossiers | [`solutions/`](solutions/) |
| numerics | provenance-stamped diagnostic artifacts | [`experiments/`](experiments/), [`research/runs/`](research/runs/) |
| history | checkpoints, candidates, reviews — append-only | [`research/`](research/), [`decisions/`](decisions/) |

The separation that matters most:

> Ledger = what is mathematically claimed. Portfolio = what the search is doing.
> Checkpoints = why the portfolio changed.

A `\label` in `modules/` **is** a ledger node id. That coupling is what
[`scripts/check.py`](scripts/check.py) enforces, and it is why a statement cannot drift from
its recorded status without something going red.

A statement that has not earned a node yet is a *candidate*, and it lives in the front matter
of the checkpoint that proposed it — never in a registry of its own ([`CLAUDE.md`](CLAUDE.md)
constraint 8).

Layers activate structurally, not by a mode flag: a repository with no portfolio has no
portfolio rules, and the checker validates only the planes that exist. The gates are listed in
[`CLAUDE.md`](CLAUDE.md); `AGENTS.md` is a symlink to it, so Claude Code and Codex receive the
same contract. Agent roles and their write permissions are in
[`.claude/agents/`](.claude/agents/README.md); the strategies they are pointed at are in
[`.claude/lenses/`](.claude/lenses/README.md).

## Verify

```bash
./scripts/check.sh                        # everything, in the order that fails fastest
./scripts/check.sh --fast                 # skip the LaTeX build

python3 scripts/check.py                  # 0 errors required after any ledger edit
python3 scripts/check.py --plane core     # core|proofs|checkpoints|portfolio|numerics|roles
python3 scripts/check.py status           # the live frontier
python3 scripts/check.py portfolio        # the live search
python3 scripts/check.py checkpoints      # current heads of durable memory
python3 scripts/check.py node <id>        # one node: deps, consumers, fences
python3 scripts/check.py candidates       # statements proposed but not yet nodes
python3 scripts/check.py --write-codex    # regenerate the Codex role adapters
```

A green check establishes structure only. It says nothing about whether a proof is correct
(`CLAUDE.md` constraint 4).

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

Seven mechanical steps. Nothing needs renaming: `research/program/` is the control directory in
every repository built from this template, so no validator needs configuration to find it.

1. **Name the program.** In [`research/program/ledger.yaml`](research/program/ledger.yaml), set
   `meta.program` to this program's id and `meta.scope` to one sentence naming the class of
   objects its nodes range over. That id is the only place the program's name is written down; it
   prefixes every checker message.

2. **Name the repository.** Replace `{{REPO_TITLE}}` above and the placeholders in
   [`main.tex`](main.tex) (title, subtitle, author, abstract).

3. **Write the problem brief.** [`research/program/brief.md`](research/program/brief.md) is the
   one document that supplies mathematical pressure: the exact target and its negation, what
   counts as a complete proof and a complete refutation, the edge cases a reviewer must check,
   the equivalent-strength traps, and a budget policy that permits an honest unresolved
   outcome. The harness remembers and certifies; the brief is what makes the search sharp.
   Rewrite the shipped one for your target rather than deleting it.

4. **Add program constraints, if any.** [`CLAUDE.md`](CLAUDE.md) ships twelve universal hard
   constraints. Anything specific to this repository's mathematics goes in the *Program
   constraints* section as `P1, P2, …` — kept separate so that a fork can drop them without
   leaving a `Reserved` hole in the universal list. Merge barriers belong here, and the
   `synthesizer` role should name the same owner.

5. **Trim and extend the roster.** [`.claude/agents/`](.claude/agents/README.md) ships four
   core roles — `scout`, `researcher`, `reviewer`, `synthesizer` — and three optional
   specialists, `numerics`, `literature-scout` and `janitor`. Delete the specialists you will
   not use. Prefer a new assignment *lens* in [`.claude/lenses/`](.claude/lenses/README.md) to
   a new role. Either way, finish with
   `python3 scripts/check.py --write-codex && python3 scripts/check.py --plane roles`, which
   also deletes the adapter of a role you removed.

6. **Confirm it is green.** `./scripts/check.sh` should pass on a fresh clone, before you have
   written anything.

7. **Delete the worked example in one commit.** It exists so that step 6 passes and so each
   artifact genre ships with one instance to copy. It is:

   - `modules/00-overview.tex` (the three seed `\label`s)
   - the three nodes in `research/program/ledger.yaml`
   - `research/program/portfolio.yaml` (rewrite for your search, or delete it until several
     routes are in flight)
   - `solutions/prop-example.tex`
   - `research/reviews/2026-09-01-prop-example-proof-review.md`
   - `research/explorations/2026-09-02-example-exploration.md` and the
     `research/runs/` artifact it cites
   - `research/explorations/2026-09-03-example-dedup.md`
   - `research/program/brief.md` (rewrite it for your target; do not start a sustained
     search without one)
   - `experiments/numerics/targets/example.py` and its registry entry

   Delete this section at the same time.

## What to fill in as the program grows

These ship as skeletons on purpose — a wrong entry is worse than an empty table:

- [`preamble.tex`](preamble.tex) — add macros to the *program macros* block; the
  core block above it stays diffable against the template. A macro standing for a fixed
  normalization needs a `kind: definition` node, not just a macro.
- [`references.bib`](references.bib) — empty. A node with `provenance: literature` needs keys here
  first.
- [`research/instances.md`](research/instances.md) — the shared adversarial battery; instances
  enter only through the `synthesizer`.
