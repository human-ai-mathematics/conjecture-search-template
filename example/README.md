# example/ — the worked example

One complete search, from a precise conjecture through routes and checkpoints to a
certified refutation and a ledger status — with one instance of every artifact genre this
harness validates, arranged exactly as a real repository arranges them.

It is a **fixture, not history**: nothing here records a search anyone ran, so `CLAUDE.md`
constraint 6 does not apply to it and you may edit or delete any of it freely.

Copy from it. Do not build on it.

**The mathematics is deliberately trivial.** The target is an inequality with a uniform
constant that a two-entry vector destroys, and the one proved lemma is the variance
identity. That is on purpose: every line of attention this fixture asks for should go to
the *shape* — which file says what, what a promotion costs, why a witness is not yet a
refutation — and none of it to the content. A real program has this shape and hard
content.

For the unfilled scaffolds to copy, see [`../templates/`](../templates/README.md). The
division is sharp: `templates/` is what a thing looks like empty, `example/` is what it
looks like finished.

```bash
python3 scripts/check.py --root example      # kept green by scripts/check.sh
```

## What is in it

| genre | file |
|---|---|
| manuscript module | [`modules/00-overview.tex`](modules/00-overview.tex) |
| claim graph | [`research/program/ledger.yaml`](research/program/ledger.yaml) |
| problem brief | [`research/program/brief.md`](research/program/brief.md) |
| search portfolio | [`research/program/portfolio.yaml`](research/program/portfolio.yaml) |
| proof dossier | [`solutions/prop-example.tex`](solutions/prop-example.tex) |
| refutation dossier | [`solutions/prop-example-refuter.tex`](solutions/prop-example-refuter.tex) |
| proof reviews | [`research/reviews/`](research/reviews/) |
| checkpoints | [`research/explorations/`](research/explorations/) |
| run artifact | [`research/runs/`](research/runs/) |

`python3 scripts/check.py ready --root example` **passes**: this is an instantiated
repository, and reading it is meant to answer "what does a finished one look like?"

## The search it records, in order

The target is `conj:example`: for all real $a_1,\dots,a_n$ with $n \ge 2$,
$\sum_i (a_i - \bar a)^2 \ge \tfrac12 \sum_i a_i^2$. It is false.

| # | what | where |
|---|---|---|
| 1 | the target is stated and gets a node | `modules/00-overview.tex`, `ledger.yaml` |
| 2 | the brief fixes the exact negation and what would finish it | [`research/program/brief.md`](research/program/brief.md) |
| 3 | the portfolio seeds one family and three routes | [`research/program/portfolio.yaml`](research/program/portfolio.yaml) |
| 4 | a numerical run is spent; it does **not** test the target, and two candidates come out | [`…/2026-09-02-example-exploration.md`](research/explorations/2026-09-02-example-exploration.md) |
| 5 | the roundoff route stops on the analytic estimate it needs | [`…/2026-09-03-example-roundoff.md`](research/explorations/2026-09-03-example-roundoff.md) |
| 6 | a second route is recognized as a duplicate of the first | [`…/2026-09-03-example-dedup.md`](research/explorations/2026-09-03-example-dedup.md) |
| 7 | the witness candidate is promoted to a node; routes and family close | [`…/2026-09-03-example-refuter.md`](research/explorations/2026-09-03-example-refuter.md) |
| 8 | the refuter gets an ordinary dossier and an independent review | `solutions/`, `research/reviews/` |
| 9 | only now does the target become `refuted`, via `refuted_by` | `ledger.yaml` |

Steps 4 and 8 are the two the harness exists to keep apart. A run found nothing and
certified nothing (`CLAUDE.md` constraint 2); a status moved only after a dossier was
independently reviewed (constraints 9 and 10).

`conj:weighted-example` is left `open` and `cand:example-identity-stability` is left live, on
purpose: a repository does not empty out when its conjecture falls.

## Three things it does differently, and why

- **It has no `.claude/`.** The roles lane skips a tree with no `.claude/agents/`, which is
  what keeps this fixture cheap. Adding one without a matching `.codex/` would turn it red.
- **It must stay a top-level sibling** of `research/` and `modules/`. Nested inside either,
  its ledger would trip the one-ledger rule and its checkpoints and run artifact would be
  swept into the live repository state.
- **Its `.tex` files name `../../main.tex`** as the `subfiles` master, not the `../main.tex`
  that [`../templates/solution.tex`](../templates/solution.tex) teaches, because they sit one
  level deeper. Use `../main.tex` in a real repository.

`experiments/numerics/targets/example.py` deliberately stayed at the repository root: it is
reference code the numerics test suite exercises, not a research record. Running
`numerics run example` therefore writes into the root `research/runs/`, not into this tree's.
