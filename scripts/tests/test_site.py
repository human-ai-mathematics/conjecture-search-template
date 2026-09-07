"""The published site: a derived view, and nothing else.

``scripts/site.py`` has no lane in ``check.py`` and cannot have one — the checker
validates repository state, and a built site is a build artifact under ``build/``. This
file is therefore the only thing standing between the exporter and the failure mode the
whole design exists to avoid:

    a beautiful second source of truth.

So the tests below are mostly about *boundaries* rather than about rendering. That the
frontend holds no mathematics, that the two modes of certification are not presented as
equal evidence, that a candidate is never dressed as a claim, that supersession is
applied, and that an invalid revision is never published at all.

    python3 -m unittest discover -s scripts/tests -p 'test_*.py'
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fixtures import REPO, CheckerFixture, node  # noqa: E402

# Loaded by path rather than by name. `import site` would return the standard library's
# module, which the interpreter imports at startup and caches long before scripts/ is on
# sys.path — so the name is taken, and the collision would be silent rather than loud.
_spec = importlib.util.spec_from_file_location("harness_site", REPO / "scripts/site.py")
site_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(site_module)

EXAMPLE = REPO / "example"
FRONTEND = REPO / "site"
PAGES_WORKFLOW = REPO / ".github/workflows/pages.yml"
CHECK_WORKFLOW = REPO / ".github/workflows/check.yml"


class SiteFixture(CheckerFixture):
    """A fixture tree plus a throwaway output directory."""

    def setUp(self):
        super().setUp()
        self.out = self.root / "build/site"

    def publish(self, **kwargs):
        return site_module.build(self.root, self.out, **kwargs)

    def data(self, **kwargs) -> dict:
        data, errors = self.publish(**kwargs)
        self.assertEqual(errors, [], "fixture was expected to validate")
        return data


class RefusesInvalidRevisions(SiteFixture):
    """A structurally invalid revision is not this repository's research state."""

    def test_a_red_repository_is_not_published(self):
        self.add_ledger("program", "test", [node("thm:a", depends_on=["thm:missing"])])

        data, errors = self.publish()

        self.assertTrue(errors)
        self.assertEqual(data, {})

    def test_a_refusal_writes_nothing_at_all(self):
        """Not even a stale shell. A half-written site is worse than no site."""
        self.add_ledger("program", "test", [node("thm:a", depends_on=["thm:missing"])])

        self.publish()

        self.assertFalse(self.out.exists())

    def test_an_uninstantiated_template_is_published_and_says_so(self):
        """A fresh clone is correct and not ready; refusing it would make that red."""
        self.add_ledger("program", "program", [])

        data = self.data()

        self.assertFalse(data["program"]["instantiated"])
        self.assertEqual(data["claims"], {})
        self.assertIsNone(data["search"])


