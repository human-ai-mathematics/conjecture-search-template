# CLAUDE.md — repository contract

`AGENTS.md` is a symlink to this file, so Claude Code and Codex receive the same instructions.
This is the root contract for work entering the repository. Scoped contracts may add narrower
requirements: [`research/program/ledger-schema.md`](research/program/ledger-schema.md) for the
ledger, [`research/program/portfolio-schema.md`](research/program/portfolio-schema.md) for the
search portfolio, [`solutions/README.md`](solutions/README.md) for proofs,
[`experiments/README.md`](experiments/README.md) for numerical work,
[`.claude/agents/`](.claude/agents/README.md) for role permissions, and
[`.claude/lenses/`](.claude/lenses/README.md) for the assignment lenses those roles load.
They never override this file. Use [`research/README.md`](research/README.md) to locate each
domain's source of truth; other READMEs are navigation maps.

Three words, three meanings, kept apart on purpose. A **domain** is one of the three things
the repository is organized into — mathematical state, search state, durable evidence; the
`README.md` table lists them. A **gate** is an optional layer the work activates, listed
below. A **lane** is an implementation partition of `scripts/check.py`, selected with
`--lane`. Nothing lines the three up, and nothing should.

## Scope

This is a harness for **sustained conjecture search**: proving or refuting one hard statement,
over many sessions and several agents at once, without losing what the search has learned.

It is deliberately not a general mathematical-research harness. Theory building,
classification, algorithm design, exposition, and computer-assisted proof with first-class
certificates are all outside what it is tuned for. Say so plainly rather than bending the
machinery, and add what a different mode needs as a new domain of its own.

The separation everything else follows from:

> Ledger = what is mathematically claimed. Portfolio = what the search is doing.
> Checkpoints = why the portfolio changed.

## The gates

Nothing here is a global mode flag. Each gate is activated by the work itself, and a gate
whose files are absent has no rules to obey — `python3 scripts/check.py` validates only what
exists. A fresh clone therefore passes `check` while `check.py ready` correctly reports it as
an uninstantiated template.

| gate | activate when | durable state |
|---|---|---|
| claim graph | a statement is precise, stable, and reusable | a manuscript statement and a ledger node |
| problem brief | a sustained search starts | target node, exact negation, completion criteria, edge cases, known traps |
| search portfolio | several routes, agents, or sessions are in flight | approach families, route states, blockers, saturation |
| checkpoint memory | a result will affect future search | dated records in `research/explorations/` |
| certification | a proof or refutation is claimed | a standalone dossier and an independent review |

The order is not arbitrary at the top. A sustained search opens with a target precise enough to
be a ledger node, because the brief and the portfolio both name one and must resolve to it; the
claim graph is therefore the first gate a search crosses, not a later one. A portfolio also
requires a brief, for the same reason in the other direction: several coordinated routes *are*
a sustained search. After that the gates are independent.

Numerics, literature import, and repository hygiene are capability packs on the same footing:
present when used, irrelevant when not.

An afternoon of speculative work may cross none of these and leave no repository artifact at
all. That is a correct outcome, not a gap. Something crosses a gate when it must survive the
session or coordinate someone else.

## Workflow

### Search contribution

1. Read the problem brief. Attack the target through the one lens you were assigned.
2. **Record a checkpoint** in a new `research/explorations/YYYY-MM-DD-slug.md` when the work
   is durable — see [`research/explorations/README.md`](research/explorations/README.md) for
   the six triggers and the validated front matter. A speculative calculation that dies in ten
   minutes needs no file; a dead end plausible or expensive enough that the next agent would
   repeat it does.
3. A statement not yet stable enough for the manuscript and ledger is a **candidate**: it goes
   in that checkpoint's `candidates:` list and nowhere else (constraint 8). When one is
   promoted, the checkpoint that records the promotion is what ends it — see constraint 8.
4. Return a `portfolio_delta` in your handoff — the state your route is now in, and if it is
   blocked, the exact `cand:` id or ledger node it is blocked on plus what would reopen it.
   The `synthesizer` applies it; you do not edit the portfolio.

### Mathematical contribution

1. Sharpen or confirm a target, or supply a standalone proof dossier.
2. When a claim changes, update its manuscript statement and ledger state, provenance, and
   edges together.
3. After a ledger edit, leave `python3 scripts/check.py` at 0 errors.
4. A finding reusable enough to be cited elsewhere earns a ledger node and a manuscript
   statement, not a second home in a side registry.

### Proof or refutation contribution

Follow [`solutions/README.md`](solutions/README.md). An author never certifies their own proof;
`proofs[].mode: agent` requires a persisted review naming distinct author(s) and reviewer.

Refuting takes the same channel. A witness is a candidate; the statement it establishes becomes
a refuter node with a manuscript statement and an ordinary dossier; that dossier is certified
like any other; and only then does the target become `refuted`, naming the proved refuter in
`refuted_by` and not in `depends_on`. A run artifact is never a step in that chain
(constraints 2 and 11).

### Harness or repository contribution

Record the rationale and validation in a new `decisions/YYYY-MM-DD-slug.md`. Do not invent a
mathematical attempt; harness work does not by itself change mathematical status.

## Hard constraints

These are the universal constraints. They are numbered, and append-only records cite the
numbers, so **do not renumber them** — a constraint that stops applying becomes `**Reserved.**`
and keeps its slot. Constraints specific to this repository's mathematics go in the next
section, numbered `P1, P2, …`, so that a fork can drop them without disturbing this list.

