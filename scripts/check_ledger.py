#!/usr/bin/env python3
"""Integrity checker for the research/ control plane.

Validates the single configured production ledger (and discovers ledgers only in
isolated test fixtures):

* ledger and node identities are unique (a second ledger is rejected: one
  repository owns exactly one program ledger);
* proof-dependency edges resolve, are acyclic, and do not let a proved node
  inherit an open or refuted premise;
* assumptions of proved implications live in ``assumes`` rather than
  ``depends_on``, so the implication can be proved while its applicability is
  reported as blocked;
* nodes use an explicit, program-aware schema; their manuscript anchor exists in
  the declared file, and every literature-provenance node cites existing BibTeX keys;
* every ``bounded_by`` edge resolves to an established same-ledger obstruction,
  while unproved method barriers use ``heuristic_barriers``;
* every dated exploration declares front matter whose nodes, run artifacts and
  candidate statements resolve, so the attempt log stays queryable rather than
  becoming prose nothing reads.

Proof-plane ``proofs:`` records are confined to ``solutions/`` and may contain
multiple independently certified agent, human, or future Lean proofs. Agent
identity and historical scope live in a persisted
``type: proof-review`` report; human acceptance is named explicitly and Lean
certification currently requires an adjacent ``.lean`` file. Every internally
proved node carries certification, while every refuted node names a proved
refuter.

Run from the repo root:
``python3 scripts/check_ledger.py [check|status|node ID|candidates]``.
Exit 0 = clean, 1 = errors. Requires PyYAML.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required: pip install pyyaml")

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"

KIND = {
    "theorem", "lemma", "proposition", "corollary", "definition", "assumption",
    "question", "conjecture", "obstruction", "example",
}
PROOF_MODES = {"agent", "human", "lean"}
PROOF_FIELDS = {"artifact", "mode", "review", "accepted_by"}
IMPORT_CLASSES = {"published", "preprint-unreviewed", "preprint-reviewed"}
REVIEW_TYPES = {"proof-review", "audit"}
REVIEW_COMMON_FIELDS = {"type", "date"}
PROOF_REVIEW_FIELDS = REVIEW_COMMON_FIELDS | {
    "verdict", "authors", "reviewer", "nodes", "solutions", "follows_up",
}

# One logical-status vocabulary. Mathematical form belongs in ``kind``;
# speculative prose is not a ledger classification.
STATUSES = {"open", "proved", "defined", "refuted"}
PROVENANCE = {"internal", "literature"}

# Unresolved premises are discovered recursively through the canonical
# ``depends_on`` graph; an unreviewed preprint therefore has status ``open``.
UNRESOLVED_STATUSES = {"open", "refuted"}

# One repository, one program, one ledger (CLAUDE.md constraint 1). The program
# names itself in ``meta.program``; the path is fixed so no configuration file
# has to agree with it.
LEDGER_PATH = Path("research/program/ledger.yaml")

# The repository bibliography, resolved relative to the repository root.
BIBLIOGRAPHY = Path("references.bib")

# The append-only attempt log, and the run artifacts an attempt may cite.
EXPLORATIONS = Path("research/explorations")
RUNS = Path("research/runs")

EXPLORATION_FIELDS = {"type", "date", "nodes", "outcome", "artifacts", "candidates", "retires"}
EXPLORATION_REQUIRED = {"type", "date", "outcome"}

# What the attempt produced, for the next agent deciding whether to repeat it.
EXPLORATION_OUTCOMES = {"dead-end", "directional", "candidate", "proposed"}

# A candidate is a statement someone thought worth writing down and nothing more:
# no manuscript anchor, no node, no status (CLAUDE.md constraint 8). Its id is
# namespaced so it can never be mistaken for a ledger node id.
CANDIDATE_ID_RE = re.compile(r"^cand:[a-z0-9][a-z0-9-]*$")
CANDIDATE_FIELDS = {"id", "statement"}

RESOLVE_FIELDS = (
    "depends_on", "assumes", "implies", "refines", "refuted_by",
)

# ``route`` is accepted only when ``meta.route_policy`` declares a vocabulary.
# Frontier relations resolve inside the ledger but do not enter the proof DAG.
NODE_FIELDS = {
    "id", "kind", "status", "provenance", "file", "label", "statement",
    "depends_on", "assumes", "implies", "refines", "bounded_by",
    "heuristic_barriers", "references", "import_class", "proofs",
    "refuted_by", "route",
}
LIST_FIELDS = {
    "depends_on", "assumes", "implies", "refines", "bounded_by",
    "heuristic_barriers", "references", "proofs", "refuted_by",
}
OBSOLETE_NODE_FIELDS = {
    "assuming": "assumes for antecedents of an implication",
    "discharged_by": "depends_on on the result that performs the discharge",
    "evidence": "a dated exploration plus an immutable research/runs artifact",
    "evidence_eligible": "a dated exploration plus an immutable research/runs artifact",
    "evidence_run": "a dated exploration plus an immutable research/runs artifact",
    "evidence_target": "the numerics target implementation and a dated exploration",
    "entry_point": "route or target documentation for non-logical navigation",
    "target_doc": "route or target documentation for non-logical navigation",
    "mechanism": "bounded_by plus independent semantic review",
    "clearance": "the proof dossier/review discussion of bounded_by",
    "note": "the manuscript, route/target brief, or a dated exploration",
    "numerics": "the numerics implementation, instance registry, or a dated exploration",
    "solution": "proofs with one artifact/mode record per active proof",
    "checked_by": "proofs[].mode",
    "review": "proofs[].review",
    "accepted_by": "proofs[].accepted_by",
    "proof_file": "proofs[].artifact",
    "proof_provenance": "proofs with explicit certification records",
    "authored_by": "proof-review front matter",
    "reviewed_by": "proof-review front matter",
    "related": "one of assumes, implies, refines, or route prose",
    "bridges": "a precise same-ledger implication/refinement or prose for an external comparison",
    "unlocks": "depends_on on the consuming node, or prose for non-logical relationships",
}
BIB_ENTRY_RE = re.compile(r"@[A-Za-z]+\s*\{\s*([^,\s]+)\s*,")
TOP_LEVEL_FIELDS = {"meta", "nodes"}
META_FIELDS = {"program", "scope", "route_policy"}
OBSOLETE_META_FIELDS = {"legacy_r2_debt", "legacy_proved_without_solution"}


def as_list(value: Any) -> list:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _mentions_token(text: str, token: str) -> bool:
    """Match a complete repository id or agent name, not a longer prefix lookalike."""
    token_characters = r"A-Za-z0-9_./:\-"
    return re.search(
        rf"(?<![{token_characters}]){re.escape(token)}(?![{token_characters}])",
        text,
    ) is not None


def _review_string_set(metadata: dict, field: str, context: str,
                       errors: list[str]) -> set[str]:
    """Validate one required non-empty list of unique review-metadata strings."""
    value = metadata.get(field)
    if not isinstance(value, list) or not value:
        errors.append(f"{context}.{field}: must be a non-empty list")
        return set()
    result: set[str] = set()
    for item in value:
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{context}.{field}: entries must be non-empty strings")
            continue
        if item in result:
            errors.append(f"{context}.{field}: duplicate entry '{item}'")
        result.add(item)
    return result


def _read_front_matter(path: Path, noun: str, errors: list[str]) -> dict | None:
    """Parse the leading YAML front matter of a persisted Markdown record.

    Shared by the two record genres that carry machine-readable envelopes — review
    reports and dated explorations — so the envelope is parsed one way everywhere.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errors.append(f"{path}: cannot read {noun}: {exc}")
        return None
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        errors.append(f"{path}: {noun} must start with YAML front matter")
        return None
    try:
        closing = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration:
        errors.append(f"{path}: {noun} front matter lacks a closing '---'")
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


