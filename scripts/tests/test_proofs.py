"""Proofs lane: dossiers, certification modes, and persisted review provenance."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fixtures import CheckerFixture, node  # noqa: E402


class ProofsTests(CheckerFixture):
    def test_independent_agent_certification_requires_provenance(self):
        solution = self.add_solution(
            "agent-proof",
            node_ids=(
                "thm:agent-pass",
                "thm:agent-self-review",
                "thm:agent-missing-review",
            ),
        )
        review = self.add_review(
            "agent-proof-audit",
            node_ids=("thm:agent-pass",),
            solutions=(solution,),
        )
        self_review = self.add_review(
            "agent-self-review-audit",
            node_ids=("thm:agent-self-review",),
            reviewer="/root/same",
            authors=("/root/same",),
            solutions=(solution,),
        )
        nodes = [
            node(
                "thm:agent-pass",
                proofs=[{"artifact": solution, "mode": "agent", "review": review}],
            ),
            node(
                "thm:agent-self-review",
                proofs=[{"artifact": solution, "mode": "agent", "review": self_review}],
            ),
            node(
                "thm:agent-missing-review",
                proofs=[{
                    "artifact": solution,
                    "mode": "agent",
                    "review": "research/reviews/missing.md",
                }],
            ),
        ]
        self.add_ledger("main", "program", nodes)

        errors = self.errors()

        self.assertNotIn("thm:agent-pass", errors)
        self.assertIn(
            "agent-self-review-audit.md.reviewer: must be distinct from every proof author",
            errors,
        )
        self.assertIn("review 'research/reviews/missing.md': report does not exist", errors)

    def test_agent_certification_rejects_partial_or_out_of_scope_review(self):
        solution = self.add_solution(
            "agent-proof",
            node_ids=("thm:partial", "thm:wrong-scope", "thm:wrong-reviewer"),
        )
        partial = self.add_review(
            "partial-audit",
            verdict="changes-requested",
            node_ids=("thm:partial",),
            solutions=(solution,),
        )
        wrong_scope = self.add_review(
            "wrong-scope-audit",
            node_ids=("thm:wrong-scope-extra",),
            solutions=(solution,),
            body="## Explicit exclusions\n\nThis report does not certify `thm:wrong-scope`.\n",
        )
        wrong_reviewer = self.add_review(
            "wrong-reviewer-audit",
            node_ids=("thm:wrong-reviewer",),
            reviewer="/root/reviewer-extra",
            solutions=(solution,),
        )
        self.add_ledger(
            "main",
            "program",
            [
                node(
                    "thm:partial",
                    proofs=[{"artifact": solution, "mode": "agent", "review": partial}],
                ),
                node(
                    "thm:wrong-scope",
                    proofs=[{"artifact": solution, "mode": "agent", "review": wrong_scope}],
                ),
                node(
                    "thm:wrong-reviewer",
                    proofs=[{"artifact": solution, "mode": "agent", "review": wrong_reviewer}],
                ),
            ],
        )

        errors = self.errors()

        self.assertIn("partial-audit.md.verdict: a proof-review must have", errors)
        self.assertIn(
            "wrong-scope-audit.md'.nodes: active [program] certification 'thm:wrong-scope'",
            errors,
        )
        self.assertNotIn("wrong-reviewer-audit.md'.reviewer", errors)

    def test_agent_review_owns_identity_and_may_retain_historical_scope(self):
        solution = self.add_solution("agent-proof", node_ids=("thm:contract",))
        review = self.add_review(
            "wrong-contract-audit",
            node_ids=("thm:contract", "thm:unwired"),
            authors=("/root/not-the-author",),
            solutions=("solutions/not-the-dossier.tex",),
        )
        self.add_ledger(
            "main",
            "program",
            [node(
                "thm:contract",
                proofs=[{"artifact": solution, "mode": "agent", "review": review}],
            )],
        )

        errors = self.errors()

        self.assertIn(
            "wrong-contract-audit.md'.solutions: active [program] certification 'thm:contract'",
            errors,
        )
        self.assertNotIn("wrong-contract-audit.md'.nodes", errors)
        self.assertNotIn("wrong-contract-audit.md'.authors", errors)

    def test_audit_pass_prose_cannot_certify_and_review_path_is_confined(self):
        solution = self.add_solution(
            "agent-proof",
            node_ids=("thm:audit", "thm:outside"),
        )
        audit = self.add_review(
            "non-certifying-audit",
            report_type="audit",
            body="- **Verdict:** pass for `thm:audit` by `/root/reviewer`\n",
        )
        outside = "docs/outside-review.md"
        outside_path = self.root / outside
        outside_path.parent.mkdir(parents=True)
        outside_path.write_text(
            "---\n"
            "type: proof-review\n"
            "date: '2026-08-25'\n"
            "verdict: pass\n"
            "authors: [/root/researcher]\n"
            "reviewer: /root/reviewer\n"
            "nodes: [thm:outside]\n"
            f"solutions: [{solution}]\n"
            "---\n"
        )
        self.add_ledger(
            "main",
            "program",
            [
                node(
                    "thm:audit",
                    proofs=[{"artifact": solution, "mode": "agent", "review": audit}],
                ),
                node(
                    "thm:outside",
                    proofs=[{"artifact": solution, "mode": "agent", "review": outside}],
                ),
            ],
        )

        errors = self.errors()

        self.assertIn("type 'audit' cannot certify a proof", errors)
        self.assertIn("agent review reports must be under research/reviews/", errors)

    def test_review_archive_allows_historical_orphans_but_validates_envelopes(self):
        self.add_review(
            "orphaned-proof-review",
            node_ids=("thm:orphan",),
            solutions=("solutions/orphan.tex",),
        )
        malformed = self.root / "research/reviews/2026-08-25-malformed-audit.md"
        malformed.write_text("# Missing front matter\n")
        self.add_ledger("main", "program", [node("thm:fixture")])

        errors = self.errors()

        self.assertNotIn("orphaned-proof-review.md", errors)
        self.assertIn("malformed-audit.md: review report must start with YAML front matter", errors)

    def test_every_proved_node_requires_a_solution_and_no_other_signal_bypasses(self):
        self.add_ledger(
            "main",
            "program",
            [
                node("thm:missing"),
                node("thm:narrative-only", proof_provenance="inline manuscript argument"),
                node(
                    "thm:numerics-only",
                    evidence="numerical-directional",
                    evidence_run="research/runs/directional.jsonl",
                    evidence_target="fixture",
                ),
            ],
            certify_fixture_proofs=False,
        )

        errors = self.errors()

        self.assertIn("thm:missing: internally proved node requires a certified proof", errors)
        self.assertIn(
            "thm:narrative-only: internally proved node requires a certified proof", errors
        )
        self.assertIn(
            "thm:numerics-only: internally proved node requires a certified proof", errors
        )
        self.assertIn(
            "thm:narrative-only: unknown field 'proof_provenance'",
            errors,
        )

    def test_refuted_nodes_name_a_certified_refuter(self):
        nodes = [
            node("obs:proved-counterexample"),
            node("conj:open-counterexample", status="open", kind="conjecture"),
            node(
                "conj:refuted",
                status="refuted",
                kind="conjecture",
                refuted_by=["obs:proved-counterexample"],
            ),
            node("conj:missing-refuter", status="refuted", kind="conjecture"),
            node(
                "conj:open-refuter",
                status="refuted",
                kind="conjecture",
                refuted_by=["conj:open-counterexample"],
            ),
        ]
        self.add_ledger("main", "program", nodes)

        errors = self.errors()

        self.assertNotIn("conj:refuted.refuted_by", errors)
        self.assertIn("conj:missing-refuter: refuted node requires refuted_by", errors)
        self.assertIn("conj:open-refuter.refuted_by: 'conj:open-counterexample' is not proved", errors)

    def test_a_refuter_is_not_a_proof_dependency_of_what_it_refutes(self):
        """A refuted node has no proof, so depends_on has nothing to record."""
        nodes = [
            node("obs:proved-counterexample"),
            node(
                "conj:refuted",
                status="refuted",
                kind="conjecture",
                refuted_by=["obs:proved-counterexample"],
            ),
        ]
        self.add_ledger("main", "program", nodes)

        self.assertEqual(self.errors(), "")

    def test_human_certification_names_who_accepted_it(self):
        human_solution = self.add_solution("human-proof", node_ids=("thm:human",))
        self.add_ledger(
            "main",
            "program",
            [
                node(
                    "thm:human",
                    proofs=[{
                        "artifact": human_solution,
                        "mode": "human",
                        "accepted_by": "",
                    }],
                ),
            ],
        )

        errors = self.errors()
        self.assertIn(
            "thm:human.proofs[0].accepted_by: mode human requires a non-empty identity",
            errors,
        )

    def test_a_dossier_header_must_say_what_it_proves(self):
        """The header is parsed, not grepped: an id in the prose declares nothing."""
        relative = "solutions/loose-header.md"
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "---\ntitle: A dossier that forgot its node\n---\n\n"
            "ledger-node: thm:loose appears in the prose, which is not the header\n"
        )
        self.add_ledger(
            "main", "program",
            [node("thm:loose", proofs=[{
                "artifact": relative, "mode": "human", "accepted_by": "fixture human",
            }])],
        )

        errors = self.errors()

        self.assertIn("dossier header has no 'ledger-node' field", errors)

    def test_a_dossier_rejects_fields_outside_the_header_vocabulary(self):
        relative = self.add_solution("unknown-header", node_ids=("thm:header",))
        path = self.root / relative
        path.write_text(path.read_text().replace(
            "title: Fixture dossier\n", "title: Fixture dossier\nchecked_by: none\n",
        ))
        self.add_ledger(
            "main", "program",
            [node("thm:header", proofs=[{
                "artifact": relative, "mode": "human", "accepted_by": "fixture human",
            }])],
        )

        errors = self.errors()

        self.assertIn("dossier header has unknown field 'checked_by'", errors)

    def test_a_dossier_header_accepts_the_myst_fields_it_needs_to_render(self):
        relative = "solutions/rendered.md"
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "---\n"
            "title: Solution\n"
            "ledger-node: thm:rendered\n"
            "refines: [thm:rendered]\n"
            "bounded_by: []\n"
            "author: /root/researcher\n"
            "date: '2026-09-01'\n"
            "exports:\n  - format: pdf+tex\n    template: ../templates/latex\n"
            "---\n\nproof\n"
        )
        self.add_ledger(
            "main", "program",
            [node("thm:rendered", proofs=[{
                "artifact": relative, "mode": "human", "accepted_by": "fixture human",
            }])],
        )

        self.assertEqual(self.errors(), "")

    def test_a_dossier_without_front_matter_is_reported(self):
        relative = "solutions/bare.md"
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("ledger-node: thm:bare\n")
        self.add_ledger(
            "main", "program",
            [node("thm:bare", proofs=[{
                "artifact": relative, "mode": "human", "accepted_by": "fixture human",
            }])],
        )

        self.assertIn("dossier must start with YAML front matter", self.errors())

    def test_a_dossier_node_list_must_hold_ids(self):
        relative = self.add_solution("mangled", node_ids=("thm:mangled",))
        path = self.root / relative
        path.write_text(path.read_text().replace(
            "ledger-node:\n- thm:mangled\n", "ledger-node:\n  id: thm:mangled\n",
        ))
        self.add_ledger(
            "main", "program",
            [node("thm:mangled", proofs=[{
                "artifact": relative, "mode": "human", "accepted_by": "fixture human",
            }])],
        )

        self.assertIn("'ledger-node' must be a node id or a list of them", self.errors())

    def test_an_unimplemented_machine_certification_mode_is_invalid(self):
        lean_solution = self.add_solution("lean-proof", node_ids=("thm:lean",))
        (self.root / lean_solution).with_suffix(".lean").write_text("-- fixture\n")
        self.add_ledger(
            "main",
            "program",
            [node("thm:lean", proofs=[{"artifact": lean_solution, "mode": "lean"}])],
        )

        errors = self.errors()

        self.assertIn("thm:lean.proofs[0].mode: want one of ['agent', 'human'], got 'lean'", errors)

    def test_solution_path_is_confined_to_solutions(self):
        self.add_ledger(
            "main",
            "program",
            [node(
                "thm:outside",
                proofs=[{
                    "artifact": "modules/test.md",
                    "mode": "human",
                    "accepted_by": "fixture human",
                }],
            )],
        )

        errors = self.errors()
        self.assertIn("thm:outside.proofs[].artifact: must stay under solutions/", errors)

    def test_unknown_proof_exception_fields_are_forbidden(self):
        for field in ("proof_exception", "proved_without_record"):
            with self.subTest(field=field):
                self.add_ledger(
                    "main",
                    "program",
                    [node("thm:certified")],
                    meta_fields={field: {}},
                )

                errors = self.errors()

                self.assertIn(f"meta: unknown field '{field}'", errors)

    def test_unknown_proof_fields_are_rejected(self):
        self.add_ledger(
            "main",
            "program",
            [
                node("thm:proof-file", proof_file="modules/test.tex"),
                node("thm:narrative", proof_provenance="inline proof"),
            ],
        )

        errors = self.errors()

        self.assertIn("thm:proof-file: unknown field 'proof_file'", errors)
        self.assertIn("thm:narrative: unknown field 'proof_provenance'", errors)

    def test_solution_header_must_enumerate_shared_dossier_node(self):
        solution = self.add_solution(
            "shared-proof", node_ids=("thm:missing-from-header-extra",)
        )
        self.add_ledger(
            "main",
            "program",
            [node("thm:missing-from-header", proofs=[{
                "artifact": solution,
                "mode": "human",
                "accepted_by": "fixture human",
            }])],
        )

        errors = self.errors()

        self.assertIn("dossier header declares ledger-node "
                      "['thm:missing-from-header-extra'], not 'thm:missing-from-header'",
                      errors)

    def test_a_tex_dossier_is_no_longer_a_dossier(self):
        relative = "solutions/legacy.tex"
        (self.root / "solutions").mkdir(exist_ok=True)
        (self.root / relative).write_text("% === SOLUTION HEADER ===\n")
        self.add_ledger(
            "main", "program",
            [node("thm:legacy", proofs=[{
                "artifact": relative, "mode": "human", "accepted_by": "fixture human",
            }])],
        )

        self.assertIn("'solutions/legacy.tex' must be a .md file", self.errors())

    def test_a_review_of_the_tex_dossier_still_covers_its_markdown_conversion(self):
        """Reviews are immutable; converting a dossier to MyST changed no proof."""
        solution = self.add_solution("converted", node_ids=("thm:converted",))
        review = self.add_review(
            "converted-review",
            node_ids=("thm:converted",),
            solutions=("solutions/converted.tex",),
        )
        self.add_ledger(
            "main", "program",
            [node("thm:converted", proofs=[{
                "artifact": solution, "mode": "agent", "review": review,
            }])],
        )

        self.assertEqual(self.errors(), "")

    def test_multiple_independent_proofs_may_coexist(self):
        first = self.add_solution("first-proof", node_ids=("thm:two-proofs",))
        second = self.add_solution("second-proof", node_ids=("thm:two-proofs",))
        self.add_ledger("main", "program", [node(
            "thm:two-proofs",
            proofs=[
                {"artifact": first, "mode": "human", "accepted_by": "reader one"},
                {"artifact": second, "mode": "human", "accepted_by": "reader two"},
            ],
        )])

        self.assertEqual(self.errors(), "")

    def test_certified_implication_and_heuristic_barrier_pass(self):
        solution = self.add_solution("conditional-proof", node_ids=("thm:conditional",))
        review = self.add_review(
            "conditional-proof-review",
            node_ids=("thm:conditional",),
            solutions=(solution,),
        )
        nodes = [
            node("ass:x", status="open", kind="assumption"),
            node("obs:warning", status="open", kind="conjecture"),
            node(
                "thm:conditional",
                assumes=["ass:x"],
                implies=["conj:open"],
                proofs=[{"artifact": solution, "mode": "agent", "review": review}],
            ),
            node(
                "conj:open",
                status="open",
                kind="conjecture",
                heuristic_barriers=["obs:warning"],
            ),
        ]
        self.add_ledger(
            "main",
            "program",
            nodes,
        )

        self.assertEqual(self.errors(), "")

if __name__ == "__main__":
    unittest.main()
