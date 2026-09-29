"""The claim graph: node schema, the acyclic proof DAG, literature references, anchors.

A node's id is its manuscript anchor: ``manuscript.py`` reads every ``:label:`` in
``modules/`` from MyST, and each claim label and each node must answer for the other.
A fast check reads no manuscript and leaves that correspondence unchecked.
The statement, its kind and its file are the manuscript's; the ledger holds only status
and edges. Proof certification is ``proofs.py``'s business, search state ``search.py``'s.
"""
from __future__ import annotations

import re
from pathlib import Path

from .common import as_list, load_yaml, one_of

LEDGER_PATH = Path("research/program/ledger.yaml")
BIBLIOGRAPHY = Path("references.bib")

STATUSES = {"open", "proved", "defined", "refuted"}
UNRESOLVED = {"open", "refuted"}

REFERENCE_FIELDS = ("depends_on", "assumes", "bounded_by", "refuted_by")
LIST_FIELDS = {*REFERENCE_FIELDS, "references", "proofs"}
NODE_FIELDS = {"id", "status", *LIST_FIELDS}

BIB_ENTRY_RE = re.compile(r"@[A-Za-z]+\s*\{\s*([^,\s]+)\s*,")
BIB_COMMENT_RE = re.compile(r"(?<!\\)%.*$", re.MULTILINE)


def bibliography_keys(root: Path) -> set[str] | None:
    try:
        text = (root / BIBLIOGRAPHY).read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    return set(BIB_ENTRY_RE.findall(BIB_COMMENT_RE.sub("", text)))


def load(root: Path, errors: list[str]) -> dict[str, dict]:
    """The ledger's nodes by id; an absent ledger is an error, an empty one is not."""
    path = root / LEDGER_PATH
    if not path.is_file():
        errors.append(f"{LEDGER_PATH}: missing")
        return {}
    doc = load_yaml(path, LEDGER_PATH, errors)
    if doc is None:
        return {}
    for field in sorted(set(doc) - {"nodes"}):
        errors.append(f"{LEDGER_PATH}: unknown top-level field '{field}'")
    raw = doc.get("nodes") or []
    if not isinstance(raw, list):
        errors.append(f"{LEDGER_PATH}: 'nodes' must be a list")
        return {}
    nodes: dict[str, dict] = {}
    for index, node in enumerate(raw):
        nid = node.get("id") if isinstance(node, dict) else None
        if not isinstance(nid, str) or not nid.strip():
            errors.append(f"{LEDGER_PATH}: node #{index + 1} needs a mapping with a string 'id'")
        elif nid in nodes:
            errors.append(f"{LEDGER_PATH}: duplicate node id '{nid}'")
        else:
            nodes[nid] = node
    return nodes


def unresolved_premises(start: str, nodes: dict[str, dict]) -> dict[str, list[str]]:
    """Every open or refuted node reachable from ``start`` through ``depends_on``,
    with the shortest path that reaches it."""
    found: dict[str, list[str]] = {}
    frontier = [[start]]
    seen = {start}
    while frontier:
        path = frontier.pop(0)
        for dep in as_list(nodes[path[-1]].get("depends_on")):
            if not isinstance(dep, str) or dep not in nodes or dep in seen:
                continue
            seen.add(dep)
            if one_of(nodes[dep].get("status"), UNRESOLVED):
                found[dep] = path + [dep]
            frontier.append(path + [dep])
    return found


def _cycles(nodes: dict[str, dict]) -> list[str]:
    errors: list[str] = []
    state: dict[str, int] = {}  # 1 = on the stack, 2 = done

    def visit(nid: str, stack: list[str]) -> None:
        state[nid] = 1
        for dep in as_list(nodes[nid].get("depends_on")):
            if not isinstance(dep, str) or dep not in nodes:
                continue
            if state.get(dep) == 1:
                errors.append(f"dependency cycle: {' -> '.join(stack + [nid, dep])}")
            elif dep not in state:
                visit(dep, stack + [nid])
        state[nid] = 2

    for nid in nodes:
        if nid not in state:
            visit(nid, [])
    return errors


def _node(nid: str, node: dict, nodes: dict[str, dict], labels: dict[str, dict] | None,
          bib_keys: set[str] | None, errors: list[str]) -> None:
    for field in sorted(set(node) - NODE_FIELDS):
        errors.append(f"{nid}: unknown field '{field}'")
    for field in sorted(LIST_FIELDS & set(node)):
        if not isinstance(node[field], list):
            errors.append(f"{nid}.{field}: must be a list")

    status = node.get("status")
    if "status" not in node:
        errors.append(f"{nid}: missing 'status'")
    elif not one_of(status, STATUSES):
        errors.append(f"{nid}: bad status '{status}' (want one of {sorted(STATUSES)})")

    anchor = labels.get(nid) if labels is not None else None
    if labels is not None and anchor is None:
        errors.append(f"{nid}: no manuscript label '{nid}' in modules/; the node id is the anchor")
    elif anchor is not None and anchor["kind"] is None:
        errors.append(f"{nid}: labels a structural element in {anchor['file']}, not a claim")
    elif anchor is not None and (anchor["kind"] == "definition") != (status == "defined"):
        errors.append(f"{nid}: status defined is for, and only for, a prf:definition")

    if "references" in node:
        references = node["references"]
        if not isinstance(references, list) or not references:
            errors.append(f"{nid}.references: must be a non-empty list of BibTeX keys")
        elif bib_keys is None:
            errors.append(f"{nid}.references: {BIBLIOGRAPHY} is missing")
        else:
            for key in references:
                if not isinstance(key, str):
                    errors.append(f"{nid}.references: '{key}' is not a BibTeX key")
                elif key not in bib_keys:
                    errors.append(f"{nid}.references: unknown BibTeX key '{key}'")

    for field in REFERENCE_FIELDS:
        for ref in as_list(node.get(field)):
            if not isinstance(ref, str) or ref not in nodes:
                errors.append(f"{nid}.{field}: '{ref}' is not a node in the ledger")

    if status == "proved":
        for target, path in sorted(unresolved_premises(nid, nodes).items()):
            errors.append(f"{nid} (proved) depends on {nodes[target].get('status')} "
                          f"'{target}' via {' -> '.join(path)}")


def check(root: Path, labels: dict[str, dict] | None,
          errors: list[str]) -> dict[str, dict]:
    """Validate the ledger; ``labels`` is ``None`` when the manuscript was not read."""
    nodes = load(root, errors)
    bib_keys = bibliography_keys(root)
    for nid, node in nodes.items():
        _node(nid, node, nodes, labels, bib_keys, errors)
    errors.extend(_cycles(nodes))
    for label, entry in sorted((labels or {}).items()):
        if entry["kind"] is not None and label not in nodes:
            errors.append(f"{entry['file']}: prf:{entry['kind']} '{label}' has no ledger node")
    return nodes
