"""Search state: the brief, the portfolio of routes, and the checkpoint log.

None of this is mathematical truth, so none of it is in the ledger. It only points into
the ledger by id: the brief's target, a route's blocker. A
statement not yet stable enough to be a node is a *candidate*, proposed in a checkpoint's
``candidates:`` and ended by a later ``closes:``; the log is append-only, so which
candidates are live is derived here and recorded nowhere. So is where each route was last
discussed: the latest checkpoint that names it, which is where a resumed session looks.
"""
from __future__ import annotations

import re
from pathlib import Path

from .common import (contained_path, load_yaml, markdown_records, one_of,
                     read_front_matter, string_list)

BRIEF = Path("research/program/brief.md")
PORTFOLIO = Path("research/program/portfolio.yaml")
EXPLORATIONS = "research/explorations"
RUNS = "research/runs"

APPROACH_ID_RE = re.compile(r"^ap:[a-z0-9][a-z0-9-]*$")
CANDIDATE_ID_RE = re.compile(r"^cand:[a-z0-9][a-z0-9-]*$")
APPROACH_FIELDS = {"id", "objective", "state", "blocker", "reopen_if", "next"}
APPROACH_STATES = {"active", "blocked", "closed"}
CHECKPOINT_FIELDS = {"artifacts", "candidates", "closes"}
SETTLED = {"proved", "refuted"}


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def brief_target(root: Path, nodes: dict[str, dict], errors: list[str]) -> str | None:
    path = root / BRIEF
    if not path.is_file():
        return None
    raw = read_front_matter(path, "brief", errors)
    if raw is None:
        return None
    for field in sorted(set(raw) - {"target"}):
        errors.append(f"{BRIEF}: unknown field '{field}'")
    target = raw.get("target")
    if not isinstance(target, str) or target not in nodes:
        errors.append(f"{BRIEF}.target: '{target}' is not a ledger node")
        return None
    return target


def load_portfolio(root: Path, errors: list[str]) -> dict[str, dict] | None:
    """The routes by id, or ``None`` when there is no portfolio."""
    path = root / PORTFOLIO
    if not path.is_file():
        return None
    doc = load_yaml(path, PORTFOLIO, errors)
    if doc is None:
        return {}
    for field in sorted(set(doc) - {"approaches"}):
        errors.append(f"{PORTFOLIO}: unknown top-level field '{field}'")
    raw = doc.get("approaches") or []
    if not isinstance(raw, list):
        errors.append(f"{PORTFOLIO}.approaches: must be a list")
        return {}
    approaches: dict[str, dict] = {}
    for index, approach in enumerate(raw):
        aid = approach.get("id") if isinstance(approach, dict) else None
        if not isinstance(aid, str) or not APPROACH_ID_RE.match(aid):
            errors.append(f"{PORTFOLIO}: approach #{index + 1} needs an id 'ap:<slug>'")
            continue
        if aid in approaches:
            errors.append(f"{PORTFOLIO}: duplicate approach '{aid}'")
            continue
        approaches[aid] = approach
        where = f"{PORTFOLIO} {aid}"
        for field in sorted(set(approach) - APPROACH_FIELDS):
            errors.append(f"{where}: unknown field '{field}'")
        if not _text(approach.get("objective")):
            errors.append(f"{where}.objective: one sentence saying what the route tries")
        if "next" in approach and not _text(approach["next"]):
            errors.append(f"{where}.next: the next test that would move the route")
        state = approach.get("state")
        if not one_of(state, APPROACH_STATES):
            errors.append(f"{where}.state: want one of {sorted(APPROACH_STATES)}")
        if state == "blocked" and not _text(approach.get("blocker")):
            errors.append(f"{where}.blocker: required when blocked")
        for field in ("blocker", "reopen_if"):
            if state != "blocked" and field in approach:
                errors.append(f"{where}.{field}: only for a blocked route")
    return approaches


