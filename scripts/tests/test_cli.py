"""The command-line surface: lane selection and the derived views.

These run the real ``scripts/check.py`` against a fixture tree through ``--root``, so
the entry point, the lane filter, and the views are exercised as a user meets them.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fixtures import CheckerFixture, node  # noqa: E402


class CommandLineTests(CheckerFixture):
    def test_cli_reports_malformed_status_instead_of_crashing(self):
        malformed = node("thm:bad")
        malformed["status"] = []
        self.add_ledger("program", "program", [malformed])

        result = self.cli()

        self.assertEqual(result.returncode, 1)
        self.assertIn("bad status '[]'", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_errors_are_tagged_with_the_plane_that_raised_them(self):
        malformed = node("thm:bad")
        malformed["status"] = []
        self.add_ledger("program", "program", [malformed])
        self.add_checkpoint("dangling", nodes=("q:ghost",))

        everything = self.cli()
        core_only = self.cli("--lane", "core")

        self.assertIn("FAIL [core]", everything.stdout)
        self.assertIn("FAIL [checkpoints]", everything.stdout)
        self.assertIn("FAIL [core]", core_only.stdout)
        self.assertNotIn("FAIL [checkpoints]", core_only.stdout)

    def test_a_plane_with_no_files_reports_nothing(self):
        """Activation is structural: an absent lane has no rules to obey."""
        self.add_ledger("program", "program", [node("q:open", status="open", kind="question")])

        for lane in ("portfolio", "numerics", "checkpoints", "roles"):
            with self.subTest(lane=lane):
                result = self.cli("--lane", lane)
                self.assertEqual(result.returncode, 0, result.stdout)

    def test_cli_status_and_node_views_are_derived(self):
        self.add_ledger(
            "program",
            "program",
            [
                node("lem:base"),
                node(
                    "q:frontier",
                    status="open",
                    kind="question",
                    depends_on=["lem:base"],
                ),
            ],
        )

        status = self.cli("status")
        detail = self.cli("node", "q:frontier")

        self.assertEqual(status.returncode, 0)
        self.assertIn("[program]", status.stdout)
        self.assertIn("open (1): q:frontier", status.stdout)
        self.assertEqual(detail.returncode, 0)
        self.assertIn("[program] q:frontier", detail.stdout)
        self.assertIn("depends_on:", detail.stdout)
        self.assertIn("used_by: []", detail.stdout)

    def test_cli_lists_live_candidate_statements(self):
        self.add_ledger("program", "program", [node("q:open", status="open", kind="question")])
        self.add_checkpoint("propose", outcome="candidate",
                            candidates=({"id": "cand:alpha",
                                         "statement": "the candidate statement"},))

        result = self.cli("candidates")

        self.assertEqual(result.returncode, 0)
        self.assertIn("cand:alpha", result.stdout)
        self.assertIn("the candidate statement", result.stdout)

    def test_cli_portfolio_view_shows_routes_blockers_and_relations(self):
        self.add_ledger("program", "program", [node("q:open", status="open", kind="question")])
        why = self.add_checkpoint("blocked", nodes=("q:open",), approach="ap:stuck")
        self.add_portfolio({
            "target": "q:open",
            "families": [{"id": "fam:one", "mechanism": "M", "state": "active"}],
            "approaches": [
                {"id": "ap:live", "family": "fam:one", "state": "active"},
                {"id": "ap:stuck", "family": "fam:one", "state": "blocked",
                 "blocker": "q:open", "reopen_if": "a new mechanism appears",
                 "checkpoints": [why]},
            ],
        })

        result = self.cli("portfolio")

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("target: q:open", result.stdout)
        self.assertIn("[fam:one] active", result.stdout)
        self.assertIn("ap:stuck [blocked]", result.stdout)
        self.assertIn("blocked on: q:open", result.stdout)
        self.assertIn("reopen if: a new mechanism appears", result.stdout)

    def test_cli_checkpoint_view_shows_heads_and_names_the_superseding_record(self):
        """A current-memory view must say what to read instead, not just what is stale."""
        self.add_ledger("program", "program", [node("q:open", status="open", kind="question")])
        old = self.add_checkpoint("first", nodes=("q:open",))
        self.add_checkpoint("second", date="2026-08-27", nodes=("q:open",),
                            supersedes=(old,))
        stale = self.add_review("stale-audit", report_type="audit", date="2026-08-25")
        self.add_review("current-audit", report_type="audit", date="2026-08-26",
                        supersedes=(stale,))

        result = self.cli("checkpoints")

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("1 current checkpoint(s), 1 superseded", result.stdout)
        self.assertIn("2026-08-27-second.md", result.stdout)
        self.assertIn("superseded  research/explorations/2026-08-26-first.md", result.stdout)
        self.assertIn("read instead: research/explorations/2026-08-27-second.md",
                      result.stdout)
        self.assertIn("1 current audit(s), 1 superseded", result.stdout)
        self.assertIn("read instead: research/reviews/2026-08-26-current-audit.md",
                      result.stdout)

    def test_the_deprecated_plane_alias_still_selects_a_lane(self):
        """Old habits and old docs keep working, with one note on stderr."""
        malformed = node("thm:bad")
        malformed["status"] = []
        self.add_ledger("program", "program", [malformed])
        self.add_checkpoint("dangling", nodes=("q:ghost",))

        result = self.cli("--plane", "core")

        self.assertEqual(result.returncode, 1)
        self.assertIn("--plane is deprecated; use --lane", result.stderr)
        self.assertIn("FAIL [core]", result.stdout)
        self.assertNotIn("FAIL [checkpoints]", result.stdout)

    def test_a_scoped_run_summarises_only_the_lanes_it_was_asked_for(self):
        """A green scoped run must not report an error count it also exits 0 on."""
        self.add_ledger("program", "program", [node("q:open", status="open", kind="question")])
        self.add_checkpoint("dangling", nodes=("q:ghost",))

        result = self.cli("--lane", "core")

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("0 error(s)", result.stdout)

    def test_a_ledger_with_no_nodes_prints_no_dangling_separator(self):
        self.add_ledger("program", "program", [])

        result = self.cli()

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("[program] 0 nodes", result.stdout)
        self.assertNotIn("0 nodes —", result.stdout)

    def test_ready_fails_on_a_template_and_passes_on_an_instantiated_repository(self):
        """A fresh clone is structurally correct and deliberately not ready."""
        self.add_ledger("program", "program", [])

        template = self.cli("ready")

        self.assertEqual(template.returncode, 1)
        self.assertIn("not ready", template.stdout)
        self.assertIn("meta.program is still 'program'", template.stdout)
        self.assertIn("no nodes", template.stdout)
        self.assertIn("research/program/brief.md: absent", template.stdout)

        self.add_ledger("program", "real-program",
                        [node("q:target", status="open", kind="question")])
        self.add_brief("q:target", body="The negation, spelled out.\n")

        instantiated = self.cli("ready")

        self.assertEqual(instantiated.returncode, 0, instantiated.stdout)
        self.assertIn("ready:", instantiated.stdout)

    def test_a_view_refuses_to_render_over_a_broken_repository(self):
        malformed = node("thm:bad")
        malformed["status"] = []
        self.add_ledger("program", "program", [malformed])

        result = self.cli("status")

        self.assertEqual(result.returncode, 1)
        self.assertIn("bad status '[]'", result.stdout)


if __name__ == "__main__":
    unittest.main()
