"""The claim graph: schema, status, references, the proof DAG, fences, anchors."""
from __future__ import annotations

import unittest

from fixtures import CheckerFixture, node


class LedgerTests(CheckerFixture):
    def test_an_empty_ledger_is_clean_and_a_missing_one_is_not(self):
        self.assertClean()
        (self.root / "research/program/ledger.yaml").unlink()
        self.assertIn("ledger.yaml: missing", self.errors())

    def test_schema_fields_and_vocabularies(self):
        self.ledger([
            node("thm:a", colour="red"),
            node("thm:b", summary="a gloss"),
            node("thm:c", status="conjectured"),
            node("thm:e", depends_on="thm:a"),
            {"id": "thm:g", "kind": "theorem"},
            node("thm:a"),
        ])
        errors = self.errors()
        for expected in ("thm:a: unknown field 'colour'", "thm:b: unknown field 'summary'",
                         "thm:c: bad status 'conjectured'", "thm:e.depends_on: must be a list",
                         "thm:g: missing 'status'", "duplicate node id 'thm:a'"):
            self.assertIn(expected, errors)

    def test_defined_status_goes_with_a_definition_directive(self):
        self.ledger([node("def:a", kind="definition", status="defined"),
                     node("def:b", kind="definition", status="open"),
                     node("thm:c", status="defined")])
        errors = self.errors()
        self.assertNotIn("def:a", errors)
        self.assertIn("def:b: status defined is for, and only for, a prf:definition", errors)
        self.assertIn("thm:c: status defined is for, and only for, a prf:definition", errors)

    def test_references_make_a_literature_node_and_must_be_known_keys(self):
        self.ledger([
            node("thm:ok", references=["Known"]),
            node("thm:bad-key", references=["Unknown"]),
            node("thm:empty", references=[]),
            node("thm:typed", references=[{"key": "Known"}, ["Known"]]),
        ])
        errors = self.errors()
        self.assertIn("thm:typed.references: '{'key': 'Known'}' is not a BibTeX key", errors)
        self.assertIn("thm:typed.references: '['Known']' is not a BibTeX key", errors)
        self.assertNotIn("thm:ok", errors)
        self.assertIn("unknown BibTeX key 'Unknown'", errors)
        self.assertIn("thm:empty.references: must be a non-empty list", errors)

    def test_references_resolve_and_the_proof_graph_is_acyclic(self):
        self.ledger([node("lem:a", status="open", depends_on=["lem:b"]),
                     node("lem:b", status="open", depends_on=["lem:a", "lem:ghost"])])
        errors = self.errors()
        self.assertIn("lem:b.depends_on: 'lem:ghost' is not a node", errors)
        self.assertIn("dependency cycle: lem:a -> lem:b -> lem:a", errors)

    def test_a_proved_node_cannot_rest_on_an_unresolved_premise_even_transitively(self):
        self.ledger([node("thm:top", depends_on=["lem:mid"]),
                     node("lem:mid", kind="lemma", depends_on=["lem:gap"]),
                     node("lem:gap", kind="lemma", status="open")])
        errors = self.errors()
        self.assertIn("thm:top (proved) depends on open 'lem:gap' via "
                      "thm:top -> lem:mid -> lem:gap", errors)
        self.assertIn("lem:mid (proved) depends on open 'lem:gap'", errors)

    def test_truth_is_separate_from_applicability(self):
        """A proved implication stays proved while its antecedent is open."""
        self.ledger([node("conj:h", kind="conjecture", status="open"),
                     node("thm:impl", assumes=["conj:h"]),
                     node("thm:bad", depends_on=["conj:h"])])
        errors = self.errors()
        self.assertNotIn("thm:impl", errors)
        self.assertIn("thm:bad (proved) depends on open 'conj:h'", errors)

    def test_a_fence_is_any_node_and_must_exist(self):
        self.ledger([node("thm:fence"), node("conj:barrier", kind="conjecture", status="open"),
                     node("conj:ok", kind="conjecture", status="open",
                          bounded_by=["thm:fence", "conj:barrier"]),
                     node("conj:bad", kind="conjecture", status="open",
                          bounded_by=["conj:ghost"])])
        errors = self.errors()
        self.assertNotIn("conj:ok", errors)
        self.assertIn("conj:bad.bounded_by: 'conj:ghost' is not a node", errors)

    def test_every_node_labels_a_claim_and_every_claim_has_a_node(self):
        self.anchors.update({
            "sec:intro": {"kind": None, "file": "modules/test.md"},
            "lem:orphan": {"kind": "lemma", "file": "modules/test.md"},
            "thm:heading": {"kind": None, "file": "modules/test.md"},
        })
        self.ledger([node("thm:unlabelled"), node("thm:heading")],
                    anchor=False)
        errors = self.errors()
        self.assertNotIn("sec:intro", errors)
        self.assertIn("thm:unlabelled: no manuscript label", errors)
        self.assertIn("prf:lemma 'lem:orphan' has no ledger node", errors)
        self.assertIn("thm:heading: labels a structural element", errors)

    def test_a_fast_check_leaves_the_anchors_unchecked(self):
        self.ledger([node("thm:unlabelled", status="open")], anchor=False)
        from checks import analyze
        report = analyze(self.root, fast=True)
        self.assertEqual(report["errors"], [])
        self.assertTrue(report["fast"])


if __name__ == "__main__":
    unittest.main()
