"""Portfolio lane: the search state, and everything it is not allowed to become.

The rules under test are all structural. Whether two routes are really the same idea,
and whether a family is really exhausted, are synthesizer judgments the checker refuses
to guess at (CLAUDE.md constraint 11).
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fixtures import CheckerFixture, node  # noqa: E402


def target_ledger(case: CheckerFixture) -> None:
    case.add_ledger("program", "program", [
        node("conj:target", status="open", kind="conjecture"),
        node("obs:fence", status="open", kind="conjecture"),
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
            "target": "conj:ghost",
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
        self.assertIn("target: 'conj:ghost' is not a ledger node id", errors)

    def test_a_blocked_route_names_its_blocker_and_its_reopening_condition(self):
        target_ledger(self)
        vague = self.add_checkpoint("vague", nodes=("conj:target",), approach="ap:vague")
        fenced = self.add_checkpoint("fenced", nodes=("conj:target",), approach="ap:fenced")
        self.add_portfolio({
            "target": "conj:target",
            "families": [{"id": "fam:one", "mechanism": "M", "state": "active"}],
            "approaches": [
                {"id": "ap:vague", "family": "fam:one", "state": "blocked",
                 "checkpoints": [vague]},
                {"id": "ap:fenced", "family": "fam:one", "state": "blocked",
                 "blocker": "obs:fence", "reopen_if": "a new mechanism appears",
                 "checkpoints": [fenced]},
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
        candidate = self.add_checkpoint(
            "propose", outcome="candidate", approach="ap:on-candidate",
            candidates=({"id": "cand:gap", "statement": "S"},),
        )
        on_node = self.add_checkpoint("on-node", nodes=("conj:target",), approach="ap:on-node")
        on_prose = self.add_checkpoint("on-prose", nodes=("conj:target",), approach="ap:on-prose")
        self.add_portfolio({
            "target": "conj:target",
            "families": [{"id": "fam:one", "mechanism": "M", "state": "active"}],
            "approaches": [
                {"id": "ap:on-candidate", "family": "fam:one", "state": "blocked",
                 "blocker": "cand:gap", "reopen_if": "it is proved",
                 "checkpoints": [candidate]},
                {"id": "ap:on-node", "family": "fam:one", "state": "blocked",
                 "blocker": "obs:fence", "reopen_if": "the fence moves",
                 "checkpoints": [on_node]},
                {"id": "ap:on-prose", "family": "fam:one", "state": "blocked",
                 "blocker": "the missing estimate seems hard",
                 "reopen_if": "someone has an idea", "checkpoints": [on_prose]},
            ],
        })

        errors = self.errors()

        self.assertIn("ap:on-prose.blocker: 'the missing estimate seems hard' is "
                      "neither a ledger node nor a live candidate", errors)
        self.assertNotIn("ap:on-candidate", errors)
        self.assertNotIn("ap:on-node", errors)

    def test_a_retired_candidate_no_longer_blocks_a_route(self):
        target_ledger(self)
        self.add_checkpoint("propose", outcome="candidate",
                            candidates=({"id": "cand:gap", "statement": "S"},))
        why = self.add_checkpoint("kill", date="2026-08-27", nodes=("conj:target",),
                                  retires=("cand:gap",))
        self.add_portfolio({
            "target": "conj:target",
            "families": [{"id": "fam:one", "mechanism": "M", "state": "active"}],
            "approaches": [{"id": "ap:stale", "family": "fam:one", "state": "blocked",
                            "blocker": "cand:gap", "reopen_if": "never",
                            "checkpoints": [why]}],
        })

        self.assertIn("ap:stale.blocker: 'cand:gap' is neither a ledger node nor a live "
                      "candidate", self.errors())

    def test_a_closed_family_owes_a_synthesis_and_a_reopening_condition(self):
        target_ledger(self)
        checkpoint = self.add_checkpoint("synthesis", nodes=("conj:target",),
                                         approach="ap:complete")
        self.add_portfolio({
            "target": "conj:target",
            "families": [
                {"id": "fam:bare", "mechanism": "M", "state": "saturated"},
                {"id": "fam:complete", "mechanism": "M", "state": "parked",
                 "closure_checkpoint": checkpoint, "reopen_if": "a new mechanism"},
                {"id": "fam:overreaching", "mechanism": "M", "state": "active",
                 "reopen_if": "meaningless while active"},
            ],
            "approaches": [
                {"id": "ap:complete", "family": "fam:complete", "state": "completed",
                 "checkpoints": [checkpoint]},
            ],
        })

        errors = self.errors()

        self.assertIn("fam:bare.closure_checkpoint: state 'saturated' requires", errors)
        self.assertIn("fam:bare.reopen_if: state 'saturated' requires", errors)
        self.assertIn("fam:overreaching.reopen_if: valid only for a closed "
                      "(saturated or parked) family", errors)
        self.assertNotIn("fam:complete", errors)

    def test_a_closed_family_cannot_hold_an_active_or_queued_route(self):
        """A queued route is planned live work, so the family has not actually closed."""
        target_ledger(self)
        checkpoint = self.add_checkpoint("synthesis", nodes=("conj:target",),
                                         approach="ap:done")
        self.add_portfolio({
            "target": "conj:target",
            "families": [{"id": "fam:closed", "mechanism": "M", "state": "saturated",
                          "closure_checkpoint": checkpoint, "reopen_if": "a new idea"}],
            "approaches": [
                {"id": "ap:still-running", "family": "fam:closed", "state": "active"},
                {"id": "ap:next-up", "family": "fam:closed", "state": "queued"},
                {"id": "ap:done", "family": "fam:closed", "state": "completed",
                 "checkpoints": [checkpoint]},
            ],
        })

        errors = self.errors()

        self.assertIn("fam:closed: state 'saturated' with live approach(es) "
                      "['ap:next-up', 'ap:still-running']", errors)
        self.assertNotIn("ap:done", errors)

    def test_the_tree_is_acyclic_and_stays_inside_one_family(self):
        target_ledger(self)
        self.add_portfolio({
            "target": "conj:target",
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
            "target": "conj:target",
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
            "target": "conj:target",
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
            "target": "conj:target",
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
        """The claim graph accepts only its current mathematical-state fields."""
        self.add_ledger("program", "program", [
            node("conj:target", status="open", kind="conjecture",
                 approach="ap:one", family="fam:one"),
        ])

        errors = self.errors()

        self.assertIn("conj:target: unknown field 'approach'", errors)
        self.assertIn("conj:target: unknown field 'family'", errors)

    def test_a_state_change_owes_a_checkpoint_that_explains_it(self):
        """Checkpoints = why the portfolio changed. A route does not stop for no reason."""
        target_ledger(self)
        why = self.add_checkpoint("why", nodes=("conj:target",), approach="ap:explained")
        self.add_portfolio({
            "target": "conj:target",
            "families": [{"id": "fam:one", "mechanism": "M", "state": "active"}],
            "approaches": [
                {"id": "ap:silent-block", "family": "fam:one", "state": "blocked",
                 "blocker": "obs:fence", "reopen_if": "the fence moves"},
                {"id": "ap:silent-done", "family": "fam:one", "state": "completed"},
                {"id": "ap:silent-dupe", "family": "fam:one", "state": "duplicate",
                 "related": [{"to": "ap:explained", "relation": "duplicates"}]},
                {"id": "ap:queued-is-fine", "family": "fam:one", "state": "queued"},
                {"id": "ap:explained", "family": "fam:one", "state": "completed",
                 "checkpoints": [why]},
            ],
        })

        errors = self.errors()

        for approach_id in ("ap:silent-block", "ap:silent-done", "ap:silent-dupe"):
            self.assertIn(f"{approach_id}.checkpoints: state", errors)
        self.assertNotIn("ap:queued-is-fine", errors)
        self.assertNotIn("ap:explained", errors)

    def test_a_checkpoint_reference_resolves_through_the_parsed_index(self):
        """Existing on disk is not enough: a README is a file and is not durable memory."""
        target_ledger(self)
        readme = self.root / "research/explorations/README.md"
        readme.parent.mkdir(parents=True, exist_ok=True)
        readme.write_text("# Checkpoints\n\nThe contract, not a record.\n")
        self.add_portfolio({
            "target": "conj:target",
            "families": [{"id": "fam:one", "mechanism": "M", "state": "active"}],
            "approaches": [{"id": "ap:one", "family": "fam:one", "state": "queued",
                            "checkpoints": ["research/explorations/README.md"]}],
        })

        self.assertIn("'research/explorations/README.md' is not a checkpoint",
                      self.errors())

    def test_a_checkpoint_naming_an_approach_must_name_the_one_that_lists_it(self):
        target_ledger(self)
        theirs = self.add_checkpoint("theirs", nodes=("conj:target",), approach="ap:theirs")
        unanchored = self.add_checkpoint("unanchored", date="2026-08-27", nodes=("conj:target",))
        self.add_portfolio({
            "target": "conj:target",
            "families": [{"id": "fam:one", "mechanism": "M", "state": "active"}],
            "approaches": [
                {"id": "ap:theirs", "family": "fam:one", "state": "queued"},
                {"id": "ap:mine", "family": "fam:one", "state": "completed",
                 "checkpoints": [theirs, unanchored]},
            ],
        })

        errors = self.errors()

        self.assertIn("declares approach 'ap:theirs', which is not 'ap:mine'", errors)
        self.assertIn("does not declare an approach", errors)

    def test_a_closure_checkpoint_belongs_to_the_family_it_closes(self):
        target_ledger(self)
        outside = self.add_checkpoint("outside", nodes=("conj:target",),
                                      approach="ap:elsewhere")
        self.add_portfolio({
            "target": "conj:target",
            "families": [
                {"id": "fam:closed", "mechanism": "M", "state": "saturated",
                 "closure_checkpoint": outside, "reopen_if": "a new mechanism"},
                {"id": "fam:other", "mechanism": "M", "state": "active"},
            ],
            "approaches": [{"id": "ap:elsewhere", "family": "fam:other",
                            "state": "queued"}],
        })

        self.assertIn("declares approach 'ap:elsewhere', which is not an approach in "
                      "'fam:closed'", self.errors())

    def test_a_family_accepts_only_the_current_closure_field(self):
        target_ledger(self)
        checkpoint = self.add_checkpoint("synthesis", nodes=("conj:target",))
        self.add_portfolio({
            "target": "conj:target",
            "families": [{"id": "fam:one", "mechanism": "M", "state": "parked",
                          "saturation_checkpoint": checkpoint,
                          "reopen_if": "a new mechanism"}],
        })

        errors = self.errors()

        self.assertIn("fam:one: unknown field 'saturation_checkpoint'", errors)

    def test_an_unavailable_claim_graph_is_a_portfolio_dependency_error(self):
        """Scoping restricts what is reported; it never turns a missing check into a pass."""
        self.add_brief("conj:target")
        self.add_portfolio({
            "target": "conj:target",
            "families": [{"id": "fam:one", "mechanism": "M", "state": "active"}],
            "approaches": [{"id": "ap:one", "family": "fam:one", "state": "blocked",
                            "blocker": "obs:fence", "reopen_if": "the fence moves",
                            "checkpoints": []}],
        })

        errors = self.errors(lanes=("portfolio",))

        self.assertIn("the claim graph is unavailable or holds no nodes", errors)
        # The blocker check depends on the same missing lane, so it must not fire
        # a second, misleading error about a node that simply could not be loaded.
        self.assertNotIn("neither a ledger node nor a live candidate", errors)

    def test_the_brief_scopes_one_ledger_node_and_agrees_with_the_portfolio(self):
        target_ledger(self)
        self.add_brief("conj:ghost")
        self.add_portfolio({
            "target": "conj:target",
            "families": [{"id": "fam:one", "mechanism": "M", "state": "active"}],
        })

        errors = self.errors()

        self.assertIn("brief.md.target: 'conj:ghost' is not a ledger node id", errors)
        self.assertIn("disagrees with the problem brief's target", errors)

    def test_an_agreeing_brief_and_portfolio_pass(self):
        target_ledger(self)
        self.add_brief("conj:target")
        self.add_portfolio({
            "target": "conj:target",
            "families": [{"id": "fam:one", "mechanism": "M", "state": "active"}],
            "approaches": [{"id": "ap:one", "family": "fam:one", "state": "active"}],
        })

        self.assertEqual(self.errors(), "")

    def test_a_blocker_moves_with_the_candidate_it_names(self):
        """Promotion is atomic: the route follows the statement to its node."""
        self.add_ledger("program", "program", [
            node("conj:target", status="open", kind="conjecture"),
            node("lem:stability", status="open", kind="lemma"),
        ])
        self.add_checkpoint(
            "proposal", date="2026-08-20", outcome="candidate",
            candidates=[{"id": "cand:stability", "statement": "A precise statement."}],
        )
        self.add_checkpoint(
            "promotion", date="2026-08-21", outcome="proposed", nodes=("lem:stability",),
            promotes=[{"candidate": "cand:stability", "node": "lem:stability"}],
        )
        self.add_portfolio({
            "target": "conj:target",
            "families": [{"id": "fam:one", "mechanism": "M", "state": "active"}],
            "approaches": [{
                "id": "ap:stuck", "family": "fam:one", "state": "blocked",
                "blocker": "cand:stability", "reopen_if": "The lemma is proved.",
                "checkpoints": ["research/explorations/2026-08-20-proposal.md"],
            }],
        })

        errors = self.errors()

        self.assertIn("ap:stuck.blocker: 'cand:stability' was promoted to "
                      "'lem:stability'", errors)
        self.assertIn("block the route on the node instead", errors)

    def test_a_portfolio_without_a_brief_is_a_search_nobody_scoped(self):
        """Several coordinated routes are a sustained search, and one opens with a brief."""
        target_ledger(self)
        self.add_portfolio({
            "target": "conj:target",
            "families": [{"id": "fam:one", "mechanism": "M", "state": "active"}],
            "approaches": [{"id": "ap:one", "family": "fam:one", "state": "active"}],
        }, brief=False)

        errors = self.errors()

        self.assertIn("brief.md: a portfolio coordinates several routes", errors)

    def test_every_route_says_what_it_tries(self):
        target_ledger(self)
        self.add_portfolio({
            "target": "conj:target",
            "families": [{"id": "fam:one", "mechanism": "M", "state": "active"}],
            "approaches": [{"id": "ap:mute", "family": "fam:one", "state": "queued",
                            "objective": "   "}],
        })

        errors = self.errors()

        self.assertIn("ap:mute.objective: one sentence saying what this route tries",
                      errors)

    def test_a_search_is_not_aimed_at_a_definition_or_a_fence(self):
        self.add_ledger("program", "program", [
            node("def:convention", status="defined", kind="definition"),
        ])
        self.add_portfolio({
            "target": "def:convention",
            "families": [{"id": "fam:one", "mechanism": "M", "state": "active"}],
        })

        errors = self.errors()

        self.assertIn("target: 'def:convention' is a definition", errors)

    def test_a_node_cited_as_a_fence_is_not_a_target(self):
        """The fence role lives on the edges, so the target rule reads the edges."""
        self.add_ledger("program", "program", [
            node("conj:barrier", status="open", kind="conjecture"),
            node("conj:fenced", status="open", kind="conjecture",
                 heuristic_barriers=["conj:barrier"]),
        ])
        self.add_portfolio({
            "target": "conj:barrier",
            "families": [{"id": "fam:one", "mechanism": "M", "state": "active"}],
        })

        errors = self.errors()

        self.assertIn("target: 'conj:barrier' is a fence for conj:fenced", errors)

    def test_a_node_merely_citing_a_fence_can_be_a_target(self):
        self.add_ledger("program", "program", [
            node("conj:barrier", status="open", kind="conjecture"),
            node("conj:fenced", status="open", kind="conjecture",
                 heuristic_barriers=["conj:barrier"]),
        ])
        self.add_portfolio({
            "target": "conj:fenced",
            "families": [{"id": "fam:one", "mechanism": "M", "state": "active"}],
        })

        self.assertNotIn("is a fence", self.errors())

    def test_a_resolved_target_leaves_no_route_running(self):
        """The answer arrived; the routes it settled are not still being worked."""
        self.add_ledger("program", "program", [
            node("obs:witness"),
            node("conj:target", status="refuted", kind="conjecture",
                 refuted_by=["obs:witness"]),
        ])
        self.add_portfolio({
            "target": "conj:target",
            "families": [{"id": "fam:one", "mechanism": "M", "state": "active"}],
            "approaches": [{"id": "ap:still-going", "family": "fam:one", "state": "active"}],
        })

        errors = self.errors()

        self.assertIn("target 'conj:target' is refuted, but ap:still-going remain active "
                      "or queued", errors)


if __name__ == "__main__":
    unittest.main()
