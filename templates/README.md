# templates/ — the copy-me scaffolds

One minimal, fill-in-the-blank instance of each artifact the harness asks for. These
exist so that starting a search is copying a scaffold rather than editing the worked
example, which is instructional and whose relative paths are written for its own
location.

Two directories, two jobs, and they are not interchangeable:

| | `templates/` | [`example/`](../example/README.md) |
|---|---|---|
| holds | unfilled scaffolds with `{{PLACEHOLDER}}` tokens | one complete worked search |
| answers | "what are the required fields?" | "what does a good filled-in one look like?" |
| `check.py ready` | its placeholders are what `ready` looks for | passes — it is an instantiated repository |

Nothing here is validated by `scripts/check.py`: `templates/` is a top-level sibling, and
every checker glob is rooted at `modules/`, `research/`, `solutions/`, `.claude/` or
`.codex/`. A scaffold is inert until it is copied into place.

## What is here, and what emits it

| file | copy to | command |
|---|---|---|
| [`brief.md`](brief.md) | `research/program/brief.md` | `python3 scripts/new.py brief --target <node-id>` |
| [`portfolio.yaml`](portfolio.yaml) | `research/program/portfolio.yaml` | `python3 scripts/new.py portfolio --target <node-id>` |
| [`checkpoint.md`](checkpoint.md) | `research/explorations/<date>-<slug>.md` | `python3 scripts/new.py checkpoint <slug> --node <node-id>` |
| [`solution.md`](solution.md) | `solutions/<ledger-id>.md` | `python3 scripts/new.py dossier <node-id>` |
| [`module.md`](module.md) | `modules/<nn>-<slug>.md` | `python3 scripts/new.py module <slug> --node <node-id> --kind <kind>` |
| [`node.yaml`](node.yaml) | **stdout only** | `python3 scripts/new.py node <id> --kind <kind>` |

`node.yaml` is the exception on purpose. `research/program/ledger.yaml` is a single-file
write-contention point with one writer (`CLAUDE.md` constraint 1), so the scaffolder
prints the node and the orchestrator pastes it. No tool edits that file behind the
orchestrator's back.

Scaffold commands never overwrite an existing file; they refuse and say so. The separate
`new.py agents` command replaces only generated role frontmatter and Codex adapters.
`scripts/check.py` writes nothing the repository tracks, which is why validation and writing
are separate commands.

A checkpoint needs exactly one initial anchor: use `--node` without a portfolio, or
`--approach ap:<slug>` when the record explains one coordinated route. You may add the
other field by hand when the finished record genuinely engages both.

## `latex/` is not a scaffold

[`latex/`](latex/template.yml) is the LaTeX template every PDF export uses — the manuscript's
in [`../myst.yml`](../myst.yml), and each dossier's in its own front matter. Nothing copies it;
edit it in place to change how the PDFs look. It builds with `pdflatex`, and being local, an
export never downloads a template.

## Placeholder tokens

`{{TARGET_NODE}}`, `{{NODE}}`, `{{KIND}}`, `{{STATUS}}`, `{{SLUG}}`, `{{TITLE}}`,
`{{FILE}}`, `{{FILE_ID}}`, `{{DATE}}`, `{{ENGAGEMENT}}`. `new.py` substitutes the ones it knows from its
arguments and leaves the rest for you.

The instructional prose in `brief.md` is itself a placeholder: `python3 scripts/check.py
ready` fails while those sentences are still in `research/program/brief.md`, which is how
a copied-but-unwritten brief is caught. Filling the sections in is what clears it.
