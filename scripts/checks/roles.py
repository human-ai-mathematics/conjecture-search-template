"""The roles lane: canonical Claude role definitions, assignment lenses, and adapters.

The roster is the set of ``.claude/agents/*.md`` files: adding a role is a one-file
operation. Each role's frontmatter is self-describing, so no list of role names is
duplicated here or in any configuration file. Codex cannot read the Markdown, so this
lane also owns generation of ``.codex/agents/*.toml`` and rejects a stale adapter.

``.claude/lenses/*.md`` holds the assignment lenses. A lens is one strategy a role can be
pointed at; it has no tools and no write surface of its own, so it is not a role and gets
no adapter. Both clients read a lens from disk at run time, which is what keeps a
four-strategy role from paying for all four on every invocation. The link is checked in
both directions: a lens nobody declares and a declared lens that does not exist are both
errors.
"""
from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

CLAUDE_AGENTS = Path(".claude/agents")
CLAUDE_LENSES = Path(".claude/lenses")

#: Files in .claude/agents/ that document the roster rather than declare a role.
#: README.md is the runtime contract every role body must reference;
#: MAINTAINING.md is the maintainer's roster and extension guide.
RUNTIME_CONTRACT = "README.md"
ROSTER = "MAINTAINING.md"
NOT_ROLES = frozenset({RUNTIME_CONTRACT, ROSTER})
CODEX_AGENTS = Path(".codex/agents")

WRITE_TOOLS = {"Edit", "Write"}
REQUIRED_FRONTMATTER = ("name", "description", "tools", "read_only", "reasoning")
REQUIRED_LENS_FRONTMATTER = ("name", "role")
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
    relative: str


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
    return metadata, "".join(lines[closing + 1:])


def load_roles(root: Path, errors: list[str]) -> dict[str, Role]:
    roles: dict[str, Role] = {}
    directory = root / CLAUDE_AGENTS
    paths = sorted(directory.glob("*.md"))
    if not [path for path in paths if path.name not in NOT_ROLES]:
        errors.append(f"{CLAUDE_AGENTS}/ declares no role")

    for path in paths:
        if path.name in NOT_ROLES:
            continue
        relative = path.relative_to(root).as_posix()
        try:
            metadata, body = _parse_frontmatter(path)
        except (OSError, UnicodeError, ValueError) as exc:
            errors.append(f"{relative}: {exc}")
            continue

        missing_fields = [key for key in REQUIRED_FRONTMATTER if not metadata.get(key)]
        if missing_fields:
            errors.append(f"{relative}: missing fields {missing_fields}")
            continue
        name = metadata["name"]
        if name != path.stem:
            errors.append(f"{relative}: name '{name}' must match filename stem")
        if name in roles:
            errors.append(f"{relative}: duplicate role name '{name}'")
            continue
        client_model_fields = {"model", "model_reasoning_effort"}.intersection(metadata)
        if client_model_fields:
            errors.append(
                f"{relative}: client-specific fields {sorted(client_model_fields)} belong "
                "in an adapter, not canonical frontmatter"
            )

        tools = tuple(part.strip() for part in metadata["tools"].split(",") if part.strip())

        raw_read_only = metadata["read_only"].strip().lower()
        if raw_read_only not in BOOLEANS:
            errors.append(
                f"{relative}: read_only must be 'true' or 'false', "
                f"got '{metadata['read_only']}'"
            )
            continue
        read_only = BOOLEANS[raw_read_only]
        if read_only and WRITE_TOOLS.intersection(tools):
            errors.append(f"{relative}: read-only role declares a write tool")

        reasoning = metadata["reasoning"].strip()
        if reasoning not in REASONING_EFFORTS:
            errors.append(
                f"{relative}: reasoning must be one of {sorted(REASONING_EFFORTS)}, "
                f"got '{reasoning}'"
            )
            continue
        if ".claude/agents/README.md" not in body:
            errors.append(f"{relative}: does not load the shared execution contract")
        if "## Report" not in body:
            errors.append(f"{relative}: missing role-specific Report section")

        roles[name] = Role(name, metadata["description"], tools, read_only, reasoning,
                           body, path, relative)
    return roles


def _validate_lenses(root: Path, roles: dict[str, Role], errors: list[str]) -> dict[str, str]:
    """Check the lens files against the roles that declare them, both directions.

    A lens is not a role: it inherits every permission from the role it belongs to, so the
    only things worth checking are that it is well formed and that it is actually reachable.
    An orphan lens is dead prose nobody will load; a declared lens that does not exist is a
    role contract pointing at nothing.
    """
    directory = root / CLAUDE_LENSES
    declared_by_roles = {
        name: sorted(set(re.findall(r"\.claude/lenses/([A-Za-z0-9._-]+)\.md", role.body))
                     - {"README"})
        for name, role in roles.items()
    }
    if not directory.is_dir():
        # Returning early here let a role's lens declarations dangle unchecked, which is
        # the one arrangement where a researcher is told to load a file nobody ships.
        for name, references in sorted(declared_by_roles.items()):
            for reference in references:
                errors.append(
                    f"{roles[name].relative}: declares lens '{reference}', but "
                    f"{CLAUDE_LENSES}/ does not exist"
                )
        return {}

    lenses: dict[str, str] = {}
    for path in sorted(directory.glob("*.md")):
        if path.name == RUNTIME_CONTRACT:
            continue
        relative = path.relative_to(root).as_posix()
        try:
            metadata, _body = _parse_frontmatter(path)
        except (OSError, UnicodeError, ValueError) as exc:
            errors.append(f"{relative}: {exc}")
            continue
        missing_fields = [key for key in REQUIRED_LENS_FRONTMATTER if not metadata.get(key)]
        if missing_fields:
            errors.append(f"{relative}: missing fields {missing_fields}")
            continue
        if metadata["name"] != path.stem:
            errors.append(
                f"{relative}: name '{metadata['name']}' must match filename stem"
            )
        owner = metadata["role"]
        if owner not in roles:
            errors.append(f"{relative}: role '{owner}' is not a role")
            continue
        lenses[relative] = owner

    for relative, owner in sorted(lenses.items()):
        if relative not in roles[owner].body:
            errors.append(
                f"{relative}: no role declares this lens; "
                f"{roles[owner].relative} must reference it or the file is dead prose"
            )
    for name, references in sorted(declared_by_roles.items()):
        for reference in references:
            declared = (CLAUDE_LENSES / f"{reference}.md").as_posix()
            if lenses.get(declared) != name:
                errors.append(
                    f"{roles[name].relative}: declares lens '{reference}', which is not "
                    f"a lens belonging to '{name}'"
                )
    return lenses


