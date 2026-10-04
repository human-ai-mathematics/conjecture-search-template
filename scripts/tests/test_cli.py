"""The command line, run for real: MyST build, exit codes, summary, fingerprints."""
from __future__ import annotations

import subprocess
import unittest

import yaml

from fixtures import CheckerFixture, node

from checks.history import directive  # noqa: E402


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
        impact = self.cli("--impact")
        self.assertEqual(impact.returncode, 1, impact.stdout + impact.stderr)
        self.assertIn("changed: thm:a", impact.stdout)
        self.assertIn(f"  thm:a | {artifact} | {review}", impact.stdout)
        self.assertNotIn("changed since", impact.stdout)
        self.assertNotIn("nodes:", impact.stdout)

    def test_statements_are_listed_and_an_edit_changes_the_list(self):
        self.ledger([node("conj:b", kind="conjecture", status="open"),
                     node("def:a", kind="definition", status="defined")])
        before = self.cli("--statements")
        self.assertEqual(before.returncode, 0, before.stdout + before.stderr)
        self.assertEqual([line.split()[0] for line in before.stdout.splitlines()],
                         ["conj:b", "def:a"])
        self.module.write_text(self.module.read_text() + "\nProse around the statements.\n")
        self.assertEqual(self.cli("--statements").stdout, before.stdout)
        self.module.write_text(self.module.read_text().replace("fixture", "edited", 1))
        self.assertNotEqual(self.cli("--statements").stdout, before.stdout)

    def test_a_fast_check_runs_no_build_and_says_what_it_skipped(self):
        self.ledger([node("conj:main", kind="conjecture", status="open")], anchor=False)
        result = self.cli("--fast")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("fast: manuscript not read", result.stdout)
        self.assertFalse((self.root / "_build/site").exists())
        self.assertEqual(self.cli().returncode, 1)

    def test_impact_keeps_other_errors_and_marks_fast_checks(self):
        self.ledger([node("thm:a")], certify=False)
        result = self.cli("--impact", "--fast")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("FAIL thm:a: a proved node without references needs a proof record",
                      result.stdout)
        self.assertIn("impact: 0 changed item(s) detected", result.stdout)
        self.assertIn("fast: manuscript not read", result.stdout)
        self.assertFalse((self.root / "_build/site").exists())
        for option in ("--drafts", "--statements", "--fingerprint"):
            args = ["--impact", option]
            if option == "--fingerprint":
                args.append("solutions/a.md")
            self.assertEqual(self.cli(*args).returncode, 2)

    def test_drafts_lists_the_dossiers_no_proof_record_names(self):
        self.ledger([node("thm:a")])
        self.solution("draft", "thm:a")
        result = self.cli("--drafts")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "solutions/draft.md\n")

    def commit(self) -> None:
        for command in (["init", "-q"], ["add", "-A"],
                        ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "c"]):
            subprocess.run(["git", "-C", str(self.root), *command], check=True,
                           capture_output=True)

    def test_diff_shows_each_change_since_the_certified_version(self):
        self.ledger([node("thm:a", proofs=[])], certify=False)
        artifact = self.solution("a", "thm:a")
        recorded = yaml.safe_load(self.cli("--fingerprint", artifact).stdout)["fingerprints"]
        review = self.review("a", fingerprints=recorded)
        self.ledger([node("thm:a", proofs=[{"artifact": artifact, "review": review}])])
        self.commit()
        self.module.write_text(self.module.read_text().replace("fixture\n:::", "edited\n:::"))
        with (self.root / artifact).open("a") as stream:
            stream.write("A new sentence.\n")
        result = self.cli("--diff")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("changed: solutions/a.md", result.stdout)
        self.assertIn("(fingerprint verified)", result.stdout)
        self.assertIn("+A new sentence.", result.stdout)
        self.assertIn("changed: thm:a", result.stdout)
        self.assertIn("not re-fingerprinted", result.stdout)
        self.assertIn("-fixture", result.stdout)
        self.assertIn("+edited", result.stdout)
        self.assertEqual(self.cli("--diff", "--statements").returncode, 2)

    def test_a_directive_is_found_by_its_label(self):
        text = ("Prose.\n\n::::{prf:theorem} Title\n:label: thm:a\n:::{note}\nx\n:::\n"
                "Body.\n::::\n\nAfter.\n")
        self.assertEqual(directive(text, "thm:a"),
                         "::::{prf:theorem} Title\n:label: thm:a\n:::{note}\nx\n:::\n"
                         "Body.\n::::\n")
        self.assertIsNone(directive(text, "thm:b"))


if __name__ == "__main__":
    unittest.main()