class ClaimExport(SiteFixture):
    def test_both_directions_of_a_relation_are_derived(self):
        self.add_ledger("program", "test", [
            node("lem:base"),
            node("thm:top", depends_on=["lem:base"]),
        ])

        claims = self.data()["claims"]

        self.assertEqual(claims["thm:top"]["edges"]["depends_on"], ["lem:base"])
        self.assertEqual(claims["lem:base"]["reverse"]["used_by"], ["thm:top"])

    def test_the_one_line_summary_is_exported_as_a_gloss(self):
        """`summary` is a gloss, not the statement (research/program/ledger-schema.md).

        The field is renamed on the way out so that no view can present it as canonical
        by accident, and the anchor travels with it so a reader can reach the real text.
        """
        self.add_ledger("program", "test", [node("thm:a")])

        claim = self.data()["claims"]["thm:a"]

        self.assertIn("gloss", claim)
        self.assertNotIn("statement", claim)
        self.assertEqual(claim["source"]["file"], "modules/test.tex")
        self.assertIsInstance(claim["source"]["line"], int)

    def test_hard_and_advisory_fences_are_different_classes(self):
        """A proved obstruction fences; an open one advises. Drawing them alike lies."""
        self.add_ledger("program", "test", [
            node("obs:hard", kind="obstruction"),
            node("obs:soft", kind="obstruction", status="open"),
            node("thm:a", bounded_by=["obs:hard"], heuristic_barriers=["obs:soft"]),
        ])

        data = self.data()
        classes = {relation["field"]: relation["class"]
                   for relation in data["vocabulary"]["relations"]}

        self.assertEqual(classes["bounded_by"], "hard-fence")
        self.assertEqual(classes["heuristic_barriers"], "soft-fence")
        self.assertNotEqual(classes["assumes"], classes["depends_on"])
        claim = data["claims"]["thm:a"]
        self.assertEqual(claim["edges"]["bounded_by"], ["obs:hard"])
        self.assertEqual(claim["edges"]["heuristic_barriers"], ["obs:soft"])

    def test_an_applicability_blocked_proof_is_marked_without_losing_its_status(self):
        self.add_ledger("program", "test", [
            node("asm:open", status="open", kind="assumption"),
            node("thm:conditional", assumes=["asm:open"]),
        ])

        claim = self.data()["claims"]["thm:conditional"]

        self.assertEqual(claim["status"], "proved")
        self.assertEqual(claim["applicability_blocked_by"], ["asm:open"])

    def test_a_refuter_is_not_a_dependency_of_what_it_refutes(self):
        self.add_ledger("program", "test", [
            node("prop:refuter"),
            node("conj:target", status="refuted", kind="conjecture",
                 refuted_by=["prop:refuter"]),
        ])

        claims = self.data()["claims"]

        self.assertEqual(claims["conj:target"]["edges"]["depends_on"], [])
        self.assertEqual(claims["conj:target"]["edges"]["refuted_by"], ["prop:refuter"])
        self.assertEqual(claims["prop:refuter"]["reverse"]["refutes"], ["conj:target"])


class CertificationIsNotFlattened(SiteFixture):
    """The two proof modes are not equally evidenced, and the export says which is which."""

    def test_an_agent_certification_carries_its_persisted_review(self):
        solution = self.add_solution("thm-a", node_ids=("thm:a",))
        review = self.add_review("a-review", node_ids=("thm:a",), solutions=(solution,))
        self.add_ledger("program", "test", [
            node("thm:a", proofs=[{"artifact": solution, "mode": "agent", "review": review}]),
        ], certify_fixture_proofs=False)

        proof = self.data()["claims"]["thm:a"]["proofs"][0]

        self.assertEqual(proof["evidence"], "persisted-review")
        self.assertEqual(proof["review_detail"]["verdict"], "pass")
        self.assertEqual(proof["review_detail"]["reviewer"], "/root/reviewer")
        self.assertEqual(proof["review_detail"]["authors"], ["/root/researcher"])

    def test_a_human_acceptance_is_marked_an_attestation(self):
        """It carries a name and no artifact. That is honest, and honestly weaker."""
        self.add_ledger("program", "test", [node("thm:a")])  # fixture writes mode: human

        proof = self.data()["claims"]["thm:a"]["proofs"][0]

        self.assertEqual(proof["mode"], "human")
        self.assertEqual(proof["evidence"], "attestation")
        self.assertNotIn("review_detail", proof)