def render_codex_adapter(role: Role) -> str:
    sandbox_mode = "read-only" if role.read_only else "workspace-write"
    return "\n".join([
        f"# Generated from {role.relative} by scripts/check.py.",
        "# Edit the canonical Markdown and regenerate; do not edit this file directly.",
        f"name = {json.dumps(role.name, ensure_ascii=False)}",
        f"description = {json.dumps(role.description, ensure_ascii=False)}",
        f"model = {json.dumps(CODEX_MODEL)}",
        f"model_reasoning_effort = {json.dumps(role.reasoning)}",
        f"sandbox_mode = {json.dumps(sandbox_mode)}",
        f"developer_instructions = {json.dumps(role.body, ensure_ascii=False)}",
        "",
    ])


def write_codex_adapters(root: Path, roles: dict[str, Role]) -> list[str]:
    """Regenerate the Codex adapters, removing any that no longer have a role."""
    directory = root / CODEX_AGENTS
    if directory.is_symlink():
        return [
            f"{CODEX_AGENTS} is a symlink; replace it with a real directory before "
            "generating Codex TOML adapters"
        ]
    directory.mkdir(parents=True, exist_ok=True)
    for name, role in sorted(roles.items()):
        (directory / f"{name}.toml").write_text(render_codex_adapter(role), encoding="utf-8")
    for path in sorted(directory.glob("*.toml")):
        if path.stem not in roles:
            path.unlink()
    return []


def _validate_roster(root: Path, roles: dict[str, Role], errors: list[str]) -> None:
    """The roster table names every role and nothing else.

    It lives in the maintainer's guide rather than the runtime contract: a role loads
    README.md to execute a task and never needs the table of its colleagues.
    """
    path = root / CLAUDE_AGENTS / ROSTER
    relative = (CLAUDE_AGENTS / ROSTER).as_posix()
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errors.append(f"{relative}: {exc}")
        return
    linked = set(re.findall(r"\]\(([A-Za-z0-9._-]+)\.md\)", text))
    for name in sorted(roles):
        if name not in linked:
            errors.append(f"{relative}: roster does not link role '{name}'")
    for name in sorted(linked - set(roles) - {stem.removesuffix(".md") for stem in NOT_ROLES}):
        errors.append(f"{relative}: roster links '{name}.md', which is not a role")


def _validate_codex_adapters(root: Path, roles: dict[str, Role], errors: list[str]) -> None:
    directory = root / CODEX_AGENTS
    if directory.is_symlink():
        errors.append(f"{CODEX_AGENTS} must be a real directory, not a symlink")
        return
    if not directory.is_dir():
        errors.append(f"{CODEX_AGENTS} directory is missing")
        return

    adapter_paths = sorted(directory.glob("*.toml"))
    adapter_stems = {path.stem for path in adapter_paths}
    if adapter_stems != set(roles):
        missing = sorted(set(roles) - adapter_stems)
        extra = sorted(adapter_stems - set(roles))
        if missing:
            errors.append(f"Codex adapters missing: {missing}")
        if extra:
            errors.append(f"unexpected Codex adapters: {extra}")

    for path in adapter_paths:
        role = roles.get(path.stem)
        if role is None:
            continue
        relative = path.relative_to(root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
            parsed = tomllib.loads(text)
        except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
            errors.append(f"{relative}: {exc}")
            continue
        for field in ("name", "description", "developer_instructions"):
            if not parsed.get(field):
                errors.append(f"{relative}: missing required Codex field '{field}'")
        if text != render_codex_adapter(role):
            errors.append(
                f"{relative}: stale or hand-edited; run "
                "'python3 scripts/check.py --write-codex'"
            )


def check(root: Path, errors: list[str], *, write_codex: bool = False) -> dict[str, Role]:
    """Validate the role roster and its adapters; ``.claude/agents/`` absent means skip."""
    if not (root / CLAUDE_AGENTS).is_dir():
        return {}
    before = len(errors)
    roles = load_roles(root, errors)
    if write_codex and len(errors) == before:
        errors.extend(write_codex_adapters(root, roles))
    _validate_roster(root, roles, errors)
    _validate_lenses(root, roles, errors)
    _validate_codex_adapters(root, roles, errors)
    return roles
