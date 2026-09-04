"""The roles lane: canonical role definitions, assignment lenses, and adapters.

The roster is the set of ``.claude/agents/*.md`` files: adding a role is a one-file
operation. Each role's frontmatter follows Claude Code's published subagent schema, so
the files are ordinary subagent definitions and nothing in them is invented here.

Model and effort are the two variables worth tuning, and they live in exactly one place:
``.claude/agents/profiles.yaml``. Both clients' artifacts are generated from it — the
frontmatter block of each role file, and each ``.codex/agents/*.toml`` adapter — and this
lane rejects either one when it drifts. That is the only arrangement in which a profile
means the same thing on both clients: Claude resolves frontmatter *above* its
``CLAUDE_CODE_SUBAGENT_MODEL`` environment variable, while Codex resolves its ``[agents]``
defaults above the agent file, so relying on each client's native knob would make one
switch override the roles and the other be overridden by them.

The role body below the frontmatter is canonical prose and is never rewritten; only the
frontmatter block is stamped.

``.claude/lenses/*.md`` holds the assignment lenses. A lens is one strategy a role can be
pointed at; it has no tools and no write surface of its own, so it is not a role and gets
no adapter. Both clients read a lens from disk at run time, which is what keeps a
four-strategy role from paying for all four on every invocation — and what keeps lenses
off both clients' `skills` fields, which do not mean the same thing. The link is checked
in both directions: a lens nobody declares and a declared lens that does not exist are
both errors.
"""
from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

from .common import yaml

CLAUDE_AGENTS = Path(".claude/agents")
CLAUDE_LENSES = Path(".claude/lenses")
CODEX_AGENTS = Path(".codex/agents")

#: The one place model and effort are written down, for both clients.
PROFILES = Path(".claude/agents/profiles.yaml")

#: Files in .claude/agents/ that document the roster rather than declare a role.
#: README.md is the runtime contract every role body must reference;
#: MAINTAINING.md is the maintainer's roster and extension guide.
RUNTIME_CONTRACT = "README.md"
ROSTER = "MAINTAINING.md"
NOT_ROLES = frozenset({RUNTIME_CONTRACT, ROSTER})

#: Optional capability packs. A pack is a role a repository installs when its work calls
#: for it — numerical experiment, literature import, repository hygiene — rather than one
#: a fresh clone carries whether or not it is used. `python3 scripts/new.py role <pack>`
#: copies one into .claude/agents/, at which point it is an ordinary role in every
#: respect. The roster in MAINTAINING.md links the packs by path, which is why an
#: installed pack needs no further paperwork. A pack is stamped where it sits, so that
#: installing one lands a file that already agrees with the active profile.
PACKS = Path("packs")

WRITE_TOOLS = {"Edit", "Write"}
REQUIRED_FRONTMATTER = ("name", "description", "tools", "model")
REQUIRED_LENS_FRONTMATTER = ("name", "role")

#: Claude Code's effort scale, and Codex's, which extends it by one rung. The two are
#: validated separately and deliberately differ: `heavy` is `max` on Claude because that
#: is Claude's ceiling, and `ultra` on Codex because that is Codex's.
CLAUDE_EFFORTS = ("low", "medium", "high", "xhigh", "max")
CODEX_EFFORTS = CLAUDE_EFFORTS + ("ultra",)

#: Claude Code model aliases, or a full model id.
CLAUDE_MODEL_ALIASES = ("opus", "sonnet", "haiku", "fable")
CLAUDE_MODEL_ID = re.compile(r"^claude-[A-Za-z0-9._\[\]-]+$")

#: Claude Code's transcript colours. Cosmetic, and Claude-only.
COLORS = ("red", "blue", "green", "yellow", "purple", "orange", "pink", "cyan")

#: Written into Claude frontmatter for an inheriting tier. Codex has no such literal:
#: there, inheriting the parent's setting means omitting the key.
INHERIT = "inherit"

#: Agent names both clients already ship. A role taking one of these shadows a built-in
#: on that client, which is never what a research roster means to do — and `explorer` is
#: close enough to `scout` to be a live temptation.
BUILT_IN_AGENTS = frozenset({
    "default", "worker", "explorer",                      # Codex
    "explore", "plan", "general-purpose", "claude",       # Claude Code
})

PROFILE_KEYS = frozenset({"active", "tiers", "roles", "profiles"})


