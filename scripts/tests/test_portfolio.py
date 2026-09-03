"""Portfolio plane: the search state, and everything it is not allowed to become.

The rules under test are all structural. Whether two routes are really the same idea,
and whether a family is really exhausted, are synthesizer judgments the checker refuses
to guess at (CLAUDE.md constraint 12).
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fixtures import CheckerFixture, node  # noqa: E402


def target_ledger(case: CheckerFixture) -> None:
    case.add_ledger("program", "program", [
        node("q:target", status="open", kind="question"),
        node("obs:fence", status="open", kind="obstruction"),
    ])


class PortfolioTests(CheckerFixture):
    def test_an_absent_portfolio_is_not_an_error(self):
        """Activation is structural: no portfolio means no portfolio rules."""
        target_ledger(self)

        self.assertEqual(self.errors(), "")
        self.assertIsNone(self.check()["portfolio"])

    def test_ids_are_namespaced_unique_and_resolve(self):
        target_ledger(self)
        self.add_portfolio({
            "target": "q:ghost",
            "families": [
                {"id": "fam:one", "mechanism": "M", "state": "active"},
                {"id": "fam:one", "mechanism": "M", "state": "active"},
                {"id": "localization", "mechanism": "M", "state": "active"},
            ],
            "approaches": [
                {"id": "ap:orphan", "family": "fam:missing", "state": "queued"},
                {"id": "cand:wrong-namespace", "family": "fam:one", "state": "queued"},
            ],
        })

        errors = self.errors()

        self.assertIn("families: duplicate id 'fam:one'", errors)
        self.assertIn("want an id of the form 'fam:<slug>', got 'localization'", errors)
        self.assertIn("want an id of the form 'ap:<slug>', got 'cand:wrong-namespace'", errors)
        self.assertIn("ap:orphan.family: 'fam:missing' is not a family", errors)
        self.assertIn("target: 'q:ghost' is not a ledger node id", errors)

    def test_a_blocked_route_names_its_blocker_and_its_reopening_condition(self):
        target_ledger(self)
        self.add_portfolio({
            "target": "q:target",
            "families": [{"id": "fam:one", "mechanism": "M", "state": "active"}],
            "approaches": [
                {"id": "ap:vague", "family": "fam:one", "state": "blocked"},
                {"id": "ap:fenced", "family": "fam:one", "state": "blocked",
                 "blocker": "obs:fence", "reopen_if": "a new mechanism appears"},
                {"id": "ap:premature", "family": "fam:one", "state": "queued",
                 "blocker": "obs:fence"},
            ],
        })

        errors = self.errors()

        self.assertIn("ap:vague.blocker: a blocked approach names the exact", errors)
        self.assertIn("ap:vague.reopen_if: a blocked approach names the", errors)
        self.assertIn("ap:premature.blocker: valid only for a blocked approach", errors)
        self.assertNotIn("ap:fenced", errors)

    def test_a_blocker_must_resolve_to_a_node_or_a_live_candidate(self):
        """A route worth formally blocking has a lemma worth stating precisely."""
        target_ledger(self)
        self.add_checkpoint("propose", outcome="candidate",
                            candidates=({"id": "cand:gap", "statement": "S"},))
        self.add_portfolio({
            "target": "q:target",
            "families": [{"id": "fam:one", "mechanism": "M", "state": "active"}],
            "approaches": [
                {"id": "ap:on-candidate", "family": "fam:one", "state": "blocked",
                 "blocker": "cand:gap", "reopen_if": "it is proved"},
                {"id": "ap:on-node", "family": "fam:one", "state": "blocked",
                 "blocker": "obs:fence", "reopen_if": "the fence moves"},
                {"id": "ap:on-prose", "family": "fam:one", "state": "blocked",
                 "blocker": "the compatibility condition seems hard",
                 "reopen_if": "someone has an idea"},
            ],
        })

        errors = self.errors()

        self.assertIn("ap:on-prose.blocker: 'the compatibility condition seems hard' is "
                      "neither a ledger node nor a live candidate", errors)
        self.assertNotIn("ap:on-candidate", errors)
        self.assertNotIn("ap:on-node", errors)

    def test_a_retired_candidate_no_longer_blocks_a_route(self):
        target_ledger(self)
        self.add_checkpoint("propose", outcome="candidate",
                            candidates=({"id": "cand:gap", "statement": "S"},))
        self.add_checkpoint("kill", date="2026-08-27", nodes=("q:target",),
                            retires=("cand:gap",))
        self.add_portfolio({
            "target": "q:target",
            "families": [{"id": "fam:one", "mechanism": "M", "state": "active"}],
            "approaches": [{"id": "ap:stale", "family": "fam:one", "state": "blocked",
                            "blocker": "cand:gap", "reopen_if": "never"}],
        })

        self.assertIn("ap:stale.blocker: 'cand:gap' is neither a ledger node nor a live "
                      "candidate", self.errors())

    def test_a_closed_family_owes_a_synthesis_and_a_reopening_condition(self):
        target_ledger(self)
        checkpoint = self.add_checkpoint("synthesis", nodes=("q:target",))
        self.add_portfolio({
            "target": "q:target",
            "families": [
                {"id": "fam:bare", "mechanism": "M", "state": "saturated"},
                {"id": "fam:complete", "mechanism": "M", "state": "parked",
                 "saturation_checkpoint": checkpoint, "reopen_if": "a new mechanism"},
                {"id": "fam:overreaching", "mechanism": "M", "state": "active",
                 "reopen_if": "meaningless while active"},
            ],
        })

        errors = self.errors()

        self.assertIn("fam:bare.saturation_checkpoint: state 'saturated' requires", errors)
        self.assertIn("fam:bare.reopen_if: state 'saturated' requires", errors)
        self.assertIn("fam:overreaching.reopen_if: valid only for a saturated or parked "
                      "family", errors)
        self.assertNotIn("fam:complete", errors)

    def test_a_closed_family_cannot_hold_an_active_route(self):
        target_ledger(self)
        checkpoint = self.add_checkpoint("synthesis", nodes=("q:target",))
        self.add_portfolio({
            "target": "q:target",
            "families": [{"id": "fam:closed", "mechanism": "M", "state": "saturated",
                          "saturation_checkpoint": checkpoint, "reopen_if": "a new idea"}],
            "approaches": [
                {"id": "ap:still-running", "family": "fam:closed", "state": "active"},
                {"id": "ap:done", "family": "fam:closed", "state": "completed"},
            ],
        })

        self.assertIn("fam:closed: state 'saturated' with active approach(es) "
                      "['ap:still-running']", self.errors())

    def test_the_tree_is_acyclic_and_stays_inside_one_family(self):
        target_ledger(self)
        self.add_portfolio({
            "target": "q:target",
            "families": [
                {"id": "fam:one", "mechanism": "M", "state": "active"},
                {"id": "fam:two", "mechanism": "M", "state": "active"},
            ],
            "approaches": [
                {"id": "ap:a", "family": "fam:one", "parent": "ap:b", "state": "queued"},
                {"id": "ap:b", "family": "fam:one", "parent": "ap:a", "state": "queued"},
                {"id": "ap:self", "family": "fam:one", "parent": "ap:self",
                 "state": "queued"},
                {"id": "ap:crossing", "family": "fam:two", "parent": "ap:a",
                 "state": "queued"},
            ],
        })

        errors = self.errors()

        self.assertIn("ap:a.parent: approach ancestry contains a cycle", errors)
        self.assertIn("ap:self.parent: an approach cannot parent itself", errors)
        self.assertIn("ap:crossing.parent: 'ap:a' is in family 'fam:one'", errors)

    def test_duplicate_routes_are_declared_and_never_both_active(self):
        target_ledger(self)
        self.add_portfolio({
            "target": "q:target",
            "families": [{"id": "fam:one", "mechanism": "M", "state": "active"}],
            "approaches": [
                {"id": "ap:original", "family": "fam:one", "state": "active"},
                {"id": "ap:undeclared", "family": "fam:one", "state": "duplicate"},
                {"id": "ap:rival", "family": "fam:one", "state": "active",
                 "related": [{"to": "ap:original", "relation": "duplicates"}]},
                {"id": "ap:bad-relation", "family": "fam:one", "state": "queued",
                 "related": [{"to": "ap:ghost", "relation": "overlaps"},
                             {"to": "ap:original", "relation": "supersedes"}]},
            ],
        })

        errors = self.errors()

        self.assertIn("ap:undeclared: state 'duplicate' requires a related entry", errors)
        self.assertIn("ap:rival: duplicates 'ap:original', so both cannot be active", errors)
        self.assertIn("to: 'ap:ghost' is not an approach", errors)
        self.assertIn("relation: want one of ['duplicates', 'overlaps', 'refines'], "
                      "got 'supersedes'", errors)

    def test_checkpoint_references_must_resolve(self):
        target_ledger(self)
        self.add_portfolio({
            "target": "q:target",
            "families": [{"id": "fam:one", "mechanism": "M", "state": "active"}],
            "approaches": [{"id": "ap:one", "family": "fam:one", "state": "queued",
                            "checkpoints": ["research/explorations/2026-01-01-ghost.md",
                                            "solutions/not-a-checkpoint.tex"]}],
        })

        errors = self.errors()

        self.assertIn("'research/explorations/2026-01-01-ghost.md' does not exist", errors)
        self.assertIn("'solutions/not-a-checkpoint.tex' must stay under "
                      "research/explorations/", errors)

    def test_the_portfolio_holds_no_mathematics(self):
        """Unknown fields are how a statement would try to sneak in."""
        target_ledger(self)
        self.add_portfolio({
            "target": "q:target",
            "conjecture": "an inequality nobody validated",
            "families": [{"id": "fam:one", "mechanism": "M", "state": "active",
                          "statement": "smuggled"}],
            "approaches": [{"id": "ap:one", "family": "fam:one", "state": "queued",
                            "status": "proved"}],
        })

        errors = self.errors()

        self.assertIn("unknown top-level field 'conjecture'", errors)
        self.assertIn("fam:one: unknown field 'statement'", errors)
        self.assertIn("ap:one: unknown field 'status'", errors)

    def test_the_ledger_rejects_search_state(self):
        """The reverse direction of constraint 12: no route lives in the claim graph."""
        self.add_ledger("program", "program", [
            node("q:target", status="open", kind="question",
                 approach="ap:one", family="fam:one"),
        ])

        errors = self.errors()

        self.assertIn("q:target.approach: obsolete field; use the search portfolio", errors)
        self.assertIn("q:target.family: obsolete field; use the search portfolio", errors)

    def test_the_brief_scopes_one_ledger_node_and_agrees_with_the_portfolio(self):
        target_ledger(self)
        self.add_brief("q:ghost")
        self.add_portfolio({
            "target": "q:target",
            "families": [{"id": "fam:one", "mechanism": "M", "state": "active"}],
        })

        errors = self.errors()

        self.assertIn("brief.md.target: 'q:ghost' is not a ledger node id", errors)
        self.assertIn("disagrees with the problem brief's target", errors)

    def test_an_agreeing_brief_and_portfolio_pass(self):
        target_ledger(self)
        self.add_brief("q:target")
        self.add_portfolio({
            "target": "q:target",
            "families": [{"id": "fam:one", "mechanism": "M", "state": "active"}],
            "approaches": [{"id": "ap:one", "family": "fam:one", "state": "active"}],
        })

        self.assertEqual(self.errors(), "")


if __name__ == "__main__":
    unittest.main()
