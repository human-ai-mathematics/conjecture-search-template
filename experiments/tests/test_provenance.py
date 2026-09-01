"""Artifact writes are immutable; provenance separates configuration and environment."""

from __future__ import annotations

import json

import pytest

from numerics import provenance as provenance_module


def test_write_jsonl_uses_exclusive_creation(tmp_path):
    path = tmp_path / "run.jsonl"
    provenance_module.write_jsonl(
        path, {"target": "test"}, [{"kind": "diagnostic"}], {"passed": True})
    with pytest.raises(FileExistsError):
        provenance_module.write_jsonl(path, {"target": "test"}, [])

    lines = path.read_text().splitlines()
    assert json.loads(lines[0])["_provenance"]["target"] == "test"
    assert json.loads(lines[1])["kind"] == "diagnostic"
    assert json.loads(lines[2]) == {"kind": "run-summary", "passed": True}


def test_provenance_does_not_gate_on_worktree_state(monkeypatch):
    answers = {("rev-parse", "HEAD"): "abc123"}
    monkeypatch.setattr(provenance_module, "_git", lambda *args: answers.get(args))
    header = provenance_module.provenance(
        schema_version=1, target="test", profile="standard", stochastic=False,
        config={"seed": 0},
    )
    assert header["git_commit"] == "abc123"
    assert header["config"] == {"seed": 0}
    assert "git_dirty" not in header
    assert "evidence_eligible" not in header
