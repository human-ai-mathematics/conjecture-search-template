"""Core lane: the claim graph, its manuscript anchors, and its bibliography.

Run from the repository root with::

    python3 -m unittest discover -s scripts/tests -p 'test_*.py'
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import yaml  # noqa: E402

from checks import failures, ledger  # noqa: E402
from checks.ledger import applicability_blockers  # noqa: E402
from fixtures import CheckerFixture, node  # noqa: E402


class CoreTests(CheckerFixture):
    def test_program_is_never_inferred_from_ledger_directory(self):
        path = self.research / "program" / "ledger.yaml"
        path.parent.mkdir(parents=True)
        path.write_text(yaml.safe_dump({"meta": {}, "nodes": []}))

        errors = self.errors()

        self.assertIn("meta.program must be a non-empty string", errors)

    def test_production_configuration_rejects_a_second_ledger(self):
        """One repository owns one program ledger (CLAUDE.md constraint 1)."""
        self.add_ledger("program", "program", [node("thm:real")])
        self.add_ledger("legacy", "program", [node("thm:legacy")])

        report = self.check(configured_ledger="research/program/ledger.yaml")
        errors = "\n".join(failures(report))

        self.assertIn("unexpected second ledger", errors)
        self.assertIn("research/legacy/ledger.yaml", errors)
        self.assertNotIn("research/program/ledger.yaml: unexpected", errors)

    def test_missing_configured_ledger_is_reported(self):
        report = self.check(configured_ledger="research/program/ledger.yaml")

        self.assertIn("configured ledger does not exist", "\n".join(failures(report)))

    def test_duplicate_program_ledgers_and_node_ids_fail(self):
        duplicated = [node("thm:a"), node("thm:a")]
        self.add_ledger("first", "program", duplicated)
        self.add_ledger("second", "program", [node("thm:b")])

        errors = self.errors()

        self.assertIn("duplicate node id 'thm:a'", errors)
        self.assertIn("duplicate ledger for program 'program'", errors)

    def test_dependencies_accept_only_nodes_in_the_same_ledger(self):
        self.add_ledger(
            "main",
            "program",
            [node("thm:a", depends_on=["thm:missing_slug", "external theorem in prose"])],
        )

        errors = self.errors()

        self.assertIn("depends_on: 'thm:missing_slug' is not a node in this ledger", errors)
        self.assertIn("depends_on: 'external theorem in prose' is not a node in this ledger", errors)

    def test_unlocks_is_an_obsolete_field_even_when_empty(self):
        nodes = [
            node("lem:base", unlocks=["thm:uses"]),
            node("q:empty", status="open", kind="question", unlocks=[]),
            node("thm:uses", depends_on=["lem:base"]),
        ]
        self.add_ledger("main", "program", nodes)

        errors = self.errors()

        self.assertIn("lem:base.unlocks: obsolete field", errors)
        self.assertIn("q:empty.unlocks: obsolete field", errors)
        self.assertNotIn("already declares", errors)

    def test_navigation_and_duplicated_assumption_fields_are_obsolete(self):
        self.add_ledger(
            "main",
            "program",
            [
                node("ass:x", status="open", kind="assumption"),
                node(
                    "thm:conditional",
                    status="conditional",
                    depends_on=["ass:x"],
                    assuming=["ass:x"],
                    related=["ass:x"],
                    entry_point=["ass:x"],
                    target_doc="research/program/targets/some-target.md",
                    discharged_by=["ass:x"],
                ),
            ],
        )

        errors = self.errors()

        for field in ("assuming", "related", "entry_point", "target_doc", "discharged_by"):
            self.assertIn(f"thm:conditional.{field}: obsolete field", errors)

    def test_conjectured_status_is_rejected_but_open_conjecture_is_valid(self):
        self.add_ledger(
            "main",
            "program",
            [
                node("conj:open", status="open", kind="conjecture"),
                node("conj:legacy", status="conjectured", kind="conjecture"),
            ],
        )

        errors = self.errors()

        self.assertNotIn("conj:open: status", errors)
        self.assertIn(
            "conj:legacy: status 'conjectured' is obsolete; use status open",
            errors,
        )

    def test_kind_records_mathematical_form_not_role_or_provenance(self):
        self.add_ledger(
            "main",
            "program",
            [
                node("thm:baseline", status="open", kind="baseline"),
                node("thm:imported-kind", status="open", kind="imported"),
            ],
        )

        errors = self.errors()

        self.assertIn("thm:baseline: bad kind 'baseline'", errors)
        self.assertIn("thm:imported-kind: bad kind 'imported'", errors)

    def test_all_imports_require_explicit_class_and_known_bibtex_references(self):
        self.add_ledger(
            "main",
            "program",
            [
                node(
                    "thm:import-good",
                    provenance="literature",
                    import_class="published",
                    references=["FixtureReference"],
                ),
                node("thm:import-missing", status="open", provenance="literature", references=[]),
                node(
                    "thm:import-unknown",
                    status="open",
                    provenance="literature",
                    import_class="published",
                    references=["MissingReference"],
                ),
                node(
                    "thm:local-with-reference",
                    status="open",
                    references=["FixtureReference"],
                ),
            ],
        )

        errors = self.errors()

        self.assertNotIn("thm:import-good", errors)
        self.assertIn("thm:import-missing: literature node requires explicit import_class", errors)
        self.assertIn("thm:import-missing: literature node requires non-empty references", errors)
        self.assertIn(
            "thm:import-unknown.references: unknown BibTeX key 'MissingReference'",
            errors,
        )
        self.assertIn(
            "thm:local-with-reference: references is only valid with provenance literature",
            errors,
        )

    def test_schema_rejects_unknown_retired_and_non_list_fields(self):
        ledger = self.add_ledger(
            "main",
            "program",
            [
                node(
                    "q:schema",
                    status="open",
                    kind="question",
                    depends_on="thm:premise",
                    related=["thm:premise"],
                    evidence_eligible=True,
                    mystery="typo",
                ),
                node("thm:premise", status="open"),
            ],
            meta_fields={"mystery_meta": True},
        )
        document = yaml.safe_load(ledger.read_text())
        document["workflow"] = {}
        ledger.write_text(yaml.safe_dump(document, sort_keys=False))

        errors = self.errors()

        self.assertIn("q:schema.depends_on: must be a list", errors)
        self.assertIn("q:schema.related: obsolete field", errors)
        self.assertIn("q:schema.evidence_eligible: obsolete field", errors)
        self.assertIn("q:schema: unknown field 'mystery'", errors)
        self.assertIn("unknown top-level field 'workflow'", errors)
        self.assertIn("meta: unknown field 'mystery_meta'", errors)

    def test_the_ledger_holds_a_summary_and_never_the_statement(self):
        """modules/ is canonical; a second field called `statement` invited drift."""
        bad = node("thm:copy")
        bad["statement"] = "a second copy of the manuscript text"
        self.add_ledger("main", "program", [bad])

        errors = self.errors()

        self.assertIn("thm:copy.statement: obsolete field", errors)
        self.assertIn("the statement itself lives in modules/", errors)

    def test_the_manuscript_anchor_is_the_node_id_and_nothing_overrides_it(self):
        """An override made "the id is the anchor" untrue and had no second reader."""
        self.add_ledger(
            "main",
            "program",
            [node("obs:synthetic", status="open", kind="obstruction",
                  label="thm:effective-anchor")],
        )

        errors = self.errors()

        self.assertIn("obs:synthetic.label: obsolete field", errors)
        self.assertIn("the node id itself as the manuscript anchor", errors)

    def test_a_declared_file_must_be_the_one_holding_the_anchor(self):
        other = self.root / "modules/other.tex"
        other.write_text("fixture without the anchor\n")
        self.add_ledger(
            "main",
            "program",
            [node("obs:synthetic", status="open", kind="obstruction",
                  file="modules/other.tex")],
        )

        errors = self.errors()

        self.assertIn(
            "obs:synthetic.file: 'modules/other.tex' does not contain 'obs:synthetic'; "
            "it is in modules/test.tex",
            errors,
        )

    def test_a_claim_is_stated_in_modules_and_nowhere_else(self):
        dossier = self.root / "solutions/elsewhere.tex"
        dossier.parent.mkdir(parents=True, exist_ok=True)
        dossier.write_text("\\begin{theorem}\n\\label{thm:elsewhere}\nfixture\n"
                           "\\end{theorem}\n")
        self.add_ledger(
            "main", "program",
            [node("thm:elsewhere", status="open", kind="theorem",
                  file="solutions/elsewhere.tex")],
        )

        errors = self.errors()

        self.assertIn("thm:elsewhere.file:", errors)
        self.assertIn("a claim is stated in modules/, nowhere else", errors)

    def test_a_structural_label_needs_no_node_but_a_claim_label_does(self):
        """The honest invariant: theorem environments are nodes, sections are not."""
        self.module.write_text(
            "\\section{Orientation}\n\\label{sec:overview}\n"
            "\\begin{lemma}\n\\label{lem:orphan}\nfixture\n\\end{lemma}\n"
        )
        self.add_ledger("main", "program", [])

        errors = self.errors()

        self.assertNotIn("sec:overview", errors)
        self.assertIn("\\label{lem:orphan} states a \\begin{lemma} that no ledger node "
                      "answers for", errors)

    def test_a_node_kind_must_agree_with_the_environment_it_labels(self):
        """A \\begin{conjecture} behind kind: theorem is a real defect, now a caught one."""
        self.add_ledger(
            "main", "program",
            [node("thm:mislabelled", status="open", kind="theorem")],
        )
        self.module.write_text(
            "\\begin{conjecture}\n\\label{thm:mislabelled}\nfixture\n"
            "\\end{conjecture}\n"
        )

        errors = self.errors()

        self.assertIn("thm:mislabelled.kind: 'theorem' disagrees with the "
                      "\\begin{conjecture} it labels", errors)

    def test_one_anchor_lives_in_one_place(self):
        self.add_ledger("main", "program",
                        [node("lem:twice", status="open", kind="lemma")])
        second = self.root / "modules/second.tex"
        second.write_text("\\begin{lemma}\n\\label{lem:twice}\nfixture\n\\end{lemma}\n")

        errors = self.errors()

        self.assertIn("duplicate manuscript label 'lem:twice'", errors)

    def test_a_label_inside_a_proof_still_belongs_to_its_theorem(self):
        """The enclosing claim environment is the innermost one, not the innermost env."""
        self.add_ledger(
            "main", "program",
            [node("prop:nested", status="open", kind="proposition")],
        )
        self.module.write_text(
            "\\begin{proposition}\n\\label{prop:nested}\n"
            "\\begin{proof}\n\\begin{itemize}\\item fixture\\end{itemize}\n"
            "\\end{proof}\n\\end{proposition}\n"
        )

        self.assertEqual(self.errors(), "")

    def test_implication_truth_is_separate_from_applicability(self):
        nodes = [
            node("ass:x", status="open", kind="assumption"),
            node(
                "thm:reduction",
                assumes=["ass:x"],
                implies=["q:target"],
            ),
            node("q:target", status="open", kind="conjecture"),
            node("thm:uses-reduction", depends_on=["thm:reduction"]),
            node("thm:bad-dependency", depends_on=["ass:x"]),
        ]
        self.add_ledger("main", "program", nodes)

        errors = self.errors()

        self.assertNotIn("thm:reduction (proved) inherits", errors)
        self.assertNotIn("thm:uses-reduction (proved) inherits", errors)
        self.assertIn("thm:bad-dependency (proved) inherits unresolved open 'ass:x'", errors)
        blockers = applicability_blockers("thm:reduction", {
            item["id"]: item for item in nodes
        })
        self.assertEqual(blockers, ["ass:x"])

    def test_unreviewed_preprint_cannot_be_claimed_proved(self):
        nodes = [
            node(
                "thm:preprint",
                status="open",
                provenance="literature",
                import_class="preprint-unreviewed",
                references=["FixtureReference"],
            ),
            node(
                "thm:published",
                provenance="literature",
                import_class="published",
                references=["FixtureReference"],
            ),
            node(
                "thm:overclaimed-preprint",
                provenance="literature",
                import_class="preprint-unreviewed",
                references=["FixtureReference"],
            ),
            node("thm:middle", depends_on=["thm:preprint"]),
            node("thm:top", depends_on=["thm:middle"]),
            node("thm:published-use", depends_on=["thm:published"]),
        ]
        self.add_ledger("main", "program", nodes)

        errors = self.errors()

        self.assertIn("thm:middle (proved) inherits unresolved open 'thm:preprint'", errors)
        self.assertIn("thm:top (proved) inherits unresolved open 'thm:preprint'", errors)
        self.assertIn("thm:overclaimed-preprint: an unreviewed preprint cannot have status proved", errors)
        self.assertNotIn("thm:published-use (proved) inherits", errors)

    def test_numerical_and_narrative_ledger_fields_are_retired(self):
        self.add_ledger(
            "main",
            "program",
            [node(
                "q:retired",
                status="open",
                kind="question",
                evidence="numerical-directional",
                evidence_run="research/runs/old.jsonl",
                evidence_target="A1",
                numerics="old inline specification",
                note="old inline navigation",
            )],
        )

        errors = self.errors()

        for field in ("evidence", "evidence_run", "evidence_target", "numerics", "note"):
            self.assertIn(f"q:retired.{field}: obsolete field", errors)

    def test_bounded_by_requires_ledger_obstruction_node(self):
        self.add_ledger(
            "main",
            "program",
            [
                node("obs:established", kind="obstruction"),
                node("obs:warning", status="open", kind="obstruction"),
                node("thm:bounded", bounded_by=["obs:established"]),
                node("q:warned", status="open", kind="question", heuristic_barriers=["obs:warning"]),
                node("q:bad-hard", status="open", kind="question", bounded_by=["obs:warning"]),
                node("thm:non-obstruction", bounded_by=["thm:bounded"]),
                node("thm:unknown", bounded_by=["obs:missing"]),
                node("thm:old-mechanism", mechanism=["direct-excess"]),
            ],
        )

        errors = self.errors()

        self.assertNotIn("thm:bounded.bounded_by", errors)
        self.assertNotIn("q:warned.heuristic_barriers", errors)
        self.assertIn("q:bad-hard.bounded_by: 'obs:warning' is not an established obstruction", errors)
        self.assertIn(
            "thm:non-obstruction.bounded_by: 'thm:bounded' is not a declared obstruction",
            errors,
        )
        self.assertIn("thm:unknown.bounded_by: 'obs:missing' is not a declared obstruction", errors)
        self.assertIn("thm:old-mechanism.mechanism: obsolete field", errors)

    def test_status_vocabulary_is_shared_and_minimal(self):
        self.assertEqual(ledger.STATUSES, {
            "open", "proved", "defined", "refuted",
        })
        self.assertEqual(ledger.UNRESOLVED_STATUSES, {"open", "refuted"})

    def test_kind_vocabulary_is_shared_and_minimal(self):
        self.assertEqual(ledger.KIND, {
            "theorem", "proposition", "lemma", "corollary", "conjecture",
            "assumption", "question", "definition", "obstruction", "example",
        })

    def test_removed_node_kinds_are_rejected(self):
        self.add_ledger("main", "program", [
            node("ass:valid", status="open", kind="assumption"),
            node("hyp:invalid", status="open", kind="hypothesis"),
            node("prog:invalid", status="open", kind="program"),
            node("rem:invalid", status="open", kind="remark"),
        ])

        errors = self.errors()

        self.assertNotIn("ass:valid: bad kind", errors)
        for nid, kind in (
            ("hyp:invalid", "hypothesis"),
            ("prog:invalid", "program"),
            ("rem:invalid", "remark"),
        ):
            self.assertIn(f"{nid}: bad kind '{kind}'", errors)

    def test_defined_status_and_definition_kind_are_reciprocal(self):
        self.add_ledger("program-definitions", "program", [
            node("def:sample-valid", status="defined", kind="definition"),
            node("thm:sample-invalid", status="defined", kind="theorem"),
            node("def:sample-invalid", status="open", kind="definition"),
        ])

        errors = self.errors()

        self.assertNotIn("def:sample-valid", errors)
        self.assertNotIn("def:sample-valid", errors)
        self.assertIn(
            "thm:sample-invalid: status defined is only valid for kind definition",
            errors,
        )
        self.assertIn("def:sample-invalid: kind definition requires status defined", errors)

    def test_removed_heuristic_classification_is_rejected(self):
        self.add_ledger("main", "program", [
            node("rem:bad-kind", status="open", kind="heuristic"),
            node("rem:bad-status", status="heuristic", kind="proposition"),
        ])

        errors = self.errors()

        self.assertIn("rem:bad-kind: bad kind 'heuristic'", errors)
        self.assertIn("rem:bad-status: bad status 'heuristic'", errors)

    def test_definition_requires_defined_status(self):
        self.add_ledger(
            "main",
            "program",
            [
                node("def:proved", kind="definition"),
                node("def:defined", status="defined", kind="definition"),
            ],
            certify_fixture_proofs=False,
        )

        errors = self.errors()

        self.assertIn("def:proved: internally proved node requires a certified proof", errors)
        self.assertIn("def:proved: kind definition requires status defined", errors)
        self.assertNotIn("def:defined", errors)

    def test_route_state_is_retired_from_the_ledger(self):
        """Constraint 12 in the ledger's own direction: coordination is not a claim.

        ``route`` and ``meta.route_policy`` were the pre-portfolio coordination
        mechanism. They are rejected by name rather than merely dropped, so a ledger
        inherited from an earlier copy of this template is told where the state moved.
        """
        self.add_ledger(
            "main",
            "program",
            [node("thm:owned", route="shared")],
            meta_fields={"route_policy": {"allowed": ["shared"]}},
        )

        errors = self.errors()

        self.assertIn("thm:owned.route: obsolete field", errors)
        self.assertIn("meta.route_policy: obsolete field", errors)
        self.assertIn("the search portfolio", errors)
        self.assertNotIn("unknown field 'route_policy'", errors)

    def test_malformed_field_types_report_without_crashing(self):
        malformed = node("thm:bad")
        malformed.update({
            "kind": [],
            "status": [],
            "file": [],
            "checked_by": {},
            "solution": {},
            "depends_on": [{}],
            "bounded_by": [{}],
        })
        self.add_ledger("main", "program", [malformed])

        # The missing-ledger branch is covered by
        # test_program_is_never_inferred_from_ledger_directory; this case checks that
        # malformed field types are reported rather than crashing the checker.
        errors = self.errors()

        self.assertIn("bad kind '[]'", errors)
        self.assertIn("bad status '[]'", errors)
        self.assertIn("references must be non-empty strings", errors)

if __name__ == "__main__":
    unittest.main()