@dataclass(frozen=True)
class Tier:
    """One resource level, resolved for both clients. ``None`` means inherit."""
    name: str
    claude_model: str | None
    claude_effort: str | None
    codex_model: str | None
    codex_effort: str | None

    @property
    def inherits(self) -> bool:
        return self.claude_model is None


@dataclass(frozen=True)
class Profiles:
    active: str
    tiers: dict[str, Tier]
    read_only: dict[str, bool]
    color: dict[str, str | None]
    assignment: dict[str, str]

    def tier_of(self, role_name: str) -> Tier | None:
        tier = self.assignment.get(role_name)
        return self.tiers.get(tier) if tier else None


@dataclass(frozen=True)
class Role:
    name: str
    description: str
    tools: tuple[str, ...]
    read_only: bool
    color: str | None
    tier: Tier
    body: str
    path: Path
    relative: str

    @property
    def effort(self) -> str | None:
        """The Claude-side effort, or None when the role inherits it."""
        return self.tier.claude_effort


def _parse_frontmatter(path: Path) -> tuple[dict[str, str], str, str]:
    """Return the frontmatter mapping, the body, and the frontmatter block verbatim.

    The block is returned because it is generated: comparing it against what the profile
    table renders is what catches a hand-edited model, a stale effort, and a key nobody
    is supposed to be writing, in one check rather than three.
    """
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
    return metadata, "".join(lines[closing + 1:]), "".join(lines[:closing + 1])


def _tier_client(relative: str, tier: str, client: str, raw: object,
                 efforts: tuple[str, ...], errors: list[str]) -> tuple[str | None, str | None]:
    """Resolve one client's half of a tier. An empty block means inherit."""
    where = f"{relative}: tier '{tier}' / {client}"
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        errors.append(f"{where}: expected a mapping")
        return None, None
    unknown = sorted(set(raw) - {"model", "effort"})
    if unknown:
        errors.append(f"{where}: unknown keys {unknown}")
    model, effort = raw.get("model"), raw.get("effort")
    if model is None and effort is None:
        return None, None
    if model is None or effort is None:
        errors.append(f"{where}: give both 'model' and 'effort', or neither to inherit")
        return None, None
    if not isinstance(model, str) or not isinstance(effort, str):
        errors.append(f"{where}: 'model' and 'effort' must be strings")
        return None, None
    if effort not in efforts:
        errors.append(f"{where}: effort must be one of {list(efforts)}, got '{effort}'")
    if client == "claude":
        if model == INHERIT:
            errors.append(
                f"{where}: write an inheriting tier as an empty block, not "
                f"'model: {INHERIT}'; the literal is a rendering detail of the "
                "Claude frontmatter"
            )
        elif model not in CLAUDE_MODEL_ALIASES and not CLAUDE_MODEL_ID.match(model):
            errors.append(
                f"{where}: model must be one of {list(CLAUDE_MODEL_ALIASES)} or a "
                f"'claude-' id, got '{model}'"
            )
    elif not model:
        errors.append(f"{where}: model must be a non-empty string")
    return model, effort