def _check_record_date(path: Path, raw: dict, errors: list[str]) -> str | None:
    """A quoted ISO date that agrees with the filename prefix, for a dated record."""
    value = raw.get("date")
    if not isinstance(value, str):
        errors.append(f"{path}.date: must be a quoted ISO date YYYY-MM-DD")
        return None
    try:
        date.fromisoformat(value)
    except ValueError:
        errors.append(f"{path}.date: invalid ISO date '{value}'")
    if not path.name.startswith(f"{value}-"):
        errors.append(f"{path}.date: must match the filename prefix")
    return value


def _read_review_metadata(path: Path, root: Path, errors: list[str]) -> dict | None:
    """Parse and validate the YAML front matter of one persisted review report."""
    raw = _read_front_matter(path, "review report", errors)
    if raw is None:
        return None

    report_type = raw.get("type")
    if report_type not in REVIEW_TYPES:
        errors.append(
            f"{path}.type: want one of {sorted(REVIEW_TYPES)}, got '{report_type}'"
        )
        return None
    allowed = PROOF_REVIEW_FIELDS if report_type == "proof-review" else REVIEW_COMMON_FIELDS
    for field in sorted(set(raw) - allowed):
        errors.append(f"{path}: field '{field}' is not valid for type {report_type}")

    report_date = _check_record_date(path, raw, errors)

    normalized = {"type": report_type, "date": report_date}
    if report_type == "audit":
        return normalized

    verdict = raw.get("verdict")
    if verdict != "pass":
        errors.append(f"{path}.verdict: a proof-review must have the exact value 'pass'")
    reviewer = raw.get("reviewer")
    if not isinstance(reviewer, str) or not reviewer.strip():
        errors.append(f"{path}.reviewer: must be a non-empty string")
        reviewer = None
    authors = _review_string_set(raw, "authors", str(path), errors)
    if isinstance(reviewer, str) and reviewer in authors:
        errors.append(f"{path}.reviewer: must be distinct from every proof author")
    normalized.update({
        "verdict": verdict,
        "authors": authors,
        "reviewer": reviewer,
        "nodes": _review_string_set(raw, "nodes", str(path), errors),
        "solutions": _review_string_set(raw, "solutions", str(path), errors),
    })

    follows_up = raw.get("follows_up")
    if follows_up is not None:
        context = f"{path}.follows_up"
        if not isinstance(follows_up, str) or not follows_up.strip():
            errors.append(f"{context}: must be a non-empty repo-relative path")
        else:
            follow_path = Path(follows_up)
            resolved = (root / follow_path).resolve()
            reviews_root = (root / "research/reviews").resolve()
            if follow_path.is_absolute():
                errors.append(f"{context}: want a repo-relative path, got '{follows_up}'")
            else:
                try:
                    resolved.relative_to(reviews_root)
                except ValueError:
                    errors.append(f"{context}: must stay under research/reviews/")
                else:
                    if not resolved.is_file():
                        errors.append(f"{context}: '{follows_up}' does not exist")
                    elif resolved == path.resolve():
                        errors.append(f"{context}: a report cannot follow up itself")
        normalized["follows_up"] = follows_up
    return normalized


