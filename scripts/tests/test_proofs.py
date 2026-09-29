"""Certification: proof records, dossiers, independent reviews, refutations."""
from __future__ import annotations

import unittest

from fixtures import CheckerFixture, node


class ProofTests(CheckerFixture):
    def agent_proof(self, nid: str = "thm:a", **review) -> dict:
        """A reviewed proof of ``nid``; its statement is fingerprinted once ``ledger()`` has
        labelled it, so write the ledger first and call this through ``certify``."""
        artifact = self.solution("a", nid)
        report = self.review("a", **{"solutions": [artifact], "statements": [nid], **review})
        return {"artifact": artifact, "review": report}

    def certify(self, nid: str = "thm:a", **review) -> None:
        """Label ``nid`` in the manuscript, then write its reviewed proof."""
        self.ledger([node(nid, proofs=[])], certify=False)
        self.ledger([node(nid, proofs=[self.agent_proof(nid, **review)])])

    def test_a_passing_independent_review_certifies(self):
        self.certify()
        self.assertClean()

    def test_a_proved_node_without_references_needs_a_proof_record(self):
        self.ledger([node("thm:a")], certify=False)
        self.assertIn("thm:a: a proved node without references needs a proof record", self.errors())

    def test_the_author_never_certifies_their_own_proof(self):
        self.certify(reviewer="researcher")
        self.assertIn("reviewer: must not be one of the authors", self.errors())

    def test_a_revise_verdict_cannot_certify(self):
        self.certify(verdict="revise")
        self.assertIn("verdict 'revise' cannot certify", self.errors())

    def test_the_review_fingerprints_the_dossier_and_the_statement(self):
        self.certify(solutions=["solutions/x.md"], statements=[])
        errors = self.errors()
        self.assertIn("2026-08-25-a.md does not fingerprint 'solutions/a.md'", errors)
        self.assertIn("does not fingerprint the statement of 'thm:a'", errors)

    def test_the_review_exists_under_research_reviews(self):
        artifact = self.solution("a", "thm:a")
        self.ledger([node("thm:a", proofs=[
            {"artifact": artifact, "review": "research/reviews/missing.md"},
            {"artifact": artifact, "review": "solutions/a.md"},
            {"artifact": artifact, "review": ""},
        ])])
        errors = self.errors()
        self.assertIn("'research/reviews/missing.md' does not exist", errors)
        self.assertIn("'solutions/a.md' must be under research/reviews/", errors)
        self.assertIn("proofs[2].review: want a repo-relative path", errors)

    def test_a_review_header_is_validated_even_when_unused(self):
        self.review("orphan", verdict="maybe", authors=[], extra_field=1)
        self.write("research/reviews/2026-08-25-list.md",
                   "---\nverdict: pass\nauthors: [a]\nreviewer: b\n"
                   "fingerprints: [solutions/a.md]\n---\n")
        self.review("keys", fingerprints={"notes/a.md": "0" * 64, "thm:ghost": "0" * 64,
                                          "solutions/a.md": "ABC"})
        errors = self.errors()
        self.assertIn(".verdict: want one of ['pass', 'revise']", errors)
        self.assertIn(".authors: must be a non-empty list", errors)
        self.assertIn("unknown field 'extra_field'", errors)
        self.assertIn("list.md.fingerprints: want a mapping", errors)
        self.assertIn("'notes/a.md' is neither a dossier under solutions/ nor a ledger node",
                      errors)
        self.assertIn("'thm:ghost' is neither a dossier", errors)
        self.assertIn("'solutions/a.md' needs a lowercase hex SHA-256", errors)

    def test_a_dossier_edited_after_its_review_is_no_longer_certified(self):
        self.certify()
        self.assertClean()
        with (self.root / "solutions/a.md").open("a") as stream:
            stream.write("An edit after the review.\n")
        self.assertIn("solutions/a.md changed since research/reviews/2026-08-25-a.md "
                      "fingerprinted it; it needs a new review", self.errors())

    def test_a_statement_edited_after_its_review_is_no_longer_certified(self):
        self.certify()
        self.edit_statement("thm:a")
        self.assertIn("the statement of 'thm:a' changed since research/reviews/2026-08-25-a.md "
                      "fingerprinted it; it needs a new review", self.errors())

    def test_a_fast_check_compares_dossiers_but_not_statements(self):
        self.certify()
        self.edit_statement("thm:a")
        from checks import analyze
        self.assertEqual(analyze(self.root, fast=True)["errors"], [])
        with (self.root / "solutions/a.md").open("a") as stream:
            stream.write("An edit after the review.\n")
        self.assertIn("solutions/a.md changed since", "\n".join(
            analyze(self.root, fast=True)["errors"]))

    def test_editing_a_premise_unsettles_every_proof_that_uses_it(self):
        self.ledger([node("lem:base", kind="lemma"),
                     node("def:norm", kind="definition", status="defined"),
                     node("thm:user", depends_on=["lem:base"], assumes=["def:norm"])])
        self.assertClean()
        self.edit_statement("lem:base")
        self.edit_statement("def:norm")
        errors = self.errors()
        self.assertIn("lem:base.proofs[0]: the statement of 'lem:base' changed since the "
                      "acceptance by fixture human fingerprinted it; it needs a new acceptance",
                      errors)
        self.assertIn("thm:user.proofs[0]: the statement of 'lem:base' changed", errors)
        self.assertIn("thm:user.proofs[0]: the statement of 'def:norm' changed", errors)

    def test_editing_a_refuted_target_unsettles_its_refuter(self):
        self.ledger([node("conj:t", kind="conjecture", status="refuted", refuted_by=["prop:cx"]),
                     node("prop:cx", kind="proposition")])
        self.assertClean()
        self.edit_statement("conj:t")
        self.assertIn("prop:cx.proofs[0]: the statement of 'conj:t' changed", self.errors())

    def test_a_human_acceptance_is_fingerprinted_too(self):
        self.ledger([node("thm:a", proofs=[])], certify=False)
        artifact = self.solution("a", "thm:a")
        self.ledger([node("thm:a", proofs=[
            {"artifact": artifact, "accepted_by": "A. Referee"},
            {"artifact": artifact, "accepted_by": "A. Referee",
             "fingerprints": self.fingerprints([artifact], ["thm:a"])},
            {"artifact": artifact, "review": "research/reviews/r.md",
             "fingerprints": self.fingerprints([artifact], ["thm:a"])},
        ])])
        errors = self.errors()
        self.assertIn("proofs[0].fingerprints: want a mapping", errors)
        self.assertNotIn("proofs[1]", errors)
        self.assertIn("proofs[2].fingerprints: a reviewed proof's fingerprints are its review's",
                      errors)
        with (self.root / artifact).open("a") as stream:
            stream.write("An edit after the acceptance.\n")
        self.assertIn("proofs[1]: solutions/a.md changed since the acceptance by A. Referee "
                      "fingerprinted it; it needs a new acceptance", self.errors())

    def test_a_record_is_either_reviewed_or_accepted_by_a_named_human(self):
        self.ledger([node("thm:a", proofs=[])], certify=False)
        artifact = self.solution("a", "thm:a")
        self.ledger([node("thm:a", proofs=[
            {"artifact": artifact, "accepted_by": "A. Referee",
             "fingerprints": self.fingerprints([artifact], ["thm:a"])},
            {"artifact": artifact},
            {"artifact": artifact, "accepted_by": "B", "review": "research/reviews/r.md"},
            {"artifact": artifact, "accepted_by": " "},
            {"artifact": artifact, "accepted_by": "B", "mode": "human"},
        ])])
        errors = self.errors()
        self.assertNotIn("proofs[0]", errors)
        self.assertIn("proofs[1]: needs exactly one of review", errors)
        self.assertIn("proofs[2]: needs exactly one of review", errors)
        self.assertIn("proofs[3].accepted_by: must name who accepted", errors)
        self.assertIn("proofs[4]: unknown field 'mode'", errors)

    def test_a_dossier_is_markdown_under_solutions_and_names_its_node(self):
        self.write("notes/a.md", "---\nledger-node: thm:a\n---\n")
        self.write("solutions/plain.md", "no front matter\n")
        self.ledger([node("thm:a", proofs=[
            {"artifact": "notes/a.md", "accepted_by": "X"},
            {"artifact": self.solution("other", "thm:b"), "accepted_by": "X"},
            {"artifact": "solutions/plain.md", "accepted_by": "X"},
        ])])
        errors = self.errors()
        self.assertIn("'notes/a.md' must be under solutions/", errors)
        self.assertIn("other.md: front matter 'ledger-node' must name 'thm:a'", errors)
        self.assertIn("plain.md: dossier must start with a '---'", errors)

    def test_one_dossier_may_prove_several_nodes_and_one_node_several_proofs(self):
        self.ledger([node("thm:a", proofs=[]), node("thm:b", proofs=[])], certify=False)
        shared = self.solution("shared", "thm:a", "thm:b")
        second = self.solution("second", "thm:a")
        both = self.fingerprints([shared, second], ["thm:a", "thm:b"])
        self.ledger([
            node("thm:a", proofs=[{"artifact": shared, "accepted_by": "X", "fingerprints": both},
                                  {"artifact": second, "accepted_by": "Y", "fingerprints": both}]),
            node("thm:b", proofs=[{"artifact": shared, "accepted_by": "X", "fingerprints": both}]),
        ])
        self.assertClean()

    def test_a_dossier_no_proof_record_names_is_a_draft(self):
        self.certify()
        self.solution("draft", "thm:a")
        self.assertEqual(self.check()["drafts"], ["solutions/draft.md"])

    def test_proofs_only_on_a_proved_node(self):
        self.ledger([node("conj:a", kind="conjecture", status="open",
                          proofs=[self.agent_proof("conj:a")])])
        self.assertIn("conj:a.proofs: only for status proved", self.errors())

    def test_a_refuted_node_names_a_proved_refuter_and_never_depends_on_it(self):
        self.ledger([
            node("conj:false", kind="conjecture", status="refuted", refuted_by=["prop:cx"]),
            node("prop:cx", kind="proposition"),
            node("conj:bare", kind="conjecture", status="refuted"),
            node("conj:weak", kind="conjecture", status="refuted", refuted_by=["conj:open"]),
            node("conj:open", kind="conjecture", status="open", refuted_by=["prop:cx"]),
        ])
        errors = self.errors()
        self.assertNotIn("conj:false", errors)
        self.assertIn("conj:bare: a refuted node needs refuted_by", errors)
        self.assertIn("conj:weak.refuted_by: 'conj:open' is not proved", errors)
        self.assertIn("conj:open.refuted_by: only for status refuted", errors)


if __name__ == "__main__":
    unittest.main()
