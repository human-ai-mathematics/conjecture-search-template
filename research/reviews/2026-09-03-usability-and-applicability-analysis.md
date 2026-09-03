---
type: audit
date: "2026-09-03"
supersedes:
  - research/reviews/2026-09-03-template-harness-consistency-analysis.md
---

# Simplicity and applicability analysis of the conjecture-search harness

## Scope

This is a design and usability analysis of the repository as a harness for sustained conjecture
search. It asks whether the current structure is simple to adopt and practical during an actual
multi-session or multi-agent search. It does not certify a proof or change any mathematical
status.

It supersedes the earlier template-harness consistency analysis as the current reading of this
subject. The intervening readiness and consistency work fixed most lifecycle defects identified
there. This report evaluates the resulting repository and records the remaining friction.

## Overall assessment

The architecture should be kept, but its user-facing surface should be simplified. The repository
is a strong harness for sustained, multi-agent conjecture search; it is not yet a simple starter
harness.

It is appropriate when one hard conjecture spans several sessions, routes, or agents and the work
needs durable memory, provenance, and independent review. It is deliberately excessive for a
one-off lemma or broad theory building, which agrees with the scope declared in `CLAUDE.md`.

The right simplification is not to merge the ledger, portfolio, and checkpoints or to weaken
certification. It is to provide better defaults, a shorter operational path, and automation around
the existing epistemic model.

## Strengths to preserve

### Three distinct domains

The central separation is sound:

```text
ledger      = mathematical claims
portfolio   = current search activity
checkpoints = durable reasons and discoveries
```

This prevents route management from contaminating mathematical truth. It also lets the checker
derive views without creating secondary registries that can drift.

### Candidate statements

The candidate mechanism is valuable. A tentative lemma, strengthening, or witness can survive a
session without prematurely becoming a manuscript claim. Promotion is now one explicit act that
adds a manuscript statement and ledger node, records the promotion in a checkpoint, and repoints
portfolio blockers.

### Proof and refutation discipline

Proof and refutation follow an honest certification path. A numerical witness cannot silently
refute a claim: it first becomes a candidate, then a refuter node with an analytic dossier, then an
independently reviewed result. Only afterward can the target move to `refuted` through
`refuted_by`.

### Logical precision

The separation of `depends_on`, `assumes`, and `implies` correctly distinguishes truth from
applicability. Hard `bounded_by` fences are also kept separate from open
`heuristic_barriers`.

### Proportional schemas

Although the complete schemas are rich, a first ledger node needs only six straightforward
fields. The optional graph relations do not burden the minimal case, and the portfolio is absent
until several routes, agents, or sessions need coordination.

### Executable structural checks

The derived commands for status, nodes, candidates, checkpoints, and the portfolio are useful.
The validator is extensively tested and clearly states that structural validity does not establish
mathematical correctness.

## Principal usability findings

### 1. `ready` measures template completion rather than research readiness

The current readiness command requires the LaTeX author, abstract, repository title, and removal
of the instantiation instructions in addition to the target and problem brief. Those publication
and cleanup details are not needed to begin attacking a conjecture.

Research readiness should require only:

- a named program and mathematical scope;
- a canonical target with its ledger node; and
- a completed problem brief naming that target.

Publication metadata should be a separate checklist or a `publish-ready` command. This would make
`ready` answer the operational question its name naturally suggests.

### 2. The worked example demonstrates schemas rather than a real search

The example target is explicitly still a placeholder, and its exact negation and completion
criteria remain instructions. Its portfolio targets that placeholder while the route objectives
actually investigate a separate sum-of-squares identity.

The fixture is structurally useful, but it does not show a newcomer what a good completed brief or
a coherent target-to-route search looks like. The repository needs one small, mathematically
complete example that runs from a precise conjecture through a route and checkpoint to a proof or
refutation and independent certification.

That example should remain outside the live planes. It should replace the current placeholder
content rather than introduce another domain or registry.

### 3. The operational path is scattered across too many documents

A researcher using the `prove` lens is expected to absorb roughly 530 lines across the root
contract, shared execution contract, researcher role, lens, and example-sized brief before reading
the mathematical statement and prior work. The rules are mostly justified, but their context cost
is high.

The repository would benefit from one short "run a search cycle" guide covering:

1. initialization of the target and brief;
2. one research assignment and its handoff;
3. when a checkpoint is required;
4. when the portfolio becomes necessary; and
5. the dossier-review-ledger transition for a claimed result.

The root contract should retain the normative invariants, numbered constraints, write ownership,
and primary verification command. Explanations and historical rationale can remain in the schema
and decision documents.

### 4. Optional capability packs are shipped as active machinery

Seven roles and the numerical package are present in a fresh clone and participate in validation,
even though the documentation describes the specialist roles and numerics as optional. A new user
must remove unwanted specialists and regenerate adapters during initialization.

A simpler default would ship only the four core roles. Numerics, literature scouting, and
repository hygiene could be installable or copyable capability packs. If cross-client support is
not a requirement for a particular repository, it should also be possible to omit the unused
adapter tree.

### 5. There is no scaffold for the routine artifacts

