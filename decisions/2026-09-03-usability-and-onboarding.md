# Two readiness questions, scaffolds instead of copying, and four honest validators

**Date.** 2026-09-03

Adopts the ten findings of
[`../research/reviews/2026-09-03-usability-and-applicability-analysis.md`](../research/reviews/2026-09-03-usability-and-applicability-analysis.md),
which supersedes
[`2026-09-03-template-harness-consistency-analysis.md`](../research/reviews/2026-09-03-template-harness-consistency-analysis.md)
as the current reading of this harness. Amends, and does not rewrite,
[`2026-09-03-harness-consistency-and-readiness.md`](2026-09-03-harness-consistency-and-readiness.md);
its invariants stand except where this record says otherwise.

Per `CLAUDE.md`, harness work changes no mathematical status. Nothing here proves, refutes, or
certifies anything.

## Problem

The audit's verdict was that the architecture is right and the surface is not: *"Removing the
ledger/portfolio/checkpoint separation would make the harness smaller but less trustworthy."*
So nothing here merges a plane or weakens certification. What it does is stop the harness
overstating what it knows, and stop onboarding being an act of copying an instructional
fixture.

- **`ready` answered two questions at once.** Nine blockers, four of which were a LaTeX title,
  an author, an abstract and a leftover README section. None of them blocks an attack on a
  conjecture, and bundling them meant the command that sounds like "can I start?" was really
  asking "is this ready to publish?"
- **The worked example demonstrated schemas, not a search.** Its target `q:example` was
  literally *"Placeholder for the question this repository is organized around"*, its brief's
  exact-negation section was an instruction to write one, and its portfolio declared
  `target: q:example` while all three route objectives attacked `prop:example` — a different,
  already-proved node. A newcomer could see what the fields were and not what a search is.
- **The only scaffold was for dossiers.** A brief, a portfolio, a module and a checkpoint were
  all created by copying out of `example/`, whose prose is instructional and whose relative
  paths are written for its own location one level deeper.
- **`checked_by` had no owner.** The checker validated the vocabulary and never compared it to
  the ledger — `_dossier` returned before `mode` was even read — so a dossier could say
  `checked_by: none` under a `mode: agent` record with a passing review and nothing went red.
- **Chronology was inferred from filename slugs.** `enumerate(sorted(rglob(...)))` was the only
  event clock for candidate proposal, promotion and retirement, and supersession fell back to
  the path whenever two dates tied. Every same-day supersession in `research/reviews/` passed
  by lexical luck, and a legitimate same-day promotion could be rejected for starting with the
  wrong letter.
- **`check.sh` said "all checks passed" over suites it had skipped**, and compiled no dossier
  at all — so a dossier with a LaTeX error passed every validator in the repository, while
  standalone compilation is part of the proof definition of done.
- **The claim scanner read commented-out LaTeX**, and the summary counted a `\section` anchor
  as a label, so a template with no claims reported `0 nodes, 1 labels`.
- **Optional machinery shipped active.** Seven roles and their adapters in a fresh clone,
  where the documentation called three of them optional.
- **PyYAML was declared nowhere.** The requirement existed only in the error message you got
  when it was missing, and the sole manifest covered the numerics harness instead.
- **Twelve links pointed at files that are correctly absent.** `research/README.md`'s entire
  program entry-point table was one row, and that row was a 404 in a fresh clone.

## Decisions

Continuing the invariant numbering of the record this amends.

32. **Research readiness and publication readiness are different questions, asked separately.**
    `check.py ready` now asks only what a search needs: a named program and scope, a target
    with a ledger node, and a brief that has actually been written. `check.py publish-ready`
    asks about the manuscript title, author, abstract and the leftover instantiation section.
    On the shipped template that is 4 blockers and 5 blockers respectively, and a repository
    may correctly be deep into a search while still owing an abstract.

