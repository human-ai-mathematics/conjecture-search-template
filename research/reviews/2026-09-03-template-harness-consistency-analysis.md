---
type: audit
date: "2026-09-03"
supersedes:
  - research/reviews/2026-09-03-modular-search-portfolio-followup-audit.md
  - research/reviews/2026-09-03-simple-modular-search-portfolio-analysis.md
---

# Current harness consistency and simplicity analysis

## Scope

This is a design audit of the current repository as a harness for agents proving or refuting
conjectures. It examines the planes of truth, the conjecture lifecycle, role permissions,
validators, durable memory, and the cost imposed on an agent before it can begin mathematics.

It supersedes the two earlier portfolio design audits above as the current reading of the
implemented harness. Those records remain the historical rationale for the portfolio redesign;
the later consistency decision adopted their principal recommendations. This report evaluates
the repository after that work and identifies the remaining seams.

This is a non-certifying `type: audit`. It certifies no proof and changes no mathematical status.
No existing repository file was rewritten or deleted to produce it.

## Overall assessment

The architecture is fundamentally sound and worth keeping. Its strongest invariant is:

> Mathematical truth goes to the ledger; search coordination goes to the portfolio; durable
> reasoning goes to checkpoints.

The implementation mostly respects that separation. It is structurally green, but it is not yet
as simple or internally consistent as it appears. The remaining problems occur mainly at
lifecycle boundaries: initialization, statement identity, candidate promotion, refutation, route
definition, and certification. The current checkout is also an uninstantiated template that the
checker cannot distinguish from a real active program.

The right next step is to tighten and simplify the present architecture, not replace it and not
add another plane.

## Strengths to preserve

- Mathematical state and search state are genuinely separated. The ledger rejects retired
  coordination fields, while the portfolio contains no claim text.
- Persistence is proportional: only reusable failures, blockers, candidates, artifacts, and
  synthesis require checkpoints.
- Author and reviewer have disjoint write surfaces, and agent certification requires a persisted
  review.
- Numerical evidence cannot directly change mathematical status.
- Mutable shared files have explicit single writers.
- `scripts/check.py` exposes useful derived views rather than storing reverse indexes and status
  summaries elsewhere.
- The checker is well tested. At the time of this audit, all 95 checker tests passed and the
  current repository reported zero structural errors.

## Principal findings

### 1. A green repository is not necessarily ready for research

The current brief points to `q:example`, contains no actual exact negation, and still consists
largely of instructions to the future author. Nevertheless, the checker passes because it
validates only the brief envelope.

At the same time, `prompt_openai.md` looks like an active Cycle Double Cover task and asserts that
it led to a proof. It is actually comparison material for a historical audit, but nothing near
the root identifies it as non-active. An incoming agent therefore sees two apparent targets:

- the generic `q:example` recognized by the harness; and
- the Cycle Double Cover prompt at the repository root.

The harness needs an explicit readiness boundary. A separate `check.py ready` command would be
cleaner than weakening the useful rule that absent optional planes are valid. Readiness should
reject template placeholders, an unfilled negation or completion section, and the default program
id.

### 2. Template initialization contradicts append-only policy

The root instantiation checklist tells users to delete the example explorations and their run
artifact. The root contract says explorations are append-only and must never be deleted; the
review and run documentation makes similar permanence claims.

This is not merely a wording problem: the first operation requested of a new repository violates
its universal contract. Worked examples should ship outside the live planes, under an `examples/`
or template-fixture area. A real program should begin with empty live directories and copy an
example only when useful. Existing append-only records should not now be silently moved or
deleted.

### 3. The label-to-node invariant is false as written and weakly enforced

The root README says every `\label` in `modules/` is a ledger node id. The example module contains
`sec:overview`, which has no node; the current checker accordingly reports four labels and three
nodes without error.

There are further loopholes:

- optional `label:` may override the node id, contradicting the simple identity slogan;
- duplicate labels across modules are collapsed into a set and are not detected;
- a node's declared `file` must exist and contain its label, but is not confined to `modules/`;
  and
- the checker does not distinguish a theorem label from a section or equation label.

A simpler honest invariant is:

