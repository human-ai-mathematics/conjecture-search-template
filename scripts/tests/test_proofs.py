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
            "thm:narrative-only.proof_provenance: obsolete field",
            errors,
        )

    def test_refuted_nodes_name_a_certified_refuter(self):
        nodes = [
            node("obs:proved-counterexample", kind="obstruction"),
            node("q:open-counterexample", status="open", kind="question"),
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
                refuted_by=["q:open-counterexample"],
            ),
        ]
        self.add_ledger("main", "program", nodes)

        errors = self.errors()

        self.assertNotIn("conj:refuted.refuted_by", errors)
        self.assertIn("conj:missing-refuter: refuted node requires refuted_by", errors)
        self.assertIn("conj:open-refuter.refuted_by: 'q:open-counterexample' is not proved", errors)

    def test_a_refuter_is_not_a_proof_dependency_of_what_it_refutes(self):
        """A refuted node has no proof, so depends_on has nothing to record."""
        nodes = [
            node("obs:proved-counterexample", kind="obstruction"),
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
        """The header is parsed, not grepped: the word and the id may not sit apart."""
        relative = "solutions/loose-header.tex"
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "% a dossier that mentions ledger-node nowhere in particular\n"
            + "% padding\n" * 20
            + "% thm:loose appears far below, in prose\n"
        )
        self.add_ledger(
            "main", "program",
            [node("thm:loose", proofs=[{
                "artifact": relative, "mode": "human", "accepted_by": "fixture human",
            }])],
        )

        errors = self.errors()

        self.assertIn("dossier header has no 'ledger-node' field", errors)

    def test_a_dossier_carrying_checked_by_is_rejected_by_name(self):
        """Certification has one home. The header duplicated it with nothing to reconcile
        the two, so a dossier could read `checked_by: none` under a certified proof
        record and nothing went red."""
        relative = self.add_solution("retired-header", node_ids=("thm:retired",))
        path = self.root / relative
        path.write_text(path.read_text() + "%   checked_by  : none\n")
        self.add_ledger(
            "main", "program",
            [node("thm:retired", proofs=[{
                "artifact": relative, "mode": "human", "accepted_by": "fixture human",
            }])],
        )

        errors = self.errors()

        self.assertIn("dossier header field 'checked_by' is retired", errors)
        self.assertIn("proofs[].mode", errors)

    def test_machine_certification_is_retired_until_the_kernel_actually_runs(self):
        """An empty .lean file satisfied the strongest-sounding mode in the ladder."""
        lean_solution = self.add_solution("lean-proof", node_ids=("thm:lean",))
        (self.root / lean_solution).with_suffix(".lean").write_text("-- fixture\n")
        self.add_ledger(
            "main",
            "program",
            [node("thm:lean", proofs=[{"artifact": lean_solution, "mode": "lean"}])],
        )

        errors = self.errors()

        self.assertIn("thm:lean.proofs[0].mode: 'lean' is retired", errors)
        self.assertIn("never ran the kernel", errors)

    def test_solution_path_is_confined_to_tex_dossiers(self):
        self.module.write_text("% ledger-node: thm:outside\n\\label{thm:outside}\n")
        self.add_ledger(
            "main",
            "program",
            [node(
                "thm:outside",
                proofs=[{
                    "artifact": "modules/test.tex",
                    "mode": "human",
                    "accepted_by": "fixture human",
                }],
            )],
        )

        errors = self.errors()
        self.assertIn("thm:outside.proofs[].artifact: must stay under solutions/", errors)

    def test_legacy_proof_exception_fields_are_forbidden(self):
        for field in ("legacy_r2_debt", "legacy_proved_without_solution"):
            with self.subTest(field=field):
                self.add_ledger(
                    "main",
                    "program",
                    [node("thm:certified")],
                    meta_fields={field: {}},
                )

                errors = self.errors()

                self.assertIn(f"meta.{field}: obsolete field; use a certified proof", errors)

    def test_legacy_proof_fields_are_rejected(self):
        self.add_ledger(
            "main",
            "program",
            [
                node("thm:proof-file", proof_file="modules/test.tex"),
                node("thm:narrative", proof_provenance="inline proof"),
            ],
        )

        errors = self.errors()

        self.assertIn("thm:proof-file.proof_file: obsolete field; use proofs[].artifact", errors)
        self.assertIn(
            "thm:narrative.proof_provenance: obsolete field; use proofs with explicit certification records",
            errors,
        )

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
                      "'thm:missing-from-header-extra', not 'thm:missing-from-header'",
                      errors)

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
            node("obs:warning", status="open", kind="obstruction"),
            node(
                "thm:conditional",
                assumes=["ass:x"],
                implies=["q:open"],
                proofs=[{"artifact": solution, "mode": "agent", "review": review}],
            ),
            node(
                "q:open",
                status="open",
                kind="question",
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
