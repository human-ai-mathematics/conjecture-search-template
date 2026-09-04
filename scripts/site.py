#!/usr/bin/env python3
"""Render this repository's derived views as a static, human-facing website.

    python3 scripts/site.py                         # -> build/site/
    python3 scripts/site.py --root example          # the worked example
    python3 scripts/site.py --out /tmp/preview      # anywhere
    python3 scripts/site.py --pdf-dir build         # attach the compiled PDFs
    python3 scripts/site.py --html-dir build/html   # attach the make4ht conversion
    python3 scripts/site.py --serve                 # build, then serve it locally

The governing rule, and the reason this file exists at all:

> The site is a derived view of the repository, never another source of mathematical or
> search state.

Everything it publishes is computed from ``checks.analyze`` — the same parsed, resolved
report ``scripts/check.py`` prints from. Nothing here re-reads YAML, re-parses LaTeX, or
re-implements a rule: two parsers of the same files eventually disagree, and the one that
is prettier wins the argument. ``site/`` holds the frontend and contains no mathematical
content; ``data.json`` holds the mathematics and contains no presentation.

**It refuses to build a repository that does not validate.** A structurally invalid
revision is not the current research state, and publishing one as though it were is worse
than publishing nothing. It does *not* refuse an uninstantiated template: a fresh clone is
correctly green and correctly not ready, and the site says so on its front page rather
than failing.

This is the third script in ``scripts/``, and the split is deliberate. ``check.py`` reads
and never writes. ``new.py`` creates hand-authored scaffolds without overwriting them and
regenerates explicitly derived agent files. This one writes, and overwrites freely, because
everything it produces is a *build artifact* under ``build/`` — gitignored, reproducible
from the tree, and never cited by anything in the repository. No lane of ``check.py``
validates its output, because its output is not repository state;
``scripts/tests/test_site.py`` is what keeps it honest.

Standard library plus PyYAML, which the checker already requires. No frontend framework,
bundler, or graph library: layouts are computed here, in Python, and drawn as plain SVG in
the browser. MathJax is the one optional CDN dependency; without it the LaTeX source remains
visible. A research program's claim graph has tens of nodes, not thousands, and the
deterministic layout works offline and cannot silently fail to load.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from checks import analyze, failures  # noqa: E402
from checks.common import LANES, as_list  # noqa: E402
from checks.ledger import LEDGER_PATH, applicability_blockers  # noqa: E402

#: Where the frontend lives, and where a build lands. Both repo-relative. ``build/`` is
#: already gitignored, so a built site is never committed by accident.
FRONTEND = Path("site")
DEFAULT_OUT = Path("build/site")

#: Relations, in the order a reader should meet them, with what each one *means*. The
#: gloss travels with the data so the frontend never has to know mathematics — and so the
#: legend cannot drift from ``research/program/ledger-schema.md`` in a second place.
#:
#: ``class`` separates truth from applicability from fencing, which is the distinction
#: CLAUDE.md constraints 5 and 8 exist to protect. Drawing them alike would erase it.
RELATIONS: tuple[tuple[str, str, str, str], ...] = (
    ("depends_on", "proof", "depends on",
     "Claims this proof actually used. This is the acyclic proof DAG."),
    ("assumes", "applicability", "assumes",
     "Antecedents of an implication. They affect applicability, not whether the "
     "implication was proved."),
    ("implies", "applicability", "implies",
     "Conclusions advertised by a proved implication."),
    ("refines", "refinement", "refines",
     "Statements this one makes more precise or stronger."),
    ("bounded_by", "hard-fence", "bounded by",
     "A proved obstruction: a hard mathematical fence. A statement violating one is "
     "wrong by construction."),
    ("heuristic_barriers", "soft-fence", "heuristic barrier",
     "An open obstruction: an advisory method barrier. It guides work; it fences "
     "nothing logically."),
    ("refuted_by", "refutation", "refuted by",
     "Proved refuters of a refuted node. Never a proof dependency: a refuted statement "
     "has no proof."),
)

#: The reverse reading of each relation, derived on demand and stored nowhere — the same
#: rule ``checks/views.py`` follows, for the same reason.
REVERSE = {
    "depends_on": ("used_by", "used by"),
    "assumes": ("assumed_by", "assumed by"),
    "implies": ("implied_by", "implied by"),
    "refines": ("refined_by", "refined by"),
    "refuted_by": ("refutes", "refutes"),
}

#: Front matter fence, so a checkpoint excerpt starts at the prose.
FRONT_MATTER_RE = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
HEADING_RE = re.compile(r"^#{1,6}\s")
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)

#: ``git@github.com:owner/name.git`` and ``https://github.com/owner/name`` alike.
REMOTE_RE = re.compile(r"github\.com[:/]+([^/]+)/([^/]+?)(?:\.git)?/?$")


# --------------------------------------------------------------------------------------
# provenance — which revision is on screen
# --------------------------------------------------------------------------------------

def _git(root: Path, *arguments: str) -> str | None:
    """One git query, or ``None`` when this is not a checkout and git cannot answer."""
    try:
        finished = subprocess.run(
            ["git", "-C", str(root), *arguments],
            capture_output=True, text=True, timeout=15, check=False,
        )
    except (OSError, subprocess.SubprocessError):  # pragma: no cover - environment guard
        return None
    return finished.stdout.strip() if finished.returncode == 0 else None


def provenance(root: Path, repository: str | None) -> dict:
    """What revision this build came from, so a reader can tell what they are looking at.

    Every page shows it. A site build that fails leaves the previous one online while the
    repository moves on, and a page that cannot say which commit it is displaying is
    indistinguishable from a page that is current (audit: *stale publication*).
    """
    root = root.resolve()
    commit = _git(root, "rev-parse", "HEAD")
    if repository is None:
        remote = _git(root, "remote", "get-url", "origin") or ""
        match = REMOTE_RE.search(remote)
        repository = f"{match.group(1)}/{match.group(2)}" if match else None
    return {
        "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "commit": commit,
        "short_commit": commit[:12] if commit else None,
        "dirty": bool(_git(root, "status", "--porcelain")),
        "branch": _git(root, "rev-parse", "--abbrev-ref", "HEAD"),
        "repository": repository,
        "source_prefix": _source_prefix(root),
    }


def _source_prefix(root: Path) -> str:
    """What to put in front of a repo-relative path to address it in the checkout.

    Every path in the report is relative to ``--root``, which is not always the checkout:
    ``--root example`` publishes the worked example, whose ``modules/00-overview.tex`` is
    ``example/modules/00-overview.tex`` to anyone following a link. Without this every
    source link on that build is a 404 that looks like a missing file rather than a
    mis-built site.
    """
    toplevel = _git(root, "rev-parse", "--show-toplevel")
    if not toplevel:
        return ""
    try:
        relative = root.relative_to(Path(toplevel).resolve())
    except ValueError:  # pragma: no cover - root outside its own checkout
        return ""
    return "" if relative == Path(".") else f"{relative.as_posix()}/"


# --------------------------------------------------------------------------------------
# derived data — the normalized artifact the frontend reads
# --------------------------------------------------------------------------------------

def _excerpt(path: Path, limit: int = 420) -> str | None:
    """The first prose paragraph of a dated record, for a card that must fit on screen.

    Deliberately an *excerpt* and labelled as one in the interface. Rendering a whole
    checkpoint would need a Markdown engine, which is a second renderer of repository
    prose and therefore a second place for it to be wrong; the record itself is one click
    away and GitHub already renders it.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):  # pragma: no cover - unreadable record
        return None
    text = HTML_COMMENT_RE.sub("", FRONT_MATTER_RE.sub("", text))
    for block in text.split("\n\n"):
        block = block.strip()
        if not block or HEADING_RE.match(block) or block.startswith(("---", "|", ">")):
            continue
        block = " ".join(block.split())
        return block if len(block) <= limit else block[:limit].rsplit(" ", 1)[0] + "…"
    return None


