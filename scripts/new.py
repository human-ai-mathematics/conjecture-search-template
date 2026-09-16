#!/usr/bin/env python3
"""Create routine search artifacts and regenerate derived agent definitions.

This is the repository's writer. ``scripts/check.py`` reads and never writes, and the two
stayed separate on purpose: a validator that edits the tree it is judging is a validator
nobody can trust twice.

    python3 scripts/new.py brief --target conj:main
    python3 scripts/new.py portfolio --target conj:main
    python3 scripts/new.py checkpoint first-attempt --node conj:main
    python3 scripts/new.py dossier lem:key
    python3 scripts/new.py module 01-reductions --node lem:key --kind lemma
    python3 scripts/new.py node lem:key --kind lemma --file 01-reductions.md
    python3 scripts/new.py role numerics                    # installs a capability pack
    python3 scripts/new.py agents                           # regenerate agent files

Scaffolds never overwrite an existing hand-authored file. The ``agents`` command is the
deliberate exception for generated material: it restamps role frontmatter and replaces
Codex adapters from the profile table. Nothing here edits research/program/ledger.yaml —
that file has exactly one writer (CLAUDE.md constraint 1), so ``node`` prints a block for
the orchestrator to paste rather than reaching into it.

Scaffolding uses only the standard library. Agent generation uses the checker's declared
PyYAML dependency because it reads ``.claude/agents/profiles.yaml``.
"""
from __future__ import annotations

import argparse
import datetime
import re
import sys
from pathlib import Path

#: The repository this scaffolder writes into. ``--root`` retargets it, which is how the
#: tests exercise it without writing into the repository they are testing.
DEFAULT_ROOT = Path(__file__).resolve().parents[1]

