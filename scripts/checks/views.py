"""Derived views over a validated repository.

Nothing here stores anything. Every view is computed from the ledger, the portfolio and
the checkpoint log at the moment it is asked for, which is why no role is allowed to
keep a second copy of the frontier, the reverse dependency graph, or the live candidate
list anywhere in the repository.
"""
from __future__ import annotations

import sys
from collections import Counter

import yaml

from .common import PLANES, as_list
from .ledger import applicability_blockers


def summary(report: dict, planes: tuple[str, ...] = PLANES) -> None:
    """The stable structural summary printed by the default command."""
    ledgers = report["ledgers"]
    total = sum(len(item["nodes"]) for item in ledgers)
    error_count = sum(len(report["errors"][plane]) for plane in planes)
    print(
        f"\n{len(ledgers)} ledger(s), {total} nodes, {len(report['labels'])} labels. "
        f"{error_count} error(s)."
    )
    for item in sorted(ledgers, key=lambda entry: (entry["program"], str(entry["path"]))):
        counts = Counter(str(node.get("status")) for node in item["nodes"].values())
        statuses = ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))
        print(f"  [{item['program']}] {len(item['nodes'])} nodes — {statuses}")

    live_portfolio = report.get("portfolio")
    if live_portfolio is not None:
        print(
            f"  portfolio: {len(live_portfolio['families'])} family(ies), "
            f"{len(live_portfolio['approaches'])} approach(es) — "
            "see 'check.py portfolio'"
        )
    live = report.get("candidates") or []
    if live:
        print(f"  {len(live)} live candidate(s) — see 'check.py candidates'")
    artifacts = report.get("artifacts") or []
    if artifacts:
        print(f"  {len(artifacts)} run artifact(s) under research/runs/")
    if report.get("roles"):
        print(f"  {len(report['roles'])} agent role(s)")


def candidates(report: dict) -> None:
    """List the candidate statements no checkpoint has retired yet.

    These are not ledger nodes and carry no status. A stable, reusable candidate earns a
    node and a manuscript statement by an orchestrator decision (CLAUDE.md constraint 8).
    """
    live = report.get("candidates") or []
    if not live:
        print("No live candidate statements.")
        return
    for entry in live:
        print(f"{entry['id']}  ({entry['date']}, {entry['source']})")
        print(f"  {entry['statement']}")


def status(report: dict) -> None:
    """The unresolved frontier derived from ledger state."""
    frontier_statuses = {"open", "refuted"}
    for item in sorted(report["ledgers"], key=lambda entry: entry["program"]):
        groups: dict[str, dict[str, list[str]]] = {}
        for nid, node in item["nodes"].items():
            node_status = node.get("status")
            if node_status not in frontier_statuses:
                if node_status == "proved" and applicability_blockers(nid, item["nodes"]):
                    node_status = "applicability-blocked"
                else:
                    continue
            group = str(node.get("route", item["program"]))
            groups.setdefault(group, {}).setdefault(str(node_status), []).append(nid)
        for group, statuses in sorted(groups.items()):
            label = item["program"] if group == item["program"] else f"{item['program']}/{group}"
            print(f"[{label}]")
            for node_status, node_ids in sorted(statuses.items()):
                print(f"  {node_status} ({len(node_ids)}): {', '.join(sorted(node_ids))}")


