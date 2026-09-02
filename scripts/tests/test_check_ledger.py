"""Focused regression tests for the research control-plane checker.

Run from the repository root with::

    python3 -m unittest discover -s scripts/tests -p 'test_*.py'

The fixtures live in temporary directories, so these tests never modify the real
ledgers or append-only run artifacts.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("check_ledger", REPO / "scripts/check_ledger.py")
CHECKER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(CHECKER)


def node(node_id: str, *, status: str = "proved", kind: str = "theorem", **fields):
    result = {
        "id": node_id,
        "kind": kind,
        "status": status,
        "provenance": "internal",
        "file": "modules/test.tex",
        "statement": f"fixture statement for {node_id}",
    }
    result.update(fields)
    return result


class CheckerFixture(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.research = self.root / "research"
        self.research.mkdir(parents=True)
        modules = self.root / "modules"
        modules.mkdir()
        self.module = modules / "test.tex"
        self.module.write_text("fixture\n")
        (self.root / "references.bib").write_text(
            "@article{FixtureReference,\n"
            "  title = {Fixture reference},\n"
            "  year = {2026}\n"
            "}\n"
        )

    def tearDown(self):
        self.tempdir.cleanup()

    def add_ledger(self, relative: str, program: str, nodes: list[dict], *,
                   meta_fields: dict | None = None,
                   certify_fixture_proofs: bool = True) -> Path:
        path = self.research / relative / "ledger.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        meta = {"program": program}
        if meta_fields:
            meta.update(meta_fields)
        fixture_nodes = [dict(item) for item in nodes]
        manuscript_labels = []
        for item in fixture_nodes:
            label = item.get("label", item.get("id"))
            if isinstance(label, str) and label.strip():
                manuscript_labels.append(label)
        if manuscript_labels:
            with self.module.open("a", encoding="utf-8") as stream:
                for label in manuscript_labels:
                    stream.write(f"\\label{{{label}}}\n")
        if certify_fixture_proofs:
            bare_proved = [
                item for item in fixture_nodes
                if item.get("status") == "proved"
                and item.get("provenance") == "internal"
                and "proofs" not in item
            ]
            if bare_proved:
                solution = f"solutions/fixture-{relative.replace('/', '-')}.tex"
                solution_path = self.root / solution
                solution_path.parent.mkdir(parents=True, exist_ok=True)
                covered = "; ".join(str(item.get("id")) for item in bare_proved)
                solution_path.write_text(
                    f"% ledger-nodes: {covered}\nstandalone fixture proofs\n"
                )
                for item in bare_proved:
                    item["proofs"] = [{
                        "artifact": solution,
                        "mode": "human",
                        "accepted_by": "fixture human",
                    }]
        path.write_text(
            CHECKER.yaml.safe_dump({"meta": meta, "nodes": fixture_nodes}, sort_keys=False)
        )
        return path

    def add_solution(self, name: str, *, node_ids: tuple[str, ...] = ()) -> str:
        relative = f"solutions/{name}.tex"
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        covered = "; ".join(node_ids)
        path.write_text(f"% ledger-nodes: {covered}\nstandalone proof fixture\n")
        return relative

    def add_review(self, name: str, *, verdict: str = "pass",
                   node_ids: tuple[str, ...] = (), reviewer: str = "/root/reviewer",
                   authors: tuple[str, ...] = ("/root/prover",),
                   solutions: tuple[str, ...] = (), report_type: str = "proof-review",
                   body: str = "fixture review\n") -> str:
        relative = f"research/reviews/2026-08-25-{name}.md"
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        metadata = {"type": report_type, "date": "2026-08-25"}
        if report_type == "proof-review":
            metadata.update({
                "verdict": verdict,
                "authors": list(authors),
                "reviewer": reviewer,
                "nodes": list(node_ids),
                "solutions": list(solutions),
            })
        path.write_text(
            "---\n"
            + CHECKER.yaml.safe_dump(metadata, sort_keys=False)
            + "---\n\n"
            + body
        )
        return relative

    def add_run(self, name: str) -> str:
        relative = f"research/runs/{name}"
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{"_provenance": {"target": "fixture"}}\n')
        return relative

    def add_exploration(self, name: str, *, date: str = "2026-08-26",
                        outcome: str = "dead-end", nodes: tuple[str, ...] = (),
                        artifacts: tuple[str, ...] = (),
                        candidates: tuple[dict, ...] = (),
                        retires: tuple[str, ...] = (),
                        front_matter: dict | None = None,
                        body: str = "fixture exploration\n") -> str:
        relative = f"research/explorations/{date}-{name}.md"
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        metadata: dict = {"type": "exploration", "date": date, "outcome": outcome}
        for field, value in (("nodes", nodes), ("artifacts", artifacts),
                             ("candidates", candidates), ("retires", retires)):
            if value:
                metadata[field] = [dict(item) if isinstance(item, dict) else item
                                   for item in value]
        if front_matter:
            metadata.update(front_matter)
        path.write_text(
            "---\n"
            + CHECKER.yaml.safe_dump(metadata, sort_keys=False)
            + "---\n\n"
            + body
        )
        return relative

    def check(self):
        return CHECKER.check_control_plane(self.research, self.root)


class CheckerHardeningTests(CheckerFixture):
    def test_program_is_never_inferred_from_ledger_directory(self):
        path = self.research / "program" / "ledger.yaml"
        path.parent.mkdir(parents=True)
        path.write_text(CHECKER.yaml.safe_dump({"meta": {}, "nodes": []}))

        errors = "\n".join(self.check()["errors"])

        self.assertIn("meta.program must be a non-empty string", errors)

    def test_production_configuration_rejects_a_second_ledger(self):
        """One repository owns one program ledger (CLAUDE.md constraint 1)."""
        self.add_ledger("program", "program", [node("thm:real")])
        self.add_ledger("legacy", "program", [node("thm:legacy")])

        report = CHECKER.check_control_plane(
            self.research,
            self.root,
            configured_ledger="research/program/ledger.yaml",
        )
        errors = "\n".join(report["errors"])

        self.assertIn("unexpected second ledger", errors)
        self.assertIn("research/legacy/ledger.yaml", errors)
        self.assertNotIn("research/program/ledger.yaml: unexpected", errors)

    def test_missing_configured_ledger_is_reported(self):
        report = CHECKER.check_control_plane(
            self.research,
            self.root,
            configured_ledger="research/program/ledger.yaml",
        )

        self.assertIn("configured ledger does not exist", "\n".join(report["errors"]))

    def test_duplicate_program_ledgers_and_node_ids_fail(self):
        duplicated = [node("thm:a"), node("thm:a")]
        self.add_ledger("first", "program", duplicated)
        self.add_ledger("second", "program", [node("thm:b")])

        errors = "\n".join(self.check()["errors"])

        self.assertIn("duplicate node id 'thm:a'", errors)
        self.assertIn("duplicate ledger for program 'program'", errors)

    def test_dependencies_accept_only_nodes_in_the_same_ledger(self):
        self.add_ledger(
            "main",
            "program",
            [node("thm:a", depends_on=["thm:missing_slug", "external theorem in prose"])],
        )

        errors = "\n".join(self.check()["errors"])

        self.assertIn("depends_on: 'thm:missing_slug' is not a node in this ledger", errors)
        self.assertIn("depends_on: 'external theorem in prose' is not a node in this ledger", errors)

    def test_unlocks_is_an_obsolete_field_even_when_empty(self):
        nodes = [
            node("lem:base", unlocks=["thm:uses"]),
            node("q:empty", status="open", kind="question", unlocks=[]),
            node("thm:uses", depends_on=["lem:base"]),
        ]
        self.add_ledger("main", "program", nodes)

        errors = "\n".join(self.check()["errors"])

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

        errors = "\n".join(self.check()["errors"])

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

        errors = "\n".join(self.check()["errors"])

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

        errors = "\n".join(self.check()["errors"])

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

        errors = "\n".join(self.check()["errors"])

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
        document = CHECKER.yaml.safe_load(ledger.read_text())
        document["workflow"] = {}
        ledger.write_text(CHECKER.yaml.safe_dump(document, sort_keys=False))

        errors = "\n".join(self.check()["errors"])

        self.assertIn("q:schema.depends_on: must be a list", errors)
        self.assertIn("q:schema.related: obsolete field", errors)
        self.assertIn("q:schema.evidence_eligible: obsolete field", errors)
        self.assertIn("q:schema: unknown field 'mystery'", errors)
        self.assertIn("unknown top-level field 'workflow'", errors)
        self.assertIn("meta: unknown field 'mystery_meta'", errors)

    def test_declared_file_must_contain_effective_manuscript_label(self):
        other = self.root / "modules/other.tex"
        other.write_text("fixture without the anchor\n")
        self.add_ledger(
            "main",
            "program",
            [
                node(
                    "obs:synthetic",
                    status="open",
                    kind="obstruction",
                    file="modules/other.tex",
                    label="thm:effective-anchor",
                ),
            ],
        )

        errors = "\n".join(self.check()["errors"])

        self.assertIn(
            "obs:synthetic.file: 'modules/other.tex' does not contain effective label "
            "'thm:effective-anchor'",
            errors,
        )

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

        errors = "\n".join(self.check()["errors"])

        self.assertNotIn("thm:reduction (proved) inherits", errors)
        self.assertNotIn("thm:uses-reduction (proved) inherits", errors)
        self.assertIn("thm:bad-dependency (proved) inherits unresolved open 'ass:x'", errors)
        blockers = CHECKER._applicability_blockers("thm:reduction", {
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

        errors = "\n".join(self.check()["errors"])

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

        errors = "\n".join(self.check()["errors"])

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

        errors = "\n".join(self.check()["errors"])

        self.assertNotIn("thm:bounded.bounded_by", errors)
        self.assertNotIn("q:warned.heuristic_barriers", errors)
        self.assertIn("q:bad-hard.bounded_by: 'obs:warning' is not an established obstruction", errors)
        self.assertIn(
            "thm:non-obstruction.bounded_by: 'thm:bounded' is not a declared obstruction",
            errors,
        )
        self.assertIn("thm:unknown.bounded_by: 'obs:missing' is not a declared obstruction", errors)
        self.assertIn("thm:old-mechanism.mechanism: obsolete field", errors)

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

        errors = "\n".join(self.check()["errors"])

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

        errors = "\n".join(self.check()["errors"])

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

        errors = "\n".join(self.check()["errors"])

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
            "authors: [/root/prover]\n"
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

        errors = "\n".join(self.check()["errors"])

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

        errors = "\n".join(self.check()["errors"])

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

        errors = "\n".join(self.check()["errors"])

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
                depends_on=["obs:proved-counterexample"],
                refuted_by=["obs:proved-counterexample"],
            ),
            node("conj:missing-refuter", status="refuted", kind="conjecture"),
            node(
                "conj:open-refuter",
                status="refuted",
                kind="conjecture",
                depends_on=["q:open-counterexample"],
                refuted_by=["q:open-counterexample"],
            ),
            node(
                "conj:unlinked-refuter",
                status="refuted",
                kind="conjecture",
                refuted_by=["obs:proved-counterexample"],
            ),
        ]
        self.add_ledger("main", "program", nodes)

        errors = "\n".join(self.check()["errors"])

        self.assertNotIn("conj:refuted.refuted_by", errors)
        self.assertIn("conj:missing-refuter: refuted node requires refuted_by", errors)
        self.assertIn("conj:open-refuter.refuted_by: 'q:open-counterexample' is not proved", errors)
        self.assertIn(
            "conj:unlinked-refuter.refuted_by: 'obs:proved-counterexample' must also appear",
            errors,
        )

    def test_human_and_lean_certification_contracts(self):
        human_solution = self.add_solution("human-proof", node_ids=("thm:human",))
        lean_solution = self.add_solution("lean-proof", node_ids=("thm:lean",))
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
                node("thm:lean", proofs=[{"artifact": lean_solution, "mode": "lean"}]),
            ],
        )

        errors = "\n".join(self.check()["errors"])
        self.assertIn("thm:human.proofs[0].accepted_by: mode human requires a non-empty identity", errors)
        self.assertIn("thm:lean.proofs[0]: mode lean requires adjacent 'lean-proof.lean'", errors)

        (self.root / lean_solution).with_suffix(".lean").write_text("-- fixture\n")
        errors = "\n".join(self.check()["errors"])
        self.assertNotIn("thm:lean.proofs[0]: mode lean", errors)

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

        errors = "\n".join(self.check()["errors"])
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

                errors = "\n".join(self.check()["errors"])

                self.assertIn(f"meta.{field}: legacy proof exceptions are forbidden", errors)

    def test_status_vocabulary_is_shared_and_minimal(self):
        self.assertEqual(CHECKER.STATUSES, {
            "open", "proved", "defined", "refuted",
        })
        self.assertEqual(CHECKER.UNRESOLVED_STATUSES, {"open", "refuted"})

    def test_kind_vocabulary_is_shared_and_minimal(self):
        self.assertEqual(CHECKER.KIND, {
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

        errors = "\n".join(self.check()["errors"])

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

        errors = "\n".join(self.check()["errors"])

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

        errors = "\n".join(self.check()["errors"])

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

        errors = "\n".join(self.check()["errors"])

        self.assertIn("def:proved: internally proved node requires a certified proof", errors)
        self.assertIn("def:proved: kind definition requires status defined", errors)
        self.assertNotIn("def:defined", errors)

    def test_route_policy_requires_explicit_routes_and_checks_vocabulary(self):
        self.add_ledger(
            "main",
            "program",
            [
                node("thm:default-route"),
                node("thm:allowed-route", route="shared"),
                node("thm:bad-route", route="unlisted"),
            ],
            meta_fields={
                "route_policy": {
                    "allowed": ["eldan-localization", "shared"],
                }
            },
        )

        errors = "\n".join(self.check()["errors"])

        self.assertIn("thm:default-route.route: required", errors)
        self.assertNotIn("thm:allowed-route.route", errors)
        self.assertIn("thm:bad-route.route: 'unlisted' is not", errors)

        self.add_ledger(
            "main",
            "program",
            [node("thm:bad-policy", route="shared")],
            meta_fields={
                "route_policy": {
                    "default": "missing",
                    "allowed": ["shared", "shared", ""],
                }
            },
        )
        errors = "\n".join(self.check()["errors"])
        self.assertIn("route_policy.allowed: duplicate route 'shared'", errors)
        self.assertIn("route_policy.allowed: entries must be non-empty strings", errors)
        self.assertIn("route_policy: unknown field 'default'", errors)

    def test_legacy_proof_fields_are_rejected(self):
        self.add_ledger(
            "main",
            "program",
            [
                node("thm:proof-file", proof_file="modules/test.tex"),
                node("thm:narrative", proof_provenance="inline proof"),
            ],
        )

        errors = "\n".join(self.check()["errors"])

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

        errors = "\n".join(self.check()["errors"])

        self.assertIn("dossier header does not enumerate", errors)

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

        self.assertEqual(self.check()["errors"], [])

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

        self.assertEqual(self.check()["errors"], [])

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
            "route": {},
        })
        self.add_ledger("main", "program", [malformed])

        # The missing-ledger branch is covered by
        # test_program_is_never_inferred_from_ledger_directory; this case checks that
        # malformed field types are reported rather than crashing the checker.
        errors = "\n".join(self.check()["errors"])

        self.assertIn("bad kind '[]'", errors)
        self.assertIn("bad status '[]'", errors)
        self.assertIn("references must be non-empty strings", errors)

    def test_cli_reports_malformed_status_instead_of_crashing(self):
        malformed = node("thm:bad")
        malformed["status"] = []
        self.add_ledger("program", "program", [malformed])
        script = self.research / "check_ledger.py"
        script.write_text((REPO / "scripts/check_ledger.py").read_text())

        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("bad status '[]'", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_cli_status_and_node_views_are_derived(self):
        self.add_ledger(
            "program",
            "program",
            [
                node("lem:base"),
                node(
                    "q:frontier",
                    status="open",
                    kind="question",
                    depends_on=["lem:base"],
                ),
            ],
        )
        script = self.research / "check_ledger.py"
        script.write_text((REPO / "scripts/check_ledger.py").read_text())

        status = subprocess.run(
            [sys.executable, str(script), "status"], cwd=self.root,
            capture_output=True, text=True, check=False,
        )
        detail = subprocess.run(
            [sys.executable, str(script), "node", "q:frontier"], cwd=self.root,
            capture_output=True, text=True, check=False,
        )

        self.assertEqual(status.returncode, 0)
        self.assertIn("[program]", status.stdout)
        self.assertIn("open (1): q:frontier", status.stdout)
        self.assertEqual(detail.returncode, 0)
        self.assertIn("[program] q:frontier", detail.stdout)
        self.assertIn("depends_on:", detail.stdout)
        self.assertIn("used_by: []", detail.stdout)


    # --- the attempt log ---------------------------------------------------------------

    def test_exploration_requires_a_typed_dated_envelope(self):
        self.add_ledger("program", "program", [node("q:open", status="open", kind="question")])
        directory = self.root / "research/explorations"
        directory.mkdir(parents=True)
        (directory / "2026-08-26-bare.md").write_text("# no front matter\n")
        (directory / "README.md").write_text("navigation, not an attempt\n")
        self.add_exploration("wrong-outcome", nodes=("q:open",), outcome="promising")
        self.add_exploration("stale-date", nodes=("q:open",),
                             front_matter={"date": "2026-08-25"})
        self.add_exploration("extra-field", nodes=("q:open",),
                             front_matter={"verdict": "pass"})
        self.add_exploration("engages-nothing")

        errors = "\n".join(self.check()["errors"])

        self.assertIn("2026-08-26-bare.md: exploration must start with YAML front matter", errors)
        self.assertIn("outcome: want one of", errors)
        self.assertIn("date: must match the filename prefix", errors)
        self.assertIn("field 'verdict' is not valid for an exploration", errors)
        self.assertIn("must name at least one ledger node in 'nodes' or propose a candidate",
                      errors)
        self.assertNotIn("README.md", errors)

    def test_exploration_nodes_and_cited_artifacts_must_resolve(self):
        self.add_ledger("program", "program", [node("q:open", status="open", kind="question")])
        artifact = self.add_run("2026-08-26T000000Z-example.jsonl")
        self.add_exploration("grounded", nodes=("q:open",), artifacts=(artifact,))
        self.add_exploration("dangling", date="2026-08-27", nodes=("q:ghost",),
                             artifacts=("research/runs/missing.jsonl", "solutions/aside.jsonl"))

        errors = "\n".join(self.check()["errors"])

        self.assertIn("nodes: 'q:ghost' is not a ledger node id", errors)
        self.assertIn("'research/runs/missing.jsonl' does not exist", errors)
        self.assertIn("'solutions/aside.jsonl' must be an artifact under research/runs/", errors)
        self.assertNotIn("2026-08-26-grounded.md", errors)

    def test_candidate_list_and_candidate_outcome_require_each_other(self):
        self.add_ledger("program", "program", [node("q:open", status="open", kind="question")])
        self.add_exploration("claims-none", nodes=("q:open",), outcome="candidate")
        self.add_exploration("unflagged", date="2026-08-27", nodes=("q:open",),
                             outcome="dead-end",
                             candidates=({"id": "cand:quiet", "statement": "S"},))

        errors = "\n".join(self.check()["errors"])

        self.assertEqual(errors.count("outcome 'candidate' and a non-empty 'candidates' list"), 2)

    def test_candidate_ids_are_namespaced_unique_and_never_ledger_nodes(self):
        self.add_ledger("program", "program", [
            node("q:open", status="open", kind="question"),
            node("cand:collide", status="open", kind="question"),
        ])
        self.add_exploration("first", outcome="candidate",
                             candidates=({"id": "cand:same", "statement": "S"},))
        self.add_exploration("second", date="2026-08-27", outcome="candidate",
                             candidates=(
                                 {"id": "cand:same", "statement": "S again"},
                                 {"id": "cand:collide", "statement": "already a node"},
                                 {"id": "Bad Id", "statement": "wrong shape"},
                                 {"id": "cand:untyped", "statement": ""},
                             ))

        errors = "\n".join(self.check()["errors"])

        self.assertIn("'cand:same' was already proposed in "
                      "research/explorations/2026-08-26-first.md", errors)
        self.assertIn("'cand:collide' is already a ledger node", errors)
        self.assertIn("id: want 'cand:<slug>', got 'Bad Id'", errors)
        self.assertIn("statement: must be a non-empty string", errors)

    def test_a_candidate_stays_live_until_a_later_exploration_retires_it(self):
        self.add_ledger("program", "program", [node("q:open", status="open", kind="question")])
        self.add_exploration("propose", outcome="candidate", candidates=(
            {"id": "cand:alpha", "statement": "A"},
            {"id": "cand:beta", "statement": "B"},
        ))
        self.add_exploration("kill", date="2026-08-27", nodes=("q:open",),
                             retires=("cand:alpha",))

        report = self.check()

        self.assertEqual(report["errors"], [])
        self.assertEqual([entry["id"] for entry in report["candidates"]], ["cand:beta"])
        self.assertEqual(report["candidates"][0]["source"],
                         "research/explorations/2026-08-26-propose.md")

    def test_retiring_an_unproposed_or_not_yet_proposed_candidate_fails(self):
        self.add_ledger("program", "program", [node("q:open", status="open", kind="question")])
        self.add_exploration("early", nodes=("q:open",),
                             retires=("cand:later", "cand:ghost"))
        self.add_exploration("later", date="2026-08-27", outcome="candidate",
                             candidates=({"id": "cand:later", "statement": "L"},))
        self.add_exploration("self-retiring", date="2026-08-28", outcome="candidate",
                             candidates=({"id": "cand:self", "statement": "S"},),
                             retires=("cand:self",))

        errors = "\n".join(self.check()["errors"])

        self.assertIn("'cand:ghost' was never proposed", errors)
        self.assertIn("'cand:later' is retired before", errors)
        self.assertIn("'cand:self' is proposed by this same exploration", errors)

    def test_cli_lists_live_candidate_statements(self):
        self.add_ledger("program", "program", [node("q:open", status="open", kind="question")])
        self.add_exploration("propose", outcome="candidate",
                             candidates=({"id": "cand:alpha",
                                          "statement": "the candidate statement"},))
        script = self.research / "check_ledger.py"
        script.write_text((REPO / "scripts/check_ledger.py").read_text())

        result = subprocess.run(
            [sys.executable, str(script), "candidates"], cwd=self.root,
            capture_output=True, text=True, check=False,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("cand:alpha", result.stdout)
        self.assertIn("the candidate statement", result.stdout)


if __name__ == "__main__":
    unittest.main()
