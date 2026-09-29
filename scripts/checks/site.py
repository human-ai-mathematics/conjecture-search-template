"""The reader's site: the pages under ``site/``, and whether they still tell the truth.

A page is exposition, free in form, and owns no statement. What it may not do is misstate
a status. So a page that states one records, for each statement it rests on, the status and
the fingerprint it was written against (``relies-on``), and the day it was last checked
(``checked``); a problem card also names its ``problem``. ``check.py --stamp`` writes those
fields and a generated block that shows them, never a person. It also writes the two lists
no person should keep: the problem cards on ``site/open.md`` and the certified dossiers on
``site/proofs.md``.

A page whose record no longer matches the ledger, the manuscript or the checkpoints, or
whose list no longer matches the cards or the dossiers, is *stale*; a page still carrying a
template placeholder is *unfinished*. Both are warnings while the research goes on, and
errors under ``--site-strict``, which is how the site is published. The check covers what
a page declares, never whether its prose is faithful: that stays a reader's job.
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import yaml

from .common import as_list, repo_relative, text_fingerprint

SITE = "site"
PROBLEMS = "site/open"
OPEN_INDEX = "site/open.md"
PROOFS_INDEX = "site/proofs.md"
CONFIG = "myst.yml"
ENTRY_FIELDS = {"status", "fingerprint"}
BEGIN = "% stamp: written by check.py --stamp; do not edit"
END = "% end stamp"
LIST_BEGIN = "% list: written by check.py --stamp; do not edit"
LIST_END = "% end list"

#: What a template leaves for its user to replace: an ``<angle-bracketed hint>`` or a
#: "Replace this" instruction. Math, comments, autolinks and HTML tags are not placeholders.
PLACEHOLDER = re.compile(r"<([^<>\n]+)>")
REPLACE = re.compile(r"\breplace this\b", re.IGNORECASE)
MATH = re.compile(r"\$\$.*?\$\$|\$[^$]*\$|<!--.*?-->", re.DOTALL)
NOT_PLACEHOLDER = re.compile(
    r"^(\w+://\S+|[^\s@]+@[^\s@]+|/?(a|abbr|b|br|cite|code|details|div|em|figcaption|figure|"
    r"hr|i|iframe|img|kbd|li|ol|p|pre|small|span|strong|sub|summary|sup|table|td|th|tr|u|"
    r"ul|video)(\s[^<>]*)?/?)$", re.IGNORECASE)
SHOWN = {"open": "open", "live": "open", "proved": "solved", "refuted": "answered (no)",
         "defined": "definition", "closed": "withdrawn"}


class _Entry(dict):
    """A ``relies-on`` entry, written on one line."""


class _Dumper(yaml.SafeDumper):
    pass


_Dumper.add_representer(_Entry, lambda dumper, data: dumper.represent_mapping(
    "tag:yaml.org,2002:map", data, flow_style=True))


def pages(root: Path) -> list[Path]:
    return sorted((root / SITE).rglob("*.md"))


def current(nodes: dict[str, dict], labels: dict[str, dict] | None,
            proposed: dict[str, dict]) -> dict[str, dict]:
    """Every id a page may rest on, with its status and statement fingerprint as they stand
    now. Without the manuscript (``labels is None``) a node has no fingerprint to compare."""
    result: dict[str, dict] = {}
    for nid, node in nodes.items():
        entry = {"status": node.get("status")}
        digest = (labels or {}).get(nid, {}).get("fingerprint")
        if digest is not None:
            entry["fingerprint"] = digest
        result[nid] = entry
    for cid, candidate in proposed.items():
        result[cid] = {"status": "closed" if candidate["closed"] else "live",
                       "fingerprint": text_fingerprint(candidate["statement"])}
    return result


def _split(text: str) -> tuple[list[str], list[str]] | None:
    """A page's front matter lines and body lines, or ``None`` without front matter."""
    lines = text.splitlines()
    closing = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), None)
    if not lines or lines[0].strip() != "---" or closing is None:
        return None
    return lines[1:closing], lines[closing + 1:]


