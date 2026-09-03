"""numerics: list the targets, or run one into a research artifact.

Once ``research/runs/`` holds artifacts a target id is public, and renaming one breaks the
trail back from an exploration to its evidence. The CLI therefore carries no aliases.
"""
from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    from .targets import REGISTRY

    parser = argparse.ArgumentParser(prog="numerics", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="show targets and their available run profiles")

    run_parser = sub.add_parser("run", help="run a target's battery -> a research/runs artifact")
    run_parser.add_argument("target", choices=sorted(REGISTRY), help="target id")
    run_parser.add_argument("--profile", default="standard",
                            help="target-owned run profile (default: standard; see 'list')")
    run_parser.add_argument("--seed", type=int, default=0)
    run_parser.add_argument("--out", default=None,
                            help="artifact path under research/runs/ "
                                 "(default research/runs/<timestamp>-<target>.jsonl)")

    args = parser.parse_args(argv)

    if args.cmd == "list":
        for name, spec in REGISTRY.items():
            mode = "stochastic" if spec.stochastic else "deterministic"
            print(f"{name:14} {mode:13} profiles={','.join(spec.profiles)}  {spec.summary}")
        return 0

    from . import artifact
    out = args.out
    if out is not None:
        # The production CLI writes only into the archive. `artifact.run(out=...)` stays
        # unconstrained so test helpers can write to a temporary directory, but an
        # artifact outside research/runs/ is one no reader and no checker will ever see.
        try:
            out = artifact.confine_to_runs(out)
        except ValueError as exc:
            parser.error(str(exc))
    try:
        path = artifact.run(args.target, seed=args.seed, profile=args.profile, out=out)
    except ValueError as exc:
        parser.error(str(exc))
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
