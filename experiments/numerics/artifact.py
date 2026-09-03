"""Run a target and write its provenance-stamped JSONL artifact.

"Committed + seeded" is what makes a run reproducible, so every artifact carries a versioned
header recording the seed, the resolved configuration, and the environment, separately from the
derived summary. Artifacts are written with exclusive creation and never rewritten; a dated
exploration may cite one, but a run enters no claim node (CLAUDE.md constraint 2).
"""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import date, datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from .contract import ARTIFACT_SCHEMA_VERSION, RunResult
from .targets import REGISTRY

# Third-party versions stamped into every artifact. Extend this tuple when the harness takes a
# new numerical dependency; a package that is absent is recorded as null rather than crashing.
STAMPED_PACKAGES = ("numpy",)


def repo_root() -> Path:
    """The nearest ancestor holding both research/ and modules/, else the git top level."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "research").is_dir() and (parent / "modules").is_dir():
            return parent
    top = _git("rev-parse", "--show-toplevel")
    return Path(top) if top else here.parents[2]


def runs_dir() -> Path:
    """``research/runs/`` (created on demand), where artifacts land."""
    directory = repo_root() / "research" / "runs"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def confine_to_runs(out: str | Path) -> Path:
    """Resolve one requested artifact path, refusing anything outside ``research/runs/``."""
    directory = runs_dir().resolve()
    resolved = Path(out).expanduser()
    resolved = (directory / resolved).resolve() if not resolved.is_absolute() \
        else resolved.resolve()
    try:
        resolved.relative_to(directory)
    except ValueError:
        raise ValueError(
            f"--out must stay under research/runs/, got '{out}'"
        ) from None
    return resolved


def _git(*args: str) -> str | None:
    try:
        done = subprocess.run(["git", *args], cwd=Path(__file__).resolve().parent,
                              capture_output=True, text=True, check=True)
        return done.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _package_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def source_state() -> dict[str, Any]:
    """Which source tree produced this artifact: the commit, plus any uncommitted diff.

    ``git_commit`` alone could not reproduce a run whose target implementation was still
    uncommitted, which is the normal case while a diagnostic is being written. Recording
    ``git_dirty`` and a hash of the diff closes that gap without gating anything: a dirty
    run is still a run, and its numbers are worth exactly what any numbers are worth
    (CLAUDE.md constraint 2). This is provenance, not eligibility — the retired
    ``evidence_eligible`` field decided whether output counted, and nothing here does.

    Every field is present even outside a git checkout, where the values are null.
    """
    commit = _git("rev-parse", "HEAD")
    if commit is None:
        return {"git_commit": None, "git_dirty": None, "git_diff_sha256": None}
    diff = _git("diff", "HEAD")
    dirty = bool(_git("status", "--porcelain"))
    digest = (hashlib.sha256(diff.encode("utf-8")).hexdigest()
              if dirty and diff else None)
    return {"git_commit": commit, "git_dirty": dirty, "git_diff_sha256": digest}


def provenance(*, target: str, profile: str, stochastic: bool,
               config: dict[str, Any]) -> dict[str, Any]:
    """The artifact header: inputs, then environment, kept apart from derived results."""
    return {
        "schema_version": ARTIFACT_SCHEMA_VERSION,
        "date": date.today().isoformat(),
        "target": target,
        "profile": profile,
        "stochastic": bool(stochastic),
        "config": config,
        **source_state(),
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            **{name: _package_version(name) for name in STAMPED_PACKAGES},
        },
    }


def write_jsonl(path: str | Path, header: dict, records: list[dict],
                summary: dict | None = None) -> Path:
    """Write a versioned JSONL artifact, refusing to overwrite an existing path.

    ``.jsonl`` (not ``.log``) so the repository's LaTeX .gitignore does not swallow it.
    """
    path = Path(path)
    if path.suffix == ".log":
        raise ValueError("use .jsonl for artifacts; the repo .gitignore eats *.log")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as fh:
        fh.write(json.dumps({"_provenance": header}) + "\n")
        for rec in records:
            fh.write(json.dumps(rec) + "\n")
        if summary is not None:
            fh.write(json.dumps({"kind": "run-summary", **summary}) + "\n")
    return path


def run(target: str, seed: int = 0, profile: str = "standard",
        out: str | Path | None = None) -> Path:
    """Run one target's battery into a new artifact; return its path."""
    if target not in REGISTRY:
        raise ValueError(f"unknown target '{target}'; have {sorted(REGISTRY)}")
    spec = REGISTRY[target]
    result = spec.module.run_records(seed, **spec.config_for(profile))
    if not isinstance(result, RunResult):
        raise TypeError(f"target '{target}' returned {type(result).__name__}, expected RunResult")
    result.validate()
    header = provenance(target=target, profile=profile, stochastic=spec.stochastic,
                        config={"seed": int(seed), **result.config})
    if out is None:
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%S.%fZ")
        out = runs_dir() / f"{stamp}-{target}.jsonl"
    return write_jsonl(out, header, result.records,
                       {"target": target, "profile": profile, **result.summary})
