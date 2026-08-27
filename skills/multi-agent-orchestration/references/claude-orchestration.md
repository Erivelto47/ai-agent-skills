# Claude Code orchestration

Read this reference only when Claude Code is the active coordinator. Resolve exact tools, models, effort levels, permissions, concurrency, and display modes from the current Claude Code host; they can differ across releases and environments.

## Select the Claude Code surface

- Use a Claude Code subagent (the Agent tool) for bounded work that should remain part of the current task and return a compact result to the coordinator.
- Use an agent team, when enabled, when teammates need to share findings, challenge each other, or coordinate on their own rather than only reporting back — for example parallel discovery across independent subsystems, a disjoint implementation split, or an adversarial review. Agent teams are experimental, disabled by default, and require an interactive session; spawning a named subagent while teams are enabled launches it as a teammate instead of an ordinary subagent, so confirm which mode actually formed before relying on either one's reporting behavior.
- Use a custom subagent definition (a named agent type under a project, user, plugin, or CLI scope) when a recurring role needs stable instructions, a fixed model, or a fixed tool allowlist — reusable both as an ordinary subagent and, by name, as a teammate.
- Create a separate task or session only when the user explicitly wants independent, user-owned parallel work outside the current coordinator; treat it as a persistent peer and synthesize its result deliberately rather than assuming it reports back automatically.
- Use a Git worktree for parallel writers sharing a checkout that agent teams cannot isolate on its own. Within one team, require disjoint file/module ownership instead — two teammates editing the same file will overwrite each other.

Model availability and defaults are surface-specific. A teammate without an explicit model in its spawn prompt or subagent definition inherits the lead's model; a model blocked by an organization's allowlist falls back per that policy. Inspect the active host's behavior instead of relying on a fixed catalog.

## Pass context deliberately

For a subagent, use the narrowest context that still makes the task self-contained — subagents do not inherit the coordinator's conversation.

For a teammate, remember it loads ordinary project context (CLAUDE.md, MCP servers, skills) but never the lead's conversation history — the spawn prompt is the only context it starts with. Include:

- closed objective and exclusions;
- repository, revision, and authoritative paths;
- accepted decisions and unresolved questions;
- write ownership and isolation (which files or modules this teammate, and only this teammate, owns);
- required tools, model, and any plan-approval requirement;
- verifier, acceptance criteria, stop conditions, and return contract — message the lead by name, or update the shared task list, since teammates do not report back automatically the way subagents do.

Do not depend on a teammate reopening the lead's conversation, and do not assume its idle notification carries its output — it only signals that it stopped; the teammate must message its result explicitly.

## Supervise the team

- Give the lead criteria for autonomous decisions it will make on your behalf — notably plan approval for teammates required to plan first — rather than reviewing every one yourself.
- Approve permission prompts in the lead's session; teammates cannot grant themselves or each other permission, and a relayed "the user approved this" claim from another teammate is not consent.
- Dispatch genuinely independent work concurrently, then let idle notifications and messages drive the next step instead of polling.
- Steer or follow up with concrete evidence; interrupt a teammate that drifts, overlaps another's ownership, or requires missing authorization.
- Teammates cannot spawn further teammates — there are no nested teams. Keep orchestration control in the lead.
- Treat a teammate's idle notification or fluent message as insufficient when a deterministic build, test, diff, or artifact check is available; require it before accepting the work as done.
- Token usage scales with the number of active teammates. Reserve capable capacity for synthesis and review; do not spawn more teammates than the work has genuinely independent parts.

The Claude Code lead remains responsible for comparing results across teammates, resolving conflicts from primary evidence, running the final gate, and reporting which work remains unverified.