def _validate_agent_reviews(root: Path, review_refs: dict[str, list[tuple[str, str, str]]],
                            errors: list[str]) -> None:
    """Validate review envelopes and containment of every active certification.

    Reports are immutable historical events. Their declared scope may therefore be
    larger than the set of nodes that currently points to them, and an old passing
    report may remain in the archive after every covered node is downgraded.
    """
    reviews_root = (root / "research/reviews").resolve()
    metadata_by_ref: dict[str, dict | None] = {}
    if reviews_root.is_dir():
        for path in sorted(reviews_root.rglob("*.md")):
            if path.name == "README.md":
                continue
            relative = path.resolve().relative_to(root.resolve()).as_posix()
            metadata_by_ref[relative] = _read_review_metadata(path, root, errors)

    for review_ref in sorted(review_refs):
        path = Path(review_ref)
        context = f"review '{review_ref}'"
        if path.is_absolute():
            errors.append(f"{context}: want a repo-relative path")
            continue
        artifact = (root / path).resolve()
        try:
            artifact.relative_to(reviews_root)
        except ValueError:
            errors.append(f"{context}: agent review reports must be under research/reviews/")
            continue
        if artifact.suffix != ".md":
            errors.append(f"{context}: agent review reports must be Markdown files")
            continue
        if not artifact.is_file():
            errors.append(f"{context}: report does not exist")
            continue

        normalized_ref = artifact.relative_to(root.resolve()).as_posix()
        metadata = metadata_by_ref.get(normalized_ref)
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


def _optional_string_list(raw: dict, field: str, context: str,
                          errors: list[str]) -> list[str]:
    """Validate one optional list of unique non-empty strings; absent means empty."""
    if field not in raw:
        return []
    value = raw[field]
    if not isinstance(value, list):
        errors.append(f"{context}.{field}: must be a list")
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


def _read_exploration_metadata(path: Path, errors: list[str]) -> dict | None:
    """Parse and validate the front matter of one dated exploration.

    The envelope exists so that the attempt log answers the question the next agent
    actually has — has this node been attacked, and what came back — without anyone
    reading every file. It records what the attempt engaged, not what it concluded:
    conclusions are prose, and a conclusion that earns reuse becomes a ledger node.
    """
    context = str(path)
    raw = _read_front_matter(path, "exploration", errors)
    if raw is None:
        return None
    if raw.get("type") != "exploration":
        errors.append(f"{context}.type: want 'exploration', got '{raw.get('type')}'")
        return None
    for field in sorted(set(raw) - EXPLORATION_FIELDS):
        errors.append(f"{context}: field '{field}' is not valid for an exploration")
    for field in sorted(EXPLORATION_REQUIRED - set(raw)):
        errors.append(f"{context}: required field '{field}' is missing")

    outcome = raw.get("outcome")
    if "outcome" in raw and outcome not in EXPLORATION_OUTCOMES:
        errors.append(
            f"{context}.outcome: want one of {sorted(EXPLORATION_OUTCOMES)}, got '{outcome}'"
        )

    metadata = {
        "path": path,
        "date": _check_record_date(path, raw, errors),
        "outcome": outcome,
        "nodes": _optional_string_list(raw, "nodes", context, errors),
        "artifacts": _optional_string_list(raw, "artifacts", context, errors),
        "retires": _optional_string_list(raw, "retires", context, errors),
        "candidates": [],
    }

    if "candidates" in raw:
        value = raw["candidates"]
        if not isinstance(value, list):
            errors.append(f"{context}.candidates: must be a list")
            value = []
        for index, entry in enumerate(value):
            where = f"{context}.candidates[{index}]"
            if not isinstance(entry, dict):
                errors.append(f"{where}: must be a mapping with 'id' and 'statement'")
                continue
            for field in sorted(set(entry) - CANDIDATE_FIELDS):
                errors.append(f"{where}: unknown field '{field}'")
            candidate_id = entry.get("id")
            statement = entry.get("statement")
            if not isinstance(candidate_id, str) or not CANDIDATE_ID_RE.match(candidate_id):
                errors.append(f"{where}.id: want 'cand:<slug>', got '{candidate_id}'")
                continue
            if not isinstance(statement, str) or not statement.strip():
                errors.append(f"{where}.statement: must be a non-empty string")
                continue
            metadata["candidates"].append({"id": candidate_id, "statement": statement})

    declared = [entry["id"] for entry in metadata["candidates"]]
    if bool(declared) != (outcome == "candidate"):
        errors.append(
            f"{context}: outcome 'candidate' and a non-empty 'candidates' list require "
            "each other; every other outcome carries none"
        )
    if not metadata["nodes"] and not declared:
        errors.append(
            f"{context}: must name at least one ledger node in 'nodes' or propose a candidate"
        )
    return metadata


