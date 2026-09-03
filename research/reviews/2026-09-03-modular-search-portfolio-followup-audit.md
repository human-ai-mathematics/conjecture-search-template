---
type: audit
date: "2026-09-03"
---

# Follow-up audit of the modular search portfolio

## Scope

This is a read-only design audit of the implementation adopted in
[`../../decisions/2026-09-03-modular-search-portfolio.md`](../../decisions/2026-09-03-modular-search-portfolio.md),
following the recommendations in
[`2026-09-03-simple-modular-search-portfolio-analysis.md`](2026-09-03-simple-modular-search-portfolio-analysis.md).
It assesses whether the new design reduces administrative overhead, manages a search portfolio,
and curates append-only memory without confusing search state with mathematical state.

This audit recommends a focused consistency pass but adopts no harness, schema, role, or workflow
change. It certifies no proof or mathematical statement. No files were modified during the audit,
and validation commands were not run at the user's request.

## Overall assessment

The redesign is a strong architectural improvement. The template now manages a search rather
than merely archiving attempts. The scope is explicit, persistence is gated, the portfolio is
separate from the claim graph, stale audits have a supersession path, and author/reviewer
separation survived the role consolidation.

It is best regarded as a successful prototype that needs one focused consistency pass before the
new architecture is stable. Its main remaining weakness is that “modular” and “simple” have
diverged: operational overhead is lower, but the static contracts, prompts, validators, and tests
are larger, and several old coordination concepts still overlap the new portfolio.

## Improvements that succeeded

### The scope is now honest

`CLAUDE.md` states that this is a harness for sustained conjecture proving or refuting, not a
general mathematical-research harness. This converts several criticisms in the earlier
research-modes audit into deliberate boundaries rather than partially served ambitions.

### Persistence is proportional to research value

An exploration is now a checkpoint created for a durable search event, not a mandatory transcript
of every nontrivial attempt. Cheap speculative work can disappear, while reusable dead ends,
blockers, candidates, artifacts, portfolio changes, and synthesis remain durable.

This addresses the most important source of day-to-day administrative overhead.

### The portfolio captures actual search topology

The new portfolio represents:

- approach families and their mechanisms;
- parent approaches, from which siblings and descendants can be derived;
- queued, active, blocked, completed, and duplicate routes;
- precise blockers identified by candidate or ledger-node id;
- reopening conditions;
- overlap, duplication, and refinement relations; and
- saturation or parking supported by a checkpoint.

Requiring a blocker to resolve to a live candidate or ledger node is particularly valuable. It
prevents a vague phrase such as “the compatibility step is hard” from acquiring the operational
force of a precise missing lemma.

### Append-only memory now has a current-reading mechanism

`supersedes:` distinguishes an obsolete operational summary from deleted history. Candidate
retirement remains a separate operation with separate meaning. Extending supersession to audits
directly addresses the stale-audit problem demonstrated by the earlier research-modes review.

### Epistemic controls survived the simplification

The researcher and reviewer retain disjoint write surfaces. A fresh dossier has no ledger value
until independently reviewed, and a proof review remains structurally different from a
non-certifying audit. Numerical output still cannot silently become a proof or a status change.

### The checker has a better public shape

One entry point now exposes plane-tagged validation and derived views for the mathematical
frontier, portfolio, checkpoint heads, candidates, and individual nodes. The implementation is
split by plane internally, which makes the code easier to locate and reason about even though the
overall validation surface has grown.

## Important remaining inconsistencies

### 1. The ledger still contains an old coordination route mechanism

`CLAUDE.md` constraint 12 says that approach families and route states never enter the ledger.
The ledger schema nevertheless retains `meta.route_policy` and per-node `route`, explicitly
described as coordination ownership.

This leaves two homes for coordination:

- ledger routes; and
- portfolio families and approaches.

That conflicts with the new separation of mathematical state from search state. Either remove
`route_policy` and `route` from the ledger, or redefine the field as a genuinely mathematical
classification such as `component` or `topic`. In its current meaning, it belongs in the
portfolio.

### 2. Portfolio changes do not yet require their checkpoint explanation

The portfolio checker verifies that a listed checkpoint path exists under
`research/explorations/`, but it does not verify that:

- the file was parsed as a valid checkpoint;
- a checkpoint declaring `approach:` agrees with the approach that lists it; or
- a blocked, completed, or duplicate approach has any checkpoint at all.

The portfolio can therefore pass while a state change has no durable explanation, contrary to
the governing sentence “Checkpoints = why the portfolio changed.” A path can also satisfy the
portfolio's containment check without being a record in the checkpoint index.

The intended invariant should be enforced as follows:

1. `blocked`, `completed`, and `duplicate` approaches require at least one checkpoint.
2. Every portfolio checkpoint reference resolves through the parsed checkpoint index, not only
   through the filesystem.
3. If a referenced checkpoint declares `approach:`, it must name the approach that lists it.
4. A legacy checkpoint without `approach:` may still be attached from the portfolio side, so
   existing append-only records need not be edited.
5. A `saturation_checkpoint` must likewise be a parsed checkpoint rather than merely an existing
   Markdown file.

### 3. A closed family may still contain queued work

The checker prevents a `saturated` or `parked` family from containing an `active` approach, but it
permits a `queued` approach. A queued route is planned live work, so the family has not actually
closed.

