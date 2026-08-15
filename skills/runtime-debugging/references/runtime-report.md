# Runtime debugging report

Use this structure for an evidence-backed debugging handoff.

## Status

`FIXED`, `MITIGATED`, `NOT_REPRODUCED`, or `BLOCKED`.

## Symptom and expected behavior

Describe the failure, expected result, environment boundary, inputs, and time window without sensitive payloads.

## Reproduction

- Reproduction command, request, or test:
- Fixture or sanitized input:
- Before-fix result:
- Reproducibility:

## Evidence

List logs, traces, stack frames, state snapshots, timestamps, code paths, and external responses. Include paths or artifact identifiers and redact secrets.

## Hypotheses

| Hypothesis | Supporting evidence | Test performed | Result |
|---|---|---|---|
| A concise cause | Evidence reference | Controlled check | Supported, disproved, or unresolved |

## Change and verification

- Changed paths:
- Minimal fix or mitigation:
- After-fix reproduction:
- Regression checks:
- Commands and results:

## Remaining uncertainty

Record untested branches, unavailable dependencies, intermittent behavior, and follow-up work.
