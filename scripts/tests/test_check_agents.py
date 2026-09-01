"""Regression tests for the cross-client agent-definition checker."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]


class AgentCheckerFixture(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        shutil.copytree(REPO / ".claude", self.root / ".claude")
        shutil.copytree(REPO / ".codex", self.root / ".codex")
        (self.root / "scripts").mkdir()
        shutil.copy2(REPO / "scripts/check_agents.py", self.root / "scripts/check_agents.py")

    def tearDown(self):
        self.tempdir.cleanup()

    def run_checker(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "scripts/check_agents.py"],
            cwd=self.root,
            check=False,
            capture_output=True,
            text=True,
        )

    def role_files(self) -> list[Path]:
        return [path for path in sorted((self.root / ".claude/agents").glob("*.md"))
                if path.name != "README.md"]

    def test_generated_adapters_match_canonical_roles(self):
        result = self.run_checker()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(f"0 errors ({len(self.role_files())} roles)", result.stdout)

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
        role = self.root / ".claude/agents/prover.md"
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


if __name__ == "__main__":
    unittest.main()