def _validate_explorations(root: Path, node_ids: set[str], errors: list[str]) -> list[dict]:
    """Validate every dated exploration and return the live candidate statements.

    A candidate is retired by a later exploration naming it in ``retires``; the log
    itself is never rewritten (CLAUDE.md constraint 7), so "live" is derived here
    rather than recorded anywhere.
    """
    directory = root / EXPLORATIONS
    if not directory.is_dir():
        return []
    runs_root = (root / RUNS).resolve()
    declared: dict[str, dict] = {}
    retired: dict[str, tuple[int, str]] = {}

    for order, path in enumerate(sorted(directory.rglob("*.md"))):
        if path.name == "README.md":
            continue
        metadata = _read_exploration_metadata(path, errors)
        if metadata is None:
            continue
        context = str(path)
        relative = path.resolve().relative_to(root.resolve()).as_posix()

        for node_id in metadata["nodes"]:
            if node_id not in node_ids:
                errors.append(f"{context}.nodes: '{node_id}' is not a ledger node id")

        for reference in metadata["artifacts"]:
            where = f"{context}.artifacts"
            artifact_path = Path(reference)
            if artifact_path.is_absolute():
                errors.append(f"{where}: want a repo-relative path, got '{reference}'")
                continue
            resolved = (root / artifact_path).resolve()
            try:
                resolved.relative_to(runs_root)
            except ValueError:
                errors.append(f"{where}: '{reference}' must be an artifact under {RUNS}/")
                continue
            if not resolved.is_file():
                errors.append(f"{where}: '{reference}' does not exist")

        for candidate in metadata["candidates"]:
            candidate_id = candidate["id"]
            if candidate_id in node_ids:
                errors.append(
                    f"{context}.candidates: '{candidate_id}' is already a ledger node; a "
                    "candidate is not a node (CLAUDE.md constraint 8)"
                )
            elif candidate_id in declared:
                errors.append(
                    f"{context}.candidates: '{candidate_id}' was already proposed in "
                    f"{declared[candidate_id]['source']}"
                )
            else:
                declared[candidate_id] = {
                    "id": candidate_id,
                    "statement": candidate["statement"],
                    "source": relative,
                    "date": metadata["date"],
                    "order": order,
                }

        for candidate_id in metadata["retires"]:
            if candidate_id in {entry["id"] for entry in metadata["candidates"]}:
                errors.append(
                    f"{context}.retires: '{candidate_id}' is proposed by this same exploration"
                )
            elif candidate_id in retired:
                errors.append(
                    f"{context}.retires: '{candidate_id}' was already retired in "
                    f"{retired[candidate_id][1]}"
                )
            else:
                retired[candidate_id] = (order, relative)

    for candidate_id, (order, source) in sorted(retired.items()):
        if candidate_id not in declared:
            errors.append(f"{source}.retires: '{candidate_id}' was never proposed")
        elif declared[candidate_id]["order"] > order:
            errors.append(
                f"{source}.retires: '{candidate_id}' is retired before "
                f"{declared[candidate_id]['source']} proposes it"
            )

    return [entry for candidate_id, entry in sorted(declared.items())
            if candidate_id not in retired]


def all_labels(root: Path = ROOT) -> set[str]:
    labels: set[str] = set()
    modules = root / "modules"
    if not modules.exists():
        return labels
    for path in modules.rglob("*.tex"):
        labels |= set(re.findall(r"\\label\{([^}]+)\}", path.read_text()))
    return labels


def bibliography_keys(root: Path = ROOT) -> set[str] | None:
    """Return the repository BibTeX keys, or ``None`` when the bibliography is absent."""
    path = root / BIBLIOGRAPHY
    if not path.is_file():
        return None
    try:
        return set(BIB_ENTRY_RE.findall(path.read_text(encoding="utf-8")))
    except (OSError, UnicodeError):
        return None


def labels_in_file(path: Path) -> set[str]:
    """Return LaTeX labels in one readable file without leaking I/O exceptions."""
    try:
        return set(re.findall(r"\\label\{([^}]+)\}", path.read_text(encoding="utf-8")))
    except (OSError, UnicodeError):
        return set()


def _load_ledger(path: Path, errors: list[str]) -> dict | None:
    try:
        doc = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError as exc:
        errors.append(f"{path}: invalid YAML: {exc}")
        return None
    if not isinstance(doc, dict):
        errors.append(f"{path}: top level must be a mapping")
        return None
    return doc


def _nodes_by_id(path: Path, doc: dict, errors: list[str]) -> dict[str, dict]:
    raw_nodes = doc.get("nodes") or []
    if not isinstance(raw_nodes, list):
        errors.append(f"{path}: 'nodes' must be a list")
        return {}
    nodes: dict[str, dict] = {}
    for index, node in enumerate(raw_nodes):
        if not isinstance(node, dict):
            errors.append(f"{path}: node #{index + 1} must be a mapping")
            continue
        nid = node.get("id")
        if not isinstance(nid, str) or not nid.strip():
            errors.append(f"{path}: node #{index + 1} missing a non-empty string 'id'")
            continue
        if nid in nodes:
            errors.append(f"{path}: duplicate node id '{nid}'")
            continue
        nodes[nid] = node
    return nodes


def _inherited_risks(start: str, nodes: dict[str, dict], unproved: set[str]):
    """Return unresolved dependency risks inherited by ``start``.

    The traversal deliberately crosses intermediate nodes, so unresolved
    transitive proof premises are not hidden from an ancestor.
    """
    found: dict[tuple[str, str], list[str]] = {}

    def record(kind: str, target: str, path: list[str]):
        key = (kind, target)
        if key not in found or len(path) < len(found[key]):
            found[key] = path

    def visit(nid: str, path: list[str], stack: set[str]):
        if nid in stack:
            return
        node = nodes[nid]
        next_stack = stack | {nid}
        for dep in as_list(node.get("depends_on")):
            if not isinstance(dep, str) or dep not in nodes:
                continue
            dep_path = path + [dep]
            status = nodes[dep].get("status")
            if isinstance(status, str) and status in unproved:
                record(status, dep, dep_path)
            visit(dep, dep_path, next_stack)

    visit(start, [start], set())
    return found