def _proof_record(proof: dict, archive: dict) -> dict:
    """One certification record, with what actually backs it.

    The two modes are *not* equally evidenced and the site must not draw them alike.
    ``mode: agent`` points at a persisted report whose front matter names distinct
    authors and reviewer, and that report is on disk. ``mode: human`` carries a name and
    no artifact — an honest record of a human acceptance, and honestly weaker evidence.
    """
    reference = proof.get("review")
    report = archive.get(reference) if isinstance(reference, str) else None
    record = {
        "artifact": proof.get("artifact"),
        "mode": proof.get("mode"),
        "review": reference,
        "accepted_by": proof.get("accepted_by"),
        "evidence": "persisted-review" if proof.get("mode") == "agent" else "attestation",
    }
    if report is not None:
        record["review_detail"] = {
            "date": report.get("date"),
            "verdict": report.get("verdict"),
            "reviewer": report.get("reviewer"),
            "authors": sorted(report.get("authors") or []),
        }
    return record


def _claims(report: dict, archive: dict) -> dict[str, dict]:
    """Every ledger node, with both directions of every relation and its certification."""
    labels = report["labels"]
    claims: dict[str, dict] = {}
    for ledger in report["ledgers"]:
        nodes = ledger["nodes"]
        for nid, node in nodes.items():
            anchor = labels.get(nid) or {}
            edges = {field: [item for item in as_list(node.get(field)) if isinstance(item, str)]
                     for field, _class, _label, _gloss in RELATIONS}
            reverse = {
                name: sorted(other for other, candidate in nodes.items()
                             if nid in as_list(candidate.get(field)))
                for field, (name, _label) in REVERSE.items()
            }
            claims[nid] = {
                "id": nid,
                "program": ledger["program"],
                "kind": node.get("kind"),
                "status": node.get("status"),
                "provenance": node.get("provenance"),
                "import_class": node.get("import_class"),
                # Named `gloss`, not `statement`. The canonical text is the \label in
                # modules/ and nowhere else (CLAUDE.md constraint 7); this one line is
                # what `ledger-schema.md` calls a gloss, and the interface says so next
                # to every occurrence of it.
                "gloss": node.get("summary"),
                "source": {"file": node.get("file") or anchor.get("file"),
                           "line": anchor.get("line"),
                           "environment": anchor.get("environment")},
                "references": [item for item in as_list(node.get("references"))
                               if isinstance(item, str)],
                "edges": edges,
                "reverse": reverse,
                "applicability_blocked_by": applicability_blockers(nid, nodes),
                "proofs": [_proof_record(proof, archive)
                           for proof in as_list(node.get("proofs"))
                           if isinstance(proof, dict)],
            }
    return claims


