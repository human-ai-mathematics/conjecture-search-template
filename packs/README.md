# packs/ — optional capability packs

Three roles a repository installs when its work calls for them, rather than carrying
whether or not it uses them.

| pack | install when |
|---|---|
| [`numerics`](numerics/numerics.md) | there is something to compute |
| [`literature-scout`](literature-scout/literature-scout.md) | there is external work to import |
| [`janitor`](janitor/janitor.md) | the repository needs tidying |

```bash
python3 scripts/new.py role numerics     # copies it into .claude/agents/, regenerates the adapter
python3 scripts/check.py --lane roles    # confirms the install
```

An installed pack is an ordinary role in every respect — same frontmatter contract, same
runtime contract in [`../.claude/agents/README.md`](../.claude/agents/README.md), same
validation, and a tier every profile in
[`../.claude/agents/profiles.yaml`](../.claude/agents/profiles.yaml) already assigns it.
That is why installing one is a single command: the pack file on disk here is stamped
with the active profile's model and effort before it is ever copied. This file remains canonical
after installation; `python3 scripts/new.py agents` refreshes the installed copy and the checker
rejects drift between them. Uninstalling is deleting the file from `.claude/agents/`; then
`python3 scripts/new.py agents` drops the orphaned adapter.

Nothing here is loaded, generated from, or validated until it is installed. The roster in
[`../.claude/agents/MAINTAINING.md`](../.claude/agents/MAINTAINING.md) links these files
by path, which is why installing one needs no documentation edit.

**The `numerics` pack is the role, not the harness.** `experiments/` stays where it is
whether or not the pack is installed: the numerics lane validates only run artifacts that
exist, so an unused harness costs nothing. What the pack adds is the one agent permitted
to execute a run (`CLAUDE.md` constraint 2).

Prefer a new assignment *lens* to a new role, and a new pack to neither: see
[`../.claude/agents/MAINTAINING.md`](../.claude/agents/MAINTAINING.md).
