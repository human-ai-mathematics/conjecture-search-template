"""Search state: the brief, the portfolio of routes, the checkpoint log and its candidates."""
from __future__ import annotations

import unittest

from fixtures import CheckerFixture, node

TARGET = node("conj:main", kind="conjecture", status="open")


class CheckpointTests(CheckerFixture):
    def test_a_checkpoint_is_dated_by_its_name_and_resolves_what_it_cites(self):
        self.ledger([TARGET])
        self.write("research/runs/out.jsonl", "{}\n")
        self.checkpoint("good", artifacts=["research/runs/out.jsonl"])
        self.assertClean()
        self.checkpoint("bad", date="2026-08-27", outcome="dead-end", nodes=["conj:main"],
                        artifacts=["solutions/x.md", "research/runs/missing.jsonl"])
        self.write("research/explorations/undated.md", "---\n---\n")
        self.write("research/explorations/2026-08-28-typed.md", "---\ntype: exploration\n---\n")
        errors = self.errors()
        self.assertIn("unknown field 'outcome'", errors)
        self.assertIn("unknown field 'nodes'", errors)
        self.assertIn("'solutions/x.md' must be under research/runs/", errors)
        self.assertIn("'research/runs/missing.jsonl' does not exist", errors)
        self.assertIn("undated.md: name it '<YYYY-MM-DD>-<slug>.md'", errors)
        self.assertIn("typed.md: unknown field 'type'", errors)

    def test_a_candidate_is_live_until_a_checkpoint_closes_it(self):
        self.ledger([TARGET])
        self.checkpoint("propose", candidates=[
            {"id": "cand:a", "statement": "A holds."},
            {"id": "cand:b", "statement": "B holds."},
        ])
        self.assertEqual(sorted(self.check()["candidates"]), ["cand:a", "cand:b"])
        self.checkpoint("close", date="2026-08-27", closes=["cand:a"])
        self.assertEqual(sorted(self.check()["candidates"]), ["cand:b"])
        self.assertClean()

    def test_candidate_ids_are_namespaced_unique_and_never_node_ids(self):
        self.ledger([TARGET, node("cand:taken", kind="lemma", status="open")])
        self.checkpoint("one", candidates=[{"id": "cand:a", "statement": "A."},
                                           {"id": "cand:taken", "statement": "T."},
                                           {"id": "lemma-a", "statement": "L."},
                                           {"id": "cand:empty", "statement": " "}])
        self.checkpoint("two", date="2026-08-27", candidates=[{"id": "cand:a", "statement": "A."}])
        errors = self.errors()
        self.assertIn("'cand:a' was already proposed", errors)
        self.assertIn("candidate 'cand:taken' is also a node id", errors)
        self.assertIn("want entries {id: cand:<slug>, statement}", errors)
        self.assertIn("cand:empty: needs exactly an id and a statement", errors)

    def test_only_a_proposed_open_candidate_can_be_closed(self):
        self.ledger([TARGET])
        self.checkpoint("propose", candidates=[{"id": "cand:a", "statement": "A."}])
        self.checkpoint("close", date="2026-08-27", closes=["cand:a", "cand:never"])
        self.checkpoint("again", date="2026-08-28", closes=["cand:a"])
        errors = self.errors()
        self.assertIn("'cand:never' was not proposed by an earlier checkpoint", errors)
        self.assertIn("'cand:a' is already closed", errors)

    def test_a_checkpoint_closes_only_what_an_earlier_one_proposed(self):
        self.ledger([TARGET])
        self.checkpoint("early", closes=["cand:later", "cand:same"],
                        candidates=[{"id": "cand:same", "statement": "S."}])
        self.checkpoint("late", date="2026-08-27",
                        candidates=[{"id": "cand:later", "statement": "L."}])
        errors = self.errors()
        self.assertIn("early.md.closes: 'cand:later' was not proposed by an earlier", errors)
        self.assertIn("early.md.closes: 'cand:same' was not proposed by an earlier", errors)