33. **`templates/` is what a thing looks like empty; `example/` is what it looks like
    finished.** The division is now sharp, and both halves changed to make it true.

    `templates/` is new and holds `brief.md`, `portfolio.yaml`, `checkpoint.md`, `module.tex`,
    `node.yaml` and `solution.tex` (moved from `solutions/TEMPLATE.tex`). It carries the
    placeholder strings `ready` looks for, which is where they belong: the file people copy.

    `example/` is now a complete search. `conj:example` is the target of both the brief and the
    portfolio; the brief's every section is written, negation included; the route objectives
    attack that target; a new checkpoint promotes `cand:example-constant-witness` to
    `prop:example-refuter` and closes the routes and the family. `check.py ready --root example`
    now **passes**, which is the property that makes it worth reading.

    The mathematics stayed elementary on purpose, and `example/README.md` says so: every line
    of attention the fixture asks for should go to the shape, none to the content.

34. **`scripts/new.py` writes; `scripts/check.py` still only reads.** They are separate
    commands because a validator that edits the tree it judges is a validator nobody can trust
    twice. `new.py` scaffolds a brief, portfolio, checkpoint, module or dossier, never
    overwrites a file, and prints the next step.

    `new.py node` is the deliberate exception: it prints a ledger node to stdout and writes
    nothing, because `research/program/ledger.yaml` has exactly one writer (constraint 1). No
    tool reaches into that file behind the orchestrator's back.

35. **Certification has one home, and it is the ledger.** `checked_by` is removed from the
    dossier header and rejected by name, alongside `reviewer` and `review`, each pointing at
    what owns it now. **A dossier that no `proofs[]` record names is a draft, and that absence
    is the whole signal** — there is nothing left to keep in sync, which is what the old field
    could not do.

36. **A filename is not a clock.** The lexical event order is gone. `date:` now accepts a UTC
    timestamp `YYYY-MM-DDTHH:MM:SSZ` whose date part still matches the filename prefix, and
    ordering is consulted only where it is real:

    | | ordered? |
    |---|---|
    | different days | yes |
    | same day, both timestamped | yes |
    | same day, either untimed | **no** — and the checker does not pretend otherwise |

    A same-day proposal and promotion is therefore accepted rather than judged on its slugs.
    Supersession keeps its strict check where dates differ and is verified **acyclic** where
    they do not, which is the property the total order was standing in for. Nothing on disk
    was renamed, so constraint 7 is untouched and the three existing same-day supersessions in
    `research/reviews/` now pass on purpose rather than by luck.

37. **A suite that did not run has not passed.** `check.sh` accumulates what it skipped and
    reports `all AVAILABLE checks passed` with the list, reserving `all checks passed` for a
    complete run. `--strict` makes a missing `uv` or `latexmk` a failure. It also compiles
    every dossier the ledger certifies, in both the live tree and `example/`, via the new
    `check.py dossiers` view — the definition-of-done step that no validator had ever
    exercised.

38. **The claim scanner reads LaTeX, not commented-out LaTeX.** `strip_comments` blanks an
    unescaped `%` to end of line, preserving character offsets so the two merged regex streams
    still interleave correctly, and it is applied to `modules/` and to `references.bib`. A
    character scan rather than a lookbehind, because `\%` is an escaped percent and `\\%` is a
    line break followed by a comment. The default summary now counts claim labels and
    structural labels apart: the template reads `0 nodes, 0 claim label(s), 1 structural`.

39. **Three roles became capability packs, and cross-client adapters became optional.**
    `.claude/agents/` ships the four core roles; `numerics`, `literature-scout` and `janitor`
    wait in `packs/` until `python3 scripts/new.py role <pack>` installs one, which also
    regenerates its adapter. The roster links each pack by path, so installing is genuinely one
    command and not a command plus a documentation edit the checker demands.

    `.codex/` may now be deleted outright — the roles lane skips an absent adapter tree the way
    it already skipped an absent `.claude/agents/`. What is still never allowed is an adapter
    that disagrees with its Markdown.

    The `numerics` **harness** under `experiments/` did not move. Its lane already validates
    only the artifacts that exist, so an unused harness costs nothing; what the pack gates is
    the one role permitted to execute a run (constraint 2).