Closed families should reject both `active` and `queued` approaches.

The field name `saturation_checkpoint` is also misleading for a `parked` family. Parking can be a
budget or prioritization decision rather than a claim that a mechanism has been exhausted.
Renaming it `closure_checkpoint`, or removing `parked` until a distinct lifecycle is needed,
would keep the vocabulary honest.

### 4. The brief and manuscript both appear to own the exact target

`research/README.md` names the brief as the source of truth for the exact target. The brief itself
says the statement lives in the manuscript and its logical state lives in the ledger, while also
asking the brief author to state the exact target with every quantifier.

That creates a possible duplicate mathematical statement. A clearer ownership boundary is:

- manuscript: canonical quantified target;
- ledger: target identity, status, provenance, and relations;
- brief: target id, exact negation, completion and refutation criteria, edge cases, traps, audit
  tests, and search policy.

If the brief restates the target for convenience, the reviewer's `sync` lens should compare that
text with the manuscript and ledger too.

This also clarifies the activation gates. A sustained conjecture search necessarily begins with a
precise target ledger node. The current table suggests the claim graph activates later, even
though the brief and portfolio require targets that resolve to the ledger.

### 5. A plane-scoped portfolio check can omit an unresolved target

Brief and portfolio target resolution is guarded by the condition that the derived ledger-node
set be nonempty. If the ledger is absent or cannot be loaded, a run reporting only portfolio-plane
errors can omit the unresolved-target error while the core error is filtered out.

Cross-plane validation should report that the portfolio target cannot be validated because its
ledger plane is unavailable. Scoping should restrict presentation, not turn an unresolved
dependency into a successful validation.

## Modularity and complexity

### Operational simplicity improved

The checkpoint policy is a real reduction in routine cost. A search no longer creates a durable
file merely because an agent spent time on an idea. The brief and portfolio also reduce the time
future agents spend reconstructing context from prose.

### Static and prompt complexity increased

The comparable root contracts, role contracts, validators, and tests grew from approximately
3,943 lines before the redesign to approximately 5,400 lines afterward. Line count is not itself
a defect, especially when tests explain the growth, but it shows that the redesign moved
complexity rather than simply removing it.

The consolidated `researcher` role is the clearest example. It contains complete `prove`,
`refute`, `mine`, and `construct` instructions. A researcher assigned the proof lens still
receives the other three lenses in its generated adapter and must read a larger shared contract,
role contract, and brief before doing mathematics.

A more genuinely modular shape would be:

```text
.claude/agents/researcher.md
.claude/lenses/prove.md
.claude/lenses/refute.md
.claude/lenses/mine.md
.claude/lenses/construct.md
```

The researcher role would retain the shared permissions, epistemic rules, write surface, and
handoff. Each assignment would load exactly one lens. This preserves a small role roster without
paying the prompt cost of every strategy on every invocation.

The same observation applies, less strongly, to the reviewer's `certify` and `sync` lenses.

### Optional specialists are not yet optional packaging

The documentation correctly identifies `numerics`, `literature-scout`, and `janitor` as optional
specialists, but the instantiation guide still describes all seven roles as the backbone and the
template ships every specialist and its adapter. The architecture is optional in policy, not yet
in distribution.

This is acceptable for a working template, but a genuinely minimal distribution would keep four
core roles and install specialist packs only when used.

## Smaller findings

### Numerical evidence is restricted too broadly in the researcher contract

The researcher forbids numerical evidence as a proof step, justification, or plausibility
argument. The proof restriction is correct; the plausibility restriction conflicts with the
purpose of directional numerics. Reproducible numerical evidence should be permitted to guide
route selection and conjecture generation while remaining inadmissible as proof justification.

### A live bibliography comment is stale

`references.bib` still says that a literature node has `status: imported` and that
`scripts/check_ledger.py` validates its references. Both names are obsolete in the current
schema. This is a live navigation comment rather than immutable historical prose.

### Audit supersession is not fully visible in the derived view

The checkpoint view lists audits that have been superseded, but it does not list the current audit
heads or show which later audit replaced each old one. The replacement is discoverable only by
reading or searching the archive. A current-memory view would be more useful if it displayed the
superseding record directly.

### The current change is not yet a clean version-control boundary

At the time of this audit, the worktree contains a broad mixture of modified files, deleted old
roles and validators, and untracked replacements. This is expected during a redesign but makes
the current state harder to review or bisect as a unit.

## Recommended next pass

Keep the architecture and make a narrow consistency pass:

1. Remove or mathematically redefine the ledger's `route` mechanism.
2. Enforce portfolio-to-checkpoint consistency in both directions.
3. Reject queued routes inside closed families and clarify the meaning of `parked`.
4. Resolve ownership of the exact target between brief, manuscript, and ledger.
5. Make an unavailable claim graph an explicit portfolio-plane dependency error.
6. Split researcher and reviewer lenses into separately loaded instruction modules.
7. Sweep live documentation for obsolete commands and vocabulary.

These changes would preserve the new architecture while making it structurally stronger and more
genuinely modular.

## Outcome

The redesign successfully fixes the original coordination problem and substantially lowers the
cost of exploratory work. It should be retained. Before calling it stable, resolve the remaining
route duplication, cross-plane checkpoint gaps, target ownership ambiguity, and prompt-size
growth identified above.

No validation result is asserted by this audit.
