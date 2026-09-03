#!/usr/bin/env python3
"""Structural checker and derived views for this repository.

One entry point, six planes:

* ``core`` — the claim graph: node schema, the acyclic proof DAG, manuscript anchors,
  the separation of proof dependencies from implication antecedents, and both classes
  of obstruction;
* ``proofs`` — dossiers under ``solutions/`` and the persisted review provenance that
  makes ``mode: agent`` mean something;
* ``checkpoints`` — dated durable memory in ``research/explorations/``, the candidate
  statements it carries, and supersession;
* ``portfolio`` — the problem brief and the live search portfolio;
* ``numerics`` — the provenance headers of the immutable artifacts in
  ``research/runs/``;
* ``roles`` — the agent roster and its generated Codex adapters.

A plane whose files are absent contributes nothing, so an early repository pays for
nothing it is not using.

    python3 scripts/check.py                       # every plane
    python3 scripts/check.py --plane core          # repeatable
    python3 scripts/check.py --write-codex         # regenerate Codex adapters
    python3 scripts/check.py status                # the live frontier
    python3 scripts/check.py node <id>             # one node: deps, consumers, fences
    python3 scripts/check.py candidates            # statements proposed but not nodes
    python3 scripts/check.py portfolio             # families, routes, blockers
    python3 scripts/check.py checkpoints           # current heads of durable memory

Exit 0 = clean, 1 = errors. A green run establishes structure only; it says nothing
about whether a proof is correct (CLAUDE.md constraint 4). Requires PyYAML.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from checks import analyze, failures, views  # noqa: E402
from checks.common import PLANES  # noqa: E402
from checks.ledger import LEDGER_PATH  # noqa: E402

VIEWS = ("status", "node", "candidates", "portfolio", "checkpoints")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate and inspect this repository's research planes",
    )
    parser.add_argument("command", nargs="?", choices=("check", *VIEWS), default="check",
                        help="'check' (default) validates; the rest are derived views")
    parser.add_argument("node_id", nargs="?", help="node id, optionally qualified as program/id")
    parser.add_argument("--plane", action="append", choices=PLANES, dest="planes",
                        help="restrict reporting to one plane; repeatable")
    parser.add_argument("--write-codex", action="store_true",
                        help="regenerate project-scoped Codex adapters from the roles")
    parser.add_argument("--root", type=Path, default=None,
                        help="repository root to validate (default: this checker's own)")
    args = parser.parse_args(argv)
    if args.command != "node" and args.node_id:
        parser.error(f"{args.command} does not accept a node id")
    if args.write_codex and args.command != "check":
        parser.error("--write-codex is only valid for a check run")

    report = analyze(root=args.root, configured_ledger=LEDGER_PATH,
                     write_codex=args.write_codex)
    planes = tuple(dict.fromkeys(args.planes)) if args.planes else PLANES
    errors = failures(report, planes)
    for error in errors:
        print("FAIL", error)
    if errors:
        views.summary(report, planes)
        return 1

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
        views.summary(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