40. **The operational path has one home.** `docs/RUNNING-A-SEARCH.md` is the five-step guide
    the audit asked for — initialize, assign, checkpoint, coordinate, claim — and it is
    explicitly *not* contract. `CLAUDE.md` keeps every numbered constraint verbatim, the gates,
    the write ownership and the verification commands, and its Workflow section now states only
    what is normative and points at the guide for the rest.

    Its line count barely moved (207 → 208): the Workflow section shrank, and the Verify block
    grew by the same amount because there are more commands to name. The consolidation is real
    but it is the guide, not a shorter contract — cutting normative text to hit a number would
    have been the wrong trade, and this record says so rather than claiming a reduction that
    did not happen.

41. **One dependency, declared.** A root `pyproject.toml` names PyYAML. `check.sh` falls back
    to `uv run` when `python3` cannot import it, so a fresh clone bootstraps itself. The
    guarded import in `common.py` is now the *only* one — `ledger`, `portfolio` and `views` take
    `yaml` from it — so the install hint fires regardless of which module loads first, where
    before it depended on `checkpoints` sorting alphabetically ahead of `ledger`.

42. **A navigation table may not point at a file that is not there.** A seventh lane, `docs`,
    validates every repository-relative Markdown link. `decisions/` and `research/reviews/` are
    exempt because they are append-only and several deliberately name paths that have since
    moved; `templates/` is exempt because a scaffold's links are written for its destination.

    The twelve dead links are fixed by naming the gated path as code and linking the scaffold or
    the worked instance instead. The lane immediately found two more the audit had not — both in
    `example/`, both pre-existing — which is the argument for having it.

## Migration boundary

Append-only records are untouched. Breaking for an inherited repository, each reported by name:

| was | is |
|---|---|
| `checked_by` in a dossier header | rejected; `proofs[].mode` owns certification |
| `solutions/TEMPLATE.tex` | `templates/solution.tex` |
| `.claude/agents/{numerics,literature-scout,janitor}.md` | `packs/<name>/<name>.md`, installed on demand |
| `.codex/agents/` required | optional; absent is valid |
| `check.sh` printing `all checks passed` unconditionally | `all AVAILABLE checks passed` plus the skip list |
| `check.py` summary `N labels` | `N claim label(s), M structural` |

Not breaking: `date:` still accepts a plain `YYYY-MM-DD`, and every existing record keeps its
filename. The ordering change only *removes* judgments the checker was not entitled to make, so
a repository that was green stays green.

`ready` is the one behaviour change that could surprise: a repository that passed it before
still passes, and one that failed it only on manuscript placeholders now passes `ready` and
fails `publish-ready`.

## Validation

`./scripts/check.sh --strict` green on a machine with both `uv` and `latexmk`:
`scripts/check.py` at 0 errors on the live tree and on `--root example`, 149 checker tests
(125 carried over, 24 new), 16 numerics tests, a full `latexmk` build, and both example
dossiers compiled standalone — the last of those for the first time as part of the script.

Spot-checked by hand, each against the finding it closes: `ready` lists four research blockers
and no manuscript cosmetics; `publish-ready` lists the five publication ones;
`ready --root example` passes; `check.py candidates --root example` shows one live candidate
and one promoted; `check.py portfolio --root example` shows a saturated family with one
completed, one blocked and one duplicate route; a dossier carrying `checked_by` is rejected by
name; deleting `.codex/` leaves `--lane roles` green; and a scaffolded tree
(`new.py module`, `node`, `brief`, `portfolio`, `checkpoint`) reports 0 errors while `ready`
correctly names the three brief sections still unwritten.
