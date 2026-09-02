# Collapse the side registries into the ledger and the manuscript

**Date.** 2026-09-02

Amends, and does not rewrite, [`2026-09-01-template-baseline.md`](2026-09-01-template-baseline.md).
That record's invariants 1–6 stand; this one removes a document genre it shipped.

## Problem

The template shipped four Markdown registries that duplicate a plane which already had a source of
truth: `research/knowledge/{obstructions,lemmas,instances}.md`, grouped because they look alike —
curated, mutable, prose reference about the mathematics — and `shared/notation.md` off in the
LaTeX plane. Three of the four recorded things the ledger and the manuscript already own.

- **`obstructions.md`** was a second home for something the ledger already fully described. An
  obstruction node carries `id`, `kind: obstruction`, `status`, `file`, `statement`, and a
  `\label` in `modules/`. The registry added no structural information; `check_ledger.py` merely
  verified that a heading with the same id existed, in both directions. What it did carry — the
  "rules out / leaves open" prose — is mathematical content that belongs at the `\label`, where
  `latex-sync` already audits prose against the ledger. Keeping it separate also split ownership:
  the file described ledger state, so the orchestrator owned it, but it sat under the
  `synthesizer`'s `knowledge` concurrency key.
- **`lemmas.md`** was a waiting room for statements that should be ledger nodes. The file conceded
  as much in its own text: "if a proof depends on it, it needs a node and a dossier." A reusable
  fact with a guardrail is a mathematical statement; giving it a second-class Markdown home let it
  acquire the appearance of settled knowledge without a node, a manuscript statement, a dossier,
  or a review.
- **`notation.md`** aimed at something real — the conventions a claim's *truth* depends on, a
  sign, a scaling, a log base, which constant absorbs what — but the ledger already has the slot
  for it: `kind: definition` with `status: defined`, a status that exists precisely because a
  definition has no truth value. Every column of its table was a duplicate: the convention is the
  node's `statement:`, its definition is the `\label`ed environment, "defined in" is the node's
  `file:`, and "claims that depend on it" is *derived* by `check_ledger.py node <id>`. That last
  one was a hand-maintained copy of the reverse dependency graph, which this repository forbids in
  two places (`research/program/README.md`; `.claude/agents/README.md`, "no role maintains a
  second copy").
- **`instances.md`** is the one that is genuinely not mathematics. An adversarial instance has no
  truth value, no proof, and no `\label`; it is input to the numerics harness. It needed to
  survive, but not to live in a directory justified by the other two.

## Chosen invariants

7. **Every mathematical object is a ledger node with a manuscript statement.** Obstructions,
   reusable lemmas, and fixed normalizations included. There is no second registry in which a
   statement or a convention can be recorded, and therefore no place where an uncertified fact can
   look certified, and no second copy of the dependency graph. A finding earns promotion by
   acquiring a node and a `\label`, not by being copied into a curated file.

8. **An obstruction is an ordinary node.** It is stated in `modules/` under its `\label` like a
   definition, and it states both halves — what it rules out *and* what it leaves open. The
   checker no longer enforces a registry heading; `bounded_by` still resolves to a same-ledger
   `kind: obstruction` node, which is the check that carried the logical weight.

9. **A fixed normalization is a `kind: definition` node with `status: defined`.** It is stated in
   `modules/` under its `\label` like any other definition, and claims resting on it name it in
   `depends_on`. Verified: `defined` is not in the checker's unresolved set, so such an edge does
   not make a dependent claim `conditional`, and `check_ledger.py node <id>` reports the claims a
   convention holds up.

10. **`research/instances.md` is the sole exception, and it is explicitly not mathematics.** It
   stays prose because it describes harness inputs. It keeps its curator and `CLAUDE.md`
   constraint 3; its concurrency key is renamed `knowledge` → `instances`.

## Migration boundary

- `research/knowledge/obstructions.md` — deleted; the `obs:example` fence prose moved into the
  `\begin{remark}` at `modules/00-overview.tex`.
- `research/knowledge/lemmas.md`, `research/knowledge/README.md` — deleted, no replacement.
- `research/knowledge/instances.md` → `research/instances.md`.
- `shared/notation.md` — deleted, no replacement. It was briefly renamed to
  `shared/normalizations.md` during this change before the duplication was spotted; neither file
  survives. The preamble's program-macros comment now points at the ledger instead.
- `scripts/check_ledger.py` — `obstruction_ids_md()` and the heading/node correspondence errors
  removed. Two fixtures in `scripts/tests/test_check_ledger.py` no longer write a registry;
  `test_bounded_by_requires_ledger_obstruction_node` now exercises the surviving check with a
  non-obstruction target instead of a heading-only id.

Also folded into this change, since the pointers had to be swept anyway: the earlier moves of
`research/ledger-schema.md` → `research/program/` and `research/decisions/` → `decisions/`, whose
references were still stale across `CLAUDE.md`, four READMEs, the ledger header, and six role
definitions. `decisions/` at the repository root sharpens baseline invariant 2 rather than
weakening it: harness decisions are not written *about* the mathematics.

Two defects fixed in passing: `janitor` cited a nonexistent `CLAUDE.md` constraint 8 (now 7) and
spoke of "either `ledger.yaml`" from a two-ledger ancestor; `.latexmkrc` had a corrupted filename.

## The LaTeX plane

`shared/` is gone. It held two files at the start of this change and one by the end, so the
directory stopped earning itself: the preamble is now `preamble.tex` at the repository root beside
`main.tex`, the only file that inputs it. It is still reached through `\subfix`, so it resolves
identically for a full build, a standalone module, and a standalone dossier. The root is the right
home rather than `modules/`: the preamble has no `\documentclass` and does not compile alone, so
living among the modules would have made it the one file a `modules/*.tex` glob breaks on.

- `shared/notation.md` deleted. It was two documents: a symbol glossary that duplicated the
  manuscript non-authoritatively, and a register of the conventions a statement's truth depends on.
  The glossary would only rot. The register looked load-bearing — the first pass at this change
  kept it, renamed to `shared/normalizations.md`, on the belief that nothing else in the repository
  held it. That belief was wrong: `kind: definition` with `status: defined` is exactly that slot,
  and the register's own "claims that depend on it" column was a hand-maintained copy of a graph
  `check_ledger.py` derives.
- The preamble cut from 131 lines to 74, then moved `shared/preamble.tex` → `preamble.tex`. Removed: `\partgroup` and its 30 lines of
  `\makeatletter` TOC internals; `tikz` and four libraries, unused and paid for on every module
  and dossier build; `inputenc`, a no-op under modern pdflatex; `mathrsfs`, `bm`, `booktabs`,
  `tabularx`, `array`, `enumitem` and the `Y` column type, all unused; six unused theorem
  environments; and the concentration-theory macros (`\Ent`, `\KL`, `\lmax`, `\Cov`, …) that the
  file's own comment called domain-neutral and which are not. The omitted packages are listed in a
  comment so re-adding one is a decision rather than a rediscovery.

## Compatibility

Constraint numbers 1–7 in `CLAUDE.md` are unchanged and none becomes `Reserved`; invariants 7–9
above continue the decision record's own numbering, which is separate. A repository built from an
earlier copy of the template inherits none of this and should not be migrated merely for
uniformity — its append-only records cite its own paths.

## Validation

`./scripts/check.sh` green: ledger checker at 0 errors, agent checker at 10 roles with regenerated
Codex adapters, 45 checker tests, the numerics suite and calibration lane, and a full `latexmk`
build of the document.
