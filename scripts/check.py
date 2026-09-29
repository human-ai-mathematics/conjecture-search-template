#!/usr/bin/env python3
"""Validate this repository's research state and print a one-screen summary.

    uv run scripts/check.py                  # this repository, manuscript included
    uv run scripts/check.py --fast           # research state only: no MyST build
    uv run scripts/check.py --root example   # another tree, e.g. the worked example
    uv run scripts/check.py --fingerprint solutions/thm-main.md   # for a review or acceptance
    uv run scripts/check.py --stamp site/results.md   # after rereading a site page
    uv run scripts/check.py --site-strict    # before publishing: a stale page is an error

Exit 0 = clean, 1 = errors. A stale site page is a warning (WARN) unless --site-strict. A green run establishes structure only, never that a proof
is correct. Reading the manuscript runs 'myst build --site', whose output lands in the
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

from checks import analyze, fingerprint, stamp  # noqa: E402


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
    if report["pages"]:
        print(f"site: {report['pages']} page(s), {len(report['warnings'])} stale warning(s)")
        if report["unmentioned"]:
            print(f"site: no page rests on {', '.join(report['unmentioned'])}")
    if report["fast"]:
        print("fast: manuscript not read; anchors and statement fingerprints unchecked")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=None,
                        help="repository root to validate (default: this one)")
    parser.add_argument("--fast", action="store_true",
                        help="skip the MyST build: research state only")
    parser.add_argument("--fingerprint", nargs="+", metavar="DOSSIER",
                        help="print the fingerprints a review or acceptance of these "
                             "dossiers records, and check nothing else")
    parser.add_argument("--stamp", nargs="+", metavar="PAGE",
                        help="record in these site pages the current status and fingerprint "
                             "of what they rest on, date them today, and check nothing else")
    parser.add_argument("--site-strict", action="store_true",
                        help="a stale site page is an error, not a warning: for publishing")
    args = parser.parse_args(argv)
    if args.stamp:
        written, errors = stamp(args.root, args.stamp)
        for error in errors:
            print("FAIL", error)
        for page in written:
            print("stamped", page)
        return 1 if errors else 0
    if args.fingerprint:
        recorded, errors = fingerprint(args.root, args.fingerprint)
        for error in errors:
            print("FAIL", error)
        if errors:
            return 1
        print(yaml.safe_dump({"fingerprints": recorded}, sort_keys=False), end="")
        return 0
    report = analyze(args.root, fast=args.fast)
    if args.site_strict:
        report["errors"] += report["warnings"]
    for error in report["errors"]:
        print("FAIL", error)
    if not args.site_strict:
        for warning in report["warnings"]:
            print("WARN", warning)
    summary(report)
    if report["errors"]:
        print(f"{len(report['errors'])} error(s)")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
