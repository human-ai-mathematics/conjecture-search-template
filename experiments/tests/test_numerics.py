"""End-to-end checks for the public target and artifact boundary.

These test the harness contract, not any particular mathematics: every registered target must
expose the same shape and reproduce its own closed-form anchors, and every run must produce a
versioned envelope whose inputs stay separate from its derived summary. They keep passing as
targets come and go. Passing proves nothing mathematical (CLAUDE.md constraint 4).
"""
from __future__ import annotations

import hashlib
import json

import pytest

from numerics import artifact
from numerics.__main__ import main
from numerics.contract import (
    ARTIFACT_SCHEMA_VERSION,
    OBSERVATION_FIELDS,
    RunResult,
    compare,
    matches,
    observe,
    searched,
)
from numerics.targets import REGISTRY


# --- the target contract -------------------------------------------------------------------

def test_registry_has_explicit_metadata_and_standard_profiles():
    assert REGISTRY, "the registry must expose at least one target"
    for target, spec in REGISTRY.items():
        assert spec.id == target
        assert spec.summary
        assert "standard" in spec.profiles
        assert hasattr(spec.module, "run_records")


@pytest.mark.parametrize("target", sorted(REGISTRY))
def test_every_target_reproduces_its_closed_form_anchors(target, tmp_path):
    """The calibration lane: a target whose anchors drift has a bug, not a discovery."""
    path = artifact.run(target, seed=7, profile="standard", out=tmp_path / f"{target}.jsonl")
    records = [json.loads(line) for line in path.read_text().splitlines()[1:-1]]
    calibrations = [r for r in records if r.get("evidence") == "calibration"]
    assert calibrations, f"target '{target}' records no calibration against a closed form"
    assert [r for r in calibrations if r["outcome"] == "mismatch"] == []


@pytest.mark.parametrize("target", sorted(REGISTRY))
def test_every_recorded_observation_is_fully_labelled(target, tmp_path):
    """A reader of research/runs/ never has to infer a claim or an evidence class."""
    path = artifact.run(target, seed=7, profile="standard", out=tmp_path / f"{target}.jsonl")
    records = [json.loads(line) for line in path.read_text().splitlines()[1:-1]]
    observations = [r for r in records if "claim" in r]
    assert observations, f"target '{target}' records no observation"
    for record in observations:
        assert all(record.get(name) for name in OBSERVATION_FIELDS)
        assert isinstance(record["detail"], dict)


def test_target_rejects_unknown_profile():
    with pytest.raises(ValueError, match="no profile"):
        REGISTRY["example"].config_for("no-such-profile")


def test_run_result_rejects_untyped_records():
    with pytest.raises(ValueError, match="string 'kind'"):
        RunResult([{"instance": "missing-kind"}]).validate()
    with pytest.raises(ValueError, match="runner-owned 'seed'"):
        RunResult([], config={"seed": 1}).validate()
    with pytest.raises(ValueError, match="runner-owned field"):
        RunResult([], summary={"kind": "wrong"}).validate()


def test_run_result_rejects_half_labelled_observations():
    """An unlabelled number must not be able to look like evidence."""
    with pytest.raises(ValueError, match="'evidence' must be"):
        RunResult([{"kind": "diagnostic", "instance": "i", "claim": "c"}]).validate()
    with pytest.raises(ValueError, match="takes outcome"):
        RunResult([{"kind": "diagnostic", "instance": "i", "claim": "c",
                    "evidence": "exact", "outcome": "match"}]).validate()
    # Auxiliary data a target chose to keep alongside its observations stays legal.
    RunResult([{"kind": "spectrum", "eigenvalues": [1.0, 2.0]}]).validate()


# --- the record vocabulary -----------------------------------------------------------------

def test_outcomes_are_neutral_across_genres_and_evidence_is_checked():
    assert compare("i", "c", bound=1.0, value=2.0, evidence="directional").outcome == "contradicts"
    assert compare("i", "c", bound=1.0, value=0.5, evidence="exact").outcome == "consistent"
    assert compare("i", "c", bound=float("inf"), value=0.5,
                   evidence="exact").outcome == "inconclusive"
    assert matches("i", "c", value=1.0, exact=1.0).outcome == "match"
    assert matches("i", "c", value=2.0, exact=1.0).outcome == "mismatch"
    assert searched("i", "c", domain="n <= 10^6").outcome == "consistent"
    assert searched("i", "c", domain="n <= 10^6", witness=[3, 5]).outcome == "contradicts"
    with pytest.raises(ValueError, match="evidence must be one of"):
        compare("i", "c", bound=1.0, value=0.5, evidence="proved")
    with pytest.raises(ValueError, match="takes outcome"):
        observe("i", "c", evidence="calibration", outcome="consistent")


