---
title: "Solution: short target name"
ledger-node: conj:main
numbering:
  enumerator: "1.%s"
---

% Copy to solutions/<ledger-id>.md (":" replaced by "-"). The header records no
% certification: the ledger's proofs[] record does. See SPECIFICATION.md, Formats → Proof
% records and dossiers. Set the enumerator prefix to this dossier's place under *Full
% proofs*, so that its statements read Theorem 3.1, Lemma 3.2, … and never collide with
% another page's; fix it before the first review, since an edit afterwards lifts the
% certification until at least an editorial note carries it over.
% Point at the manuscript by label (`[](#thm:x)`) or section anchor (`[](#sec:x)`), never
% by a module's file name or a line number: modules are renumbered, and repairing a stale
% path takes at least an editorial note.

**Overview.** What is proved, and how, before any detail: the steps in order and what each
one contributes.

**Dependencies.** Name the results actually used in this proof. If claiming independence
from another proof, specify which inputs are excluded and justify that exclusion; the
statement-level ledger DAG alone does not establish it.

1. First step: what it establishes.
2. Second step: what it adds, and which earlier step it uses.

**Refined statement.** The sharp current form. Cite the manuscript statement it sharpens
with `[](#<label>)`.

:::{prf:theorem} Refined form
:label: thm:sol-main
The precise theorem.
:::

:::{prf:proof}
Self-contained natural-language proof. Cite literature results and cross-reference manuscript
lemmas. No numerical output may justify any step. Mark each step not closed with a
`prf:remark` naming what remains.
:::

A technical lemma or a routine computation the reader may skip goes in a folded block,
still in full:

:::{prf:lemma} A routine estimate
:label: lem:sol-main-routine
The statement.
:::

:::{prf:proof}
:class: dropdown
The computation, every step written out.
:::

**Fences respected.** One line per `bounded_by` node: why this statement does not violate it.
