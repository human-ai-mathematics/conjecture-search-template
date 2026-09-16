"""Numerics lane: the envelopes of the immutable run artifacts.

A run artifact is worth exactly as much as its provenance header (CLAUDE.md
constraint 2), so this lane checks that the header a later reader needs in order to
reproduce or retract the numbers is still there and still parses.
"""
from __future__ import annotations

import ast
import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from checks import numerics as numerics_lane  # noqa: E402
from fixtures import CheckerFixture, node  # noqa: E402


class NumericsTests(CheckerFixture):
    def setUp(self):
        super().setUp()
        self.add_ledger("program", "program",
                        [node("conj:open", status="open", kind="conjecture")])

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
                         '{"_provenance": {"schema_version": 1, "date": "2026-08-26",'
                         ' "target": "fixture", "profile": "p", "config": {},'
                         ' "environment": {}}}',
                         '{"_provenance": {"target": "smuggled"}}',
                     ])

        self.assertIn("fixture.jsonl:2: only the first record carries provenance",
                      self.errors())

    def test_the_filename_must_name_the_target_it_recorded(self):
        self.add_run("2026-08-26T000000Z-mislabelled.jsonl", target="fixture")

        self.assertIn("filename must end with '-fixture.jsonl'", self.errors())

    def test_a_current_artifact_records_which_source_tree_produced_it(self):
        """git_commit alone cannot reproduce a run whose target was still uncommitted."""
        self.add_run("2026-08-26T000000Z-fixture.jsonl",
                     header={"git_commit": None, "git_dirty": None,
                             "git_diff_sha256": None})
        self.assertEqual(self.errors(), "")

        self.add_run("2026-08-27T000000Z-fixture.jsonl",
                     lines=[
                         '{"_provenance": {"schema_version": 1, "date": "2026-08-27",'
                         ' "target": "fixture", "profile": "p", "stochastic": false,'
                         ' "config": {}, "environment": {}}}',
                         '{"kind": "note"}',
                     ])

        errors = self.errors()

        self.assertIn("_provenance is missing 'git_commit'", errors)
        self.assertIn("_provenance is missing 'git_dirty'", errors)

    def test_an_unsupported_artifact_schema_is_rejected(self):
        self.add_run("2026-08-26T000000Z-fixture.jsonl",
                     lines=[
                         '{"_provenance": {"schema_version": 2, "date": "2026-08-26",'
                         ' "target": "fixture", "profile": "p", "stochastic": false,'
                         ' "config": {}, "environment": {}}}',
                         '{"kind": "note"}',
                     ])

        self.assertIn("schema_version must be 1, got '2'", self.errors())

    def test_a_migrated_artifact_verifies_its_preserved_source(self):
        source = self.root / "research/legacy-runs/original.jsonl"
        source.parent.mkdir(parents=True)
        source.write_bytes(b'{"legacy": true}\n')
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        self.add_run(
            "2026-08-26T000000Z-fixture.jsonl",
            header={"migrated_from": {
                "path": "research/legacy-runs/original.jsonl",
                "sha256": digest,
            }},
        )

        self.assertEqual(self.errors(), "")

        source.write_bytes(b'{"legacy": false}\n')
        self.assertIn("migrated source", self.errors())
        self.assertIn("expected", self.errors())

    def test_a_migrated_source_must_stay_in_the_legacy_archive(self):
        outside = self.root / "research/original.jsonl"
        outside.write_bytes(b"legacy\n")
        self.add_run(
            "2026-08-26T000000Z-fixture.jsonl",
            header={"migrated_from": {
                "path": "research/original.jsonl",
                "sha256": hashlib.sha256(outside.read_bytes()).hexdigest(),
            }},
        )

        self.assertIn(
            "migrated_from.path must stay under research/legacy-runs/",
            self.errors(),
        )

    def test_half_an_observation_is_not_evidence(self):
        self.add_run("2026-08-26T000000Z-fixture.jsonl",
                     lines=[
                         '{"_provenance": {"schema_version": 1, "date": "2026-08-26",'
                         ' "target": "fixture", "profile": "p", "stochastic": false,'
                         ' "config": {}, "environment": {}}}',
                         '{"kind": "observation", "instance": "n=3", "evidence": "exact"}',
                     ])

        errors = self.errors()

        self.assertIn("half an observation", errors)
        self.assertIn("an unlabelled number is not evidence", errors)

    def test_an_outcome_must_belong_to_its_evidence_class(self):
        self.add_run("2026-08-26T000000Z-fixture.jsonl",
                     lines=[
                         '{"_provenance": {"schema_version": 1, "date": "2026-08-26",'
                         ' "target": "fixture", "profile": "p", "stochastic": false,'
                         ' "config": {}, "environment": {}}}',
                         '{"kind": "observation", "instance": "n=3", "claim": "c",'
                         ' "evidence": "calibration", "outcome": "contradicts"}',
                     ])

        errors = self.errors()

        self.assertIn("evidence 'calibration' allows ['match', 'mismatch']", errors)

    def test_the_archive_vocabulary_matches_the_harness_that_writes_it(self):
        """Duplicated on purpose, so the two copies are checked rather than trusted."""
        source = (Path(__file__).resolve().parents[2]
                  / "experiments/numerics/contract.py").read_text(encoding="utf-8")
        # Read the literals out of the source rather than importing the package, which
        # would drag in numpy and couple the checker's test suite to the harness.
        wanted = {
            "ARTIFACT_SCHEMA_VERSION", "EVIDENCE_CLASSES", "OUTCOMES",
            "OBSERVATION_FIELDS",
        }
        found = {}
        for statement in ast.parse(source).body:
            if not isinstance(statement, (ast.Assign, ast.AnnAssign)):
                continue
            targets = (statement.targets if isinstance(statement, ast.Assign)
                       else [statement.target])
            for target in targets:
                if isinstance(target, ast.Name) and target.id in wanted:
                    found[target.id] = ast.literal_eval(statement.value)

        self.assertEqual(sorted(found), sorted(wanted))
        self.assertEqual(found["ARTIFACT_SCHEMA_VERSION"],
                         numerics_lane.ARTIFACT_SCHEMA_VERSION)
        self.assertEqual(tuple(found["EVIDENCE_CLASSES"]),
                         tuple(numerics_lane.EVIDENCE_CLASSES))
        self.assertEqual(tuple(found["OBSERVATION_FIELDS"]),
                         tuple(numerics_lane.OBSERVATION_FIELDS))
        self.assertEqual({key: tuple(value) for key, value in found["OUTCOMES"].items()},
                         {key: tuple(value) for key, value in numerics_lane.OUTCOMES.items()})


if __name__ == "__main__":
    unittest.main()
