"""The numerics lane: the shape of the immutable run artifacts.

A run artifact is the only admissible form of numerical work (CLAUDE.md constraint 2),
and it is worth exactly as much as its provenance header. This lane checks that every
artifact under ``research/runs/`` still parses and still carries the header a later
reader needs in order to reproduce or retract it. It does not run anything: the numerics
package has its own test suite, invoked by ``scripts/check.sh``.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from .common import repo_relative

RUNS = Path("research/runs")
LEGACY_RUNS = Path("research/legacy-runs")

#: Every field a reader needs before an artifact's numbers mean anything.
PROVENANCE_FIELDS = ("schema_version", "date", "target", "profile", "config", "environment")
ARTIFACT_SCHEMA_VERSION = 1

#: Fields whose *presence* is required but whose value may be null — an artifact produced
#: outside a git checkout records nulls honestly rather than omitting the question.
PRESENT_FIELDS = ("stochastic",)

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
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _check_migrated_source(root: Path, context: str, header: dict,
                           errors: list[str]) -> None:
    """Verify the byte-preserved source named by a migrated artifact."""
    migrated = header.get("migrated_from")
    if migrated is None:
        return
    if not isinstance(migrated, dict):
        errors.append(f"{context}: _provenance.migrated_from must be a mapping")
        return

    source_name = migrated.get("path")
    expected = migrated.get("sha256")
    if not isinstance(source_name, str) or not source_name.strip():
        errors.append(f"{context}: migrated_from.path must be a non-empty string")
        return
    if not isinstance(expected, str) or SHA256_RE.fullmatch(expected) is None:
        errors.append(f"{context}: migrated_from.sha256 must be a lowercase SHA-256")
        return

    relative = Path(source_name)
    archive = (root / LEGACY_RUNS).resolve()
    source = (root / relative).resolve()
    try:
        source.relative_to(archive)
    except ValueError:
        errors.append(
            f"{context}: migrated_from.path must stay under {LEGACY_RUNS.as_posix()}/"
        )
        return
    if not source.is_file():
        errors.append(f"{context}: migrated source '{source_name}' does not exist")
        return
    actual = hashlib.sha256(source.read_bytes()).hexdigest()
    if actual != expected:
        errors.append(
            f"{context}: migrated source '{source_name}' has SHA-256 {actual}, "
            f"expected {expected}"
        )


def _check_observation(context: str, number: int, record: dict, errors: list[str]) -> None:
    """A record carrying any observation field carries all four, labelled from the vocabulary.

    This is the shape that lets an unlabelled number look like evidence. The harness
    rejects it at write time; this rejects it for every artifact already on disk,
    including every immutable artifact already in the repository.
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
        if version != ARTIFACT_SCHEMA_VERSION:
            errors.append(
                f"{context}: _provenance.schema_version must be "
                f"{ARTIFACT_SCHEMA_VERSION}, got '{version}'"
            )
        for field in SOURCE_FIELDS:
            if field not in header:
                errors.append(f"{context}: _provenance is missing '{field}'")
        _check_migrated_source(root, context, header, errors)
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
