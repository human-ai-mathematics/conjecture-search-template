"""The portfolio lane: what the search is doing, and the brief that scopes it.

The ledger says what is mathematically claimed. This lane says which routes are alive,
which are blocked and on what, which are duplicates of each other, and which families
have been worked out. None of that is mathematical truth, so none of it belongs in the
ledger — and the portfolio in turn never restates a statement: it points at a `cand:` id
or a node id and stops (CLAUDE.md constraint 12).

Every check here is structural. Whether two routes are *really* the same idea, and
whether a family is *really* exhausted, are synthesizer judgments; a validator that
guessed at them would be worse than one that admits it cannot.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

from .common import APPROACH_ID_RE, contained_path, read_front_matter

PORTFOLIO_PATH = Path("research/program/portfolio.yaml")
BRIEF_PATH = Path("research/program/brief.md")
CHECKPOINTS = "research/explorations"

FAMILY_ID_RE = re.compile(r"^fam:[a-z0-9][a-z0-9-]*$")

TOP_LEVEL_FIELDS = {"target", "families", "approaches"}

FAMILY_FIELDS = {"id", "mechanism", "state", "closure_checkpoint", "reopen_if"}
FAMILY_STATES = {"active", "saturated", "parked"}
#: A family that is no longer being worked owes the next agent two things: the synthesis
#: that closed it, and the condition that would open it again. ``saturated`` claims the
#: mechanism is worked out; ``parked`` claims only that nobody is working it. The field is
#: named for closure rather than saturation so it reads honestly for both.
FAMILY_CLOSED_STATES = {"saturated", "parked"}
#: Retired field names, rejected by name so an inherited portfolio is told where to look.
OBSOLETE_FAMILY_FIELDS = {"saturation_checkpoint": "closure_checkpoint"}

APPROACH_FIELDS = {
    "id", "family", "objective", "parent", "state", "blocker", "reopen_if", "related",
    "checkpoints",
}
APPROACH_STATES = {"queued", "active", "blocked", "completed", "duplicate"}
#: A route that is no longer running left the search in a different shape than it found it.
#: "Checkpoints = why the portfolio changed" is only true if the change carries its record.
APPROACH_EXPLAINED_STATES = {"blocked", "completed", "duplicate"}
#: Live work. A closed family holds neither: a queued route is planned work, so a family
#: with one has not actually closed.
APPROACH_LIVE_STATES = {"active", "queued"}

#: Kinds a search cannot be aimed at. A definition is fixed by decision, not resolved by
#: work, and an obstruction is a fence the search reads rather than a thing it settles.
NON_TARGET_KINDS = {"definition", "obstruction"}

#: Once the target is one of these, the search has its answer.
RESOLVED_STATUSES = {"proved", "refuted"}
RELATION_FIELDS = {"to", "relation"}
RELATIONS = {"overlaps", "duplicates", "refines"}

BRIEF_FIELDS = {"type", "target"}


def _entries(raw: object, field: str, context: str, errors: list[str]) -> list[dict]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        errors.append(f"{context}.{field}: must be a list")
        return []
    entries = []
    for index, entry in enumerate(raw):
        if not isinstance(entry, dict):
            errors.append(f"{context}.{field}[{index}]: must be a mapping")
            continue
        entries.append(entry)
    return entries


def _identified(entries: list[dict], pattern: re.Pattern, shape: str, context: str,
                errors: list[str]) -> dict[str, dict]:
    identified: dict[str, dict] = {}
    for entry in entries:
        entry_id = entry.get("id")
        if not isinstance(entry_id, str) or not pattern.match(entry_id):
            errors.append(f"{context}: want an id of the form '{shape}', got '{entry_id}'")
            continue
        if entry_id in identified:
            errors.append(f"{context}: duplicate id '{entry_id}'")
            continue
        identified[entry_id] = entry
    return identified


def _state(entry: dict, entry_id: str, allowed: set[str], context: str,
           errors: list[str]) -> str | None:
    state = entry.get("state")
    if not isinstance(state, str) or state not in allowed:
        errors.append(
            f"{context} {entry_id}.state: want one of {sorted(allowed)}, got '{state}'"
        )
        return None
    return state


def _checkpoint_refs(root: Path, references: object, context: str,
                     errors: list[str]) -> list[str]:
    if references is None:
        return []
    if not isinstance(references, list):
        errors.append(f"{context}: must be a list of repo-relative checkpoint paths")
        return []
    resolved = []
    for reference in references:
        if contained_path(root, reference, CHECKPOINTS, context, errors, suffix=".md"):
            resolved.append(reference)
    return resolved


def load(root: Path, errors: list[str]) -> dict | None:
    """Parse and structurally validate the portfolio; ``None`` when there is none.

    An absent portfolio is not an error. A repository with one target and one route
    coordinates itself; the portfolio earns its keep only once several routes, agents,
    or sessions are in flight.
    """
    path = root / PORTFOLIO_PATH
    if not path.is_file():
        return None
    context = str(PORTFOLIO_PATH)
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (yaml.YAMLError, OSError, UnicodeError) as exc:
        errors.append(f"{context}: invalid YAML: {exc}")
        return None
    if not isinstance(doc, dict):
        errors.append(f"{context}: top level must be a mapping")
        return None
    for field in sorted(set(doc) - TOP_LEVEL_FIELDS):
        errors.append(f"{context}: unknown top-level field '{field}'")

    target = doc.get("target")
    if not isinstance(target, str) or not target.strip():
        errors.append(f"{context}.target: must name the ledger node this search is aimed at")
        target = None

    families = _identified(
        _entries(doc.get("families"), "families", context, errors),
        FAMILY_ID_RE, "fam:<slug>", f"{context}.families", errors,
    )
    approaches = _identified(
        _entries(doc.get("approaches"), "approaches", context, errors),
        APPROACH_ID_RE, "ap:<slug>", f"{context}.approaches", errors,
    )

    for family_id, family in sorted(families.items()):
        where = f"{context}.families"
        for field, replacement in OBSOLETE_FAMILY_FIELDS.items():
            if field in family:
                errors.append(
                    f"{where} {family_id}.{field}: obsolete field; use {replacement}"
                )
        for field in sorted(set(family) - FAMILY_FIELDS - set(OBSOLETE_FAMILY_FIELDS)):
            errors.append(f"{where} {family_id}: unknown field '{field}'")
        mechanism = family.get("mechanism")
        if not isinstance(mechanism, str) or not mechanism.strip():
            errors.append(f"{where} {family_id}.mechanism: must say what the family tries")
        state = _state(family, family_id, FAMILY_STATES, where, errors)
        family["_state"] = state
        checkpoint = family.get("closure_checkpoint")
        reopen = family.get("reopen_if")
        family["_closure_checkpoint"] = None
        if state in FAMILY_CLOSED_STATES:
            if checkpoint is None:
                errors.append(
                    f"{where} {family_id}.closure_checkpoint: state '{state}' requires "
                    "the checkpoint that closed the family"
                )
            elif contained_path(root, checkpoint, CHECKPOINTS,
                                f"{where} {family_id}.closure_checkpoint", errors,
                                suffix=".md"):
                family["_closure_checkpoint"] = checkpoint
            if not isinstance(reopen, str) or not reopen.strip():
                errors.append(
                    f"{where} {family_id}.reopen_if: state '{state}' requires the condition "
                    "under which the family reopens"
                )
        elif state is not None:
            for field, value in (("closure_checkpoint", checkpoint), ("reopen_if", reopen)):
                if value is not None:
                    errors.append(
                        f"{where} {family_id}.{field}: valid only for a closed "
                        "(saturated or parked) family"
                    )

    for approach_id, approach in sorted(approaches.items()):
        where = f"{context}.approaches"
        for field in sorted(set(approach) - APPROACH_FIELDS):
            errors.append(f"{where} {approach_id}: unknown field '{field}'")
        state = _state(approach, approach_id, APPROACH_STATES, where, errors)
        approach["_state"] = state

        family_id = approach.get("family")
        if not isinstance(family_id, str) or not family_id.strip():
            errors.append(f"{where} {approach_id}.family: must name an approach family")
        elif family_id not in families:
            errors.append(f"{where} {approach_id}.family: '{family_id}' is not a family")

        # A family says what mechanism it tries; without this, an individual route said
        # nothing at all and was legible only by reading its slug. Coordination text, not
        # a statement: it names an intention, never a claim (constraint 12).
        objective = approach.get("objective")
        if not isinstance(objective, str) or not objective.strip():
            errors.append(
                f"{where} {approach_id}.objective: one sentence saying what this route "
                "tries; a route nobody can read is a route nobody can deduplicate"
            )

        parent = approach.get("parent")
        if parent is not None:
            if not isinstance(parent, str) or parent not in approaches:
                errors.append(f"{where} {approach_id}.parent: '{parent}' is not an approach")
            elif parent == approach_id:
                errors.append(f"{where} {approach_id}.parent: an approach cannot parent itself")
            elif approaches[parent].get("family") != family_id:
                errors.append(
                    f"{where} {approach_id}.parent: '{parent}' is in family "
                    f"'{approaches[parent].get('family')}'; a child stays in its parent's "
                    "family, and a cross-family descendant is a 'refines' relation"
                )

        blocker = approach.get("blocker")
        reopen = approach.get("reopen_if")
        if state == "blocked":
            if not isinstance(blocker, str) or not blocker.strip():
                errors.append(
                    f"{where} {approach_id}.blocker: a blocked approach names the exact "
                    "candidate or ledger node it is blocked on"
                )
            if not isinstance(reopen, str) or not reopen.strip():
                errors.append(
                    f"{where} {approach_id}.reopen_if: a blocked approach names the "
                    "condition under which it reopens"
                )
        elif state is not None:
            for field, value in (("blocker", blocker), ("reopen_if", reopen)):
                if value is not None:
                    errors.append(
                        f"{where} {approach_id}.{field}: valid only for a blocked approach"
                    )

        approach["_related"] = []
        for index, relation in enumerate(
            _entries(approach.get("related"), "related", f"{where} {approach_id}", errors)
        ):
            marker = f"{where} {approach_id}.related[{index}]"
            for field in sorted(set(relation) - RELATION_FIELDS):
                errors.append(f"{marker}: unknown field '{field}'")
            other = relation.get("to")
            kind = relation.get("relation")
            if not isinstance(other, str) or other not in approaches:
                errors.append(f"{marker}.to: '{other}' is not an approach")
                continue
            if other == approach_id:
                errors.append(f"{marker}.to: an approach cannot relate to itself")
                continue
            if kind not in RELATIONS:
                errors.append(f"{marker}.relation: want one of {sorted(RELATIONS)}, got '{kind}'")
                continue
            approach["_related"].append((other, kind))

        approach["_checkpoints"] = _checkpoint_refs(
            root, approach.get("checkpoints"), f"{where} {approach_id}.checkpoints", errors
        )

    for approach_id, approach in sorted(approaches.items()):
        where = f"{context}.approaches"
        if approach.get("parent") == approach_id:
            continue
        seen: set[str] = set()
        ancestor = approach.get("parent")
        while isinstance(ancestor, str) and ancestor in approaches and ancestor not in seen:
            seen.add(ancestor)
            if ancestor == approach_id:
                break
            ancestor = approaches[ancestor].get("parent")
        if isinstance(ancestor, str) and ancestor == approach_id:
            errors.append(f"{where} {approach_id}.parent: approach ancestry contains a cycle")

        if approach.get("_state") == "duplicate" and not any(
            kind == "duplicates" for _other, kind in approach["_related"]
        ):
            errors.append(
                f"{where} {approach_id}: state 'duplicate' requires a "
                "related entry naming what it duplicates"
            )
        for other, kind in approach["_related"]:
            if kind != "duplicates":
                continue
            if approach.get("_state") == "active" and approaches[other].get("_state") == "active":
                errors.append(
                    f"{where} {approach_id}: duplicates '{other}', so both cannot be active; "
                    "keep one and mark the other 'duplicate'"
                )

    for family_id, family in sorted(families.items()):
        if family.get("_state") not in FAMILY_CLOSED_STATES:
            continue
        stragglers = sorted(
            approach_id for approach_id, approach in approaches.items()
            if approach.get("family") == family_id
            and approach.get("_state") in APPROACH_LIVE_STATES
        )
        if stragglers:
            errors.append(
                f"{context}.families {family_id}: state '{family['_state']}' with live "
                f"approach(es) {stragglers}; a queued route is planned work, so close them "
                "or reopen the family"
            )

    return {"path": path, "target": target, "families": families, "approaches": approaches}


def check_brief(root: Path, errors: list[str]) -> dict | None:
    """Validate the problem brief's envelope; ``None`` when there is none.

    Shape only. The target's resolution into the claim graph happens in :func:`resolve`
    with every other cross-lane reference, so that an unavailable ledger produces one
    honest dependency error instead of several silent omissions.
    """
    path = root / BRIEF_PATH
    if not path.is_file():
        return None
    context = str(BRIEF_PATH)
    raw = read_front_matter(path, "brief", errors)
    if raw is None:
        return None
    if raw.get("type") != "brief":
        errors.append(f"{context}.type: want 'brief', got '{raw.get('type')}'")
        return None
    for field in sorted(set(raw) - BRIEF_FIELDS):
        errors.append(f"{context}: field '{field}' is not valid for a brief")
    target = raw.get("target")
    if not isinstance(target, str) or not target.strip():
        errors.append(f"{context}.target: must name the ledger node this brief scopes")
        target = None
    return {"path": path, "target": target}


def _checkpoint_agreement(index: dict[str, dict], reference: str, expected: set[str],
                          context: str, subject: str, errors: list[str]) -> None:
    """Resolve one checkpoint reference through the parsed index and check its anchor.

    Existing on disk is not enough: ``research/explorations/README.md`` is a file in the
    right directory and is not a checkpoint, and a record whose envelope failed to parse
    is not durable memory either. Resolving through the index is what makes "checkpoints
    are why the portfolio changed" a fact rather than a slogan.
    """
    record = index.get(reference)
    if record is None:
        errors.append(
            f"{context}: '{reference}' is not a checkpoint; it must be a dated record "
            f"under {CHECKPOINTS}/ with a valid envelope"
        )
        return
    approach = record.get("approach")
    if approach is not None and approach not in expected:
        errors.append(
            f"{context}: '{reference}' declares approach '{approach}', which is not "
            f"{subject}"
        )


def resolve(portfolio: dict | None, brief: dict | None, node_ids: set[str],
            memory: dict, errors: list[str], nodes: dict[str, dict] | None = None) -> None:
    """Check every reference out of this lane: into the ledger, candidates, and memory.

    Kept separate from :func:`load` because the candidate set and the checkpoint index are
    derived from the checkpoint lane, which in turn needs this lane's approach ids.
    """
    if portfolio is None and brief is None:
        return
    context = str(PORTFOLIO_PATH)
    brief_context = str(BRIEF_PATH)
    nodes = nodes or {}
    target = portfolio["target"] if portfolio is not None else None
    brief_target = brief["target"] if brief is not None else None

    # Several coordinated routes *are* a sustained search, and a sustained search opens
    # with a brief. The reverse is not required: a brief with one live route needs no
    # portfolio (CLAUDE.md, "The gates").
    if portfolio is not None and brief is None:
        errors.append(
            f"{brief_context}: a portfolio coordinates several routes, which is a "
            "sustained search; write the brief that says what would finish it"
        )

    # The brief and the portfolio must agree with each other whether or not the claim
    # graph loaded: that comparison needs no ledger.
    if brief_target is not None and target is not None and brief_target != target:
        errors.append(
            f"{context}.target: '{target}' disagrees with the problem brief's target "
            f"'{brief_target}'"
        )

    # An unavailable claim graph is a dependency failure of this lane, not an absence of
    # errors in it. Scoping restricts what is reported; it never turns an unresolved
    # reference into a successful validation.
    if not node_ids:
        if target is not None or brief_target is not None:
            errors.append(
                f"{context}: the claim graph is unavailable or holds no nodes, so the "
                "target and blocker references cannot be resolved; fix the core lane first"
            )
    else:
        if isinstance(target, str) and target not in node_ids:
            errors.append(f"{context}.target: '{target}' is not a ledger node id")
        if isinstance(brief_target, str) and brief_target not in node_ids:
            errors.append(f"{brief_context}.target: '{brief_target}' is not a ledger node id")

    target_node = nodes.get(target) if isinstance(target, str) else None
    if target_node is not None:
        if target_node.get("kind") in NON_TARGET_KINDS:
            errors.append(
                f"{context}.target: '{target}' is a {target_node.get('kind')}; a search "
                "resolves a claim, and a definition or a fence is not one to resolve"
            )
        if portfolio is not None and target_node.get("status") in RESOLVED_STATUSES:
            still_live = sorted(
                approach_id for approach_id, approach in portfolio["approaches"].items()
                if approach.get("_state") in APPROACH_LIVE_STATES
            )
            if still_live:
                errors.append(
                    f"{context}: target '{target}' is "
                    f"{target_node.get('status')}, but {', '.join(still_live)} "
                    "remain active or queued; close the routes the answer settled"
                )

    if portfolio is None:
        return

    candidate_ids = {entry["id"] for entry in memory.get("candidates", [])}
    promoted = memory.get("promoted", {})
    index = {record["relative"]: record for record in memory.get("records", [])}

    for approach_id, approach in sorted(portfolio["approaches"].items()):
        where = f"{context}.approaches"
        blocker = approach.get("blocker")
        if node_ids and isinstance(blocker, str) and blocker.strip():
            if blocker in promoted:
                # The third half of an atomic promotion. The candidate is gone, the node
                # exists, and a route still pointing at the old id reads as blocked on
                # something nobody can look up.
                errors.append(
                    f"{where} {approach_id}.blocker: '{blocker}' was promoted to "
                    f"'{promoted[blocker]['node']}' in {promoted[blocker]['source']}; "
                    "block the route on the node instead"
                )
            elif blocker not in node_ids and blocker not in candidate_ids:
                errors.append(
                    f"{where} {approach_id}.blocker: '{blocker}' is neither a ledger node "
                    "nor a live candidate; state the missing lemma precisely before "
                    "blocking a route on it"
                )

        references = approach["_checkpoints"]
        if not references and approach.get("_state") in APPROACH_EXPLAINED_STATES:
            errors.append(
                f"{where} {approach_id}.checkpoints: state "
                f"'{approach['_state']}' requires the checkpoint that explains the change; "
                "a route does not stop without a reason the next agent can read"
            )
        for reference in references:
            _checkpoint_agreement(
                index, reference, {approach_id},
                f"{where} {approach_id}.checkpoints", f"'{approach_id}'", errors,
            )

    for family_id, family in sorted(portfolio["families"].items()):
        reference = family.get("_closure_checkpoint")
        if reference is None:
            continue
        members = {
            approach_id for approach_id, approach in portfolio["approaches"].items()
            if approach.get("family") == family_id
        }
        _checkpoint_agreement(
            index, reference, members,
            f"{context}.families {family_id}.closure_checkpoint",
            f"an approach in '{family_id}'", errors,
        )


def approach_ids(portfolio: dict | None) -> set[str] | None:
    return None if portfolio is None else set(portfolio["approaches"])