class SearchStateStaysSearchState(SiteFixture):
    def test_a_route_carries_no_status_and_no_statement(self):
        self.add_ledger("program", "test", [node("conj:target", kind="conjecture",
                                                 status="open")])
        self.add_portfolio({
            "target": "conj:target",
            "families": [{"id": "fam:one", "mechanism": "try it", "state": "active"}],
            "approaches": [{"id": "ap:one", "family": "fam:one", "state": "active"}],
        })

        route = self.data()["search"]["routes"]["ap:one"]

        self.assertNotIn("status", route)
        self.assertNotIn("gloss", route)
        self.assertIn("objective", route)

    def test_what_a_route_is_blocked_on_is_named_from_the_claim_side_too(self):
        """The portfolio names a blocker and never restates it, so the join is derived."""
        self.add_ledger("program", "test", [
            node("conj:target", kind="conjecture", status="open"),
            node("lem:blocker", status="open", kind="lemma"),
        ])
        self.add_portfolio({
            "target": "conj:target",
            "families": [{"id": "fam:one", "mechanism": "try it", "state": "active"}],
            "approaches": [{
                "id": "ap:one", "family": "fam:one", "state": "blocked",
                "blocker": "lem:blocker", "reopen_if": "someone proves it",
                "checkpoints": [self.add_checkpoint("stuck", approach="ap:one")],
            }],
        })

        data = self.data()

        self.assertEqual(data["claims"]["lem:blocker"]["blocks_routes"], ["ap:one"])
        self.assertEqual(data["search"]["routes"]["ap:one"]["blocker"], "lem:blocker")

    def test_route_ancestry_is_derived_rather_than_stored(self):
        self.add_ledger("program", "test", [node("conj:target", kind="conjecture",
                                                 status="open")])
        self.add_portfolio({
            "target": "conj:target",
            "families": [{"id": "fam:one", "mechanism": "try it", "state": "active"}],
            "approaches": [
                {"id": "ap:parent", "family": "fam:one", "state": "active"},
                {"id": "ap:child", "family": "fam:one", "state": "active",
                 "parent": "ap:parent"},
            ],
        })

        routes = self.data()["search"]["routes"]

        self.assertEqual(routes["ap:parent"]["children"], ["ap:child"])


class DurableMemory(SiteFixture):
    def test_a_candidate_is_exported_with_its_canonical_statement(self):
        """The asymmetry with a node's gloss is the point: nothing else holds this text."""
        self.add_ledger("program", "test", [node("thm:a")])
        source = self.add_checkpoint("found", outcome="candidate", candidates=(
            {"id": "cand:x", "statement": "A precise statement."},
        ))

        candidates = self.data()["memory"]["candidates"]

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["statement"], "A precise statement.")
        self.assertEqual(candidates[0]["source"], source)

    def test_a_promoted_candidate_is_no_longer_live(self):
        self.add_ledger("program", "test", [node("thm:a"), node("lem:x")])
        self.add_checkpoint("propose", date="2026-08-26", outcome="candidate", candidates=(
            {"id": "cand:x", "statement": "A precise statement."},
        ))
        self.add_checkpoint("promote", date="2026-08-27", outcome="proposed",
                            nodes=("lem:x",),
                            promotes=({"candidate": "cand:x", "node": "lem:x"},))

        memory = self.data()["memory"]

        self.assertEqual(memory["candidates"], [])
        self.assertEqual(memory["promoted"]["cand:x"]["node"], "lem:x")

    def test_a_superseded_checkpoint_names_its_heir(self):
        """An append-only archive keeps provenance; naming the heir supplies a reading."""
        self.add_ledger("program", "test", [node("thm:a")])
        old = self.add_checkpoint("old", date="2026-08-26", nodes=("thm:a",))
        self.add_checkpoint("new", date="2026-08-27", nodes=("thm:a",), supersedes=(old,))

        records = {record["path"]: record for record in self.data()["memory"]["checkpoints"]}

        self.assertEqual(records[old]["superseded_by"],
                         ["research/explorations/2026-08-27-new.md"])

    def test_a_run_artifact_is_exported_without_being_attached_to_a_status(self):
        self.add_ledger("program", "test", [node("thm:a")])
        self.add_run("2026-08-26T000000.000000Z-fixture.jsonl", target="fixture")

        runs = self.data()["memory"]["runs"]

        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["target"], "fixture")
        self.assertNotIn("certifies", json.dumps(runs))


