# Discovery report contract

Use this compact structure when returning a codebase discovery.

## Status

`COMPLETE`, `PARTIAL`, or `BLOCKED`, with one sentence explaining why.

## Scope

- Project root and revision:
- Question investigated:
- Included paths or subsystem:
- Excluded paths:

## Current behavior

Describe only behavior supported by evidence. Separate observed facts from inferences.

## Execution flow

List the relevant entry point, calls, branches, outputs, and side effects in order.

## Data flow

Name important inputs, transformations, validation, state changes, and outputs. Include persistence or external boundaries when relevant.

## Relevant files and symbols

| Path | Symbol or region | Why it matters | Evidence |
|---|---|---|---|
| `src/example/...` | `ExampleHandler.handle` | Entry point | Search or symbol lookup |

## Tests and checks found

List relevant tests, fixtures, configuration, commands, and whether each was run.

## Evidence

Include exact paths, symbols, commands, result summaries, and artifact locations. Redact sensitive values.

## Uncertainties

List missing evidence, conflicting observations, untested branches, and assumptions.

## Recommended next step

State the smallest safe next action and the verifier that should prove it.
