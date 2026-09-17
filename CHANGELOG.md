# Changelog

All notable changes to the conjecture-search template are recorded here. Each released section
corresponds to the Git tag with the same version.

The template is pre-stable. Until `v1.0.0`, increment the minor version for a feature or a change
that requires forks to migrate, and increment the patch version for a backward-compatible fix.
Batch related breaking changes into one minor release. Publish `v1.0.0` only when the template
contract is intended to remain stable; from that point onward, use standard semantic versioning.

## [Unreleased]

This release makes MyST Markdown the source of the manuscript and of the proof dossiers.
Mathematics stays LaTeX, the PDF is still built by LaTeX, and `references.bib` stays; what
changes is that a claim is a typed node MyST parses rather than a `\label` a regular
expression finds. It also reduces the ledger kinds to eight and removes the old website.
Every fork has to migrate: see *Migrating a fork* below.

### Added

- Add the MyST project: `myst.yml` and `index.md` at the root and in `example/`, modules
  under `modules/*.md`, dossiers under `solutions/*.md`, the scaffolds `templates/module.md`
  and `templates/solution.md`, and the local, `pdflatex`-based export template
  `templates/latex/`. `package.json` pins `mystmd` 1.10.1 and `npm ci` applies
  `patches/mystmd+1.10.1.patch`, which fixes two LaTeX export bugs. Without it MyST silently
  drops every `prf:assumption`, the fix proposed upstream in jupyter-book/mystmd#3031. It
  also escapes a code block as mathematics, which puts a space before every hyphen
  (`2026 -09 -03`) and strips the first line's indentation; the patch writes the block
  verbatim, and no upstream fix is proposed yet. Drop each hunk once a release carries its
  fix.
- Add `docs/SPECIFICATION.md`, a descriptive technical specification of the whole harness
  for human readers: domains, file genres and their fields, roles and permissions,
  workflows, and what every checker lane enforces, with excerpts from the worked example.
  It is not contract, and each section names the file that owns its rules. It is its own
  MyST project (`docs/myst.yml`): `cd docs && npx myst build --pdf`.
- Add `scripts/checks/manuscript.py`, which builds the MyST site content and reads its tree.
  Every MyST error, unknown directive or role, unresolved cross-reference, duplicate label,
  and pair of labels colliding on one HTML anchor (`a:b-c` and `a-b:c`) is a `core` error.
- `./scripts/check.sh` builds the PDF of the manuscript and of every dossier, in the
  repository and in `example/`, and fails on a LaTeX error or on a claim missing from the
  exported manuscript — two failures `myst build --pdf` does not report. It installs MyST
  with `npm ci` when it can and fails when it cannot.
- Add a `check` workflow that installs MyST and validates the repository, the worked example
  and the checker's test suite on pull requests into the default branch.
- Add a minimal `site` workflow that, on manual dispatch only, validates the repository and
  publishes `myst build --html` to GitHub Pages.

### Changed

- **Breaking:** `scripts/check.py` reads the manuscript through MyST. A node's anchor is a
  `:label:` on the `prf:<kind>` directive in `modules/*.md` matching its `kind`; `file:` names
  a `.md` file. MyST is required, and the checker now writes MyST's gitignored `_build/` —
  still nothing the repository tracks.
- **Breaking:** a dossier is `solutions/<id>.md`, and its header is YAML front matter —
  `ledger-node` (an id or a list), `refines`, `bounded_by`, `author`, `date`, plus the MyST
  fields `title`, `subtitle`, `short_title`, `label`, `exports` and `numbering` — instead of
  the `% === SOLUTION HEADER` comment block. A review written before this release that names
  `solutions/<id>.tex` still covers `solutions/<id>.md`, so no immutable review needs
  rewriting.
- **Breaking:** reduce the ledger `kind` vocabulary from ten to eight: `theorem`, `lemma`,
  `proposition`, `corollary`, `conjecture`, `definition`, `example`, `assumption`. Being an
  obstruction is a role carried by the edges, not a form: `bounded_by` may name any proved
  node, `heuristic_barriers` any open node, and a brief or portfolio may not target a node
  another node cites in either. Constraint 5 changes in wording only.
- **Breaking:** `check.py publish-ready` looks for its placeholders in `myst.yml` and in the
  abstract at the top of `modules/00-overview.md`. `new.py module` and `new.py dossier` write
  MyST, and `new.py node --file` defaults to `00-overview.md`.
