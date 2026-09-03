"""Shared fixture tree for the plane checkers.

Every test builds a throwaway repository in a temporary directory, so nothing here can
touch the real ledger, the append-only checkpoints, or the immutable run artifacts.

The fixtures deliberately omit ``configured_ledger``: production pins exactly one ledger
path, while a fixture tree may hold several so that the one-ledger rule is itself
testable.
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
from checks.common import PLANES  # noqa: E402

CHECK = REPO / "scripts/check.py"


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
        path.write_text(yaml.safe_dump({"meta": meta, "nodes": fixture_nodes}, sort_keys=False))
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
                   authors: tuple[str, ...] = ("/root/researcher",),
                   solutions: tuple[str, ...] = (), report_type: str = "proof-review",
                   date: str = "2026-08-25", supersedes: tuple[str, ...] = (),
                   body: str = "fixture review\n") -> str:
        relative = f"research/reviews/{date}-{name}.md"
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
            "schema_version": 2,
            "date": "2026-08-26",
            "target": target,
            "profile": "standard",
            "config": {"seed": 1},
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
                       approach: str | None = None,
                       supersedes: tuple[str, ...] = (),
                       front_matter: dict | None = None,
                       body: str = "fixture checkpoint\n") -> str:
        relative = f"research/explorations/{date}-{name}.md"
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        metadata: dict = {"type": "exploration", "date": date, "outcome": outcome}
        if approach is not None:
            metadata["approach"] = approach
        for field, value in (("nodes", nodes), ("artifacts", artifacts),
                             ("candidates", candidates), ("retires", retires),
                             ("supersedes", supersedes)):
            if value:
                metadata[field] = [dict(item) if isinstance(item, dict) else item
                                   for item in value]
        if front_matter:
            metadata.update(front_matter)
        path.write_text(
            "---\n" + yaml.safe_dump(metadata, sort_keys=False) + "---\n\n" + body
        )
        return relative

    def add_portfolio(self, document: dict) -> Path:
        path = self.root / "research/program/portfolio.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(document, sort_keys=False))
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
        return analyze(self.root, self.research, **kwargs)

    def errors(self, planes: tuple[str, ...] = PLANES, **kwargs) -> str:
        return "\n".join(failures(self.check(**kwargs), planes))

    def cli(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CHECK), "--root", str(self.root), *arguments],
            cwd=self.root, capture_output=True, text=True, check=False,
        )
