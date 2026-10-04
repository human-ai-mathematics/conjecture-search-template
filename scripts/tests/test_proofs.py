"""Certification: proof records, dossiers, independent reviews, refutations."""
from __future__ import annotations

import unittest

from fixtures import AUTHOR, HUMAN, CheckerFixture, front_matter, node, statement

from checks.common import text_digest  # noqa: E402  (fixtures puts checks on the path)


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

    def test_impact_groups_shared_changes_and_keeps_certification_sources(self):
        self.ledger([node("def:common", kind="definition", status="defined"),
                     node("thm:a", proofs=[]), node("thm:b", proofs=[])], certify=False)
        a, b = self.solution("a", "thm:a"), self.solution("b", "thm:b")
        review = self.review("a", solutions=[a], statements=["thm:a", "def:common"])
        self.ledger([
            node("def:common", kind="definition", status="defined"),
            node("thm:a", depends_on=["def:common"], proofs=[{"artifact": a, "review": review}]),
            node("thm:b", assumes=["def:common"], proofs=[{
                "artifact": b, "accepted_by": HUMAN,
                "fingerprints": self.fingerprints([b], ["thm:b", "def:common"])}]),
        ])
        self.assertEqual(self.check()["impact"], {})
        self.edit_statement("def:common")
        with (self.root / a).open("a") as stream:
            stream.write("An edit.\n")
        report = self.check()
        self.assertEqual(set(report["impact"]), {"def:common", a})
        affected = report["impact"]["def:common"]
        self.assertEqual({(e["node"], e["artifact"], e["source"]) for e in affected},
                         {("thm:a", a, review), ("thm:b", b, f"the acceptance by {HUMAN}")})
        self.assertEqual([e["node"] for e in report["impact"][a]], ["thm:a"])
        self.assertTrue(all(e["error"] in report["errors"] for e in affected))
        from checks import analyze
        fast = analyze(self.root, fast=True)
        self.assertEqual(set(fast["impact"]), {a})
        self.assertTrue(fast["fast"])

    def test_impact_does_not_call_missing_fingerprints_a_change(self):
        self.certify(statements=[])
        self.edit_statement("thm:a")
        report = self.check()
        self.assertEqual(report["impact"], {})
        self.assertIn("does not fingerprint the statement", "\n".join(report["errors"]))

    def test_a_passing_independent_review_certifies(self):
        self.certify()
        self.assertClean()

    def test_a_proved_node_without_references_needs_a_proof_record(self):
        self.ledger([node("thm:a")], certify=False)
        self.assertIn("thm:a: a proved node without references needs a proof record", self.errors())

    def test_the_author_never_certifies_their_own_proof(self):
        self.certify(reviewer="researcher, claude-fable-5, 2026-08-26")
        self.assertIn("reviewer: must not be one of the authors", self.errors())

    def test_an_author_is_matched_by_name_whatever_the_model_or_date(self):
        self.certify(reviewer="Researcher, claude-opus-5-5, 2026-08-30")
        self.assertIn("reviewer: must not be one of the authors", self.errors())

    def test_reviewers_and_authors_are_identities(self):
        self.certify(reviewer="reviewer", authors=[AUTHOR, "researcher, 2026-08-25",
                                                   "researcher, m, 2026-02-30"])
        errors = self.errors()
        self.assertIn(".reviewer: want '<who>, <model or human>, <YYYY-MM-DD>', got 'reviewer'",
                      errors)
        self.assertIn("got 'researcher, 2026-08-25'", errors)
        self.assertIn("got 'researcher, m, 2026-02-30'", errors)

    def test_a_human_reviews_too(self):
        self.certify(reviewer=HUMAN)
        self.assertClean()

    def test_only_a_human_accepts_a_proof(self):
        self.ledger([node("thm:a", proofs=[])], certify=False)
        artifact = self.solution("a", "thm:a")
        self.ledger([node("thm:a", proofs=[
            {"artifact": artifact, "accepted_by": AUTHOR,
             "fingerprints": self.fingerprints([artifact], ["thm:a"])}])])
        self.assertIn("proofs[0].accepted_by: an acceptance is a human's", self.errors())

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
                   "---\nverdict: pass\nauthors: ['a, m, 2026-08-25']\nreviewer: 'b, m, 2026-08-25'\n"
                   "fingerprints: [solutions/a.md]\n---\n")
        self.review("keys", fingerprints={"notes/a.md": "0" * 64, "thm:ghost": "0" * 64,
                                          "solutions/a.md": "ABC"})
        errors = self.errors()
        self.assertIn(".verdict: want one of ['editorial', 'pass', 'revise']", errors)
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
                      f"acceptance by {HUMAN} fingerprinted it; it needs a new acceptance",
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
            {"artifact": artifact, "accepted_by": HUMAN},
            {"artifact": artifact, "accepted_by": HUMAN,
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
        self.assertIn(f"proofs[1]: solutions/a.md changed since the acceptance by {HUMAN} "
                      "fingerprinted it; it needs a new acceptance", self.errors())

    def test_a_record_is_either_reviewed_or_accepted_by_a_named_human(self):
        self.ledger([node("thm:a", proofs=[])], certify=False)
        artifact = self.solution("a", "thm:a")
        self.ledger([node("thm:a", proofs=[
            {"artifact": artifact, "accepted_by": HUMAN,
             "fingerprints": self.fingerprints([artifact], ["thm:a"])},
            {"artifact": artifact},
            {"artifact": artifact, "accepted_by": HUMAN, "review": "research/reviews/r.md"},
            {"artifact": artifact, "accepted_by": " "},
            {"artifact": artifact, "accepted_by": HUMAN, "mode": "human"},
        ])])
        errors = self.errors()
        self.assertNotIn("proofs[0]", errors)
        self.assertIn("proofs[1]: needs exactly one of review", errors)
        self.assertIn("proofs[2]: needs exactly one of review", errors)
        self.assertIn("proofs[3].accepted_by: want '<who>, <model or human>", errors)
        self.assertIn("proofs[4]: unknown field 'mode'", errors)

    def test_a_dossier_is_markdown_under_solutions_and_names_its_node(self):
        self.write("notes/a.md", "---\nledger-node: thm:a\n---\n")
        self.write("solutions/plain.md", "no front matter\n")
        self.ledger([node("thm:a", proofs=[
            {"artifact": "notes/a.md", "accepted_by": HUMAN},
            {"artifact": self.solution("other", "thm:b"), "accepted_by": HUMAN},
            {"artifact": "solutions/plain.md", "accepted_by": HUMAN},
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
            node("thm:a", proofs=[{"artifact": shared, "accepted_by": HUMAN, "fingerprints": both},
                                  {"artifact": second, "accepted_by": "B. Referee, human, 2026-08-26", "fingerprints": both}]),
            node("thm:b", proofs=[{"artifact": shared, "accepted_by": HUMAN, "fingerprints": both}]),
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


class EditorialNoteTests(CheckerFixture):
    agent_proof, certify = ProofTests.agent_proof, ProofTests.certify
    EDITOR = "orchestrator, claude-opus-5-5, 2026-09-01"
    EXAMINER = "reviewer, claude-sonnet-5-5, 2026-09-01"

    def note(self, name: str, changes: dict, amends=("research/reviews/2026-08-25-a.md",),
             reviewer: str = EXAMINER) -> str:
        return self.write(f"research/reviews/2026-09-01-{name}.md", front_matter({
            "verdict": "editorial", "amends": list(amends), "authors": [self.EDITOR],
            "reviewer": reviewer, "changes": changes}))

    def edit_dossier(self, text: str = "An edit after the review.\n") -> tuple[str, str]:
        before = self.digest("solutions/a.md")
        with (self.root / "solutions/a.md").open("a") as stream:
            stream.write(text)
        return before, text_digest((self.root / "solutions/a.md").read_text())

    def test_a_note_carries_a_certification_over_an_edited_statement_and_dossier(self):
        self.certify()
        self.edit_statement("thm:a")
        before, after = self.edit_dossier()
        self.assertIn("needs a new review", self.errors())
        self.note("wording", {
            "thm:a": {"from": statement("thm:a"), "to": statement("thm:a", "edited")},
            "solutions/a.md": {"from": before, "to": after}})
        self.assertClean()

    def test_notes_chain_oldest_first(self):
        self.certify()
        first, second = statement("thm:a"), statement("thm:a", "edited")
        self.edit_statement("thm:a")
        self.note("one", {"thm:a": {"from": first, "to": second}})
        self.anchors["thm:a"]["fingerprint"] = third = statement("thm:a", "again")
        self.assertIn("the statement of 'thm:a' changed", self.errors())
        self.write("research/reviews/2026-09-02-two.md", front_matter({
            "verdict": "editorial", "amends": ["research/reviews/2026-08-25-a.md"],
            "authors": [self.EDITOR], "reviewer": self.EXAMINER,
            "changes": {"thm:a": {"from": second, "to": third}}}))
        self.assertClean()

    def test_a_note_must_start_from_the_certified_version(self):
        self.certify()
        self.edit_statement("thm:a")
        self.note("wording", {"thm:a": {"from": "1" * 64,
                                        "to": statement("thm:a", "edited")}})
        errors = self.errors()
        self.assertIn("'thm:a' from does not match what research/reviews/2026-08-25-a.md "
                      "certifies", errors)
        self.assertIn("the statement of 'thm:a' changed", errors)

    def test_a_note_amends_only_passing_reviews_that_fingerprint_the_item(self):
        self.certify(verdict="revise")
        self.note("wording", {"thm:a": {"from": statement("thm:a"), "to": "2" * 64}})
        self.note("ghost", {"solutions/other.md": {"from": "1" * 64, "to": "2" * 64}},
                  amends=("research/reviews/2026-09-01-wording.md",))
        errors = self.errors()
        self.assertIn("'research/reviews/2026-08-25-a.md' is not a passing review", errors)
        self.assertIn("'research/reviews/2026-09-01-wording.md' is not a passing review",
                      errors)

    def test_a_note_names_an_item_its_reviews_fingerprint(self):
        self.certify()
        self.note("ghost", {"solutions/other.md": {"from": "1" * 64, "to": "2" * 64}})
        self.assertIn("no review it amends fingerprints 'solutions/other.md'", self.errors())

    def test_a_note_is_examined_by_someone_other_than_the_editor(self):
        self.certify()
        self.note("self", {"thm:a": {"from": statement("thm:a"), "to": "2" * 64}},
                  reviewer=self.EDITOR)
        self.assertIn("2026-09-01-self.md.reviewer: must not be one of the authors",
                      self.errors())

    def test_a_proof_record_names_the_review_not_the_note(self):
        self.certify()
        note = self.note("wording", {"thm:a": {"from": statement("thm:a"), "to": "2" * 64}})
        self.ledger([node("thm:a", proofs=[{"artifact": "solutions/a.md", "review": note}])])
        self.assertIn("an editorial note certifies nothing; name the review it amends",
                      self.errors())

    def test_layout_and_comments_leave_a_dossier_fingerprint_alone(self):
        self.ledger([node("thm:a", proofs=[])], certify=False)
        artifact = self.solution("a", "thm:a")
        text = (self.root / artifact).read_text()
        self.review("a", fingerprints={artifact: text_digest(text),
                                       "thm:a": statement("thm:a")})
        self.ledger([node("thm:a", proofs=[{"artifact": artifact,
                                            "review": "research/reviews/2026-08-25-a.md"}])])
        (self.root / artifact).write_text(text.replace("fixture", "fixture\n\n   ")
                                          + "% a note for agents\n")
        self.assertClean()
        (self.root / artifact).write_text(text.replace("fixture", "fixtures"))
        self.assertIn("solutions/a.md changed since", self.errors())

    def test_a_review_recording_the_raw_sha256_still_certifies(self):
        self.certify()  # the fixture records the SHA-256 of the dossier's bytes
        self.assertClean()


if __name__ == "__main__":
    unittest.main()