def _search(report: dict) -> dict | None:
    """The portfolio, with route ancestry derived rather than stored."""
    live = report.get("portfolio")
    if live is None:
        return None
    routes = {}
    for route_id, approach in live["approaches"].items():
        routes[route_id] = {
            "id": route_id,
            "family": approach.get("family"),
            "objective": (approach.get("objective") or "").strip() or None,
            "parent": approach.get("parent"),
            "state": approach.get("state"),
            "blocker": approach.get("blocker"),
            "reopen_if": (approach.get("reopen_if") or "").strip() or None,
            "related": [{"to": other, "relation": kind}
                        for other, kind in approach.get("_related", [])],
            "checkpoints": list(approach.get("_checkpoints", [])),
            "children": [],
        }
    for route_id, route in routes.items():
        parent = route["parent"]
        if isinstance(parent, str) and parent in routes:
            routes[parent]["children"].append(route_id)
    for route in routes.values():
        route["children"].sort()

    families = {}
    for family_id, family in live["families"].items():
        families[family_id] = {
            "id": family_id,
            "mechanism": (family.get("mechanism") or "").strip() or None,
            "state": family.get("state"),
            "closure_checkpoint": family.get("closure_checkpoint"),
            "reopen_if": (family.get("reopen_if") or "").strip() or None,
            "routes": sorted(route_id for route_id, route in routes.items()
                             if route["family"] == family_id),
        }
    return {"target": live["target"], "families": families, "routes": routes}


def _memory(report: dict) -> dict:
    """Durable evidence: checkpoints, candidates, promotions, reviews, audits, runs.

    Supersession is applied here rather than left to the reader. An append-only archive
    keeps provenance and supplies no current reading; naming the heir is what supplies it.
    """
    memory = report.get("checkpoints") or {}
    superseded = memory.get("superseded") or {}
    records = []
    for record in memory.get("records") or []:
        records.append({
            "path": record["relative"],
            "date": record["date"],
            "outcome": record["outcome"],
            "approach": record["approach"],
            "nodes": list(record["nodes"]),
            "artifacts": list(record["artifacts"]),
            "candidates": [dict(item) for item in record["candidates"]],
            "retires": list(record["retires"]),
            "promotes": [dict(item) for item in record["promotes"]],
            "superseded_by": sorted(superseded.get(record["relative"], [])),
            "excerpt": _excerpt(record["path"]),
        })
    records.sort(key=lambda item: (item["date"] or "", item["path"]), reverse=True)

    archive = report.get("archive") or {}
    superseded_audits = memory.get("superseded_audits") or set()
    reviews, audits = {}, {}
    for reference, metadata in archive.items():
        if metadata.get("type") == "proof-review":
            reviews[reference] = {
                "path": reference,
                "date": metadata.get("date"),
                "verdict": metadata.get("verdict"),
                "reviewer": metadata.get("reviewer"),
                "authors": sorted(metadata.get("authors") or []),
                "nodes": sorted(metadata.get("nodes") or []),
                "solutions": sorted(metadata.get("solutions") or []),
            }
        else:
            audits[reference] = {
                "path": reference,
                "date": metadata.get("date"),
                "superseded": reference in superseded_audits,
                "excerpt": _excerpt(metadata["path"]),
            }

    return {
        "checkpoints": records,
        "candidates": [{"id": entry["id"], "statement": entry["statement"],
                        "date": entry["date"], "source": entry["source"]}
                       for entry in report.get("candidates") or []],
        "promoted": {candidate: {"node": promotion["node"],
                                 "date": promotion["date"],
                                 "source": promotion["source"]}
                     for candidate, promotion in (memory.get("promoted") or {}).items()},
        "reviews": reviews,
        "audits": audits,
        "runs": [{"path": artifact["path"],
                  "target": artifact["target"],
                  "observations": artifact["records"]}
                 for artifact in report.get("artifacts") or []],
    }


