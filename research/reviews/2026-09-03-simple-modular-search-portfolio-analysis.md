---
type: audit
date: "2026-09-03"
---

# A simpler, modular search portfolio for conjecture research

## Scope

This is a design analysis of the repository as a harness for proving or refuting conjectures. It
focuses on three findings from
[`2026-09-02-template-vs-raw-prompt-analysis.md`](2026-09-02-template-vs-raw-prompt-analysis.md):
administrative overhead, the absence of explicit search-portfolio state, and the continuing need
to curate append-only memory. It also takes account of
[`2026-09-02-mathematical-research-modes-audit.md`](2026-09-02-mathematical-research-modes-audit.md).

This audit recommends a direction but adopts no harness, schema, role, or workflow change. It
certifies no proof or mathematical statement.

## Overall recommendation

Make the template explicitly a conjecture-search harness and organize it as a progression of
gates rather than requiring the entire machinery for every attempt.

The ledger should remain the source of mathematical truth. A new, small portfolio layer should
manage live search activity. The exploration directory should become a curated checkpoint log,
not a transcript of every agent turn.

The governing separation should be:

> Ledger = what is mathematically claimed. Portfolio = what the search is doing. Explorations =
> why the portfolio changed.

## Diagnosis

### The principal overhead is operational

The cost is not merely the number of files or lines in the template. The root workflow requires a
new exploration for every nontrivial attempt, including dead ends, and the exploration contract
repeats that requirement. Consequently:

- a cheap speculative calculation pays the same recording tax as a reusable obstruction;
- a large parallel search can accumulate hundreds of records without revealing which approach
  families remain alive; and
- the synthesizer must reconstruct approach identity, duplication, blockers, and saturation from
  prose.

At the time of this audit, the root contract, ledger and exploration contracts, ten role
definitions, ledger and agent validators, and their tests contain approximately 4,000 lines.
Static machinery of this size is acceptable when it is activated only as needed. It is excessive
when presented as the universal path for an afternoon's exploratory work.

### The attempt log is not a portfolio

The current exploration envelope records nodes, outcome, candidates, retired candidates, and run
artifacts. It does not record the mathematical family of an approach, its parent, its conceptual
overlap with another route, its exact blocker, or the condition that would justify reopening it.

Those concepts do not belong in the ledger: they describe research activity rather than the
truth, provenance, or dependencies of mathematical claims. They do require a structured home if
the harness is to coordinate a large search rather than merely remember it afterward.

### The existing archive demonstrates the curation problem

The mathematical-research-modes audit reports that `conditional` and `imported` mix orthogonal
ledger concepts and that the template supports only one active proof. Those observations have
already been superseded by
[`../decisions/2026-09-02-conjecture-solving-ledger-semantics.md`](../../decisions/2026-09-02-conjecture-solving-ledger-semantics.md):
the current schema separates `status` from `provenance`, separates truth from applicability with
`assumes`, and permits multiple `proofs` records.

The old audit remains useful history, but a reader has no structural way to learn that these
parts are no longer current. This is exactly the weakness identified in the reviews: append-only
storage preserves provenance but does not supply a current view.

## A progressively activated architecture

Use five layers, activated by the work rather than by a global mode flag:

| layer | activation condition | durable state |
|---|---|---|
| problem brief | any sustained conjecture search | exact target and negation, completion criteria, edge cases, known traps |
| live search | multiple agents, routes, or sessions | mutable approach portfolio |
| checkpoint memory | a result affects future search | curated exploration records |
| claim graph | a statement is stable and reusable | manuscript statement and ledger node |
| certification | a proof or refutation is claimed | dossier and independent review |

Numerics, literature work, formalization, and proof-producing computation should remain optional
capability packs.

This should not be implemented as several configured profiles such as `quick`, `full`, and
`formal`. Profiles tend to spread conditional rules through every contract. Activation can be
structural instead:

- no numerical work means the numerics contract is irrelevant;
- no claimed proof means the certification contract is irrelevant;
- no multi-session or parallel search means a portfolio is unnecessary; and
- an afternoon of speculative work may produce no repository artifact at all.

Once something must survive a session or coordinate another researcher, it crosses the relevant
persistence gate.

## A mutable search portfolio

The current program contract already permits mutable route briefs, target briefs, and gating
tables under `research/program/`. A portfolio such as `research/program/portfolio.yaml` fits that
existing seam. It is not a forbidden second home for mathematical results if it stores only
coordination state and refers to exact statements through candidate or ledger identifiers.

A deliberately small shape would be:

```yaml
target: q:main-conjecture

families:
  - id: fam:localization
    mechanism: Reduce the claim through localization.
    state: active

  - id: fam:transport
    mechanism: Construct a transport or coupling argument.
    state: saturated
    saturation_checkpoint: research/explorations/2026-09-03-transport-synthesis.md
    reopen_if: A construction avoiding cand:transport-compatibility is found.

approaches:
  - id: ap:transport-gluing
    family: fam:transport
    parent: ap:transport-local
    state: blocked
    blocker: cand:transport-compatibility
    reopen_if: The blocker is proved, weakened, or bypassed by a new mechanism.
    related:
      - to: ap:localization-patching
        relation: overlaps
    checkpoints:
      - research/explorations/2026-09-03-transport-gluing.md
```

