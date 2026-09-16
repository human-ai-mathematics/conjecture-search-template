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
| `id` | Stable id. It **is** the manuscript anchor: `:label: <id>` in `modules/`. |
| `kind` | `theorem`, `proposition`, `lemma`, `corollary`, `conjecture`, `assumption`, `definition`, or `example`. Mathematical form only: an open question is a `conjecture` in the direction the search tries to establish, and an obstruction is whichever form it has, cited as a fence through `bounded_by` or `heuristic_barriers`. |
| `status` | `open`, `proved`, `refuted`, or `defined`. `defined` is valid exactly for definitions. |
| `provenance` | `internal` or `literature`. This is independent of logical status. |
| `file` | The `.md` file under `modules/` holding that label. |
| `summary` | One line glossing the statement, for the derived views. **Not canonical.** |

### The anchor invariant

> Every labelled claim directive in `modules/` corresponds to exactly one ledger node, whose
> `kind` is that directive. Structural labels do not.

`scripts/check.py` does not parse the manuscript; it builds it with MyST (`myst build
--site`) and reads the tree MyST produces, so a claim is exactly what MyST says it is.
Concretely, and all of it checked:

- The node's statement is a `prf:<kind>` directive in `modules/*.md` carrying `:label: <id>`,
  and `<kind>` equals the node's `kind`. The eight claim directives are the eight `kind`
  values, all native to MyST; `prf:remark` is deliberately not among them.

  ```markdown
  :::{prf:conjecture}
  :label: conj:main
  The precise quantified statement.
  :::
  ```

- A label on a heading (`(sec:x)=`), an equation, a figure, a table or a `prf:remark` is
  structural: it needs no node, and a node may not claim it. MyST gives each labelled object
  its own node, so an equation inside a theorem stays structural, and a `prf:proof` nested in
  a theorem carries no label of its own.
- A claim label with no node is an error. So is the same label twice anywhere in the MyST
  project, and so are two labels MyST turns into the same HTML anchor — the anchor of
  `conj:main` is `#conj-main`, so `a:b-c` and `a-b:c` collide.
- An unknown directive (`prf:question` is not one), an unresolved cross-reference, and any
  error MyST itself reports are errors too: each is a statement or a link that silently went
  missing.
- `file` is confined to `modules/` and must be the file that actually holds the label.
- There is no `label:` override. It made "the id is the anchor" untrue and had no second
  reader; it is rejected by name.

### `summary` is a gloss, not a home

The statement lives in `modules/` and nowhere else (`CLAUDE.md` constraint 7). `summary`
exists so `check.py status` and `check.py node` are readable without opening the manuscript, and the
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
| `bounded_by` | Proved nodes: hard mathematical fences. |
| `heuristic_barriers` | Open nodes: advisory method barriers only. |
| `refuted_by` | Proved refuters of a refuted node. Not a proof dependency: see below. |

This distinction prevents a standard category error. A theorem of the form $A\Rightarrow B$ can
be proved while $A$ remains open: store $A$ in `assumes`, $B$ in `implies`, and keep the theorem
`proved`. `check.py status` reports such a result as applicability-blocked.

A refuted node names its refuters in `refuted_by` and stops there. It does **not** repeat them
in `depends_on`: that field is the graph of facts a proof used, and a refuted statement has no
proof. Each refuter must itself be `proved`, which is the whole of the provenance
(`CLAUDE.md` constraint 10). The refuter is an ordinary node with an ordinary dossier — the
worked instance is `example/solutions/prop-example-refuter.md`.

## Proof records

An internally proved node requires one or more independently certified proofs:

```yaml
proofs:
  - artifact: solutions/thm-example.md
    mode: agent
    review: research/reviews/2026-09-02-example-proof-review.md
  - artifact: solutions/thm-example-second-proof.md
    mode: human
    accepted_by: <human identity>
```

`artifact` is a standalone MyST dossier under `solutions/`. Its header is its YAML front
matter, and exactly one field is checked: `ledger-node` must name this node. Certification
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