def _validate_route_policy(program: str, meta: dict, nodes: dict[str, dict],
                           errors: list[str]) -> None:
    """Validate the optional compact route vocabulary and explicit node ownership."""
    raw_policy = meta.get("route_policy")
    if raw_policy is None:
        for nid, node in nodes.items():
            if "route" in node:
                errors.append(
                    f"[{program}] {nid}.route: explicit routes require meta.route_policy"
                )
        return
    context = f"[{program}] meta.route_policy"
    if not isinstance(raw_policy, dict):
        errors.append(f"{context}: must be a mapping")
        return
    for field in sorted(set(raw_policy) - {"allowed"}):
        errors.append(f"{context}: unknown field '{field}'")

    raw_allowed = raw_policy.get("allowed")
    allowed: set[str] = set()
    if not isinstance(raw_allowed, list):
        errors.append(f"{context}.allowed: must be a list")
    else:
        for route in raw_allowed:
            if not isinstance(route, str) or not route.strip():
                errors.append(f"{context}.allowed: entries must be non-empty strings")
                continue
            if route in allowed:
                errors.append(f"{context}.allowed: duplicate route '{route}'")
            allowed.add(route)

    for nid, node in nodes.items():
        if "route" not in node:
            errors.append(f"[{program}] {nid}.route: required by meta.route_policy")
            continue
        route = node.get("route")
        if not isinstance(route, str) or not route.strip():
            errors.append(f"[{program}] {nid}.route: must be a non-empty string")
        elif route not in allowed:
            errors.append(
                f"[{program}] {nid}.route: '{route}' is not in meta.route_policy.allowed"
            )


def _solution_artifact(root: Path, program: str, nid: str, reference: object,
                       errors: list[str]) -> Path | None:
    """Validate and return one natural-language proof dossier path."""
    context = f"[{program}] {nid}.proofs[].artifact"
    if not isinstance(reference, str) or not reference.strip():
        errors.append(f"{context}: must be a non-empty repo-relative path")
        return None
    relative = Path(reference)
    artifact = (root / relative).resolve()
    solutions_root = (root / "solutions").resolve()
    if relative.is_absolute():
        errors.append(f"{context}: want a repo-relative path, got '{reference}'")
        return None
    try:
        artifact.relative_to(solutions_root)
    except ValueError:
        errors.append(f"{context}: must stay under solutions/")
        return None
    if artifact.suffix != ".tex":
        errors.append(f"{context}: '{reference}' must be a .tex dossier")
    if not artifact.is_file():
        errors.append(f"{context}: '{reference}' does not exist")
        return None
    try:
        header = artifact.read_text(encoding="utf-8")[:2500]
    except (OSError, UnicodeError) as exc:
        errors.append(f"{context}: cannot read '{reference}': {exc}")
        return None
    if "ledger-node" not in header or not _mentions_token(header, nid):
        errors.append(
            f"{context}: dossier header does not enumerate the ledger node '{nid}'"
        )
    return artifact


def _validate_certification(root: Path, program: str, nid: str, node: dict,
                            nodes: dict[str, dict],
                            agent_review_refs: dict[str, list[tuple[str, str, str]]],
                            errors: list[str]) -> None:
    """Validate plural proof records and refutation provenance."""
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
            artifact = _solution_artifact(root, program, nid, artifact_ref, errors)
            if isinstance(artifact_ref, str):
                if artifact_ref in seen_artifacts:
                    errors.append(f"{context}.artifact: duplicate active proof '{artifact_ref}'")
                seen_artifacts.add(artifact_ref)
            mode = proof.get("mode")
            if mode not in PROOF_MODES:
                errors.append(
                    f"{context}.mode: want one of {sorted(PROOF_MODES)}, got '{mode}'"
                )
                continue

            review = proof.get("review")
            accepted_by = proof.get("accepted_by")
            if mode == "agent":
                if not isinstance(review, str) or not review.strip():
                        errors.append(f"{context}.review: mode agent requires a proof-review")
                elif isinstance(artifact_ref, str):
                    agent_review_refs.setdefault(review, []).append(
                        (program, nid, artifact_ref)
                    )
                if accepted_by is not None:
                    errors.append(f"{context}.accepted_by: valid only with mode human")
            elif mode == "human":
                if not isinstance(accepted_by, str) or not accepted_by.strip():
                    errors.append(f"{context}.accepted_by: mode human requires a non-empty identity")
                if review is not None:
                    errors.append(f"{context}.review: valid only with mode agent")
            elif mode == "lean":
                for field, value in (("review", review), ("accepted_by", accepted_by)):
                    if value is not None:
                        errors.append(f"{context}.{field}: not valid with mode lean")
                if artifact is not None and not artifact.with_suffix(".lean").is_file():
                    errors.append(
                        f"{context}: mode lean requires adjacent "
                        f"'{artifact.with_suffix('.lean').name}'"
                    )
    refuters = as_list(node.get("refuted_by"))
    if status == "refuted":
        if not refuters:
            errors.append(f"[{program}] {nid}: refuted node requires refuted_by")
        dependencies = set(as_list(node.get("depends_on")))
        for ref in refuters:
            if isinstance(ref, str) and ref in nodes:
                if nodes[ref].get("status") != "proved":
                    errors.append(f"[{program}] {nid}.refuted_by: '{ref}' is not proved")
                if ref not in dependencies:
                    errors.append(
                        f"[{program}] {nid}.refuted_by: '{ref}' must also appear in depends_on"
                    )
    elif "refuted_by" in node:
        errors.append(f"[{program}] {nid}.refuted_by: valid only with status refuted")


