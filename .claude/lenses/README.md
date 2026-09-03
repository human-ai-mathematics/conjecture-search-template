# Assignment lenses

A lens is one strategy a role can be pointed at. It is not a role: it has no tools, no write
surface, and no permissions of its own — it inherits all of that from the role that declares
it.

| lens | role | what it does |
|---|---|---|
| [`prove.md`](prove.md) | `researcher` | build a standalone proof dossier |
| [`refute.md`](refute.md) | `researcher` | negate the exact statement and hunt a witness |
| [`mine.md`](mine.md) | `researcher` | extract what an existing proof really buys |
| [`construct.md`](construct.md) | `researcher` | build the object and verify it analytically |
| [`certify.md`](certify.md) | `reviewer` | the gate for `proofs[].mode: agent` |
| [`sync.md`](sync.md) | `reviewer` | manuscript ↔ ledger ↔ dossier ↔ brief agreement |

## Why they are separate files

Every invocation is given one lens. When four strategies live inside one role contract, a
researcher assigned `prove` still reads `refute`, `mine` and `construct` before doing any
mathematics — and the three it did not need are the ones most likely to blur the one it did.
Splitting them keeps the roster small, which is what
[`../agents/README.md`](../agents/README.md) wants, without paying for every strategy on every
run.

**Read exactly the lens you were assigned, and no other.** Reading a second lens is not
thoroughness; it is the shallow-pass failure the `researcher` contract warns about.

## The contract

Each file carries `name` and `role` front matter. `python3 scripts/check.py --lane roles`
checks that `name` matches the filename, that `role` names a real role, that every lens a role
declares exists, and that every lens file is declared by its role. A lens nobody loads and a
lens that does not exist are both errors.

The lens body holds only what is specific to that strategy: its method, and the bullets it
adds to the role's `## Report`. Anything true of every lens on a role belongs in the role
contract instead — permissions, write surface, checkpoint triggers, and the handoff envelope
are all shared and are stated once.

## Both clients

`.claude/agents/*.md` is canonical for Claude, and `.codex/agents/*.toml` is generated from it
for Codex. Lens files are **not** inlined into either: both clients read them from disk at run
time with the tools the role already declares. So a lens edit needs no regeneration, while a
role edit still needs `python3 scripts/check.py --write-codex`.

## Adding one

Write the file, add its row above, and reference it from the role's lens table. Prefer a new
lens to a new role — a lens costs one file and no permissions, and a role costs a contract, an
adapter, a roster row, and a concurrency key.
