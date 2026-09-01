"""Run provenance + repo paths: turn "committed + seeded" into reproducible.

Every artifact carries a versioned header from ``provenance()``. Run configuration, execution
environment, and derived summaries remain separate so a reader can reconstruct the invocation.
"""
from __future__ import annotations

import json
import platform
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

from importlib.metadata import PackageNotFoundError, version

# Third-party versions stamped into every artifact. Extend this tuple when the
# harness takes a new numerical dependency; a package that is absent is recorded
# as null rather than crashing the run.
STAMPED_PACKAGES = ("numpy",)


def repo_root() -> Path:
    """The repository root: the nearest ancestor holding both research/ and modules/,
    else `git rev-parse --show-toplevel`, else two levels up from this file."""
    here = Path(__file__).resolve()
    for p in here.parents:
        if (p / "research").is_dir() and (p / "modules").is_dir():
            return p
    top = _git("rev-parse", "--show-toplevel")
    if top:
        return Path(top)
    return here.parents[2]


def runs_dir() -> Path:
    """``research/runs/`` (created on demand), for directional research artifacts."""
    d = repo_root() / "research" / "runs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _package_version(name: str) -> str | None:
    """The installed version of one stamped dependency, or ``None`` when absent."""
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def _git(*args: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", *args],
            cwd=Path(__file__).resolve().parent,
            capture_output=True, text=True, check=True,
        )
        return out.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def provenance(*, schema_version: int, target: str, profile: str, stochastic: bool,
               config: dict[str, Any]) -> dict[str, Any]:
    """A JSON-serializable artifact header with inputs separated from environment.

    ``git_commit`` is a best-effort trace of which checkout produced the artifact. It is
    informational: reproducibility rests on the recorded seed, params, and library versions,
    and nothing gates on the state of the worktree.
    """
    return {
        "schema_version": int(schema_version),
        "date": date.today().isoformat(),
        "target": target,
        "profile": profile,
        "stochastic": bool(stochastic),
        "config": config,
        "git_commit": _git("rev-parse", "HEAD"),
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            **{name: _package_version(name) for name in STAMPED_PACKAGES},
        },
    }


def write_jsonl(path: str | Path, header: dict, records: list[dict],
                summary: dict | None = None) -> Path:
    """Write a versioned JSONL artifact without overwriting an existing path.

    ``.jsonl`` (not ``.log``) so the repo's LaTeX .gitignore does not swallow it.
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
