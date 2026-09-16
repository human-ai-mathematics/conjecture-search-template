"""Shared fixture tree for the lane checkers.

Every test builds a throwaway repository in a temporary directory, so nothing here can
touch the real ledger, the append-only checkpoints, or the immutable run artifacts.

The fixtures deliberately omit ``configured_ledger``: production pins exactly one ledger
path, while a fixture tree may hold several so that the one-ledger rule is itself
testable.

Each fixture is also a real MyST project — ``myst.yml``, a module under ``modules/`` — so
that ``cli()`` runs the checker exactly as production does, MyST build included. The
in-process ``check()`` skips that build and passes the anchors ``add_ledger`` wrote
straight to ``analyze``: the lane rules never read prose, and a hundred MyST builds would
test nothing more. How MyST's tree becomes those anchors is ``test_manuscript.py``'s job.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from checks import analyze, failures  # noqa: E402
from checks.common import LANES  # noqa: E402
from checks.ledger import KIND  # noqa: E402

CHECK = REPO / "scripts/check.py"

#: A fixture's MyST configuration. The site template is a local stub, so a fixture build
#: never downloads MyST's theme.
MYST_CONFIG = """version: 1
project:
  title: Fixture
  toc:
    - file: index.md
    - pattern: '{modules,solutions}/!(README).md'
site:
  template: ./site-template
