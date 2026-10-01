# Conjecture search template

<!-- Replace this paragraph: what mathematical object this repository studies, which
     question it is organized around, and what is proved versus open. The ledger, not
     this file, is the source of truth. -->

A MyST Markdown manuscript together with a harness for **sustained conjecture search**:
proving or refuting one hard statement over many sessions and several agents, while keeping
track of what is claimed, what the search is doing, and why.

Why the template exists, and how to judge a change to it, is in [`goal.md`](goal.md). The
rules are in [`SPECIFICATION.md`](SPECIFICATION.md). Start every session that edits the
repository by reading it.

## Layout

| path | holds |
|---|---|
| [`modules/`](modules/) | the manuscript, the text a reader reads: every claim as a labelled `prf:` directive, in prose written for a mathematician |
| [`research/program/`](research/program/) | the ledger; the brief once a search runs, the portfolio of routes from the first route |
| [`research/explorations/`](research/explorations/) | dated checkpoints and candidate statements |
| [`research/reviews/`](research/reviews/) | independent proof reviews |
| [`research/runs/`](research/runs/) | computation scripts and their output |
| [`solutions/`](solutions/) | standalone proof and refutation dossiers |
| [`.claude/agents/`](.claude/agents/), [`.codex/agents/`](.codex/agents/) | the three roles: `researcher`, `reviewer` and `writer`, for Claude Code and for Codex |
| [`templates/`](templates/) | an empty copy of each file genre |
| [`example/`](example/README.md) | one complete worked search, a fixture to copy from |

## Setup and verify

Needs [uv](https://docs.astral.sh/uv/), which provisions Python and PyYAML from
`pyproject.toml`, and Node.js 18+ for MyST (pinned in `package.json`):

```bash
npm ci
./scripts/check.sh               # the checker, the worked example, the unit tests
uv run scripts/check.py         # full check; 0 errors required before any status change
uv run scripts/check.py --fast  # research state only, no MyST build
uv run scripts/check.py --statements   # before and after a writer's pass: must not change
uv run scripts/check.py --drafts       # the draft dossiers, never published
npx myst start                   # read the manuscript and the proofs in a browser
```

Agents run the checker and MyST many times per session. Approve those commands once and
for good (`uv run scripts/check.py` and `node_modules/.bin/myst`): in Claude Code, as
`allow` rules in `.claude/settings.json`; in Codex, by accepting the prefix rule offered
on the first escalation. Each approval asked again costs a turn, and in Codex a call to
its reviewing model. How agents are launched and awaited is *Orchestration* in
`SPECIFICATION.md`.

The first check in a fresh clone downloads MyST's site theme into `_build/`. A green check
establishes structure only. Each statement shows its status, read from the ledger by
[`scripts/status.mjs`](scripts/status.mjs). The `pages` workflow publishes the manuscript
and the certified dossiers to GitHub Pages when dispatched by hand, after a person has
read them.

---

# Instantiating this template

<!-- Delete everything below this line once the checklist is done. -->

1. **State the target.** Copy [`templates/module.md`](templates/module.md) to
   `modules/01-target.md` and write the statement in the `prf:` directive matching its kind,
   under a `:label:`.
2. **Give it a ledger node.** Paste [`templates/node.yaml`](templates/node.yaml) under
   `nodes:` in [`research/program/ledger.yaml`](research/program/ledger.yaml).
3. **Write the brief.** Copy [`templates/brief.md`](templates/brief.md) to
   `research/program/brief.md` and rewrite every section for your target, including any
   rule specific to your program under its traps.
4. **Name things.** Replace the title above, the placeholders in [`myst.yml`](myst.yml) and
   the abstract in [`modules/00-overview.md`](modules/00-overview.md).
5. **Write the overview.** Replace the prose of
   [`modules/00-overview.md`](modules/00-overview.md) for a reader, and put the contact
   address there and in
   [`.github/ISSUE_TEMPLATE/config.yml`](.github/ISSUE_TEMPLATE/config.yml); then delete
   this section.
6. **Open it to contributions.** Set `github:` in [`myst.yml`](myst.yml) to the
   repository URL, so that each statement links to the issue forms, and replace
   `<repository URL>` in `config.yml`. To use Discussions, enable them and create the
   categories *Announcements*, *Q&A* (answerable), *Ideas* and *Literature* in the
   repository settings; the forms in `.github/DISCUSSION_TEMPLATE/` match the last three.
   Otherwise delete that directory and the Discussions link of `config.yml`.

Create `research/program/portfolio.yaml` from
[`templates/portfolio.yaml`](templates/portfolio.yaml) with the first route. Add
macros to `myst.yml` under `math:`, and BibTeX entries to `references.bib` before any
node cites them in `references:`.
