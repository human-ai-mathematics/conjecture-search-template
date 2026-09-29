"""The reader's site: a page is stale once what it rests on moves, and --stamp is how it
catches up."""
from __future__ import annotations

import unittest
from datetime import date

from fixtures import CheckerFixture, node

from checks import analyze, site
from checks.common import text_fingerprint

TODAY = date(2026, 9, 29)


class SiteTests(CheckerFixture):
    def setUp(self):
        super().setUp()
        self.ledger([node("conj:a", kind="conjecture", status="open"), node("thm:b")])
        self.checkpoint("c", candidates=[{"id": "cand:x", "statement": "X holds."}])

    def stamp(self, *pages: str) -> list[str]:
        report = self.check()
        errors: list[str] = []
        site.stamp(self.root, list(pages), site.current(
            report["nodes"], self.anchors, report["proposed"]), TODAY, errors)
        return errors

    def warnings(self) -> str:
        return "\n".join(self.check()["warnings"])

    def stamped(self, name: str = "p", **fields) -> str:
        page = self.page(name, **{"relies-on": ["conj:a", "thm:b", "cand:x"], **fields})
        self.assertEqual(self.stamp(page), [])
        return page

    def test_a_stamped_page_is_current(self):
        page = self.stamped()
        self.assertEqual(self.check()["warnings"], [])
        self.assertEqual(self.check()["pages"], 1)
        text = (self.root / page).read_text()
        self.assertIn("checked: 2026-09-29", text)
        self.assertIn("*Last checked against the research record: 2026-09-29.*", text)
        self.assertTrue(text.rstrip().endswith("Exposition."))

    def test_stamping_is_idempotent_and_keeps_the_rest_of_the_page(self):
        page = self.stamped(numbering=False)
        first = (self.root / page).read_text()
        self.stamp(page)
        self.assertEqual((self.root / page).read_text(), first)
        self.assertIn("numbering: false", first)
        self.assertEqual(first.count(site.BEGIN), 1)

    def test_an_unstamped_page_is_stale(self):
        self.page("p", **{"relies-on": ["conj:a"]})
        self.assertIn("never stamped", self.warnings())
        self.page("q")
        self.assertIn("site/q.md: stale: no 'checked' date", self.warnings())

    def test_a_status_change_makes_the_page_stale(self):
        self.stamped()
        self.ledger([node("conj:a", kind="conjecture", status="refuted",
                          refuted_by=["thm:b"]), node("thm:b")])
        self.assertIn("'conj:a' is now refuted, the page says open", self.warnings())

    def test_an_edited_statement_makes_the_page_stale(self):
        self.stamped()
        self.edit_statement("conj:a")
        self.assertIn("the statement of 'conj:a' changed", self.warnings())

    def test_a_fast_check_compares_statuses_but_not_node_statements(self):
        self.stamped()
        self.edit_statement("conj:a")
        self.assertEqual(analyze(self.root, fast=True)["warnings"], [])

    def test_a_candidate_is_fingerprinted_by_its_statement_not_its_layout(self):
        self.stamped()
        self.checkpoint("c", candidates=[{"id": "cand:x", "statement": "X\n   holds."}])
        self.assertEqual(self.check()["warnings"], [])
        self.checkpoint("c", candidates=[{"id": "cand:x", "statement": "X fails."}])
        self.assertIn("the statement of 'cand:x' changed", self.warnings())
        self.assertEqual(text_fingerprint("a  b\nc"), text_fingerprint("a b c"))

    def test_a_closed_candidate_makes_the_page_stale(self):
        self.stamped()
        self.checkpoint("d", date="2026-08-27", closes=["cand:x"])
        self.assertIn("'cand:x' is now closed, the page says live", self.warnings())

    def test_a_vanished_id_makes_the_page_stale(self):
        self.stamped()
        (self.root / "research/explorations/2026-08-26-c.md").unlink()
        self.assertIn("'cand:x' no longer exists", self.warnings())

    def test_a_hand_edited_block_makes_the_page_stale(self):
        page = self.root / self.stamped()
        page.write_text(page.read_text().replace("Last checked", "Checked"))
        self.assertIn("stamp block is missing or was edited by hand", self.warnings())

    def test_a_problem_card_shows_the_status_of_its_problem(self):
        page = self.write("site/open/a.md", "---\nproblem: conj:a\nrelies-on: [conj:a]\n---\n")
        self.assertEqual(self.stamp(page), [])
        self.assertIn("**Status: open.**", (self.root / page).read_text())
        self.assertEqual(self.check()["warnings"], [])

    def test_a_problem_card_names_its_problem_among_what_it_rests_on(self):
        self.write("site/open/a.md", "---\nrelies-on: [conj:a]\n---\n")
        self.assertIn("a problem card names the id it presents", self.errors())
        self.write("site/open/a.md", "---\nproblem: thm:b\nrelies-on: [conj:a]\n---\n")
        self.assertIn("'thm:b' must also be in relies-on", self.errors())

    def test_settled_nodes_no_page_rests_on_are_listed_as_a_reminder(self):
        self.assertEqual(self.check()["unmentioned"], [])  # no site, no reminder
        self.page("p", **{"relies-on": ["conj:a"]})
        report = self.check()
        self.assertEqual(report["unmentioned"], ["thm:b"])
        self.assertNotIn("thm:b", "\n".join(report["warnings"]))
        self.page("q", **{"relies-on": ["thm:b"]})
        self.assertEqual(self.check()["unmentioned"], [])

    def test_stamping_refuses_an_unknown_id_and_writes_nothing(self):
        page = self.page("p", **{"relies-on": ["conj:nope"]})
        before = (self.root / page).read_text()
        self.assertIn("unknown id(s) conj:nope", "\n".join(self.stamp(page)))
        self.assertEqual((self.root / page).read_text(), before)

    def test_stamping_refuses_a_file_outside_the_site(self):
        self.assertIn("not a page under site/", "\n".join(self.stamp("modules/test.md")))


if __name__ == "__main__":
    unittest.main()
