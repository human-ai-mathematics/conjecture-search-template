"""Checkpoints lane: durable memory, candidates, approaches, and supersession."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from checks import failures  # noqa: E402
from fixtures import CheckerFixture, node  # noqa: E402


class CheckpointTests(CheckerFixture):
    def test_exploration_requires_a_typed_dated_envelope(self):
        self.add_ledger("program", "program", [node("conj:open", status="open", kind="conjecture")])
        directory = self.root / "research/explorations"
        directory.mkdir(parents=True)
        (directory / "2026-08-26-bare.md").write_text("# no front matter\n")
        (directory / "README.md").write_text("navigation, not an attempt\n")
        self.add_checkpoint("wrong-outcome", nodes=("conj:open",), outcome="promising")
        self.add_checkpoint("stale-date", nodes=("conj:open",),
                             front_matter={"date": "2026-08-25"})
        self.add_checkpoint("extra-field", nodes=("conj:open",),
                             front_matter={"verdict": "pass"})
        self.add_checkpoint("engages-nothing")

        errors = self.errors()

        self.assertIn("2026-08-26-bare.md: checkpoint must start with YAML front matter", errors)
        self.assertIn("outcome: want one of", errors)
        self.assertIn("date: must match the filename prefix", errors)
        self.assertIn("field 'verdict' is not valid for a checkpoint", errors)
        self.assertIn("must engage a ledger node, name a portfolio approach, or "
                      "propose a candidate", errors)
        self.assertNotIn("README.md", errors)

    def test_exploration_nodes_and_cited_artifacts_must_resolve(self):
        self.add_ledger("program", "program", [node("conj:open", status="open", kind="conjecture")])
        artifact = self.add_run("2026-08-26T000000Z-example.jsonl")
        self.add_checkpoint("grounded", nodes=("conj:open",), artifacts=(artifact,))
        self.add_checkpoint("dangling", date="2026-08-27", nodes=("conj:ghost",),
                             artifacts=("research/runs/missing.jsonl", "solutions/aside.jsonl"))

        errors = self.errors()

        self.assertIn("nodes: 'conj:ghost' is not a ledger node id", errors)
        self.assertIn("'research/runs/missing.jsonl' does not exist", errors)
        self.assertIn("'solutions/aside.jsonl' must be an artifact under research/runs/", errors)
        self.assertNotIn("2026-08-26-grounded.md", errors)

    def test_candidate_list_and_candidate_outcome_require_each_other(self):
        self.add_ledger("program", "program", [node("conj:open", status="open", kind="conjecture")])
        self.add_checkpoint("claims-none", nodes=("conj:open",), outcome="candidate")
        self.add_checkpoint("unflagged", date="2026-08-27", nodes=("conj:open",),
                             outcome="dead-end",
                             candidates=({"id": "cand:quiet", "statement": "S"},))

        errors = self.errors()

        self.assertEqual(errors.count("outcome 'candidate' and a non-empty 'candidates' list"), 2)

    def test_candidate_ids_are_namespaced_unique_and_never_ledger_nodes(self):
        self.add_ledger("program", "program", [
            node("conj:open", status="open", kind="conjecture"),
            node("cand:collide", status="open", kind="conjecture"),
        ])
        self.add_checkpoint("first", outcome="candidate",
                             candidates=({"id": "cand:same", "statement": "S"},))
        self.add_checkpoint("second", date="2026-08-27", outcome="candidate",
                             candidates=(
                                 {"id": "cand:same", "statement": "S again"},
                                 {"id": "cand:collide", "statement": "already a node"},
                                 {"id": "Bad Id", "statement": "wrong shape"},
                                 {"id": "cand:untyped", "statement": ""},
                             ))

        errors = self.errors()

        self.assertIn("'cand:same' was already proposed in "
                      "research/explorations/2026-08-26-first.md", errors)
        self.assertIn("'cand:collide' is already a ledger node", errors)
        self.assertIn("id: want 'cand:<slug>', got 'Bad Id'", errors)
        self.assertIn("statement: must be a non-empty string", errors)

    def test_a_candidate_stays_live_until_a_later_exploration_retires_it(self):
        self.add_ledger("program", "program", [node("conj:open", status="open", kind="conjecture")])
        self.add_checkpoint("propose", outcome="candidate", candidates=(
            {"id": "cand:alpha", "statement": "A"},
            {"id": "cand:beta", "statement": "B"},
        ))
        self.add_checkpoint("kill", date="2026-08-27", nodes=("conj:open",),
                             retires=("cand:alpha",))

        report = self.check()

        self.assertEqual(failures(report), [])
        self.assertEqual([entry["id"] for entry in report["candidates"]], ["cand:beta"])
        self.assertEqual(report["candidates"][0]["source"],
                         "research/explorations/2026-08-26-propose.md")

    def test_retiring_an_unproposed_or_not_yet_proposed_candidate_fails(self):
        self.add_ledger("program", "program", [node("conj:open", status="open", kind="conjecture")])
        self.add_checkpoint("early", nodes=("conj:open",),
                             retires=("cand:later", "cand:ghost"))
        self.add_checkpoint("later", date="2026-08-27", outcome="candidate",
                             candidates=({"id": "cand:later", "statement": "L"},))
        self.add_checkpoint("self-retiring", date="2026-08-28", outcome="candidate",
                             candidates=({"id": "cand:self", "statement": "S"},),
                             retires=("cand:self",))

        errors = self.errors()

        self.assertIn("'cand:ghost' was never proposed", errors)
        self.assertIn("'cand:later' is retired before", errors)
        self.assertIn("'cand:self' is proposed by this same checkpoint", errors)

    # --- the two additions that attach memory to the search ------------------------------

    def test_a_checkpoint_may_be_anchored_to_a_portfolio_approach(self):
        self.add_ledger("program", "program", [node("conj:open", status="open", kind="conjecture")])
        self.add_portfolio({
            "target": "conj:open",
            "families": [{"id": "fam:one", "mechanism": "M", "state": "active"}],
            "approaches": [{"id": "ap:real", "family": "fam:one", "state": "active"}],
        })
        self.add_checkpoint("anchored", approach="ap:real")
        self.add_checkpoint("dangling", date="2026-08-27", approach="ap:ghost")
        self.add_checkpoint("misshapen", date="2026-08-28", approach="transport-gluing")

        errors = self.errors()

        self.assertIn("approach: 'ap:ghost' is not a portfolio approach", errors)
        self.assertIn("approach: want 'ap:<slug>', got 'transport-gluing'", errors)
        self.assertNotIn("2026-08-26-anchored.md", errors)

    def test_an_approach_reference_needs_a_portfolio_to_resolve_against(self):
        self.add_ledger("program", "program", [node("conj:open", status="open", kind="conjecture")])
        self.add_checkpoint("anchored", approach="ap:real")

        self.assertIn("names an approach, but this repository has no "
                      "research/program/portfolio.yaml", self.errors())

    def test_supersession_points_backwards_at_the_same_genre(self):
        self.add_ledger("program", "program", [node("conj:open", status="open", kind="conjecture")])
        first = self.add_checkpoint("first", nodes=("conj:open",))
        second = self.add_checkpoint("second", date="2026-08-27", nodes=("conj:open",),
                                     supersedes=(first,))
        self.add_checkpoint("backwards", date="2026-08-28", nodes=("conj:open",),
                            supersedes=(second, "research/explorations/2026-08-29-later.md"))
        self.add_checkpoint("later", date="2026-08-29", nodes=("conj:open",))
        self.add_checkpoint("selfish", date="2026-08-30", nodes=("conj:open",),
                            supersedes=("research/explorations/2026-08-30-selfish.md",))
        self.add_checkpoint("wrong-genre", date="2026-08-31", nodes=("conj:open",),
                            supersedes=("research/reviews/2026-08-25-audit.md",))

        errors = self.errors()

        self.assertIn("'research/explorations/2026-08-29-later.md' is not older than this "
                      "record", errors)
        self.assertIn("a record cannot supersede itself", errors)
        self.assertIn("'research/reviews/2026-08-25-audit.md' must stay under "
                      "research/explorations/", errors)
        self.assertNotIn("2026-08-27-second.md.supersedes", errors)

    def test_superseded_checkpoints_leave_the_current_heads(self):
        """Supersession changes what to read first; it deletes nothing."""
        self.add_ledger("program", "program", [node("conj:open", status="open", kind="conjecture")])
        first = self.add_checkpoint("first", nodes=("conj:open",))
        second = self.add_checkpoint("second", date="2026-08-27", nodes=("conj:open",),
                                     supersedes=(first,))

        report = self.check()
        memory = report["checkpoints"]

        self.assertEqual(failures(report), [])
        self.assertEqual(len(memory["records"]), 2)
        self.assertEqual(memory["superseded"], {first: [second]})

    def test_an_audit_may_be_superseded_but_a_proof_review_may_not(self):
        self.add_ledger("program", "program", [node("conj:open", status="open", kind="conjecture")])
        stale = self.add_review("stale-audit", report_type="audit", date="2026-08-25")
        fresh = self.add_review("current-audit", report_type="audit", date="2026-08-26",
                                supersedes=(stale,))
        solution = self.add_solution("proof", node_ids=("conj:open",))
        review = self.add_review("proof-review", date="2026-08-27",
                                 node_ids=("conj:open",), solutions=(solution,))
        replacing = self.root / "research/reviews/2026-08-28-replaces-a-proof.md"
        replacing.write_text(
            "---\ntype: audit\ndate: '2026-08-28'\n"
            f"supersedes: [{review}]\n---\n"
        )

        report = self.check()
        errors = "\n".join(failures(report))

        self.assertIn(f"'{review}' is not an audit", errors)
        self.assertEqual(report["checkpoints"]["superseded_audits"], {stale: [fresh]})

    def test_promotion_ends_a_candidate_in_one_act(self):
        """Adding the node while leaving the candidate live left one statement two homes."""
        self.add_ledger("program", "program",
                        [node("lem:stability", status="open", kind="lemma")])
        self.add_checkpoint(
            "proposal", date="2026-08-20", outcome="candidate",
            candidates=[{"id": "cand:stability", "statement": "A precise statement."}],
        )
        self.add_checkpoint(
            "promotion", date="2026-08-21", outcome="proposed", nodes=("lem:stability",),
            promotes=[{"candidate": "cand:stability", "node": "lem:stability"}],
        )

        report = self.check()

        self.assertEqual(failures(report, ("checkpoints",)), [])
        self.assertEqual([entry["id"] for entry in report["candidates"]], [])
        self.assertEqual(report["checkpoints"]["promoted"]["cand:stability"]["node"],
                         "lem:stability")

    def test_a_same_day_promotion_after_its_proposal_is_accepted(self):
        """Filename order supplies no chronology for two untimed same-day records."""
        self.add_ledger("program", "program",
                        [node("lem:stability", status="open", kind="lemma")])
        self.add_checkpoint(
            "zebra-proposal", date="2026-08-20", outcome="candidate",
            candidates=[{"id": "cand:stability", "statement": "A precise statement."}],
        )
        self.add_checkpoint(
            "alpha-promotion", date="2026-08-20", outcome="proposed",
            nodes=("lem:stability",),
            promotes=[{"candidate": "cand:stability", "node": "lem:stability"}],
        )

        report = self.check()

        self.assertEqual(failures(report, ("checkpoints",)), [])
        self.assertEqual([entry["id"] for entry in report["candidates"]], [])

    def test_a_utc_timestamp_still_orders_two_records_within_one_day(self):
        """Ambiguity is the default, not the ceiling: a record that wants to be ordered
        says so with a timestamp, and then the check bites again."""
        self.add_ledger("program", "program",
                        [node("lem:stability", status="open", kind="lemma")])
        self.add_checkpoint(
            "proposal", date="2026-08-20T15:00:00Z", outcome="candidate",
            candidates=[{"id": "cand:stability", "statement": "A precise statement."}],
        )
        self.add_checkpoint(
            "promotion", date="2026-08-20T09:00:00Z", outcome="proposed",
            nodes=("lem:stability",),
            promotes=[{"candidate": "cand:stability", "node": "lem:stability"}],
        )

        errors = self.errors()

        self.assertIn("'cand:stability' is promoted before", errors)

    def test_a_same_day_supersession_cycle_is_rejected(self):
        """Same-day records have no strict order, so acyclicity is checked directly."""
        self.add_ledger("program", "program", [node("lem:x", status="open", kind="lemma")])
        first = self.add_checkpoint("first", date="2026-08-20", nodes=("lem:x",))
        second = self.add_checkpoint("second", date="2026-08-20", nodes=("lem:x",),
                                     supersedes=(first,))
        self.add_checkpoint("first", date="2026-08-20", nodes=("lem:x",),
                            supersedes=(second,))

        errors = self.errors()

        self.assertIn("supersession cycle", errors)

    def test_two_records_on_one_day_may_supersede_in_either_direction(self):
        """A legitimate same-day supersession is accepted whichever way the slugs sort."""
        self.add_ledger("program", "program", [node("lem:x", status="open", kind="lemma")])
        stale = self.add_checkpoint("zebra", date="2026-08-20", nodes=("lem:x",))
        self.add_checkpoint("alpha", date="2026-08-20", nodes=("lem:x",),
                            supersedes=(stale,))

        report = self.check()

        self.assertEqual(failures(report, ("checkpoints",)), [])

    def test_a_promotion_names_a_node_that_actually_exists(self):
        self.add_ledger("program", "program",
                        [node("lem:real", status="open", kind="lemma")])
        self.add_checkpoint(
            "proposal", date="2026-08-20", outcome="candidate",
            candidates=[{"id": "cand:stability", "statement": "A precise statement."}],
        )
        self.add_checkpoint(
            "promotion", date="2026-08-21", outcome="proposed", nodes=("lem:real",),
            promotes=[{"candidate": "cand:stability", "node": "lem:ghost"}],
        )

        errors = self.errors()

        self.assertIn("promotes: 'lem:ghost' is not a ledger node id", errors)

    def test_a_promoted_candidate_is_not_retired_a_second_time(self):
        self.add_ledger("program", "program",
                        [node("lem:stability", status="open", kind="lemma")])
        self.add_checkpoint(
            "proposal", date="2026-08-20", outcome="candidate",
            candidates=[{"id": "cand:stability", "statement": "A precise statement."}],
        )
        self.add_checkpoint(
            "promotion", date="2026-08-21", outcome="proposed", nodes=("lem:stability",),
            promotes=[{"candidate": "cand:stability", "node": "lem:stability"}],
        )
        self.add_checkpoint(
            "retirement", date="2026-08-22", outcome="dead-end", nodes=("lem:stability",),
            retires=("cand:stability",),
        )

        errors = self.errors()

        self.assertIn("was promoted to 'lem:stability'", errors)


if __name__ == "__main__":
    unittest.main()
