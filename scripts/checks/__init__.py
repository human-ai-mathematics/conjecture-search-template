"""Structural validation of one repository tree.

Absent files contribute nothing: a repository with no portfolio has no portfolio rules
to obey, so a fresh clone of the template passes.
"""
from __future__ import annotations

from pathlib import Path

from . import ledger, manuscript, proofs, search
from .common import (as_list, contained_path, read_front_matter, repo_relative,
                     text_digest)

ROOT = Path(__file__).resolve().parents[2]


def analyze(root: Path | None = None, labels: dict[str, dict] | None = None, *,
            fast: bool = False) -> dict:
    """Validate ``root`` and return ``{"errors", "nodes", "drafts", "target",
    "approaches", "candidates", "mentions", "latest", "fast", "impact"}``.

    ``drafts`` are the dossiers no proof record names; they are left out of the published
    site. ``impact`` groups fingerprint mismatches by changed dossier or statement,
    recording affected nodes, dossiers, certification sources, the fingerprint each source
    recorded and their validation errors.
    Missing fingerprints remain ordinary errors, not claims that a version changed.

    ``fast`` skips the manuscript: no MyST build, so the anchors and the statement
    fingerprints go unchecked. ``labels`` is the manuscript as
    :func:`manuscript.manuscript_labels` returns it; the unit tests pass it in so that each
    small fixture tree need not run a MyST build.
    """
    root = Path(root) if root is not None else ROOT
    errors: list[str] = []
    if labels is None and not fast:
        labels = manuscript.manuscript_labels(root, errors)
    nodes = ledger.check(root, labels, errors)
    impact: dict[str, list[dict]] = {}
    drafts = proofs.check(root, nodes, labels, errors, impact)
    state = search.check(root, nodes, errors)
    return {"errors": errors, "nodes": nodes, "drafts": drafts, "fast": labels is None,
            "impact": impact, **state}


def fingerprint(root: Path | None, dossiers: list[str]) -> tuple[dict[str, str], list[str]]:
    """The ``fingerprints`` a certification of ``dossiers`` records: each dossier's
    fingerprint (``common.text_digest``) and the fingerprint of every statement its proof
    is checked against. Returns the mapping and the reasons it is incomplete; manuscript
    errors elsewhere do not count."""
    root = Path(root) if root is not None else ROOT
    errors: list[str] = []
    labels = manuscript.manuscript_labels(root, errors)
    if labels:
        errors = []  # the manuscript was read; its other defects are check.py's business
    nodes = ledger.load(root, errors)
    result: dict[str, str] = {}
    for reference in dossiers:
        path = contained_path(root, reference, proofs.SOLUTIONS, reference, errors,
                              suffix=".md")
        header = read_front_matter(path, "dossier", errors) if path is not None else None
        if header is None:
            continue
        result[repo_relative(root, path)] = text_digest(path.read_text(encoding="utf-8"))
        for nid in as_list(header.get("ledger-node")):
            if not isinstance(nid, str) or nid not in nodes:
                errors.append(f"{reference}: ledger-node '{nid}' is not a ledger node")
                continue
            for ref in proofs.relied_on(nid, nodes):
                digest = labels.get(ref, {}).get("fingerprint")
                if digest is None:
                    errors.append(f"'{ref}' has no claim in modules/ to fingerprint")
                else:
                    result[ref] = digest
    return result, errors


def statements(root: Path | None) -> tuple[dict[str, str], list[str]]:
    """Every statement of the manuscript and its fingerprint, sorted by label: what a
    writer's pass must leave unchanged. Returns the mapping and why the manuscript could
    not be read; its other defects are check.py's business."""
    root = Path(root) if root is not None else ROOT
    errors: list[str] = []
    labels = manuscript.manuscript_labels(root, errors)
    digests = {label: labels[label]["fingerprint"] for label in sorted(labels)
               if "fingerprint" in labels[label]}
    return digests, [] if labels else errors
