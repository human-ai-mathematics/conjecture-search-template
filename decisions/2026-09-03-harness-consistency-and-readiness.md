# Readiness, one anchor invariant, and lifecycle transitions that carry through

**Date.** 2026-09-03

Adopts the twelve findings of
[`../research/reviews/2026-09-03-template-harness-consistency-analysis.md`](../research/reviews/2026-09-03-template-harness-consistency-analysis.md),
which supersedes the two earlier portfolio audits as the current reading of the implemented
harness. Amends, and does not rewrite,
[`2026-09-03-search-portfolio-consistency-pass.md`](2026-09-03-search-portfolio-consistency-pass.md)
and [`2026-09-02-simplify-numerics-harness.md`](2026-09-02-simplify-numerics-harness.md); the
invariants of both stand except where this record says otherwise.

Per `CLAUDE.md`, harness work changes no mathematical status. Nothing here proves, refutes, or
certifies anything.

## Problem

The three-domain architecture was sound and the repository was structurally green, and neither
fact meant what an incoming agent would assume. The defects sat at lifecycle boundaries.

- **A green repository was not a ready one.** The brief pointed at `q:example`, contained no
  actual negation, and consisted largely of instructions to its own future author — and passed,
  because the checker validates the brief's envelope. Meanwhile `prompt_openai.md` sat at the
  root looking like a live Cycle Double Cover assignment. An incoming agent saw two apparent
  targets and no way to tell either was fictional.
- **Instantiation contradicted constraint 7.** The first operation the README asked of a new
  repository was to delete `research/explorations/` records, which that constraint forbids.
- **The advertised label invariant was false.** "A `\label` in `modules/` **is** a ledger node
  id" — `sec:overview` was neither. The checker enforced only the node→label direction, allowed
  a `label:` override that contradicted the slogan outright, collapsed duplicate labels into a
  set, did not confine a node's `file` to `modules/`, and could not tell a theorem from a
  section.
- **A statement had four homes.** The manuscript, the ledger's `statement`, the brief's quoted
  copy, and the dossier. Only the second was avoidable and unowned.
- **Refutation stopped at the witness.** The `refute` lens found one and reported it; nothing
  said what turns a witness into `status: refuted`. The ledger meanwhile required each refuter
  to appear in the refuted node's `depends_on` — the graph of facts a proof used, for a node
  that has no proof.
- **Promotion leaked.** Liveness came only from `retires:`, so promoting `cand:x` to `lem:x`
  left `cand:x` live forever: one statement, two homes, which is what constraint 8 exists to
  prevent.
- **A route said nothing about itself.** Families had a `mechanism`; an individual approach had
  an id, a family, a state and no prose at all. `ap:example-roundoff-bound` was legible only by
  reading its slug.
- **`mode: lean` overclaimed.** It checked that a file with a `.lean` suffix existed beside the
  dossier. An empty one satisfied it, no kernel ran, and it could support `status: proved`.
- **Numerical provenance promised more than it recorded.** A run whose target implementation was
  uncommitted could not be reproduced from its `git_commit`, and `--out` could write anywhere.
- **`plane` named three different partitions** — six in the README, six different ones in
  `check.py`, five activation layers in `CLAUDE.md`.
- **Runtime instructions carried maintainer material.** A researcher loaded 200 lines of
  `.claude/agents/README.md` to reach the ~85 it executes under, and three role files told
  checkpoints to name `approach:` although the portfolio is optional.

## Decisions

Continuing the invariant numbering of the two records this amends.

20. **The worked example is a fixture, and it lives outside the live planes.** Everything that
    demonstrated a genre moved to a single top-level `example/`: the module, the ledger, the
    brief, the portfolio, the dossier, the review, both checkpoints and the run artifact. The
    live planes ship empty — a ledger with `meta` and no nodes, no brief, no portfolio, a
    label-free `modules/00-overview.tex`. Instantiating is now copying, never deleting, and
    constraint 7 gains one sentence saying that `example/` records no search and is freely
    editable.

    `example/` is invisible to every lane: all ten globs in `scripts/checks/` are rooted at
    `modules/`, `research/`, `.claude/` or `.codex/`. That is a property of it being a
    top-level sibling, and `example/README.md` says so — nested under `research/` its ledger
    would trip constraint 1 and its checkpoints would be swept into durable memory.