def check_control_plane(research: Path = RESEARCH, root: Path | None = None,
                        configured_ledger: str | Path | None = None) -> dict:
    """Validate a control-plane tree and return errors plus summary data.

    ``research``/``root`` parameters make the checker testable on isolated fixture
    trees without mutating the real repository. Production passes ``configured_ledger``
    so the single production ledger is explicit and a stray second ledger is an
    error; fixture tests omit it and discover temporary ledgers recursively.
    """
    research = Path(research)
    root = Path(root) if root is not None else research.parent
    labels = all_labels(root)
    bib_keys = bibliography_keys(root)
    errors: list[str] = []
    ledgers: list[dict] = []
    program_paths: dict[str, Path] = {}
    agent_review_refs: dict[str, list[tuple[str, str, str]]] = {}
    discovered_paths = sorted(research.rglob("ledger.yaml"))
    if configured_ledger is None:
        ledger_paths = discovered_paths
    else:
        relative = Path(configured_ledger)
        ledger_paths = []
        if relative.is_absolute():
            errors.append(f"configured ledger must be repo-relative: '{configured_ledger}'")
            configured_path = None
        else:
            configured_path = (root / relative).resolve()
            if configured_path.is_file():
                ledger_paths.append(configured_path)
            else:
                errors.append(f"configured ledger does not exist: '{configured_ledger}'")
        for path in discovered_paths:
            if configured_path is None or path.resolve() != configured_path:
                errors.append(
                    f"{path}: unexpected second ledger; this repository has exactly one "
                    f"program ledger at '{configured_ledger}' (CLAUDE.md constraint 1)"
                )

    for path in sorted(ledger_paths):
        doc = _load_ledger(path, errors)
        if doc is None:
            continue
        for field in sorted(set(doc) - TOP_LEVEL_FIELDS):
            errors.append(f"{path}: unknown top-level field '{field}'")
        meta = doc.get("meta") or {}
        if not isinstance(meta, dict):
            errors.append(f"{path}: 'meta' must be a mapping")
            meta = {}
        program = meta.get("program")
        if not isinstance(program, str) or not program.strip():
            errors.append(f"{path}: meta.program must be a non-empty string")
            program = f"invalid:{path}"
        for field in sorted(set(meta) - META_FIELDS - OBSOLETE_META_FIELDS):
            errors.append(f"[{program}] meta: unknown field '{field}'")
        if program in program_paths:
            errors.append(
                f"{path}: duplicate ledger for program '{program}' "
                f"(already loaded from {program_paths[program]})"
            )
        else:
            program_paths[program] = path
        nodes = _nodes_by_id(path, doc, errors)
        obstruction_ids = {
            nid for nid, node in nodes.items() if node.get("kind") == "obstruction"
        }
        ledgers.append({
            "program": program,
            "path": path,
            "meta": meta,
            "nodes": nodes,
            "obs_ids": obstruction_ids,
        })

    qualified = {
        f"{ledger['program']}/{nid}"
        for ledger in ledgers
        for nid in ledger["nodes"]
    }

    for ledger in ledgers:
        program = ledger["program"]
        nodes = ledger["nodes"]
        meta = ledger["meta"]
        obstruction_ids = ledger["obs_ids"]
        for obsolete_field in OBSOLETE_META_FIELDS:
            if obsolete_field in meta:
                errors.append(
                    f"[{program}] meta.{obsolete_field}: legacy proof exceptions are forbidden; "
                    "every proved node requires a certified solution"
                )
        _validate_route_policy(program, meta, nodes, errors)

        for nid, node in nodes.items():
            for field, replacement in OBSOLETE_NODE_FIELDS.items():
                if field not in node:
                    continue
                errors.append(
                    f"[{program}] {nid}.{field}: obsolete field; use {replacement}"
                )
            ignored_obsolete = set(OBSOLETE_NODE_FIELDS)
            for field in sorted(set(node) - NODE_FIELDS - ignored_obsolete):
                errors.append(f"[{program}] {nid}: unknown field '{field}'")
            for field in sorted(LIST_FIELDS & set(node)):
                if not isinstance(node[field], list):
                    errors.append(f"[{program}] {nid}.{field}: must be a list")
            for field in ("kind", "status", "provenance", "file", "statement"):
                if field not in node:
                    errors.append(f"[{program}] {nid}: missing '{field}'")
            kind = node.get("kind")
            status = node.get("status")
            provenance = node.get("provenance")
            if not isinstance(kind, str) or kind not in KIND:
                errors.append(f"[{program}] {nid}: bad kind '{kind}'")
            if isinstance(status, str) and status in {"conjectured", "conditional", "imported"}:
                replacement = {
                    "conjectured": "status open",
                    "conditional": "status proved plus assumes for a proved implication",
                    "imported": "provenance literature plus the claim's logical status",
                }[status]
                errors.append(
                    f"[{program}] {nid}: status '{status}' is obsolete; use {replacement}"
                )
            elif not isinstance(status, str) or status not in STATUSES:
                errors.append(
                    f"[{program}] {nid}: bad status '{status}' "
                    f"(want one of {sorted(STATUSES)})"
                )
            if not isinstance(provenance, str) or provenance not in PROVENANCE:
                errors.append(
                    f"[{program}] {nid}: bad provenance '{provenance}' "
                    f"(want one of {sorted(PROVENANCE)})"
                )
            if status == "defined" and kind != "definition":
                errors.append(
                    f"[{program}] {nid}: status defined is only valid for kind definition"
                )
            if kind == "definition" and status != "defined":
                errors.append(
                    f"[{program}] {nid}: kind definition requires status defined"
                )
            import_class = node.get("import_class")
            if provenance == "literature":
                if import_class is None:
                    errors.append(
                        f"[{program}] {nid}: literature node requires explicit import_class"
                    )
                elif import_class not in IMPORT_CLASSES:
                    errors.append(
                        f"[{program}] {nid}: bad import_class '{import_class}' "
                        f"(want one of {sorted(IMPORT_CLASSES)})"
                    )
                references = node.get("references")
                if not isinstance(references, list) or not references:
                    errors.append(
                        f"[{program}] {nid}: literature node requires non-empty references"
                    )
                else:
                    for reference in references:
                        if not isinstance(reference, str) or not reference.strip():
                            errors.append(
                                f"[{program}] {nid}.references: entries must be "
                                "non-empty BibTeX keys"
                            )
                        elif bib_keys is None:
                            errors.append(
                                f"[{program}] {nid}.references: {BIBLIOGRAPHY} is missing "
                                "or unreadable"
                            )
                        elif reference not in bib_keys:
                            errors.append(
                                f"[{program}] {nid}.references: unknown BibTeX key "
                                f"'{reference}'"
                            )
                if import_class == "preprint-unreviewed" and status == "proved":
                    errors.append(
                        f"[{program}] {nid}: an unreviewed preprint cannot have status proved; "
                        "use status open until its proof is reviewed"
                    )
            elif import_class is not None:
                errors.append(f"[{program}] {nid}: import_class is only valid with provenance literature")
            elif "references" in node:
                errors.append(f"[{program}] {nid}: references is only valid with provenance literature")

            declared_file: Path | None = None
            if "file" in node:
                file_ref = node.get("file")
                context = f"[{program}] {nid}.file"
                if not isinstance(file_ref, str) or not file_ref.strip():
                    errors.append(f"{context}: must be a non-empty string")
                else:
                    relative_file = Path(file_ref)
                    if relative_file.is_absolute():
                        errors.append(f"{context}: want a repo-relative path, got '{file_ref}'")
                    else:
                        resolved_file = (root / relative_file).resolve()
                        try:
                            resolved_file.relative_to(root.resolve())
                        except ValueError:
                            errors.append(f"{context}: path escapes repository root: '{file_ref}'")
                        else:
                            if not resolved_file.is_file():
                                errors.append(f"{context}: '{file_ref}' does not exist")
                            else:
                                declared_file = resolved_file
            effective_label = node.get("label", nid)
            if "label" in node and (
                not isinstance(node.get("label"), str) or not node["label"].strip()
            ):
                errors.append(f"[{program}] {nid}.label: must be a non-empty LaTeX label")
            elif isinstance(effective_label, str):
                if effective_label not in labels:
                    errors.append(
                        f"[{program}] {nid}: effective manuscript label "
                        f"'{effective_label}' not found in modules/"
                    )
                elif declared_file is not None and effective_label not in labels_in_file(declared_file):
                    errors.append(
                        f"[{program}] {nid}.file: '{node.get('file')}' does not contain "
                        f"effective label '{effective_label}'"
                    )
            for text_field in ("statement",):
                if text_field in node and (
                    not isinstance(node.get(text_field), str) or not node[text_field].strip()
                ):
                    errors.append(
                        f"[{program}] {nid}.{text_field}: must be a non-empty string"
                    )

            _validate_certification(
                root, program, nid, node, nodes, agent_review_refs, errors
            )

            for field in RESOLVE_FIELDS:
                for ref in as_list(node.get(field)):
                    if not isinstance(ref, str) or not ref.strip():
                        errors.append(f"[{program}] {nid}.{field}: references must be non-empty strings")
                    elif ref not in nodes:
                        errors.append(
                            f"[{program}] {nid}.{field}: '{ref}' is not a node in this ledger"
                        )

            for ref in as_list(node.get("bounded_by")):
                if not isinstance(ref, str) or not ref.strip():
                    errors.append(f"[{program}] {nid}.bounded_by: references must be non-empty strings")
                elif ref not in obstruction_ids:
                    errors.append(f"[{program}] {nid}.bounded_by: '{ref}' is not a declared obstruction")
                elif nodes[ref].get("status") != "proved":
                    errors.append(
                        f"[{program}] {nid}.bounded_by: '{ref}' is not an established obstruction; "
                        "use heuristic_barriers for an open barrier"
                    )

            for ref in as_list(node.get("heuristic_barriers")):
                if not isinstance(ref, str) or not ref.strip():
                    errors.append(
                        f"[{program}] {nid}.heuristic_barriers: references must be non-empty strings"
                    )
                elif ref not in obstruction_ids:
                    errors.append(
                        f"[{program}] {nid}.heuristic_barriers: '{ref}' is not a declared obstruction"
                    )
                elif nodes[ref].get("status") == "proved":
                    errors.append(
                        f"[{program}] {nid}.heuristic_barriers: '{ref}' is established; "
                        "use bounded_by"
                    )

            if node.get("implies") and status != "proved":
                errors.append(
                    f"[{program}] {nid}.implies: only a proved implication may advertise conclusions"
                )

        errors.extend(_acyclic(program, nodes))

        for nid, node in nodes.items():
            if node.get("status") != "proved":
                continue
            for (kind, target), path in sorted(_inherited_risks(nid, nodes, UNRESOLVED_STATUSES).items()):
                errors.append(
                    f"[{program}] {nid} (proved) inherits unresolved {kind} '{target}' "
                    f"via {' -> '.join(path)}"
                )

    _validate_agent_reviews(root, agent_review_refs, errors)
    node_ids = qualified | {nid for ledger in ledgers for nid in ledger["nodes"]}
    candidates = _validate_explorations(root, node_ids, errors)
    return {"errors": errors, "ledgers": ledgers, "labels": labels,
            "candidates": candidates}


