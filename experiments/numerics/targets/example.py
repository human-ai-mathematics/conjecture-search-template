"""Worked example target: the smallest thing that exercises the whole contract.

It probes the seed ledger's `prop:example` — the identity
$\\sum_i (a_i-\\bar a)^2 = \\sum_i a_i^2 - n\\bar a^2$ — in three different shapes, so the
template ships one instance of each supplied helper rather than a schema to interpret:

* `matches`   — a calibration of one side against the closed form of the other;
* `searched`  — an exhaustive check over a finite integer family, which is `consistent` over
  that family and, by `conj:finite-battery`, establishes nothing about the family it did not cover;
* `compare`   — a computed value against a proposed bound, the inequality shape.

None of them certifies anything. Copy this file's shape for a real diagnostic; delete it once
one exists.
"""
from __future__ import annotations

import itertools

import numpy as np

from ..contract import RunResult, compare, matches, searched


CLAIM = "sum_i (a_i - abar)^2 == sum_i a_i^2 - n abar^2"


def _identity_sides(vector: np.ndarray) -> tuple[float, float]:
    """The two sides of prop:example, computed independently of each other."""
    mean = vector.mean()
    return float(((vector - mean) ** 2).sum()), float((vector**2).sum() - vector.size * mean**2)


def _exhaustive_witness(grid: int, width: int) -> list[int] | None:
    """Search every integer vector in [-grid, grid]^width for a failure of the identity."""
    for entries in itertools.product(range(-grid, grid + 1), repeat=width):
        left, right = _identity_sides(np.array(entries, dtype=float))
        if abs(left - right) > 1e-9 * max(1.0, abs(right)):
            return list(entries)
    return None


def run_records(seed: int, *, n: int = 2_000, grid: int = 2, width: int = 4) -> RunResult:
    """Sample once, search once, and record one observation of each supplied shape."""
    rng = np.random.default_rng(seed)
    sample = rng.standard_normal(n)
    mean = float(sample.mean())
    left, right = _identity_sides(sample)
    witness = _exhaustive_witness(grid, width)
    domain = f"all integer vectors in [-{grid},{grid}]^{width} ({(2 * grid + 1) ** width} of them)"
    # Fixed BEFORE the run: the value that would count against the target.
    threshold = 4.0 / np.sqrt(n)

    # Every record carries a string `kind` naming what it is to a reader, plus the claim,
    # evidence class and outcome the contract checks; the runner rejects a half-labelled
    # record, so a reader of the artifact never has to guess.
    records = [
        matches("standard-normal-sample", CLAIM, value=left, exact=right, rel_tol=1e-9,
                note="the two sides computed independently; any residual is roundoff").record(
                    "calibration"),
        searched("small-integer-vectors", CLAIM, domain=domain, witness=witness,
                 evidence="exact",
                 note="exhaustive over the stated domain only (conj:finite-battery)").record("search"),
        compare("standard-normal-sample", "|sample mean| <= 4 / sqrt(n)",
                bound=threshold, value=abs(mean), evidence="directional",
                note="directional: one finite sample says nothing universal").record(
                    "diagnostic"),
    ]
    return RunResult(
        records=records,
        config={"n": int(n), "grid": int(grid), "width": int(width),
                "threshold": float(threshold)},
        summary={"mean": mean, "identity_residual": left - right, "searched": domain,
                 "witness_found": witness is not None},
    )
