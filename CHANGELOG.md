# Changelog

Notable changes to the conjecture-search template. The template is pre-stable: every
release below `v1.0.0` may require forks to migrate.

## [Unreleased]

The manuscript moves to MyST Markdown, and the harness is cut down to what protects the
status of a result. A reader's site, written for mathematicians, sits on top of it.

### Added

- The reader's site under `site/`: exposition for a mathematician who has never seen the
  repository — the problem, the results with the idea of each proof, and a card per open
  problem — with the dossiers and the manuscript after it in the table of contents.
  `templates/site/` holds its pages; `example/site/` is a finished one. See *Site page* in
  `SPECIFICATION.md`.
- A page records the status and statement fingerprint of each id it rests on
  (`relies-on`, `checked`). `check.py --stamp <page>` writes them and the block that shows
  them; a page whose record no longer matches is stale — a `WARN` during the search, an
  error under `check.py --site-strict`, which the `site` workflow now runs. Once there is a
  site, the summary also lists the proved and refuted nodes no page rests on.
- A candidate's statement has a fingerprint: the SHA-256 of its whitespace-normalized
  text.
- The `writer` agent (`.claude/agents/writer.md`), launched at milestones, as the new
  workflow step 8.
- GitHub issue forms for an idea on an open problem, a counterexample and a correction.
- `templates/solution.md` opens with an *Overview*, sets a `numbering` prefix and shows a
  folded proof, for the dossiers to come; existing dossiers are left as they are, since
  editing them lifts their certification.

### Changed

- **Breaking:** `index.md` is gone, at the root and in `example/`; the site starts at
  `site/index.md`, and the table of contents in `myst.yml` is now in parts: the site, the
  *Open problems*, *Full proofs* and *Precise statements*. A fork moves its landing text
  into `site/index.md` and copies the new `toc:`.
- **Breaking:** the manuscript (`modules/*.md`) and the dossiers (`solutions/*.md`) are MyST
  Markdown. A claim is a `prf:<kind>` directive whose `:label:` is its ledger id; the checker
  reads it through `myst build --site`. The ledger has eight kinds.
- **Breaking:** `SPECIFICATION.md` is the single contract. The per-directory READMEs, the
  ledger and portfolio schemas and `templates/README.md` are merged into it. The numbered
  hard and program constraints give way to six principles; each precise rule sits in the
  format it governs, and a program-specific rule goes under the brief's traps.
- **Breaking:** two roles, `researcher` and `reviewer`, with their lenses folded into their
  files. The orchestrator takes over the `synthesizer`'s portfolio work.
- **Breaking:** the ledger drops `meta`: it is `nodes:` alone. A ledger node is `id`,
  `status` and its edges. `kind`, `file` and `summary` are read from, or live in, the
  manuscript; `provenance` and `import_class` give way to `references` (a recent preprint
  is proved through a dossier and a review, like any result); `heuristic_barriers` merges
  into `bounded_by`; `implies` and `refines` are removed.
- **Breaking:** a proof record drops `mode`: it carries `review` or `accepted_by`. A review
  drops `nodes` (its dossier names them); a dossier's front matter is `title` and
  `ledger-node`. A refutation needs no prior candidate.
- **Breaking:** a certification is pinned to the versions it saw. A review's
  `fingerprints` map the dossier to its SHA-256 and each statement the proof is checked
  against — the node's own, its `depends_on` and `assumes`, the target it refutes — to a
  fingerprint of the claim as MyST parsed it, blind to wrapping, spacing and numbering. A
  human acceptance (`accepted_by`) carries the same `fingerprints`. Editing the dossier,
  the node's statement or a premise's statement lifts the certification until a new review
  or acceptance; `check.py --fingerprint <dossier>` prints the block to record. Reviews,
  checkpoints and the brief lose `type`, and reviews and checkpoints lose `date`: the
  filename carries it.
- **Breaking:** checkpoints lose `outcome`, `retires`, `promotes`, `nodes` and `approach`; a candidate is ended
  by `closes:`. The portfolio loses `target` (the brief owns it) and its states are
  `active | blocked | closed`; `reopen_if` is optional, and the checker flags a route
  whose blocker is settled. The brief no longer copies the target or lists routes.
- **Breaking:** the handoff has three fields, `files`, `deltas` and `next`; `outcome`,
  `next_role` and `portfolio_delta` are gone (a portfolio change is an ordinary delta).
- The workflow gives the orchestrator's session loop. The brief lists the routes in a
  *Routes* section while one agent works at a time; the portfolio is for parallel routes.
- A reviewer's independence is a fresh context, not a different name; `authors` and
  `reviewer` name a human, or an agent's role, model and date.
- `templates/run.py`: a PEP 723 run script whose `provenance()` writes the seed, the
  commit, the dirty flag and the versions as the first line of its `.jsonl` output.
- The worked example's fences are mathematics: the proved `prop:upper-constant` bounds the
  target and tells the brief where it is weakest, and the open `conj:weighted-upper`
  bounds `conj:weighted-example`. `conj:finite-battery` is removed.
- **Breaking:** `scripts/check.py` has no subcommands and no lanes: it validates and prints
  a summary. `scripts/new.py` is removed; copy from `templates/`.
- `check.py --fast` validates the research state without a MyST build, leaving the
  manuscript anchors and statement fingerprints unchecked; the full check, which CI runs,
  is required before a status change. Concurrent full checks of one tree take turns on
  `_build/` instead of deleting each other's output.
- The summary is what a resumed session starts from: each route's `next` test (a new
  optional portfolio field) and the latest checkpoint naming it, the draft dossiers no
  proof record names, and the latest checkpoint.
- Exploration is lighter. Throwaway computation is allowed; only a result something
  durable rests on must come from a committed run. An exact witness checked by hand goes
  straight to a manuscript claim, without a candidate stage. Reports and handoffs are as
  long as their result, and every handoff field is optional.
- A researcher works a mission — a question and its expected result — from a starting
  lens it may leave, saying why. Its file gains guiding questions (tools, not a checklist)
  and an early critique of unfinished ideas, distinct from review. A special case, a
  reduction or an identified hypothesis counts as a result.
- A checkpoint records what was learned: *Question examined*, *What we learned* (each item
  *established*, *observed* or *intuition*; an established result is not certified),
  *What resists*, *Proposed next step*. An observation need not become a candidate.
- The orchestrator decides which route to pursue, set aside or reformulate, and may
  synthesize several explorations in one checkpoint. The brief gains a *Neighbourhood* of
  statements near the target; a corrected version of a refuted target is a new id.

### Removed

- PDF export: the LaTeX template, the `mystmd` patch and `check.sh --pdf`.
- `experiments/` and the `numerics` role: a computation is a seeded script under
  `research/runs/`, run with `uv run`, whose output header flags a dirty tree. Dependencies
  grow from none, to PEP 723 inline metadata, to a `research/lib/` package once scripts
  share code.
- The `synthesizer` and `literature-scout` roles, `packs/`, `research/instances.md`, the
  issue forms, the concurrency-key table, and the Markdown link checker.

### Fixed

- A checkpoint can close only a candidate an earlier checkpoint proposed; the checker used
  to accept one proposed in the same or a later checkpoint.
- A non-string entry in a node's `references` is reported instead of crashing the checker.
