"""Structural validation of this repository, split by lane.

One pass gathers every lane, because the lanes reference each other: a checkpoint
names a portfolio approach, the portfolio blocks a route on a candidate the checkpoint
log proposes, and a proof record points at a review. Errors are *tagged* by lane so a
caller can scope what it reports without the checker having to guess which half of a
cross-lane reference to trust.

A lane whose files are absent contributes nothing. That is what makes activation
structural: a repository with no portfolio has no portfolio rules to obey, and one that
has never run a numeric has no numerics lane.
"""
from __future__ import annotations

from pathlib import Path

from . import checkpoints, ledger, numerics, portfolio, proofs, roles
from .common import LANES

ROOT = Path(__file__).resolve().parents[2]


def analyze(root: Path | None = None, research: Path | None = None,
            configured_ledger: str | Path | None = None, *,
            write_codex: bool = False) -> dict:
    """Validate every lane of one repository tree and return the tagged report."""
    root = Path(root) if root is not None else ROOT
    research = Path(research) if research is not None else root / "research"
    errors: dict[str, list[str]] = {lane: [] for lane in LANES}

    labels = ledger.manuscript_labels(root, errors["core"])
    ledgers = ledger.check(root, research, errors["core"], configured_ledger, labels)
    node_ids = ledger.node_ids(ledgers)

    archive = proofs.check(root, ledgers, errors["proofs"])

    live_portfolio = portfolio.load(root, errors["portfolio"])
    brief = portfolio.check_brief(root, errors["portfolio"])

    memory = checkpoints.check(
        root, node_ids, portfolio.approach_ids(live_portfolio), errors["checkpoints"]
    )
    memory["superseded_audits"] = checkpoints.check_audit_supersession(
        root, archive, errors["checkpoints"]
    )

    all_nodes = {nid: node for item in ledgers for nid, node in item["nodes"].items()}
    portfolio.resolve(live_portfolio, brief, node_ids, memory, errors["portfolio"],
                      nodes=all_nodes)

    artifacts = numerics.check(root, errors["numerics"])
    role_definitions = roles.check(root, errors["roles"], write_codex=write_codex)

    return {
        "errors": errors,
        "ledgers": ledgers,
        "labels": labels,
        "candidates": memory["candidates"],
        "checkpoints": memory,
        "portfolio": live_portfolio,
        "brief": brief,
        "artifacts": artifacts,
        "roles": role_definitions,
        "archive": archive,
    }


def failures(report: dict, lanes: tuple[str, ...] = LANES) -> list[str]:
    """Every error from the selected lanes, prefixed with the lane that raised it."""
    return [f"[{lane}] {message}"
            for lane in lanes for message in report["errors"][lane]]
