% modules/{{SLUG}}.md — a manuscript module.
%
% Every labelled claim directive here is exactly one ledger node whose `kind` is the
% directive's name: prf:theorem, prf:lemma, prf:proposition, prf:corollary,
% prf:conjecture, prf:definition, prf:example or prf:assumption. A heading, an equation
% or a prf:remark label is structural and is not a node. myst.yml picks this file up by
% its path, so nothing else has to list it.
%
% A worked module holding a fence, an open conjecture, a proved proposition and a
% refuted conjecture is example/modules/00-overview.md.

(sec:{{SLUG}})=
# {{TITLE}}

Orientation prose. What this module studies and which conventions everything in it rests
on. A fixed normalization — a sign, a scaling, a log base, which constant absorbs what — is
not prose: state it in a `prf:definition` directive under its own `:label:` and give it a
ledger node with `kind: definition` and `status: defined`, so that changing it is a
mathematical edit the checker can see.

:::{prf:{{KIND}}}
:label: {{NODE}}
The precise quantified statement. This text is canonical: the ledger's `summary` is a
gloss of it, and the problem brief may quote it verbatim as a marked copy, but nothing else
in the repository holds it.
:::