def read_checkpoints(root: Path, nodes: dict[str, dict],
                     errors: list[str]) -> tuple[dict[str, dict], list[Path]]:
    """Validate the log, in date order; return every proposed candidate by id — its
    ``statement``, its ``source`` and whether a later checkpoint ``closed`` it — and the
    log."""
    proposed: dict[str, dict] = {}
    closed: set[str] = set()
    log = markdown_records(root, EXPLORATIONS, errors)
    for path in log:
        raw = read_front_matter(path, "checkpoint", errors)
        if raw is None:
            continue
        context = str(path)
        # Before this checkpoint's own proposals: it closes only what an earlier one proposed.
        for cid in string_list(raw, "closes", context, errors):
            if cid in closed:
                errors.append(f"{context}.closes: '{cid}' is already closed")
            elif cid not in proposed:
                errors.append(f"{context}.closes: '{cid}' was not proposed by an earlier "
                              "checkpoint")
            closed.add(cid)
        for field in sorted(set(raw) - CHECKPOINT_FIELDS):
            errors.append(f"{context}: unknown field '{field}'")

        for reference in string_list(raw, "artifacts", context, errors):
            contained_path(root, reference, RUNS, f"{context}.artifacts", errors)

        candidates = raw.get("candidates") or []
        if not isinstance(candidates, list):
            errors.append(f"{context}.candidates: must be a list")
            candidates = []
        for entry in candidates:
            cid = entry.get("id") if isinstance(entry, dict) else None
            if not isinstance(cid, str) or not CANDIDATE_ID_RE.match(cid):
                errors.append(f"{context}.candidates: want entries {{id: cand:<slug>, statement}}")
            elif set(entry) != {"id", "statement"} or not _text(entry["statement"]):
                errors.append(f"{context}.candidates {cid}: needs exactly an id and a statement")
            elif cid in proposed:
                errors.append(f"{context}.candidates: '{cid}' was already proposed in "
                              f"{proposed[cid]['source']}")
            else:
                proposed[cid] = {"statement": entry["statement"], "source": context}
    for cid in sorted(set(proposed) & set(nodes)):
        errors.append(f"{proposed[cid]['source']}: candidate '{cid}' is also a node id")
    return {cid: {**entry, "closed": cid in closed}
            for cid, entry in sorted(proposed.items())}, log


def last_mention(root: Path, route: str, log: list[Path]) -> str | None:
    """The latest checkpoint whose text names ``route``."""
    pattern = re.compile(rf"(?<![\w:-]){re.escape(route)}(?![\w-])")
    for path in reversed(log):
        try:
            if pattern.search(path.read_text(encoding="utf-8")):
                return path.relative_to(root).as_posix()
        except (OSError, UnicodeError):
            continue  # already reported while reading the log
    return None


def check(root: Path, nodes: dict[str, dict], errors: list[str]) -> dict:
    target = brief_target(root, nodes, errors)
    approaches = load_portfolio(root, errors)
    proposed, log = read_checkpoints(root, nodes, errors)
    candidates = {cid: entry for cid, entry in proposed.items() if not entry["closed"]}
    for aid, approach in sorted((approaches or {}).items()):
        blocker = approach.get("blocker")
        if not _text(blocker):
            continue
        if blocker not in nodes and blocker not in candidates:
            errors.append(f"{PORTFOLIO} {aid}.blocker: '{blocker}' is neither a ledger node "
                          "nor a live candidate")
        elif one_of(nodes.get(blocker, {}).get("status"), SETTLED):
            errors.append(f"{PORTFOLIO} {aid}.blocker: '{blocker}' is now "
                          f"{nodes[blocker]['status']}; reopen or close the route")
    status = nodes.get(target, {}).get("status")
    if one_of(status, SETTLED):
        active = sorted(a for a, r in (approaches or {}).items() if r.get("state") == "active")
        if active:
            errors.append(f"{PORTFOLIO}: the target '{target}' is {status}; close "
                          f"{', '.join(active)}")
    return {"target": target, "approaches": approaches or {}, "candidates": candidates,
            "mentions": {aid: last_mention(root, aid, log) for aid in approaches or {}},
            "latest": log[-1].relative_to(root).as_posix() if log else None}