"""


def write_myst_project(root: Path) -> None:
    """Make ``root`` a MyST project whose site build needs no network."""
    (root / "myst.yml").write_text(MYST_CONFIG)
    (root / "index.md").write_text("# Fixture\n")
    template = root / "site-template"
    template.mkdir(exist_ok=True)
    (template / "template.yml").write_text("jtex: v1\ntitle: fixture stub\n")


def dossier_text(node_ids: tuple[str, ...] | list[str], body: str) -> str:
    """A dossier whose front matter names the nodes it discharges."""
    header = {"title": "Fixture dossier", "ledger-node": list(node_ids)}
    return "---\n" + yaml.safe_dump(header, sort_keys=False) + "---\n\n" + body


def node(node_id: str, *, status: str = "proved", kind: str = "theorem", **fields):
    result = {
        "id": node_id,
        "kind": kind,
        "status": status,
        "provenance": "internal",
        "file": "modules/test.md",
        "summary": f"fixture summary for {node_id}",
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
        self.module = modules / "test.md"
        self.module.write_text("# Fixture module\n")
        write_myst_project(self.root)
        #: What MyST would report for the module: ``{label: {"kind", "file"}}``.
        self.anchors: dict[str, dict] = {}
        (self.root / "references.bib").write_text(
            "@article{FixtureReference,\n"
            "  title = {Fixture reference},\n"
            "  year = {2026}\n"
            "}\n"
        )

    def tearDown(self):
        self.tempdir.cleanup()

    # --- building a fixture repository -------------------------------------------------

    def add_ledger(self, relative: str, program: str, nodes: list[dict], *,
                   meta_fields: dict | None = None,
                   certify_fixture_proofs: bool = True) -> Path:
        path = self.research / relative / "ledger.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        meta = {"program": program}
        if meta_fields:
            meta.update(meta_fields)
        fixture_nodes = [dict(item) for item in nodes]
        # Anchor each node the way the manuscript must: inside the claim directive named by
        # its own `kind`, so the fixture tree satisfies the same invariant a real modules/
        # does. A kind that is not a claim kind gets a structural heading label instead,
        # which is what the manuscript lane would find for it.
        anchors = [
            (item["id"], str(item.get("kind") or "theorem"))
            for item in fixture_nodes
            if isinstance(item.get("id"), str) and item["id"].strip()
        ]
        if anchors:
            with self.module.open("a", encoding="utf-8") as stream:
                for label, kind in anchors:
                    if kind in KIND:
                        stream.write(f"\n:::{{prf:{kind}}}\n:label: {label}\nfixture\n:::\n")
                    else:
                        stream.write(f"\n({label})=\n## Fixture {label}\n")
                    self.anchors[label] = {
                        "kind": kind if kind in KIND else None,
                        "file": self.module.relative_to(self.root).as_posix(),
                    }
        if certify_fixture_proofs:
            bare_proved = [
                item for item in fixture_nodes
                if item.get("status") == "proved"
                and item.get("provenance") == "internal"
                and "proofs" not in item
            ]
            if bare_proved:
                solution = f"solutions/fixture-{relative.replace('/', '-')}.md"
                solution_path = self.root / solution
                solution_path.parent.mkdir(parents=True, exist_ok=True)
                covered = [str(item.get("id")) for item in bare_proved]
                solution_path.write_text(dossier_text(covered, "standalone fixture proofs\n"))
                for item in bare_proved:
                    item["proofs"] = [{
                        "artifact": solution,
                        "mode": "human",
                        "accepted_by": "fixture human",
                    }]
        path.write_text(yaml.safe_dump({"meta": meta, "nodes": fixture_nodes}, sort_keys=False))
        return path

    def add_solution(self, name: str, *, node_ids: tuple[str, ...] = ()) -> str:
        relative = f"solutions/{name}.md"
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(dossier_text(node_ids, "standalone proof fixture\n"))
        return relative

    def add_review(self, name: str, *, verdict: str = "pass",
                   node_ids: tuple[str, ...] = (), reviewer: str = "/root/reviewer",
                   authors: tuple[str, ...] = ("/root/researcher",),
                   solutions: tuple[str, ...] = (), report_type: str = "proof-review",
                   date: str = "2026-08-25", supersedes: tuple[str, ...] = (),
                   body: str = "fixture review\n") -> str:
        relative = f"research/reviews/{date[:10]}-{name}.md"
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        metadata: dict = {"type": report_type, "date": date}
        if report_type == "proof-review":
            metadata.update({
                "verdict": verdict,
                "authors": list(authors),
                "reviewer": reviewer,
                "nodes": list(node_ids),
                "solutions": list(solutions),
            })
        elif supersedes:
            metadata["supersedes"] = list(supersedes)
        path.write_text(
            "---\n" + yaml.safe_dump(metadata, sort_keys=False) + "---\n\n" + body
        )
        return relative

    def add_run(self, name: str, *, target: str = "fixture", records: int = 1,
                header: dict | None = None, lines: list[str] | None = None) -> str:
        relative = f"research/runs/{name}"
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if lines is not None:
            path.write_text("".join(f"{line}\n" for line in lines))
            return relative
        provenance = {
            "schema_version": 1,
            "date": "2026-08-26",
            "target": target,
            "profile": "standard",
            "stochastic": False,
            "config": {"seed": 1},
            "git_commit": "0" * 40,
            "git_dirty": False,
            "git_diff_sha256": None,
            "environment": {"python": "3.13.0"},
        }
        if header is not None:
            provenance.update(header)
        body = [json.dumps({"_provenance": provenance})]
        body += [json.dumps({"kind": "observation", "index": index})
                 for index in range(records)]
        path.write_text("".join(f"{line}\n" for line in body))
        return relative

    def add_checkpoint(self, name: str, *, date: str = "2026-08-26",
                       outcome: str = "dead-end", nodes: tuple[str, ...] = (),
                       artifacts: tuple[str, ...] = (),
                       candidates: tuple[dict, ...] = (),
                       retires: tuple[str, ...] = (),
                       promotes: tuple[dict, ...] = (),
                       approach: str | None = None,
                       supersedes: tuple[str, ...] = (),
                       front_matter: dict | None = None,
                       body: str = "fixture checkpoint\n") -> str:
        relative = f"research/explorations/{date[:10]}-{name}.md"
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        metadata: dict = {"type": "exploration", "date": date, "outcome": outcome}
        if approach is not None:
            metadata["approach"] = approach
        for field, value in (("nodes", nodes), ("artifacts", artifacts),
                             ("candidates", candidates), ("retires", retires),
                             ("promotes", promotes), ("supersedes", supersedes)):
            if value:
                metadata[field] = [dict(item) if isinstance(item, dict) else item
                                   for item in value]
        if front_matter:
            metadata.update(front_matter)
        path.write_text(
            "---\n" + yaml.safe_dump(metadata, sort_keys=False) + "---\n\n" + body
        )
        return relative

    def add_portfolio(self, document: dict, *, brief: bool = True) -> Path:
        """Write a portfolio, filling in what every well-formed one carries.

        Each approach gets an ``objective`` unless the test supplies one, and a matching
        brief is written unless the test is exercising the portfolio-implies-brief rule.
        """
        document = dict(document)
        approaches = [dict(item) for item in document.get("approaches") or []]
        for item in approaches:
            item.setdefault("objective", f"fixture objective for {item.get('id')}")
        if approaches:
            document["approaches"] = approaches
        path = self.root / "research/program/portfolio.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(document, sort_keys=False))
        if brief and not (self.root / "research/program/brief.md").is_file():
            target = document.get("target")
            if isinstance(target, str):
                self.add_brief(target)
        return path

    def add_brief(self, target: str, *, body: str = "fixture brief\n") -> Path:
        path = self.root / "research/program/brief.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "---\n" + yaml.safe_dump({"type": "brief", "target": target}, sort_keys=False)
            + "---\n\n" + body
        )
        return path

    # --- running the checker -----------------------------------------------------------

    def check(self, **kwargs) -> dict:
        kwargs.setdefault("labels", self.anchors)
        return analyze(self.root, self.research, **kwargs)

    def errors(self, lanes: tuple[str, ...] = LANES, **kwargs) -> str:
        return "\n".join(failures(self.check(**kwargs), lanes))

    def cli(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CHECK), "--root", str(self.root), *arguments],
            cwd=self.root, capture_output=True, text=True, check=False,
        )
