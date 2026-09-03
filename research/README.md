# Research control plane

`research/` coordinates this repository's search. The manuscript owns accepted statements, the
ledger owns logical state and graph edges, the portfolio owns what the search is currently
doing, `solutions/` owns standalone proofs, and numerical runs guide research without
certifying claims.

Nothing here is executable: the validator lives in [`../scripts/`](../scripts/). This directory
is what people and agents write *about* the mathematics.

## Program

| program | entry point | purpose |
|---|---|---|
| *(this repository's program)* | [`program/brief.md`](program/brief.md) | which node is the target, what counts as done, and the known traps |

There is one ledger, at `program/ledger.yaml`. All ledger writes pass through one orchestrator
(`CLAUDE.md` constraint 1). There is one portfolio, at `program/portfolio.yaml`, written only
by the `synthesizer` (constraint 12).

## Sources of truth

| content | location |
|---|---|
| accepted mathematical prose, the canonical quantified target included | [`../modules/`](../modules/) |
| a worked instance of every genre below, as a fixture to copy | [`../example/`](../example/README.md) |
| what finishing means, the exact negation, and the known traps | [`program/brief.md`](program/brief.md) |
| ledger fields and invariants | [`program/ledger-schema.md`](program/ledger-schema.md) |
| portfolio and brief fields | [`program/portfolio-schema.md`](program/portfolio-schema.md) |
| claim state and logical edges | `program/ledger.yaml` |
| which routes are alive, blocked, or saturated | `program/portfolio.yaml` |
| hard/advisory proof barriers | proved/open obstruction nodes via `bounded_by`/`heuristic_barriers` |
| proof dossiers | [`../solutions/`](../solutions/) |
| shared adversarial instances | [`instances.md`](instances.md) |
| durable search memory and dead ends | [`explorations/`](explorations/) |
| candidate statements not yet ledger nodes | `candidates:` front matter in [`explorations/`](explorations/) |
| independent reviews | [`reviews/`](reviews/) |
| numerical artifacts | [`runs/`](runs/) |
| harness decisions | [`../decisions/`](../decisions/) |

The ledger separates proof dependencies (`depends_on`), implication antecedents/conclusions
(`assumes`/`implies`), and hard/advisory barriers (`bounded_by`/`heuristic_barriers`). The
portfolio holds none of those: a route is not a claim.

## Contribution flow

1. Read the brief, then select a ledger node or a portfolio approach and read its manuscript
   statement, dependencies, obstructions, and prior checkpoints.
2. Do the work. Put numerical work through `numerics`.
3. Record a checkpoint when the result is durable, with its validated front matter. A tentative
   statement stays there as a `cand:` candidate until it is precise, stable, and worth tracking
   (`CLAUDE.md` constraint 8). Promoting one is a single act: manuscript `\label`, ledger node,
   `promotes:` in a checkpoint, and any portfolio blocker repointed at the node.
4. Return a `portfolio_delta` in the handoff; the `synthesizer` applies it.
5. Send accepted statement and ledger changes through the orchestrator.
6. For a proof, supply a standalone dossier and independent review.
7. Run the structural checker.

## Verify

```bash
python3 scripts/check.py
python3 scripts/check.py ready
python3 scripts/check.py status
python3 scripts/check.py portfolio
python3 scripts/check.py checkpoints
python3 scripts/check.py node <id>
python3 scripts/check.py candidates
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
```

The checker validates repository structure, not mathematical correctness. The contribution
rules are in [`../CLAUDE.md`](../CLAUDE.md).
