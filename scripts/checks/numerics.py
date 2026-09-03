"""The numerics lane: the shape of the immutable run artifacts.

A run artifact is the only admissible form of numerical work (CLAUDE.md constraint 2),
and it is worth exactly as much as its provenance header. This lane checks that every
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

#: Fields whose *presence* is required but whose value may be null — an artifact produced
#: outside a git checkout records nulls honestly rather than omitting the question.
PRESENT_FIELDS = ("stochastic",)

#: Source-tree provenance arrived with schema 3. Artifacts are immutable, so an older one
#: is asked only for what its own version promised.
SOURCE_FIELDS_FROM_VERSION = 3
SOURCE_FIELDS = ("git_commit", "git_dirty", "git_diff_sha256")

#: The observation vocabulary, duplicated from ``experiments/numerics/contract.py`` on
#: purpose: this package validates the archive without importing the harness that wrote
#: it, so a deleted or broken numerics package still leaves the artifacts checkable.
#: ``scripts/tests/test_numerics.py`` asserts the two copies agree.
EVIDENCE_CLASSES = ("exact", "directional", "calibration")
OUTCOMES = {
    "exact": ("contradicts", "consistent", "inconclusive"),
    "directional": ("contradicts", "consistent", "inconclusive"),
    "calibration": ("match", "mismatch"),
}
OBSERVATION_FIELDS = ("instance", "claim", "evidence", "outcome")


def _check_observation(context: str, number: int, record: dict, errors: list[str]) -> None:
    """A record carrying any observation field carries all four, labelled from the vocabulary.

    This is the shape that lets an unlabelled number look like evidence. The harness
    rejects it at write time; this rejects it for every artifact already on disk,
    including ones written by an older harness.
    """
    present = [field for field in OBSERVATION_FIELDS if field in record]
    if not present:
        return
    if len(present) != len(OBSERVATION_FIELDS):
        missing = [field for field in OBSERVATION_FIELDS if field not in record]
        errors.append(
            f"{context}:{number}: half an observation — carries {present}, missing "
            f"{missing}; an unlabelled number is not evidence"
        )
        return
    evidence = record.get("evidence")
    if evidence not in EVIDENCE_CLASSES:
        errors.append(
            f"{context}:{number}.evidence: want one of {list(EVIDENCE_CLASSES)}, "
            f"got '{evidence}'"
        )
        return
    outcome = record.get("outcome")
    if outcome not in OUTCOMES[evidence]:
        errors.append(
            f"{context}:{number}.outcome: evidence '{evidence}' allows "
            f"{list(OUTCOMES[evidence])}, got '{outcome}'"
        )


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
        for field in PRESENT_FIELDS:
            if field not in header:
                errors.append(f"{context}: _provenance is missing '{field}'")
        version = header.get("schema_version")
        if isinstance(version, int) and version >= SOURCE_FIELDS_FROM_VERSION:
            for field in SOURCE_FIELDS:
                if field not in header:
                    errors.append(
                        f"{context}: _provenance is missing '{field}'; schema "
                        f"{version} records which source tree produced the run"
                    )
        for number, record in enumerate(records[1:], 2):
            if "_provenance" in record:
                errors.append(f"{context}:{number}: only the first record carries provenance")
            elif record.get("kind") != "run-summary":
                _check_observation(context, number, record, errors)

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
