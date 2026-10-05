"""What changed since a certification: the diff an editorial note or a re-review reads.

For a dossier, the baseline is the latest commit whose version has the fingerprint the
certification recorded, so it is verified. For a statement, it is the commit that first
recorded the fingerprint, and the statement is the text of its labelled directive there:
rebuilding the manuscript of that commit is a re-review's job, so this baseline is not
verified. Either way the diff runs to the working tree.
"""
from __future__ import annotations

import difflib
import hashlib
import re
import subprocess
from pathlib import Path

from .common import text_digest

OPENING_RE = re.compile(r"^\s*(:{3,}|`{3,})\{prf:")


def _git(root: Path, *arguments: str) -> str | None:
    try:
        result = subprocess.run(["git", "-C", str(root), *arguments], capture_output=True,
                                text=True, check=False)
    except OSError:
        return None
    return result.stdout if result.returncode == 0 else None


def _dossier_baseline(root: Path, path: str, digest: str) -> tuple[str, str] | None:
    """The latest committed version of ``path`` with fingerprint ``digest``."""
    for commit in (_git(root, "log", "--format=%H", "--", path) or "").split():
        text = _git(root, "show", f"{commit}:./{path}")
        if text is not None and digest in {
                text_digest(text), hashlib.sha256(text.encode("utf-8")).hexdigest()}:
            return commit, text
    return None


def directive(text: str, label: str) -> str | None:
    """The labelled claim directive carrying ``:label: <label>`` in ``text``."""
    lines = text.splitlines(keepends=True)
    at = next((i for i, line in enumerate(lines) if line.strip() == f":label: {label}"), None)
    if at is None:
        return None
    start = next((i for i in range(at, -1, -1) if OPENING_RE.match(lines[i])), None)
    if start is None:
        return None
    fence = OPENING_RE.match(lines[start]).group(1)
    end = next((i for i in range(at, len(lines)) if lines[i].strip() == fence), len(lines) - 1)
    return "".join(lines[start:end + 1])


def _statement(root: Path, revision: str | None, label: str) -> str | None:
    """The directive of ``label`` under ``modules/`` at ``revision``, or in the tree."""
    if revision is None:
        files = sorted((root / "modules").glob("**/*.md"))
        texts = (path.read_text(encoding="utf-8") for path in files)
    else:
        listed = _git(root, "grep", "-l", "-F", f":label: {label}", revision, "--", "modules")
        texts = (_git(root, "show", name.replace(":", ":./", 1)) or ""
                 for name in (listed or "").split())
    return next(filter(None, (directive(text, label) for text in texts)), None)


def _statement_baseline(root: Path, label: str, digest: str) -> tuple[str, str] | None:
    """The directive of ``label`` at the commit that first recorded ``digest``."""
    commits = (_git(root, "log", "--reverse", "--format=%H", f"-S{digest}") or "").split()
    if not commits:
        return None
    text = _statement(root, commits[0], label)
    return (commits[0], text) if text is not None else None


def diff(root: Path, item: str, recorded: str) -> list[str]:
    """Lines describing how ``item`` changed since the version fingerprinted ``recorded``."""
    if _git(root, "rev-parse", "--git-dir") is None:
        return ["baseline: not found (not a Git repository); diff by hand or review in full"]
    if item.startswith("solutions/"):
        found = _dossier_baseline(root, item, recorded)
        current_path = root / item
        current = current_path.read_text(encoding="utf-8") if current_path.is_file() else ""
        verified = "fingerprint verified"
    else:
        found = _statement_baseline(root, item, recorded)
        current = _statement(root, None, item) or ""
        verified = "commit that first recorded it; not re-fingerprinted"
    if found is None:
        return ["baseline: not found in Git history; diff by hand or review in full"]
    commit, before = found
    lines = [f"baseline: {commit[:12]} ({verified})"]
    lines += [line.rstrip("\n") for line in difflib.unified_diff(
        before.splitlines(keepends=True), current.splitlines(keepends=True),
        f"certified/{item}", f"current/{item}")]
    return lines