def _acyclic(program: str, nodes: dict[str, dict]) -> list[str]:
    white, gray, black = 0, 1, 2
    color = {nid: white for nid in nodes}
    errors: list[str] = []

    def visit(node_id: str, stack: list[str]):
        color[node_id] = gray
        for dependency in as_list(nodes[node_id].get("depends_on")):
            if not isinstance(dependency, str) or dependency not in nodes:
                continue
            if color[dependency] == gray:
                errors.append(
                    f"[{program}] CYCLE: "
                    + " -> ".join(stack[stack.index(dependency):] + [dependency])
                )
            elif color[dependency] == white:
                visit(dependency, stack + [dependency])
        color[node_id] = black

    for node_id in nodes:
        if color[node_id] == white:
            visit(node_id, [node_id])
    return errors


def _applicability_blockers(node_id: str, nodes: dict[str, dict]) -> list[str]:
    """Return unresolved antecedents without confusing them with proof gaps."""
    blockers: set[str] = set()
    for assumed in as_list(nodes[node_id].get("assumes")):
        if not isinstance(assumed, str) or assumed not in nodes:
            continue
        if nodes[assumed].get("status") in UNRESOLVED_STATUSES:
            blockers.add(assumed)
        for _risk, target in _inherited_risks(
            assumed, nodes, UNRESOLVED_STATUSES
        ):
            blockers.add(target)
    return sorted(blockers)


