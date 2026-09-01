"""numerics — the numerical channel for this repository's research program.

Role (see ../../research/README.md): produce provenance-stamped diagnostic
artifacts that guide exploration. Numerics NEVER promote a statement to proved.

Soundness contract: artifacts label every comparison as exact, directional, or
calibration evidence, and their outcomes are deliberately not ledger statuses.
Sampled, MCMC, FEM, quadrature, finite-grid and floating-eigensolver values are
directional only; corroboration is never proof. An exact arithmetic witness or
analytic certificate emitted here is a candidate that still requires an
independently reviewed proof or refutation dossier before it has logical force
(CLAUDE.md constraint 2).
"""
from __future__ import annotations

from .comparison import (
    Comparison,
    calibration_ok,
    compare_directional,
    compare_exact,
    convergence_ok,
    matches,
)
from .contract import ARTIFACT_SCHEMA_VERSION, RunResult, TargetSpec

__all__ = [
    "ARTIFACT_SCHEMA_VERSION",
    "Comparison",
    "RunResult",
    "TargetSpec",
    "calibration_ok",
    "compare_directional",
    "compare_exact",
    "convergence_ok",
    "matches",
]
