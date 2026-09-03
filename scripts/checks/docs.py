"""The docs lane: repository-relative Markdown links resolve.

Small, and it earns its place. Several of this repository's source-of-truth tables pointed
straight at ``research/program/brief.md`` and ``research/program/portfolio.yaml``, which are
*correctly* absent until their gates open — so a fresh clone shipped twelve links that 404'd,
and the one role that would have found them is proposal-only and, since the packs split, not
installed by default. A structural invariant beats a role nobody ran.

Two directories are exempt, and the exemption is the point rather than an oversight.
``decisions/`` and ``research/reviews/`` are append-only (CLAUDE.md constraint 7): several of
their records deliberately name paths that have since moved, and they are correct as written
for the repository they described. Rewriting them to satisfy a link checker would be exactly
the rewriting that constraint forbids.

``templates/`` is exempt for a different reason: a scaffold's links are written for where the
file is going, not where it sits.
"""
from __future__ import annotations

import re
from pathlib import Path

#: ``[text](target)``. Reference-style links and bare URLs are not matched, and neither is
#: anything with whitespace in the target, which in Markdown is a title rather than a path.
LINK_RE = re.compile(r"\[[^\]\n]*\]\(([^)\s]+)\)")

#: Append-only archives, plus the scaffolds whose links point at their destination.
EXEMPT = ("decisions", "research/reviews", "templates", "build")

SKIP_PREFIXES = ("http://", "https://", "mailto:", "#", "//", "data:")


def _targets(text: str):
    for match in LINK_RE.finditer(text):
        target = match.group(1)
        if target.startswith(SKIP_PREFIXES):
            continue
        # Drop a fragment or a query; neither is part of the path on disk.
        path = target.split("#", 1)[0].split("?", 1)[0]
        if path:
            yield target, path


def check(root: Path, errors: list[str]) -> int:
    """Validate every repository-relative Markdown link; return how many were checked."""
    checked = 0
    for path in sorted(root.rglob("*.md")):
        try:
            relative = path.relative_to(root).as_posix()
        except ValueError:  # pragma: no cover - rglob cannot leave root
            continue
        if any(relative == item or relative.startswith(f"{item}/") for item in EXEMPT):
            continue
        if any(part.startswith(".") and part not in {".claude", ".codex"}
               for part in Path(relative).parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"{relative}: cannot read: {exc}")
            continue
        for target, candidate in _targets(text):
            checked += 1
            if candidate.startswith("/"):
                errors.append(
                    f"{relative}: link '{target}' is absolute; use a path relative to "
                    "this file, so the repository stays readable from any checkout"
                )
                continue
            if not (path.parent / candidate).exists():
                errors.append(f"{relative}: link '{target}' does not resolve")
    return checked
