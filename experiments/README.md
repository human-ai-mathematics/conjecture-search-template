# numerics — numerical research diagnostics

`numerics` runs numerical batteries for this repository's research program. Its output guides the
search; it never changes a ledger status or certifies a proof (`CLAUDE.md` constraint 2).

## Boundary

- Sampled, MCMC, FEM, quadrature, finite-grid and floating-eigensolver values are `directional`
  evidence. Closed-form or rationally certified values are `exact` evidence inside the artifact,
  and remain candidates until an independently reviewed dossier states them.
- Outcomes are neutral — `contradicts`/`consistent`/`inconclusive`, or `match`/`mismatch` for a
  calibration. They are not claim statuses.
- A finite battery can expose a bug or an obstruction. Passing it proves nothing universal.

The canonical instance registry is [`research/instances.md`](../research/instances.md). It is not
executable configuration: target modules own their effective battery and record it in each
artifact.

## Commands

Run from this directory so `uv` uses the tracked lock file:

```bash
uv run python -m numerics list                                  # targets and their profiles
uv run python -m numerics run example                           # -> research/runs/<ts>-example.jsonl
uv run python -m numerics run example --profile full --seed 20260901
uv run pytest                                                   # artifact contract + calibrations
```

A run target is mandatory — there is no silent default. `pytest` is the only check lane: it
exercises the artifact contract and re-runs every registered target against its closed-form
anchors, so a target whose calibration drifts fails the suite.

| target | role | profiles |
|---|---|---|
| `example` | worked example: the `prop:example` identity, in all three record shapes | `standard`, `full` |

`numerics list` is the executable source of truth. Delete `example` once this repository has a
real target.

## Artifact contract

Each run creates a new JSONL file under `research/runs/` unless `--out` is given; existing files
are never overwritten. Line 1 is the `_provenance` header (schema version, target, profile,
stochasticity, exact configuration, commit, interpreter and library versions), then the
target-owned records, then one `run-summary`. Inputs never share a mapping with derived results.
Historical artifacts are append-only and are not migrated when
`numerics.contract.ARTIFACT_SCHEMA_VERSION` changes.

A record is one of two things, and the runner rejects anything in between:

- an **observation** — `kind`, `instance`, `claim`, `evidence`, `outcome`, and a `detail`
  mapping the target owns;
- **auxiliary data** the target chose to keep — a `kind` and whatever else, carrying none of
  `claim`, `evidence`, `outcome`.

Those four fields are the whole contract, and they are deliberately genre-free. Everything that
depends on what is being computed — a bound and a value, a search domain and a witness, a range
verified, a certificate — lives in `detail`.

| `evidence` | admissible `outcome` |
|---|---|
| `exact` | `contradicts`, `consistent`, `inconclusive` |
| `directional` | `contradicts`, `consistent`, `inconclusive` |
| `calibration` | `match`, `mismatch` |

`contradicts` is the outcome that counts against the claim; with `evidence: exact` it is the one
worth escalating to a refutation dossier, and it is still only a candidate until that dossier is
independently reviewed. `consistent` says the computation failed to contradict the claim over
what it actually covered — never that the claim holds.

## Layout

```text
numerics/
  contract.py   Observation, RunResult, TargetSpec, the vocabularies, and the record helpers
  artifact.py   repo paths, provenance stamp, exclusive JSONL writer, run dispatch
  __main__.py   the CLI
  targets/      stable public registry + example.py
tests/          artifact contract and per-target calibration checks
```

`artifact.py` stamps the versions in `STAMPED_PACKAGES` — extend it when the harness takes a new
numerical dependency — and finds the repository root by looking for a directory holding both
`research/` and `modules/`, so those two names are structural.

## Writing a target

A target module exposes exactly one function, `run_records(seed: int, **cfg) -> RunResult`.
Register it in `numerics/targets/__init__.py` with a `TargetSpec`: a stable id, a one-line
summary, whether it is stochastic, and its named profiles. Record at least one `matches(...)`
calibration against a closed form — that is what the suite checks the target by.

Four constructors build an observation. Three are conveniences for common shapes; the fourth is
the contract itself, and a genre the others do not fit uses it rather than being bent into them.

| constructor | shape | typical genre |
|---|---|---|
| `compare(instance, claim, *, bound, value, evidence)` | computed value against a proposed bound | inequalities, spectral gaps |
| `matches(instance, claim, *, value, exact)` | one value against a closed form | any calibration |
| `searched(instance, claim, *, domain, witness=None)` | a finite search; `witness` is what was found | counterexample hunts, verified-up-to-$N$ sweeps, SAT/Gröbner witnesses |
| `observe(instance, claim, *, evidence, outcome, **detail)` | anything else; `detail` is yours | everything the three above distort |

```python
observe("K_7", "every 2-colouring contains a monochromatic triangle",
        evidence="exact", outcome="consistent",
        colourings=2**21, certificate="exhaustive")
```

The target id is a **stable public name**: artifacts keep the id they were written with and the
archive is append-only, so renaming a target breaks the trail from a checkpoint back to its
evidence. `python3 scripts/check.py --plane numerics` validates that trail's near end: every
artifact still parses and still carries its provenance header.

Before writing a target, fix the discriminating threshold: what value would count against the
candidate, and what value is merely consistent with it. A diagnostic with no refuting outcome is
not worth running. Mathematical conclusions and run interpretation belong in a dated
checkpoint under `research/explorations/`, not in this guide.