1. **A ledger is a single-file write-contention point.** This repository has exactly one program
   ledger, `research/program/ledger.yaml`. Funnel every ledger edit through one orchestrator.
   Role definitions may narrow write access; no spawned role writes the ledger.
2. **Numerical work must be public and reproducible.** All numerical experiments must be executed
   through the `numerics` harness into a provenance-stamped artifact. Numerical output certifies no
   claim, proof step, or dossier. Exact arithmetic or an analytic witness it emits remains a
   candidate until checked independently in the proof or refutation workflow.
3. **The research battery is shared.** Use `research/instances.md`. Anyone may propose
   an adversarial instance; only the `synthesizer` curates the registry. Passing a finite battery
   changes no claim or proof status.
4. **`check.py` is necessary, not sufficient.** A green check establishes structure only.
   Semantic agreement among manuscript, ledger, and dossier, and the correctness of a proof,
   require independent review.
5. **Respect established fences.** `bounded_by` may name only a proved obstruction. A statement
   violating one is wrong by construction. Put plausible but unproved method barriers in
   `heuristic_barriers`; they guide work but do not logically fence a claim.
6. **Reserved.**
7. **`research/explorations/` and `decisions/` are append-only.** Add dated files; never
   rewrite or delete their history. A later record may declare an earlier one superseded —
   that changes which record to read first, and nothing else. This governs records of *this
   program's* search. The worked example under `example/` is a fixture, not history: it
   records no search anyone ran, and may be edited or deleted freely.
8. **A candidate statement is not a ledger node.** A tentative statement lives in
   the `candidates:` front matter of the checkpoint that proposed it, under a `cand:<slug>`
   id, and carries no manuscript anchor, no status, and no certification. It is killed by a
   later checkpoint naming it in `retires:`. Once it is precise, stable, and worth reusing or
   tracking on the research frontier, promote it, at which point it is subject to every
   constraint above.
   Promotion is **one act**, not a node addition with paperwork to follow: the manuscript
   `\label`, the ledger node, a `promotes:` entry in a checkpoint — which is what ends the
   candidate — and every portfolio blocker repointed at the node. Skipping the third step
   left the candidate live forever, which is one statement in two homes, which is what this
   constraint exists to prevent.
   `python3 scripts/check.py candidates` lists the live ones. There is no other place a
   statement may be written down. A verbatim quotation of a manuscript statement, marked as a
   copy, is not a second home — the problem brief may quote its target that way, and the
   `reviewer`'s `sync` lens checks that the copy still agrees. A ledger node's `summary:` is
   a gloss, not a home; the candidate's `statement:` is canonical, because nothing else holds
   that text.
9. **Truth and applicability are separate.** A proved implication remains `proved` when its
   antecedent is open. Put antecedents in `assumes`, conclusions in `implies`, and only claims
   actually used to prove the implication in `depends_on`. Never encode an antecedent as a proof
   dependency merely to make a conditional status propagate.
10. **Proof provenance is plural.** An internally proved node has one or more `proofs` records.
    Each record names its dossier and independent certification mode, so alternative proofs can
    coexist. A dossier may reuse certified dependency nodes instead of reproving them.
11. **Quantifiers govern refutation.** A refutation dossier must negate the exact quantified
    statement. A single witness refutes a universal claim; failure of a dimension-free or
    uniform constant generally requires a certified family with the relevant divergence. The
    refuter is an ordinary proved node: it appears in the target's `refuted_by` and never in
    its `depends_on`, which records facts a proof used and a refuted statement has none.
12. **The portfolio is search state, not mathematical state.** `research/program/portfolio.yaml`
    records what the search is doing — approach families, route objectives and states, blockers,
    saturation — and has one writer, the `synthesizer`. It never restates a claim: a blocker is
    named by its `cand:` id or ledger node id, and nothing is copied. A route's `objective` says
    what it tries, which is an intention and not a claim. Approach families and route states
    never enter the ledger, and a transient route never becomes a node. Saturation is a
    judgment that costs a synthesis checkpoint and a reopening condition; it is never inferred
    from attempt counts or elapsed time.

## Program constraints

Constraints that depend on this repository's mathematics. Use them for merge barriers — a
comparison exactly one agent may hold — and for anything a fork of this template would not
inherit. Same rule: numbered, cited, never renumbered.

<!-- Delete this comment and add constraints as the program grows. A merge
     barrier states the objects compared, what is and is not proved between
     them, and who holds the comparison. Name the same owner in
     .claude/agents/synthesizer.md. -->

*(none yet)*

## Global convention

Write Markdown mathematics in LaTeX `$...$`.

## Verify

```bash
./scripts/check.sh                    # everything below, in order

python3 scripts/check.py              # 0 errors required after any ledger edit
python3 scripts/check.py --lane core  # one lane: core|proofs|checkpoints|portfolio|numerics|roles
python3 scripts/check.py ready        # is this repository instantiated, or still the template?
python3 scripts/check.py status       # the live frontier
python3 scripts/check.py portfolio    # the live search
python3 scripts/check.py checkpoints  # current heads of durable memory
python3 scripts/check.py candidates   # statements proposed but not yet nodes
python3 scripts/check.py --root example   # the worked example, kept green as a fixture
```

`check` and `ready` answer different questions. A freshly cloned template passes `check` and
fails `ready`, and both are correct: activation is structural, so an absent optional plane is
valid, while `ready` asks whether the placeholders are gone and a search has something to aim
at. Neither weakens the other.
