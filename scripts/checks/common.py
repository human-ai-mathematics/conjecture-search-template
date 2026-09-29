"""Helpers shared by the checks: YAML files, front matter, string lists, contained paths."""
from __future__ import annotations

import hashlib
from datetime import date
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - environment guard
    raise SystemExit("PyYAML required: run the checker with 'uv run scripts/check.py'.")


def as_list(value: Any) -> list:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def one_of(value: Any, vocabulary: set[str]) -> bool:
    """``value in vocabulary``, without choking on an unhashable YAML list."""
    return isinstance(value, str) and value in vocabulary


def load_yaml(path: Path, context: object, errors: list[str]) -> dict | None:
    """A YAML file whose top level is a mapping, or ``None`` after reporting why not."""
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        errors.append(f"{context}: invalid YAML: {exc}")
        return None
    if not isinstance(doc, dict):
        errors.append(f"{context}: top level must be a mapping")
        return None
    return doc


def read_front_matter(path: Path, noun: str, errors: list[str]) -> dict | None:
    """The leading ``---`` YAML block of a Markdown record, as a mapping."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        errors.append(f"{path}: cannot read {noun}: {exc}")
        return None
    closing = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), None)
    if not lines or lines[0].strip() != "---" or closing is None:
        errors.append(f"{path}: {noun} must start with a '---' YAML front matter block")
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


def string_list(raw: dict, field: str, context: str, errors: list[str], *,
                required: bool = False) -> list[str]:
    """A list of unique non-empty strings; absent means empty unless ``required``."""
    value = raw.get(field)
    if value is None and not required:
        return []
    if not isinstance(value, list) or (required and not value):
        errors.append(f"{context}.{field}: must be a {'non-empty ' if required else ''}list")
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


def contained_path(root: Path, reference: object, directory: str, context: str,
                   errors: list[str], *, suffix: str | None = None) -> Path | None:
    """Resolve a repo-relative path that must exist under ``directory``."""
    if not isinstance(reference, str) or not reference.strip() or Path(reference).is_absolute():
        errors.append(f"{context}: want a repo-relative path, got '{reference}'")
        return None
    resolved = (root / reference).resolve()
    if not resolved.is_relative_to((root / directory).resolve()):
        errors.append(f"{context}: '{reference}' must be under {directory}/")
        return None
    if suffix is not None and resolved.suffix != suffix:
        errors.append(f"{context}: '{reference}' must be a {suffix} file")
        return None
    if not resolved.is_file():
        errors.append(f"{context}: '{reference}' does not exist")
        return None
    return resolved


def repo_relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def markdown_records(root: Path, directory: str, errors: list[str]) -> list[Path]:
    """Every Markdown record under ``directory``, oldest first. A record's date is its
    ``YYYY-MM-DD-`` filename prefix, which is therefore required."""
    records = []
    for path in sorted((root / directory).rglob("*.md")):
        try:
            date.fromisoformat(path.name[:10])
            if path.name[10:11] != "-":
                raise ValueError
        except ValueError:
            errors.append(f"{path}: name it '<YYYY-MM-DD>-<slug>.md'")
            continue
        records.append(path)
    return sorted(records, key=lambda path: path.name)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_fingerprint(text: str) -> str:
    """The SHA-256 of ``text`` with its whitespace runs collapsed: a candidate's statement
    keeps its fingerprint when a checkpoint is merely re-wrapped."""
    return hashlib.sha256(" ".join(text.split()).encode("utf-8")).hexdigest()
