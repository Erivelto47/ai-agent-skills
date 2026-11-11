# Runtime Debugging

Diagnose reproducible software failures as a disciplined evidence loop instead of a sequence of guesses. The skill keeps a failing scenario reproducible, tests one falsifiable hypothesis at a time, and leaves an auditable record of what was actually observed and verified — including a documented before/after for the fix itself.

## Why use it?

It is easy to "fix" a bug by changing code until the symptom disappears once, without ever confirming the mechanism. This skill requires a safe reproduction first, bounded and redacted evidence collection, one controlled experiment per hypothesis, and a before/after comparison of the same reproduction case before a fix is reported as done.

## What it does

- Establishes a safe, minimal reproduction and records whether the failure is deterministic, intermittent, or not reproduced.
- Collects bounded evidence — logs, stack traces, request/response metadata, state snapshots — correlated by request id or timestamp, with credentials and personal data redacted before storage or reporting.
- Forms each hypothesis as a falsifiable explanation tied to observed evidence, and tests it with one controlled change at a time, marking it disproved, supported, or unresolved.
- Applies the smallest safe fix only once the failure mechanism is sufficiently supported, then reproduces the original failure and the expected post-fix behavior for comparison.
- Reports reproduction status, evidence paths, hypothesis history, changed files, commands, results, and remaining uncertainty.

See [SKILL.md](SKILL.md) for the full workflow and tool-selection order. See [references/runtime-report.md](references/runtime-report.md) for the exact report format.

## Boundaries

This skill never runs destructive commands, mutates production data, sends external messages, or changes deployment state without explicit authorization. It does not expose secrets or copy sensitive runtime payloads into a public report, and it does not silently retry a failing external dependency until the evidence becomes ambiguous. It stops when reproduction is unsafe, evidence is insufficient, or the suspected fix would change an unrelated contract.

## Cross-tool support

[agents/openai.yaml](agents/openai.yaml) exposes the same workflow under Codex's agent interface, so the evidence loop is identical whether the active coordinator is Claude Code, Codex, or another `SKILL.md`-compatible tool.
