"""Certification: proof records, dossiers under ``solutions/``, reviews, refutations.

A proof record is a dossier plus exactly one of ``review`` (an agent's independent review)
or ``accepted_by`` (a human's attestation). The review is checked hardest: it must exist
under ``research/reviews/``, pass, and name a reviewer who is not an author.

Either way, a certification holds only for the versions it saw. Its ``fingerprints`` map
the dossier's path to its SHA-256, and each statement the proof is checked against — the
node's own, those it depends on or assumes, the target it refutes — to the fingerprint
``manuscript.py`` computes. A dossier or a statement edited since is no longer certified.
A fast check reads no manuscript, so it compares only the dossiers.
"""
from __future__ import annotations

import re
from pathlib import Path

from .common import (as_list, contained_path, markdown_records, one_of,
                     read_front_matter, repo_relative, sha256, string_list)

REVIEWS = "research/reviews"
SOLUTIONS = "solutions"

PROOF_FIELDS = {"artifact", "review", "accepted_by", "fingerprints"}
REVIEW_VERDICTS = {"pass", "revise"}
REVIEW_FIELDS = {"verdict", "authors", "reviewer", "fingerprints"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def relied_on(nid: str, nodes: dict[str, dict]) -> list[str]:
    """The statements a proof of ``nid`` is checked against, and so fingerprints: its own,
    its ``depends_on`` and ``assumes``, and every target that names it in ``refuted_by``."""
    ids = [nid, *as_list(nodes[nid].get("depends_on")), *as_list(nodes[nid].get("assumes"))]
    ids += [other for other, node in nodes.items() if nid in as_list(node.get("refuted_by"))]
    return list(dict.fromkeys(ref for ref in ids if isinstance(ref, str) and ref in nodes))


def fingerprints(raw: object, nodes: dict[str, dict], context: str,
                 errors: list[str]) -> dict[str, str]:
    """A validated ``fingerprints`` mapping: dossier paths and node ids to SHA-256s."""
    if not isinstance(raw, dict) or not raw:
        errors.append(f"{context}: want a mapping of 'solutions/<file>.md' and node ids "
                      "to SHA-256s")
        return {}
    result: dict[str, str] = {}
    for key, digest in raw.items():
        if not isinstance(key, str) or not (key.startswith(f"{SOLUTIONS}/") or key in nodes):
            errors.append(f"{context}: '{key}' is neither a dossier under {SOLUTIONS}/ "
                          "nor a ledger node")
        elif not isinstance(digest, str) or not SHA256_RE.match(digest):
            errors.append(f"{context}: '{key}' needs a lowercase hex SHA-256")
        else:
            result[key] = digest
    return result


def read_reviews(root: Path, nodes: dict[str, dict], errors: list[str]) -> dict[str, dict]:
    """Every review's validated front matter, keyed by repo-relative path."""
    reviews: dict[str, dict] = {}
    for path in markdown_records(root, REVIEWS, errors):
        raw = read_front_matter(path, "review", errors)
        if raw is None:
            continue
        context = str(path)
        for field in sorted(set(raw) - REVIEW_FIELDS):
            errors.append(f"{context}: unknown field '{field}'")
        if not one_of(raw.get("verdict"), REVIEW_VERDICTS):
            errors.append(f"{context}.verdict: want one of {sorted(REVIEW_VERDICTS)}")
        reviewer = raw.get("reviewer")
        authors = string_list(raw, "authors", context, errors, required=True)
        if not isinstance(reviewer, str) or not reviewer.strip():
            errors.append(f"{context}.reviewer: must be a non-empty string")
        elif reviewer in authors:
            errors.append(f"{context}.reviewer: must not be one of the authors")
        reviews[repo_relative(root, path)] = {
            "verdict": raw.get("verdict"),
            "fingerprints": fingerprints(raw.get("fingerprints"), nodes,
                                         f"{context}.fingerprints", errors),
        }
    return reviews


def _dossier(root: Path, nid: str, reference: object, context: str,
             errors: list[str]) -> Path | None:
    path = contained_path(root, reference, SOLUTIONS, f"{context}.artifact", errors,
                          suffix=".md")
    if path is None:
        return None
    header = read_front_matter(path, "dossier", errors)
    if header is not None and nid not in as_list(header.get("ledger-node")):
        errors.append(f"{path}: front matter 'ledger-node' must name '{nid}'")
    return path


def _current(root: Path, nid: str, artifact: object, dossier: Path | None,
             recorded: dict[str, str], source: str, redo: str, nodes: dict[str, dict],
             labels: dict[str, dict] | None, context: str, errors: list[str]) -> None:
    """Report every version ``source`` did not see: an unrecorded or edited dossier or
    statement. ``redo`` names what restores the certification."""
    if dossier is not None:
        digest = recorded.get(artifact)
        if digest is None:
            errors.append(f"{context}: {source} does not fingerprint '{artifact}'")
        elif sha256(dossier) != digest:
            errors.append(f"{context}: {artifact} changed since {source} fingerprinted it; "
                          f"it needs {redo}")
    for ref in relied_on(nid, nodes):
        digest = recorded.get(ref)
        current = (labels or {}).get(ref, {}).get("fingerprint")
        if digest is None:
            errors.append(f"{context}: {source} does not fingerprint the statement of '{ref}'")
        elif current is not None and current != digest:
            errors.append(f"{context}: the statement of '{ref}' changed since {source} "
                          f"fingerprinted it; it needs {redo}")


def _proof(root: Path, nid: str, proof: object, context: str, reviews: dict[str, dict],
           nodes: dict[str, dict], labels: dict[str, dict] | None,
           errors: list[str]) -> str | None:
    """Validate one proof record; return its dossier's repo-relative path."""
    if not isinstance(proof, dict):
        errors.append(f"{context}: must be a mapping")
        return None
    for field in sorted(set(proof) - PROOF_FIELDS):
        errors.append(f"{context}: unknown field '{field}'")
    artifact = proof.get("artifact")
    dossier = _dossier(root, nid, artifact, context, errors)
    named = repo_relative(root, dossier) if dossier is not None else None
    review, accepted_by = proof.get("review"), proof.get("accepted_by")
    if (review is None) == (accepted_by is None):
        errors.append(f"{context}: needs exactly one of review (agent) or accepted_by (human)")
        return named
    if accepted_by is not None:
        if not isinstance(accepted_by, str) or not accepted_by.strip():
            errors.append(f"{context}.accepted_by: must name who accepted the proof")
            return named
        recorded = fingerprints(proof.get("fingerprints"), nodes,
                                f"{context}.fingerprints", errors)
        if recorded:
            _current(root, nid, artifact, dossier, recorded, f"the acceptance by {accepted_by}",
                     "a new acceptance", nodes, labels, context, errors)
        return named
    if "fingerprints" in proof:
        errors.append(f"{context}.fingerprints: a reviewed proof's fingerprints are its "
                      "review's")
    path = contained_path(root, review, REVIEWS, f"{context}.review", errors, suffix=".md")
    if path is None:
        return named
    report = reviews.get(repo_relative(root, path))
    if report is None:
        return named  # its front matter is already reported as broken
    if report["verdict"] != "pass":
        errors.append(f"{context}.review: verdict '{report['verdict']}' cannot certify a proof")
    if report["fingerprints"]:
        _current(root, nid, artifact, dossier, report["fingerprints"], review,
                 "a new review", nodes, labels, context, errors)
    return named


def check(root: Path, nodes: dict[str, dict], labels: dict[str, dict] | None,
          errors: list[str]) -> list[str]:
    """Validate certification; return the draft dossiers, those no proof record names."""
    reviews = read_reviews(root, nodes, errors)
    named: set[str] = set()
    for nid, node in nodes.items():
        status, proofs = node.get("status"), node.get("proofs")
        if status == "proved" and "references" not in node and not proofs:
            errors.append(f"{nid}: a proved node without references needs a proof record")
        if proofs is not None and status != "proved":
            errors.append(f"{nid}.proofs: only for status proved")
        for index, proof in enumerate(as_list(proofs)):
            dossier = _proof(root, nid, proof, f"{nid}.proofs[{index}]", reviews, nodes,
                             labels, errors)
            if dossier is not None:
                named.add(dossier)

        refuters = as_list(node.get("refuted_by"))
        if status == "refuted" and not refuters:
            errors.append(f"{nid}: a refuted node needs refuted_by")
        if refuters and status != "refuted":
            errors.append(f"{nid}.refuted_by: only for status refuted")
        for ref in refuters:
            if isinstance(ref, str) and ref in nodes and nodes[ref].get("status") != "proved":
                errors.append(f"{nid}.refuted_by: '{ref}' is not proved")
    return [path for path in dossiers(root) if path not in named]


def dossiers(root: Path) -> list[str]:
    """Every dossier under ``solutions/``, repo-relative."""
    solutions = root / SOLUTIONS
    return sorted(repo_relative(root, path) for path in solutions.glob("*.md")) \
        if solutions.is_dir() else []