21. **`check.py ready` is a separate question from `check.py check`.** A fresh clone is
    correctly green and correctly not ready. `ready` tests for shipped placeholder *strings* —
    `{{REPO_TITLE}}`, `<Document title>`, `meta.program: program`, the brief's instructional
    comment — never for a plausible-looking id, because a real program may legitimately own a
    node called `…:example`. Activation stays structural: no optional plane became mandatory.

22. **One honest anchor invariant, enforced in both directions.** Every claim-bearing
    theorem-environment `\label` in `modules/` is exactly one ledger node whose `kind` is that
    environment; structural labels are not nodes. The ten claim environments are the ten `kind`
    values, so `preamble.tex` gains an `obstruction` environment and the example's obstruction
    stops borrowing `remark`. Duplicate labels are caught, `file` is confined to `modules/` like
    every other cross-lane pointer, and `label:` is rejected by name.

23. **The ledger holds a `summary`, not a `statement`.** Renamed and documented as a
    noncanonical gloss for the derived views; `statement:` is rejected by name, pointing at
    `modules/`. A *candidate's* `statement:` is untouched and stays canonical, because nothing
    else holds that text — the asymmetry is the point and both schemas say so.

24. **Refutation is a channel, not an outcome.** The five-step transition — candidate, refuter
    node, dossier, certification, `refuted_by` — is written into `refute.md`, `certify.md`,
    `solutions/README.md` and `research/program/README.md`, and `example/` now ships a refuted
    conjecture with a proved refuter, its dossier and its review. `refuted_by ⊆ depends_on` is
    dropped: a refuted node has no proof, so it has no proof dependencies.

25. **Promotion is one act.** A new checkpoint field records it:

    ```yaml
    promotes:
      - candidate: cand:x
        node: lem:x
    ```

    It ends the candidate, must name a node that exists, and cannot precede the proposal. A
    portfolio `blocker:` still naming a promoted candidate is an error that names the node to
    use instead. No second registry was added.

26. **Every route says what it tries.** `objective` is required on each approach — one
    sentence, coordination text, never a claim. `completed` is defined as "this route's
    objective is finished", explicitly saying nothing about the target. A portfolio now requires
    a brief, a target must be a claim-bearing kind, and a `proved` or `refuted` target may not
    leave routes `active` or `queued`.

27. **`mode: lean` is retired and rejected by name.** A mode that certifies nothing must not sit
    at the top of a certification ladder. Restore it when `check.py` invokes the kernel with
    pinned tooling. The dossier header is now parsed rather than grepped — `ledger-node` must
    name this node and `checked_by` must be `none`/`agent`/`human` — and the header's duplicate
    `reviewer` and `review` fields are gone, since `proofs[].review` and the report's front
    matter already own them.

28. **Numerical provenance records the source tree.** `git_dirty` and `git_diff_sha256` join
    `git_commit`, artifact schema goes to 3, and the archive checker requires them of schema-3
    artifacts while asking an older one only for what its own version promised. It also rejects
    a half-observation. The production CLI confines `--out` to `research/runs/`.

    This **amends** `2026-09-02-simplify-numerics-harness.md` and does not reverse it. That
    record removed `evidence_eligible`, which *gated* whether output counted. Nothing here
    gates: a dirty run is a run, worth exactly what any numbers are worth (constraint 2). The
    test that asserted the absence of a dirty flag is renamed to assert what it now checks.

29. **Domain, gate, lane.** Three words, three meanings, stated at the top of `CLAUDE.md`. The
    README describes three *domains*; `CLAUDE.md` keeps its activation *gates*; `check.py`
    exposes validation *lanes* through `--lane`, with `--plane` kept as a deprecated alias that
    prints one note. Nothing lines the three partitions up, and nothing should.

