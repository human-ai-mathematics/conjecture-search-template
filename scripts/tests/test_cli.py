"""The command line, run for real: MyST build, exit codes, summary, fingerprints."""
from __future__ import annotations

import unittest

import yaml

from fixtures import CheckerFixture, node


class CommandLineTests(CheckerFixture):
    def test_a_clean_tree_exits_zero_and_summarises_the_search(self):
        self.ledger([node("conj:main", kind="conjecture", status="open")])
        self.brief("conj:main")
        self.checkpoint("c", candidates=[{"id": "cand:a", "statement": "A holds.\nMore."}])
        self.portfolio({"id": "ap:a", "state": "blocked", "blocker": "cand:a",
                        "reopen_if": "A is proved"})
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("nodes: 1 (1 open)", result.stdout)
        self.assertIn("target: conj:main (open)", result.stdout)
        self.assertIn("route ap:a: blocked on cand:a", result.stdout)
        self.assertIn("candidate cand:a: A holds.", result.stdout)

    def test_errors_exit_one_without_crashing_on_malformed_input(self):
        self.ledger([node("thm:a", status=["proved"]), "not a mapping"])
        result = self.cli()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("FAIL thm:a: bad status", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_fingerprints_printed_for_a_review_certify_until_the_statement_changes(self):
        self.ledger([node("thm:a", proofs=[])], certify=False)
        artifact = self.solution("a", "thm:a")
        printed = self.cli("--fingerprint", artifact)
        self.assertEqual(printed.returncode, 0, printed.stdout + printed.stderr)
        recorded = yaml.safe_load(printed.stdout)["fingerprints"]
        self.assertEqual(sorted(recorded), ["solutions/a.md", "thm:a"])
        review = self.review("a", fingerprints=recorded)
        self.ledger([node("thm:a", proofs=[{"artifact": artifact, "review": review}])])
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.module.write_text(self.module.read_text().replace("fixture", "edited"))
        result = self.cli()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("the statement of 'thm:a' changed since", result.stdout)

    def test_a_fast_check_runs_no_build_and_says_what_it_skipped(self):
        self.ledger([node("conj:main", kind="conjecture", status="open")], anchor=False)
        result = self.cli("--fast")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("fast: manuscript not read", result.stdout)
        self.assertFalse((self.root / "_build/site").exists())
        self.assertEqual(self.cli().returncode, 1)

    def test_a_stale_page_warns_while_searching_and_fails_a_publication(self):
        self.ledger([node("conj:main", kind="conjecture", status="open")])
        self.page("p", **{"relies-on": ["conj:main"]})
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("WARN site/p.md: stale", result.stdout)
        self.assertEqual(self.cli("--site-strict").returncode, 1)
        stamped = self.cli("--stamp", "site/p.md")
        self.assertEqual(stamped.returncode, 0, stamped.stdout + stamped.stderr)
        self.assertIn("stamped site/p.md", stamped.stdout)
        result = self.cli("--site-strict")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("site: 1 page(s), 0 warning(s)", result.stdout)

    def test_an_unfinished_page_warns_and_fails_a_publication(self):
        self.page("p", "Replace this page.\n")
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("WARN site/p.md:5: unfinished: 'Replace this'", result.stdout)
        self.assertEqual(self.cli("--site-strict").returncode, 1)

    def test_drafts_lists_the_dossiers_no_proof_record_names(self):
        self.ledger([node("thm:a")])
        self.solution("draft", "thm:a")
        result = self.cli("--drafts")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "solutions/draft.md\n")


if __name__ == "__main__":
    unittest.main()
