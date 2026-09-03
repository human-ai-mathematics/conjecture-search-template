"""The numerics plane: the shape of the immutable run artifacts.

A run artifact is the only admissible form of numerical work (CLAUDE.md constraint 2),
and it is worth exactly as much as its provenance header. This plane checks that every
artifact under ``research/runs/`` still parses and still carries the header a later
reader needs in order to reproduce or retract it. It does not run anything: the numerics
package has its own test suite, invoked by ``scripts/check.sh``.
"""
from __future__ import annotations

import json
from pathlib import Path

from .common import repo_relative

RUNS = Path("research/runs")

#: Every field a reader needs before an artifact's numbers mean anything.
PROVENANCE_FIELDS = ("schema_version", "date", "target", "profile", "config", "environment")


def check(root: Path, errors: list[str]) -> list[dict]:
    """Validate every run artifact envelope; return one summary per artifact."""
    directory = root / RUNS
    artifacts: list[dict] = []
    if not directory.is_dir():
        return artifacts

    for path in sorted(directory.rglob("*.jsonl")):
        context = repo_relative(root, path)
        try:
            lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        except (OSError, UnicodeError) as exc:
            errors.append(f"{context}: cannot read run artifact: {exc}")
            continue
        if not lines:
            errors.append(f"{context}: run artifact is empty")
            continue

        records = []
        malformed = False
        for number, line in enumerate(lines, 1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"{context}:{number}: not valid JSON: {exc}")
                malformed = True
                break
            if not isinstance(record, dict):
                errors.append(f"{context}:{number}: every record must be a JSON object")
                malformed = True
                break
            records.append(record)
        if malformed:
            continue

        header = records[0].get("_provenance")
        if not isinstance(header, dict):
            errors.append(f"{context}: first record must be the '_provenance' header")
            continue
        for field in PROVENANCE_FIELDS:
            if header.get(field) in (None, ""):
                errors.append(f"{context}: _provenance is missing '{field}'")
        for number, record in enumerate(records[1:], 2):
            if "_provenance" in record:
                errors.append(f"{context}:{number}: only the first record carries provenance")

        target = header.get("target")
        if isinstance(target, str) and target.strip() and not path.stem.endswith(f"-{target}"):
            errors.append(
                f"{context}: filename must end with '-{target}.jsonl' so an artifact is "
                "identifiable without opening it"
            )
        if len(records) < 2:
            errors.append(f"{context}: run artifact records no observation")
        artifacts.append({"path": context, "target": target, "records": len(records) - 1})
    return artifacts
