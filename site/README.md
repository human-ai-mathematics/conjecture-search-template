# site/ — the human-facing half

The frontend of the published website. Four files, and a rule that explains all of them:

> The site is a derived view of the repository, never another source of mathematical or
> search state.

| file | what it is |
|---|---|
| [`index.html`](index.html) | the shell: masthead, nav, colophon. No mathematics. |
| [`site.css`](site.css) | presentation. Colour never carries meaning alone. |
| [`site.js`](site.js) | the router, the two maps, and every view. Knows no mathematics. |
| [`tex4ht.cfg`](tex4ht.cfg) | what preserves the anchor invariant through LaTeX → HTML. |

Nothing substantive is written here. Everything a reader sees — statements, statuses,
routes, blockers, checkpoints, certifications — arrives at load time in `data.json`,
which [`../scripts/site.py`](../scripts/site.py) derives from the same validated report
[`../scripts/check.py`](../scripts/check.py) prints from. A gloss or a route objective
typed into these files would drift from the ledger and the portfolio the first time
either changed, and the prettier copy would win the argument.
[`../scripts/tests/test_site.py`](../scripts/tests/test_site.py) asserts that no claim
gloss, candidate statement, route objective or node id appears in this directory.

## Build it

```bash
python3 scripts/site.py                        # -> build/site/
python3 scripts/site.py --root example         # the worked example, fully populated
python3 scripts/site.py --serve                # build, then serve it at :8000
```

Output goes under `build/`, which is gitignored: a built site is a build artifact, never
committed state. The full pipeline — PDFs, HTML conversion, deployment — is
[`../docs/PUBLISHING-THE-SITE.md`](../docs/PUBLISHING-THE-SITE.md).

## What it will not do

- **Publish a repository that does not validate.** `site.py` runs every lane of the
  checker first and refuses on any error, writing nothing at all. An invalid revision is
  not this repository's research state.
- **Merge the two maps.** The claim graph and the search portfolio are drawn on separate
  canvases with separate vocabularies. A route is not a theorem, `completed` means a
  route's objective ended rather than that anything was settled, and `saturated` is a
  judgment about effort.
- **Flatten certification.** `mode: agent` shows the persisted review, its reviewer and
  its distinct authors; `mode: human` shows a name and says plainly that it carries no
  report on disk. They are not drawn as equal evidence.
- **Dress a candidate as a claim.** A candidate is labelled as one, has no status, and
  carries the note that unlike a node's gloss its text is canonical.
- **Let a contribution change anything by itself.** Every action link opens a public
  inbox. Triage is [`../docs/PUBLISHING-THE-SITE.md`](../docs/PUBLISHING-THE-SITE.md),
  and the boundary is [`../CLAUDE.md`](../CLAUDE.md) constraint 12.

## Dependencies

None at build time beyond the checker's own PyYAML. The graph layouts are computed in
Python and drawn as plain SVG — a research program's claim graph has tens of nodes, not
thousands, and a deterministic layout is diffable, works offline, and cannot silently
fail to load.

The one thing loaded from a network is MathJax, and only to typeset the LaTeX `$...$` in
glosses and candidate statements. It is deliberately optional: the raw source is placed
in the DOM first and typeset afterwards, so a blocked or missing CDN leaves the
mathematics visible and readable rather than blank.

## Editing it

Change presentation freely. Before adding a *field* to a view, check that
`scripts/site.py` already exports it — if it does not, the addition belongs there, in
the derivation, not here in a hand-written string.
