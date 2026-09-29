# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Probe the identity of prop:example numerically, and search a small integer grid for a
vector that breaks it.

    uv run research/runs/2026-09-02-example.py

Copied from templates/run.py; writes 2026-09-02-example.jsonl beside itself. Seeded and
dependency-free, so rerunning it reproduces the artifact. Nothing it prints certifies
anything.
"""
import itertools
import json
import platform
import random
import subprocess
from importlib.metadata import version
from pathlib import Path

SEED = 20260902
PACKAGES: list[str] = []
OUT = Path(__file__).with_suffix(".jsonl")
N, GRID, WIDTH = 2000, 2, 4


def provenance(**params) -> dict:
    """The seed, the parameters, the commit (dirty if uncommitted) and the versions."""
    def git(*args: str) -> str:
        return subprocess.run(["git", *args], capture_output=True, text=True,
                              cwd=OUT.parent).stdout.strip()
    return {"provenance": {"seed": SEED, **params,
                           "git_commit": git("rev-parse", "HEAD") or None,
                           "dirty": bool(git("status", "--porcelain")),
                           "python": platform.python_version(),
                           "versions": {name: version(name) for name in PACKAGES}}}


def sides(a: list[float]) -> tuple[float, float]:
    """The two sides of prop:example, computed independently of each other."""
    mean = sum(a) / len(a)
    return sum((x - mean) ** 2 for x in a), sum(x * x for x in a) - len(a) * mean**2


def run(rng: random.Random) -> list[dict]:
    left, right = sides([rng.gauss(0.0, 1.0) for _ in range(N)])
    witness = next((list(v) for v in itertools.product(range(-GRID, GRID + 1), repeat=WIDTH)
                    if abs(sides(list(v))[0] - sides(list(v))[1]) > 1e-9), None)
    return [
        {"kind": "calibration", "claim": "prop:example on one Gaussian sample",
         "left": left, "right": right, "rel_err": abs(left - right) / abs(right)},
        {"kind": "search", "claim": "prop:example on every integer vector in [-2,2]^4",
         "searched": (2 * GRID + 1) ** WIDTH, "witness": witness},
    ]


if __name__ == "__main__":
    records = [provenance(n=N, grid=GRID, width=WIDTH), *run(random.Random(SEED))]
    OUT.write_text("".join(json.dumps(record) + "\n" for record in records))
    print(OUT.read_text(), end="")
