---
name: codebase-discovery
description: Map an existing software codebase before a change by tracing behavior, data flow, integrations, persistence, tests, and evidence. Use when an agent must understand an unfamiliar repository, investigate an implementation question, prepare a change plan, or verify whether a behavior already exists.
---

# Codebase Discovery

Build a concise, evidence-backed model of current behavior before proposing or implementing a change. Keep discovery read-only unless the user separately authorizes a different action.

## Workflow

### 1. Establish scope

- Resolve the project root and read its governing instructions first.
- State the question, requested boundary, relevant subsystem, and excluded areas.
- Record the starting revision and any pre-existing worktree changes when available.
- Prefer a narrow, question-driven investigation over a repository-wide dump.

### 2. Locate entry points

- Search for symbols, routes, commands, events, configuration keys, and tests named by the task.
- Use deterministic search and symbol navigation before broad file reading.
- Record exact paths and symbols for every meaningful finding.

### 3. Trace behavior

- Follow the normal execution path from entry point to response, side effect, or output.
- Trace important data transformations, validation, branching, persistence, queues, and external calls.
- Identify ownership boundaries and the source of truth for relevant state.

### 4. Inspect verification surfaces

- Find unit, integration, contract, end-to-end, fixture, and configuration coverage.
- Distinguish tests that exercise the target behavior from nearby tests that merely share names.
- Run read-only inspection or existing checks only when requested or when they are safe and relevant to the discovery question.

### 5. Synthesize evidence

- Separate observed facts, reasonable inferences, and unresolved questions.
- Report the smallest set of paths, symbols, commands, and results that supports the conclusion.
- Do not invent behavior from naming alone; mark unverified assumptions explicitly.
- Finish with a recommended next step and the validation still required.

## Output contract

Return a discovery report with the sections in [references/discovery-report.md](references/discovery-report.md). Keep it short enough for another agent to consume without reopening the whole repository.

## Tool selection

- Prefer capabilities in this order: repository inventory/search, symbol navigation, version-control inspection, targeted documentation lookup, then safe build or test inspection.
- Use a project-specific adapter when available, but keep the report independent of any vendor, IDE, model, or MCP name.
- If a capability is unavailable, continue with the narrowest reliable alternative and disclose the limitation.

## Boundaries

- Do not edit source files, commit, push, migrate data, or change runtime state as part of discovery.
- Do not broaden the scope because adjacent code looks inconsistent.
- Do not include credentials, tokens, private user data, or copied proprietary documents in the report.
- Escalate when the evidence conflicts, the requested scope is ambiguous, or the next step would be materially destructive.

## Example

For a request such as “find where a sample service applies an eligibility rule,” locate the public entry point, trace the rule through validation and persistence, find relevant tests, and return exact paths plus any unverified branch. Do not implement the rule while performing this discovery.