class Layout(SiteFixture):
    def test_every_claim_is_placed(self):
        self.add_ledger("program", "test", [node("lem:base"),
                                            node("thm:top", depends_on=["lem:base"])])

        layout = self.data()["layout"]["claims"]

        self.assertEqual(sorted(layout), ["lem:base", "thm:top"])

    def test_a_dependency_is_laid_out_below_what_rests_on_it(self):
        """Layout is navigation only, but it must not assert the reverse of the truth."""
        self.add_ledger("program", "test", [node("lem:base"),
                                            node("thm:top", depends_on=["lem:base"])])

        layout = self.data()["layout"]["claims"]

        self.assertGreater(layout["thm:top"]["y"], layout["lem:base"]["y"])

    def test_only_proof_dependencies_set_the_layering(self):
        """An antecedent is not a dependency; letting it layer would say it was."""
        self.add_ledger("program", "test", [
            node("asm:a", status="open", kind="assumption"),
            node("thm:b", assumes=["asm:a"]),
        ])

        layout = self.data()["layout"]["claims"]

        self.assertEqual(layout["asm:a"]["y"], layout["thm:b"]["y"])


class Output(SiteFixture):
    def test_the_frontend_and_the_data_are_written(self):
        self.add_ledger("program", "test", [node("thm:a")])

        self.publish()

        for name in ("index.html", "site.css", "site.js", "data.json"):
            self.assertTrue((self.out / name).is_file(), name)

    def test_data_json_is_valid_json_and_matches_what_build_returned(self):
        self.add_ledger("program", "test", [node("thm:a")])

        data, _errors = self.publish()

        self.assertEqual(json.loads((self.out / "data.json").read_text()), data)

    def test_publishing_a_subtree_records_the_prefix_its_links_need(self):
        """`--root example` publishes paths that are only addressable with a prefix."""
        prefix = site_module._source_prefix(EXAMPLE)

        self.assertEqual(prefix, "example/")
        self.assertEqual(site_module._source_prefix(REPO), "")


class TheFrontendHoldsNoMathematics(unittest.TestCase):
    """The invariant that keeps this a derived view rather than a second home.

    Everything substantive is derived at build time. A statement, a status, a route
    objective or a blocker typed into site/ would drift from the ledger and the portfolio
    the first time either changed, and the prettier copy would win the argument.
    """

    @classmethod
    def setUpClass(cls):
        if not EXAMPLE.is_dir():  # pragma: no cover - fixture tree always ships
            raise unittest.SkipTest("no worked example to publish")
        cls.out = Path(REPO / "build/site-selftest")
        shutil.rmtree(cls.out, ignore_errors=True)
        cls.data, cls.errors = site_module.build(EXAMPLE, cls.out)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.out, ignore_errors=True)

    def setUp(self):
        self.assertEqual(self.errors, [], "the worked example must stay publishable")

    #: Exactly the suffixes ``build()`` copies into the site. The scope is deliberate:
    #: only these files become the page, so only these can leak a second copy of a
    #: statement to a reader. ``README.md`` and ``tex4ht.cfg`` are prose *about* the
    #: frontend and name ids freely — a documentation example is not a source of truth,
    #: and forbidding it would be a rule with no failure behind it.
    DEPLOYED = {".html", ".css", ".js"}

    def frontend_text(self) -> str:
        return "\n".join(path.read_text(encoding="utf-8")
                         for path in sorted(FRONTEND.iterdir())
                         if path.is_file() and path.suffix in self.DEPLOYED)

    def test_the_scope_of_these_checks_is_what_actually_ships(self):
        """If build() starts copying a suffix, this class must start reading it."""
        published = {path.suffix for path in (self.out).iterdir() if path.is_file()}

        self.assertLessEqual(published - {".json"}, self.DEPLOYED)

    def test_no_claim_gloss_appears_in_the_frontend(self):
        text = self.frontend_text()
        for claim in self.data["claims"].values():
            self.assertNotIn(claim["gloss"], text, claim["id"])

    def test_no_candidate_statement_or_route_objective_appears_in_the_frontend(self):
        text = self.frontend_text()
        for candidate in self.data["memory"]["candidates"]:
            self.assertNotIn(candidate["statement"], text, candidate["id"])
        for route in self.data["search"]["routes"].values():
            if route["objective"]:
                self.assertNotIn(route["objective"], text, route["id"])

    def test_no_node_or_route_id_is_hard_coded_in_the_frontend(self):
        text = self.frontend_text()
        for identifier in [*self.data["claims"], *self.data["search"]["routes"],
                           *self.data["search"]["families"]]:
            self.assertNotIn(identifier, text, identifier)

    def test_the_worked_example_exercises_every_genre_the_site_renders(self):
        """If this fails, the fixture stopped covering a path the site draws."""
        statuses = {claim["status"] for claim in self.data["claims"].values()}
        states = {route["state"] for route in self.data["search"]["routes"].values()}
        modes = {proof["mode"] for claim in self.data["claims"].values()
                 for proof in claim["proofs"]}

        self.assertLessEqual({"proved", "open", "refuted"}, statuses)
        self.assertLessEqual({"completed", "blocked", "duplicate"}, states)
        self.assertIn("agent", modes)
        self.assertTrue(self.data["memory"]["candidates"])
        self.assertTrue(self.data["memory"]["promoted"])
        self.assertTrue(self.data["memory"]["reviews"])


