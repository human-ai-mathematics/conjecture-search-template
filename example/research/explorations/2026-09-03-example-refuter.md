---
closes:
  - cand:example-constant-witness
---

Worked example of the record that ends a search: it promotes a candidate, closes the
routes, and hands the orchestrator the ledger delta that moves a status. It is a fixture in
`example/`, not history.

## Question examined

Does `cand:example-constant-witness` refute `conj:example` through the ordinary channel? The witness had been sitting in
[`2026-09-02-example-exploration.md`](2026-09-02-example-exploration.md) since the previous
day, doing nothing: a candidate carries no status, so `conj:example` was still `open` with
a known counterexample written down two files away.

## What we learned

Yes, and the witness is now certified. How the refutation went (*Refutation* in
`SPECIFICATION.md`):

1. **The witness was a candidate.** A witness is not a refutation.
2. **The statement it establishes becomes a node.** `prop:example-refuter`, with its own
   manuscript statement at `:label: prop:example-refuter` in
   [`../../modules/02-refutation.md`](../../modules/02-refutation.md). The node asserts that
   the specific vector $(1,1)$ has centred sum of squares $0$ and half sum of squares $1$ —
   an ordinary provable claim — and only then concludes that `conj:example` is false.
3. **It gets an ordinary dossier.** `solutions/prop-example-refuter.md`.
4. **That dossier is independently certified** by the persisted report
   [`../reviews/2026-09-03-prop-example-refuter-proof-review.md`](../reviews/2026-09-03-prop-example-refuter-proof-review.md)
   naming an author and a distinct reviewer.
5. **Only then does the target move.** `conj:example` becomes `status: refuted` and names
   `prop:example-refuter` in `refuted_by` — and **not** in `depends_on`, which records
   facts a proof used, and a refuted statement has no proof.

The candidate became the node `prop:example-refuter`, so this record `closes:` it: the
statement now has exactly one home, the manuscript. `cand:example-identity-stability` is
still live.

## What resists

Nothing on the target. Off it, the orchestrator's decision on the routes:

- `ap:example-finite-battery` is **closed**. It established that the available run was
  only an identity check and, by inspecting its domain, produced the witness candidate.
- `ap:example-roundoff-bound` is **blocked** on `cand:example-identity-stability`, which
  nobody has proved. It reopens if that candidate is proved or if any explicit
  floating-point error bound turns up. The blocker is named by its id and its statement is
  not copied.

## Proposed next step

None for the target, which is settled.

`conj:weighted-example` is untouched and still `open`: no route here attacked it. Neither
it nor `cand:example-identity-stability` is a loose end in the target's search — the
target is settled — and both are why a repository does not empty out when a conjecture
falls.
