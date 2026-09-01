"""Public target registry, keyed by stable CLI target id.

Each implementation module exposes:
  run_records(seed, **cfg) -> RunResult
  selftest(rng)            -> list[(name: str, ok: bool)]

A target id is a stable public name: historical artifacts under research/runs/
keep the id they were written with, so renaming one is a breaking change to the
archive. Add a target by writing its module and registering it here.

``example`` is the template's worked target. Delete it once this repository has
a real one; ``python -m numerics list`` is the executable source of truth.
"""
from __future__ import annotations

from ..contract import TargetSpec
from . import example

REGISTRY = {
    "example": TargetSpec(
        "example", example, "worked example target: seeded mean estimate", True,
        {
            "standard": {"n": 2_000},
            "full": {"n": 50_000},
        },
    ),
}
