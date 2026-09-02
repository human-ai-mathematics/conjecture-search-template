# Ledger schema

This is the field contract for [`ledger.yaml`](ledger.yaml).
[`../../scripts/check_ledger.py`](../../scripts/check_ledger.py) is the executable validator;
[`../../CLAUDE.md`](../../CLAUDE.md) owns contribution policy.

## Document

```yaml
meta:
  program: <program-id>
  scope: <optional mathematical scope>
  route_policy:                 # optional
    allowed: [route-a, shared]
nodes:
  - ...
```

The repository has exactly one ledger. If `route_policy` exists, every node has one `route` from
its closed vocabulary. A route is coordination ownership, not mathematical exclusivity: a node
may support several routes through ordinary graph relations.

## Required node fields

| field | values / meaning |
|---|---|
| `id` | Stable id, normally the LaTeX label. |
| `kind` | `theorem`, `proposition`, `lemma`, `corollary`, `conjecture`, `assumption`, `question`, `definition`, `obstruction`, or `example`. |
| `status` | `open`, `proved`, `refuted`, or `defined`. `defined` is valid exactly for definitions. |
| `provenance` | `internal` or `literature`. This is independent of logical status. |
| `file` | Existing manuscript file containing the effective label. |
| `statement` | Concise statement agreeing with that anchor. |

Optional `label` overrides `id` as the manuscript anchor.

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
| `refuted_by` | Proved refuters of a refuted node; each must also occur in `depends_on`. |

This distinction prevents a standard category error. A theorem of the form $A\Rightarrow B$ can
be proved while $A$ remains open: store $A$ in `assumes`, $B$ in `implies`, and keep the theorem
`proved`. `check_ledger.py status` reports such a result as applicability-blocked.

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

`artifact` is a standalone `.tex` dossier under `solutions/` whose header names the node.
`mode: agent` requires a passing proof review by a distinct agent. `mode: human` requires
`accepted_by`. `mode: lean` is reserved for later integration and currently only checks for an
adjacent `.lean` file; it is not a present project priority.

A dossier may be modular: it may cite already certified `depends_on` nodes rather than duplicate
their proofs. Multiple records allow genuinely alternative proofs to coexist.

## Boundary

The ledger contains current mathematical state, not attempt history, numerical output, or loose
roadmap links. Put those in `research/explorations/`, `research/runs/`, and program briefs.
Numerical evidence never changes a status. Candidate statements stay in exploration front matter
until they are precise, stable, and worth tracking as manuscript/ledger nodes.

The checker establishes structural consistency only. Independent review establishes agreement of
the manuscript, ledger, dossier, quantifiers, and mathematics.

## Verify

```bash
python3 scripts/check_ledger.py
python3 scripts/check_ledger.py status
python3 scripts/check_ledger.py node q:example
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
```
