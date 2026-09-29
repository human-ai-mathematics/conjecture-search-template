"""Structural validation of one repository tree.

Absent files contribute nothing: a repository with no portfolio has no portfolio rules
to obey, so a fresh clone of the template passes.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

from . import ledger, manuscript, proofs, search, site
from .common import as_list, contained_path, read_front_matter, repo_relative, sha256

ROOT = Path(__file__).resolve().parents[2]


def analyze(root: Path | None = None, labels: dict[str, dict] | None = None, *,
            fast: bool = False) -> dict:
    """Validate ``root`` and return ``{"errors", "warnings", "nodes", "drafts", "target",
    "approaches", "candidates", "proposed", "mentions", "latest", "pages", "unmentioned",
    "fast"}``.

    ``drafts`` are the dossiers no proof record names; they are left out of the published
    site. ``warnings`` are the stale and unfinished pages of the reader's site: they never
    fail a check, and
    ``check.py --site-strict`` turns them into errors. ``unmentioned`` lists the proved and
    refuted nodes no site page rests on, once there is a site: a reminder, not a warning.

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
    drafts = proofs.check(root, nodes, labels, errors)
    state = search.check(root, nodes, errors)
    warnings: list[str] = []
    certified = [path for path in proofs.dossiers(root) if path not in drafts]
    count, mentioned = site.check(root, site.current(nodes, labels, state["proposed"]),
                                  certified, errors, warnings)
    return {"errors": errors, "warnings": warnings, "nodes": nodes, "drafts": drafts,
            "pages": count, "unmentioned": site.unmentioned(nodes, mentioned) if count else [],
            "fast": labels is None, **state}


def fingerprint(root: Path | None, dossiers: list[str]) -> tuple[dict[str, str], list[str]]:
    """The ``fingerprints`` a certification of ``dossiers`` records: each dossier's SHA-256
    and the fingerprint of every statement its proof is checked against. Returns the
    mapping and the reasons it is incomplete; manuscript errors elsewhere do not count."""
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
        result[repo_relative(root, path)] = sha256(path)
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


def stamp(root: Path | None, pages: list[str], today: date | None = None) -> tuple[list[str], list[str]]:
    """Stamp ``pages`` of the reader's site against the research record as it stands, and
    rewrite the lists of the index pages among them: the pages written, and the reasons any
    was not. Defects elsewhere do not count."""
    root = Path(root) if root is not None else ROOT
    errors: list[str] = []
    labels = manuscript.manuscript_labels(root, errors)
    if errors and not labels:
        return [], errors  # no manuscript, so no fingerprint to record
    ignored: list[str] = []
    nodes = ledger.load(root, ignored)
    proposed, _ = search.read_checkpoints(root, nodes, ignored)
    drafts = proofs.check(root, nodes, labels, ignored)
    certified = [path for path in proofs.dossiers(root) if path not in drafts]
    errors = []
    written = site.stamp(root, pages, site.current(nodes, labels, proposed), certified,
                         today or date.today(), errors)
    return written, errors
