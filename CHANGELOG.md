# Changelog

Notable changes to the conjecture-search template. Each released section corresponds to
the Git tag with the same version. The template is pre-stable: until `v1.0.0`, a minor
version may require forks to migrate, and a patch version is a backward-compatible fix.

## [Unreleased]

## [0.2.0] - 2026-09-29

The manuscript moves to MyST Markdown, the harness is cut down to what protects the status
of a result, and a reader's site for mathematicians sits on top of it. Forks migrate: most
items below are breaking.

### Contract and roles

- `SPECIFICATION.md` is the single contract, built on six principles; the per-directory
  READMEs, the schemas and `templates/README.md` are merged into it.
- Three roles: `researcher`, `reviewer` and the new `writer`. The orchestrator takes over
  the portfolio. A researcher works a mission — a question and its expected result — from
  a starting lens it may leave; early critique of an unfinished idea is distinct from
  review. A reviewer's independence is a fresh context, not a different name.
- The handoff has three optional fields: `files`, `deltas`, `next`.

### Manuscript, ledger and certification

- The manuscript (`modules/`) and the dossiers (`solutions/`) are MyST Markdown: a claim
  is a `prf:<kind>` directive whose `:label:` is its ledger id.
- A ledger node is `id`, `status` and its edges (`depends_on`, `assumes`, `bounded_by`,
  `references`, `proofs`, `refuted_by`); everything else is read from the manuscript.
- A proof record carries `review` or `accepted_by`. Its certification is pinned by
  fingerprints to the dossier and the statements it was checked against; editing any of
  them lifts it. `check.py --fingerprint <dossier>` prints the block to record.

### Search state

- Every route lives in `research/program/portfolio.yaml` (states `active | blocked |
  closed`, optional `next`); the brief holds the target, its negation, traps and
  neighbourhood, but no route.
- A checkpoint records what was learned under four headings; a candidate is proposed in
  `candidates:` and ended by `closes:`. Throwaway computation needs no file; a run is a
  seeded script under `research/runs/`, from `templates/run.py`.

### Checker

- `scripts/check.py` has no subcommands: it validates and prints the summary a resumed
  session starts from. `--fast` skips the MyST build; `--root` checks another tree.
  `scripts/new.py` is removed: copy from `templates/`.

### Reader's site

- `site/` tells a mathematician what the search found: the problem, the results with the
  idea of each proof, a card per open problem. It replaces the root `index.md`; the
  dossiers and the manuscript follow it in the table of contents.
- A page that states a status lists what it rests on (`relies-on`); `check.py --stamp`
  records their status and fingerprint and writes the lists of `open.md` and `proofs.md`.
  A stale page, or one still carrying a template placeholder, is a warning, and an error
  under `--site-strict`. The check sees what a page declares, not whether it is faithful.
- The `site` workflow publishes by hand only, and leaves out the draft dossiers
  (`check.py --drafts`).
- GitHub issue forms for an idea, a counterexample and a correction.

### Removed

- PDF export, `experiments/`, `packs/`, `research/instances.md`, the Markdown link
  checker, and the `numerics`, `synthesizer` and `literature-scout` roles.

### Fixed

- A checkpoint can close only a candidate an earlier checkpoint proposed.
- A non-string entry in a node's `references` is reported instead of crashing the checker.

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

[Unreleased]: https://github.com/numina-functional-inequalities/conjecture-search-template/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/numina-functional-inequalities/conjecture-search-template/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/numina-functional-inequalities/conjecture-search-template/releases/tag/v0.1.0
