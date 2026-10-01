"""The manuscript as MyST parses it: every labelled target, and what MyST could not resolve.

This module runs ``myst build --site`` and reads the tree MyST writes under
``_build/site/content/``. A claim is a ``proof`` node whose ``kind`` is one of ``KIND``
(``prf:theorem``, ``prf:conjecture``, …) carrying a ``label``; every other label is
structural. Every MyST error is an error here, and so are three things MyST only warns
about, because each silently breaks the node/label correspondence: an unknown directive
or role, an unresolved cross-reference, and a duplicate label.

Each claim also gets a *fingerprint*: the SHA-256 of its statement as MyST parsed it, blind
to what does not change the mathematics — line wrapping, source positions, numbering, the
title, the text a cross-reference or a link to a label renders to and the page its target
lives on, a proof nested in the claim, the status ``scripts/status.mjs`` displays from the
ledger. A
certification records the fingerprints of the statements it checked, so an edited
statement is detected.
"""
from __future__ import annotations

import contextlib
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows: builds are not serialized
    fcntl = None

#: The directives that make a labelled statement a claim, and so a ledger node.
KIND = {
    "theorem", "lemma", "proposition", "corollary", "conjecture", "definition",
    "example", "assumption",
}

#: The checker's own repository. Its ``node_modules`` holds the pinned MyST, and a
#: tree validated with ``--root`` — ``example/``, a test fixture — uses that one too.
REPO = Path(__file__).resolve().parents[2]

CONFIG = "myst.yml"
CONTENT = Path("_build/site/content")
#: Held for a whole build-and-read, so concurrent checks of one tree never read a half-built
#: or deleted content directory.
LOCK = Path("_build/.check.lock")
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


#: The node fields that carry the mathematics; everything else is layout or rendering.
STATEMENT_FIELDS = ("type", "kind", "name", "value", "identifier", "url", "lang")
#: Nodes that point elsewhere: their identifier matters, their rendered text and the page
#: their target lives on do not, so moving a statement to another module changes nothing.
POINTERS = frozenset({"crossReference", "cite", "footnoteReference"})
WHITESPACE = re.compile(r"\s+")


def _pointer(node: dict) -> bool:
    """A reference to a label. MyST resolves ``[](#sec:x)`` to a heading on another page
    as a ``link`` carrying the label and the heading's text: it is a pointer too, so
    renaming the heading changes nothing. A link to a URL keeps its text and its URL."""
    kind = node.get("type")
    return kind in POINTERS or (kind == "link" and bool(node.get("identifier")))


def _statement(node: dict) -> dict:
    pointer = _pointer(node)
    kept: dict = {}
    for field in STATEMENT_FIELDS:
        if field == "url" and pointer:
            continue
        value = node.get(field)
        if isinstance(value, str):
            kept[field] = WHITESPACE.sub(" ", value).strip()
    if not pointer:
        kept["children"] = [
            _statement(child) for child in node.get("children") or []
            if isinstance(child, dict)
            and not (child.get("type") == "proof" and child.get("kind") == "proof")
            and not child.get("claimStatus")
        ]
    return kept


def fingerprint(claim: dict, title: bool = False) -> str:
    """The SHA-256 of a claim's statement: its kind and its content, not its label nor its
    title. With ``title``, the fingerprint recorded before 0.5.0, which included it."""
    children = _statement(claim)["children"]
    if not title:
        children = [child for child in children if child.get("type") != "admonitionTitle"]
    canonical = {"kind": claim.get("kind"), "children": children}
    text = json.dumps(canonical, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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

    Returns ``{label: {"kind": <claim kind or None>, "file": "modules/…md"}}``: ``kind``
    is set only for a claim, and ``None`` marks a structural label; a claim also carries
    its ``fingerprint``. Targets outside ``modules/`` — a theorem restated in a dossier,
    the index page — are not manuscript anchors and are left out, but they still take
    part in the duplicate check, because MyST resolves labels across the whole project.
    """
    labels: dict[str, dict] = {}
    seen: dict[str, str] = {}
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

            if relative.startswith(f"{MODULES}/"):
                claim = kind == "proof" and node.get("kind") in KIND
                labels[label] = {"kind": node.get("kind") if claim else None,
                                 "file": relative}
                if claim:
                    labels[label]["fingerprint"] = fingerprint(node)
                    titled = fingerprint(node, title=True)
                    if titled != labels[label]["fingerprint"]:
                        labels[label]["titled"] = titled
    return labels


def manuscript_labels(root: Path, errors: list[str]) -> dict[str, dict]:
    """Build the manuscript and read its labels; a tree with no ``myst.yml`` has none."""
    if not (root / CONFIG).is_file():
        return {}
    with _locked(root):
        content = build(root, errors)
        return {} if content is None else read(content, errors)


@contextlib.contextmanager
def _locked(root: Path):
    """Serialize builds of one tree: each deletes and rewrites the directory it reads."""
    if fcntl is None:
        yield
        return
    path = root / LOCK
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)

