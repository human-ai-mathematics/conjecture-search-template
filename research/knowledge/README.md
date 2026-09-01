# Shared research knowledge

This directory is the current reference for material reused across the program:

- [`lemmas.md`](lemmas.md) records compact mathematical facts and their guardrails.
- [`instances.md`](instances.md) is the canonical calibration and stress-instance registry.

Keep only stable, reusable content here. Claim status and graph structure belong in the ledger;
full statements and proofs belong in the manuscript and `solutions/`; attempts and earlier
formulations belong in `research/explorations/`; numerical results belong in `research/runs/`;
and harness rationale belongs in `research/decisions/`.

Unlike `explorations/` and `decisions/`, this directory is *curated*: entries are rewritten and
removed as understanding improves. The `synthesizer` owns it (`CLAUDE.md` constraint 3).

Obstructions remain in [`../program/obstructions.md`](../program/obstructions.md).
Add an instance to the shared registry only after review of its relevance to the common battery.
Math in Markdown uses LaTeX `$...$`.