> Every claim-bearing theorem-environment label corresponds to exactly one ledger node.
> Structural labels such as `sec:` and `eq:` do not.

The validator should then remove `label:` overrides, require node files under `modules/`, and
detect duplicate effective anchors.

### 4. The repository still carries several copies of a statement

The manuscript is canonical, but the ledger has a `statement`, the brief may quote the target,
and the dossier restates the theorem. Only semantic review can keep those texts aligned.

Some duplication is necessary: a standalone dossier must state what it proves. The ledger and
brief copies are optional choices. For a simpler boundary:

- remove the ledger `statement`, or rename it `summary` and declare it noncanonical;
- let the brief name the target and contain only its negation, completion criteria, edge cases,
  and traps;
- have agents read the manuscript target directly or obtain it through a derived command; and
- retain the theorem statement in the dossier because independent review requires it.

### 5. Refutation is valid in principle but is not an operationally complete path

The shared role transition diagram intends:

```text
researcher(refute) -> researcher(prove) proves the refuter
                   -> reviewer(certify) -> orchestrator
```

The refutation lens itself stops after finding and reporting an exact witness. It does not state
the complete durable transition:

1. Record the witness or divergent family as a candidate.
2. Promote it to a precise refuter node and manuscript statement.
3. Prove that node in a dossier.
4. Independently certify it.
5. Mark the target `refuted` using `refuted_by`.

The graph also represents the refuter twice: it must occur in both `refuted_by` and `depends_on`.
But `depends_on` is defined as facts used in a proof, while a refuted target has no proof.
`refuted_by` already requires a proved refuter and is sufficient by itself.

A refutation-specific dossier example and one explicit transition contract would make proving
and refuting genuinely symmetric.

### 6. Candidate promotion leaves stale candidates behind

A candidate is live until a later checkpoint retires it. Promotion is described only as adding a
manuscript label and ledger node. The checker computes liveness exclusively from `retires:`.
Promoting `cand:x` to a normally named node such as `lem:x` therefore leaves `cand:x` live unless
someone separately remembers to retire it.

Promotion should be one atomic orchestration operation:

- add the manuscript statement and ledger node;
- retire the candidate in a new checkpoint; and
- update portfolio blockers from the candidate id to the promoted node when appropriate.

An explicitly required retirement checkpoint is simpler than adding a second promotion registry.

### 7. The portfolio does not say what an individual route tries

A family has a `mechanism`, but an approach has only an id, family, ancestry, state, blockers,
relations, and checkpoints. A queued or active route may have no checkpoint and no prose
describing its actual objective. In the worked example, `ap:example-roundoff-bound` is
understandable only by interpreting its id.

Every route needs one short `objective` or `mechanism` field. This is coordination text, not a
mathematical statement, so it belongs in the portfolio.

Other lifecycle gaps remain:

- a portfolio may exist without a problem brief, although several coordinated routes necessarily
  constitute a sustained search;
- `completed` does not say whether the route objective, the target, or the mechanism is complete;
- a portfolio may retain active routes after its target becomes proved or refuted; and
- a target may be any node, including a definition or an already resolved node.

At minimum, enforce `portfolio => brief`, define `completed`, and warn when the target is resolved
but live routes remain.

### 8. Lean certification currently overclaims

`mode: lean` is described as machine certification but presently checks only that an adjacent
`.lean` file exists. No Lean command runs. That mode should be removed until the checker invokes
the kernel with pinned tooling. A future capability should not currently be able to support
`status: proved`.

Natural-language dossier headers are also mostly decorative: the checker searches only the first
part of the file for `ledger-node` and the node token. Either parse a small structured header and
compare it with the review, or remove duplicated fields such as reviewer and review path from the
dossier header.

### 9. Numerical provenance is not fully reproducible

The numerical design is responsibly conservative, but its provenance claim is stronger than its
implementation:

- the commit hash is informational and dirty worktree state is ignored;
- an uncommitted target implementation cannot therefore be reproduced from the recorded commit;
- `--out` may write outside `research/runs/`; and
- the archive checker does not require `git_commit` or `stochastic`, nor validate archived
  observation records against the numerical contract.

