"""Derived views over a validated repository.

Nothing here stores anything. Every view is computed from the ledger, the portfolio and
the checkpoint log at the moment it is asked for, which is why no role is allowed to
keep a second copy of the frontier, the reverse dependency graph, or the live candidate
list anywhere in the repository.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import yaml

from .common import LANES, as_list, repo_relative
from .ledger import applicability_blockers

#: Strings this template ships that a real repository must have replaced. Each is a
#: literal placeholder, never a guess at what a filled-in value looks like: a readiness
#: gate that infers is worse than none, and a real program may legitimately own a node
#: called ``…:example``.
PLACEHOLDERS: tuple[tuple[str, str, str], ...] = (
    ("README.md", "{{REPO_TITLE}}", "name the repository"),
    ("main.tex", "<Document title>", "set the manuscript title"),
    ("main.tex", "<author>", "set the manuscript author"),
    ("main.tex", "Replace this abstract.", "write the abstract"),
    ("README.md", "# Instantiating this template",
     "delete the instantiation section once its steps are done"),
    ("research/program/brief.md", "<!-- This is the worked example's brief",
     "rewrite the brief for this repository's target"),
    ("research/program/brief.md", "Write the logical negation, with quantifier order intact",
     "write the exact negation in the brief"),
    ("research/program/brief.md", "Two lists, both explicit.",
     "write what counts as a complete proof and a complete refutation"),
)

BRIEF = "research/program/brief.md"


def summary(report: dict, lanes: tuple[str, ...] = LANES) -> None:
    """The stable structural summary printed by the default command."""
    ledgers = report["ledgers"]
    total = sum(len(item["nodes"]) for item in ledgers)
    error_count = sum(len(report["errors"][lane]) for lane in lanes)
    print(
        f"\n{len(ledgers)} ledger(s), {total} nodes, {len(report['labels'])} labels. "
        f"{error_count} error(s)."
    )
    for item in sorted(ledgers, key=lambda entry: (entry["program"], str(entry["path"]))):
        counts = Counter(str(node.get("status")) for node in item["nodes"].values())
        statuses = ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))
        breakdown = f" — {statuses}" if statuses else ""
        print(f"  [{item['program']}] {len(item['nodes'])} nodes{breakdown}")

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


def ready(report: dict, root: Path | None) -> bool:
    """Is this repository instantiated, or is it still the shipped template?

    A different question from ``check``. Activation is structural, so an absent optional
    plane is valid and must stay valid — a fresh clone is *correct* and *not ready*.
    This view asks only whether the placeholders are gone and a sustained search has
    something to aim at, and it prints what to do rather than what is wrong.
    """
    base = Path(root) if root is not None else Path(__file__).resolve().parents[2]
    blockers: list[str] = []

    nodes = sum(len(item["nodes"]) for item in report["ledgers"])
    if not nodes:
        blockers.append(
            "research/program/ledger.yaml: no nodes — state the target in modules/ and "
            "give it a node"
        )
    for item in report["ledgers"]:
        where = repo_relative(base, item["path"])
        if item["program"] == "program":
            blockers.append(f"{where}: meta.program is still 'program' — name this program")
        scope = str((item["meta"] or {}).get("scope") or "")
        if "One sentence naming the class of objects" in scope:
            blockers.append(f"{where}: meta.scope is still the shipped sentence")

    if report.get("brief") is None:
        blockers.append(
            f"{BRIEF}: absent — a sustained search opens with a brief naming its target"
        )

    for relative, needle, remedy in PLACEHOLDERS:
        path = base / relative
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            blockers.append(f"{relative}: cannot read: {exc}")
            continue
        if needle in text:
            blockers.append(f"{relative}: {remedy}")

    if blockers:
        print(f"not ready — {len(blockers)} thing(s) to do:")
        for blocker in dict.fromkeys(blockers):
            print(f"  {blocker}")
        print("\nThis is not a defect. A freshly cloned template is correct and not yet")
        print("instantiated; see the instantiation checklist in README.md.")
        return False
    print("ready: the placeholders are gone and the brief names a target in the ledger.")
    print("A green check is still structure only (CLAUDE.md constraint 4).")
    return True


def candidates(report: dict) -> None:
    """List the candidate statements no checkpoint has retired yet.

    These are not ledger nodes and carry no status. A stable, reusable candidate earns a
    node and a manuscript statement by an orchestrator decision (CLAUDE.md constraint 8).
    """
    live = report.get("candidates") or []
    promoted = (report.get("checkpoints") or {}).get("promoted") or {}
    if not live:
        print("No live candidate statements.")
    for entry in live:
        print(f"{entry['id']}  ({entry['date']}, {entry['source']})")
        print(f"  {entry['statement']}")
    if promoted:
        print(f"\n{len(promoted)} promoted — now ledger nodes, no longer candidates:")
        for candidate_id, promotion in sorted(promoted.items()):
            print(f"  {candidate_id} -> {promotion['node']}  "
                  f"({promotion['date']}, {promotion['source']})")


def status(report: dict) -> None:
    """The unresolved frontier derived from ledger state."""
    frontier_statuses = {"open", "refuted"}
    for item in sorted(report["ledgers"], key=lambda entry: entry["program"]):
        statuses: dict[str, list[str]] = {}
        for nid, node in item["nodes"].items():
            node_status = node.get("status")
            if node_status not in frontier_statuses:
                if node_status == "proved" and applicability_blockers(nid, item["nodes"]):
                    node_status = "applicability-blocked"
                else:
                    continue
            statuses.setdefault(str(node_status), []).append(nid)
        if not statuses:
            continue
        print(f"[{item['program']}]")
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
        if family.get("closure_checkpoint"):
            print(f"  closed at: {family['closure_checkpoint']}")
        for child in children:
            approach = approaches[child]
            parent = approach.get("parent")
            print(f"  - {child} [{approach.get('state')}]"
                  + (f" < {parent}" if parent else ""))
            if approach.get("objective"):
                print(f"      {approach['objective'].strip()}")
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
    """The current heads of durable memory, and what replaced everything else.

    Append-only storage keeps provenance but supplies no current reading. Supersession is
    what supplies it, so this view names the *heir* rather than only reporting that a
    record went stale — otherwise the replacement is discoverable only by searching the
    archive, which is the problem supersession exists to solve.
    """
    memory = report.get("checkpoints") or {}
    records = memory.get("records") or []
    superseded = memory.get("superseded") or {}
    if not records:
        print("No checkpoints recorded.")
    else:
        heads = [record for record in records if record["relative"] not in superseded]
        print(f"{len(heads)} current checkpoint(s), {len(superseded)} superseded:")
        for record in sorted(heads, key=lambda item: (item["date"] or "", item["relative"])):
            approach = f" {record['approach']}" if record["approach"] else ""
            nodes = ", ".join(record["nodes"]) or "—"
            print(f"  {record['date']}  {record['outcome']:<11}{approach}  {record['relative']}")
            print(f"      nodes: {nodes}")
        for relative, heirs in sorted(superseded.items()):
            print(f"  superseded  {relative}\n      read instead: {', '.join(heirs)}")

    superseded_audits = memory.get("superseded_audits") or {}
    audits = sorted(
        relative for relative, metadata in (report.get("archive") or {}).items()
        if metadata.get("type") == "audit"
    )
    if not audits:
        return
    heads = [relative for relative in audits if relative not in superseded_audits]
    print(f"\n{len(heads)} current audit(s), {len(superseded_audits)} superseded:")
    for relative in heads:
        print(f"  {relative}")
    for relative, heirs in sorted(superseded_audits.items()):
        print(f"  superseded  {relative}\n      read instead: {', '.join(heirs)}")
