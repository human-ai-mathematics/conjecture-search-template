# numerics — numerical research diagnostics

`numerics` runs calibrated numerical batteries for this repository's research program. Its output
guides exploration; it never changes a ledger status or certifies a proof.

## Boundary

- Sampled, MCMC, FEM, quadrature, finite-grid, and floating-eigensolver values are `directional`
  evidence.
- Closed-form or rationally certified comparisons are `exact` evidence inside the artifact, but
  still require an independently reviewed proof or refutation dossier before they have logical
  force.
- Comparison outcomes are neutral: `match`/`mismatch` for calibration and
  `exceeds`/`within`/`unavailable` otherwise. They are not claim statuses.
- A finite battery can expose a bug or an obstruction. Passing it proves nothing universal.

The canonical, human-reviewed instance registry is
[`research/knowledge/instances.md`](../research/knowledge/instances.md). It is not executable
configuration; target modules own their effective battery and record it in each artifact.

## Commands

Run from this directory so `uv` uses the tracked lock file:

```bash
uv run python -m numerics list
uv run python -m numerics check
uv run python -m numerics check example
uv run python -m numerics run example
uv run python -m numerics run example --profile full --seed 20260901
uv run pytest -m "not slow"
uv run pytest
```

A run target is mandatory — there is no silent default.

`check` is the fast installed-package smoke lane. Pytest without the `slow` marker is the normal
development lane. Full pytest includes any expensive Monte Carlo regression.

## Targets and profiles

| target | role | profiles |
|---|---|---|
| `example` | worked example: seeded mean estimate against an exact anchor | `standard`, `full` |

Use `numerics list` as the executable source of truth. Delete `example` once this repository has a
real target.

A target id is a **stable public name**: artifacts under `research/runs/` record the id they were
written with, and the archive is append-only, so renaming a target breaks the trail back from an
exploration to its evidence. Choose the name once.

## Artifact contract

Every run creates a new JSONL file under `research/runs/` unless `--out` is supplied. Existing
files are never overwritten. The lines are:

1. `_provenance`: artifact schema version, target, profile, stochasticity, exact run
   configuration, commit, and interpreter/library environment;
2. target-owned records, each with a string `kind`;
3. one `run-summary` record containing derived run-level outputs.

Inputs never share a mapping with derived results. The current envelope version is
`numerics.contract.ARTIFACT_SCHEMA_VERSION`. Historical artifacts are append-only and are not
migrated when the schema changes.

## Package layout

```text
numerics/
  contract.py       TargetSpec, RunResult, artifact schema version
  provenance.py     repository paths, environment stamp, exclusive JSONL writer
  run.py            profile resolution and artifact dispatch
  selftest.py       per-target calibration checks with independent seeded streams
  comparison.py     evidence classes and neutral comparison outcomes
  targets/          stable public registry
    example.py      the worked example target
tests/              fast deterministic/oracle tests plus explicitly marked slow MC regressions
```

`provenance.py` stamps the versions listed in its `STAMPED_PACKAGES`; extend that tuple when the
harness takes a new numerical dependency. It locates the repository root by looking for a
directory holding both `research/` and `modules/`, so those two names are structural.

## Writing a target

A target module exposes exactly two functions:

```python
def run_records(seed: int, **cfg) -> RunResult: ...
def selftest(rng: np.random.Generator) -> list[tuple[str, bool]]: ...
```

Register it in `numerics/targets/__init__.py` with a `TargetSpec`: a stable id, a one-line
summary, whether it is stochastic, and its named profiles. Before writing one, fix the
discriminating threshold: what value would count against the candidate, and what value is merely
consistent with it. A diagnostic with no refuting outcome is not worth running.

Target-specific mathematical conclusions, limitations, and historical run interpretation belong in
`research/explorations/`, `research/knowledge/`, and the program documents — not in this guide.
