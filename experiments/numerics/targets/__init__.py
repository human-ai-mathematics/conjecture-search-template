"""Public target registry, keyed by stable CLI target id.

Each implementation module exposes one function::

    run_records(seed: int, **cfg) -> RunResult

Historical artifacts under research/runs/ keep the id they were written with, so renaming a
target is a breaking change to the archive. Add a target by writing its module and registering
it here; ``python -m numerics list`` is the executable source of truth.

``example`` is the template's worked target. Delete it once this repository has a real one.
"""
from __future__ import annotations

from ..contract import TargetSpec
from . import example

REGISTRY = {
    "example": TargetSpec(
        "example", example,
        "worked example target: the prop:example identity, in all three record shapes", True,
        {"standard": {"n": 2_000}, "full": {"n": 50_000, "grid": 3}},
    ),
}
