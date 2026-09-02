# Research control plane

`research/` coordinates this repository's program. The manuscript owns accepted statements, the
ledger owns logical state and graph edges, `solutions/` owns standalone proofs, and numerical runs
guide research without certifying claims.

Nothing here is executable: the validators live in [`../scripts/`](../scripts/). This directory is
what people and agents write *about* the mathematics.

## Program

| program | entry point | purpose |
|---|---|---|
| *(this repository's program)* | [`program/README.md`](program/README.md) | *(what a contribution here should accomplish)* |

There is one ledger, at `program/ledger.yaml`. All ledger writes pass through one orchestrator
(`CLAUDE.md` constraint 1).

## Sources of truth

| content | location |
|---|---|
| ledger fields and invariants | [`program/ledger-schema.md`](program/ledger-schema.md) |
| accepted mathematical prose | [`../modules/`](../modules/) |
| claim state and logical edges | `program/ledger.yaml` |
| hard/advisory proof barriers | proved/open obstruction nodes via `bounded_by`/`heuristic_barriers` |
| proof dossiers | [`../solutions/`](../solutions/) |
| shared adversarial instances | [`instances.md`](instances.md) |
| mathematical attempts and dead ends | [`explorations/`](explorations/) |
| candidate statements not yet ledger nodes | `candidates:` front matter in [`explorations/`](explorations/) |
| independent reviews | [`reviews/`](reviews/) |
| numerical artifacts | [`runs/`](runs/) |
| harness decisions | [`../decisions/`](../decisions/) |

The ledger separates proof dependencies (`depends_on`), implication antecedents/conclusions
(`assumes`/`implies`), and hard/advisory barriers (`bounded_by`/`heuristic_barriers`).

## Contribution flow

1. Select a ledger node and read its manuscript statement, dependencies, and obstructions.
2. Record the attempt in a new dated exploration, with its validated front matter; put
   numerical work through `numerics`. A tentative statement stays there as a `cand:` candidate
   until it is precise, stable, and worth tracking (`CLAUDE.md` constraint 8).
3. Send accepted statement and ledger changes through the orchestrator.
4. For a proof, supply a standalone dossier and independent review.
5. Run the structural checker.

## Verify

```bash
python3 scripts/check_ledger.py
python3 scripts/check_ledger.py status
python3 scripts/check_ledger.py node <id>
python3 scripts/check_ledger.py candidates
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
```

The checker validates repository structure, not mathematical correctness. The contribution rules
are in [`../CLAUDE.md`](../CLAUDE.md).
