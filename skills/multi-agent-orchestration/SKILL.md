---
name: multi-agent-orchestration
description: Coordinate complex software work across agents, models, tools, task surfaces, or providers with bounded ownership, budget-aware executor selection, controlled context, evidence contracts, and validation gates. Use when independent fronts, heterogeneous executors, quota constraints, costly context, or independent review justify orchestration.
---

# Multi-Agent Orchestration

Coordinate work around a shared outcome while keeping each delegated task narrow, independently verifiable, and safe to integrate. The coordinator is the global decision-maker: it owns intent, decomposition, provider allocation, synthesis, and final gates while delegating bounded execution to the best available surface. The active environment must still provide and authorize the tools, agents, task runtimes, and providers used.

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

Keep roles abstract. A role may be fulfilled by the coordinator's native agent, a same-session worker, an isolated task, an external agent runtime, a deterministic tool, or a specialist service. Resolve the concrete provider, model, reasoning effort, task surface, and tool set through the active environment or local adapter only after confirming actual availability.

## Workflow

### 1. Define the global task and resource posture

- State the outcome, constraints, acceptance criteria, exclusions, risk level, and human decisions still required.
- Read project instructions and inspect existing work before assigning ownership.
- Inventory relevant executors and deterministic capabilities, including permissions, context limits, concurrency, isolation, model or effort support, and provider budget or quota state.
- Treat unobservable remaining quota as `unknown`; never invent usage. Preserve enough capable capacity for synthesis, recovery, and high-risk review instead of exhausting one provider on routine work.
- Run environment and capability checks required by the local adapter; never claim a provider is available from configuration alone.

### 2. Plan capabilities and ownership

- Map each front to the minimum capabilities it needs: search, symbol navigation, build, test, runtime control, documentation, version control, or review.
- Give every writable path one owner and declare read-only paths explicitly.
- Order dependent tasks and run only genuinely independent fronts in parallel.
- Keep global decisions, cross-front trade-offs, and final acceptance with the coordinator. Delegate implementation or complex analysis to another capable provider when that is the best use of the available portfolio.

### 3. Select the execution surface and executor

- Prefer a deterministic tool when it can complete or verify the work without an agent.
- Otherwise choose among a same-session agent, isolated task or worktree, external agent runtime, or specialist service based on context needs, lifetime, write isolation, observability, and integration cost.
- Select the lowest-cost executor that is sufficiently capable for the front while balancing latency, quality, verifier strength, and remaining provider capacity. Do not equate "small worker" with "low effort": choose any supported reasoning level justified by ambiguity, risk, and verification difficulty.
- Use a stronger model or alternate provider for difficult coding when a cheap worker would create rework. Keep reviewers independent from the implementation path when risk warrants it.
- Read [references/executor-selection.md](references/executor-selection.md) when more than one provider, model tier, quota pool, or execution surface is available.
- When the active coordinator is Codex, read [references/codex-orchestration.md](references/codex-orchestration.md) before dispatching Codex subagents, separate tasks, custom agents, or external agent CLIs.

### 4. Dispatch bounded tasks

- Fill the child task envelope from [references/orchestration-contracts.md](references/orchestration-contracts.md).
- Pass the minimum sufficient context needed to act, not the entire conversation or repository. Prefer a compact context packet with authoritative paths, state or revision, decisions, and evidence.
- Include a verifier, acceptance criteria, escalation condition, return contract, and stop conditions.
- Do not dispatch tasks that overlap in ownership or ask a worker to infer missing authorization.
- For external agent runtimes, use the configured non-interactive interface, bound execution and retries, capture status and evidence, and keep credentials or private configuration out of prompts and reports.

### 5. Supervise and rebalance

- Respect the environment's concurrency limit and the task's dependency graph. Avoid spending all available slots or provider capacity when a later gate may need a capable worker.
- Wait for required results, steer workers with concrete evidence, and stop work that has drifted outside scope. Do not create nested delegation loops.
- Retry only when failure evidence indicates a bounded repair. Escalate effort, model tier, provider, or execution surface deliberately; record the reason and the quota or quality trade-off.
- Rebalance when a provider is constrained or unavailable, but never replace a required capability with an unverified fallback.

### 6. Synthesize evidence

- Require each worker to return status, changed paths, commands, results, artifacts, assumptions, and blockers.
- Compare independent reports and resolve conflicts using primary evidence, not confidence or verbosity.
- Preserve the coordinator's global context as decisions and condensed evidence; discard redundant raw context after it is safely archived.

### 7. Apply gates and escalate

- Run the validation gates defined by the task and local adapter.
- Escalate only decisions that require human judgment, unavailable authority, conflicting evidence, unsafe operations, or a failed gate that cannot be repaired within scope.
- Return an auditable final state: complete, partial, blocked, or failed, with the reason and next action.

## Contracts

Use the discovery, child-task, and validation templates in [references/orchestration-contracts.md](references/orchestration-contracts.md). Contracts are part of the workflow: a task without ownership, verifier, acceptance criteria, and return format is not ready for dispatch.

## Boundaries

- Keep the core workflow provider-neutral. Put environment-specific mechanics in explicitly routed references or local adapters, and always verify them at runtime.
- Do not delegate secrets, destructive actions, production changes, external communication, or irreversible decisions without explicit authorization.
- Do not treat a worker's assertion as evidence when a deterministic check is available.
- Do not retry unavailable dependencies indefinitely or silently replace a failed capability with an unverified substitute.
- Do not commit, push, merge, or deploy unless the parent task explicitly authorizes it.

## Example

For a feature touching an API handler and its tests, keep architecture and acceptance with the coordinator, assign discovery to a read-only economical executor, give implementation to one sufficiently capable worker owning source and tests, and use an independent reviewer when risk warrants it. The workers may come from different providers or task surfaces. Reserve provider capacity for synthesis, give each worker a narrow context and deterministic verifier, then run the final gate.
