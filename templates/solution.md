---
title: "Solution: short target name"
ledger-node: conj:main
---

% Copy to solutions/<ledger-id>.md (":" replaced by "-"). The header records no
% certification: the ledger's proofs[] record does. See SPECIFICATION.md, Formats → Proof
% records and dossiers.

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

**Fences respected.** One line per `bounded_by` node: why this statement does not violate it.
