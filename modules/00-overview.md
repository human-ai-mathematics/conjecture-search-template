% modules/00-overview.md — the manuscript's first module.
%
% Every labelled claim directive here — prf:theorem, prf:lemma, prf:proposition,
% prf:corollary, prf:conjecture, prf:definition, prf:example, prf:assumption — is a
% ledger node in research/program/ledger.yaml with a matching `kind`. Other labels
% (headings, equations, remarks) are structural and need no node.
%
% This file ships with orientation prose and no claims. A worked module holding a fence,
% an open conjecture and a proved proposition is example/modules/00-overview.md.

(sec:overview)=
# Orientation

+++ {"part": "abstract"}

Replace this abstract. Say what this document maps, what is established here, and what
remains open. Keep it honest about status: the ledger is the source of truth, and
`python3 scripts/check.py status` prints the live frontier.

+++

Replace this section. State what this document studies, which question it is organized
around, and which conventions everything else rests on.

A convention this program fixes — a sign, a scaling, a log base, which constant absorbs
what — is stated in a `prf:definition` directive under its own `:label:` and carries a
ledger node with `kind: definition` and `status: defined`. Claims resting on it name it in
`depends_on`, so changing it is a mathematical edit the checker can see. There is no
separate notation or normalization file: a second list would be a copy of the dependency
graph that nothing keeps honest.

An obstruction is a fence, read *before* a proof is attempted or a numerical run is spent
(`CLAUDE.md` constraint 5). It is not a kind of node: it is an ordinary claim in the
directive matching its form, and other nodes cite it — in `bounded_by` once it is proved,
so a statement violating it is wrong by construction, or in `heuristic_barriers` while it
is open. It lives here, rather than in a registry of its own, because a fence is only
useful next to the mathematics it fences. State both halves: what it rules out, and what
it leaves open.