def node(report: dict, reference: str) -> bool:
    """One node and its derived consumers, without storing a reverse graph."""
    matches: list[tuple[dict, str, dict]] = []
    for item in report["ledgers"]:
        for nid, entry in item["nodes"].items():
            if reference in {nid, f"{item['program']}/{nid}"}:
                matches.append((item, nid, entry))
    if not matches:
        print(f"No ledger node matches '{reference}'.", file=sys.stderr)
        return False
    if len(matches) > 1:
        choices = ", ".join(f"{item['program']}/{nid}" for item, nid, _entry in matches)
        print(f"Ambiguous node '{reference}'; use one of: {choices}", file=sys.stderr)
        return False

    item, nid, entry = matches[0]
    print(f"[{item['program']}] {nid}")
    print(yaml.safe_dump(entry, sort_keys=False, allow_unicode=True).rstrip())
    consumers = sorted(
        candidate_id for candidate_id, candidate in item["nodes"].items()
        if nid in as_list(candidate.get("depends_on"))
    )
    print("used_by:", consumers or "[]")
    for field, label in (
        ("assumes", "assumed_by"),
        ("implies", "implied_by"),
        ("refines", "refined_by"),
    ):
        reverse = sorted(
            candidate_id for candidate_id, candidate in item["nodes"].items()
            if nid in as_list(candidate.get(field))
        )
        print(f"{label}:", reverse or "[]")
    print("applicability_blocked_by:", applicability_blockers(nid, item["nodes"]) or "[]")

    live_portfolio = report.get("portfolio")
    if live_portfolio is not None:
        blocking = sorted(
            approach_id for approach_id, approach in live_portfolio["approaches"].items()
            if approach.get("blocker") == nid
        )
        print("blocks_approaches:", blocking or "[]")
    return True


def portfolio(report: dict) -> None:
    """The live search: which routes are running, blocked, saturated, or duplicated."""
    live = report.get("portfolio")
    if live is None:
        print("No search portfolio (research/program/portfolio.yaml).")
        return
    print(f"target: {live['target']}")
    approaches = live["approaches"]
    for family_id, family in sorted(live["families"].items()):
        children = sorted(
            approach_id for approach_id, approach in approaches.items()
            if approach.get("family") == family_id
        )
        counts = Counter(str(approaches[child].get("state")) for child in children)
        breakdown = ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))
        print(f"\n[{family_id}] {family.get('state')}" + (f" — {breakdown}" if breakdown else ""))
        print(f"  {family.get('mechanism')}")
        if family.get("reopen_if"):
            print(f"  reopen if: {family['reopen_if']}")
        if family.get("saturation_checkpoint"):
            print(f"  closed at: {family['saturation_checkpoint']}")
        for child in children:
            approach = approaches[child]
            parent = approach.get("parent")
            print(f"  - {child} [{approach.get('state')}]"
                  + (f" < {parent}" if parent else ""))
            if approach.get("blocker"):
                print(f"      blocked on: {approach['blocker']}")
            if approach.get("reopen_if"):
                print(f"      reopen if: {approach['reopen_if']}")
            for other, kind in approach.get("_related", []):
                print(f"      {kind}: {other}")
            for reference in approach.get("_checkpoints", []):
                print(f"      checkpoint: {reference}")
    orphans = sorted(
        approach_id for approach_id, approach in approaches.items()
        if approach.get("family") not in live["families"]
    )
    if orphans:
        print(f"\napproaches with no family: {', '.join(orphans)}")


def checkpoints(report: dict) -> None:
    """The current heads of durable memory: records nothing later has superseded."""
    memory = report.get("checkpoints") or {}
    records = memory.get("records") or []
    if not records:
        print("No checkpoints recorded.")
        return
    superseded = memory.get("superseded") or set()
    heads = [record for record in records if record["relative"] not in superseded]
    print(f"{len(heads)} current checkpoint(s), {len(superseded)} superseded:")
    for record in sorted(heads, key=lambda item: (item["date"] or "", item["relative"])):
        approach = f" {record['approach']}" if record["approach"] else ""
        nodes = ", ".join(record["nodes"]) or "—"
        print(f"  {record['date']}  {record['outcome']:<11}{approach}  {record['relative']}")
        print(f"      nodes: {nodes}")
    superseded_audits = memory.get("superseded_audits") or set()
    if superseded_audits:
        print(f"\n{len(superseded_audits)} superseded audit(s):")
        for relative in sorted(superseded_audits):
            print(f"  {relative}")
