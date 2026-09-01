"""numerics: list targets, run fast checks, or emit a numerical research artifact.

A fresh repository has no artifact history to stay compatible with, so the CLI
carries no legacy spellings. Keep it that way: once ``research/runs/`` holds
artifacts, a target id is public and renaming it breaks the archive.
"""
from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    from .targets import REGISTRY

    p = argparse.ArgumentParser(prog="numerics", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="show targets and their available run profiles")

    pc = sub.add_parser("check", help="run fast target-owned calibration/regression checks")
    pc.add_argument("target", nargs="?", choices=sorted(REGISTRY))
    pc.add_argument("--seed", type=int, default=7)

    pr = sub.add_parser("run", help="run a target's battery -> a research/runs artifact")
    pr.add_argument("target", choices=sorted(REGISTRY), help="target id")
    pr.add_argument("--profile", default="standard",
                    help="target-owned run profile (default: standard; see 'numerics list')")
    pr.add_argument("--seed", type=int, default=0)
    pr.add_argument("--out", default=None,
                    help="artifact path (default research/runs/<timestamp>-<target>.jsonl)")

    args = p.parse_args(argv)

    if args.cmd == "list":
        for name, spec in REGISTRY.items():
            mode = "stochastic" if spec.stochastic else "deterministic"
            print(f"{name:14} {mode:13} profiles={','.join(spec.profiles)}  {spec.summary}")
        return 0

    if args.cmd == "check":
        from .selftest import selftest
        return selftest(target=args.target, seed=args.seed)

    if args.cmd == "run":
        from .run import run
        try:
            path = run(args.target, seed=args.seed, profile=args.profile, out=args.out)
        except ValueError as exc:
            p.error(str(exc))
        print(f"wrote {path}")
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