Keep the vocabulary small:

- family state: `active`, `saturated`, or `parked`;
- approach state: `queued`, `active`, `blocked`, `completed`, or `duplicate`;
- approach relations: `overlaps`, `duplicates`, or `refines`;
- `parent` defines the tree, so siblings are derived rather than stored;
- a blocked approach requires both `blocker` and `reopen_if`; and
- a saturated family requires a synthesis checkpoint and reopening condition.

An exact blocker should resolve to a `cand:` id or ledger node. If a route is important enough to
be formally blocked, its missing lemma is important enough to be stated precisely. The portfolio
does not copy that statement.

Saturation remains a synthesizer judgment. A validator may ensure that the declaration has a
checkpoint, no unexplained active child, and a reopening condition; it cannot infer mathematical
exhaustion from attempt counts.

The portfolio is a single-file write-contention point. One synthesizer, or the orchestrator,
should own it. Parallel researchers return proposed changes through their handoff rather than
editing it concurrently.

## Explorations should be checkpoints, not transcripts

Replace “one file per nontrivial attempt” with “one file per durable search event.” An exploration
should be required when work:

- creates or retires a candidate;
- identifies a reusable dead end or exact blocker;
- blocks, reopens, duplicates, or saturates an approach;
- produces a numerical or literature artifact that future work may use;
- proposes a manuscript or ledger change; or
- synthesizes a batch of parallel work.

A speculative calculation that fails immediately need not be recorded. A dead end should become
durable when it is plausible or expensive enough that another researcher might repeat it.

Only two additions to the exploration envelope are needed:

```yaml
approach: ap:transport-gluing
supersedes:
  - research/explorations/2026-09-02-earlier-summary.md
```

`approach` connects durable memory to the portfolio. `supersedes` allows a default memory view to
show current checkpoint heads while retaining the full archive.

Candidate retirement and record supersession have different meanings:

- `retires:` says that a tentative mathematical statement is no longer live;
- `supersedes:` says that a later operational summary should be read instead of an earlier one;
- neither operation deletes or rewrites history.

The same generic supersession relation can apply to non-certifying audits. Proof-certification
reviews and decision records should keep their stricter existing semantics.

## A smaller core role system

Four core roles are sufficient for conjecture search:

| role | responsibility |
|---|---|
| `scout` | read-only orientation on an unfamiliar target or route |
| `researcher` | proof attempts, refutation attempts, proof mining, and constructions |
| `reviewer` | independent audit of a proposed proof or refutation |
| `synthesizer` | portfolio curation, deduplication, saturation, and convergence |

Refutation seeking, proof mining, and other mathematical strategies can be assignment lenses for
the `researcher`, not permanent role contracts. Numerics, literature, formal or certificate
checking, and repository hygiene remain optional specialists.

Author and reviewer separation must remain. That is an epistemic control rather than
administrative ornament.

## Validation should be modular by plane

`check_ledger.py` currently validates the ledger, proof records, reviews, explorations,
candidates, and artifact references. Its name and scope have diverged. Retain one user-facing
entry point but split its checks internally by plane, for example:

```text
scripts/check.py core
scripts/check.py portfolio
scripts/check.py proofs
scripts/check.py numerics
scripts/check.py all
```

The fast default should validate only the planes present or used. The full lane remains suitable
for CI and releases.

Portfolio validation should remain structural:

- ids and references resolve;
- state-specific fields are present;
- blocked and saturated routes have reopening data;
- duplicate routes are not simultaneously active;
- supersession references older records and is acyclic; and
- blocker references resolve to candidates or ledger nodes.

It should not attempt to validate conceptual overlap, novelty, or genuine mathematical
saturation.

## Suggested implementation order

1. State the scope explicitly: sustained conjecture proving and refuting, not every mathematical
   research mode.
2. Add the exact problem brief.
3. Add the mutable portfolio and a small validator/status view.
4. Relax the exploration rule from every attempt to every durable checkpoint.
5. Add `approach` and `supersedes` to checkpoint metadata.
6. Give the synthesizer explicit portfolio ownership and curation duties.
7. Collapse the core role roster.
8. Later, split validator implementation and optional capability packs.

The first five changes address the coordination gap without changing ledger semantics, proof
certification, or numerical provenance.

## Non-goals and guardrails

- Do not put approach families, agent activity, or route saturation in the ledger.
- Do not turn transient approaches into ledger nodes.
- Do not let the portfolio restate mathematical claims or duplicate the dependency graph.
- Do not declare saturation automatically from elapsed time or attempt counts.
- Do not broaden the core to applied modeling, databases, and every other research mode before
  the conjecture-search workflow is sound.
- Do not rewrite old explorations or audits during migration.

## Migration boundary

Existing append-only records remain unchanged. A later decision adopting this design can apply
the new rules prospectively, create the initial portfolio through one synthesis pass, and use a
new audit or checkpoint to supersede stale operational summaries. Historical proof reviews and
decision records retain their present meaning.

## Outcome

Recommended, but not adopted: a small mutable portfolio, checkpoint-based durable memory, a
four-role core, and optional evidence and certification modules. No repository contract or
mathematical status changes as a result of this audit.