def _read(path: Path, context: str, errors: list[str]) -> tuple[dict, list[str]] | None:
    """A page's front matter, validated for shape, and its body lines."""
    try:
        parts = _split(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as exc:
        errors.append(f"{context}: cannot read page: {exc}")
        return None
    if parts is None:
        errors.append(f"{context}: a site page must start with a '---' front matter block")
        return None
    try:
        raw = yaml.safe_load("\n".join(parts[0])) or {}
    except yaml.YAMLError as exc:
        errors.append(f"{context}: invalid front matter: {exc}")
        return None
    if not isinstance(raw, dict):
        errors.append(f"{context}: front matter must be a mapping")
        return None
    relies = raw.get("relies-on")
    if relies is not None and not (
            isinstance(relies, dict) and all(isinstance(k, str) for k in relies)
            or isinstance(relies, list) and all(isinstance(k, str) for k in relies)):
        errors.append(f"{context}.relies-on: want a list of ids, or the mapping --stamp writes")
        return None
    if isinstance(relies, dict):
        for rid, entry in relies.items():
            if not isinstance(entry, dict) or set(entry) - ENTRY_FIELDS:
                errors.append(f"{context}.relies-on {rid}: want {{status, fingerprint}}")
                return None
    problem = raw.get("problem")
    if context.startswith(f"{PROBLEMS}/") and not isinstance(problem, str):
        errors.append(f"{context}.problem: a problem card names the id it presents")
        return None
    if problem is not None and problem not in (relies or []):
        errors.append(f"{context}.problem: '{problem}' must also be in relies-on")
        return None
    return raw, parts[1]


def _checked(raw: dict) -> date | None:
    value = raw.get("checked")
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def block(raw: dict) -> list[str] | None:
    """The generated lines a stamped page shows under its title; ``None`` for a page that
    rests on nothing, which has no status to show."""
    if not raw.get("relies-on"):
        return None
    checked = _checked(raw)
    line = f"*Last checked against the research record: {checked.isoformat()}.*"
    problem = raw.get("problem")
    if problem is not None:
        status = (raw.get("relies-on") or {}).get(problem, {}).get("status")
        line = f"**Status: {SHOWN.get(status, status)}.** " + line
    return [BEGIN, line, END]


def _body(lines: list[str], begin: str = BEGIN,
          end: str = END) -> tuple[list[str] | None, list[str]]:
    """The generated block between ``begin`` and ``end`` a body carries, if any, and the
    body without it."""
    try:
        first = lines.index(begin)
        last = lines.index(end, first)
    except ValueError:
        return None, lines
    return lines[first:last + 1], lines[:first] + lines[last + 1:]


def _number(title: str) -> tuple[int, str]:
    found = re.match(r"Problem (\d+)\b", title)
    return (int(found.group(1)) if found else 1 << 30, title)


def lists(root: Path, now: dict[str, dict], certified: list[str]) -> dict[str, list[str]]:
    """The generated list each index page shows: every problem card with the current status
    of its problem on ``site/open.md``, every certified dossier on ``site/proofs.md``.
    Draft dossiers are never listed: they are not published."""
    cards = []
    for path in sorted((root / PROBLEMS).glob("*.md")):
        parts = _split(path.read_text(encoding="utf-8")) if path.is_file() else None
        try:
            raw = yaml.safe_load("\n".join(parts[0])) if parts else None
        except yaml.YAMLError:
            raw = None
        if not isinstance(raw, dict):
            continue  # reported on the card itself
        title = str(raw.get("title") or path.stem)
        status = now.get(raw.get("problem"), {}).get("status")
        cards.append((_number(title), f"- [{title}](open/{path.name}) — "
                                      f"{SHOWN.get(status, status)}."))
    dossiers = []
    for reference in certified:
        path = root / reference
        parts = _split(path.read_text(encoding="utf-8")) if path.is_file() else None
        try:
            raw = yaml.safe_load("\n".join(parts[0])) if parts else None
        except yaml.YAMLError:
            raw = None
        raw = raw if isinstance(raw, dict) else {}
        nodes = [nid for nid in as_list(raw.get("ledger-node")) if nid in now]
        about = f", for {', '.join(f'[](#{nid})' for nid in nodes)}" if nodes else ""
        dossiers.append(f"- [{raw.get('title') or path.stem}](../{reference}){about}.")
    return {
        OPEN_INDEX: [line for _, line in sorted(cards)]
        or ["*No problem is published yet.*"],
        PROOFS_INDEX: dossiers or ["*No proof is published yet.*"],
    }


def _listed(context: str, expected: dict[str, list[str]]) -> list[str] | None:
    lines = expected.get(context)
    return None if lines is None else [LIST_BEGIN, *lines, LIST_END]


def unfinished(text: str, comment: str = "%") -> list[tuple[int, str]]:
    """Every template placeholder left in ``text``, with its line number. Lines starting
    with ``comment`` are skipped, and so are math and HTML comments."""
    text = MATH.sub(lambda found: "\n" * found.group().count("\n"), text)
    found: list[tuple[int, str]] = []
    for number, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith(comment):
            continue
        for marker in PLACEHOLDER.finditer(line):
            if not NOT_PLACEHOLDER.match(marker.group(1).strip()):
                found.append((number, marker.group()))
        found += [(number, marker.group()) for marker in REPLACE.finditer(line)]
    return found


def _unfinished(path: Path, context: str, comment: str, warnings: list[str]) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return  # reported where the file is read
    for number, marker in unfinished(text, comment):
        warnings.append(f"{context}:{number}: unfinished: '{marker}' is left from a "
                        "template; replace it")


def check(root: Path, now: dict[str, dict], certified: list[str], errors: list[str],
          warnings: list[str]) -> tuple[int, set[str]]:
    """Warn about every stale or unfinished page; return how many pages there are, and
    every id some page rests on. ``certified`` lists the dossiers a proof record names."""
    found = pages(root)
    mentioned: set[str] = set()
    expected = lists(root, now, certified) if found else {}
    if found and (root / CONFIG).is_file():
        _unfinished(root / CONFIG, CONFIG, "#", warnings)
    for path in found:
        context = repo_relative(root, path)
        _unfinished(path, context, "%", warnings)
        page = _read(path, context, errors)
        if page is None:
            continue
        raw, body = page
        stale: list[str] = []
        relies = raw.get("relies-on") or {}
        mentioned.update(relies)
        if isinstance(relies, list):
            stale.append("relies-on lists ids but was never stamped")
            relies = {}
        elif relies and _checked(raw) is None:
            stale.append("no 'checked' date")
        for rid, recorded in relies.items():
            if rid not in now:
                stale.append(f"'{rid}' no longer exists")
                continue
            status = now[rid]["status"]
            if recorded.get("status") != status:
                stale.append(f"'{rid}' is now {status}, the page says {recorded.get('status')}")
            digest = now[rid].get("fingerprint")
            if digest is not None and recorded.get("fingerprint") != digest:
                stale.append(f"the statement of '{rid}' changed")
        if not stale:
            shown, _ = _body(body)
            if shown != block(raw):
                stale.append("its stamp block is missing, out of date or edited by hand")
        listed = _listed(context, expected)
        if listed is not None and _body(body, LIST_BEGIN, LIST_END)[0] != listed:
            stale.append("its list is missing, out of date or edited by hand")
        for reason in stale:
            warnings.append(f"{context}: stale: {reason}; reread it, then run "
                            f"'check.py --stamp {context}'")
    return len(found), mentioned


def unmentioned(nodes: dict[str, dict], mentioned: set[str]) -> list[str]:
    """The settled nodes no page rests on: a result or a refutation the site may be
    missing. Not every lemma deserves a page, so this is a reminder, never a warning."""
    return sorted(nid for nid, node in nodes.items()
                  if node.get("status") in {"proved", "refuted"} and nid not in mentioned)


def stamp(root: Path, references: list[str], now: dict[str, dict], certified: list[str],
          today: date, errors: list[str]) -> list[str]:
    """Record the current status and fingerprint of what each page rests on, date it
    ``today`` and rewrite its block; on an index page, rewrite its list too. Only those
    fields change: a page that rests on nothing loses its date and block. Returns the pages
    written."""
    written: list[str] = []
    expected = lists(root, now, certified)
    for reference in references:
        path = (root / reference).resolve()
        if not path.is_file() or not path.is_relative_to((root / SITE).resolve()):
            errors.append(f"{reference}: not a page under {SITE}/")
            continue
        context = repo_relative(root, path)
        page = _read(path, context, errors)
        if page is None:
            continue
        raw, body = page
        ids = list(raw.get("relies-on") or [])
        unknown = [rid for rid in ids if rid not in now]
        if unknown:
            errors.append(f"{context}: relies on unknown id(s) {', '.join(unknown)}; "
                          "not stamped")
            continue
        header = dict(raw)
        header.pop("checked", None)
        if ids:
            header["relies-on"] = {rid: _Entry(now[rid]) for rid in ids}
            header["checked"] = today
        else:
            header.pop("relies-on", None)
        _, rest = _body(body)
        listed = _listed(context, expected)
        if listed is not None:
            shown, without = _body(rest, LIST_BEGIN, LIST_END)
            if shown is None:
                while rest and not rest[-1].strip():
                    rest.pop()
                rest = [*rest, "", *listed]
            else:
                at = rest.index(LIST_BEGIN)
                rest = without[:at] + listed + without[at:]
        while rest and not rest[0].strip():
            rest.pop(0)
        shown = block(header)
        text = ("---\n"
                + yaml.dump(header, Dumper=_Dumper, sort_keys=False, allow_unicode=True,
                            default_flow_style=False, width=100)
                + "---\n\n" + ("\n".join(shown) + "\n\n" if shown else "")
                + "\n".join(rest) + "\n")
        path.write_text(text, encoding="utf-8")
        written.append(context)
    return written

