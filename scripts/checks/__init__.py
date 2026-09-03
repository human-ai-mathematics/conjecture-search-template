"""Structural validation of this repository, split by plane.

One pass gathers every plane, because the planes reference each other: a checkpoint
names a portfolio approach, the portfolio blocks a route on a candidate the checkpoint
log proposes, and a proof record points at a review. Errors are *tagged* by plane so a
caller can scope what it reports without the checker having to guess which half of a
cross-plane reference to trust.

A plane whose files are absent contributes nothing. That is what makes activation
structural: a repository with no portfolio has no portfolio rules to obey, and one that
has never run a numeric has no numerics plane.
"""
from __future__ import annotations

from pathlib import Path

from . import checkpoints, ledger, numerics, portfolio, proofs, roles
from .common import PLANES

ROOT = Path(__file__).resolve().parents[2]


def analyze(root: Path | None = None, research: Path | None = None,
            configured_ledger: str | Path | None = None, *,
            write_codex: bool = False) -> dict:
    """Validate every plane of one repository tree and return the tagged report."""
    root = Path(root) if root is not None else ROOT
    research = Path(research) if research is not None else root / "research"
    errors: dict[str, list[str]] = {plane: [] for plane in PLANES}

    labels = ledger.all_labels(root)
    ledgers = ledger.check(root, research, errors["core"], configured_ledger, labels)
    node_ids = ledger.node_ids(ledgers)

    archive = proofs.check(root, ledgers, errors["proofs"])

    live_portfolio = portfolio.load(root, errors["portfolio"])
    brief = portfolio.check_brief(root, node_ids, errors["portfolio"])

    memory = checkpoints.check(
        root, node_ids, portfolio.approach_ids(live_portfolio), errors["checkpoints"]
    )
    memory["superseded_audits"] = checkpoints.check_audit_supersession(
        root, archive, errors["checkpoints"]
    )

    portfolio.resolve(live_portfolio, brief, node_ids,
                      {entry["id"] for entry in memory["candidates"]}, errors["portfolio"])

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


def failures(report: dict, planes: tuple[str, ...] = PLANES) -> list[str]:
    """Every error from the selected planes, prefixed with the plane that raised it."""
    return [f"[{plane}] {message}"
            for plane in planes for message in report["errors"][plane]]
