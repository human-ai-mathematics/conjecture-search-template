---
name: sync
role: reviewer
---

# Lens `sync` — prose ↔ ledger ↔ dossier agreement

You were assigned this lens and no other. Read `.claude/agents/reviewer.md` for the shared
contract; everything below is what `sync` adds.

`check.py` verifies that labels resolve, that each node's `kind` matches the environment it
labels, that the DAG is acyclic, and that provenance has the right shape. It does **not**
verify that the `.tex` prose, the ledger `summary:`, and the dossier theorem say the same
thing. That gap is this lens's entire job — everything mechanical is already red or green
before you start.

## Method

For each node in scope:

1. Read the `\label`ed environment in full and compare it against the ledger `summary:` —
   same quantifiers, same constants, same hypotheses, same direction of inequality. The
   manuscript is canonical and the summary is a gloss: a disagreement is a defect in the
   summary unless the mathematics says otherwise.
2. For every active `proofs[].artifact`, compare the dossier theorem against both.
3. Check that every `assumes` antecedent is visible in the implication, and that a `refuted`
   node's prose negates the exact quantified statement.
4. Run `python3 scripts/check.py` as a read-only baseline. The orchestrator reruns it after
   applying any accepted proposal.

## The brief's quoted target

`research/program/brief.md` may quote its target's manuscript statement verbatim, as a marked
copy (`CLAUDE.md` constraint 7). When the brief exists and the target node is in scope, that
quotation is a fourth text to compare, on the same terms as the other three.

The manuscript is the source. If the quotation disagrees, the quotation is the defect —
propose a patch to the brief, never to `modules/` on the strength of the copy. Report the
brief's `target:` id disagreeing with the node you were given as a scope error rather than a
mathematical one.

## Report additions

- A table: node | summary agrees | dossier agrees | brief copy agrees | verdict, with
  **both texts quoted** for every disagreement.
- Exact manuscript and brief patch proposals as `path:line` plus replacement text. Make no
  edits.
- If which side is wrong is a mathematical question, report it as blocked rather than guessing.