30. **Runtime instructions and maintainer documentation are separate files.**
    `.claude/agents/README.md` keeps only what a role loads to execute — author/reviewer
    disjointness, merge points, the handoff envelope, concurrency keys, checkpoint naming — and
    drops from 200 lines to 99. The roster, the transitions diagram, adapter generation and
    role-extension guidance move to `.claude/agents/MAINTAINING.md`, which the roster check now
    validates. The three roles that demanded `approach:` unconditionally now say: name the route
    when a portfolio exists, otherwise name the nodes.

31. **Audit currency is per subject.** `research/reviews/README.md` and the `reviewer` role now
    say it: supersede an earlier reading of the same subject, name nothing when the subject is
    new, and never supersede an unrelated audit for being older. No checker can infer this, which
    is why it is written down.

## Migration boundary

Append-only records are untouched, and four of them now name paths that moved or a file that is
gone: `2026-09-02-collapse-side-registries.md:67`,
`2026-09-03-modular-search-portfolio.md:156`,
`2026-09-03-search-portfolio-consistency-pass.md:94`, and
`2026-09-02-template-vs-raw-prompt-analysis.md` (three references to `prompt_openai.md`). They
are correct as written for the repository they described. The old→new table is in
[`../example/README.md`](../example/README.md) and here:

| was | is |
|---|---|
| `modules/00-overview.tex` | `example/modules/00-overview.tex` |
| the three seed nodes of `research/program/ledger.yaml` | `example/research/program/ledger.yaml` |
| `research/program/brief.md` | `example/research/program/brief.md` |
| `research/program/portfolio.yaml` | `example/research/program/portfolio.yaml` |
| `solutions/prop-example.tex` | `example/solutions/prop-example.tex` |
| `research/reviews/2026-09-01-prop-example-proof-review.md` | `example/research/reviews/2026-09-01-prop-example-proof-review.md` |
| `research/explorations/2026-09-02-example-exploration.md` | `example/research/explorations/2026-09-02-example-exploration.md` |
| `research/explorations/2026-09-03-example-dedup.md` | `example/research/explorations/2026-09-03-example-dedup.md` |
| `research/runs/2026-09-02T092336.680787Z-example.jsonl` | `example/research/runs/2026-09-02T092336.680787Z-example.jsonl` |
| `prompt_openai.md` | **deleted** |

`prompt_openai.md` was comparison material for one historical audit, which quotes what it needs.
At the repository root it read as a live assignment, which is the defect the readiness boundary
exists to remove; it is deleted rather than relocated, so nothing has to explain why a
Cycle Double Cover prompt ships with a template.

An inherited repository sees named errors rather than silent breakage. `statement`, `label` and
`mode: lean` each report their replacement and why. The genuinely new failures are: a claim
label with no node, a `kind` disagreeing with its environment, a node `file` outside `modules/`,
an approach with no `objective`, a portfolio with no brief, a resolved target with live routes,
and a schema-3 artifact missing its source fields. Each names the offending id or path.

## Compatibility

Proof semantics are unchanged apart from the removal of `lean`: `agent` and `human` mean exactly
what they meant. The checkpoint envelope gains one optional field and loses none. Artifacts
already on disk stay valid — schema 2 is asked only for what schema 2 promised. `--plane`
continues to work.

The `--lane`/`--plane` pair, the `statement`→`summary` rename and the required `objective` are
breaking for an inherited repository, which is why each is rejected or reported by name rather
than silently ignored.

## Validation

`./scripts/check.sh` green: `scripts/check.py` at 0 errors on the live tree and on
`--root example`, 125 checker tests (95 carried over, 30 new), 16 numerics tests, and a full
`latexmk` build. `example/modules/00-overview.tex` and both example dossiers also compile
standalone against the root master.

Spot-checked by hand, each against the finding it closes: `check.py ready` lists nine
outstanding steps on the shipped template and exits 1; `check.py ready --root example` reports
the example as not ready for exactly the right reason, its instructional brief; `check.py
candidates` prints promotions separately from live candidates; `check.py portfolio` shows each
route's objective; and `check.py --plane core` prints its deprecation note while reporting only
the core lane.
