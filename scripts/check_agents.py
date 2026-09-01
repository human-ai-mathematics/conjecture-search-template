#!/usr/bin/env python3
"""Validate canonical Claude roles and generated Codex agent adapters.

The roster is the set of ``.claude/agents/*.md`` files: adding a role is a
one-file operation. Each role's frontmatter is self-describing, so no list of
role names is duplicated here or in any configuration file.

Run from the repo root: ``python3 scripts/check_agents.py [--write-codex]``.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLAUDE_AGENTS = ROOT / ".claude" / "agents"
CODEX_AGENTS = ROOT / ".codex" / "agents"

WRITE_TOOLS = {"Edit", "Write"}
REQUIRED_FRONTMATTER = ("name", "description", "tools", "read_only", "reasoning")
BOOLEANS = {"true": True, "false": False}
REASONING_EFFORTS = {"high", "ultra"}
CODEX_MODEL = "gpt-5.6-sol"


@dataclass(frozen=True)
class Role:
    name: str
    description: str
    tools: tuple[str, ...]
    read_only: bool
    reasoning: str
    body: str
    path: Path


def _parse_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing opening YAML frontmatter delimiter")
    try:
        closing = next(i for i, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration as exc:
        raise ValueError("missing closing YAML frontmatter delimiter") from exc

    metadata: dict[str, str] = {}
    for lineno, line in enumerate(lines[1:closing], 2):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            raise ValueError(f"line {lineno}: expected 'key: value'")
        key, value = stripped.split(":", 1)
        key = key.strip()
        if key in metadata:
            raise ValueError(f"line {lineno}: duplicate key '{key}'")
        metadata[key] = value.strip()
    return metadata, "".join(lines[closing + 1 :])


def load_roles() -> tuple[dict[str, Role], list[str]]:
    errors: list[str] = []
    roles: dict[str, Role] = {}
    paths = sorted(CLAUDE_AGENTS.glob("*.md"))
    if not [path for path in paths if path.name != "README.md"]:
        errors.append(".claude/agents/ declares no role")

    for path in paths:
        if path.name == "README.md":
            continue
        try:
            metadata, body = _parse_frontmatter(path)
        except (OSError, UnicodeError, ValueError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")
            continue

        missing_fields = [key for key in REQUIRED_FRONTMATTER if not metadata.get(key)]
        if missing_fields:
            errors.append(f"{path.relative_to(ROOT)}: missing fields {missing_fields}")
            continue
        name = metadata["name"]
        if name != path.stem:
            errors.append(f"{path.relative_to(ROOT)}: name '{name}' must match filename stem")
        if name in roles:
            errors.append(f"{path.relative_to(ROOT)}: duplicate role name '{name}'")
            continue
        client_model_fields = {"model", "model_reasoning_effort"}.intersection(metadata)
        if client_model_fields:
            errors.append(
                f"{path.relative_to(ROOT)}: client-specific fields "
                f"{sorted(client_model_fields)} belong in an adapter, not canonical frontmatter"
            )

        tools = tuple(part.strip() for part in metadata["tools"].split(",") if part.strip())

        raw_read_only = metadata["read_only"].strip().lower()
        if raw_read_only not in BOOLEANS:
            errors.append(
                f"{path.relative_to(ROOT)}: read_only must be 'true' or 'false', "
                f"got '{metadata['read_only']}'"
            )
            continue
        read_only = BOOLEANS[raw_read_only]
        if read_only and WRITE_TOOLS.intersection(tools):
            errors.append(f"{path.relative_to(ROOT)}: read-only role declares a write tool")

        reasoning = metadata["reasoning"].strip()
        if reasoning not in REASONING_EFFORTS:
            errors.append(
                f"{path.relative_to(ROOT)}: reasoning must be one of "
                f"{sorted(REASONING_EFFORTS)}, got '{reasoning}'"
            )
            continue
        if ".claude/agents/README.md" not in body:
            errors.append(f"{path.relative_to(ROOT)}: does not load the shared execution contract")
        if "## Report" not in body:
            errors.append(f"{path.relative_to(ROOT)}: missing role-specific Report section")

        roles[name] = Role(name, metadata["description"], tools, read_only, reasoning,
                           body, path)

    return roles, errors


def render_codex_adapter(role: Role) -> str:
    sandbox_mode = "read-only" if role.read_only else "workspace-write"
    reasoning_effort = role.reasoning
    relative_source = role.path.relative_to(ROOT).as_posix()
    return "\n".join(
        [
            f"# Generated from {relative_source} by scripts/check_agents.py.",
            "# Edit the canonical Markdown and regenerate; do not edit this file directly.",
            f"name = {json.dumps(role.name, ensure_ascii=False)}",
            f"description = {json.dumps(role.description, ensure_ascii=False)}",
            f"model = {json.dumps(CODEX_MODEL)}",
            f"model_reasoning_effort = {json.dumps(reasoning_effort)}",
            f"sandbox_mode = {json.dumps(sandbox_mode)}",
            f"developer_instructions = {json.dumps(role.body, ensure_ascii=False)}",
            "",
        ]
    )


def write_codex_adapters(roles: dict[str, Role]) -> list[str]:
    if CODEX_AGENTS.is_symlink():
        return [
            ".codex/agents is a symlink; replace it with a real directory before generating "
            "Codex TOML adapters"
        ]
    CODEX_AGENTS.mkdir(parents=True, exist_ok=True)
    for name, role in sorted(roles.items()):
        (CODEX_AGENTS / f"{name}.toml").write_text(
            render_codex_adapter(role), encoding="utf-8"
        )
    return []


def validate_readme(roles: dict[str, Role]) -> list[str]:
    errors: list[str] = []
    path = CLAUDE_AGENTS / "README.md"
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [f"{path.relative_to(ROOT)}: {exc}"]
    linked = set(re.findall(r"\]\(([A-Za-z0-9._-]+)\.md\)", text))
    for name in sorted(roles):
        if name not in linked:
            errors.append(f"{path.relative_to(ROOT)}: roster does not link role '{name}'")
    for name in sorted(linked - set(roles) - {"README"}):
        errors.append(f"{path.relative_to(ROOT)}: roster links '{name}.md', which is not a role")
    return errors


def validate_codex_adapters(roles: dict[str, Role]) -> list[str]:
    errors: list[str] = []
    if CODEX_AGENTS.is_symlink():
        return [".codex/agents must be a real directory, not a symlink"]
    if not CODEX_AGENTS.is_dir():
        return [".codex/agents directory is missing"]

    adapter_paths = sorted(CODEX_AGENTS.glob("*.toml"))
    adapter_stems = {path.stem for path in adapter_paths}
    role_names = set(roles)
    if adapter_stems != role_names:
        missing = sorted(role_names - adapter_stems)
        extra = sorted(adapter_stems - role_names)
        if missing:
            errors.append(f"Codex adapters missing: {missing}")
        if extra:
            errors.append(f"unexpected Codex adapters: {extra}")

    for path in adapter_paths:
        role = roles.get(path.stem)
        if role is None:
            continue
        try:
            text = path.read_text(encoding="utf-8")
            parsed = tomllib.loads(text)
        except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")
            continue
        for field in ("name", "description", "developer_instructions"):
            if not parsed.get(field):
                errors.append(f"{path.relative_to(ROOT)}: missing required Codex field '{field}'")
        expected = render_codex_adapter(role)
        if text != expected:
            errors.append(
                f"{path.relative_to(ROOT)}: stale or hand-edited; run "
                "'python3 scripts/check_agents.py --write-codex'"
            )
    return errors


def collect_errors() -> list[str]:
    roles, errors = load_roles()
    errors.extend(validate_readme(roles))
    errors.extend(validate_codex_adapters(roles))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write-codex",
        action="store_true",
        help="regenerate project-scoped Codex TOML adapters from canonical Markdown roles",
    )
    args = parser.parse_args(argv)

    roles, errors = load_roles()
    if args.write_codex and not errors:
        errors.extend(write_codex_adapters(roles))
    if not errors:
        errors.extend(validate_readme(roles))
        errors.extend(validate_codex_adapters(roles))

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"{len(errors)} error(s)")
        return 1
    print(f"agent definitions: 0 errors ({len(roles)} roles)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
