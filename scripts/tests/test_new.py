"""The scaffolder: scripts/new.py.

Its contract is narrow and worth pinning. It writes files from ``templates/``, it never
overwrites one, and it never touches ``research/program/ledger.yaml`` — that file has a
single writer (CLAUDE.md constraint 1), so ``new.py node`` prints and stops.

    python3 -m unittest discover -s scripts/tests -p 'test_*.py'
"""
from __future__ import annotations

import io
import contextlib
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import new as scaffold  # noqa: E402

REPO = Path(__file__).resolve().parents[2]


class ScaffoldTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        shutil.copytree(REPO / "templates", self.root / "templates")
        self.addCleanup(self._tmp.cleanup)

    def run_scaffold(self, *argv: str) -> tuple[int, str]:
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            code = scaffold.main(["--root", str(self.root), *argv])
        return code, stream.getvalue()

    def read(self, relative: str) -> str:
        return (self.root / relative).read_text(encoding="utf-8")

    def test_a_brief_is_written_with_its_target_substituted(self):
        code, output = self.run_scaffold("brief", "--target", "q:main")

        self.assertEqual(code, 0, output)
        brief = self.read("research/program/brief.md")
        self.assertIn("target: q:main", brief)
        self.assertNotIn("{{TARGET_NODE}}", brief)

    def test_a_scaffold_never_overwrites_an_existing_file(self):
        """Two planes here are append-only, and a scaffolder that clobbers is how a
        durable record stops being durable."""
        self.run_scaffold("brief", "--target", "q:main")
        (self.root / "research/program/brief.md").write_text("hand written\n")

        code, output = self.run_scaffold("brief", "--target", "q:other")

        self.assertEqual(code, 1)
        self.assertIn("already exists", output)
        self.assertEqual(self.read("research/program/brief.md"), "hand written\n")

    def test_a_checkpoint_lands_under_a_dated_filename(self):
        code, output = self.run_scaffold("checkpoint", "first-attempt", "--node", "q:main")

        self.assertEqual(code, 0, output)
        written = sorted((self.root / "research/explorations").glob("*.md"))
        self.assertEqual(len(written), 1)
        self.assertTrue(written[0].name.endswith("-first-attempt.md"))
        self.assertIn("- q:main", written[0].read_text())

    def test_a_timestamped_checkpoint_keeps_the_plain_date_in_its_filename(self):
        """`date:` may carry a UTC time to order same-day records; the filename prefix
        stays YYYY-MM-DD, which is what check_record_date compares against."""
        code, output = self.run_scaffold("checkpoint", "ordered", "--timestamp")

        self.assertEqual(code, 0, output)
        written = sorted((self.root / "research/explorations").glob("*.md"))[0]
        self.assertRegex(written.name, r"^\d{4}-\d{2}-\d{2}-ordered\.md$")
        self.assertRegex(written.read_text(), r'date: "\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z"')

    def test_a_dossier_is_named_for_its_node_and_declares_it(self):
        code, output = self.run_scaffold("dossier", "lem:key")

        self.assertEqual(code, 0, output)
        dossier = self.read("solutions/lem-key.tex")
        self.assertIn("ledger-node : lem:key", dossier)
        self.assertNotIn("checked_by", dossier)

    def test_node_prints_and_writes_nothing(self):
        """The ledger has one writer. A scaffolder is not it (CLAUDE.md constraint 1)."""
        code, output = self.run_scaffold("node", "lem:key", "--kind", "lemma")

        self.assertEqual(code, 0, output)
        self.assertIn("id: lem:key", output)
        self.assertIn("kind: lemma", output)
        self.assertFalse((self.root / "research").exists())

    def test_a_malformed_id_is_refused_before_anything_is_written(self):
        code, output = self.run_scaffold("brief", "--target", "Not A Node")

        self.assertEqual(code, 1)
        self.assertIn("want a node id", output)
        self.assertFalse((self.root / "research/program/brief.md").exists())

    def test_installing_an_unknown_capability_pack_names_the_real_ones(self):
        (self.root / "packs/numerics").mkdir(parents=True)
        (self.root / "packs/numerics/numerics.md").write_text("fixture role\n")

        code, output = self.run_scaffold("role", "nonesuch")

        self.assertEqual(code, 1)
        self.assertIn("numerics", output)

    def test_installing_a_capability_pack_copies_its_role_into_place(self):
        (self.root / "packs/numerics").mkdir(parents=True)
        (self.root / "packs/numerics/numerics.md").write_text("fixture role\n")

        code, output = self.run_scaffold("role", "numerics")

        self.assertEqual(code, 0, output)
        self.assertEqual(self.read(".claude/agents/numerics.md"), "fixture role\n")


if __name__ == "__main__":
    unittest.main()
