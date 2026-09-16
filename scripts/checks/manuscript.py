"""The manuscript as MyST parses it: every labelled target, and what MyST could not resolve.

The manuscript is MyST Markdown, so this module does not parse it. It runs ``myst build
--site`` in the repository root and reads the abstract syntax tree MyST writes under
``_build/site/content/``. A claim is then exactly what MyST says it is: a ``proof`` node
whose ``kind`` is one of the ledger's kinds (``prf:theorem``, ``prf:conjecture``, …),
carrying a ``label``. Every other labelled node — a heading, an equation, a figure, a
``prf:remark`` — is structural.

The build writes only under ``_build/``, which is gitignored: ``check.py`` writes nothing
the repository tracks. Its first run in a fresh clone downloads MyST's site theme into the
same directory; later runs work offline.

Every error MyST reports (its ``⛔️`` lines) is an error here: a directive MyST dropped —
a ``prf:lemma`` with no body, say — is absent from the tree, so the tree alone would not
say so. Beyond those, three things MyST only warns about and this repository refuses,
because each one silently breaks the anchor invariant:

* an unknown directive or role, left in the tree unprocessed — a ``prf:question`` is not a
  claim MyST knows, so it is not a claim at all;
* a cross-reference that resolves to nothing;
* two targets that share a label, or whose HTML anchors collide once MyST normalizes them
  (``a:b-c`` and ``a-b:c`` both become ``#a-b-c``).
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from .ledger import KIND

#: The checker's own repository. Its ``node_modules`` holds the pinned, patched MyST, and a
#: tree validated with ``--root`` — ``example/``, a test fixture — uses that one too.
REPO = Path(__file__).resolve().parents[2]

CONFIG = "myst.yml"
CONTENT = Path("_build/site/content")
MODULES = "modules"

#: How long a site build may take before the checker gives up on it.
BUILD_TIMEOUT = 600

#: Node types that carry a ``label`` naming something *else*. They point at targets rather
#: than being targets, so they neither claim a label nor collide with one.
REFERENCE_TYPES = frozenset({
    "crossReference", "link", "cite", "citeGroup", "footnoteReference",
    "footnoteDefinition", "captionNumber",
})

#: How MyST marks an error in its output.
ERROR_MARK = "\u26d4"
#: MyST errors the tree reports better, with the directive's name and a remedy.
REPORTED_FROM_TREE = re.compile(r"unknown (directive|role):")


def myst_command(root: Path) -> list[str] | None:
    """The MyST executable: the tree's own install, the checker's, then ``PATH``."""
    for base in (root, REPO):
        candidate = base / "node_modules" / ".bin" / "myst"
        if candidate.is_file():
            return [str(candidate)]
    found = shutil.which("myst")
    return [found] if found else None


def html_id(label: str) -> str:
    """The anchor MyST derives from a label; mirrors ``createHtmlId`` in myst-common."""
    anchor = re.sub(r"[^a-z0-9-]", "-", label.lower())
    anchor = re.sub(r"^([0-9-])", r"id-\1", anchor)
    anchor = re.sub(r"-{2,}", "-", anchor)
    return anchor.strip("-")


def build(root: Path, errors: list[str]) -> Path | None:
    """Run ``myst build --site`` in ``root``; return the AST directory, or ``None``."""
    command = myst_command(root)
    if command is None:
        errors.append(
            f"{CONFIG}: MyST is required to read the manuscript and was not found; "
            "run 'npm ci' at the repository root (package.json pins it)"
        )
        return None
    content = root / CONTENT
    # A page deleted since the last build would otherwise still be read from here.
    shutil.rmtree(content, ignore_errors=True)
    try:
        result = subprocess.run(
            [*command, "build", "--site"], cwd=root, capture_output=True, text=True,
            timeout=BUILD_TIMEOUT, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        errors.append(f"{CONFIG}: 'myst build --site' did not run: {exc}")
        return None
    for line in (result.stdout + result.stderr).splitlines():
        message = line.strip()
        if message.startswith(ERROR_MARK) and not REPORTED_FROM_TREE.search(message):
            errors.append(f"MyST: {message.lstrip(ERROR_MARK).lstrip(chr(0xFE0F)).strip()}")
    if result.returncode != 0 or not content.is_dir():
        tail = "\n".join((result.stdout + result.stderr).strip().splitlines()[-5:])
        errors.append(
            f"{CONFIG}: 'myst build --site' failed (exit {result.returncode}); "
            f"its last lines:\n{tail}"
        )
        return None
    return content


def _walk(node: object):
    if isinstance(node, dict):
        yield node
        for child in node.get("children") or []:
            yield from _walk(child)


def _line(node: dict) -> str:
    line = ((node.get("position") or {}).get("start") or {}).get("line")
    return f":{line}" if line else ""


def read(content: Path, errors: list[str]) -> dict[str, dict]:
    """Every labelled target under ``modules/``, from the AST MyST wrote to ``content``.

    Returns ``{label: {"kind": <ledger kind or None>, "file": "modules/…md"}}``: ``kind``
    is set only for a claim, and ``None`` marks a structural label. Targets outside
    ``modules/`` — a theorem restated in a dossier, the index page — are not manuscript
    anchors and are left out, but they still take part in the duplicate and anchor
    collision checks, because MyST resolves labels across the whole project.
    """
    labels: dict[str, dict] = {}
    seen: dict[str, str] = {}
    anchors: dict[str, str] = {}
    for path in sorted(content.glob("*.json")):
        try:
            page = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"{path}: cannot read MyST output: {exc}")
            continue
        relative = str(page.get("location") or path.name).lstrip("/")
        for node in _walk(page.get("mdast")):
            kind = node.get("type")
            where = f"{relative}{_line(node)}"
            if kind == "mystDirective":
                errors.append(
                    f"{where}: unknown MyST directive '{node.get('name')}'; a claim is "
                    f"one of prf:{', prf:'.join(sorted(KIND))}"
                )
                continue
            if kind == "mystRole":
                errors.append(f"{where}: unknown MyST role '{node.get('name')}'")
                continue
            if kind == "crossReference" and not node.get("resolved") and not node.get("remote"):
                errors.append(
                    f"{where}: cross-reference to '{node.get('label') or node.get('identifier')}' "
                    "does not resolve"
                )
                continue
            if kind == "link" and str(node.get("url") or "").startswith("#"):
                errors.append(
                    f"{where}: cross-reference to '{str(node['url'])[1:]}' does not resolve"
                )
                continue
            label = node.get("label")
            if kind in REFERENCE_TYPES or not isinstance(label, str) or not label:
                continue
            if node.get("implicit"):
                continue  # a heading's automatic anchor, not a label anyone wrote

            if label in seen:
                errors.append(
                    f"{relative}: duplicate label '{label}', already in {seen[label]}; "
                    "one anchor, one place"
                )
                continue
            seen[label] = relative
            anchor = html_id(label)
            if anchor in anchors:
                errors.append(
                    f"{relative}: label '{label}' and label '{anchors[anchor]}' share the "
                    f"HTML anchor '#{anchor}'; rename one"
                )
            else:
                anchors[anchor] = label

            if relative.startswith(f"{MODULES}/"):
                claim = kind == "proof" and node.get("kind") in KIND
                labels[label] = {"kind": node.get("kind") if claim else None,
                                 "file": relative}
    return labels


def manuscript_labels(root: Path, errors: list[str]) -> dict[str, dict]:
    """Build the manuscript and read its labels; a tree with no ``myst.yml`` has none."""
    if not (root / CONFIG).is_file():
        return {}
    content = build(root, errors)
    if content is None:
        return {}
    return read(content, errors)

