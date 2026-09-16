#!/usr/bin/env python3
"""Structural checker and derived views for this repository.

One entry point, seven validation lanes:

* ``core`` — the claim graph: node schema, the acyclic proof DAG, manuscript anchors as
  MyST parses ``modules/`` (and whatever MyST could not resolve there),
  the separation of proof dependencies from implication antecedents, and both classes
  of fence (``bounded_by`` and ``heuristic_barriers``);
* ``proofs`` — dossiers under ``solutions/`` and the persisted review provenance that
  makes ``mode: agent`` mean something;
* ``checkpoints`` — dated durable memory in ``research/explorations/``, the candidate
  statements it carries, and supersession;
* ``portfolio`` — the problem brief and the live search portfolio;
* ``numerics`` — the provenance headers of the immutable artifacts in
  ``research/runs/``;
* ``roles`` — the agent roster, the model/effort profile table, and the artifacts
  generated from it for both clients;
* ``docs`` — repository-relative Markdown links, so a navigation table cannot point at a
  file that is not there.

A lane is an implementation partition of this checker. It is not one of the three
domains the repository is organized into (mathematical state, search state, durable
evidence) and not one of ``CLAUDE.md``'s activation gates. A lane whose files are
absent contributes nothing, so an early repository pays for nothing it is not using.

    python3 scripts/check.py                       # every lane
    python3 scripts/check.py --lane core           # repeatable
    python3 scripts/check.py --root example        # validate another tree
    python3 scripts/new.py agents                  # restamp roles from profiles.yaml
    python3 scripts/check.py ready                 # can a search start here?
    python3 scripts/check.py publish-ready         # is the manuscript fit to show?
    python3 scripts/check.py status                # the live frontier
    python3 scripts/check.py node <id>             # one node: deps, consumers, fences
    python3 scripts/check.py candidates            # statements proposed but not nodes
    python3 scripts/check.py portfolio             # families, routes, blockers
    python3 scripts/check.py checkpoints           # current heads of durable memory

This command writes nothing the repository tracks: reading the manuscript runs
'myst build --site', whose output lands in the gitignored _build/. Scaffolding a brief, a
portfolio, a checkpoint or a dossier is 'python3 scripts/new.py'.

Exit 0 = clean, 1 = errors. A green run establishes structure only; it says nothing
about whether a proof is correct (CLAUDE.md constraint 4). Requires PyYAML — see the
root pyproject.toml, or 'pip install pyyaml' — and MyST, pinned in package.json and
installed with 'npm ci'.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from checks import analyze, failures, views  # noqa: E402
from checks.common import LANES  # noqa: E402
from checks.ledger import LEDGER_PATH  # noqa: E402

VIEWS = ("ready", "publish-ready", "status", "node", "candidates", "portfolio",
         "checkpoints")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate and inspect this repository's research state",
    )
    parser.add_argument("command", nargs="?", choices=("check", *VIEWS), default="check",
                        help="'check' (default) validates; the rest are derived views")
    parser.add_argument("node_id", nargs="?", help="ledger node id")
    parser.add_argument("--lane", action="append", choices=LANES, dest="lanes",
                        help="restrict reporting to one lane; repeatable")
    parser.add_argument("--root", type=Path, default=None,
                        help="repository root to validate (default: this checker's own)")
    args = parser.parse_args(argv)
    if args.command != "node" and args.node_id:
        parser.error(f"{args.command} does not accept a node id")
    report = analyze(root=args.root, configured_ledger=LEDGER_PATH)
    lanes = tuple(dict.fromkeys(args.lanes)) if args.lanes else LANES
    errors = failures(report, lanes)
    for error in errors:
        print("FAIL", error)
    if errors:
        views.summary(report, lanes)
        return 1

    if args.command == "ready":
        return 0 if views.ready(report, args.root) else 1
    if args.command == "publish-ready":
        return 0 if views.publish_ready(report, args.root) else 1
    if args.command == "status":
        views.status(report)
    elif args.command == "candidates":
        views.candidates(report)
    elif args.command == "portfolio":
        views.portfolio(report)
    elif args.command == "checkpoints":
        views.checkpoints(report)
    elif args.command == "node":
        if not args.node_id:
            parser.error("node requires NODE_ID")
        if not views.node(report, args.node_id):
            return 1
    else:
        views.summary(report, lanes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
