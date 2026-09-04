# Running a search

The operational path, end to end, in one file. [`../CLAUDE.md`](../CLAUDE.md) is the
contract and wins on any conflict; this is how the contract is actually used.

Read [`../example/README.md`](../example/README.md) alongside it: that tree is one complete
search of exactly this shape, and every step below points at the file in it that shows the
step finished.

```text
  target + ledger node
          ↓
     problem brief                       ← a search starts here
          ↓
  portfolio, when coordination begins    ← optional
          ↓
  checkpoint, when something durable survives
          ↓
  dossier + independent review           ← when a result is claimed
          ↓
     ledger transition
```

Everything else — numerics, literature import, hygiene — is a capability activated by the
work and skipped otherwise.

---

## 1. Initialize: the target and the brief

A sustained search opens with a target precise enough to be a ledger node, because the
brief and the portfolio both name one and must resolve to it.

```bash
python3 scripts/new.py module 00-overview --node conj:main --kind conjecture
python3 scripts/new.py node conj:main --kind conjecture      # prints; you paste it
python3 scripts/new.py brief --target conj:main
python3 scripts/check.py ready                               # the checklist, executable
```

State the conjecture in `modules/` inside the environment matching its kind, under
`\label{conj:main}`. Paste the printed node under `nodes:` in
`research/program/ledger.yaml` — the scaffolder deliberately does not write that file, which
has exactly one writer (constraint 1).

Then **write the brief**. This is the step that is skipped and should not be: the harness
remembers, validates and certifies, and supplies no mathematical pressure of its own. The
brief is the only document that knows the exact negation, what would count as finishing,
the five things that actually go wrong in this problem, and which disguises a dead route
wears. `ready` fails until it is written, and that is the point.

> Finished example: [`example/research/program/brief.md`](../example/research/program/brief.md).

`python3 scripts/check.py publish-ready` asks the separate question of whether the
manuscript has a title, an author and an abstract. It blocks nothing here.

## 2. One assignment, one lens, one handoff

Roles live in [`../.claude/agents/`](../.claude/agents/README.md); the strategies they are
pointed at are [lenses](../.claude/lenses/README.md). An assignment names **one** role and
**one** lens — a role that surveys four strategies produces a shallow pass on all four.

| you want | role, lens |
|---|---|
| orientation on an unfamiliar node | `scout` |
| a proof attempt | `researcher`, `prove` |
| a counterexample hunt | `researcher`, `refute` |
| to learn what an existing proof really buys | `researcher`, `mine` |
| an object built to order | `researcher`, `construct` |
| a dossier certified | `reviewer`, `certify` |
| manuscript/ledger/dossier agreement audited | `reviewer`, `sync` |
| parallel work converged, routes deduplicated | `synthesizer` |

The author never certifies their own work: `mode: agent` requires a persisted review naming
distinct author(s) and reviewer. Launch the reviewer cold when the runtime allows it.

Every role returns the same handoff envelope — `outcome`, `artifacts`, `proposed_deltas`,
`portfolio_delta`, `next_role`, `next_prompt`. The orchestrator (the main session) applies
the deltas; no spawned role writes the ledger, the brief, the bibliography, or the
manuscript. The `synthesizer` alone writes the portfolio.

`numerics`, `literature-scout` and `janitor` are [capability packs](../packs/README.md),
installed when first needed:

```bash
python3 scripts/new.py role numerics
```

## 3. When a checkpoint is required

Not per attempt — per **durable search event**. The six triggers are listed once, in
[`../research/explorations/README.md`](../research/explorations/README.md), along with the
validated front matter; they are not repeated here.

```bash
python3 scripts/new.py checkpoint constant-vectors --node conj:main
```

The judgment they encode: a speculative calculation that dies in ten minutes needs no file. A dead end becomes durable
when it is plausible or expensive enough that another agent would repeat it. Recording
everything is how a log stops being read; recording nothing is how a week gets spent twice.

A statement not yet stable enough for the manuscript is a **candidate**: it goes in that
checkpoint's `candidates:` list under a `cand:` id and nowhere else (constraint 7).

> Finished example: [`example/research/explorations/`](../example/research/explorations/).

## 4. When the portfolio becomes necessary

When several routes, agents, or sessions are in flight and somebody has to know which are
still alive. Not before — a portfolio with one route is bookkeeping.

```bash
python3 scripts/new.py portfolio --target conj:main
```

It records what the search is *doing*, never what is claimed: approach families, route
objectives and states, blockers, saturation. A blocker is named by its `cand:` id or node id
and never restated (constraint 11). One writer, the `synthesizer`; everyone else proposes
through `portfolio_delta`.

Saturation is a judgment, not a count. It costs a synthesis checkpoint and a reopening
condition.

## 5. Claiming a result

Proving and refuting take the same channel, and neither skips the gate.

```bash
python3 scripts/new.py dossier lem:key      # a standalone .tex under solutions/
cd solutions && latexmk -pdf -outdir=../build lem-key.tex
```

1. **Dossier.** A standalone `.tex` that an independent reviewer can pick up. It records no
   certification — a dossier that no `proofs[]` record names is a draft, and that absence is
   the whole signal.
2. **Independent review.** A distinct agent, on the `certify` lens, leaves a persisted
   report under `research/reviews/`.
3. **Ledger transition.** The orchestrator adds `proofs: [{artifact, mode, review}]` and
   moves `status`.

**Refuting adds two steps in front.** The witness is a *candidate*; the statement it
establishes becomes a **refuter node** with its own manuscript statement and its own
ordinary dossier; that dossier is certified like any other; and only then does the target
become `refuted`, naming the proved refuter in `refuted_by` — never in `depends_on`, which
records facts a proof used, and a refuted statement has no proof.

A run artifact is never a step in that chain (constraints 2 and 10). Numerical output
certifies nothing; an exact witness it emits is a candidate until checked independently.

> Finished example: [`…/2026-09-03-example-refuter.md`](../example/research/explorations/2026-09-03-example-refuter.md)
> walks all five steps.

---

## Checking your work

```bash
./scripts/check.sh                     # everything available, honest about what it skipped
./scripts/check.sh --strict            # a missing tool is a failure, not a skip
python3 scripts/check.py               # 0 errors required after any ledger edit
python3 scripts/check.py status        # the live frontier
python3 scripts/check.py portfolio     # the live search
python3 scripts/check.py candidates    # statements proposed but not yet nodes
python3 scripts/check.py checkpoints   # current heads of durable memory
```

A green check establishes structure only. It says nothing about whether a proof is correct
(constraint 4) — that is what the review is for.

## Showing it to someone

`python3 scripts/site.py --serve` renders everything above as a website: the target, the
claim graph, the search map, the blockers, and the dated records explaining why each route
stopped. It is a derived view that refuses to publish a tree which does not validate, and
it is optional. [`PUBLISHING-THE-SITE.md`](PUBLISHING-THE-SITE.md) covers the deployment
and the public contribution inbox, which changes nothing by itself
([`../CLAUDE.md`](../CLAUDE.md) constraint 12).

This harness is tuned for sustained conjecture search and nothing else; what it is *not* for
is in [`../CLAUDE.md`](../CLAUDE.md) under **Scope**, and that list is worth reading before
bending the machinery to a job it was not built for.