def load_profiles(root: Path, errors: list[str]) -> Profiles | None:
    """Read the one table that assigns a model and an effort to every role."""
    path = root / PROFILES
    relative = PROFILES.as_posix()
    if not path.is_file():
        errors.append(
            f"{relative}: missing; it is where model and effort are declared for both "
            "clients"
        )
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        errors.append(f"{relative}: {exc}")
        return None
    if not isinstance(data, dict):
        errors.append(f"{relative}: expected a mapping")
        return None
    unknown = sorted(set(data) - PROFILE_KEYS)
    if unknown:
        errors.append(f"{relative}: unknown top-level keys {unknown}")

    tiers: dict[str, Tier] = {}
    raw_tiers = data.get("tiers")
    if not isinstance(raw_tiers, dict) or not raw_tiers:
        errors.append(f"{relative}: 'tiers' must be a non-empty mapping")
        raw_tiers = {}
    for name, raw in raw_tiers.items():
        if not isinstance(raw, dict):
            errors.append(f"{relative}: tier '{name}' must be a mapping")
            continue
        unknown_clients = sorted(set(raw) - {"claude", "codex"})
        if unknown_clients:
            errors.append(f"{relative}: tier '{name}': unknown clients {unknown_clients}")
        claude_model, claude_effort = _tier_client(
            relative, name, "claude", raw.get("claude"), CLAUDE_EFFORTS, errors)
        codex_model, codex_effort = _tier_client(
            relative, name, "codex", raw.get("codex"), CODEX_EFFORTS, errors)
        if (claude_model is None) != (codex_model is None):
            errors.append(
                f"{relative}: tier '{name}' inherits on one client and pins on the "
                "other; a tier means one thing or it is not a tier"
            )
        tiers[name] = Tier(name, claude_model, claude_effort, codex_model, codex_effort)

    read_only: dict[str, bool] = {}
    color: dict[str, str | None] = {}
    raw_roles = data.get("roles")
    if not isinstance(raw_roles, dict) or not raw_roles:
        errors.append(f"{relative}: 'roles' must be a non-empty mapping")
        raw_roles = {}
    for name, raw in raw_roles.items():
        if not isinstance(raw, dict):
            errors.append(f"{relative}: role '{name}' must be a mapping")
            continue
        unknown_facts = sorted(set(raw) - {"read_only", "color"})
        if unknown_facts:
            errors.append(f"{relative}: role '{name}': unknown keys {unknown_facts}")
        if not isinstance(raw.get("read_only"), bool):
            errors.append(f"{relative}: role '{name}': read_only must be true or false")
            continue
        chosen = raw.get("color")
        if chosen is not None and chosen not in COLORS:
            errors.append(
                f"{relative}: role '{name}': color must be one of {list(COLORS)}, "
                f"got '{chosen}'"
            )
            chosen = None
        read_only[name] = raw["read_only"]
        color[name] = chosen

    raw_profiles = data.get("profiles")
    if not isinstance(raw_profiles, dict) or not raw_profiles:
        errors.append(f"{relative}: 'profiles' must be a non-empty mapping")
        raw_profiles = {}
    # A profile names the occasion, a tier names a resource level, and a bare word in
    # this file has to say which layer it belongs to. Sharing a name reads as a
    # tautology on every assignment line that uses it.
    shadowed = sorted(set(raw_profiles) & set(tiers))
    if shadowed:
        errors.append(
            f"{relative}: profile name(s) {shadowed} also name a tier; keep the two "
            "vocabularies disjoint"
        )
    for profile, raw in sorted(raw_profiles.items()):
        if not isinstance(raw, dict):
            errors.append(f"{relative}: profile '{profile}' must be a mapping")
            continue
        missing = sorted(set(read_only) - set(raw))
        extra = sorted(set(raw) - set(read_only))
        if missing:
            errors.append(f"{relative}: profile '{profile}' assigns no tier to {missing}")
        if extra:
            errors.append(f"{relative}: profile '{profile}' assigns tiers to {extra}, "
                          "which are not roles")
        for role_name, tier in sorted(raw.items()):
            if tier not in tiers:
                errors.append(
                    f"{relative}: profile '{profile}' puts '{role_name}' on tier "
                    f"'{tier}', which is not defined"
                )

    active = data.get("active")
    if not isinstance(active, str) or active not in raw_profiles:
        errors.append(
            f"{relative}: 'active' must name a profile, one of "
            f"{sorted(raw_profiles)}, got {active!r}"
        )
        return None
    assignment = {name: tier for name, tier in raw_profiles[active].items()
                  if isinstance(tier, str) and tier in tiers}
    return Profiles(active, tiers, read_only, color, assignment)


