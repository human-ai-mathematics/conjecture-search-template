# Template baseline

**Date.** 2026-09-01

The first decision record in this repository, inherited from the template it was created from. It
states the invariants the structure is built on, so that a later change to the harness is made
deliberately rather than by drift. Append-only: amend it with a new dated record, never by
editing this one.

## Problem

Two research repositories with the same machinery — one ledger, one manuscript, agent roles, a
numerical harness — had drifted apart at the seams while remaining identical at the core: 57
files byte-identical, and the structural checker differing on four lines of configuration. Every
new program repeated the same setup by hand and re-derived the same schema from the checker
source.

## Chosen invariants

1. **One repository, one program, one ledger, at a fixed path.** `research/program/ledger.yaml`
   is the path in every repository built from this template. The program *names* itself in
   `meta.program`; nothing else needs to know that name, so no configuration file can disagree
   with it. A second `ledger.yaml` anywhere under `research/` is an error, not a feature: a ledger
   is a single-file write-contention point (constraint 1), and two of them means two orchestrators.

2. **`research/` holds no executable code.** The validators live in `scripts/`. `research/` is
   what people and agents write *about* the mathematics — ledger, explorations, decisions,
   reviews, knowledge, run artifacts. This is also the upgrade seam: `scripts/` is
   template-owned and can be replaced wholesale; `research/` is program-owned and never is.

3. **The program-specific configuration is the ledger's own `meta:`.** `route_policy` makes
   `route` required and validates it against a closed vocabulary; omitting it forbids `route`.
   `refines` is optional and checked against the manuscript labels wherever it appears. Both
   validators are therefore identical across repositories, and a fix to one is a copy rather than
   a merge.

4. **Roles are self-describing.** `.claude/agents/*.md` frontmatter carries `read_only` and
   `reasoning` alongside `name`, `description` and `tools`, and the roster is derived from the
   files on disk. Adding a role is one new file plus one roster row — there is no list of role
   names to keep in sync in a checker or a config file.

5. **Hard constraints are split by scope.** `CLAUDE.md` carries seven universal constraints, and
   program-specific ones live in a separate `P1, P2, …` list. The numbers are cited by
   append-only records and are never reused, so a fork that drops a program constraint leaves no
   `Reserved` hole in the universal list — which is exactly what happened the last time a
   repository split.

6. **A fresh clone is green.** The template ships one worked example of each artifact genre — a
   manuscript module, three ledger nodes, an obstruction entry, a proof dossier, a certifying
   review, a numerics target — so that `./scripts/check.sh` passes before anything has been
   written, and so each genre has one instance to copy rather than a schema to interpret. They
   are deleted in one commit during instantiation.

## Compatibility

None required: this is the first commit of a new repository. A repository built from an earlier
copy of the template does not inherit these paths and should not be migrated to them merely for
uniformity — its append-only records cite its own paths and constraint numbers.

## Validation

`./scripts/check.sh` green on a fresh clone: ledger checker, agent checker, 45 checker tests, the
numerics test suite and calibration lane, and a full `latexmk` build of the document plus a
standalone build of the seed dossier and module.
