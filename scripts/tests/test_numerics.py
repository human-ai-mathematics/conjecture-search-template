"""Numerics plane: the envelopes of the immutable run artifacts.

A run artifact is worth exactly as much as its provenance header (CLAUDE.md
constraint 2), so this plane checks that the header a later reader needs in order to
reproduce or retract the numbers is still there and still parses.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fixtures import CheckerFixture, node  # noqa: E402


class NumericsTests(CheckerFixture):
    def setUp(self):
        super().setUp()
        self.add_ledger("program", "program",
                        [node("q:open", status="open", kind="question")])

    def test_a_well_formed_artifact_passes(self):
        self.add_run("2026-08-26T000000Z-fixture.jsonl", records=3)

        self.assertEqual(self.errors(), "")
        self.assertEqual(self.check()["artifacts"][0]["records"], 3)

    def test_an_absent_runs_directory_is_not_an_error(self):
        self.assertEqual(self.errors(), "")
        self.assertEqual(self.check()["artifacts"], [])

    def test_a_missing_provenance_field_is_reported(self):
        self.add_run("2026-08-26T000000Z-fixture.jsonl", header={"git_commit": None},
                     records=1)
        self.add_run("2026-08-26T000001Z-bare.jsonl", target="bare",
                     header={"environment": None})

        errors = self.errors()

        self.assertIn("2026-08-26T000001Z-bare.jsonl: _provenance is missing "
                      "'environment'", errors)
        self.assertNotIn("2026-08-26T000000Z-fixture.jsonl", errors)

    def test_an_artifact_without_a_header_or_observations_is_reported(self):
        self.add_run("2026-08-26T000000Z-headless.jsonl",
                     lines=['{"kind": "observation"}'])
        self.add_run("2026-08-26T000001Z-empty.jsonl", lines=[])
        self.add_run("2026-08-26T000002Z-fixture.jsonl", records=0)

        errors = self.errors()

        self.assertIn("headless.jsonl: first record must be the '_provenance' header",
                      errors)
        self.assertIn("empty.jsonl: run artifact is empty", errors)
        self.assertIn("fixture.jsonl: run artifact records no observation", errors)

    def test_malformed_json_is_reported_with_its_line(self):
        self.add_run("2026-08-26T000000Z-fixture.jsonl",
                     lines=['{"_provenance": {}}', "not json at all"])

        self.assertIn("fixture.jsonl:2: not valid JSON", self.errors())

    def test_only_the_first_record_carries_provenance(self):
        self.add_run("2026-08-26T000000Z-fixture.jsonl",
                     lines=[
                         '{"_provenance": {"schema_version": 2, "date": "2026-08-26",'
                         ' "target": "fixture", "profile": "p", "config": {},'
                         ' "environment": {}}}',
                         '{"_provenance": {"target": "smuggled"}}',
                     ])

        self.assertIn("fixture.jsonl:2: only the first record carries provenance",
                      self.errors())

    def test_the_filename_must_name_the_target_it_recorded(self):
        self.add_run("2026-08-26T000000Z-mislabelled.jsonl", target="fixture")

        self.assertIn("filename must end with '-fixture.jsonl'", self.errors())


if __name__ == "__main__":
    unittest.main()
