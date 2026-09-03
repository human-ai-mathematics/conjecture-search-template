#!/usr/bin/env python3
"""Scaffold the routine artifacts of a search from templates/.

This is the repository's writer. ``scripts/check.py`` reads and never writes, and the two
stayed separate on purpose: a validator that edits the tree it is judging is a validator
nobody can trust twice.

    python3 scripts/new.py brief --target q:main
    python3 scripts/new.py portfolio --target q:main
    python3 scripts/new.py checkpoint first-attempt --node q:main
    python3 scripts/new.py dossier lem:key
    python3 scripts/new.py module 01-reductions --node lem:key --kind lemma
    python3 scripts/new.py node lem:key --kind lemma        # prints; writes nothing
    python3 scripts/new.py role numerics                    # installs a capability pack

Nothing here overwrites an existing file: a scaffold refuses and says what is already
there. And nothing here edits research/program/ledger.yaml — that file has exactly one
writer (CLAUDE.md constraint 1), so ``node`` prints a block for the orchestrator to paste
rather than reaching into it.

Standard library only, so it works before the checker's own dependency is installed.
"""
from __future__ import annotations

import argparse
import datetime
import re
import subprocess
import sys
from pathlib import Path

#: The repository this scaffolder writes into. ``--root`` retargets it, which is how the
#: tests exercise it without writing into the repository they are testing.
DEFAULT_ROOT = Path(__file__).resolve().parents[1]

