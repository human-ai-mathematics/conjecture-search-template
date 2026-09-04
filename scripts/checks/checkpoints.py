"""The checkpoints lane: durable search memory and the candidate statements it carries.

A checkpoint is one dated file in ``research/explorations/`` recording a durable search
event — not every attempt. Its envelope records what the work *engaged*: which ledger
nodes, which portfolio approach, which run artifacts, which candidate statements it
proposed or retired, and which earlier checkpoint it supersedes as the current summary.

Supersession is presentation, not deletion (CLAUDE.md constraint 6). ``retires:`` kills a
tentative *statement*; ``supersedes:`` says a later *record* should be read instead. The
same relation is offered to non-certifying audits, which have the same staleness problem.
"""
from __future__ import annotations

import re
from pathlib import Path

from .common import (APPROACH_ID_RE, check_record_date, contained_path,
                     optional_string_list, read_front_matter, record_instant,
                     repo_relative, strictly_after)

EXPLORATIONS = "research/explorations"
RUNS = "research/runs"

EXPLORATION_FIELDS = {
    "type", "date", "nodes", "outcome", "artifacts", "candidates", "retires",
    "promotes", "approach", "supersedes",
}
EXPLORATION_REQUIRED = {"type", "date", "outcome"}

#: What the checkpoint produced, for the next agent deciding whether to repeat it.
EXPLORATION_OUTCOMES = {"dead-end", "directional", "candidate", "proposed"}

# A candidate is a statement someone thought worth writing down and nothing more
# (CLAUDE.md constraint 7). Its id is namespaced so it can never be mistaken for a
# ledger node id, and an approach id is namespaced so it can never be mistaken for either.
CANDIDATE_ID_RE = re.compile(r"^cand:[a-z0-9][a-z0-9-]*$")
CANDIDATE_FIELDS = {"id", "statement"}

#: Promotion is one act, not three. Adding the manuscript statement and the node while
#: leaving the candidate live left two homes for one statement, which is exactly what
#: constraint 7 forbids; recording the promotion here retires the candidate, points the
#: portfolio at the node, and leaves the audit trail in the append-only log.
PROMOTION_FIELDS = {"candidate", "node"}


