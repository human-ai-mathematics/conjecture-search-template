# Shared instance registry

The canonical calibration and stress instances for this program's numerical batteries. This is
human-reviewed reference, **not executable configuration**: target modules own their effective
battery and record it in each artifact.

Anyone may propose an instance; only the `synthesizer` adds one (`CLAUDE.md` constraint 3). The
reason is adversarial: an instance chosen by the agent whose claim it tests will be one the claim
survives. Reject instances that only serve one agent's happy path.

Passing a finite battery changes no claim or proof status, however large the battery
(`obs:example` in the seed ledger is exactly this fence).

## Calibration instances

Instances with a known closed-form answer, used to check that an implementation is correct.

| id | description | exact anchor | used by |
|---|---|---|---|
| | | | |

## Stress instances

Instances chosen to break a claim: extremal, degenerate, or adversarially shaped.

| id | description | what it stresses | used by |
|---|---|---|---|
| | | | |