class FrontendSyntax(unittest.TestCase):
    """A syntax error in site.js is a blank page, and nothing else would catch it."""

    def test_the_script_parses(self):
        if shutil.which("node") is None:
            self.skipTest("node not installed")
        finished = subprocess.run(["node", "--check", str(FRONTEND / "site.js")],
                                  capture_output=True, text=True, check=False)

        self.assertEqual(finished.returncode, 0, finished.stderr)


class PagesWorkflow(unittest.TestCase):
    """Pin the deployment details that otherwise fail only on GitHub's runner."""

    def test_make4ht_comes_from_the_ubuntu_package_that_ships_it(self):
        text = PAGES_WORKFLOW.read_text(encoding="utf-8")
        install = text.split("sudo apt-get install", 1)[1].split("command -v make4ht", 1)[0]

        self.assertIn("texlive-extra-utils", install)
        self.assertNotRegex(install, r"(?:^|\s)make4ht(?:\s|$)")

    def test_deployment_follows_the_configured_default_branch(self):
        text = PAGES_WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("github.event.repository.default_branch", text)
        self.assertNotIn("refs/heads/main", text)
        self.assertNotIn("branches: [main]", text)

    def test_publishing_happens_only_when_a_human_asks(self):
        # Restoring `push:` here would republish the site from every commit on the
        # default branch, which is the behaviour this repository decided against.
        text = PAGES_WORKFLOW.read_text(encoding="utf-8")
        triggers = text.split("\non:", 1)[1].split("\npermissions:", 1)[0]

        self.assertIn("workflow_dispatch", triggers)
        self.assertNotIn("push", triggers)
        self.assertNotIn("pull_request", triggers)


class CheckWorkflow(unittest.TestCase):
    """The cheap checks are the ones that may run unattended."""

    def test_pull_requests_are_validated(self):
        text = CHECK_WORKFLOW.read_text(encoding="utf-8")
        triggers = text.split("\non:", 1)[1].split("\npermissions:", 1)[0]

        self.assertIn("pull_request", triggers)
        self.assertIn("scripts/check.py", text)
        self.assertIn("unittest discover", text)

    def test_the_expensive_half_stays_out_of_it(self):
        # If TeX Live ever reappears here, every pull request pays minutes for a
        # document nobody asked to build. The comments name those tools to say where
        # they live, so this reads the steps and not the prose around them.
        steps = "\n".join(line for line in CHECK_WORKFLOW.read_text(encoding="utf-8").splitlines()
                          if not line.lstrip().startswith("#"))

        self.assertNotIn("texlive", steps)
        self.assertNotIn("latexmk", steps)
        self.assertNotIn("make4ht", steps)
        self.assertNotIn("deploy-pages", steps)


if __name__ == "__main__":
    unittest.main()
