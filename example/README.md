# example/ — the worked example

One complete search, from a precise conjecture through routes and checkpoints to a certified
refutation, with one instance of every file genre the harness validates. It is a **fixture,
not history**: its records are not append-only, so edit or delete it freely. `templates/`
is what each file looks like empty; this is what it looks like finished.

```bash
uv run scripts/check.py --root example      # kept green by scripts/check.sh
```

The mathematics is deliberately trivial. The target `conj:example` — for all real
$a_1,\dots,a_n$ with $n \ge 2$, $\sum_i (a_i - \bar a)^2 \ge \tfrac12 \sum_i a_i^2$ — is false,
refuted by $a = (1,1)$. In order:

1. the target is stated in [`modules/00-overview.md`](modules/00-overview.md) and gets a node
   in [`research/program/ledger.yaml`](research/program/ledger.yaml);
2. the [brief](research/program/brief.md) fixes the exact negation and what would finish it,
   and reads the proved fence `prop:upper-constant` to say where the target is weakest;
3. the [portfolio](research/program/portfolio.yaml) lists two routes;
4. a numerical run tests nothing about the target and yields candidates
   ([`research/explorations/`](research/explorations/), [`research/runs/`](research/runs/));
5. the witness candidate is promoted to the refuter node `prop:example-refuter`;
6. the refuter gets an ordinary dossier ([`solutions/`](solutions/)) and an independent
   review ([`research/reviews/`](research/reviews/));
7. only then does the target become `refuted`, through `refuted_by`.

It is its own MyST project ([`myst.yml`](myst.yml)) and must stay a top-level sibling of
`research/` and `modules/`, or its ledger would count as a second one.