The solution dossier has `solutions/TEMPLATE.tex`, but the brief, portfolio, and checkpoints are
created by copying and editing the worked example. Because that example is instructional and
path-sensitive, copying it is more error-prone than using a dedicated minimal template.

A small initialization command or explicit templates should create:

- the target manuscript environment and minimal ledger node;
- a problem brief with the required sections;
- an optional empty portfolio with one family and route; and
- a dated checkpoint with valid front matter.

This automation would hide schema ceremony without changing the underlying model.

## Structural and lifecycle seams

### Dossier certification metadata has no complete ownership path

The dossier's `checked_by` header is parsed and checked only against the allowed vocabulary. It is
not compared with the active ledger proof mode. Consequently, a dossier may still say
`checked_by: none` while its ledger record says `mode: agent` or `mode: human`.

This does not bypass certification: the ledger still requires the appropriate review or human
identity. It does make the dossier header unreliable. Moreover, the documented workflow creates a
dossier with `checked_by: none`, but it does not clearly assign the later header update to any
role.

The simplest resolution is to remove `checked_by` from the dossier header and let the ledger own
current certification. If the field is retained, assign its update to one writer and require it to
match every active proof record that references the dossier.

### Same-day checkpoint order is inferred from filename slugs

Candidate proposal, retirement, promotion, and supersession order is derived by sorting checkpoint
paths. The validated filename carries a date but no time or sequence number, so two records on the
same day are ordered lexicographically by their arbitrary slugs rather than by the events they
represent.

This can reject a legitimate same-day promotion as occurring before its proposal, or accept the
reverse, solely because of the filenames. The same issue affects same-day audit and checkpoint
supersession.

Use UTC timestamps in durable-record filenames, add an explicit immutable event order, or validate
supersession as an acyclic reference graph without claiming that lexical path order is chronology.

### The verification script can overstate what ran

`scripts/check.sh` prints `all checks passed` when `uv` or `latexmk` is absent, even though the
corresponding suites were skipped. It builds `main.tex` but does not discover and compile every
active standalone solution dossier, despite standalone compilation being part of the proof
definition of done.

The script should distinguish "all available checks passed" from a complete verification. A strict
mode should fail on missing required tools and compile every active dossier named by the ledger.

### The LaTeX claim scanner sees commented source

Claim environments and labels are recognized with regular expressions over the raw module text.
LaTeX comments are not removed first, so a commented-out theorem or label can still enter the
structural claim inventory. At minimum the scanner should remove unescaped `%` comments before
matching. The default summary should also distinguish claim labels from structural labels; a fresh
template currently reports one label even though it has no claim labels.

### Root dependency setup is incomplete

The structural checker requires PyYAML and exits with an installation hint if it is unavailable,
but the root repository has no dependency manifest or single bootstrap command. The separate
numerics project has a lock file, while the primary checker does not.

Provide a root dependency declaration and one reproducible command for structural checks, or make
the primary checker use only the Python standard library.

### Optional-file navigation produces dead links in the fresh template

Several source-of-truth tables link directly to `research/program/brief.md` and
`research/program/portfolio.yaml`, although those files are deliberately absent until their gates
activate. The structural absence is a good invariant, but the resulting navigation is poor for a
new user. Before activation, documentation should link to the dedicated template or worked example
instead of an absent path.

## Recommended minimal operating model

The user-facing lifecycle should be:

```text
canonical target + ledger node
             |
             v
        problem brief
             |
             v
optional portfolio when coordination begins
             |
             v
checkpoint only when something durable survives
             |
             v
dossier + independent review when a result is claimed
             |
             v
        ledger transition
```

Everything else remains an optional capability:

- numerics produces directional artifacts and candidate refutations;
- literature scouting verifies source-backed nodes;
- the synthesizer manages a portfolio only when one exists; and
- repository hygiene does not participate in the mathematical lifecycle.

## Recommended order of improvement

1. Split research readiness from publication and template-cleanup readiness.
2. Replace the placeholder fixture with one coherent, completely filled toy search.
3. Add minimal scaffolds or an initialization command for the target, brief, portfolio, and
   checkpoints.
4. Remove or fully synchronize the dossier's `checked_by` field.
5. Give append-only records a real total order and remove lexical-slug chronology.
6. Make full verification report skipped suites honestly and compile active dossiers.
7. Strip LaTeX comments before scanning claim anchors and clarify label counts.
8. Ship optional specialists as capability packs and reduce the runtime instruction surface.
9. Add a reproducible root dependency/bootstrap contract.

## Conclusion

The harness's core model is already good. Its remaining complexity comes from onboarding,
duplicated certification metadata, scattered operating instructions, and optional machinery that
is present by default. Removing the ledger/portfolio/checkpoint separation would make the harness
smaller but less trustworthy. Hiding schema ceremony and tightening the remaining lifecycle seams
would make it both simpler and more applicable without losing its strongest safeguards.

## Validation baseline

During the read-only analysis that preceded this report:

- `python3 scripts/check.py` reported zero structural errors;
- `python3 scripts/check.py --root example` reported zero structural errors;
- all 125 tests under `scripts/tests/` passed;
- all 16 tests under `experiments/tests/` passed; and
- the worktree was clean.

The LaTeX build was not run because it would update generated files under `build/`. This new audit
report is the only repository change made to preserve the analysis.