NODE_ID_RE = re.compile(r"^[a-z][a-z0-9]*:[a-z0-9][a-z0-9-]*$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
KINDS = (
    "theorem", "lemma", "proposition", "corollary", "conjecture", "question",
    "definition", "assumption", "obstruction", "example",
)


def fail(message: str) -> int:
    print(f"new.py: {message}", file=sys.stderr)
    return 1


def render(root: Path, template: str, substitutions: dict[str, str]) -> str:
    text = (root / "templates" / template).read_text(encoding="utf-8")
    for token, value in substitutions.items():
        text = text.replace("{{" + token + "}}", value)
    return text


def write(root: Path, relative: str, body: str, next_step: str) -> int:
    """Write one new file, or refuse. Never clobbers; append-only planes depend on it."""
    path = root / relative
    if path.exists():
        return fail(f"{relative} already exists — edit it, or delete it first")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    print(f"wrote {relative}")
    print(f"next: {next_step}")
    return 0


def today(timestamp: bool) -> str:
    """The record's ``date``, optionally a UTC timestamp.

    Two records dated the same day are deliberately *unordered* — a filename is not a
    clock — so a checkpoint that must be ordered against another asks for a timestamp.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%SZ" if timestamp else "%Y-%m-%d")


def cmd_brief(args: argparse.Namespace) -> int:
    return write(
        args.root, "research/program/brief.md",
        render(args.root, "brief.md", {"TARGET_NODE": args.target}),
        "fill in every section, then 'python3 scripts/check.py ready'",
    )


def cmd_portfolio(args: argparse.Namespace) -> int:
    slug = args.target.split(":", 1)[-1]
    return write(
        args.root, "research/program/portfolio.yaml",
        render(args.root, "portfolio.yaml", {"TARGET_NODE": args.target, "SLUG": slug}),
        "name the real families and routes, then 'python3 scripts/check.py portfolio'. "
        "Only the synthesizer writes this file from here on",
    )


def cmd_checkpoint(args: argparse.Namespace) -> int:
    stamp = today(args.timestamp)
    title = args.slug.replace("-", " ").capitalize()
    return write(
        args.root, f"research/explorations/{stamp[:10]}-{args.slug}.md",
        render(args.root, "checkpoint.md", {
            "DATE": stamp,
            "NODE": args.node or "<ledger node id this engaged>",
            "TITLE": title,
        }),
        "record what was tried and what it costs the next agent, then "
        "'python3 scripts/check.py --lane checkpoints'",
    )


def cmd_dossier(args: argparse.Namespace) -> int:
    file_id = args.node.replace(":", "-")
    return write(
        args.root, f"solutions/{file_id}.tex",
        render(args.root, "solution.tex", {"NODE": args.node, "FILE_ID": file_id}),
        f"prove it, compile it (cd solutions && latexmk -pdf -outdir=../build "
        f"{file_id}.tex), then ask an orchestrator for a proofs[] "
        "record. Certification is the ledger's, never this file's",
    )


def cmd_module(args: argparse.Namespace) -> int:
    node = args.node or "<node id>"
    return write(
        args.root, f"modules/{args.slug}.tex",
        render(args.root, "module.tex", {
            "SLUG": args.slug,
            "TITLE": args.title or args.slug.replace("-", " ").capitalize(),
            "NODE": node,
            "KIND": args.kind,
        }),
        f"add it to main.tex with \\subfile{{modules/{args.slug}}}, then give every "
        "claim label a ledger node ('python3 scripts/new.py node <id> --kind <kind>')",
    )


def cmd_node(args: argparse.Namespace) -> int:
    """Print a ledger node. Deliberately does not write: constraint 1, one writer."""
    print(render(args.root, "node.yaml", {
        "NODE": args.node,
        "KIND": args.kind,
        "FILE": args.file,
    }).split("\n\n", 1)[1].rstrip())
    print()
    print("# ^ paste under 'nodes:' in research/program/ledger.yaml. The orchestrator owns\n"
          "#   that file (CLAUDE.md constraint 1), so this command does not write it.")
    return 0


def cmd_role(args: argparse.Namespace) -> int:
    packs = args.root / "packs"
    source = packs / args.pack / f"{args.pack}.md"
    if not source.is_file():
        available = sorted(p.name for p in packs.iterdir() if p.is_dir()) if packs.is_dir() else []
        return fail(
            f"no capability pack '{args.pack}'; available: {', '.join(available) or 'none'}"
        )
    agents = args.root / ".claude/agents"
    destination = agents / f"{args.pack}.md"
    if destination.exists():
        return fail(f".claude/agents/{args.pack}.md is already installed")
    agents.mkdir(parents=True, exist_ok=True)
    destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"wrote .claude/agents/{args.pack}.md")
    # The Codex adapters are generated, so an installed role needs one before the roles
    # lane will pass. A repository that deleted .codex/ wants no adapters and gets none.
    # The roster in MAINTAINING.md already links the pack by path, so nothing else is owed.
    code = 0
    if (args.root / ".codex/agents").is_dir():
        checker = Path(__file__).resolve().parent / "check.py"
        code = subprocess.run(
            # Scoped to the roles lane: installing a role says nothing about whether the
            # rest of the repository is green, and it should not report on it.
            [sys.executable, str(checker), "--root", str(args.root),
             "--lane", "roles", "--write-codex"],
            capture_output=True, text=True,
        ).returncode
        if code == 0:
            print(f"wrote .codex/agents/{args.pack}.toml")
    print("next: 'python3 scripts/check.py --lane roles' to confirm, then assign it")
    return code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scaffold a search artifact from templates/",
        epilog="scripts/check.py validates; this writes. See templates/README.md.",
    )
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT,
                        help="repository to scaffold into (default: this script's own)")
    sub = parser.add_subparsers(dest="command", required=True)

    brief = sub.add_parser("brief", help="the problem brief")
    brief.add_argument("--target", required=True, help="the ledger node this search aims at")
    brief.set_defaults(handler=cmd_brief)

    portfolio = sub.add_parser("portfolio", help="the search portfolio")
    portfolio.add_argument("--target", required=True, help="the ledger node this search aims at")
    portfolio.set_defaults(handler=cmd_portfolio)

    checkpoint = sub.add_parser("checkpoint", help="a dated durable record")
    checkpoint.add_argument("slug")
    checkpoint.add_argument("--node", help="a ledger node this engaged")
    checkpoint.add_argument("--timestamp", action="store_true",
                            help="stamp a UTC time, to order it against another record "
                                 "written the same day")
    checkpoint.set_defaults(handler=cmd_checkpoint)

    dossier = sub.add_parser("dossier", help="a standalone proof dossier")
    dossier.add_argument("node")
    dossier.set_defaults(handler=cmd_dossier)

    module = sub.add_parser("module", help="a manuscript module")
    module.add_argument("slug")
    module.add_argument("--node", help="the claim label it will carry")
    module.add_argument("--kind", default="theorem", choices=KINDS)
    module.add_argument("--title")
    module.set_defaults(handler=cmd_module)

    node_cmd = sub.add_parser("node", help="print a ledger node (writes nothing)")
    node_cmd.add_argument("node")
    node_cmd.add_argument("--kind", required=True, choices=KINDS)
    node_cmd.add_argument("--file", default="00-overview.tex",
                          help="the file under modules/ holding its label")
    node_cmd.set_defaults(handler=cmd_node)

    role = sub.add_parser("role", help="install an optional capability pack")
    role.add_argument("pack")
    role.set_defaults(handler=cmd_role)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    for field, pattern, want in (("target", NODE_ID_RE, "a node id like 'q:main'"),
                                 ("node", NODE_ID_RE, "a node id like 'lem:key'"),
                                 ("slug", SLUG_RE, "a lowercase slug like 'first-attempt'")):
        value = getattr(args, field, None)
        # `module --slug` is a filename and may carry a numeric prefix; `node` is optional
        # on checkpoint and module, where it is prose guidance rather than an id.
        if isinstance(value, str) and not pattern.match(value):
            return fail(f"{field} '{value}': want {want}")
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
