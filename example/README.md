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

1. the target is stated in [`modules/02-refutation.md`](modules/02-refutation.md) and gets a node
   in [`research/program/ledger.yaml`](research/program/ledger.yaml);
2. the [brief](research/program/brief.md) fixes the exact negation and what would finish it,
   and reads the proved fence `prop:upper-constant` to say where the target is weakest;
3. the [portfolio](research/program/portfolio.yaml) lists two routes;
4. a numerical run tests nothing about the target and yields candidates
   ([`research/explorations/`](research/explorations/), [`research/runs/`](research/runs/));
5. the witness candidate is promoted to the refuter node `prop:example-refuter`;
6. the refuter gets an ordinary dossier ([`solutions/`](solutions/)) and an independent
   review ([`research/reviews/`](research/reviews/));
7. only then does the target become `refuted`, through `refuted_by`;
8. the manuscript, [`modules/`](modules/), tells it all to a mathematician: the question,
   the three results with the idea of each proof, and one question left unsettled. That
   question is a classical identity, and says so up front: it shows the form, not a
   research question. Each
   statement shows its status, read from the ledger.

It is its own MyST project ([`myst.yml`](myst.yml)) and must stay a top-level sibling of
`research/` and `modules/`, or its ledger would count as a second one.


## Re-review scenarios

These scenarios illustrate the contract; they are not additional certifications of this
fixture and do not change its dossiers, statements or existing reports.

**A title correction.** Suppose only the title of `prop:example` changes. Its fingerprint
changes, so the current certification fails validation. A fresh reviewer compares the
current statement with a historical version verified against the previous passing report's
fingerprints. It checks that the new title is faithful and the body and proof are unchanged.
A short new report can retain the unaffected proof conclusions and record the current
fingerprints. This remains valid after a third or later harmless edit; a count does not
trigger a full review. If the baseline cannot be verified, a full review is required.

Illustrative Findings (placeholders must be filled from the actual comparison):

> Re-review of `<previous-report>`. Compared `<verified-revision>` with the current tree
> whose fingerprints are recorded above. Only the title of `prop:example` changed from
> `<old-title>` to `<new-title>`. The body, dependencies and dossier are unchanged. The
> new title expresses the same identity, so no proof step is affected; the earlier
> certification's proof conclusions are retained.

The report still includes Corrections and Exclusions. The title is not exempt from review;
its limited impact justifies the short examination.

**A shared definition changes.** Suppose several certified dossiers use one normalization.
Run `uv run scripts/check.py --root example --impact` to list affected certifications
by changed item (the unchanged fixture has none). One reviewer can compare the definition
once, then check its use in each dossier. If all
pass, one new report may cover them, with a conclusion for each and fingerprints produced
by `check.py --fingerprint <dossier-1> <dossier-2> ...`. Each relevant proof record points
to that report. If one dossier needs repair, put it in a separate `revise` report; the
`pass` report and its fingerprints cover only the passing dossiers and their required
statements. A structural change to an argument requires a full review of that argument.

**Prose after a status change.** A sentence saying "we prove" may introduce a certified
claim by link. If that claim is no longer established, the sentence must be revised too.
The `sync` lens reports this contradiction. Conversely, a ledger status of `open` does not
justify saying that the problem is open in the literature.
