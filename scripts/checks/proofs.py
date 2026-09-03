"""The proofs lane: dossiers, certification modes, and persisted review provenance.

A proved internal node points at one or more standalone dossiers under ``solutions/``,
each with an explicit certification mode. Agent certification is the only mode that
delegates trust to another agent, so it is the one this lane checks hardest: the
review report must exist, be typed ``proof-review``, name a reviewer distinct from every
author, and declare the node and dossier in its immutable historical scope.
"""
from __future__ import annotations

import re
from pathlib import Path

from .common import (as_list, check_record_date, contained_path, mentions_token,
                     optional_string_list, read_front_matter, repo_relative,
                     required_string_set)

REVIEWS = "research/reviews"
SOLUTIONS = "solutions"

PROOF_MODES = {"agent", "human"}
PROOF_FIELDS = {"artifact", "mode", "review", "accepted_by"}

#: Modes that once existed and no longer do, with the reason. Rejected by name so a
#: ledger carrying one gets an explanation rather than a bare vocabulary error.
RETIRED_PROOF_MODES = {
    "lean": "not implemented — the checker only looked for an adjacent .lean file and "
            "never ran the kernel, so a mode that certifies nothing could support "
            "status: proved. Restore it when check.py invokes Lean with pinned tooling",
}

#: The dossier's header, parsed rather than grepped. Exactly one field is validated:
#: `ledger-node`, the ids the dossier discharges. Nothing else in the header has a single
#: owner — the ledger's proofs[] record owns the mode and the review path, and the
#: review's own front matter owns author and reviewer identity.
HEADER_LIMIT = 2500
HEADER_GLOSS_RE = re.compile(r"\s{2,}")

#: Header fields that once existed and no longer do, with what owns them now. Rejected by
#: name, so an inherited dossier gets an explanation rather than silence.
#:
#: `checked_by` duplicated `proofs[].mode` with nothing to reconcile the two: the checker
#: validated its vocabulary and never compared it to the ledger, so a dossier could read
#: `checked_by: none` under a `mode: agent` record with a passing review and nothing went
#: red. Certification now has one home. A dossier that no proofs[] record names is a
#: draft, and that absence is what says so.
RETIRED_HEADER_FIELDS = {
    "checked_by": "proofs[].mode in research/program/ledger.yaml, which owns "
                  "certification; a dossier no proofs[] record names is a draft",
    "reviewer": "the review's own front matter",
    "review": "proofs[].review in research/program/ledger.yaml",
}

REVIEW_TYPES = {"proof-review", "audit"}
#: An audit certifies nothing, so it carries only what every dated record carries —
#: plus the generic supersession pointer that keeps the archive readable.
AUDIT_FIELDS = {"type", "date", "supersedes"}
PROOF_REVIEW_FIELDS = {
    "type", "date", "verdict", "authors", "reviewer", "nodes", "solutions", "follows_up",
}


def read_review_metadata(path: Path, root: Path, errors: list[str]) -> dict | None:
    """Parse and validate the YAML front matter of one persisted review report."""
    raw = read_front_matter(path, "review report", errors)
    if raw is None:
        return None

    report_type = raw.get("type")
    if report_type not in REVIEW_TYPES:
        errors.append(f"{path}.type: want one of {sorted(REVIEW_TYPES)}, got '{report_type}'")
        return None
    allowed = PROOF_REVIEW_FIELDS if report_type == "proof-review" else AUDIT_FIELDS
    for field in sorted(set(raw) - allowed):
        errors.append(f"{path}: field '{field}' is not valid for type {report_type}")

    normalized = {
        "type": report_type,
        "date": check_record_date(path, raw, errors),
        "path": path,
    }
    if report_type == "audit":
        normalized["supersedes"] = optional_string_list(raw, "supersedes", str(path), errors)
        return normalized

    verdict = raw.get("verdict")
    if verdict != "pass":
        errors.append(f"{path}.verdict: a proof-review must have the exact value 'pass'")
    reviewer = raw.get("reviewer")
    if not isinstance(reviewer, str) or not reviewer.strip():
        errors.append(f"{path}.reviewer: must be a non-empty string")
        reviewer = None
    authors = required_string_set(raw, "authors", str(path), errors)
    if isinstance(reviewer, str) and reviewer in authors:
        errors.append(f"{path}.reviewer: must be distinct from every proof author")
    normalized.update({
        "verdict": verdict,
        "authors": authors,
        "reviewer": reviewer,
        "nodes": required_string_set(raw, "nodes", str(path), errors),
        "solutions": required_string_set(raw, "solutions", str(path), errors),
    })

    follows_up = raw.get("follows_up")
    if follows_up is not None:
        context = f"{path}.follows_up"
        resolved = contained_path(root, follows_up, REVIEWS, context, errors,
                                  outside="must stay under research/reviews/")
        if resolved is not None and resolved == path.resolve():
            errors.append(f"{context}: a report cannot follow up itself")
        normalized["follows_up"] = follows_up
    return normalized


