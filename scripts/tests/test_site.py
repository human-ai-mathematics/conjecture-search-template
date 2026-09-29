"""The reader's site: a page is stale once what it rests on moves, and --stamp is how it
catches up."""
from __future__ import annotations

import unittest
from datetime import date

from fixtures import CheckerFixture, node

from checks import analyze, proofs, site
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
        certified = [path for path in proofs.dossiers(self.root)
                     if path not in report["drafts"]]
        site.stamp(self.root, list(pages), site.current(
            report["nodes"], self.anchors, report["proposed"]), certified, TODAY, errors)
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
        self.page("q", **{"relies-on": {"conj:a": {"status": "open"}}})
        self.assertIn("site/q.md: stale: no 'checked' date", self.warnings())

    def test_a_page_that_rests_on_nothing_needs_no_stamp_and_shows_none(self):
        page = self.page("p")
        self.assertEqual(self.check()["warnings"], [])
        self.write(page, (self.root / page).read_text().replace(
            "---\n\n", "checked: 2026-01-01\n---\n\n" + "\n".join(
                [site.BEGIN, "*Last checked: 2026-01-01.*", site.END]) + "\n\n", 1))
        self.assertIn("stamp block is missing, out of date", self.warnings())
        self.assertEqual(self.stamp(page), [])
        text = (self.root / page).read_text()
        self.assertNotIn("checked", text)
        self.assertNotIn(site.BEGIN, text)
        self.assertEqual(self.check()["warnings"], [])

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
        self.assertIn("stamp block is missing, out of date or edited by hand", self.warnings())

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

    def test_the_open_problems_page_lists_every_card_with_its_status(self):
        index = self.page("open", "Each problem below.\n")
        self.assertIn("site/open.md: stale: its list is missing", self.warnings())
        self.assertEqual(self.stamp(index), [])
        text = (self.root / index).read_text()
        self.assertIn("*No problem is published yet.*", text)
        self.assertLess(text.index("Each problem below."), text.index(site.LIST_BEGIN))
        self.assertEqual(self.check()["warnings"], [])
        for name, number in (("b", 10), ("a", 2)):
            self.write(f"site/open/{name}.md", f"---\ntitle: Problem {number} — {name}\n"
                                                "problem: conj:a\nrelies-on: [conj:a]\n---\n")
            self.assertEqual(self.stamp(f"site/open/{name}.md"), [])
        self.assertIn("site/open.md: stale: its list is missing, out of date", self.warnings())
        self.assertEqual(self.stamp(index), [])
        text = (self.root / index).read_text()
        self.assertIn("- [Problem 2 — a](open/a.md) — open.\n"
                      "- [Problem 10 — b](open/b.md) — open.", text)
        self.assertEqual(self.stamp(index), [])
        self.assertEqual((self.root / index).read_text(), text)
        self.assertEqual(self.check()["warnings"], [])

    def test_the_full_proofs_page_lists_the_certified_dossiers_and_no_draft(self):
        self.solution("draft", "conj:a")
        index = self.page("proofs")
        self.assertEqual(self.stamp(index), [])
        text = (self.root / index).read_text()
        self.assertIn("- [Dossier](../solutions/fixture-thm-b.md), for [](#thm:b).", text)
        self.assertNotIn("draft", text)
        self.assertEqual(self.check()["warnings"], [])

    def test_a_template_placeholder_left_on_a_page_is_unfinished(self):
        self.page("p", "Write to `<contact email>`.\nReplace this page.\n")
        warnings = self.warnings()
        self.assertIn("site/p.md:5: unfinished: '<contact email>'", warnings)
        self.assertIn("site/p.md:6: unfinished: 'Replace this'", warnings)
        self.write("myst.yml", (self.root / "myst.yml").read_text()
                   + "# <a comment>\nextra: <author>\n")
        self.assertIn("myst.yml:10: unfinished: '<author>'", self.warnings())
        self.assertNotIn("<a comment>", self.warnings())

    def test_math_comments_links_and_html_are_not_placeholders(self):
        self.assertEqual(site.unfinished(
            "$a<b$ and $c>d$\n$$\nx < y,\\quad z > w\n$$\n% <a hint>\n<!-- <x y> -->\n"
            "<https://example.org> <me@example.org> <br> <span class=\"x\">\n"), [])
        self.assertEqual(site.unfinished("Problem <n>\n"), [(1, "<n>")])

    def test_stamping_refuses_a_file_outside_the_site(self):
        self.assertIn("not a page under site/", "\n".join(self.stamp("modules/test.md")))


if __name__ == "__main__":
    unittest.main()