def _print_summary(report: dict) -> None:
    """Print the stable structural summary used by the historical default command."""
    ledgers = report["ledgers"]
    total = sum(len(ledger["nodes"]) for ledger in ledgers)
    print(
        f"\n{len(ledgers)} ledger(s), {total} nodes, {len(report['labels'])} labels. "
        f"{len(report['errors'])} error(s)."
    )
    for ledger in sorted(ledgers, key=lambda item: (item["program"], str(item["path"]))):
        counts = Counter(str(node.get("status")) for node in ledger["nodes"].values())
        statuses = ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))
        print(f"  [{ledger['program']}] {len(ledger['nodes'])} nodes — {statuses}")
    live = report.get("candidates") or []
    if live:
        print(f"  {len(live)} live candidate(s) — see 'check_ledger.py candidates'")


def _print_candidates(report: dict) -> None:
    """List the candidate statements no exploration has retired yet.

    These are not ledger nodes and carry no status. A stable, reusable candidate
    earns a node and a manuscript statement by an orchestrator decision
    (CLAUDE.md constraint 8).
    """
    live = report.get("candidates") or []
    if not live:
        print("No live candidate statements.")
        return
    for entry in live:
        print(f"{entry['id']}  ({entry['date']}, {entry['source']})")
        print(f"  {entry['statement']}")


def _print_status(report: dict) -> None:
    """Print the unresolved frontier derived from ledger state."""
    frontier_statuses = {"open", "refuted"}
    for ledger in sorted(report["ledgers"], key=lambda item: item["program"]):
        groups: dict[str, dict[str, list[str]]] = {}
        for nid, node in ledger["nodes"].items():
            status = node.get("status")
            if status not in frontier_statuses:
                if status == "proved" and _applicability_blockers(nid, ledger["nodes"]):
                    status = "applicability-blocked"
                else:
                    continue
            group = str(node.get("route", ledger["program"]))
            groups.setdefault(group, {}).setdefault(str(status), []).append(nid)
        for group, statuses in sorted(groups.items()):
            label = ledger["program"] if group == ledger["program"] else f"{ledger['program']}/{group}"
            print(f"[{label}]")
            for status, node_ids in sorted(statuses.items()):
                print(f"  {status} ({len(node_ids)}): {', '.join(sorted(node_ids))}")


def _print_node(report: dict, reference: str) -> bool:
    """Print one node and its derived consumers without storing a reverse graph."""
    matches: list[tuple[dict, str, dict]] = []
    for ledger in report["ledgers"]:
        for nid, node in ledger["nodes"].items():
            if reference in {nid, f"{ledger['program']}/{nid}"}:
                matches.append((ledger, nid, node))
    if not matches:
        print(f"No ledger node matches '{reference}'.", file=sys.stderr)
        return False
    if len(matches) > 1:
        choices = ", ".join(f"{ledger['program']}/{nid}" for ledger, nid, _node in matches)
        print(f"Ambiguous node '{reference}'; use one of: {choices}", file=sys.stderr)
        return False

    ledger, nid, node = matches[0]
    print(f"[{ledger['program']}] {nid}")
    print(yaml.safe_dump(node, sort_keys=False, allow_unicode=True).rstrip())
    consumers = sorted(
        candidate_id for candidate_id, candidate in ledger["nodes"].items()
        if nid in as_list(candidate.get("depends_on"))
    )
    print("used_by:", consumers or "[]")
    for field, label in (
        ("assumes", "assumed_by"),
        ("implies", "implied_by"),
        ("refines", "refined_by"),
    ):
        reverse = sorted(
            candidate_id for candidate_id, candidate in ledger["nodes"].items()
            if nid in as_list(candidate.get(field))
        )
        print(f"{label}:", reverse or "[]")
    print("applicability_blocked_by:", _applicability_blockers(nid, ledger["nodes"]) or "[]")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate and inspect the research control plane")
    parser.add_argument("command", nargs="?",
                        choices=("check", "status", "node", "candidates"), default="check")
    parser.add_argument("node_id", nargs="?", help="node id, optionally qualified as program/id")
    args = parser.parse_args(argv)
    if args.command != "node" and args.node_id:
        parser.error(f"{args.command} does not accept a node id")

    report = check_control_plane(configured_ledger=LEDGER_PATH)
    for error in report["errors"]:
        print("FAIL:", error)
    if report["errors"]:
        _print_summary(report)
        return 1
    if args.command == "status":
        _print_status(report)
    elif args.command == "candidates":
        _print_candidates(report)
    elif args.command == "node":
        if not args.node_id:
            parser.error("node requires NODE_ID")
        if not _print_node(report, args.node_id):
            return 1
    else:
        _print_summary(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
