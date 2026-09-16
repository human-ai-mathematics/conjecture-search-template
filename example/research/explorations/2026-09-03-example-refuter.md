---
type: exploration
date: "2026-09-03T11:40:00Z"
approach: ap:example-finite-battery
outcome: proposed
nodes:
  - conj:example
  - prop:example-refuter
promotes:
  - candidate: cand:example-constant-witness
    node: prop:example-refuter
---

Worked example of the record that ends a search: it promotes a candidate, closes a route
and a family, and hands the orchestrator the ledger delta that moves a status. It is a
fixture in `example/`, not history.

Two envelope details worth copying. It carries a UTC timestamp rather than a plain date:
nothing here needs one — the record it depends on is dated the day before — but it is the
form to use when two records written on the same day have to be ordered, because a filename
is not a clock ([`research/explorations/README.md`](../../../research/explorations/README.md)). Its `approach:` identifies the route whose
result produced the promoted witness; other route changes have their own checkpoints.

## What was tried

Turning `cand:example-constant-witness` into a refutation. The witness had been sitting in
[`2026-09-02-example-exploration.md`](2026-09-02-example-exploration.md) since the previous
day, doing nothing: a candidate carries no status, so `conj:example` was still `open` with
a known counterexample written down two files away. That gap is the thing this record
closes, and it closes it through the ordinary channel rather than around it.

## How

The five steps `solutions/README.md` lays out for a refutation, in order:

1. **The witness is a candidate.** Already done, and it stops there — a witness is not a
   refutation.
2. **The statement it establishes becomes a node.** `prop:example-refuter`, with its own
   manuscript statement at `:label: prop:example-refuter` in
   [`../../modules/00-overview.md`](../../modules/00-overview.md). Note the shape: the
   node asserts that the specific vector $(1,1)$ has centred sum of squares $0$ and half
   sum of squares $1$ — an ordinary provable claim — and only then concludes that
   `conj:example` is false.
3. **It gets an ordinary dossier.** `solutions/prop-example-refuter.md`. Nothing about it
   is special: it is the same file genre a proof of anything else would use.
4. **That dossier is independently certified.** `mode: agent`, with the persisted report
   [`../reviews/2026-09-03-prop-example-refuter-proof-review.md`](../reviews/2026-09-03-prop-example-refuter-proof-review.md)
   naming an author and a distinct reviewer.
5. **Only then does the target move.** `conj:example` becomes `status: refuted` and names
   `prop:example-refuter` in `refuted_by` — and **not** in `depends_on`, which records
   facts a proof used, and a refuted statement has no proof.

Promotion itself is one act, not a node addition with paperwork to follow: the manuscript
`:label:`, the ledger node, the `promotes:` entry above — which is what ends the candidate —
and every portfolio blocker repointed. `python3 scripts/check.py candidates` shows
`cand:example-constant-witness` as promoted rather than live, and
`cand:example-identity-stability` as the one still open.

## What this costs the search

Two route changes, proposed here and applied by the `synthesizer`:

- `ap:example-finite-battery` is **completed**. It established that the available run was
  only an identity check and, by inspecting its domain, produced the witness candidate.
  "Completed" says its route objective is finished and nothing more; the target's status is
  a separate fact recorded in a separate file.
- `ap:example-roundoff-bound` is **blocked** on `cand:example-identity-stability`, which
  nobody has proved. It reopens if that candidate is proved or if any explicit floating-point
  error bound turns up. The blocker is named by its id and its statement is not copied here
  (`CLAUDE.md` constraint 11).

And one family change: `fam:example-numerical` is **saturated**, with the reopening
condition recorded in [`../program/portfolio.yaml`](../program/portfolio.yaml). Saturation
is a judgment and it costs this checkpoint plus that condition — it is never inferred from
how many attempts ran or how long they took.

## What is left

`conj:weighted-example` is untouched and still `open`: it states that the identity survives
weighting, which no route here attacked. `cand:example-identity-stability` is still live. Neither is a
loose end in the target's search — the target is settled — and both are why a repository
does not empty out when a conjecture falls.
