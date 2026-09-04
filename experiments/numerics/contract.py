"""Public contracts: what a target returns, and how one recorded result is shaped.

The contract is deliberately thin: a record carries a `kind`, a `claim`, an evidence class,
and an outcome. Everything genre-specific — a bound and a computed value, a search domain and
a witness, a range verified — lives in the record's `detail`, owned by the target.

`compare`, `matches` and `searched` are supplied helpers for three common shapes, not the
contract itself. A genre they do not fit uses `observe(...)` and puts its own fields in
`detail`; the vocabulary that is checked is the same either way.

Nothing here is a ledger status. An outcome names what the numbers did to the claim
(`contradicts`/`consistent`/`inconclusive`, or `match`/`mismatch` for a calibration);
promoting a statement remains a proof-and-review question (CLAUDE.md constraint 2).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from types import ModuleType
from typing import Any, Mapping


#: The one artifact format emitted and accepted by this template.
ARTIFACT_SCHEMA_VERSION = 1

#: How far a number can be trusted. A value may be labelled `exact` only when it is
#: closed-form or rationally certified; sampled, MCMC, FEM, quadrature, finite-grid and
#: floating-eigensolver values are `directional`. `calibration` is a check of the
#: implementation against a known answer, not evidence about the claim.
EVIDENCE_CLASSES = ("exact", "directional", "calibration")

#: What the number did to the claim, in the only terms that survive a change of genre.
#: A bound comparison, an exhaustive search, a verified-up-to-N sweep and a witness
#: search all land here; none of them is a ledger status.
OUTCOMES: Mapping[str, tuple[str, ...]] = {
    "exact": ("contradicts", "consistent", "inconclusive"),
    "directional": ("contradicts", "consistent", "inconclusive"),
    "calibration": ("match", "mismatch"),
}

#: The four fields every observation record carries, on top of its `kind`.
OBSERVATION_FIELDS = ("instance", "claim", "evidence", "outcome")


def check_observation(mapping: Mapping[str, Any], context: str = "observation") -> None:
    """Raise ValueError unless `mapping` is a complete, well-labelled observation."""
    for name in OBSERVATION_FIELDS:
        value = mapping.get(name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{context}: '{name}' must be a non-empty string")
    evidence, outcome = mapping["evidence"], mapping["outcome"]
    if evidence not in EVIDENCE_CLASSES:
        raise ValueError(
            f"{context}: evidence must be one of {EVIDENCE_CLASSES}, not {evidence!r}")
    if outcome not in OUTCOMES[evidence]:
        raise ValueError(
            f"{context}: {evidence} evidence takes outcome {OUTCOMES[evidence]}, "
            f"not {outcome!r}")
    detail = mapping.get("detail", {})
    if not isinstance(detail, dict):
        raise ValueError(f"{context}: 'detail' must be a mapping")


@dataclass(frozen=True)
class Observation:
    """One recorded result: what was tested, how far it can be trusted, what it did.

    `detail` is the genre-owned payload — bound and value, witness and domain, whatever
    the target's own mathematics needs. The four fields above it are what every reader of
    `research/runs/` can rely on without knowing the genre.
    """

    instance: str
    claim: str
    evidence: str
    outcome: str
    detail: dict[str, Any] = field(default_factory=dict)
    note: str = ""

    def __post_init__(self) -> None:
        check_observation(
            {"instance": self.instance, "claim": self.claim, "evidence": self.evidence,
             "outcome": self.outcome, "detail": self.detail},
            f"observation on '{self.instance}'",
        )

    def record(self, kind: str) -> dict[str, Any]:
        """This observation as an artifact record; `kind` names what it is to a reader."""
        if not isinstance(kind, str) or not kind.strip():
            raise ValueError("record kind must be a non-empty string")
        return {
            "kind": kind,
            "instance": self.instance,
            "claim": self.claim,
            "evidence": self.evidence,
            "outcome": self.outcome,
            "detail": dict(self.detail),
            "note": self.note,
        }


@dataclass
class RunResult:
    """One target execution, with inputs and derived outputs kept separate."""

    records: list[dict[str, Any]]
    config: dict[str, Any] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if "seed" in self.config:
            raise ValueError("target config must not repeat the runner-owned 'seed'")
        reserved = {"kind", "target", "profile"} & self.summary.keys()
        if reserved:
            raise ValueError(
                f"target summary uses runner-owned field(s): {', '.join(sorted(reserved))}")
        for index, record in enumerate(self.records):
            if not isinstance(record, dict) or not isinstance(record.get("kind"), str):
                raise ValueError(f"record {index} must be a mapping with a string 'kind'")
            # A record either is an observation or is auxiliary data a target chose to
            # keep. Half of an observation is the shape that lets an unlabelled number
            # look like evidence, so it is rejected.
            claimed = {name for name in OBSERVATION_FIELDS[1:] if name in record}
            if claimed:
                check_observation(record, f"record {index} ('{record['kind']}')")


@dataclass(frozen=True)
class TargetSpec:
    """CLI-facing metadata for one numerical target."""

    id: str
    module: ModuleType
    summary: str
    stochastic: bool
    profiles: Mapping[str, Mapping[str, Any]]

    def config_for(self, profile: str) -> dict[str, Any]:
        try:
            return dict(self.profiles[profile])
        except KeyError as exc:
            raise ValueError(f"target '{self.id}' has no profile '{profile}'; "
                             f"choose one of: {', '.join(self.profiles)}") from exc


def observe(instance: str, claim: str, *, evidence: str, outcome: str, note: str = "",
            **detail: Any) -> Observation:
    """Record one result in a genre the helpers below do not cover.

    This function certifies nothing: it is the caller who must pass `evidence="exact"`
    only for a closed-form or rationally certified value, and such a value is still a
    candidate until an independently reviewed dossier states it.
    """
    return Observation(instance, claim, evidence, outcome, detail, note)


def compare(instance: str, claim: str, *, bound: float, value: float, evidence: str,
            rel_tol: float = 0.10, note: str = "") -> Observation:
    """A computed value against a proposed upper bound: the inequality shape.

    `contradicts` when the value exceeds the bound beyond `rel_tol`, `consistent` when it
    does not, `inconclusive` when no finite bound was available.
    """
    if bound is None or not math.isfinite(bound):
        return Observation(instance, claim, evidence, "inconclusive",
                           {"bound": None, "value": float(value), "tightness": None}, note)
    outcome = "contradicts" if value > bound * (1 + rel_tol) else "consistent"
    return Observation(instance, claim, evidence, outcome,
                       {"bound": float(bound), "value": float(value),
                        "tightness": float(value / bound) if bound else None}, note)


def matches(instance: str, claim: str, *, value: float, exact: float,
            rel_tol: float = 0.05, note: str = "") -> Observation:
    """Calibrate against a CLOSED FORM: `match` iff `value` is within `rel_tol` of `exact`.

    A calibration says the implementation reproduces a known answer. It says nothing about
    the claim the target was built to probe.
    """
    rel = abs(value - exact) / max(abs(exact), 1e-300)
    return Observation(instance, claim, "calibration",
                       "match" if rel <= rel_tol else "mismatch",
                       {"exact": float(exact), "value": float(value), "rel_err": float(rel)},
                       note)


def searched(instance: str, claim: str, *, domain: str, witness: Any = None,
             evidence: str = "exact", note: str = "") -> Observation:
    """A finite search for something that would count against the claim.

    Covers a counterexample hunt, an exhaustive check over a finite family, and a
    verified-up-to-N sweep: `domain` says exactly what was covered, and a non-null
    `witness` is what was found. Finding nothing is `consistent` over that domain and
    nothing more — a finite battery establishes no universal statement.
    """
    outcome = "consistent" if witness is None else "contradicts"
    return Observation(instance, claim, evidence, outcome,
                       {"domain": domain, "witness": witness}, note)