# --------------------------------------------------------------------------------------
# layout — computed here, so the browser draws and does not decide
# --------------------------------------------------------------------------------------

#: Grid spacing in the abstract coordinate space the frontend scales. Layout is
#: *navigation only*: geometric proximity and centrality carry no mathematical meaning,
#: which is exactly why it is deterministic and computed once rather than simulated.
COLUMN, ROW = 260, 130


def _depth(node_id: str, edges: dict[str, list[str]], memo: dict[str, int],
           stack: frozenset[str] = frozenset()) -> int:
    """Longest path to a root of the proof DAG. The core lane guarantees acyclicity."""
    if node_id in memo:
        return memo[node_id]
    if node_id in stack:  # pragma: no cover - the core lane rejects cycles first
        return 0
    parents = [item for item in edges.get(node_id, []) if item in edges]
    depth = 0 if not parents else 1 + max(
        _depth(parent, edges, memo, stack | {node_id}) for parent in parents
    )
    memo[node_id] = depth
    return depth


def _place(layers: dict[int, list[str]]) -> dict[str, dict]:
    """Centre each layer over the widest one and hand back abstract coordinates."""
    widest = max((len(members) for members in layers.values()), default=1)
    positions: dict[str, dict] = {}
    for depth, members in layers.items():
        offset = (widest - len(members)) / 2
        for index, member in enumerate(sorted(members)):
            positions[member] = {"x": round((offset + index) * COLUMN),
                                 "y": round(depth * ROW)}
    return positions


def layout_claims(claims: dict[str, dict]) -> dict[str, dict]:
    """Layer the claim graph by proof depth: what a proof rests on sits below it.

    Only ``depends_on`` sets the layering. The other relations are drawn on top of it
    because they mean different things — an antecedent is not a dependency (constraint 8)
    — and letting them pull the layout would quietly assert that they were.
    """
    edges = {nid: [item for item in claim["edges"]["depends_on"] if item in claims]
             for nid, claim in claims.items()}
    memo: dict[str, int] = {}
    layers: dict[int, list[str]] = {}
    for nid in claims:
        layers.setdefault(_depth(nid, edges, memo), []).append(nid)
    return _place(layers)


def layout_search(search: dict | None) -> dict[str, dict]:
    """Lay routes out under their family, and children under their parent."""
    if search is None:
        return {}
    routes, positions = search["routes"], {}
    x = 0
    for family_id in sorted(search["families"]):
        family = search["families"][family_id]
        members = [route_id for route_id in family["routes"]]
        depth = {route_id: 0 for route_id in members}
        for _pass in range(len(members)):
            for route_id in members:
                parent = routes[route_id]["parent"]
                if parent in depth:
                    depth[route_id] = depth[parent] + 1
        rows: dict[int, list[str]] = {}
        for route_id in members:
            rows.setdefault(depth[route_id] + 1, []).append(route_id)
        width = max((len(row) for row in rows.values()), default=1)
        positions[family_id] = {"x": round((x + (width - 1) / 2) * COLUMN), "y": 0}
        for level, row in rows.items():
            for index, route_id in enumerate(sorted(row)):
                positions[route_id] = {"x": round((x + index) * COLUMN),
                                       "y": round(level * ROW)}
        x += width + 1
    return positions


# --------------------------------------------------------------------------------------
# assembly
# --------------------------------------------------------------------------------------

