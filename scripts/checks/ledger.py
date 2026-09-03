"""The core lane: the claim graph, its manuscript anchors, and its bibliography.

This is the lane that owns *what is mathematically claimed*. It validates node
identity and schema, the acyclic proof DAG, the separation of proof dependencies from
implication antecedents, the two classes of obstruction, and the coupling between a
node id and a ``\\label`` in ``modules/``. Proof certification lives in ``proofs.py``;
search activity lives in ``portfolio.py``; neither belongs here.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

from .common import as_list, contained_path, repo_relative

#: One repository, one program, one ledger (CLAUDE.md constraint 1). The program
#: names itself in ``meta.program``; the path is fixed so no configuration file
#: has to agree with it.
LEDGER_PATH = Path("research/program/ledger.yaml")

#: The repository bibliography, resolved relative to the repository root.
BIBLIOGRAPHY = Path("references.bib")

KIND = {
    "theorem", "lemma", "proposition", "corollary", "definition", "assumption",
    "question", "conjecture", "obstruction", "example",
}

#: The LaTeX environments that carry a claim. Deliberately the same words as ``KIND``:
#: a ``\label`` inside one of these, in ``modules/``, is a ledger node whose ``kind`` is
#: the environment's name. Everything else — ``\section``, ``\subsection``, ``equation``,
#: ``remark`` — is structural or expository and carries no node.
CLAIM_ENVIRONMENTS = frozenset(KIND)

ENVIRONMENT_RE = re.compile(r"\\(begin|end)\{([A-Za-z][A-Za-z0-9*]*)\}")
LABEL_RE = re.compile(r"\\label\{([^}]+)\}")

# One logical-status vocabulary. Mathematical form belongs in ``kind``;
# speculative prose is not a ledger classification.
STATUSES = {"open", "proved", "defined", "refuted"}
PROVENANCE = {"internal", "literature"}
IMPORT_CLASSES = {"published", "preprint-unreviewed", "preprint-reviewed"}

# Unresolved premises are discovered recursively through the canonical
# ``depends_on`` graph; an unreviewed preprint therefore has status ``open``.
UNRESOLVED_STATUSES = {"open", "refuted"}

RESOLVE_FIELDS = (
    "depends_on", "assumes", "implies", "refines", "refuted_by",
)

# Frontier relations resolve inside the ledger but do not enter the proof DAG.
NODE_FIELDS = {
    "id", "kind", "status", "provenance", "file", "summary",
    "depends_on", "assumes", "implies", "refines", "bounded_by",
    "heuristic_barriers", "references", "import_class", "proofs",
    "refuted_by",
}
LIST_FIELDS = {
    "depends_on", "assumes", "implies", "refines", "bounded_by",
    "heuristic_barriers", "references", "proofs", "refuted_by",
}
OBSOLETE_NODE_FIELDS = {
    "assuming": "assumes for antecedents of an implication",
    "discharged_by": "depends_on on the result that performs the discharge",
    "evidence": "a dated checkpoint plus an immutable research/runs artifact",
    "evidence_eligible": "a dated checkpoint plus an immutable research/runs artifact",
    "evidence_run": "a dated checkpoint plus an immutable research/runs artifact",
    "evidence_target": "the numerics target implementation and a dated checkpoint",
    "entry_point": "the problem brief or the search portfolio",
    "target_doc": "the problem brief or the search portfolio",
    "mechanism": "bounded_by plus independent semantic review",
    "clearance": "the proof dossier/review discussion of bounded_by",
    "note": "the manuscript, the problem brief, or a dated checkpoint",
    "numerics": "the numerics implementation, instance registry, or a dated checkpoint",
    "solution": "proofs with one artifact/mode record per active proof",
    "checked_by": "proofs[].mode",
    "review": "proofs[].review",
    "accepted_by": "proofs[].accepted_by",
    "proof_file": "proofs[].artifact",
    "proof_provenance": "proofs with explicit certification records",
    "authored_by": "proof-review front matter",
    "reviewed_by": "proof-review front matter",
    "related": "one of assumes, implies, refines, or the portfolio's approach relations",
    "bridges": "a precise same-ledger implication/refinement or prose for an external comparison",
    "unlocks": "depends_on on the consuming node, or prose for non-logical relationships",
    "approach": "the search portfolio; an approach is not a mathematical claim",
    "family": "the search portfolio; an approach family is not a mathematical claim",
    "route": "the search portfolio; a route is coordination state, not a claim "
             "(CLAUDE.md constraint 12)",
    "label": "the node id itself as the manuscript anchor; an override made the "
             "id-is-the-anchor rule untrue and had no second reader",
    "statement": "summary for the ledger's one-line gloss; the statement itself lives "
                 "in modules/ under this node's \\label and nowhere else",
}
BIB_ENTRY_RE = re.compile(r"@[A-Za-z]+\s*\{\s*([^,\s]+)\s*,")
TOP_LEVEL_FIELDS = {"meta", "nodes"}
META_FIELDS = {"program", "scope"}
OBSOLETE_META_FIELDS = {
    "legacy_r2_debt": "a certified proof on every proved node; there are no exceptions",
    "legacy_proved_without_solution":
        "a certified proof on every proved node; there are no exceptions",
    "route_policy": "the search portfolio; coordination ownership is not "
                    "mathematical state (CLAUDE.md constraint 12)",
}


def _labels_with_environments(text: str) -> list[tuple[str, str | None]]:
    """Pair every ``\\label`` in one file with the claim environment enclosing it.

    The enclosing environment is the innermost open *claim* environment, so a label
    inside a ``proof`` or an ``itemize`` nested in a ``theorem`` still belongs to the
    theorem. A label with no claim environment above it — a ``\\section`` anchor, an
    equation tag, a ``remark`` — is structural and pairs with ``None``.
    """
    events = sorted(
        [(match.start(), "env", match.group(1), match.group(2))
         for match in ENVIRONMENT_RE.finditer(text)]
        + [(match.start(), "label", match.group(1), None)
           for match in LABEL_RE.finditer(text)]
    )
    stack: list[str] = []
    found: list[tuple[str, str | None]] = []
    for _position, kind, first, second in events:
        if kind == "env":
            if first == "begin":
                stack.append(second)
            elif stack and second in stack:
                # Close to the matching \begin, tolerating unbalanced prose above it.
                del stack[stack.index(second):]
        else:
            enclosing = next(
                (name for name in reversed(stack) if name in CLAIM_ENVIRONMENTS), None
            )
            found.append((first, enclosing))
    return found


def manuscript_labels(root: Path, errors: list[str] | None = None) -> dict[str, dict]:
    """Every ``\\label`` under ``modules/``, with its environment and file.

    The invariant this supports is narrower and truer than "a label is a node id":
    every *claim-bearing theorem-environment* label is exactly one ledger node, and a
    structural label is not a node at all. Returned as a mapping so a duplicate is
    detectable — a set silently merged two anchors that disagree.
    """
    labels: dict[str, dict] = {}
    modules = root / "modules"
    if not modules.is_dir():
        return labels
    for path in sorted(modules.rglob("*.tex")):
        relative = path.relative_to(root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            if errors is not None:
                errors.append(f"{relative}: cannot read manuscript module: {exc}")
            continue
        for label, environment in _labels_with_environments(text):
            if label in labels and errors is not None:
                errors.append(
                    f"{relative}: duplicate manuscript label '{label}', already at "
                    f"{labels[label]['file']}; one anchor, one place"
                )
                continue
            labels[label] = {"environment": environment, "file": relative}
    return labels


def unclaimed_labels(labels: dict[str, dict], node_ids: set[str]) -> list[str]:
    """Claim-environment labels in ``modules/`` that no ledger node answers for."""
    return sorted(
        label for label, entry in labels.items()
        if entry["environment"] is not None and label not in node_ids
    )


def bibliography_keys(root: Path) -> set[str] | None:
    """Return the repository BibTeX keys, or ``None`` when the bibliography is absent."""
    path = root / BIBLIOGRAPHY
    if not path.is_file():
        return None
    try:
        return set(BIB_ENTRY_RE.findall(path.read_text(encoding="utf-8")))
    except (OSError, UnicodeError):
        return None


def _load(path: Path, errors: list[str]) -> dict | None:
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


def inherited_risks(start: str, nodes: dict[str, dict], unproved: set[str]):
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


def applicability_blockers(node_id: str, nodes: dict[str, dict]) -> list[str]:
    """Return unresolved antecedents without confusing them with proof gaps."""
    blockers: set[str] = set()
    for assumed in as_list(nodes[node_id].get("assumes")):
        if not isinstance(assumed, str) or assumed not in nodes:
            continue
        if nodes[assumed].get("status") in UNRESOLVED_STATUSES:
            blockers.add(assumed)
        for _risk, target in inherited_risks(assumed, nodes, UNRESOLVED_STATUSES):
            blockers.add(target)
    return sorted(blockers)


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
                    f"[{program}] dependency cycle: "
                    f"{' -> '.join(stack + [node_id, dependency])}"
                )
            elif color[dependency] == white:
                visit(dependency, stack + [node_id])
        color[node_id] = black

    for node_id in nodes:
        if color[node_id] == white:
            visit(node_id, [])
    return errors


def _validate_node(program: str, nid: str, node: dict, *, root: Path,
                   labels: dict[str, dict], bib_keys: set[str] | None,
                   nodes: dict[str, dict], obstruction_ids: set[str],
                   errors: list[str]) -> None:
    for field, replacement in OBSOLETE_NODE_FIELDS.items():
        if field in node:
            errors.append(f"[{program}] {nid}.{field}: obsolete field; use {replacement}")
    for field in sorted(set(node) - NODE_FIELDS - set(OBSOLETE_NODE_FIELDS)):
        errors.append(f"[{program}] {nid}: unknown field '{field}'")
    for field in sorted(LIST_FIELDS & set(node)):
        if not isinstance(node[field], list):
            errors.append(f"[{program}] {nid}.{field}: must be a list")
    for field in ("kind", "status", "provenance", "file", "summary"):
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
        errors.append(f"[{program}] {nid}: status '{status}' is obsolete; use {replacement}")
    elif not isinstance(status, str) or status not in STATUSES:
        errors.append(
            f"[{program}] {nid}: bad status '{status}' (want one of {sorted(STATUSES)})"
        )
    if not isinstance(provenance, str) or provenance not in PROVENANCE:
        errors.append(
            f"[{program}] {nid}: bad provenance '{provenance}' "
            f"(want one of {sorted(PROVENANCE)})"
        )
    if status == "defined" and kind != "definition":
        errors.append(f"[{program}] {nid}: status defined is only valid for kind definition")
    if kind == "definition" and status != "defined":
        errors.append(f"[{program}] {nid}: kind definition requires status defined")

    import_class = node.get("import_class")
    if provenance == "literature":
        if import_class is None:
            errors.append(f"[{program}] {nid}: literature node requires explicit import_class")
        elif import_class not in IMPORT_CLASSES:
            errors.append(
                f"[{program}] {nid}: bad import_class '{import_class}' "
                f"(want one of {sorted(IMPORT_CLASSES)})"
            )
        references = node.get("references")
        if not isinstance(references, list) or not references:
            errors.append(f"[{program}] {nid}: literature node requires non-empty references")
        else:
            for reference in references:
                if not isinstance(reference, str) or not reference.strip():
                    errors.append(
                        f"[{program}] {nid}.references: entries must be non-empty BibTeX keys"
                    )
                elif bib_keys is None:
                    errors.append(
                        f"[{program}] {nid}.references: {BIBLIOGRAPHY} is missing or unreadable"
                    )
                elif reference not in bib_keys:
                    errors.append(
                        f"[{program}] {nid}.references: unknown BibTeX key '{reference}'"
                    )
        if import_class == "preprint-unreviewed" and status == "proved":
            errors.append(
                f"[{program}] {nid}: an unreviewed preprint cannot have status proved; "
                "use status open until its proof is reviewed"
            )
    elif import_class is not None:
        errors.append(
            f"[{program}] {nid}: import_class is only valid with provenance literature"
        )
    elif "references" in node:
        errors.append(f"[{program}] {nid}: references is only valid with provenance literature")

    declared_file: str | None = None
    if "file" in node:
        # Confined to modules/ like every other cross-lane pointer is confined to its
        # own directory: the manuscript is the only place a claim may be stated, so a
        # node anchored anywhere else has no anchor a reader would think to look at.
        resolved_file = contained_path(
            root, node.get("file"), "modules", f"[{program}] {nid}.file", errors,
            suffix=".tex", outside="a claim is stated in modules/, nowhere else",
        )
        if resolved_file is not None:
            declared_file = repo_relative(root, resolved_file)

    anchor = labels.get(nid)
    if anchor is None:
        errors.append(
            f"[{program}] {nid}: no manuscript label '{nid}' in modules/; the node id "
            "is the anchor"
        )
    else:
        if anchor["environment"] is None:
            errors.append(
                f"[{program}] {nid}: '{nid}' labels a structural element in "
                f"{anchor['file']}, not a claim environment; a node states a claim"
            )
        elif isinstance(kind, str) and anchor["environment"] != kind:
            errors.append(
                f"[{program}] {nid}.kind: '{kind}' disagrees with the "
                f"\\begin{{{anchor['environment']}}} it labels in {anchor['file']}"
            )
        if declared_file is not None and declared_file != anchor["file"]:
            errors.append(
                f"[{program}] {nid}.file: '{declared_file}' does not contain '{nid}'; "
                f"it is in {anchor['file']}"
            )

    if "summary" in node and (
        not isinstance(node.get("summary"), str) or not node["summary"].strip()
    ):
        errors.append(f"[{program}] {nid}.summary: must be a non-empty string")

    for field in RESOLVE_FIELDS:
        for ref in as_list(node.get(field)):
            if not isinstance(ref, str) or not ref.strip():
                errors.append(
                    f"[{program}] {nid}.{field}: references must be non-empty strings"
                )
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
                f"[{program}] {nid}.heuristic_barriers: '{ref}' is established; use bounded_by"
            )

    if node.get("implies") and status != "proved":
        errors.append(
            f"[{program}] {nid}.implies: only a proved implication may advertise conclusions"
        )


def check(root: Path, research: Path, errors: list[str],
          configured_ledger: str | Path | None = None,
          labels: dict[str, dict] | None = None) -> list[dict]:
    """Validate the claim graph and return one record per loaded ledger.

    ``configured_ledger`` is passed in production so the single ledger is explicit and a
    stray second one is an error; fixture trees omit it and discover ledgers recursively.
    """
    labels = manuscript_labels(root, errors) if labels is None else labels
    bib_keys = bibliography_keys(root)
    ledgers: list[dict] = []
    program_paths: dict[str, Path] = {}
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
        doc = _load(path, errors)
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
        for field in sorted(set(meta) - META_FIELDS - set(OBSOLETE_META_FIELDS)):
            errors.append(f"[{program}] meta: unknown field '{field}'")
        if program in program_paths:
            errors.append(
                f"{path}: duplicate ledger for program '{program}' "
                f"(already loaded from {program_paths[program]})"
            )
        else:
            program_paths[program] = path
        nodes = _nodes_by_id(path, doc, errors)
        ledgers.append({
            "program": program,
            "path": path,
            "meta": meta,
            "nodes": nodes,
            "obs_ids": {
                nid for nid, node in nodes.items() if node.get("kind") == "obstruction"
            },
        })

    for ledger in ledgers:
        program, nodes, meta = ledger["program"], ledger["nodes"], ledger["meta"]
        for obsolete_field, replacement in OBSOLETE_META_FIELDS.items():
            if obsolete_field in meta:
                errors.append(
                    f"[{program}] meta.{obsolete_field}: obsolete field; use {replacement}"
                )
        for nid, node in nodes.items():
            _validate_node(program, nid, node, root=root, labels=labels, bib_keys=bib_keys,
                           nodes=nodes, obstruction_ids=ledger["obs_ids"], errors=errors)
        errors.extend(_acyclic(program, nodes))
        for nid, node in nodes.items():
            if node.get("status") != "proved":
                continue
            risks = inherited_risks(nid, nodes, UNRESOLVED_STATUSES)
            for (kind, target), path in sorted(risks.items()):
                errors.append(
                    f"[{program}] {nid} (proved) inherits unresolved {kind} '{target}' "
                    f"via {' -> '.join(path)}"
                )

    # The other direction of the anchor invariant. A node without its label is caught
    # per node above; a claim stated in the manuscript that no node answers for is
    # caught here, once, against every ledger loaded.
    declared = {nid for ledger in ledgers for nid in ledger["nodes"]}
    for label in unclaimed_labels(labels, declared):
        errors.append(
            f"{labels[label]['file']}: \\label{{{label}}} states a "
            f"\\begin{{{labels[label]['environment']}}} that no ledger node answers "
            "for; give it a node or make it structural"
        )

    return ledgers


def node_ids(ledgers: list[dict]) -> set[str]:
    """Every node id, bare and program-qualified, for cross-lane reference checks."""
    ids = {nid for ledger in ledgers for nid in ledger["nodes"]}
    ids |= {f"{ledger['program']}/{nid}" for ledger in ledgers for nid in ledger["nodes"]}
    return ids
