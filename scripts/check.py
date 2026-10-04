#!/usr/bin/env python3
"""Validate this repository's research state and print a one-screen summary.

    uv run scripts/check.py                  # this repository, manuscript included
    uv run scripts/check.py --impact         # group stale certifications by changed item
    uv run scripts/check.py --diff           # the same, each with its diff since certified
    uv run scripts/check.py --fast           # research state only: no MyST build
    uv run scripts/check.py --root example   # another tree, e.g. the worked example
    uv run scripts/check.py --fingerprint solutions/thm-main.md   # for a review or acceptance
    uv run scripts/check.py --drafts         # the draft dossiers, which are not published
    uv run scripts/check.py --statements     # before and after the writer: must not change

Exit 0 = clean, 1 = errors. A green run establishes structure only, never that a proof is
correct. Reading the manuscript runs 'myst build --site', whose output lands in the
gitignored _build/; --fast skips it, and with it the manuscript anchors and the statement
fingerprints. Needs MyST ('npm ci') unless --fast; uv provides PyYAML from pyproject.toml.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import yaml  # noqa: E402

from checks import ROOT, analyze, fingerprint, history, statements  # noqa: E402


def summary(report: dict) -> None:
    statuses = Counter(str(node.get("status")) for node in report["nodes"].values())
    print(f"nodes: {len(report['nodes'])} "
          f"({', '.join(f'{n} {s}' for s, n in sorted(statuses.items())) or 'none'})")
    if report["target"]:
        target = report["nodes"][report["target"]]
        print(f"target: {report['target']} ({target.get('status')})")
    routes = report["approaches"]
    for aid, route in sorted(routes.items()):
        blocker = f" on {route['blocker']}" if route.get("state") == "blocked" else ""
        seen = report["mentions"].get(aid)
        print(f"route {aid}: {route.get('state')}{blocker}"
              + (f" (last in {seen})" if seen else ""))
        if route.get("state") != "closed" and isinstance(route.get("next"), str):
            print(f"  next: {' '.join(route['next'].split())}")
    for cid, candidate in report["candidates"].items():
        print(f"candidate {cid}: {candidate['statement'].strip().splitlines()[0]}")
    for path in report["drafts"]:
        print(f"draft {path}: no proof record names it")
    if report["latest"]:
        print(f"latest checkpoint: {report['latest']}")
    if report["fast"]:
        print("fast: manuscript not read; anchors and statement fingerprints unchecked")


def print_impact(report: dict, root: Path | None = None, *, diff: bool = False) -> None:
    """Compact mission scope, without repeating mismatch diagnostics or hashes; with
    ``diff``, each changed item's diff since every version a certification recorded."""
    impact = report["impact"]
    print(f"impact: {len(impact)} changed item(s) detected")
    for item, affected in sorted(impact.items()):
        print(f"changed: {item}")
        for node, artifact, source in sorted({
                (entry["node"], entry["artifact"], entry["source"]) for entry in affected}):
            print(f"  {node} | {artifact} | {source}")
        for recorded in diff and sorted({entry["recorded"] for entry in affected}) or ():
            for line in history.diff(root or ROOT, item, recorded):
                print(f"  {line}")
    if report["fast"]:
        print("fast: manuscript not read; anchors and statement fingerprints unchecked")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=None,
                        help="repository root to validate (default: this one)")
    parser.add_argument("--impact", action="store_true",
                        help="group stale certifications by changed item; keep other errors "
                             "and the normal validation exit code")
    parser.add_argument("--diff", action="store_true",
                        help="--impact, with each changed item's diff since the certified "
                             "version, read from Git")
    parser.add_argument("--fast", action="store_true",
                        help="skip the MyST build: research state only")
    parser.add_argument("--fingerprint", nargs="+", metavar="DOSSIER",
                        help="print the fingerprints a review or acceptance of these "
                             "dossiers records, and check nothing else")
    parser.add_argument("--drafts", action="store_true",
                        help="print the draft dossiers, one per line, and check nothing else: "
                             "the pages workflow removes them before it publishes")
    parser.add_argument("--statements", action="store_true",
                        help="print every statement of the manuscript as 'label fingerprint', "
                             "and check nothing else: the output must not change across a "
                             "writer's pass")
    args = parser.parse_args(argv)
    args.impact = args.impact or args.diff
    if args.impact and (args.statements or args.drafts or args.fingerprint):
        parser.error("--impact and --diff cannot be combined with --statements, --drafts or "
                     "--fingerprint")
    if args.statements:
        digests, errors = statements(args.root)
        for error in errors:
            print("FAIL", error)
        for label, digest in digests.items():
            print(label, digest)
        return 1 if errors else 0
    if args.drafts:
        for path in analyze(args.root, fast=True)["drafts"]:
            print(path)
        return 0
    if args.fingerprint:
        recorded, errors = fingerprint(args.root, args.fingerprint)
        for error in errors:
            print("FAIL", error)
        if errors:
            return 1
        print(yaml.safe_dump({"fingerprints": recorded}, sort_keys=False), end="")
        return 0
    report = analyze(args.root, fast=args.fast)
    grouped = {entry["error"] for affected in report["impact"].values()
               for entry in affected} if args.impact else set()
    for error in report["errors"]:
        if error not in grouped:
            print("FAIL", error)
    if args.impact:
        print_impact(report, args.root, diff=args.diff)
    else:
        summary(report)
    if report["errors"]:
        print(f"{len(report['errors'])} error(s)")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
