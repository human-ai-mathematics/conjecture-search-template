# Obstructions

A fence, not a claim about difficulty. A statement whose shape violates one of
these is wrong by construction, so read the fences a node is `bounded_by` before
proving it or spending a numerical run (`CLAUDE.md` constraint 5).

Every `kind: obstruction` node in [`ledger.yaml`](ledger.yaml) needs a heading
here, and every heading here needs a node — `scripts/check_ledger.py` enforces
the correspondence in both directions. The heading is the node id in backticks.

Record what the obstruction rules out and what escape routes remain open. An
obstruction that only says "this is hard" fences nothing.

## `obs:example`

**Rules out.** Establishing a universal statement from a finite battery of
instances. Agreement across every instance tried says nothing about the untried
ones, so no run discharges a universal claim however large it is.

**Leaves open.** Refutation: one instance suffices to refute a universal
statement, and an exact arithmetic witness for such an instance is a genuine
candidate — though it still requires an independently reviewed refutation dossier
before it carries logical force (`CLAUDE.md` constraint 2).

**Source.** `\label{obs:example}` in `modules/00-overview.tex`.
