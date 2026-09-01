"""Calibration and regression self-tests for every registered target.

``python -m numerics check`` exits zero iff all checks pass.  Passing verifies the
implementation against its closed-form anchors; it is not proof of a mathematical
claim or certification of a sampled diagnostic.
"""
from __future__ import annotations

import sys

import numpy as np

from .targets import REGISTRY


def selftest(verbose: bool = True, target: str | None = None, seed: int = 7) -> int:
    """Run fast target-owned checks with an independent RNG stream per target."""
    if target is not None and target not in REGISTRY:
        raise ValueError(f"unknown target '{target}'; have {sorted(REGISTRY)}")
    fails: list[str] = []
    selected = [(target, REGISTRY[target])] if target else list(REGISTRY.items())
    streams = np.random.SeedSequence(seed).spawn(len(selected))
    for (name, spec), stream in zip(selected, streams):
        mod = spec.module
        if not hasattr(mod, "selftest"):
            continue
        rng = np.random.default_rng(stream)
        if verbose:
            print(f"[{name}]")
        for label, ok in mod.selftest(rng):
            if verbose:
                print(f"  [{'ok' if ok else 'FAIL'}] {label}")
            if not ok:
                fails.append(label)
    if verbose:
        print(f"\n{'PASS' if not fails else 'FAIL'} — {len(fails)} failure(s)"
              + ("" if not fails else ":\n  - " + "\n  - ".join(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(selftest())
