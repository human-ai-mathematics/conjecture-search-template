# Conjecture search template

<!-- Replace this paragraph: what mathematical object this repository studies, which
     question it is organized around, and what is proved versus open. The ledger, not
     this file, is the source of truth. -->

A MyST Markdown manuscript together with a harness for **sustained conjecture search**:
proving or refuting one hard statement over many sessions and several agents, while keeping
track of what is claimed, what the search is doing, and why.

The rules are in [`SPECIFICATION.md`](SPECIFICATION.md). Start every session that edits the
repository by reading it.

## Layout

| path | holds |
|---|---|
| [`modules/`](modules/) | the manuscript: every claim, as a labelled `prf:` directive |
| [`research/program/`](research/program/) | the ledger; the brief once a search runs, the portfolio of routes from the first route |
| [`research/explorations/`](research/explorations/) | dated checkpoints and candidate statements |
| [`research/reviews/`](research/reviews/) | independent proof reviews |
| [`research/runs/`](research/runs/) | computation scripts and their output |
| [`solutions/`](solutions/) | standalone proof and refutation dossiers |
| [`site/`](site/) | the reader's site: exposition for mathematicians, at milestones |
| [`.claude/agents/`](.claude/agents/) | the three roles: `researcher`, `reviewer` and `writer` |
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
uv run scripts/check.py --stamp site/results.md   # after rereading a site page
uv run scripts/check.py --drafts                  # the draft dossiers, never published
npx myst start                   # read the site, the dossiers and the manuscript in a browser
```

The first check in a fresh clone downloads MyST's site theme into `_build/`, and warns on
every template placeholder still to fill in. A green check establishes structure only; a
stale or unfinished site page is a warning. The `site` workflow publishes the HTML site to
GitHub Pages when dispatched by hand: it leaves out the draft dossiers, and publishes only
if no site page is stale or unfinished (`check.py --site-strict`).

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
5. **Open the site.** Write [`site/index.md`](site/index.md) and
   [`site/problem.md`](site/problem.md) for a reader, put the contact address in
   [`site/about.md`](site/about.md) and
   [`.github/ISSUE_TEMPLATE/config.yml`](.github/ISSUE_TEMPLATE/config.yml), and stamp the
   pages (`uv run scripts/check.py --stamp site/*.md`). The check warns on any placeholder
   left; then delete this section.

Create `research/program/portfolio.yaml` from
[`templates/portfolio.yaml`](templates/portfolio.yaml) with the first route. Add
macros to `myst.yml` under `math:`, and BibTeX entries to `references.bib` before any
node cites them in `references:`.
