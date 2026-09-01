"""Dispatch a target run -> a provenance-stamped JSONL research artifact.

The artifact may be cited by a dated exploration, but it does not enter a claim node.
``numerics`` does not edit the ledger, validate claims, or certify proofs; the artifact records
research direction only. Each target module owns its calibration gate and diagnostic logic in
``run_records``.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .contract import ARTIFACT_SCHEMA_VERSION, RunResult
from .provenance import provenance, runs_dir, write_jsonl
from .targets import REGISTRY


def run(target: str, seed: int = 0, profile: str = "standard",
        out: str | Path | None = None) -> Path:
    """Run a target's battery; write a directional research artifact. Return its path."""
    if target not in REGISTRY:
        raise ValueError(f"unknown target '{target}'; have {sorted(REGISTRY)}")
    spec = REGISTRY[target]
    profile_config = spec.config_for(profile)
    result = spec.module.run_records(seed, **profile_config)
    if not isinstance(result, RunResult):
        raise TypeError(f"target '{target}' returned {type(result).__name__}, expected RunResult")
    result.validate()
    config = {"seed": int(seed), **result.config}
    header = provenance(
        schema_version=ARTIFACT_SCHEMA_VERSION,
        target=target,
        profile=profile,
        stochastic=spec.stochastic,
        config=config,
    )
    if out is None:
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%S.%fZ")
        out = runs_dir() / f"{stamp}-{target}.jsonl"
    summary = {"target": target, "profile": profile, **result.summary}
    return write_jsonl(out, header, result.records, summary)
