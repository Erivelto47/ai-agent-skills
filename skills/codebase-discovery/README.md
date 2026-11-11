# Codebase Discovery

Build a concise, evidence-backed model of an existing codebase's current behavior before proposing or implementing a change. The skill keeps investigation read-only and turns scattered exploration into a short report another agent — or human — can act on without reopening the whole repository.

## Why use it?

Changes made on top of a guessed understanding of the code tend to widen scope, miss existing behavior, or silently break an invariant nobody wrote down. This skill forces a narrow, question-driven investigation: state the question first, trace the real execution path with evidence (exact paths and symbols, not naming guesses), and separate observed facts from inference before anything gets implemented.

It is meant to be the first step of a larger workflow, not a one-off exploration. Its output is designed to feed directly into [implementation-from-discovery](../implementation-from-discovery/README.md) or [runtime-debugging](../runtime-debugging/README.md).

## What it does

- Scopes the investigation to a stated question, boundary, and explicit exclusions instead of a repository-wide dump.
- Locates entry points (symbols, routes, commands, events, configuration) with deterministic search and symbol navigation before broad reading.
- Traces the normal execution path, including data transformations, validation, branching, persistence, and external calls, and identifies ownership boundaries.
- Inspects the verification surface (unit, integration, contract, end-to-end tests) and distinguishes tests that actually exercise the target behavior.
- Synthesizes a short, structured report that separates facts, inferences, and open questions, and states the recommended next step.

See [SKILL.md](SKILL.md) for the full workflow and tool-selection order. See [references/discovery-report.md](references/discovery-report.md) for the exact report sections.

## Boundaries

Discovery never edits source, commits, pushes, migrates data, or changes runtime state. It does not broaden scope because adjacent code looks inconsistent, and it never includes credentials, tokens, or private data in the report. When evidence conflicts or the requested scope is ambiguous, the workflow calls for escalation instead of a guess.

## Cross-tool support

[agents/openai.yaml](agents/openai.yaml) exposes the skill under Codex's agent interface with the same contract, so the skill behaves the same whether the active coordinator is Claude Code, Codex, or another `SKILL.md`-compatible tool.
