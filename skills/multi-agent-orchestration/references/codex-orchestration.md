# Codex orchestration

Read this reference only when Codex is the active coordinator. Resolve exact tools, models, reasoning levels, permissions, concurrency, and account availability from the current Codex host; they can differ across releases and environments.

## Select the Codex surface

- Use a Codex subagent for bounded work that should remain part of the current task and return a compact result to the coordinator.
- Use a custom Codex agent when a recurring role needs stable instructions, model or reasoning defaults, sandboxing, MCP access, or skill configuration.
- Create a separate Codex task only when the user explicitly requests a new task or parallel user-owned tasks. Treat it as a persistent peer, provide a self-contained prompt, wait for required results, and synthesize them in the coordinator.
- Fork a task when completed history is materially useful. Remember that an active unfinished turn may not be copied; add an explicit handoff when necessary.
- Use a separate worktree for parallel writers. In one shared checkout, require disjoint ownership or serialize writes.
- Use a configured external agent CLI when another provider is available and better suited or preserves constrained Codex capacity. Treat it as an external executor, not as an unsupervised shell command.

Model availability is surface-specific. A model available for a separate task or API call may be unavailable to the subagent spawn primitive, and supported reasoning levels may differ. Inspect the active tool metadata or adapter instead of relying on a global model catalog.

## Pass context deliberately

For subagents, use the narrowest available context fork that still makes the task self-contained: no inherited turns plus a context packet, a bounded number of recent turns, or full completed history only when necessary.

For separate or external tasks, include:

- closed objective and exclusions;
- repository, revision, and authoritative paths;
- accepted decisions and unresolved questions;
- write ownership and isolation;
- required tools and permissions;
- verifier, acceptance criteria, stop conditions, and return contract.

Do not depend on the worker reopening the coordinator's entire conversation.

## Supervise Codex and external executors

- Respect the concurrency slots reported by the active Codex environment; keep capacity for the coordinator and possible repair.
- Dispatch genuinely independent work concurrently, then use the available wait mechanism instead of frequent polling.
- Steer or follow up with concrete evidence. Interrupt tasks that drift, overlap ownership, or require missing authorization.
- Do not let subagents create recursive delegation trees unless the environment explicitly supports and the plan requires it; keep orchestration control in the coordinator.
- When using an external agent CLI, use an adapter-defined non-interactive command, an explicit working directory, bounded output and time, and captured exit status. Do not expose credentials or persist authentication output.
- Treat a successful process exit or fluent answer as insufficient when a deterministic build, test, diff, or artifact check is available.

The Codex coordinator remains responsible for comparing results across providers, resolving conflicts from primary evidence, running the final gate, and reporting which work remains unverified.
