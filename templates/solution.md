---
title: "Solution: <short target name>"
ledger-node: {{NODE}}
refines: []
bounded_by: []
author: <agent or name>
date: "{{DATE}}"
exports:
  - format: pdf+tex
    template: ../templates/latex
---

% solutions/{{FILE_ID}}.md — a standalone proof dossier.
%
% The front matter above is the dossier header, and scripts/check.py accepts only these
% fields in it besides the MyST page fields `title`, `subtitle`, `short_title`, `label`,
% `exports` and `numbering`:
%   ledger-node  research/program/ledger.yaml id(s) this discharges — checked
%   refines      statement(s) sharpened
%   bounded_by   proved node(s) fencing the statement
%   author       the agent or person who wrote the proof
%   date         when
% MyST warns that it ignores ledger-node, refines and bounded_by; that is expected.
%
% Certification is NOT recorded here. The ledger's proofs[] record owns the mode and the
% review path, and the review's own front matter owns the identities; a dossier that no
% proofs[] record names is a draft, and that absence is the only thing that says so.
%
% `npx myst build --pdf` compiles this file on its own. Cross-references into modules/
% resolve on the site and print as "??" in the standalone PDF, which is expected.

**Refined statement.** State the sharp current form — not an obsolete loose open form. Cite
the manuscript target it sharpens with `[](#<label>)`, and note which fence shapes it.

:::{prf:theorem} Refined form
:label: thm:sol-{{FILE_ID}}
The precise theorem.
:::

:::{prf:proof}
Natural-language proof. Self-contained: state literature results with a citation and used
manuscript lemmas with a cross-reference. Agent certification requires an independent
reviewer and a persisted report under `research/reviews/`. Numerical diagnostics may
motivate the statement but cannot justify any step of this proof.
:::

**Fences respected.** One line per `bounded_by` node: why this statement form does not
violate it.
