---
title: <The question, as a reader would ask it>
numbering: false
relies-on: [conj:main]
---

% Copy to site/index.md: the landing page of the reader's site. Written for a
% mathematician who has never seen this repository: no ledger ids in the prose, no harness
% vocabulary (route, checkpoint, candidate). List in relies-on every id whose status this
% page states, reread the page against those statements, then run
% `uv run scripts/check.py --stamp site/index.md`, which writes the status block. See
% SPECIFICATION.md, Formats → Site page.

<The problem in one paragraph and one displayed formula.>

$$
<the inequality, identity or bound in question>
$$

**Where things stand.** <Three sentences: what is proved, what is refuted, what is open.>

## Where you can help

% One card per published problem card under site/open/. Drop the section while there is
% none.
::::{grid} 1 1 2 2

:::{card} Problem 1 — <a title that says what is asked>
:link: open/<slug>.md
<One or two sentences, without notation.>
:::

::::

## Read further

- [The problem](problem.md): <what the reader finds there>.
- [Results](results.md): <what is proved, each with the idea of its proof>.
- [About](about.md): how to contribute, and how results are checked.