def _read_metadata(path: Path, root: Path, errors: list[str]) -> dict | None:
    """Parse and validate the front matter of one dated checkpoint.

    The envelope exists so that durable memory answers the question the next agent
    actually has — has this node been attacked, through which approach, and what came
    back — without anyone reading every file. It records what the work engaged, not what
    it concluded: conclusions are prose, and a conclusion that earns reuse becomes a
    ledger node.
    """
    context = str(path)
    raw = read_front_matter(path, "checkpoint", errors)
    if raw is None:
        return None
    if raw.get("type") != "exploration":
        errors.append(f"{context}.type: want 'exploration', got '{raw.get('type')}'")
        return None
    for field in sorted(set(raw) - EXPLORATION_FIELDS):
        errors.append(f"{context}: field '{field}' is not valid for a checkpoint")
    for field in sorted(EXPLORATION_REQUIRED - set(raw)):
        errors.append(f"{context}: required field '{field}' is missing")

    outcome = raw.get("outcome")
    if "outcome" in raw and outcome not in EXPLORATION_OUTCOMES:
        errors.append(
            f"{context}.outcome: want one of {sorted(EXPLORATION_OUTCOMES)}, got '{outcome}'"
        )

    approach = raw.get("approach")
    if approach is not None and (
        not isinstance(approach, str) or not APPROACH_ID_RE.match(approach)
    ):
        errors.append(f"{context}.approach: want 'ap:<slug>', got '{approach}'")
        approach = None

    metadata = {
        "path": path,
        "relative": repo_relative(root, path),
        "date": check_record_date(path, raw, errors),
        "outcome": outcome,
        "approach": approach,
        "nodes": optional_string_list(raw, "nodes", context, errors),
        "artifacts": optional_string_list(raw, "artifacts", context, errors),
        "retires": optional_string_list(raw, "retires", context, errors),
        "supersedes": optional_string_list(raw, "supersedes", context, errors),
        "candidates": [],
        "promotes": [],
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

    if "promotes" in raw:
        value = raw["promotes"]
        if not isinstance(value, list):
            errors.append(f"{context}.promotes: must be a list")
            value = []
        for index, entry in enumerate(value):
            where = f"{context}.promotes[{index}]"
            if not isinstance(entry, dict):
                errors.append(f"{where}: must be a mapping with 'candidate' and 'node'")
                continue
            for field in sorted(set(entry) - PROMOTION_FIELDS):
                errors.append(f"{where}: unknown field '{field}'")
            candidate_id = entry.get("candidate")
            node_id = entry.get("node")
            if not isinstance(candidate_id, str) or not CANDIDATE_ID_RE.match(candidate_id):
                errors.append(f"{where}.candidate: want 'cand:<slug>', got '{candidate_id}'")
                continue
            if not isinstance(node_id, str) or not node_id.strip():
                errors.append(f"{where}.node: must name the ledger node it became")
                continue
            metadata["promotes"].append({"candidate": candidate_id, "node": node_id})

    declared = [entry["id"] for entry in metadata["candidates"]]
    if bool(declared) != (outcome == "candidate"):
        errors.append(
            f"{context}: outcome 'candidate' and a non-empty 'candidates' list require "
            "each other; every other outcome carries none"
        )
    if not metadata["nodes"] and not declared and approach is None:
        errors.append(
            f"{context}: must engage a ledger node, name a portfolio approach, or "
            "propose a candidate"
        )
    return metadata


def check_supersession(root: Path, records: list[dict], directory: str, genre: str,
                       errors: list[str]) -> dict[str, list[str]]:
    """Validate one genre's supersession links; map each superseded record to its heirs.

    A record may only supersede an earlier record of its own genre — a later summary
    replaces an earlier one, never the reverse.

    The order is consulted only where it is real — different days, or two timestamps.
    Unordered same-day relations are checked directly for cycles.

    The result maps superseded path to the records that replaced it, so a reader is told
    what to read *instead* rather than only that something is stale. Membership tests
    against the returned mapping behave as they did against a set.
    """
    moment = {record["relative"]: record_instant(record["date"]) for record in records}
    superseded: dict[str, list[str]] = {}
    edges: dict[str, list[str]] = {}
    for record in records:
        context = f"{record['path']}.supersedes"
        for reference in record["supersedes"]:
            resolved = contained_path(root, reference, directory, context, errors,
                                      suffix=".md")
            if resolved is None:
                continue
            target = repo_relative(root, resolved)
            if target == record["relative"]:
                errors.append(f"{context}: a record cannot supersede itself")
            elif target not in moment:
                errors.append(f"{context}: '{reference}' is not {genre}")
            elif strictly_after(moment[target], moment[record["relative"]]):
                errors.append(
                    f"{context}: '{reference}' is not older than this record; "
                    "supersession only ever points backwards"
                )
            else:
                superseded.setdefault(target, []).append(record["relative"])
                edges.setdefault(record["relative"], []).append(target)

    for cycle in _cycles(edges):
        errors.append(
            f"{directory}: supersession cycle {' -> '.join(cycle)}; supersession only "
            "ever points backwards. Records dated the same day are not ordered by "
            "filename — give them UTC timestamps (YYYY-MM-DDTHH:MM:SSZ) to order them"
        )

    for heirs in superseded.values():
        heirs.sort()
    return superseded


def _cycles(edges: dict[str, list[str]]) -> list[list[str]]:
    """Every cycle reachable in a supersession graph, each reported once.

    Same-day records carry no usable order, so acyclicity is checked explicitly here.
    Iterative depth-first search with an
    explicit stack: the graph is tiny, but a recursive walk over an append-only archive
    that only ever grows is a limit waiting to be hit.
    """
    found: list[list[str]] = []
    seen: set[str] = set()
    for start in sorted(edges):
        if start in seen:
            continue
        stack = [(start, iter(sorted(edges.get(start, ()))))]
        path = [start]
        on_path = {start}
        while stack:
            node, children = stack[-1]
            child = next(children, None)
            if child is None:
                stack.pop()
                on_path.discard(path.pop())
                seen.add(node)
                continue
            if child in on_path:
                cut = path[path.index(child):] + [child]
                if cut not in found:
                    found.append(cut)
                continue
            if child in seen:
                continue
            stack.append((child, iter(sorted(edges.get(child, ())))))
            path.append(child)
            on_path.add(child)
    return found


def check(root: Path, node_ids: set[str], approach_ids: set[str] | None,
          errors: list[str]) -> dict:
    """Validate every dated checkpoint; return live candidates and the record index.

    A candidate leaves the live list two ways: a later checkpoint retires it, or a later
    checkpoint promotes it to a ledger node. The log itself is never rewritten
    (CLAUDE.md constraint 6), so "live" is derived here rather than recorded anywhere.
    """
    directory = root / EXPLORATIONS
    records: list[dict] = []
    if not directory.is_dir():
        return {"records": [], "candidates": [], "promoted": {}, "superseded": {}}

    declared: dict[str, dict] = {}
    retired: dict[str, tuple[tuple[str, str], str]] = {}
    promoted: dict[str, dict] = {}

    # Read everything first, then walk it in the partial chronological order supplied by
    # dates and timestamps. A filename slug is never treated as an event clock.
    for path in sorted(directory.rglob("*.md")):
        if path.name == "README.md":
            continue
        metadata = _read_metadata(path, root, errors)
        if metadata is None:
            continue
        metadata["moment"] = record_instant(metadata["date"])
        records.append(metadata)
    records.sort(key=lambda item: (item["moment"], item["relative"]))

    for metadata in records:
        path = metadata["path"]
        moment = metadata["moment"]
        context = str(path)
        relative = metadata["relative"]

        for node_id in metadata["nodes"]:
            if node_id not in node_ids:
                errors.append(f"{context}.nodes: '{node_id}' is not a ledger node id")

        approach = metadata["approach"]
        if approach is not None:
            if approach_ids is None:
                errors.append(
                    f"{context}.approach: '{approach}' names an approach, but this "
                    "repository has no research/program/portfolio.yaml"
                )
            elif approach not in approach_ids:
                errors.append(f"{context}.approach: '{approach}' is not a portfolio approach")

        for reference in metadata["artifacts"]:
            contained_path(
                root, reference, RUNS, f"{context}.artifacts", errors,
                outside=f"'{reference}' must be an artifact under {RUNS}/",
            )

        for candidate in metadata["candidates"]:
            candidate_id = candidate["id"]
            if candidate_id in node_ids:
                errors.append(
                    f"{context}.candidates: '{candidate_id}' is already a ledger node; a "
                    "candidate is not a node (CLAUDE.md constraint 7)"
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
                    "moment": moment,
                }

        for promotion in metadata["promotes"]:
            candidate_id, node_id = promotion["candidate"], promotion["node"]
            if node_id not in node_ids:
                errors.append(
                    f"{context}.promotes: '{node_id}' is not a ledger node id; a "
                    "promotion is complete only once the node exists"
                )
            if candidate_id in {entry["id"] for entry in metadata["candidates"]}:
                errors.append(
                    f"{context}.promotes: '{candidate_id}' is proposed by this same "
                    "checkpoint; a candidate is promoted by a later one"
                )
            elif candidate_id in promoted:
                errors.append(
                    f"{context}.promotes: '{candidate_id}' was already promoted in "
                    f"{promoted[candidate_id]['source']}"
                )
            elif candidate_id in retired:
                errors.append(
                    f"{context}.promotes: '{candidate_id}' was already retired in "
                    f"{retired[candidate_id][1]}"
                )
            else:
                promoted[candidate_id] = {
                    "node": node_id, "source": relative, "moment": moment,
                    "date": metadata["date"],
                }

        for candidate_id in metadata["retires"]:
            if candidate_id in promoted:
                errors.append(
                    f"{context}.retires: '{candidate_id}' was promoted to "
                    f"'{promoted[candidate_id]['node']}' in "
                    f"{promoted[candidate_id]['source']}; promotion already ends it"
                )
            elif candidate_id in {entry["id"] for entry in metadata["candidates"]}:
                errors.append(
                    f"{context}.retires: '{candidate_id}' is proposed by this same checkpoint"
                )
            elif candidate_id in retired:
                errors.append(
                    f"{context}.retires: '{candidate_id}' was already retired in "
                    f"{retired[candidate_id][1]}"
                )
            else:
                retired[candidate_id] = (moment, relative)

    # "Before" here means demonstrably before: different days, or two timestamps. Two
    # untimed records dated the same day are not ordered, so a same-day proposal and
    # promotion — the ordinary shape of a productive session — is accepted rather than
    # judged on its filenames.
    for candidate_id, (moment, source) in sorted(retired.items()):
        if candidate_id not in declared:
            errors.append(f"{source}.retires: '{candidate_id}' was never proposed")
        elif strictly_after(declared[candidate_id]["moment"], moment):
            errors.append(
                f"{source}.retires: '{candidate_id}' is retired before "
                f"{declared[candidate_id]['source']} proposes it"
            )

    for candidate_id, promotion in sorted(promoted.items()):
        if candidate_id not in declared:
            errors.append(f"{promotion['source']}.promotes: '{candidate_id}' was never proposed")
        elif strictly_after(declared[candidate_id]["moment"], promotion["moment"]):
            errors.append(
                f"{promotion['source']}.promotes: '{candidate_id}' is promoted before "
                f"{declared[candidate_id]['source']} proposes it"
            )
        else:
            promotion["statement"] = declared[candidate_id]["statement"]

    superseded = check_supersession(root, records, EXPLORATIONS, "a checkpoint", errors)
    return {
        "records": records,
        "candidates": [entry for candidate_id, entry in sorted(declared.items())
                       if candidate_id not in retired and candidate_id not in promoted],
        "promoted": promoted,
        "superseded": superseded,
    }


def check_audit_supersession(root: Path, archive: dict[str, dict],
                             errors: list[str]) -> set[str]:
    """Apply the same supersession relation to non-certifying audit reports.

    A proof review is a certification event and keeps ``follows_up``; only audits, whose
    findings genuinely go stale, may be superseded.
    """
    records = []
    for relative, metadata in sorted(archive.items()):
        if metadata.get("type") != "audit":
            continue
        records.append({
            "relative": relative,
            "path": metadata["path"],
            "date": metadata.get("date"),
            "supersedes": metadata.get("supersedes", []),
        })
    return check_supersession(root, records, "research/reviews", "an audit", errors)
