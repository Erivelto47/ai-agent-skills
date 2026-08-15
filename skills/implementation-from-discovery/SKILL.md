---
name: implementation-from-discovery
description: Turn a validated codebase discovery report into a minimal, reviewable software change with focused tests and an evidence-backed validation report. Use when an agent has verified current behavior and must implement a bug fix, small feature, migration step, or refactor without widening scope.
---

# Implementation From Discovery

Use a validated discovery report as the starting point for a small, explicit change. Preserve existing behavior outside the requested outcome and make every assumption visible.

## Preconditions

- Confirm that the discovery identifies the target behavior, affected files or symbols, tests, and open questions.
- Read project instructions, local conventions, and the current worktree status.
- Confirm the user has authorized the requested write scope; do not infer permission to commit, push, deploy, or alter data.
- If the discovery is stale, contradictory, or missing a critical fact, return to discovery before editing.

## Workflow

### 1. Define the change

- Restate the desired outcome, acceptance criteria, allowed scope, and explicit exclusions.
- List the smallest coherent set of files and symbols expected to change.
- Identify compatibility, security, data, and rollout risks before writing code.

### 2. Implement minimally

- Follow existing architecture, naming, error handling, validation, and test conventions.
- Prefer a focused change over opportunistic cleanup or a broad redesign.
- Preserve public contracts unless the task explicitly changes them.
- Keep secrets, private identifiers, environment-specific paths, and unrelated artifacts out of source and tests.

### 3. Validate in layers

- Run the smallest relevant test first, then broader checks justified by the change.
- Inspect the diff for accidental scope expansion, compatibility breaks, and missing tests.
- Re-run affected checks after any repair; never report a check that was not actually executed.
- Record commands, results, artifacts, failures, and unverified assumptions.

### 4. Review and hand off

- Compare the implementation against the discovery report and acceptance criteria.
- Call out behavior intentionally left unchanged and any remaining risk.
- Return the validation report before requesting review, commit, merge, release, or deployment.

## Output contract

Use the implementation checklist in [references/implementation-checklist.md](references/implementation-checklist.md) and return changed paths, test commands, results, evidence, and remaining uncertainty.

## Boundaries

- Do not implement from an unverified guess when discovery is required.
- Do not reset, overwrite, or delete unrelated user work.
- Do not commit or push unless separately authorized.
- Do not claim runtime, integration, security, or performance validation from unit tests alone.
- Stop and escalate when the requested change conflicts with repository instructions, public contracts, data safety, or the discovery evidence.

## Example

For a validated report showing that a command handler omits one field in a response, change the narrow handler or mapper, add a focused regression test, run the relevant test suite, inspect the diff, and report the exact evidence. Do not refactor neighboring handlers unless required by the acceptance criteria.