class PortfolioTests(CheckerFixture):
    def test_a_route_may_name_its_next_test_and_is_traced_to_its_last_checkpoint(self):
        self.ledger([TARGET])
        self.portfolio({"id": "ap:a", "state": "active", "next": "Try n = 3."},
                       {"id": "ap:b", "state": "active", "next": " "},
                       {"id": "ap:a-bis", "state": "closed"})
        self.checkpoint("one", date="2026-08-26")
        self.write("research/explorations/2026-08-26-one.md", "---\n---\nWork on ap:a.\n")
        self.write("research/explorations/2026-08-27-two.md", "---\n---\nap:a-bis died.\n")
        report = self.check()
        self.assertEqual(report["mentions"], {
            "ap:a": "research/explorations/2026-08-26-one.md",
            "ap:b": None, "ap:a-bis": "research/explorations/2026-08-27-two.md"})
        self.assertEqual(report["latest"], "research/explorations/2026-08-27-two.md")
        self.assertIn("ap:b.next: the next test that would move the route",
                      "\n".join(report["errors"]))

    def test_brief_and_portfolio_are_optional(self):
        self.ledger([TARGET])
        self.assertClean()

    def test_the_brief_targets_a_ledger_node(self):
        self.ledger([TARGET])
        self.brief("conj:ghost")
        self.assertIn("brief.md.target: 'conj:ghost' is not a ledger node", self.errors())

    def test_routes_are_namespaced_unique_and_say_what_they_try(self):
        self.ledger([TARGET])
        self.portfolio({"id": "ap:a", "state": "active"}, {"id": "ap:a", "state": "active"},
                       {"id": "route-b", "state": "active"},
                       {"id": "ap:c", "state": "queued", "objective": " ", "owner": "x"})
        errors = self.errors()
        self.assertIn("duplicate approach 'ap:a'", errors)
        self.assertIn("approach #3 needs an id 'ap:<slug>'", errors)
        self.assertIn("ap:c.state: want one of ['active', 'blocked', 'closed']", errors)
        self.assertIn("ap:c.objective: one sentence", errors)
        self.assertIn("ap:c: unknown field 'owner'", errors)

    def test_a_blocked_route_names_a_live_blocker(self):
        self.ledger([TARGET, node("lem:gap", kind="lemma", status="open"),
                     node("lem:done", kind="lemma")])
        self.checkpoint("propose", candidates=[{"id": "cand:live", "statement": "L."},
                                               {"id": "cand:dead", "statement": "D."}])
        self.checkpoint("close", date="2026-08-27", closes=["cand:dead"])
        self.portfolio(
            {"id": "ap:node", "state": "blocked", "blocker": "lem:gap", "reopen_if": "proved"},
            {"id": "ap:cand", "state": "blocked", "blocker": "cand:live"},
            {"id": "ap:dead", "state": "blocked", "blocker": "cand:dead"},
            {"id": "ap:settled", "state": "blocked", "blocker": "lem:done"},
            {"id": "ap:bare", "state": "blocked"},
            {"id": "ap:free", "state": "active", "blocker": "lem:gap", "reopen_if": "x"},
        )
        errors = self.errors()
        self.assertNotIn("ap:node", errors)
        self.assertNotIn("ap:cand", errors)
        self.assertIn("ap:dead.blocker: 'cand:dead' is neither a ledger node nor a live", errors)
        self.assertIn("ap:bare.blocker: required when blocked", errors)
        self.assertIn("ap:settled.blocker: 'lem:done' is now proved; reopen or close", errors)
        self.assertIn("ap:free.blocker: only for a blocked route", errors)
        self.assertIn("ap:free.reopen_if: only for a blocked route", errors)

    def test_a_settled_target_leaves_no_active_route(self):
        self.ledger([node("conj:main", kind="conjecture", status="refuted",
                          refuted_by=["prop:cx"]), node("prop:cx", kind="proposition")])
        self.brief("conj:main")
        self.portfolio({"id": "ap:a", "state": "active"}, {"id": "ap:b", "state": "closed"})
        self.assertIn("the target 'conj:main' is refuted; close ap:a", self.errors())


if __name__ == "__main__":
    unittest.main()
