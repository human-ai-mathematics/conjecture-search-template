"""Small end-to-end checks for the public target and artifact boundary.

These test the harness contract, not any particular mathematics: every target in
the registry must expose the same shape, and every run must produce a versioned
envelope whose inputs stay separate from its derived summary. They keep passing
as targets come and go.
"""
from __future__ import annotations

import json

import pytest

from numerics.__main__ import main
from numerics.contract import ARTIFACT_SCHEMA_VERSION, RunResult
from numerics.run import run
from numerics.targets import REGISTRY


def test_registry_has_explicit_metadata_and_standard_profiles():
    assert REGISTRY, "the registry must expose at least one target"
    for target, spec in REGISTRY.items():
        assert spec.id == target
        assert spec.summary
        assert "standard" in spec.profiles
        assert hasattr(spec.module, "run_records")
        assert hasattr(spec.module, "selftest")


def test_run_result_rejects_untyped_records():
    with pytest.raises(ValueError, match="string 'kind'"):
        RunResult([{"instance": "missing-kind"}]).validate()
    with pytest.raises(ValueError, match="runner-owned 'seed'"):
        RunResult([], config={"seed": 1}).validate()
    with pytest.raises(ValueError, match="runner-owned field"):
        RunResult([], summary={"kind": "wrong"}).validate()


def test_run_writes_versioned_envelope_and_separate_summary(tmp_path):
    path = run("example", seed=3, profile="standard", out=tmp_path / "example.jsonl")
    lines = [json.loads(line) for line in path.read_text().splitlines()]
    header = lines[0]["_provenance"]
    assert header["schema_version"] == ARTIFACT_SCHEMA_VERSION
    assert header["target"] == "example"
    assert header["config"]["seed"] == 3
    assert lines[-1]["kind"] == "run-summary"
    assert lines[-1]["target"] == "example"


def test_run_is_reproducible_from_its_recorded_seed(tmp_path):
    first = run("example", seed=11, profile="standard", out=tmp_path / "a.jsonl")
    second = run("example", seed=11, profile="standard", out=tmp_path / "b.jsonl")
    summary_of = lambda path: json.loads(path.read_text().splitlines()[-1])
    assert summary_of(first)["mean"] == summary_of(second)["mean"]


def test_artifact_write_never_overwrites(tmp_path):
    out = tmp_path / "once.jsonl"
    run("example", seed=1, profile="standard", out=out)
    with pytest.raises(FileExistsError):
        run("example", seed=1, profile="standard", out=out)


def test_target_rejects_unknown_profile():
    with pytest.raises(ValueError, match="no profile"):
        REGISTRY["example"].config_for("no-such-profile")


def test_cli_requires_a_known_target(monkeypatch, tmp_path):
    with pytest.raises(SystemExit):
        main(["run"])
    with pytest.raises(SystemExit):
        main(["run", "no-such-target"])

    called = {}

    def fake_run(target, seed, profile, out):
        called.update(target=target, seed=seed, profile=profile, out=out)
        return tmp_path / "artifact.jsonl"

    monkeypatch.setattr("numerics.run.run", fake_run)
    assert main(["run", "example", "--profile", "full", "--seed", "9"]) == 0
    assert called == {"target": "example", "seed": 9, "profile": "full", "out": None}
