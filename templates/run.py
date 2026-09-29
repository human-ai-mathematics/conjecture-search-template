# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""What this run probes, and which node or candidate it bears on.

    uv run research/runs/YYYY-MM-DD-slug.py

Copy to research/runs/<YYYY-MM-DD>-<slug>.py; it writes <same name>.jsonl beside itself: a
provenance line, then one record per result. Format: SPECIFICATION.md, Formats → Run.
Nothing it prints certifies anything.
"""
import json
import platform
import random
import subprocess
from importlib.metadata import version
from pathlib import Path

SEED = 0                    # fixed once the artifact is cited
PACKAGES: list[str] = []    # the dependencies above, by name, e.g. ["numpy", "mpmath"]
OUT = Path(__file__).with_suffix(".jsonl")


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


def run(rng: random.Random) -> list[dict]:
    """The computation: one record per result, naming the node or candidate it bears on."""
    return []


if __name__ == "__main__":
    records = [provenance(), *run(random.Random(SEED))]
    OUT.write_text("".join(json.dumps(record) + "\n" for record in records))
    print(OUT.read_text(), end="")