def export(report: dict, root: Path, *, repository: str | None = None,
           pdf_dir: Path | None = None, html_dir: Path | None = None) -> dict:
    """The whole derived artifact: everything the frontend is allowed to know."""
    archive = report.get("archive") or {}
    claims = _claims(report, archive)
    search = _search(report)
    memory = _memory(report)

    ledgers = report["ledgers"]
    program = ledgers[0] if ledgers else None
    brief = report.get("brief")
    target = None
    if search is not None:
        target = search["target"]
    elif brief is not None:
        target = brief.get("target")

    # Which routes a claim or a live candidate is holding up. Derived here because the
    # portfolio names a blocker and never restates it (constraint 11), so this is the
    # only place the two halves are allowed to meet.
    blocked: dict[str, list[str]] = {}
    for route_id, route in (search or {"routes": {}})["routes"].items():
        if isinstance(route.get("blocker"), str):
            blocked.setdefault(route["blocker"], []).append(route_id)
    for nid, claim in claims.items():
        claim["blocks_routes"] = sorted(blocked.get(nid, []))
        claim["checkpoints"] = sorted(record["path"] for record in memory["checkpoints"]
                                      if nid in record["nodes"])
    for candidate in memory["candidates"]:
        candidate["blocks_routes"] = sorted(blocked.get(candidate["id"], []))

    documents = _documents(root, claims, pdf_dir, html_dir)

    return {
        "generated": provenance(root, repository),
        "program": {
            "id": program["program"] if program else None,
            "scope": ((program["meta"] or {}).get("scope") or "").strip() or None
            if program else None,
            "target": target,
            "brief": "research/program/brief.md" if brief is not None else None,
            # A fresh clone is correct and not ready. The site says which it is looking at
            # rather than refusing to build, because refusing would make a correct
            # template's first deploy red.
            "instantiated": bool(claims) and bool(target),
        },
        "claims": claims,
        "search": search,
        "memory": memory,
        "documents": documents,
        "vocabulary": {
            "relations": [{"field": field, "class": relation_class,
                           "label": label, "gloss": gloss}
                          for field, relation_class, label, gloss in RELATIONS],
            "reverse": {field: {"field": name, "label": label}
                        for field, (name, label) in REVERSE.items()},
        },
        "layout": {"claims": layout_claims(claims), "search": layout_search(search)},
    }


def _dossier_artifacts(claims: dict[str, dict]) -> list[str]:
    """Every dossier an active proof record names — the same set ``check.py dossiers``
    hands the LaTeX build, so the site attaches exactly what was compiled."""
    found: list[str] = []
    for claim in claims.values():
        for proof in claim["proofs"]:
            artifact = proof.get("artifact")
            if isinstance(artifact, str) and artifact not in found:
                found.append(artifact)
    return sorted(found)


def _documents(root: Path, claims: dict[str, dict], pdf_dir: Path | None,
               html_dir: Path | None) -> dict:
    """Locate the compiled manuscript and dossiers. Absent is a normal answer.

    Both forms are optional and independent. A site with neither still says everything
    it knows and links the LaTeX source; it simply cannot offer a rendered statement.
    Silently omitting mathematics is the failure to avoid, so a missing document is a
    missing *link*, never a missing claim.
    """
    def resolve(directory: Path | None, suffix: str) -> tuple[Path | None, dict[str, Path]]:
        if directory is None:
            return None, {}
        base = directory if directory.is_absolute() else root / directory
        manuscript = base / f"main.{suffix}"
        found = {}
        for artifact in _dossier_artifacts(claims):
            candidate = base / f"{Path(artifact).stem}.{suffix}"
            if candidate.is_file():
                found[artifact] = candidate
        return (manuscript if manuscript.is_file() else None), found

    pdf_manuscript, pdf_dossiers = resolve(pdf_dir, "pdf")
    html_manuscript, html_dossiers = resolve(html_dir, "html")
    return {
        "pdf": {"manuscript": pdf_manuscript, "dossiers": pdf_dossiers},
        "html": {"manuscript": html_manuscript, "dossiers": html_dossiers},
    }


