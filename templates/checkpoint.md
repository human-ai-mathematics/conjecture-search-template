---
type: exploration
date: "{{DATE}}"
outcome: directional
nodes:
  - {{NODE}}
---

# {{TITLE}}

<!-- Front-matter contract, and the six triggers that make a checkpoint required:
     research/explorations/README.md.

     `outcome` is one of dead-end | directional | candidate | proposed, and the envelope
     records what the work *engaged*, never what it concluded. Declare at least one of
     `nodes:`, `approach:` or `candidates:`. Add `approach: ap:<slug>` when a portfolio
     exists and this record explains a route's state change. `date:` accepts a plain
     YYYY-MM-DD or a UTC timestamp; use the timestamp when two records on the same day
     have to be ordered. -->

## What was tried

The route, the instances, the tooling. Enough that the next agent can tell whether their
idea is this one in a new disguise.

## What happened

The result, stated so it is reusable. A dead end earns its file by saying *why* it died:
which step failed, on which instance, and what would have to change for the route to
reopen.

## What it costs the next agent

The exact blocker, if there is one — a `cand:` id or a ledger node id, never a restated
claim — and what would unblock it.
