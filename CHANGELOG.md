# Changelog

All notable changes to the conjecture-search template are recorded here. Each released section
corresponds to the Git tag with the same version.

The template is pre-stable. Until `v1.0.0`, increment the minor version for a feature or a change
that requires forks to migrate, and increment the patch version for a backward-compatible fix.
Batch related breaking changes into one minor release. Publish `v1.0.0` only when the template
contract is intended to remain stable; from that point onward, use standard semantic versioning.

## [Unreleased]

### Added

- Add a MyST source for the manuscript and the dossiers: `myst.yml` and `index.md` at the
  root and in `example/`, `modules/*.md`, `example/solutions/*.md`, `templates/module.md`,
  `templates/solution.md`, and a local LaTeX export template in `templates/latex/`.
  `package.json` pins `mystmd` 1.10.1 and applies `patches/mystmd+1.10.1.patch` on
  `npm ci`: without it, MyST's LaTeX export silently drops every `prf:assumption`.
  `references.bib` now ships empty, because MyST refuses a bibliography holding only
  comments; its guidance moved to `myst.yml`.
- Add a `check` workflow that validates the repository, the worked example and the checker's
  test suite on pull requests into the default branch.

### Removed

- **Breaking:** remove the LaTeX source of the manuscript: `main.tex`, `preamble.tex`,
  `.latexmkrc`, `modules/*.tex`, the dossier and module scaffolds `templates/*.tex`, and the
  editor's LaTeX output setting in `.vscode/settings.json`. `new.py module` and `new.py
  dossier` write `.md`, and `new.py node --file` defaults to `00-overview.md`. **Migrating a
  fork:** convert each module and dossier to MyST by hand — a claim environment becomes a
  `prf:<kind>` directive with `:label: <id>`, `\ref{<id>}` becomes `[](#<id>)`, a dossier's
  comment header becomes front matter — move your macros from `preamble.tex` to `math:` in
  `myst.yml`, point every ledger `file:` and `proofs[].artifact` at the `.md` path, and run
  `npm ci`. `myst build <file>.tex --md` is no shortcut: it drops every theorem environment.
  Checkpoints and reviews already written keep their `.tex` paths; they are append-only, the
  `docs` lane exempts them, and a review's `.tex` scope still covers the converted dossier.
- **Breaking:** remove the derived website: `site/`, `scripts/site.py`, the `site` Pages
  workflow and `docs/PUBLISHING-THE-SITE.md`. The manuscript becomes MyST Markdown in this
  release, and its rendering replaces the site; ledger and portfolio views may return on top
  of it later. The issue forms stay, as the public inbox constraint 12 fences.

### Changed

- **Breaking:** `scripts/check.py` reads the manuscript through MyST. It runs `myst build
  --site` and validates the tree MyST writes: a node's anchor is a `:label:` on the
  `prf:<kind>` directive in `modules/*.md`, and every MyST error, unknown directive or
  role, unresolved cross-reference, duplicate label and HTML-anchor collision
  (`a:b-c` against `a-b:c`) is a `core` error. The LaTeX label scanner is gone. MyST is
  now required: `npm ci`. The checker writes nothing tracked, only MyST's gitignored
  `_build/`.
- **Breaking:** a dossier is `solutions/<id>.md`, and its header is YAML front matter
  (`ledger-node`, `refines`, `bounded_by`, `author`, `date`, plus MyST's `title` and
  `exports`) instead of the `% === SOLUTION HEADER` comment block. `ledger-node` may be a
  list. A review written before this release that names `solutions/<id>.tex` still covers
  `solutions/<id>.md`, so an immutable review does not have to be rewritten.
- **Breaking:** `check.py publish-ready` looks for its placeholders in `myst.yml` and in the
  abstract of `modules/00-overview.md`. `check.py dossiers` is removed.
- **Breaking:** reduce the ledger `kind` vocabulary from ten to eight: `theorem`, `lemma`,
  `proposition`, `corollary`, `conjecture`, `definition`, `example`, `assumption`. `question`
  and `obstruction` are removed. Being an obstruction is a role carried by the edges, not a
  form: `bounded_by` may now name any proved node and `heuristic_barriers` any open node, and a
  portfolio or brief may not target a node another node cites in either list. Constraint 5
  keeps its number. **Migrating a fork:** rewrite each `question` node as a `conjecture` in
  the direction the search tries to establish; rewrite each `obstruction` node as the form it
  has — `theorem`, `proposition` or `lemma` when proved, `conjecture` when open — and change
  its manuscript environment to match. Id prefixes are conventions and need not change.
- Publish the site only on an explicit manual dispatch. The `site` workflow no longer runs on
  push or pull request, so no revision is built or deployed unless a human asks for it.

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
