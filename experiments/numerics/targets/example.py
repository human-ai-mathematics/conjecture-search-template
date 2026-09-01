"""Worked example target: the smallest thing that exercises the whole contract.

It draws a standard normal sample, calibrates the sample variance against its
exact value 1, and records the sample mean as a directional diagnostic. Neither
record certifies anything: the calibration says the harness and its seeding work,
and the diagnostic is one finite sample. Copy this file's shape -- ``run_records``
plus ``selftest`` -- for a real diagnostic; delete it once one exists.
"""
from __future__ import annotations

import numpy as np

from ..comparison import calibration_ok, compare_directional, matches
from ..contract import RunResult


def run_records(seed: int, *, n: int = 2_000) -> RunResult:
    """Sample once, then record one calibration and one directional comparison."""
    rng = np.random.default_rng(seed)
    sample = rng.standard_normal(n)
    mean = float(sample.mean())
    variance = float(sample.var(ddof=1))
    # Fixed BEFORE the run: the value that would count against the target.
    threshold = 4.0 / np.sqrt(n)

    # Every record carries a string ``kind`` naming what it is; the runner rejects
    # an untyped record, so a reader of the artifact never has to guess.
    records = [
        {"kind": "calibration",
         **matches("standard-normal", "sample variance reproduces the exact variance 1",
                   variance, 1.0, rel_tol=0.10).dict()},
        {"kind": "diagnostic",
         **compare_directional(
             "|sample mean| <= 4 / sqrt(n)", "standard-normal", threshold, abs(mean),
             note="directional: one finite sample says nothing universal",
         ).dict()},
    ]
    return RunResult(
        records=records,
        config={"n": int(n), "threshold": float(threshold)},
        summary={
            "mean": mean,
            "variance": variance,
            "evidence": "directional",
        },
    )


def selftest(rng: np.random.Generator) -> list[tuple[str, bool]]:
    """Fast checks against closed-form anchors. Passing proves no mathematics."""
    n = 20_000
    sample = rng.standard_normal(n)
    return [
        ("sample variance is within 10% of the exact value 1",
         calibration_ok(float(sample.var(ddof=1)), 1.0, rel_tol=0.10)),
        ("sample mean is within 5/sqrt(n) of the exact value 0",
         abs(float(sample.mean())) <= 5.0 / np.sqrt(n)),
    ]
