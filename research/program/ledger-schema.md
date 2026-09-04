# Ledger schema

This is the field contract for [`ledger.yaml`](ledger.yaml).
[`../../scripts/check.py`](../../scripts/check.py) is the executable validator (lane
`core` here, lane `proofs` for the certification records below);
[`../../CLAUDE.md`](../../CLAUDE.md) owns contribution policy.

## Document

```yaml
meta:
  program: <program-id>
  scope: <optional mathematical scope>
nodes:
  - ...
```

The repository has exactly one ledger (`CLAUDE.md` constraint 1), and `meta` carries nothing but
the program's identity and scope. Which agent or route owns a node is coordination state and
lives in `portfolio.yaml` (gated; see [`portfolio-schema.md`](portfolio-schema.md)).

## Required node fields

| field | values / meaning |
|---|---|
| `id` | Stable id. It **is** the manuscript anchor: `\label{<id>}` in `modules/`. |
| `kind` | `theorem`, `proposition`, `lemma`, `corollary`, `conjecture`, `assumption`, `question`, `definition`, `obstruction`, or `example`. |
| `status` | `open`, `proved`, `refuted`, or `defined`. `defined` is valid exactly for definitions. |
| `provenance` | `internal` or `literature`. This is independent of logical status. |
| `file` | The file under `modules/` holding that `\label`. |
| `summary` | One line glossing the statement, for the derived views. **Not canonical.** |

### The anchor invariant

> Every claim-bearing theorem-environment label in `modules/` corresponds to exactly one
> ledger node, whose `kind` is that environment. Structural labels do not.

Concretely, and all of it checked:

- `\label{<id>}` appears in `modules/`, inside a claim environment whose name equals the
  node's `kind`. The ten claim environments are the ten `kind` values, declared in
  `preamble.tex`; `remark` is deliberately not among them, which is why an obstruction has
  an `obstruction` environment rather than borrowing one.
- A `\label` on a `\section`, an equation, or a `remark` is structural: it needs no node,
  and a node may not claim it.
- A claim-environment label with no node is an error. So is the same label twice anywhere
  under `modules/`.
- `file` is confined to `modules/` and must be the file that actually holds the label.
- There is no `label:` override. It made "the id is the anchor" untrue and had no second
  reader; it is rejected by name.

### `summary` is a gloss, not a home

The statement lives in `modules/` and nowhere else (`CLAUDE.md` constraint 7). `summary`
exists so `check.py status` and `check.py node` are readable without opening LaTeX, and the
`reviewer`'s `sync` lens treats any disagreement as a defect in the summary. The field was
called `statement`, which invited exactly the drift it was supposed to survive; that name is
now rejected.

Note the deliberate asymmetry with a **candidate**, whose `statement:` in checkpoint front
matter *is* canonical — nothing else holds that text, which is the whole reason a candidate
is allowed to carry one.

Literature nodes also require `import_class: published | preprint-reviewed |
preprint-unreviewed` and non-empty `references` containing BibTeX keys. An unreviewed preprint is
`open`, not `proved`, until its proof receives review.

## Relations

All relation fields are YAML lists of same-ledger node ids.

| field | meaning |
|---|---|
| `depends_on` | Claims actually used in the proof. This is the acyclic proof DAG. A proved node cannot inherit an open or refuted dependency. |
| `assumes` | Antecedents of an implication. They affect applicability, not whether the implication itself was proved. |
| `implies` | Conclusions advertised by a proved implication. |
| `refines` | Statements made more precise or stronger by this node. |
| `bounded_by` | Proved obstruction nodes: hard mathematical fences. |
| `heuristic_barriers` | Open obstruction nodes: advisory method barriers only. |
| `refuted_by` | Proved refuters of a refuted node. Not a proof dependency: see below. |

This distinction prevents a standard category error. A theorem of the form $A\Rightarrow B$ can
be proved while $A$ remains open: store $A$ in `assumes`, $B$ in `implies`, and keep the theorem
`proved`. `check.py status` reports such a result as applicability-blocked.

A refuted node names its refuters in `refuted_by` and stops there. It does **not** repeat them
in `depends_on`: that field is the graph of facts a proof used, and a refuted statement has no
proof. Each refuter must itself be `proved`, which is the whole of the provenance
(`CLAUDE.md` constraint 10). The refuter is an ordinary node with an ordinary dossier — the
worked instance is `example/solutions/prop-example-refuter.tex`.

## Proof records

An internally proved node requires one or more independently certified proofs:

```yaml
proofs:
  - artifact: solutions/thm-example.tex
    mode: agent
    review: research/reviews/2026-09-02-example-proof-review.md
  - artifact: solutions/thm-example-second-proof.tex
    mode: human
    accepted_by: <human identity>
```

`artifact` is a standalone `.tex` dossier under `solutions/`. Its header is parsed, not
searched, and exactly one field is checked: `ledger-node` must name this node. Certification
lives here and only here — `checked_by` in a dossier header is rejected by name. `mode: agent`
requires a passing proof review by a distinct agent; `mode: human` requires `accepted_by`.

There are exactly two modes. A future machine-checked mode belongs here only once the checker
actually invokes its kernel with pinned tooling.

A dossier may be modular: it may cite already certified `depends_on` nodes rather than duplicate
their proofs. Multiple records allow genuinely alternative proofs to coexist.

## Boundary

The ledger contains current mathematical state, not attempt history, numerical output, search
activity, or loose roadmap links. Put those in `research/explorations/`, `research/runs/`,
`research/program/portfolio.yaml`, and `research/program/brief.md`. Numerical evidence never
changes a status. Candidate statements stay in checkpoint front matter until they are precise,
stable, and worth tracking as manuscript/ledger nodes.

An approach family, a route state, a blocker, and a saturation judgment are search state, not
claims: they belong in the portfolio and are not ledger fields (`CLAUDE.md` constraint 11).

The checker establishes structural consistency only. Independent review establishes agreement of
the manuscript, ledger, dossier, quantifiers, and mathematics.

## Verify

```bash
python3 scripts/check.py --lane core
python3 scripts/check.py status
python3 scripts/check.py node <id>
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
```
