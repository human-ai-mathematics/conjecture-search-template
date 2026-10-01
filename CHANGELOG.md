# Changelog

Notable changes to the conjecture-search template. Each released section corresponds to
the Git tag with the same version. The template is pre-stable: until `v1.0.0`, a minor
version may require forks to migrate, and a patch version is a backward-compatible fix.

## [Unreleased]

### Added

- `.codex/agents/` defines the three roles for Codex, mirroring `.claude/agents/`; the
  README and `SPECIFICATION.md` name both directories.
- Each proved statement shows who certified it: *agent review (model, date)* or *reviewed
  by* a human, linked to the review report on GitHub, or *accepted by* a human. A proved
  node on `references` alone shows *Established in the literature* instead of *Proved*.
  `proofs.md` explains the three kinds of certification to the reader.
- An open theorem, lemma, proposition or corollary resting on `references` shows
  *Preprint, not yet checked here* instead of *Not settled here*: a source announces it,
  and neither the field nor the project has checked it yet. An open conjecture keeps
  *Not settled here*.
- The writer gives a manuscript whose overview outgrows a first reading a short welcome
  page, `modules/index.md`: the question, the main results, the parts and reading paths.
  How the modules are organised and how results are checked move there from the overview.

### Changed

- `reviewer`, every `authors` entry and `accepted_by` are identities
  `<who>, <model or human>, <YYYY-MM-DD>`, which the checker validates; `accepted_by` must
  be a human's, and the reviewer's `<who>` must be no author's. Forks migrate: rewrite
  each review's `reviewer` and `authors` in that form (`unknown` for an unrecorded model,
  the filename's date when no other is known). The review fields are not fingerprinted,
  so no certification lapses.

## [0.4.0] - 2026-09-30

Each statement names itself and invites a contribution, and `goal.md` says what the
template is for. Forks migrate: set `github:` in `myst.yml`, rename the `problem` and
`where` fields of their issue forms to `statement`, create the Discussions categories by
hand, and recompute with `check.py --fingerprint` the certifications of the statements that
link to a section on another page.

### Added

- `goal.md` states what the template is for: organize an AI-driven search on a
  conjecture, make every status trustworthy, and open the research to mathematicians; with
  criteria of success, what is out of scope, how to judge a change to the template, and
  what a program may adapt and which guarantees it keeps.
- Each statement shows its label after its status, so that a reader can name it. When
  `project.github` in `myst.yml` names the repository, `scripts/status.mjs` also links
  each statement to the issue forms with its label filled in: *Idea* and *Counterexample*
  on an open statement, *Correction* on any other. The three forms share the field id
  `statement`, which the idea and correction forms called `problem` and `where`.
- `.github/DISCUSSION_TEMPLATE/` holds forms for the Discussions categories *Q&A*,
  *Ideas* and *Literature*; `config.yml` links to Discussions. *Contributions* in
  `SPECIFICATION.md` says how issues and discussions enter the search. Forks: set
  `github:` in `myst.yml`, rename the `problem` and `where` fields of their issue forms
  to `statement`, and create the categories by hand.

### Fixed

- A statement's fingerprint ignores the heading text of a section it links to on another
  page: MyST renders `[](#sec:x)` there as a `link`, which the fingerprint now reads as a
  pointer to `sec:x`, as it already did a cross-reference. Renaming such a heading no
  longer lifts a certification. The fingerprint of a statement holding such a link
  changes once: a fork recomputes the certifications concerned
  (`check.py --fingerprint`), since the statement itself did not change.

## [0.3.0] - 2026-09-30

The reader's site is removed: the manuscript is the one text a reader reads. Forks
migrate: delete `site/`, copy the `toc:` and `plugins:` of `myst.yml`, add `proofs.md`,
run `npm ci`, and move what the site told a reader into the prose of `modules/`.

### Changed

- `modules/` is written for a mathematician. The content of a labelled directive, its
  title included, is the statement and stays the orchestrator's; the prose around it, the
  headings and the split into files are the `writer`'s, which now works on `modules/`.
- Each statement shows its status, read from the ledger at build time by the MyST plugin
  `scripts/status.mjs` (new dev dependency `js-yaml`). Prose never states a status; the
  reviewer's `sync` lens checks it. The ledger's `open` shows as *Not settled here*: it
  says what this project has not established, not what the literature leaves open.
- `check.py --statements` prints every statement's fingerprint; it is run before and after
  a writer's pass, and must not change.
- A statement's fingerprint ignores the page a cross-reference's target lives on, and the
  displayed status, so a statement moved to another module lifts no certification.
- `templates/module.md` lists the optional paragraphs of a module: idea of the proof,
  limits, why it matters, evidence, where to start, what remains. The `writer` says
  before a statement the project has not settled whether it is a research problem, and
  never presents as undecided what an easy argument decides.
- The table of contents lists the manuscript, then the full proofs after `proofs.md`. The
  `site` workflow is renamed `pages`.

### Removed

- `site/`, `templates/site/`, `scripts/checks/site.py`, `check.py --stamp` and
  `--site-strict`, `relies-on` and `checked`, the stale and placeholder warnings, and the
  summary's `site:` lines.

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

[Unreleased]: https://github.com/numina-functional-inequalities/conjecture-search-template/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/numina-functional-inequalities/conjecture-search-template/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/numina-functional-inequalities/conjecture-search-template/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/numina-functional-inequalities/conjecture-search-template/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/numina-functional-inequalities/conjecture-search-template/releases/tag/v0.1.0
