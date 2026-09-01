"""Evidence-labelled comparisons and numerical gates.

The comparison outcome is deliberately not a ledger status. Exact analytic witnesses and
directional numerical estimates use the same neutral ``exceeds/within/unavailable`` vocabulary.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np


@dataclass
class Comparison:
    instance: str
    claim: str                # what upper bound was tested, e.g. "C_P <= bulk_bound"
    bound: float              # B
    value: float              # exact lower bound or explicitly directional estimate
    evidence: str             # "exact" | "directional" | "calibration"
    outcome: str              # "exceeds" | "within" | "unavailable" | "match" | "mismatch"
    tightness: float | None   # lower / B  (how close the LB is to the claim)
    note: str = ""

    def dict(self):
        return asdict(self)


def compare_exact(claim: str, instance: str, bound: float, lower: float,
                  rel_tol: float = 0.10, note: str = "") -> Comparison:
    """Compare a caller-supplied exact analytic lower bound with an upper proposal.

    This function does not certify ``lower``. Do not pass a raw Monte Carlo, MCMC,
    FEM, or grid estimate; use :func:`compare_directional` for those quantities.
    """
    if bound is None or not np.isfinite(bound):
        outcome = "unavailable"
        tight = None
    elif lower > bound * (1 + rel_tol):
        outcome = "exceeds"
        tight = float(lower / bound)
    else:
        outcome = "within"
        tight = float(lower / bound)
    return Comparison(instance, claim, float(bound) if bound is not None else float("nan"),
                      float(lower), "exact", outcome, tight, note)


def compare_directional(claim: str, instance: str, bound: float, estimate: float,
                        rel_tol: float = 0.10, note: str = "") -> Comparison:
    """Compare a numerical estimate with a proposal without issuing a claim status."""
    if bound is None or not np.isfinite(bound):
        outcome = "unavailable"
        tight = None
    elif estimate > bound * (1 + rel_tol):
        outcome = "exceeds"
        tight = float(estimate / bound)
    else:
        outcome = "within"
        tight = float(estimate / bound)
    return Comparison(instance, claim, float(bound) if bound is not None else float("nan"),
                      float(estimate), "directional", outcome, tight, note)


def calibration_ok(estimate: float, exact: float, rel_tol: float = 0.05) -> bool:
    """Return whether a numerical calibration reproduces an exact anchor."""
    return abs(estimate - exact) <= rel_tol * abs(exact)


def matches(instance: str, claim: str, value: float, exact: float,
            rel_tol: float = 0.05) -> Comparison:
    """Calibration against a CLOSED FORM: outcome 'match' iff value is within ``rel_tol``,
    else 'mismatch'. Used where the ground truth is an exact formula, not a falsification.
    A calibration outcome says the implementation reproduces a known answer; it says
    nothing about the claim the target was built to probe."""
    rel = abs(value - exact) / max(abs(exact), 1e-300)
    outcome = "match" if rel <= rel_tol else "mismatch"
    return Comparison(instance, claim, float(exact), float(value), "calibration", outcome,
                      float(value / exact) if exact else None, f"rel_err={rel:.3g}")


def convergence_ok(a: float, b: float, rel_tol: float = 0.15) -> bool:
    """Two independent estimates (different seeds) must agree, else the chain is untrusted."""
    scale = max(abs(a), abs(b), 1e-12)
    return abs(a - b) <= rel_tol * scale
