"""Helpers shared by every validation lane.

Nothing here knows about the mathematics. These are the four things more than one
lane needs: reading a dated Markdown record's YAML envelope, checking that its date
agrees with its filename, validating a list of unique strings, and resolving a
repo-relative path without letting it escape the repository.
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any

# PyYAML is the checker's one dependency, declared in the root pyproject.toml. Every
# other module in this package imports it *from here* rather than directly, so this hint
# is what a missing install produces no matter which module happens to load first.
try:
    import yaml
except ImportError:  # pragma: no cover - environment guard
    raise SystemExit(
        "PyYAML required. Install it with 'pip install pyyaml', or run the checker as "
        "'uv run python scripts/check.py', which reads the root pyproject.toml."
    )

#: The validation lanes, in the order a default run reports them. A lane is an
#: implementation partition of the checker, not one of the repository's three
#: domains and not one of CLAUDE.md's activation gates. A lane whose files are
#: absent contributes nothing: that is what makes activation structural rather
#: than a configured mode.
LANES = ("core", "proofs", "checkpoints", "portfolio", "numerics", "roles", "docs")

#: A portfolio approach id. Shared, because the portfolio declares these ids and the
#: checkpoint lane resolves against them; one regex keeps the two lanes agreeing.
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


#: A dated record carries either a plain ISO date or a UTC timestamp. The timestamp form
#: exists so that two records written on the same day can be *told* apart in time. Without
#: one the checker does not guess: a filename slug is not a clock, and sorting paths
#: lexically once rejected a legitimate same-day promotion because ``p`` sorts after ``r``.
RECORD_INSTANT_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})(?:T(\d{2}:\d{2}:\d{2})Z)?$")


def record_instant(value: str | None) -> tuple[str, str]:
    """Split a record's ``date`` into ``(day, time)``; an untimed record has ``time=""``.

    Comparing the pair orders two records only as far as they are actually ordered. An
    empty time is not "midnight" — it is *unknown*, and ``strictly_after`` treats it so.
    """
    match = RECORD_INSTANT_RE.match(value or "")
    if match is None:
        return (value or "", "")
    return (match.group(1), match.group(2) or "")


def strictly_after(later: tuple[str, str], earlier: tuple[str, str]) -> bool:
    """Is ``later`` genuinely after ``earlier``, rather than merely sorting after it?

    Different days answer themselves. On the same day the answer is yes only when both
    records carry a timestamp; otherwise their order is unknown and this returns ``False``
    in both directions, so a caller asking "did this happen out of order?" gets no for an
    ambiguous pair rather than an answer it has not earned.
    """
    if later[0] != earlier[0]:
        return later[0] > earlier[0]
    if not later[1] or not earlier[1]:
        return False
    return later[1] > earlier[1]


def check_record_date(path: Path, raw: dict, errors: list[str]) -> str | None:
    """A quoted ISO date or UTC timestamp agreeing with the filename prefix."""
    value = raw.get("date")
    if not isinstance(value, str):
        errors.append(
            f"{path}.date: must be a quoted ISO date YYYY-MM-DD, or a UTC timestamp "
            "YYYY-MM-DDTHH:MM:SSZ to order records written on the same day"
        )
        return None
    match = RECORD_INSTANT_RE.match(value)
    day = match.group(1) if match else value
    if match is None:
        errors.append(
            f"{path}.date: invalid ISO date '{value}': want YYYY-MM-DD or "
            "YYYY-MM-DDTHH:MM:SSZ"
        )
    else:
        try:
            date.fromisoformat(day)
        except ValueError:
            errors.append(f"{path}.date: invalid ISO date '{value}'")
    if not path.name.startswith(f"{day}-"):
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
    cross-lane pointer in this repository — a dossier, a review, a run artifact, a
    checkpoint — is confined to its own directory, so that a lane cannot quietly
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