NODE_ID_RE = re.compile(r"^[a-z][a-z0-9]*:[a-z0-9][a-z0-9-]*$")
APPROACH_ID_RE = re.compile(r"^ap:[a-z0-9][a-z0-9-]*$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
KINDS = (
    "theorem", "lemma", "proposition", "corollary", "conjecture", "definition",
    "example", "assumption",
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
    """Write one new file, or refuse. Never clobbers; append-only records depend on it."""
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
    engagement = (
        f"nodes:\n  - {args.node}" if args.node is not None else f"approach: {args.approach}"
    )
    return write(
        args.root, f"research/explorations/{stamp[:10]}-{args.slug}.md",
        render(args.root, "checkpoint.md", {
            "DATE": stamp,
            "ENGAGEMENT": engagement,
            "TITLE": title,
        }),
        "record what was tried and what it costs the next agent, then "
        "'python3 scripts/check.py --lane checkpoints'",
    )


def cmd_dossier(args: argparse.Namespace) -> int:
    file_id = args.node.replace(":", "-")
    return write(
        args.root, f"solutions/{file_id}.md",
        render(args.root, "solution.md",
               {"NODE": args.node, "FILE_ID": file_id, "DATE": today(False)}),
        "prove it, build it standalone ('npx myst build --pdf' writes "
        f"_build/exports/{file_id}.pdf), then ask an orchestrator for a proofs[] "
        "record. Certification is the ledger's, never this file's",
    )


def cmd_module(args: argparse.Namespace) -> int:
    return write(
        args.root, f"modules/{args.slug}.md",
        render(args.root, "module.md", {
            "SLUG": args.slug,
            "TITLE": args.title or args.slug.replace("-", " ").capitalize(),
            "NODE": args.node,
            "KIND": args.kind,
        }),
        f"run 'python3 scripts/new.py node {args.node} --kind {args.kind} "
        f"--file {args.slug}.md' and paste the result into the ledger. myst.yml "
        "already includes every file under modules/",
    )


def cmd_node(args: argparse.Namespace) -> int:
    """Print a ledger node. Deliberately does not write: constraint 1, one writer."""
    print(render(args.root, "node.yaml", {
        "NODE": args.node,
        "KIND": args.kind,
        "STATUS": "defined" if args.kind == "definition" else "open",
        "FILE": args.file,
    }).split("\n\n", 1)[1].rstrip())
    print()
    print("# ^ paste under 'nodes:' in research/program/ledger.yaml. The orchestrator owns\n"
          "#   that file (CLAUDE.md constraint 1), so this command does not write it.")
    return 0


def generate_agents(root: Path) -> list[str]:
    """Regenerate both clients from the profile table, then validate the result."""
    from checks import roles

    errors: list[str] = []
    profiles = roles.load_profiles(root, errors)
    if profiles is None:
        return errors
    packs = roles.load_packs(root, profiles, errors)
    if errors:
        return errors
    # A capability pack remains canonical after installation. Refresh its active
    # Claude definition before loading the roster, then derive the Codex adapter from
    # that same body below. This prevents a template update from leaving two valid but
    # contradictory copies of one role.
    for name, pack in packs.items():
        installed = root / ".claude/agents" / f"{name}.md"
        if installed.is_file():
            installed.write_text(
                roles.render_claude_frontmatter(pack) + pack.body,
                encoding="utf-8",
            )
    role_definitions = roles.load_roles(root, profiles, errors)
    if errors:
        return errors
    errors.extend(roles.write_agent_files(root, role_definitions, packs))
    if errors:
        return errors
    roles.check(root, errors)
    return errors


def cmd_agents(args: argparse.Namespace) -> int:
    errors = generate_agents(args.root)
    if errors:
        for error in errors:
            print(f"new.py: {error}", file=sys.stderr)
        return 1
    print("restamped .claude agent frontmatter and regenerated .codex adapters")
    print("next: 'python3 scripts/check.py --lane roles' to confirm")
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
    # Both clients' artifacts are generated, so an installed role is restamped from the
    # active profile before the roles lane will pass: its frontmatter carries whatever
    # model and effort .claude/agents/profiles.yaml assigns it, and it gets a Codex
    # adapter if this repository ships any. The roster in MAINTAINING.md already links
    # the pack by path, so nothing else is owed.
    errors = generate_agents(args.root)
    code = 0 if not errors else 1
    for error in errors:
        print(f"new.py: {error}", file=sys.stderr)
    if code == 0 and (args.root / ".codex/agents").is_dir():
        print(f"wrote .codex/agents/{args.pack}.toml")
    print("next: 'python3 scripts/check.py --lane roles' to confirm, then assign it")
    return code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create search artifacts and regenerate derived agent files",
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
    engagement = checkpoint.add_mutually_exclusive_group(required=True)
    engagement.add_argument("--node", help="a ledger node this engaged")
    engagement.add_argument("--approach", help="the portfolio approach this engaged")
    checkpoint.add_argument("--timestamp", action="store_true",
                            help="stamp a UTC time, to order it against another record "
                                 "written the same day")
    checkpoint.set_defaults(handler=cmd_checkpoint)

    dossier = sub.add_parser("dossier", help="a standalone proof dossier")
    dossier.add_argument("node")
    dossier.set_defaults(handler=cmd_dossier)

    module = sub.add_parser("module", help="a manuscript module")
    module.add_argument("slug")
    module.add_argument("--node", required=True, help="the claim label it will carry")
    module.add_argument("--kind", default="theorem", choices=KINDS)
    module.add_argument("--title")
    module.set_defaults(handler=cmd_module)

    node_cmd = sub.add_parser("node", help="print a ledger node (writes nothing)")
    node_cmd.add_argument("node")
    node_cmd.add_argument("--kind", required=True, choices=KINDS)
    node_cmd.add_argument("--file", default="00-overview.md",
                          help="the file under modules/ holding its label")
    node_cmd.set_defaults(handler=cmd_node)

    role = sub.add_parser("role", help="install an optional capability pack")
    role.add_argument("pack")
    role.set_defaults(handler=cmd_role)

    agents = sub.add_parser("agents", help="regenerate agent files from profiles.yaml")
    agents.set_defaults(handler=cmd_agents)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    for field, pattern, want in (("target", NODE_ID_RE, "a node id like 'conj:main'"),
                                 ("node", NODE_ID_RE, "a node id like 'lem:key'"),
                                 ("approach", APPROACH_ID_RE,
                                  "an approach id like 'ap:first-route'"),
                                 ("slug", SLUG_RE, "a lowercase slug like 'first-attempt'")):
        value = getattr(args, field, None)
        if isinstance(value, str) and not pattern.match(value):
            return fail(f"{field} '{value}': want {want}")
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
