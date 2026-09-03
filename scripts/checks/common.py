"""Helpers shared by every validation plane.

Nothing here knows about the mathematics. These are the four things more than one
plane needs: reading a dated Markdown record's YAML envelope, checking that its date
agrees with its filename, validating a list of unique strings, and resolving a
repo-relative path without letting it escape the repository.
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - environment guard
    raise SystemExit("PyYAML required: pip install pyyaml")

#: The validation planes, in the order the default lane reports them. A plane whose
#: files are absent contributes nothing: that is what makes activation structural
#: rather than a configured mode (CLAUDE.md, "The gates").
PLANES = ("core", "proofs", "checkpoints", "portfolio", "numerics", "roles")

#: A portfolio approach id. Shared, because the portfolio declares these ids and the
#: checkpoint plane resolves against them; one regex keeps the two planes agreeing.
APPROACH_ID_RE = re.compile(r"^ap:[a-z0-9][a-z0-9-]*$")


def as_list(value: Any) -> list:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def mentions_token(text: str, token: str) -> bool:
    """Match a complete repository id or agent name, not a longer prefix lookalike."""
    token_characters = r"A-Za-z0-9_./:\-"
    return re.search(
        rf"(?<![{token_characters}]){re.escape(token)}(?![{token_characters}])",
        text,
    ) is not None


def read_front_matter(path: Path, noun: str, errors: list[str]) -> dict | None:
    """Parse the leading YAML front matter of a persisted Markdown record.

    Shared by every record genre that carries a machine-readable envelope — review
    reports, dated checkpoints, the problem brief — so the envelope is parsed one way
    everywhere.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errors.append(f"{path}: cannot read {noun}: {exc}")
        return None
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        errors.append(f"{path}: {noun} must start with YAML front matter")
        return None
    try:
        closing = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration:
        errors.append(f"{path}: {noun} front matter lacks a closing '---'")
        return None
    try:
        raw = yaml.safe_load("\n".join(lines[1:closing])) or {}
    except yaml.YAMLError as exc:
        errors.append(f"{path}: invalid {noun} front matter: {exc}")
        return None
    if not isinstance(raw, dict):
        errors.append(f"{path}: {noun} front matter must be a mapping")
        return None
    return raw


def check_record_date(path: Path, raw: dict, errors: list[str]) -> str | None:
    """A quoted ISO date that agrees with the filename prefix, for a dated record."""
    value = raw.get("date")
    if not isinstance(value, str):
        errors.append(f"{path}.date: must be a quoted ISO date YYYY-MM-DD")
        return None
    try:
        date.fromisoformat(value)
    except ValueError:
        errors.append(f"{path}.date: invalid ISO date '{value}'")
    if not path.name.startswith(f"{value}-"):
        errors.append(f"{path}.date: must match the filename prefix")
    return value


def optional_string_list(raw: dict, field: str, context: str,
                         errors: list[str]) -> list[str]:
    """Validate one optional list of unique non-empty strings; absent means empty."""
    if field not in raw:
        return []
    value = raw[field]
    if not isinstance(value, list):
        errors.append(f"{context}.{field}: must be a list")
        return []
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{context}.{field}: entries must be non-empty strings")
        elif item in result:
            errors.append(f"{context}.{field}: duplicate entry '{item}'")
        else:
            result.append(item)
    return result


def required_string_set(raw: dict, field: str, context: str,
                        errors: list[str]) -> set[str]:
    """Validate one required non-empty list of unique strings."""
    value = raw.get(field)
    if not isinstance(value, list) or not value:
        errors.append(f"{context}.{field}: must be a non-empty list")
        return set()
    result: set[str] = set()
    for item in value:
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{context}.{field}: entries must be non-empty strings")
            continue
        if item in result:
            errors.append(f"{context}.{field}: duplicate entry '{item}'")
        result.add(item)
    return result


def contained_path(root: Path, reference: object, directory: str, context: str,
                   errors: list[str], *, suffix: str | None = None,
                   must_exist: bool = True, outside: str | None = None) -> Path | None:
    """Resolve one repo-relative reference that must stay under ``directory``.

    Returns the resolved path, or ``None`` when the reference is unusable. Every
    cross-plane pointer in this repository — a dossier, a review, a run artifact, a
    checkpoint — is confined to its own directory, so that a plane cannot quietly
    acquire evidence from somewhere the reader is not looking.
    """
    if not isinstance(reference, str) or not reference.strip():
        errors.append(f"{context}: must be a non-empty repo-relative path")
        return None
    relative = Path(reference)
    if relative.is_absolute():
        errors.append(f"{context}: want a repo-relative path, got '{reference}'")
        return None
    resolved = (root / relative).resolve()
    try:
        resolved.relative_to((root / directory).resolve())
    except ValueError:
        errors.append(
            f"{context}: {outside or f"'{reference}' must stay under {directory}/"}"
        )
        return None
    if suffix is not None and resolved.suffix != suffix:
        errors.append(f"{context}: '{reference}' must be a {suffix} file")
        return None
    if must_exist and not resolved.is_file():
        errors.append(f"{context}: '{reference}' does not exist")
        return None
    return resolved


def repo_relative(root: Path, path: Path) -> str:
    """The POSIX repo-relative form of a path already known to be inside the root."""
    return path.resolve().relative_to(root.resolve()).as_posix()