def _attach(documents: dict, out: Path, form: str, extra_suffixes: tuple[str, ...] = ()
            ) -> dict:
    """Copy one form of compiled document into the site and hand back its URLs."""
    found = documents[form]
    directory = out / form
    # Clear first. A rebuild that only ever adds would keep the PDF of a dossier the
    # ledger has since dropped — unlinked, but present, and published.
    shutil.rmtree(directory, ignore_errors=True)
    if found["manuscript"] is None and not found["dossiers"]:
        return {"manuscript": None, "dossiers": {}}
    directory.mkdir(exist_ok=True)
    attached: dict = {"manuscript": None, "dossiers": {}}

    def copy(path: Path) -> str:
        shutil.copyfile(path, directory / path.name)
        # A TeX4ht conversion emits its stylesheet beside the page; without it the
        # manuscript renders as unstyled runs of text rather than as mathematics.
        for suffix in extra_suffixes:
            sidecar = path.with_suffix(suffix)
            if sidecar.is_file():
                shutil.copyfile(sidecar, directory / sidecar.name)
        return f"{form}/{path.name}"

    if found["manuscript"] is not None:
        attached["manuscript"] = copy(found["manuscript"])
    for artifact, path in sorted(found["dossiers"].items()):
        attached["dossiers"][artifact] = copy(path)
    return attached


def build(root: Path, out: Path, *, repository: str | None = None,
          pdf_dir: Path | None = None, html_dir: Path | None = None,
          frontend: Path | None = None) -> tuple[dict, list[str]]:
    """Validate, export, and write the site. Returns the data and any blocking errors.

    A non-empty error list means nothing was written: a structurally invalid revision is
    not this repository's research state, and deploying it as though it were would make
    every trust signal on the page a guess.
    """
    report = analyze(root=root, configured_ledger=LEDGER_PATH)
    errors = failures(report, LANES)
    if errors:
        return {}, errors

    data = export(report, root, repository=repository, pdf_dir=pdf_dir, html_dir=html_dir)
    documents = data.pop("documents")

    out.mkdir(parents=True, exist_ok=True)
    source = frontend if frontend is not None else Path(__file__).resolve().parent.parent / FRONTEND
    for asset in sorted(source.iterdir()):
        if asset.is_file() and asset.suffix in {".html", ".css", ".js"}:
            shutil.copyfile(asset, out / asset.name)

    data["documents"] = {
        "pdf": _attach(documents, out, "pdf"),
        "html": _attach(documents, out, "html", extra_suffixes=(".css",)),
    }

    (out / "data.json").write_text(
        json.dumps(data, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return data, []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render the repository's derived views as a static website",
        epilog="The site is a derived view, never a source. It refuses to build a "
               "repository that does not validate.",
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1],
                        help="repository to publish (default: this script's own)")
    parser.add_argument("--out", type=Path, default=None,
                        help=f"output directory (default: <root>/{DEFAULT_OUT})")
    parser.add_argument("--pdf-dir", type=Path, default=None,
                        help="a LaTeX output directory whose PDFs should be attached, "
                             "e.g. 'build' after latexmk")
    parser.add_argument("--html-dir", type=Path, default=None,
                        help="a directory of make4ht output to attach, so a statement "
                             "can be read as HTML at its own anchor; see site/tex4ht.cfg")
    parser.add_argument("--repository", default=None,
                        help="owner/name for source and contribution links "
                             "(default: inferred from the 'origin' remote)")
    parser.add_argument("--serve", nargs="?", type=int, const=8000, default=None,
                        metavar="PORT", help="after building, serve the site locally")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    out = (args.out if args.out is not None else root / DEFAULT_OUT).resolve()
    data, errors = build(root, out, repository=args.repository, pdf_dir=args.pdf_dir,
                         html_dir=args.html_dir)
    if errors:
        for error in errors:
            print("FAIL", error, file=sys.stderr)
        print(f"\n{len(errors)} error(s): refusing to publish a revision that does not "
              "validate.\nFix them, or run 'python3 scripts/check.py' to see them in "
              "context.", file=sys.stderr)
        return 1

    generated = data["generated"]
    revision = generated["short_commit"] or "unknown revision"
    print(f"wrote {out}{' (working tree is dirty)' if generated['dirty'] else ''}")
    print(f"  {len(data['claims'])} claim(s), "
          f"{len((data['search'] or {'routes': {}})['routes'])} route(s), "
          f"{len(data['memory']['checkpoints'])} checkpoint(s) — at {revision}")
    if not data["program"]["instantiated"]:
        print("  note: this repository is still an uninstantiated template; the site "
              "says so.\n        'python3 scripts/check.py ready' lists what is missing.")

    if args.serve is not None:
        from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
        from functools import partial
        handler = partial(SimpleHTTPRequestHandler, directory=str(out))
        with ThreadingHTTPServer(("127.0.0.1", args.serve), handler) as server:
            print(f"\nserving http://127.0.0.1:{args.serve}/ — Ctrl-C to stop")
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