- `references.bib` ships empty, because MyST refuses a bibliography holding only comments; its
  guidance moved to `myst.yml`.

### Removed

- **Breaking:** the LaTeX source: `main.tex`, `preamble.tex`, `.latexmkrc`, `modules/*.tex`,
  `templates/module.tex`, `templates/solution.tex`, and the LaTeX output setting in
  `.vscode/settings.json`.
- **Breaking:** `check.py dossiers`, which existed to feed the old LaTeX build.
- **Breaking:** the derived website: `site/`, `scripts/site.py`, its Pages workflow and
  `docs/PUBLISHING-THE-SITE.md`. The MyST site replaces it; ledger and portfolio views may
  return on top of it later. The issue forms stay, as the public inbox constraint 12 fences.
- The `question` and `obstruction` ledger kinds, and their LaTeX environments.

### Fixed

- The `researcher`, `synthesizer`, `numerics` and `literature-scout` write surfaces name a
  checkpoint `YYYY-MM-DD-<role>-<scope>-<run-id>.md`, as `.claude/agents/README.md` requires,
  instead of `YYYY-MM-DD-<slug>.md`. Regenerate the Codex adapters with
  `python3 scripts/new.py agents`.
- Stale LaTeX-era wording: the proof-review example in `research/reviews/README.md` names a
  `.md` dossier, and promotion in `research/explorations/README.md` puts a `:label:` on a
  `prf:<kind>` directive rather than a `\label` in an environment.
- The `templates/solution.md` header comment lists every MyST page field the checker accepts,
  and a `roles.py` comment no longer claims the `heavy` tier is `max` on Claude.

### Migrating a fork

1. **Kinds.** Rewrite each `question` node as a `conjecture` stated in the direction the search
   tries to establish, and each `obstruction` node as the form it has: `theorem`,
   `proposition` or `lemma` when proved, `conjecture` when open. Id prefixes are conventions
   and need not change.
2. **Toolchain.** Copy `package.json`, `package-lock.json`, `patches/`, `myst.yml`, `index.md`
   and `templates/latex/` from the template, add `_build/` and `node_modules/` to
   `.gitignore`, and run `npm ci`. Move the macros from `preamble.tex` to `math:` in
   `myst.yml`, and the title, subtitle and author from `main.tex` to its `project:`.
3. **Modules.** Convert each `modules/*.tex` to `modules/*.md` by hand: a claim environment
   becomes a `prf:<kind>` directive with `:label: <id>`, `\ref{<id>}` becomes `[](#<id>)`,
   `\section` becomes a heading, and the abstract becomes a `+++ {"part": "abstract"}` block in
   the first module. `myst build <file>.tex --md` is not a shortcut: it drops every theorem
   environment. Point each ledger `file:` at the `.md`.
4. **Dossiers.** Convert each `solutions/*.tex` the same way, turn its comment header into
   front matter, and point each `proofs[].artifact` at the `.md`. Leave the reviews alone.
5. **Records.** Checkpoints and reviews already written keep their `.tex` paths: they are
   append-only, and the `docs` lane exempts them.
6. Delete `main.tex`, `preamble.tex` and `.latexmkrc`, then run `./scripts/check.sh`.

## [0.1.0] - 2026-09-04

### Added

- Require explicitly delimited metadata blocks in proof and refutation dossiers, so narrative
  comments cannot be interpreted as header fields.
- Treat numbered equations, alignments, figures, and tables nested inside claims as structural
  labels owned by those environments.

### Changed

- Replace control-plane decision records with this package-level changelog and Git tags.
- Keep the documentation link checker focused on live documentation while exempting immutable
  search checkpoints and proof reviews.
- Make capability-pack installation tests independent of which packs are installed in the host
  repository.
- Validate numerical `instance` observations at artifact write time.
- Correct live role and lens references to the current universal constraint order.

### Removed

- Remove the constraint-citation index and its `check.py constraints` command.
- Remove the `decisions/` control-plane archive and its contribution workflow.

### Fixed

- Keep installed capability-pack roles synchronized with their pack sources.
- Remove the synthesizer's stale reference to the retired decisions archive.
- Verify the byte-preserved source and checksum declared by migrated numerical artifacts.

[Unreleased]: https://github.com/numina-functional-inequalities/conjecture-search-template/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/numina-functional-inequalities/conjecture-search-template/releases/tag/v0.1.0
