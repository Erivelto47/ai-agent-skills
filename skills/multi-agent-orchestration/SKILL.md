---
name: multi-agent-orchestration
description: Decompose software engineering work into bounded agent roles, capability assignments, explicit ownership, evidence contracts, validation gates, and escalation paths. Use when a task has independent fronts, multiple tools or agents, costly context, parallel work, or a need for auditable coordination.
---

# Multi-Agent Orchestration

Coordinate work around a shared outcome while keeping each delegated task narrow, independently verifiable, and safe to integrate. Use this skill to structure delegation; the active environment must still provide the tools, agents, permissions, and approvals required for execution.

## Decide whether to orchestrate

- Keep the work with one agent when it is trivial, tightly coupled, faster to execute serially, or has no meaningful independent verification surface.
- Orchestrate when fronts are independent, context can be summarized, ownership can be separated, and each result has a concrete verifier.
- Never create parallel work merely to increase activity or token volume.

## Roles

- `coordinator`: owns intent, constraints, dependencies, decisions, synthesis, and final gates.
- `bounded_worker`: completes one narrow, low-risk, verifiable task.
- `deep_explorer`: investigates a broad or ambiguous question and returns condensed evidence.
- `specialist`: handles a domain or tool-specific concern within explicit scope.
- `reviewer`: independently checks correctness, regressions, security, or acceptance criteria.

Keep roles abstract. Select a model, agent, tool, or MCP through the local adapter only after confirming that it is actually available.

## Workflow

### 1. Define the global task

- State the outcome, constraints, acceptance criteria, exclusions, risk level, and human decisions still required.
- Read project instructions and inspect existing work before assigning ownership.
- Run environment and capability checks required by the local adapter; never claim a provider is available from configuration alone.

### 2. Plan capabilities and ownership

- Map each front to the minimum capabilities it needs: search, symbol navigation, build, test, runtime control, documentation, version control, or review.
- Give every writable path one owner and declare read-only paths explicitly.
- Order dependent tasks and run only genuinely independent fronts in parallel.

### 3. Dispatch bounded tasks

- Fill the child task envelope from [references/orchestration-contracts.md](references/orchestration-contracts.md).
- Pass the minimum context needed to act, not the entire conversation or repository.
- Include a verifier, acceptance criteria, escalation condition, return contract, and stop conditions.
- Do not dispatch tasks that overlap in ownership or ask a worker to infer missing authorization.

### 4. Synthesize evidence

- Require each worker to return status, changed paths, commands, results, artifacts, assumptions, and blockers.
- Compare independent reports and resolve conflicts using primary evidence, not confidence or verbosity.
- Preserve the coordinator's global context as decisions and condensed evidence; discard redundant raw context after it is safely archived.

### 5. Apply gates and escalate

- Run the validation gates defined by the task and local adapter.
- Escalate only decisions that require human judgment, unavailable authority, conflicting evidence, unsafe operations, or a failed gate that cannot be repaired within scope.
- Return an auditable final state: complete, partial, blocked, or failed, with the reason and next action.

## Contracts

Use the discovery, child-task, and validation templates in [references/orchestration-contracts.md](references/orchestration-contracts.md). Contracts are part of the workflow: a task without ownership, verifier, acceptance criteria, and return format is not ready for dispatch.

## Boundaries

- Do not hard-code provider, model, IDE, MCP, company, project, user, or filesystem names into this public Skill.
- Do not delegate secrets, destructive actions, production changes, external communication, or irreversible decisions without explicit authorization.
- Do not treat a worker's assertion as evidence when a deterministic check is available.
- Do not retry unavailable dependencies indefinitely or silently replace a failed capability with an unverified substitute.
- Do not commit, push, merge, or deploy unless the parent task explicitly authorizes it.

## Example

For a feature touching an API handler and its tests, assign discovery to a read-only explorer, implementation to one worker owning the source and tests, and review to an independent reviewer. Give each worker a narrow context and verifier, then synthesize the reports before running the final gate.
