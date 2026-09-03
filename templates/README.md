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
| [`checkpoint.md`](checkpoint.md) | `research/explorations/<date>-<slug>.md` | `python3 scripts/new.py checkpoint <slug>` |
| [`solution.tex`](solution.tex) | `solutions/<ledger-id>.tex` | `python3 scripts/new.py dossier <node-id>` |
| [`module.tex`](module.tex) | `modules/<nn>-<slug>.tex` | `python3 scripts/new.py module <slug>` |
| [`node.yaml`](node.yaml) | **stdout only** | `python3 scripts/new.py node <id> --kind <kind>` |

`node.yaml` is the exception on purpose. `research/program/ledger.yaml` is a single-file
write-contention point with one writer (`CLAUDE.md` constraint 1), so the scaffolder
prints the node and the orchestrator pastes it. No tool edits that file behind the
orchestrator's back.

`scripts/new.py` never overwrites an existing file; it refuses and says so. It writes
files and nothing else — `scripts/check.py` stays read-only, which is why the two are
separate commands.

## Placeholder tokens

`{{TARGET_NODE}}`, `{{NODE}}`, `{{KIND}}`, `{{SLUG}}`, `{{TITLE}}`, `{{FILE}}`,
`{{DATE}}`. `new.py` substitutes the ones it knows from its arguments and leaves the rest
for you.

The instructional prose in `brief.md` is itself a placeholder: `python3 scripts/check.py
ready` fails while those sentences are still in `research/program/brief.md`, which is how
a copied-but-unwritten brief is caught. Filling the sections in is what clears it.