def read_archive(root: Path, errors: list[str]) -> dict[str, dict]:
    """Validate every report envelope in the review archive, keyed by repo-relative path."""
    reviews_root = (root / REVIEWS).resolve()
    metadata_by_ref: dict[str, dict] = {}
    if not reviews_root.is_dir():
        return metadata_by_ref
    for path in sorted(reviews_root.rglob("*.md")):
        if path.name == "README.md":
            continue
        metadata = read_review_metadata(path, root, errors)
        if metadata is not None:
            metadata_by_ref[repo_relative(root, path)] = metadata
    return metadata_by_ref


def parse_dossier_header(text: str) -> dict[str, str]:
    """Read the ``%   field : value`` lines of a dossier's audit header.

    Only the leading ``HEADER_LIMIT`` characters are considered, and only comment lines
    of that exact shape. The value ends at the first run of two or more spaces, which is
    what separates it from the inline gloss the template writes beside it. Returns the
    fields it found; an absent field is simply missing, which the caller reports in its
    own words.
    """
    fields: dict[str, str] = {}
    for line in text[:HEADER_LIMIT].splitlines():
        stripped = line.strip()
        if not stripped.startswith("%") or ":" not in stripped:
            continue
        name, _, value = stripped.lstrip("% ").partition(":")
        name = name.strip()
        if name and name not in fields:
            fields[name] = HEADER_GLOSS_RE.split(value.strip(), maxsplit=1)[0].strip()
    return fields


def _dossier(root: Path, program: str, nid: str, reference: object,
             errors: list[str]) -> Path | None:
    """Validate and return one natural-language proof dossier path.

    The header is parsed, not searched. Grepping the first 2500 characters for the word
    ``ledger-node`` and, separately, for the node id let the two sit a page apart and
    still pass; a dossier that does not *say* which node it discharges is not a dossier
    an independent reviewer can pick up.
    """
    context = f"[{program}] {nid}.proofs[].artifact"
    artifact = contained_path(root, reference, SOLUTIONS, context, errors,
                              suffix=".tex", outside="must stay under solutions/")
    if artifact is None:
        return None
    try:
        text = artifact.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errors.append(f"{context}: cannot read '{reference}': {exc}")
        return None

    header = parse_dossier_header(text)
    declared = header.get("ledger-node", header.get("ledger-nodes"))
    if declared is None:
        errors.append(
            f"{context}: dossier header has no 'ledger-node' field naming what it proves"
        )
    elif not mentions_token(declared, nid):
        errors.append(
            f"{context}: dossier header declares ledger-node '{declared}', not '{nid}'"
        )

    for field in sorted(set(header) & set(RETIRED_HEADER_FIELDS)):
        errors.append(
            f"{context}: dossier header field '{field}' is retired — use "
            f"{RETIRED_HEADER_FIELDS[field]}"
        )
    return artifact


