"""A throwaway repository tree for the checker tests.

``check()`` runs the checker in process and passes the anchors ``ledger()`` wrote
straight to ``analyze``, so no MyST build is needed; ``cli()`` runs the real command,
MyST build included. How MyST's tree becomes anchors is ``test_manuscript.py``'s job.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from checks import analyze  # noqa: E402
from checks.manuscript import KIND  # noqa: E402
from checks.proofs import relied_on  # noqa: E402

CHECK = REPO / "scripts/check.py"

#: The site template is a local stub, so a fixture build never downloads MyST's theme.
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


def front_matter(metadata: dict, body: str = "fixture\n") -> str:
    return "---\n" + yaml.safe_dump(metadata, sort_keys=False) + "---\n\n" + body


def statement(node_id: str, text: str = "fixture") -> str:
    """The fingerprint the fixture's manuscript gives ``node_id``; ``text`` edits it."""
    return hashlib.sha256(f"{node_id}: {text}".encode()).hexdigest()


def node(node_id: str, *, status: str = "proved", kind: str = "theorem", **fields) -> dict:
    """A ledger node; ``kind`` is not a ledger field but the directive ``ledger()`` labels."""
    return {"id": node_id, "kind": kind, "status": status, **fields}


class CheckerFixture(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        (self.root / "modules").mkdir()
        self.module = self.root / "modules/test.md"
        self.module.write_text("# Fixture module\n")
        write_myst_project(self.root)
        (self.root / "references.bib").write_text("@article{Known,\n  title = {Known}\n}\n")
        #: What MyST would report for the module: ``{label: {"kind", "file"}}``, plus a
        #: claim's ``fingerprint``.
        self.anchors: dict[str, dict] = {}
        self.ledger([])

    def tearDown(self):
        self.tempdir.cleanup()

    def write(self, relative: str, text: str) -> str:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return relative

    def ledger(self, nodes: list[dict], *, anchor: bool = True, certify: bool = True) -> None:
        """Write the ledger. Each node gets a manuscript label of its ``kind`` and, when
        proved with neither ``references`` nor ``proofs``, a human-accepted fixture dossier
        fingerprinted as it stands now."""
        nodes = [dict(item) if isinstance(item, dict) else item for item in nodes]
        with self.module.open("a") as stream:
            for item in filter(lambda item: isinstance(item, dict), nodes):
                nid, kind = item.get("id"), item.get("kind")
                if not anchor or not isinstance(nid, str) or nid in self.anchors:
                    continue
                if kind in KIND:
                    stream.write(f"\n:::{{prf:{kind}}}\n:label: {nid}\nfixture\n:::\n")
                self.anchors[nid] = {"kind": kind if kind in KIND else None,
                                     "file": "modules/test.md"}
                if kind in KIND:
                    self.anchors[nid]["fingerprint"] = statement(nid)
        for item in filter(lambda item: isinstance(item, dict), nodes):
            item.pop("kind", None)
        graph = {item["id"]: item for item in nodes
                 if isinstance(item, dict) and isinstance(item.get("id"), str)}
        for item in filter(lambda item: isinstance(item, dict), nodes):
            if (certify and item.get("status") == "proved"
                    and "references" not in item and "proofs" not in item):
                artifact = self.solution(f"fixture-{item['id'].replace(':', '-')}", item["id"])
                item["proofs"] = [{"artifact": artifact, "accepted_by": "fixture human",
                                   "fingerprints": self.fingerprints(
                                       [artifact], relied_on(item["id"], graph))}]
        self.write("research/program/ledger.yaml",
                   yaml.safe_dump({"nodes": nodes},
                                  sort_keys=False))

    def solution(self, name: str, *node_ids: str) -> str:
        return self.write(f"solutions/{name}.md",
                          front_matter({"title": "Dossier", "ledger-node": list(node_ids)}))

    def review(self, name: str, *, solutions=(), statements=(), verdict: str = "pass",
               reviewer: str = "reviewer", authors=("researcher",), **extra) -> str:
        """A review of ``solutions`` checked against ``statements``, each fingerprinted as
        it stands now."""
        return self.write(f"research/reviews/2026-08-25-{name}.md", front_matter({
            "verdict": verdict, "authors": list(authors), "reviewer": reviewer,
            "fingerprints": self.fingerprints(solutions, statements), **extra,
        }))

    def fingerprints(self, solutions=(), statements=()) -> dict[str, str]:
        """Dossiers and statements as they stand now; zeros for what does not exist."""
        return {**{path: self.digest(path) for path in solutions},
                **{nid: self.anchors.get(nid, {}).get("fingerprint", "0" * 64)
                   for nid in statements}}

    def digest(self, relative: str) -> str:
        path = self.root / relative
        return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "0" * 64

    def checkpoint(self, name: str, *, date: str = "2026-08-26", **fields) -> str:
        return self.write(f"research/explorations/{date}-{name}.md", front_matter(fields))

    def brief(self, target: str) -> None:
        self.write("research/program/brief.md", front_matter({"target": target}))

    def portfolio(self, *approaches: dict) -> None:
        routes = [{"objective": f"try {item.get('id')}", **item} for item in approaches]
        self.write("research/program/portfolio.yaml", yaml.safe_dump({"approaches": routes}))

    def check(self) -> dict:
        return analyze(self.root, labels=self.anchors)

    def edit_statement(self, nid: str) -> None:
        """What MyST would report once the manuscript statement of ``nid`` is edited."""
        self.anchors[nid]["fingerprint"] = statement(nid, "edited")

    def errors(self) -> str:
        return "\n".join(self.check()["errors"])

    def assertClean(self) -> None:
        self.assertEqual(self.check()["errors"], [])

    def cli(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(CHECK), "--root", str(self.root), *arguments],
                              cwd=self.root, capture_output=True, text=True, check=False)