def test_genre_specific_fields_stay_in_detail():
    """The contract is kind/claim/evidence/outcome; everything else is the target's own."""
    record = observe("i", "the Groebner basis contains 1", evidence="exact",
                     outcome="contradicts", ideal="<x^2-y, y^2>", basis_size=3).record("witness")
    assert set(record) == {"kind", *OBSERVATION_FIELDS, "detail", "note"}
    assert record["detail"] == {"ideal": "<x^2-y, y^2>", "basis_size": 3}
    assert searched("i", "c", domain="n <= 10^6").record("search")["detail"]["witness"] is None


# --- the artifact --------------------------------------------------------------------------

def test_run_writes_versioned_envelope_and_separate_summary(tmp_path):
    path = artifact.run("example", seed=3, profile="standard", out=tmp_path / "example.jsonl")
    lines = [json.loads(line) for line in path.read_text().splitlines()]
    header = lines[0]["_provenance"]
    assert header["schema_version"] == ARTIFACT_SCHEMA_VERSION
    assert header["target"] == "example"
    assert header["config"]["seed"] == 3
    assert lines[-1]["kind"] == "run-summary"
    assert lines[-1]["target"] == "example"


def test_run_is_reproducible_from_its_recorded_seed(tmp_path):
    first = artifact.run("example", seed=11, out=tmp_path / "a.jsonl")
    second = artifact.run("example", seed=11, out=tmp_path / "b.jsonl")
    summary_of = lambda path: json.loads(path.read_text().splitlines()[-1])
    assert summary_of(first)["mean"] == summary_of(second)["mean"]


def test_artifact_write_never_overwrites(tmp_path):
    path = tmp_path / "once.jsonl"
    artifact.write_jsonl(path, {"target": "test"}, [{"kind": "diagnostic"}], {"passed": True})
    with pytest.raises(FileExistsError):
        artifact.write_jsonl(path, {"target": "test"}, [])

    lines = path.read_text().splitlines()
    assert json.loads(lines[0])["_provenance"]["target"] == "test"
    assert json.loads(lines[1])["kind"] == "diagnostic"
    assert json.loads(lines[2]) == {"kind": "run-summary", "passed": True}


def test_provenance_records_the_worktree_without_gating_on_it(monkeypatch):
    """The dirty flag is provenance. Nothing decides whether output "counts"."""
    monkeypatch.setattr(artifact, "_git", lambda *args: "abc123")
    header = artifact.provenance(target="test", profile="standard", stochastic=False,
                                 config={"seed": 0})
    assert header["git_commit"] == "abc123"
    assert header["config"] == {"seed": 0}
    assert header["git_dirty"] is True
    assert header["git_diff_sha256"] == hashlib.sha256(b"abc123").hexdigest()
    assert "evidence_eligible" not in header
    assert "evidence_run" not in header


def test_a_clean_worktree_records_no_diff(monkeypatch):
    monkeypatch.setattr(artifact, "_git",
                        lambda *args: "" if args[0] in {"diff", "status"} else "abc123")

    state = artifact.source_state()

    assert state == {"git_commit": "abc123", "git_dirty": False, "git_diff_sha256": None}


def test_source_state_is_complete_outside_a_checkout(monkeypatch):
    monkeypatch.setattr(artifact, "_git", lambda *args: None)

    state = artifact.source_state()

    assert state == {"git_commit": None, "git_dirty": None, "git_diff_sha256": None}


def test_the_cli_writes_only_into_the_archive(tmp_path):
    outside = tmp_path / "stray.jsonl"
    with pytest.raises(SystemExit):
        main(["run", "example", "--out", str(outside)])
    assert not outside.exists()

    inside = artifact.confine_to_runs("nested/run.jsonl")
    assert inside.parent.parent == artifact.runs_dir().resolve()


# --- the CLI -------------------------------------------------------------------------------

def test_cli_requires_a_known_target(tmp_path, monkeypatch):
    with pytest.raises(SystemExit):
        main(["run"])
    with pytest.raises(SystemExit):
        main(["run", "no-such-target"])

    called = {}

    def fake_run(target, seed, profile, out):
        called.update(target=target, seed=seed, profile=profile, out=out)
        return tmp_path / "artifact.jsonl"

    monkeypatch.setattr(artifact, "run", fake_run)
    assert main(["run", "example", "--profile", "full", "--seed", "9"]) == 0
    assert called == {"target": "example", "seed": 9, "profile": "full", "out": None}


def test_a_bare_instance_is_half_an_observation():
    """The write-time check and the archive check must agree on all four fields.

    Excluding `instance` here let a target write an artifact that the numerics lane
    then rejected, which is the one failure this check exists to prevent.
    """
    result = RunResult([{"kind": "measurement", "instance": "case-1", "value": 1.0}])
    with pytest.raises(ValueError, match="'claim' must be a non-empty string"):
        result.validate()
