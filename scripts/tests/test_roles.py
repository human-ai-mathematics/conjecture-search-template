"""Roles plane: canonical role definitions, assignment lenses, and generated adapters.

These run against a copy of the real `.claude/` and `.codex/` trees, so the shipped
roster and lens set are what is actually checked.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

REPO = Path(__file__).resolve().parents[2]
CHECK = REPO / "scripts/check.py"


class RoleTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        shutil.copytree(REPO / ".claude", self.root / ".claude")
        shutil.copytree(REPO / ".codex", self.root / ".codex")

    def tearDown(self):
        self.tempdir.cleanup()

    def run_checker(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CHECK), "--root", str(self.root), "--plane", "roles"],
            cwd=self.root, check=False, capture_output=True, text=True,
        )

    def role_files(self) -> list[Path]:
        return [path for path in sorted((self.root / ".claude/agents").glob("*.md"))
                if path.name != "README.md"]

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
        """Adding a role is one file: no list of names is kept anywhere else."""
        source = self.root / ".claude/agents/scout.md"
        added = self.root / ".claude/agents/extra-role.md"
        added.write_text(
            source.read_text(encoding="utf-8").replace("name: scout", "name: extra-role"),
            encoding="utf-8",
        )

        result = self.run_checker()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Codex adapters missing: ['extra-role']", result.stdout)
        self.assertIn("roster does not link role 'extra-role'", result.stdout)

    def test_role_declaring_an_unknown_reasoning_effort_is_rejected(self):
        role = self.root / ".claude/agents/researcher.md"
        role.write_text(
            role.read_text(encoding="utf-8").replace("reasoning: ultra", "reasoning: maximum"),
            encoding="utf-8",
        )

        result = self.run_checker()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("reasoning must be one of", result.stdout)

    def test_stale_codex_adapter_is_rejected(self):
        adapter = self.root / ".codex/agents/scout.toml"
        adapter.write_text(adapter.read_text(encoding="utf-8") + "# stale\n", encoding="utf-8")
        result = self.run_checker()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stale or hand-edited", result.stdout)

    def test_codex_adapter_mirrors_the_role_frontmatter(self):
        """Model and effort come from each role's own frontmatter, not a table here."""
        for adapter in sorted((self.root / ".codex/agents").glob("*.toml")):
            parsed = tomllib.loads(adapter.read_text(encoding="utf-8"))
            role = (self.root / f".claude/agents/{parsed['name']}.md").read_text(encoding="utf-8")
            with self.subTest(role=parsed["name"]):
                self.assertEqual(parsed["model"], "gpt-5.6-sol")
                declared_effort = "ultra" if "reasoning: ultra" in role else "high"
                self.assertEqual(parsed["model_reasoning_effort"], declared_effort)
                declared_read_only = "read_only: true" in role
                self.assertEqual(
                    parsed["sandbox_mode"],
                    "read-only" if declared_read_only else "workspace-write",
                )

    def test_read_only_claude_role_cannot_declare_write_tool(self):
        role = self.root / ".claude/agents/scout.md"
        text = role.read_text(encoding="utf-8")
        role.write_text(
            text.replace("tools: Read, Grep, Glob, Bash", "tools: Read, Grep, Glob, Bash, Write"),
            encoding="utf-8",
        )
        result = self.run_checker()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("read-only role declares a write tool", result.stdout)

    def test_write_codex_removes_an_adapter_whose_role_is_gone(self):
        orphan = self.root / ".codex/agents/retired-role.toml"
        orphan.write_text('name = "retired-role"\n', encoding="utf-8")

        subprocess.run(
            [sys.executable, str(CHECK), "--root", str(self.root), "--write-codex"],
            cwd=self.root, check=False, capture_output=True, text=True,
        )

        self.assertFalse(orphan.exists())
        self.assertEqual(self.run_checker().returncode, 0)

    def test_author_and_reviewer_remain_separate_roles(self):
        """The one epistemic control the role collapse must not lose."""
        researcher = (self.root / ".claude/agents/researcher.md").read_text(encoding="utf-8")
        reviewer = (self.root / ".claude/agents/reviewer.md").read_text(encoding="utf-8")

        self.assertIn("You never write any `ledger.yaml`, `research/reviews/`", researcher)
        self.assertIn("You never write `solutions/`", reviewer)
        self.assertIn("Never review work you authored", reviewer)


if __name__ == "__main__":
    unittest.main()
