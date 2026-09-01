# {{REPO_TITLE}}

<!-- Replace this paragraph: what mathematical object this repository studies, what
     question it is organized around, and what a reader should expect to find proved
     versus open. Keep it honest — the ledger, not this file, is the source of truth. -->

This repository contains a LaTeX manuscript together with the research harness used to track open
claims, proofs, reviews, and numerical diagnostics.

## The shape of the repository

Five planes, each with one source of truth:

| plane | owns | source |
|---|---|---|
| manuscript | accepted mathematical statements | [`main.tex`](main.tex), [`modules/`](modules/) |
| ledger | logical state and graph edges | [`research/program/ledger.yaml`](research/program/ledger.yaml) |
| proofs | standalone, independently checkable dossiers | [`solutions/`](solutions/) |
| numerics | provenance-stamped diagnostic artifacts | [`experiments/`](experiments/), [`research/runs/`](research/runs/) |
| history | attempts, decisions, reviews — append-only | [`research/`](research/) |

A `\label` in `modules/` **is** a ledger node id. That coupling is what
[`scripts/check_ledger.py`](scripts/check_ledger.py) enforces, and it is why a statement cannot
drift from its recorded status without something going red.

The contribution rules are in [`CLAUDE.md`](CLAUDE.md); `AGENTS.md` is a symlink to it, so Claude
Code and Codex receive the same contract. Agent roles and their write permissions are in
[`.claude/agents/`](.claude/agents/README.md).

## Verify

```bash
./scripts/check.sh                        # everything, in the order that fails fastest
./scripts/check.sh --fast                 # skip the LaTeX build

python3 scripts/check_ledger.py           # 0 errors required after any ledger edit
python3 scripts/check_ledger.py status    # the live frontier
python3 scripts/check_ledger.py node <id> # one node: deps, consumers, fences
python3 scripts/check_agents.py           # role definitions and Codex adapters
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

Six mechanical steps. Nothing needs renaming: `research/program/` is the ledger directory in
every repository built from this template, so no validator needs configuration to find it.

1. **Name the program.** In [`research/program/ledger.yaml`](research/program/ledger.yaml), set
   `meta.program` to this program's id and `meta.scope` to one sentence naming the class of
   objects its nodes range over. That id is the only place the program's name is written down; it
   prefixes every checker message.

2. **Name the repository.** Replace `{{REPO_TITLE}}` above and the placeholders in
   [`main.tex`](main.tex) (title, subtitle, author, abstract).

3. **Add program constraints, if any.** [`CLAUDE.md`](CLAUDE.md) ships seven universal hard
   constraints. Anything specific to this repository's mathematics goes in the *Program
   constraints* section as `P1, P2, …` — kept separate so that a fork can drop them without
   leaving a `Reserved` hole in the universal list. Merge barriers belong here, and the
   `synthesizer` role should name the same owner.

4. **Add program-specific roles, if any.** The ten roles in
   [`.claude/agents/`](.claude/agents/README.md) are the backbone and mention no mathematics. A
   program usually wants one or two of its own. Write the file, add a roster row, then
   `python3 scripts/check_agents.py --write-codex && python3 scripts/check_agents.py`.

5. **Confirm it is green.** `./scripts/check.sh` should pass on a fresh clone, before you have
   written anything.

6. **Delete the worked example in one commit.** It exists so that step 5 passes and so each
   artifact genre ships with one instance to copy. It is:

   - `modules/00-overview.tex` (the three seed `\label`s)
   - the three nodes in `research/program/ledger.yaml` and the `obs:example` entry in
     `research/program/obstructions.md`
   - `solutions/prop-example.tex`
   - `research/reviews/2026-09-01-prop-example-proof-review.md`
   - `experiments/numerics/targets/example.py` and its registry entry

   Delete this section at the same time.

## What to fill in as the program grows

These ship as skeletons on purpose — a wrong entry is worse than an empty table:

- [`shared/notation.md`](shared/notation.md) — the fixed normalizations a statement's truth
  depends on.
- [`shared/preamble.tex`](shared/preamble.tex) — add macros to the *program macros* block; the
  core block above it stays diffable against the template.
- [`references.bib`](references.bib) — empty. A node with `status: imported` needs keys here
  first.
- [`research/knowledge/`](research/knowledge/) — lemmas earn a place after their second use;
  instances enter only through the `synthesizer`.
