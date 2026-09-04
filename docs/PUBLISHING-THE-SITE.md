# Publishing the search

How the repository's state becomes a website mathematicians can read, and how their
questions, criticism and proofs come back in. [`../CLAUDE.md`](../CLAUDE.md) is the
contract and wins on any conflict; this is how it is used.

The site is **optional**. A repository that never publishes one is complete, and nothing
in `scripts/check.py` mentions it. What it buys is a reader who will never open
`ledger.yaml`: the target, what is established and at what certification level, what is
genuinely open, which mechanisms have been tried, and why each route stopped.

The rule everything follows from:

> The site is a derived view of the repository, never another source of mathematical or
> search state.

---

## 1. Build it

```bash
python3 scripts/site.py                  # -> build/site/
python3 scripts/site.py --serve          # build, then serve it at http://127.0.0.1:8000
python3 scripts/site.py --root example   # the worked example, fully populated
```

`build/` is gitignored. The site is an artifact of the tree, reproducible from any
checkout and committed nowhere.

**It refuses to publish a revision that does not validate.** Every lane of the checker
runs first, and on any error nothing is written at all — not even a shell. A structurally
invalid revision is not this repository's research state, and deploying one as though it
were would make every trust signal on the page a guess.

It does **not** refuse an uninstantiated template. A fresh clone is correctly green and
correctly not ready; the front page says so and the build succeeds. Refusing there would
make a correct repository's first deploy red.

## 2. Attach the documents

Two optional additions, and the site degrades honestly without either — a missing
document is a missing *link*, never a missing claim.

```bash
ROOT="$PWD"

latexmk -pdf -outdir=build main.tex
python3 scripts/check.py dossiers | while read -r d; do
  latexmk -pdf -cd -outdir="$ROOT/build" "$d"
done

mkdir -p build/html
make4ht -u -c site/tex4ht.cfg -d build/html main.tex "mathjax"
python3 scripts/check.py dossiers | while read -r d; do
  (cd "$(dirname "$d")" \
    && make4ht -u -c "$ROOT/site/tex4ht.cfg" -d "$ROOT/build/html" \
         "$(basename "$d")" "mathjax")
done

python3 scripts/site.py --pdf-dir build --html-dir build/html
```

`make4ht` has to run from the dossier's own directory — a `subfiles` document resolves
its master relatively — which is why that loop is a subshell and every path in it is
absolute.

`check.py dossiers` is machine-readable for exactly this: it lists the dossiers an active
`proofs[]` record names, so the site attaches what the ledger actually vouches for.

### Why the HTML build needs a config file

[`../site/tex4ht.cfg`](../site/tex4ht.cfg) exists for one reason, and it is not
cosmetic. A default TeX4ht conversion emits generated anchors — `x1-5001r3`, `QQ2-1-5` —
and drops the `\label` names, so `main.html#conj:example` lands nowhere and the site
would have to invent a second, web-specific id scheme for every claim. That is precisely
the identifier the anchor invariant exists to avoid.

The config redefines `\label` so it also plants an HTML anchor of the same name. The
LaTeX label keeps working and the PDF build is untouched — TeX4ht reads this file, and
nothing else does. Verified on this repository's manuscript and on both worked-example
dossiers: ids survive verbatim, colons included; `amsthm` environments keep their names
and numbering; and mathematics comes out as `\(...\)` for MathJax.

The same redefinition placed in `preamble.tex` silently does nothing — `\HCode` is not
defined when the preamble is read, so the build stays green and the anchors stay
missing, which is the worst of both.

## 3. Deploy it

[`../.github/workflows/pages.yml`](../.github/workflows/pages.yml) validates and builds on
every push and pull request. It deploys only from the repository's configured default branch,
so a fork using `main`, `master`, or another name needs no workflow edit.

Before the first run, a human has to enable Pages: **Settings → Pages → Build and
deployment → Source: GitHub Actions**. Nothing in the workflow can do that, and until it
is done the deploy step fails with a 404.

A failed build leaves the previous site online while the repository moves on. That is why
every page carries its source commit and build time, and why the correction form asks for
the commit in the footer: it is how a stale deployment is told apart from a real error.

---

## 4. Contributions come back through an inbox

The site's action links open GitHub issue forms in
[`../.github/ISSUE_TEMPLATE/`](../.github/ISSUE_TEMPLATE/), each prefilled with the
stable id of whatever was on screen:

| form | for |
|---|---|
| `proof-gap.yml` | a step believed unjustified in a certified proof |
| `counterexample.yml` | an instance or family believed to refute a claim |
| `literature-lead.yml` | existing work that settles, weakens or bounds something here |
| `route-proposal.yml` | a mechanism worth trying, or a way past a blocked route |
| `correction.yml` | a link, gloss or status on the site that is wrong or stale |

Conversation goes to Discussions; issues are for things that are actionable.

The boundary is [`../CLAUDE.md`](../CLAUDE.md) constraint 12 and it is not negotiable:

> A suggestion, vote, comment, or uploaded proof does not become a candidate, a route, a
> ledger node, a proof record, or a status transition.

Nothing outside the repository is citable state. A `blocker:` may not name an issue, a
ledger node may not cite a discussion, and no count of anything — comments, votes,
reactions, contributors — moves a status. Popularity is not truth, and a form is not a
promotion.

### Triage

Every incoming item leaves the inbox in exactly one of six ways. The point of the list
is that each destination already exists: nothing new is invented to hold a contribution.

| what arrived | where it goes | who |
|---|---|---|
| a reusable finding, a dead end, an exact blocker | a dated checkpoint in `research/explorations/` | whoever works it |
| a tentative statement worth not losing | a `cand:` in that checkpoint's front matter | same |
| an approach worth running | a `portfolio_delta` in the handoff | applied by the `synthesizer` |
| a reference worth importing | a `provenance: literature` node, with `import_class` | orchestrator |
| a proof or refutation | a standalone dossier and independent certification | `solutions/README.md` |
| nothing durable | answered in the thread, and closed | any maintainer |

The last row is a real outcome and the most common one. A contribution that leaves no
repository artifact is not a failure; recording everything is how a log stops being read.

A proof arriving from outside takes the ordinary channel and skips no step. If a person
supplies the argument, the honest record is a `proofs[]` entry with `mode: human` and
`accepted_by` naming them — which the site displays as an attestation carrying no
persisted review, because that is what it is. If an agent certifies it instead, that is
`mode: agent` with a report under `research/reviews/`, written by someone who is not an
author.

### What this costs

Opening a search to the public creates triage, moderation, attribution and response
expectations that do not go away. Enable Discussions when someone is willing to hold
them, not before — an unanswered inbox is worse than a closed one, and turning it on is
easier than turning it off.

---

## Instantiating this in a fork

One file names this repository by URL and has to be repointed:
`.github/ISSUE_TEMPLATE/config.yml`, whose Discussions and site links are absolute.

Everything else follows a fork on its own. The site derives its repository slug from the
`origin` remote, so contribution links, source permalinks and commit links repoint
themselves; `--repository owner/name` overrides that when the remote is not the published
home.

## Verify

```bash
python3 scripts/site.py --root example --serve    # the fully populated worked example
python3 -m unittest discover -s scripts/tests -p 'test_site.py'
node --check site/site.js                         # a syntax error here is a blank page
```