def _certification(root: Path, program: str, nid: str, node: dict, nodes: dict[str, dict],
                   agent_review_refs: dict[str, list[tuple[str, str, str]]],
                   errors: list[str]) -> None:
    """Validate plural proof records and refutation provenance for one node."""
    status = node.get("status")
    provenance = node.get("provenance")
    raw_proofs = node.get("proofs")
    if status == "proved" and provenance == "internal" and not raw_proofs:
        errors.append(f"[{program}] {nid}: internally proved node requires a certified proof")
    if status != "proved" and raw_proofs is not None:
        errors.append(f"[{program}] {nid}.proofs: valid only with status proved")

    if raw_proofs is not None:
        if not isinstance(raw_proofs, list) or not raw_proofs:
            errors.append(f"[{program}] {nid}.proofs: must be a non-empty list")
            raw_proofs = []
        seen_artifacts: set[str] = set()
        for index, proof in enumerate(raw_proofs):
            context = f"[{program}] {nid}.proofs[{index}]"
            if not isinstance(proof, dict):
                errors.append(f"{context}: must be a mapping")
                continue
            for field in sorted(set(proof) - PROOF_FIELDS):
                errors.append(f"{context}: unknown field '{field}'")
            artifact_ref = proof.get("artifact")
            artifact = _dossier(root, program, nid, artifact_ref, errors)
            if isinstance(artifact_ref, str):
                if artifact_ref in seen_artifacts:
                    errors.append(f"{context}.artifact: duplicate active proof '{artifact_ref}'")
                seen_artifacts.add(artifact_ref)
            mode = proof.get("mode")
            if isinstance(mode, str) and mode in RETIRED_PROOF_MODES:
                errors.append(f"{context}.mode: '{mode}' is retired — "
                              f"{RETIRED_PROOF_MODES[mode]}")
                continue
            if mode not in PROOF_MODES:
                errors.append(f"{context}.mode: want one of {sorted(PROOF_MODES)}, got '{mode}'")
                continue

            review = proof.get("review")
            accepted_by = proof.get("accepted_by")
            if mode == "agent":
                if not isinstance(review, str) or not review.strip():
                    errors.append(f"{context}.review: mode agent requires a proof-review")
                elif isinstance(artifact_ref, str):
                    agent_review_refs.setdefault(review, []).append((program, nid, artifact_ref))
                if accepted_by is not None:
                    errors.append(f"{context}.accepted_by: valid only with mode human")
            elif mode == "human":
                if not isinstance(accepted_by, str) or not accepted_by.strip():
                    errors.append(
                        f"{context}.accepted_by: mode human requires a non-empty identity"
                    )
                if review is not None:
                    errors.append(f"{context}.review: valid only with mode agent")

    refuters = as_list(node.get("refuted_by"))
    if status == "refuted":
        if not refuters:
            errors.append(f"[{program}] {nid}: refuted node requires refuted_by")
        # Deliberately no depends_on requirement. `depends_on` is the acyclic graph of
        # facts a proof uses, and a refuted node has no proof; recording its refuter
        # there described a proof that does not exist. `refuted_by` naming a proved
        # refuter is the whole of the provenance (CLAUDE.md constraint 11).
        for ref in refuters:
            if isinstance(ref, str) and ref in nodes:
                if nodes[ref].get("status") != "proved":
                    errors.append(f"[{program}] {nid}.refuted_by: '{ref}' is not proved")
    elif "refuted_by" in node:
        errors.append(f"[{program}] {nid}.refuted_by: valid only with status refuted")


def _containment(root: Path, archive: dict[str, dict],
                 review_refs: dict[str, list[tuple[str, str, str]]],
                 errors: list[str]) -> None:
    """Check that every active certification lies inside its report's declared scope.

    Reports are immutable historical events. Their declared scope may therefore be
    larger than the set of nodes that currently points to them, and an old passing
    report may remain in the archive after every covered node is downgraded.
    """
    for review_ref in sorted(review_refs):
        context = f"review '{review_ref}'"
        artifact = contained_path(
            root, review_ref, REVIEWS, context, errors, suffix=".md", must_exist=False,
            outside="agent review reports must be under research/reviews/",
        )
        if artifact is None:
            continue
        if not artifact.is_file():
            errors.append(f"{context}: report does not exist")
            continue
        metadata = archive.get(artifact.relative_to(root.resolve()).as_posix())
        if metadata is None:
            continue
        if metadata.get("type") != "proof-review":
            errors.append(f"{context}: type '{metadata.get('type')}' cannot certify a proof")
            continue
        for program, nid, artifact_ref in review_refs[review_ref]:
            if nid not in metadata["nodes"]:
                errors.append(
                    f"{context}.nodes: active [{program}] certification '{nid}' "
                    "is outside the report's declared historical scope"
                )
            if artifact_ref not in metadata["solutions"]:
                errors.append(
                    f"{context}.solutions: active [{program}] certification '{nid}' uses "
                    f"'{artifact_ref}', outside the report's declared historical scope"
                )


def check(root: Path, ledgers: list[dict], errors: list[str]) -> dict[str, dict]:
    """Validate proof records and the review archive; return the archive metadata."""
    archive = read_archive(root, errors)
    agent_review_refs: dict[str, list[tuple[str, str, str]]] = {}
    for ledger in ledgers:
        program, nodes = ledger["program"], ledger["nodes"]
        for nid, node in nodes.items():
            _certification(root, program, nid, node, nodes, agent_review_refs, errors)
    _containment(root, archive, agent_review_refs, errors)
    return archive
