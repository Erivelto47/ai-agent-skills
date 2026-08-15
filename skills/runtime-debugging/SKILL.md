---
name: runtime-debugging
description: Diagnose reproducible software failures through a disciplined reproduce, evidence, hypothesis, verification, minimal-fix, and regression loop. Use when behavior differs at runtime, a test or service fails intermittently, logs and state must be correlated, or a suspected fix needs proof.
---

# Runtime Debugging

Treat runtime debugging as an evidence loop, not a sequence of guesses. Keep the failing scenario reproducible, isolate one hypothesis at a time, and leave an auditable record of what was observed and verified.

## Workflow

### 1. Establish a safe reproduction

- Capture the requested symptom, expected behavior, environment, inputs, and time window.
- Check project instructions and existing worktree changes.
- Reproduce with the smallest safe command, fixture, request, or test case.
- Record whether the failure is deterministic, intermittent, or not reproduced.

### 2. Collect bounded evidence

- Collect the relevant logs, stack traces, request and response metadata, configuration, state snapshots, timestamps, and code paths.
- Correlate evidence by a safe request id or timestamp when available.
- Redact credentials, tokens, personal data, and sensitive payloads before storing or reporting evidence.
- Prefer deterministic inspection and targeted tracing over unrestricted log dumps.

### 3. Form and test hypotheses

- Write each hypothesis as a falsifiable explanation tied to observed evidence.
- Inspect only the code, configuration, dependency, data, or external boundary relevant to that hypothesis.
- Use one controlled change or experiment at a time.
- Mark a hypothesis as disproved, supported, or unresolved; do not promote correlation to cause.

### 4. Apply and verify the smallest safe fix

- Change only after the failure mechanism is sufficiently supported.
- Reproduce the original failure before the fix and the expected behavior after it.
- Run focused regression checks, then broader checks proportional to the risk.
- Compare logs, outputs, state, and exit status rather than relying on “it worked once.”

### 5. Report the result

- Use [references/runtime-report.md](references/runtime-report.md).
- Include reproduction status, evidence paths, hypothesis history, changed files, commands, results, and remaining uncertainty.
- State clearly whether the issue is fixed, mitigated, not reproduced, or blocked.

## Tool selection

- Use the least powerful capability that can answer the current question: test runner, log inspection, debugger, request replay, read-only data query, or targeted source inspection.
- Treat external services, databases, queues, and runtime controls as explicit boundaries with their own authorization and safety checks.
- If an adapter or MCP is unavailable, preserve the evidence trail and report the exact diagnostic gap instead of fabricating a result.

## Boundaries

- Do not run destructive commands, mutate production data, send external messages, or change deployment state without explicit authorization.
- Do not expose secrets or copy sensitive runtime payloads into a public report.
- Do not silently retry a failing external dependency until the evidence becomes ambiguous.
- Stop when the reproduction is unsafe, the evidence is insufficient, or the suspected fix would change an unrelated contract.

## Example

For a failing request in a sample service, capture the request shape and timestamp, reproduce it with a safe fixture, correlate the application log and downstream response, test one cause, apply the minimal fix, rerun the same fixture, and report the before/after evidence without including real user data.
