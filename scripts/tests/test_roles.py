"""Roles lane: role definitions, lenses, the profile table, and generated artifacts.

These run against a copy of the real `.claude/` and `.codex/` trees, so the shipped
roster, lens set and profile table are what is actually checked.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

REPO = Path(__file__).resolve().parents[2]
CHECK = REPO / "scripts/check.py"
NEW = REPO / "scripts/new.py"


class RoleTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        shutil.copytree(REPO / ".claude", self.root / ".claude")
        shutil.copytree(REPO / ".codex", self.root / ".codex")
        # The roster links the uninstalled capability packs by path, so they are part of
        # the world the roles lane validates.
        shutil.copytree(REPO / "packs", self.root / "packs")

    def tearDown(self):
        self.tempdir.cleanup()

    def run_checker(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CHECK), "--root", str(self.root), "--lane", "roles"],
            cwd=self.root, check=False, capture_output=True, text=True,
        )

    def role_files(self) -> list[Path]:
        return [path for path in sorted((self.root / ".claude/agents").glob("*.md"))
                if path.name not in {"README.md", "MAINTAINING.md"}]

    def profiles_path(self) -> Path:
        return self.root / ".claude/agents/profiles.yaml"

    def read_profiles(self) -> dict:
        return yaml.safe_load(self.profiles_path().read_text(encoding="utf-8"))

    def write_profiles(self, data: dict) -> None:
        """Rewrite the profile table structurally.

        The tests mutate the shipped table rather than matching strings in it, so that
        retuning a tier -- which is the whole point of the file -- does not break the
        suite. Comments are lost, but only in the temporary copy.
        """
        self.profiles_path().write_text(yaml.safe_dump(data, sort_keys=False),
                                        encoding="utf-8")

    def inheriting_profile(self, data: dict) -> str:
        """The profile that pins nothing, found by what it does, not by its name."""
        for profile, assignment in data["profiles"].items():
            if all(not data["tiers"][tier]["claude"] for tier in assignment.values()):
                return profile
        self.fail("the template ships no profile that inherits everything")

    def replace_in_role(self, relative: str, pattern: str, replacement: str) -> None:
        path = self.root / relative
        text = path.read_text(encoding="utf-8")
        replaced, count = re.subn(pattern, replacement, text, count=1,
                                  flags=re.MULTILINE)
        self.assertEqual(count, 1, f"{relative}: no match for {pattern}")
        path.write_text(replaced, encoding="utf-8")

    def write_agents(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(NEW), "--root", str(self.root), "agents"],
            cwd=self.root, check=False, capture_output=True, text=True,
        )

    def lens_files(self) -> list[Path]:
        return [path for path in sorted((self.root / ".claude/lenses").glob("*.md"))
                if path.name != "README.md"]

    def test_every_shipped_lens_is_declared_by_the_role_it_belongs_to(self):
        """A lens is reachable or it is dead prose; the roster is not a second list."""
        self.assertTrue(self.lens_files(), "the template ships no lens")
        result = self.run_checker()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        for path in self.lens_files():
            with self.subTest(lens=path.stem):
                owner = next(line.split(":", 1)[1].strip()
                             for line in path.read_text().splitlines()
                             if line.startswith("role:"))
                role = self.root / f".claude/agents/{owner}.md"
                self.assertIn(f".claude/lenses/{path.stem}.md", role.read_text())

    def test_an_orphan_lens_and_a_dangling_declaration_are_both_errors(self):
        orphan = self.root / ".claude/lenses/orphan.md"
        orphan.write_text("---\nname: orphan\nrole: researcher\n---\n\nNobody loads this.\n")

        result = self.run_checker()

        self.assertEqual(result.returncode, 1)
        self.assertIn(".claude/lenses/orphan.md: no role declares this lens", result.stdout)

        orphan.unlink()
        (self.root / ".claude/lenses/prove.md").unlink()

        result = self.run_checker()

        self.assertEqual(result.returncode, 1)
        self.assertIn("declares lens 'prove', which is not a lens belonging to 'researcher'",
                      result.stdout)

    def test_a_repository_may_ship_no_codex_adapters_at_all(self):
        """Cross-client support is a choice. Only Claude Code? Delete the tree."""
        shutil.rmtree(self.root / ".codex")

        result = self.run_checker()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_installing_a_capability_pack_leaves_the_roles_lane_green(self):
        """A pack install is one command: the roster already links it by path, so no
        documentation edit is owed before the checker will pass."""
        self.assertFalse((self.root / ".claude/agents/numerics.md").exists())

        install = subprocess.run(
            [sys.executable, str(REPO / "scripts/new.py"), "--root", str(self.root),
             "role", "numerics"],
            check=False, capture_output=True, text=True,
        )
        self.assertEqual(install.returncode, 0, install.stdout + install.stderr)

        result = self.run_checker()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.root / ".codex/agents/numerics.toml").is_file())

    def test_a_lens_is_not_a_role_and_gets_no_adapter(self):
        """Lenses carry no tools and no write surface, so they need no Codex adapter."""
        result = self.run_checker()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        adapters = {path.stem for path in (self.root / ".codex/agents").glob("*.toml")}
        self.assertEqual(adapters, {path.stem for path in self.role_files()})
        self.assertFalse(adapters & {path.stem for path in self.lens_files()})

    def test_generated_adapters_match_canonical_roles(self):
        result = self.run_checker()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(f"{len(self.role_files())} agent role(s)", result.stdout)

    def test_roster_is_derived_from_the_files_on_disk(self):
        """No list of role names is kept anywhere but the files and the profile table."""
        source = self.root / ".claude/agents/scout.md"
        added = self.root / ".claude/agents/extra-role.md"
        added.write_text(
            source.read_text(encoding="utf-8").replace("name: scout", "name: extra-role"),
            encoding="utf-8",
        )
        data = self.read_profiles()
        data["roles"]["extra-role"] = data["roles"]["scout"]
        for assignment in data["profiles"].values():
            assignment["extra-role"] = assignment["scout"]
        self.write_profiles(data)

        result = self.run_checker()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Codex adapters missing: ['extra-role']", result.stdout)
        self.assertIn("roster does not link role 'extra-role'", result.stdout)

    def test_a_role_absent_from_the_profile_table_is_rejected(self):
        """Model and effort are not optional, and there is no implicit default tier."""
        data = self.read_profiles()
        del data["roles"]["janitor"]
        self.write_profiles(data)

        result = self.run_checker()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("'janitor' has no entry under 'roles:'", result.stdout)

    def test_each_client_effort_scale_is_validated_separately(self):
        """Codex has a rung above Claude's ceiling; neither borrows the other's."""
        data = self.read_profiles()
        tier = next(name for name, block in data["tiers"].items() if block["claude"])

        # `ultra` is Codex's rung above Claude's ceiling, and stays Codex's.
        data["tiers"][tier]["claude"]["effort"] = "ultra"
        self.write_profiles(data)

        result = self.run_checker()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f"tier '{tier}' / claude: effort must be one of", result.stdout)

        data["tiers"][tier]["claude"]["effort"] = "max"
        data["tiers"][tier]["codex"]["effort"] = "colossal"
        self.write_profiles(data)

        result = self.run_checker()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f"tier '{tier}' / codex: effort must be one of", result.stdout)

    def test_a_tier_inherits_on_both_clients_or_on_neither(self):
        """A tier name that means one thing on Claude and another on Codex is not a tier."""
        data = self.read_profiles()
        tier = next(name for name, block in data["tiers"].items() if not block["claude"])
        data["tiers"][tier]["claude"] = {"model": "opus", "effort": "max"}
        self.write_profiles(data)

        result = self.run_checker()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f"tier '{tier}' inherits on one client and pins on the other",
                      result.stdout)

    def test_an_unknown_claude_model_alias_is_rejected(self):
        data = self.read_profiles()
        tier = next(name for name, block in data["tiers"].items() if block["claude"])
        data["tiers"][tier]["claude"]["model"] = data["tiers"][tier]["codex"]["model"]
        self.write_profiles(data)

        result = self.run_checker()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f"tier '{tier}' / claude: model must be one of", result.stdout)

    def test_hand_edited_role_frontmatter_is_rejected(self):
        """The frontmatter is generated; the profile table is where a model changes."""
        self.replace_in_role(".claude/agents/researcher.md",
                             r"^model: .*$", "model: haiku")

        result = self.run_checker()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("frontmatter disagrees with .claude/agents/profiles.yaml",
                      result.stdout)

    def test_switching_the_active_profile_restamps_both_clients(self):
        """One line changes model and effort everywhere, on Claude and on Codex."""
        data = self.read_profiles()
        data["active"] = self.inheriting_profile(data)
        self.write_profiles(data)

        self.assertNotEqual(self.run_checker().returncode, 0)
        write = self.write_agents()
        self.assertEqual(write.returncode, 0, write.stdout + write.stderr)
        self.assertEqual(self.run_checker().returncode, 0)

        for path in self.role_files():
            with self.subTest(role=path.stem):
                frontmatter = path.read_text(encoding="utf-8").split("---")[1]
                self.assertIn("model: inherit", frontmatter)
                self.assertNotIn("effort:", frontmatter)
        for adapter in sorted((self.root / ".codex/agents").glob("*.toml")):
            parsed = tomllib.loads(adapter.read_text(encoding="utf-8"))
            with self.subTest(adapter=adapter.stem):
                # Codex inherits by omission; it has no `inherit` literal.
                self.assertNotIn("model", parsed)
                self.assertNotIn("model_reasoning_effort", parsed)

    def test_capability_packs_are_stamped_where_they_sit(self):
        """So that installing one lands a file the roles lane already accepts."""
        self.replace_in_role("packs/numerics/numerics.md",
                             r"^effort: .*$", "effort: low")

        result = self.run_checker()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("packs/numerics/numerics.md: frontmatter disagrees", result.stdout)

    def test_stale_codex_adapter_is_rejected(self):
        adapter = self.root / ".codex/agents/scout.toml"
        adapter.write_text(adapter.read_text(encoding="utf-8") + "# stale\n", encoding="utf-8")
        result = self.run_checker()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stale or hand-edited", result.stdout)

    def test_both_clients_resolve_the_same_tier(self):
        """One table, two vocabularies: Claude differentiates by model, Codex by effort.

        The expectation is read out of the table rather than pinned here, because
        retuning a tier is what the table is for and must not break this suite. What is
        pinned is the invariant: each artifact carries its own client's half of the very
        same tier, and `read_only` is checked against Claude's tool list while Codex gets
        a sandbox setting.
        """
        data = self.read_profiles()
        assignment = data["profiles"][data["active"]]

        for path in self.role_files():
            name = path.stem
            tier = data["tiers"][assignment[name]]
            frontmatter = yaml.safe_load(path.read_text(encoding="utf-8").split("---")[1])
            parsed = tomllib.loads(
                (self.root / f".codex/agents/{name}.toml").read_text(encoding="utf-8"))
            with self.subTest(role=name):
                if tier["claude"]:
                    self.assertEqual(frontmatter["model"], tier["claude"]["model"])
                    self.assertEqual(frontmatter["effort"], tier["claude"]["effort"])
                    self.assertEqual(parsed["model"], tier["codex"]["model"])
                    self.assertEqual(parsed["model_reasoning_effort"],
                                     tier["codex"]["effort"])
                else:
                    self.assertEqual(frontmatter["model"], "inherit")
                    self.assertNotIn("effort", frontmatter)
                    self.assertNotIn("model", parsed)
                read_only = data["roles"][name]["read_only"]
                self.assertEqual(parsed["sandbox_mode"],
                                 "read-only" if read_only else "workspace-write")
                self.assertEqual(read_only,
                                 not {"Edit", "Write"} & set(frontmatter["tools"].split(", ")))

    def test_a_profile_may_not_take_a_tier_name(self):
        """A bare word in the table says which layer it belongs to, or it is ambiguous."""
        data = self.read_profiles()
        tier = next(iter(data["tiers"]))
        profile = next(iter(data["profiles"]))
        data["profiles"][tier] = data["profiles"].pop(profile)
        data["active"] = tier
        self.write_profiles(data)

        result = self.run_checker()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f"profile name(s) ['{tier}'] also name a tier", result.stdout)

    def test_read_only_role_cannot_declare_write_tool(self):
        """The profile declaration rejects explicit Claude write tools."""
        role = self.root / ".claude/agents/scout.md"
        text = role.read_text(encoding="utf-8")
        role.write_text(
            text.replace("tools: Read, Grep, Glob, Bash", "tools: Read, Grep, Glob, Bash, Write"),
            encoding="utf-8",
        )
        result = self.run_checker()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("read-only role declares a write tool", result.stdout)

    def test_write_agents_removes_an_adapter_whose_role_is_gone(self):
        orphan = self.root / ".codex/agents/retired-role.toml"
        orphan.write_text('name = "retired-role"\n', encoding="utf-8")

        result = self.write_agents()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(orphan.exists())
        self.assertEqual(self.run_checker().returncode, 0)

    def test_the_roster_lives_with_the_maintainer_documentation(self):
        """A role loads README.md to execute; the table of its colleagues is not that."""
        maintaining = (self.root / ".claude/agents/MAINTAINING.md").read_text(encoding="utf-8")
        readme = (self.root / ".claude/agents/README.md").read_text(encoding="utf-8")

        for name in ("scout", "researcher", "reviewer", "synthesizer"):
            self.assertIn(f"]({name}.md)", maintaining)
        self.assertNotIn("--write-agents", readme)
        self.assertEqual(self.run_checker().returncode, 0)

    def test_maintaining_is_documentation_and_not_a_role(self):
        result = self.run_checker()

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertNotIn("MAINTAINING", result.stdout)

    def test_a_declared_lens_is_checked_even_with_no_lens_directory(self):
        """The one arrangement where a researcher was told to load a file nobody ships."""
        shutil.rmtree(self.root / ".claude/lenses")

        result = self.run_checker()

        self.assertEqual(result.returncode, 1)
        self.assertIn("declares lens 'prove', but .claude/lenses/ does not exist",
                      result.stdout)

    def test_author_and_reviewer_remain_separate_roles(self):
        """The one epistemic control the role collapse must not lose."""
        researcher = (self.root / ".claude/agents/researcher.md").read_text(encoding="utf-8")
        reviewer = (self.root / ".claude/agents/reviewer.md").read_text(encoding="utf-8")

        self.assertIn("You never write any `ledger.yaml`, `research/reviews/`", researcher)
        self.assertIn("You never write `solutions/`", reviewer)
        self.assertIn("Never review work you authored", reviewer)


if __name__ == "__main__":
    unittest.main()