def render_claude_frontmatter(role: Role) -> str:
    """The generated frontmatter block, in Claude Code's published subagent schema."""
    lines = [
        "---",
        f"name: {role.name}",
        f"description: {role.description}",
        f"tools: {', '.join(role.tools)}",
    ]
    if role.tier.inherits:
        # Claude Code spells "use the parent's model" as a value; effort then falls
        # through to the session's own setting, so the key is left off entirely.
        lines.append(f"model: {INHERIT}")
    else:
        lines.append(f"model: {role.tier.claude_model}")
        lines.append(f"effort: {role.tier.claude_effort}")
    if role.color:
        lines.append(f"color: {role.color}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def render_codex_adapter(role: Role) -> str:
    """The generated Codex adapter. Codex inherits by omission, not by a literal."""
    sandbox_mode = "read-only" if role.read_only else "workspace-write"
    lines = [
        f"# Generated from {role.relative} by scripts/new.py agents.",
        "# Model and effort come from .claude/agents/profiles.yaml; edit that table or",
        "# the canonical Markdown and regenerate. Do not edit this file directly.",
        f"name = {json.dumps(role.name, ensure_ascii=False)}",
        f"description = {json.dumps(role.description, ensure_ascii=False)}",
    ]
    if not role.tier.inherits:
        lines.append(f"model = {json.dumps(role.tier.codex_model)}")
        lines.append(f"model_reasoning_effort = {json.dumps(role.tier.codex_effort)}")
    lines.append(f"sandbox_mode = {json.dumps(sandbox_mode)}")
    lines.append(f"developer_instructions = {json.dumps(role.body, ensure_ascii=False)}")
    lines.append("")
    return "\n".join(lines)


def _load_role_file(path: Path, root: Path, profiles: Profiles,
                    errors: list[str]) -> Role | None:
    """Parse one role file and resolve it against the active profile."""
    relative = path.relative_to(root).as_posix()
    try:
        metadata, body, _block = _parse_frontmatter(path)
    except (OSError, UnicodeError, ValueError) as exc:
        errors.append(f"{relative}: {exc}")
        return None

    missing_fields = [key for key in REQUIRED_FRONTMATTER if not metadata.get(key)]
    if missing_fields:
        errors.append(f"{relative}: missing fields {missing_fields}")
        return None
    name = metadata["name"]
    if name != path.stem:
        errors.append(f"{relative}: name '{name}' must match filename stem")
    if name.lower() in BUILT_IN_AGENTS:
        errors.append(
            f"{relative}: '{name}' shadows a built-in agent on one of the clients; "
            "choose a name of this roster's own"
        )
    if name not in profiles.read_only:
        errors.append(
            f"{relative}: '{name}' has no entry under 'roles:' in {PROFILES.as_posix()}"
        )
        return None
    tier = profiles.tier_of(name)
    if tier is None:
        errors.append(
            f"{PROFILES.as_posix()}: profile '{profiles.active}' assigns no usable tier "
            f"to '{name}'"
        )
        return None

    tools = tuple(part.strip() for part in metadata["tools"].split(",") if part.strip())
    read_only = profiles.read_only[name]
    if read_only and WRITE_TOOLS.intersection(tools):
        errors.append(f"{relative}: read-only role declares a write tool")
    if ".claude/agents/README.md" not in body:
        errors.append(f"{relative}: does not load the shared execution contract")
    if "## Report" not in body:
        errors.append(f"{relative}: missing role-specific Report section")

    return Role(name, metadata["description"], tools, read_only, profiles.color.get(name),
                tier, body, path, relative)


def load_roles(root: Path, profiles: Profiles, errors: list[str]) -> dict[str, Role]:
    roles: dict[str, Role] = {}
    directory = root / CLAUDE_AGENTS
    paths = sorted(directory.glob("*.md"))
    if not [path for path in paths if path.name not in NOT_ROLES]:
        errors.append(f"{CLAUDE_AGENTS}/ declares no role")

    for path in paths:
        if path.name in NOT_ROLES:
            continue
        role = _load_role_file(path, root, profiles, errors)
        if role is None:
            continue
        if role.name in roles:
            errors.append(f"{role.relative}: duplicate role name '{role.name}'")
            continue
        roles[role.name] = role
    return roles


def load_packs(root: Path, profiles: Profiles, errors: list[str]) -> dict[str, Role]:
    """The uninstalled capability packs, parsed like any other role.

    A pack is stamped where it sits so that `new.py role <pack>` copies in a file that
    already agrees with the active profile, rather than one the roles lane rejects until
    something regenerates it.
    """
    packs: dict[str, Role] = {}
    directory = root / PACKS
    if not directory.is_dir():
        return packs
    for entry in sorted(directory.iterdir()):
        source = entry / f"{entry.name}.md"
        if not entry.is_dir() or not source.is_file():
            continue
        role = _load_role_file(source, root, profiles, errors)
        if role is not None:
            packs[role.name] = role
    return packs


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
            metadata, _body, _block = _parse_frontmatter(path)
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


def _stamp_frontmatter(role: Role) -> None:
    """Rewrite one role file's frontmatter block, leaving the body byte-identical."""
    _metadata, body, block = _parse_frontmatter(role.path)
    rendered = render_claude_frontmatter(role)
    if block != rendered:
        role.path.write_text(rendered + body, encoding="utf-8")


def write_agent_files(root: Path, roles: dict[str, Role], packs: dict[str, Role]) -> list[str]:
    """Regenerate both clients' artifacts from the profile table.

    Role frontmatter is stamped in place; the Codex adapters are rewritten in full, and
    any whose role is gone is removed.
    """
    for role in list(roles.values()) + list(packs.values()):
        try:
            _stamp_frontmatter(role)
        except (OSError, UnicodeError, ValueError) as exc:
            return [f"{role.relative}: {exc}"]

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


def _pack_names(root: Path) -> set[str]:
    """The capability packs on offer, installed or not."""
    directory = root / PACKS
    if not directory.is_dir():
        return set()
    return {entry.name for entry in directory.iterdir()
            if entry.is_dir() and (entry / f"{entry.name}.md").is_file()}


def _validate_roster(root: Path, roles: dict[str, Role], errors: list[str]) -> None:
    """The roster table names every role and nothing else.

    It lives in the maintainer's guide rather than the runtime contract: a role loads
    README.md to execute a task and never needs the table of its colleagues.

    Links are matched by filename stem wherever they point, so the roster's packs table —
    which links ``packs/numerics/numerics.md`` — already accounts for that role once it is
    installed. Installing a pack is then genuinely one command, not a command plus a
    documentation edit the checker would otherwise demand. An uninstalled pack is likewise
    not a stray link, and neither is a lens: the roster is allowed to point at the
    strategies a role can be assigned.
    """
    path = root / CLAUDE_AGENTS / ROSTER
    relative = (CLAUDE_AGENTS / ROSTER).as_posix()
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errors.append(f"{relative}: {exc}")
        return
    linked = {Path(target).stem
              for target in re.findall(r"\]\(([A-Za-z0-9._/-]+)\.md\)", text)}
    for name in sorted(roles):
        if name not in linked:
            errors.append(f"{relative}: roster does not link role '{name}'")
    lenses = {path.stem for path in (root / CLAUDE_LENSES).glob("*.md")}
    known = (set(roles) | _pack_names(root) | lenses
             | {stem.removesuffix(".md") for stem in NOT_ROLES})
    for name in sorted(linked - known):
        errors.append(
            f"{relative}: roster links '{name}.md', which is not a role, a capability "
            "pack, or a lens"
        )


def _validate_frontmatter(roles: dict[str, Role], packs: dict[str, Role],
                          active: str, errors: list[str]) -> None:
    """Every role file's frontmatter is what the profile table renders, exactly.

    One comparison covers a hand-edited model, a stale effort, a reordered key and a key
    nobody is supposed to be writing — the description and the tool list come from the
    file itself, so the rendering is a fixed point of anything legitimately hand-authored.
    """
    for role in sorted(list(roles.values()) + list(packs.values()),
                       key=lambda item: item.relative):
        try:
            _metadata, _body, block = _parse_frontmatter(role.path)
        except (OSError, UnicodeError, ValueError) as exc:  # pragma: no cover - reparse
            errors.append(f"{role.relative}: {exc}")
            continue
        if block != render_claude_frontmatter(role):
            errors.append(
                f"{role.relative}: frontmatter disagrees with "
                f"{PROFILES.as_posix()} (profile '{active}' puts it on tier "
                f"'{role.tier.name}'); run 'python3 scripts/new.py agents'"
            )


def _validate_codex_adapters(root: Path, roles: dict[str, Role], errors: list[str]) -> None:
    """Validate the generated Codex adapters — if this repository ships any.

    Cross-client support is a choice, not a requirement. A repository driven only by
    Claude Code deletes ``.codex/`` and owes nothing; the tree is regenerated in full by
    ``python3 scripts/new.py agents`` whenever it wants one back. What is not optional is
    an adapter that disagrees with the Markdown it was generated from.
    """
    directory = root / CODEX_AGENTS
    if directory.is_symlink():
        errors.append(f"{CODEX_AGENTS} must be a real directory, not a symlink")
        return
    if not directory.is_dir():
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
                "'python3 scripts/new.py agents'"
            )


def check(root: Path, errors: list[str]) -> dict[str, Role]:
    """Validate the role roster and its adapters; ``.claude/agents/`` absent means skip."""
    if not (root / CLAUDE_AGENTS).is_dir():
        return {}
    profiles = load_profiles(root, errors)
    if profiles is None:
        return {}
    roles = load_roles(root, profiles, errors)
    packs = load_packs(root, profiles, errors)
    _validate_roster(root, roles, errors)
    _validate_lenses(root, roles, errors)
    _validate_frontmatter(roles, packs, profiles.active, errors)
    _validate_codex_adapters(root, roles, errors)
    return roles