For exact provenance, either reject dirty runs or record a source-tree or diff hash. The
production CLI should confine output to `research/runs/`, while lower-level test helpers may still
accept temporary paths.

The package description also says numerics "guides and refutes; never proves," although the root
contract correctly says numerical output cannot refute a claim. "Guides and finds candidate
refutations" would be accurate.

### 10. Planes, layers, and validation lanes are different taxonomies

The root README lists six repository planes: manuscript, ledger, portfolio, proofs, numerics, and
history. `check.py` lists six different planes: core, proofs, checkpoints, portfolio, numerics,
and roles. The root contract then lists five activation layers.

Each partition is reasonable, but reusing `plane` for different partitions makes the system
harder to learn. Prefer:

- three conceptual domains: mathematical state, search state, and durable evidence/history;
- activation gates for optional features; and
- validation lanes for the CLI implementation.

### 11. Runtime instructions remain too large

A researcher is told to read the root contract, the shared agent README, the problem brief, its
role contract, and one lens before beginning mathematics. That is roughly 600 lines before the
target and prior work.

The shared agent README mixes runtime instructions with maintainer material such as adding roles,
adapter generation, roster documentation, and configuration internals. It should be split into:

- a short execution contract read by agents; and
- maintainer documentation for roles, adapters, and extension.

There are also direct optionality conflicts. Numerics and literature roles tell their checkpoints
to name `approach:`, even though the portfolio is optional. The instruction should be: name the
approach when a portfolio exists; otherwise name the engaged node.

The role checker has a related blind spot: if `.claude/lenses/` is entirely absent, lens
validation returns early rather than rejecting the researcher's dangling lens declarations.

### 12. "Current audit" does not reliably mean current

Before this report, the derived checkpoint view listed the portfolio follow-up audit as current,
although that audit said a consistency pass was still needed and the later decision stated that
all seven findings were fixed. This demonstrates that append-only memory still requires active
curation.

This report supersedes that follow-up and the design analysis it followed as the current reading
of the implemented harness. More generally, audit currency should be understood per subject;
unrelated non-superseded audits are not competing versions of one document.

## Recommended minimal model

The conceptual lifecycle can be reduced to:

```text
Canonical target in modules/ + logical state in ledger.yaml
                         |
                         v
                  problem brief
                         |
                         v
       route in portfolio.yaml, if coordination is needed
                         |
                         v
       durable checkpoint, only when something survives
                /                       \
       candidate lemma            reusable dead end
                |
                v
   manuscript node + analytic dossier
                |
                v
        independent proof review
                |
                v
 ledger transition: proved, or refuted via proved refuter
```

Everything else should remain optional capability:

- numerics produces candidate-generating artifacts;
- literature import proposes source-backed nodes;
- scout supplies read-only orientation;
- synthesizer exists only when a portfolio exists; and
- janitor is maintenance, not part of the mathematical lifecycle.

## Recommended order of improvement

1. Add an initialization/readiness boundary and remove active-looking examples from live research
   planes in the next template version.
2. Correct and enforce the claim-label invariant.
3. Make refutation and candidate-promotion transitions explicit and atomic.
4. Add one-sentence route objectives and enforce `portfolio => brief`.
5. Remove nonfunctional Lean certification and either validate or simplify dossier headers.
6. Separate runtime instructions from maintainer documentation and align the terminology.
7. Harden numerical provenance as an optional capability pack.
8. Keep audit supersession curated so current-memory views remain trustworthy.

## Conclusion

The current high-level separation is good. Its remaining complexity comes less from the number of
files than from duplicated metadata, terminology with several meanings, and transitions that are
described in one place but not carried through the schemas and roles.

Do not add another plane. Make every lifecycle transition explicit, remove metadata that has no
single owner or executable check, and give the repository a readiness gate so that "green" means
what an incoming agent will naturally assume it means.

## Validation baseline

During this audit:

- `python3 scripts/check.py` reported 0 structural errors;
- all 95 tests under `scripts/tests/` passed; and
- the worktree was clean before this new audit record was added.

The full LaTeX and numerical lanes were not run because this audit was requested without touching
generated workspace files.
