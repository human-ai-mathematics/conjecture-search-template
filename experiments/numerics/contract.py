"""Public contracts shared by the numerics CLI, targets, and artifact writer."""
from __future__ import annotations

from dataclasses import dataclass, field
from types import ModuleType
from typing import Any, Mapping


ARTIFACT_SCHEMA_VERSION = 1


@dataclass
class RunResult:
    """One target execution, with inputs and derived outputs kept separate."""

    records: list[dict[str, Any]]
    config: dict[str, Any] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if "seed" in self.config:
            raise ValueError("target config must not repeat the runner-owned 'seed'")
        reserved_summary = {"kind", "target", "profile"} & self.summary.keys()
        if reserved_summary:
            names = ", ".join(sorted(reserved_summary))
            raise ValueError(f"target summary uses runner-owned field(s): {names}")
        for index, record in enumerate(self.records):
            if not isinstance(record, dict) or not isinstance(record.get("kind"), str):
                raise ValueError(f"record {index} must be a mapping with a string 'kind'")


@dataclass(frozen=True)
class TargetSpec:
    """CLI-facing metadata for a heterogeneous numerical target."""

    id: str
    module: ModuleType
    summary: str
    stochastic: bool
    profiles: Mapping[str, Mapping[str, Any]]

    def config_for(self, profile: str) -> dict[str, Any]:
        try:
            return dict(self.profiles[profile])
        except KeyError as exc:
            choices = ", ".join(self.profiles)
            raise ValueError(
                f"target '{self.id}' has no profile '{profile}'; choose one of: {choices}"
            ) from exc

    @property
    def default_profile(self) -> str:
        return "standard"
