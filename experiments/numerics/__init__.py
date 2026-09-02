"""numerics — the numerical channel for this repository's research program.

Role (see ../../research/README.md): produce provenance-stamped diagnostic artifacts that guide
exploration. Numerics NEVER promote a statement to proved.

Soundness contract: every record is an observation carrying a claim, an evidence class, and an
outcome, and the outcome is deliberately not a ledger status. Sampled, MCMC, FEM, quadrature,
finite-grid and floating-eigensolver values are directional only; corroboration is never proof.
An exact witness emitted here is a candidate that still requires an independently reviewed proof
or refutation dossier before it has logical force (CLAUDE.md constraint 2).

Genre neutrality: `compare`, `matches` and `searched` are supplied helpers for three common
shapes — a bound against a computed value, a calibration against a closed form, a finite search
for a witness. A target whose mathematics fits none of them uses `observe(...)` with its own
`detail` fields and is checked by exactly the same vocabulary.
"""
from __future__ import annotations

from .contract import (
    ARTIFACT_SCHEMA_VERSION,
    EVIDENCE_CLASSES,
    OBSERVATION_FIELDS,
    OUTCOMES,
    Observation,
    RunResult,
    TargetSpec,
    check_observation,
    compare,
    matches,
    observe,
    searched,
)

__all__ = [
    "ARTIFACT_SCHEMA_VERSION",
    "EVIDENCE_CLASSES",
    "OBSERVATION_FIELDS",
    "OUTCOMES",
    "Observation",
    "RunResult",
    "TargetSpec",
    "check_observation",
    "compare",
    "matches",
    "observe",
    "searched",
]
