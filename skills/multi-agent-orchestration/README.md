# Multi-Agent Orchestration

Coordinate complex software work across agents, models, tools, task surfaces, or providers while keeping every delegated task narrow, independently verifiable, and safe to integrate. The coordinator stays the global decision-maker — owning intent, decomposition, provider allocation, synthesis, and final gates — while execution is delegated to the best available surface for each front.

## Why use it?

Parallelism is only worth its coordination overhead when fronts are genuinely independent and each result has a concrete verifier; otherwise many cheap workers can cost more and produce worse results than one well-scoped capable worker. This skill provides the decision rules for when to orchestrate at all, how to size each executor to the actual difficulty of its front (never just "small worker = low effort"), and how to reserve capable capacity for synthesis and recovery instead of exhausting one provider on routine work.

## What it does

- Decides whether to orchestrate at all: keeps trivial, tightly-coupled, or unverifiable work with a single agent.
- Defines abstract roles — `coordinator`, `bounded_worker`, `deep_explorer`, `specialist`, `reviewer` — resolved to concrete providers only after confirming real availability.
- Maps each front to the minimum capabilities it needs, gives every writable path one owner, and orders dependent tasks so only genuinely independent fronts run in parallel.
- Selects the lowest-cost executor sufficiently capable for each front, matching reasoning/compute level to ambiguity, risk, and verification difficulty.
- Dispatches bounded child tasks with a compact context packet, a verifier, acceptance criteria, and stop conditions — never the entire conversation or repository.
- Supervises execution within concurrency and quota limits, synthesizes evidence from independent reports, and runs final validation gates before returning an auditable state (complete, partial, blocked, or failed).

See [SKILL.md](SKILL.md) for the full workflow. Key references:

- [references/executor-selection.md](references/executor-selection.md) — how to pick among providers, model tiers, and task surfaces when more than one is available.
- [references/orchestration-contracts.md](references/orchestration-contracts.md) — the discovery, child-task, and validation templates that make a task dispatch-ready.
- [references/claude-orchestration.md](references/claude-orchestration.md) — mechanics specific to a Claude Code coordinator.
- [references/codex-orchestration.md](references/codex-orchestration.md) — mechanics specific to a Codex coordinator.

## Boundaries

The core workflow stays provider-neutral; environment-specific mechanics live only in the routed references or local adapters, and must be verified at runtime rather than assumed from configuration. This skill never delegates secrets, destructive actions, production changes, external communication, or irreversible decisions without explicit authorization, never treats a worker's assertion as evidence when a deterministic check is available, and never commits, pushes, merges, or deploys unless the parent task explicitly authorizes it.

## Cross-tool support

[agents/openai.yaml](agents/openai.yaml) exposes the same role and contract model under Codex's agent interface. The skill is designed so the coordinator role itself can be Claude Code, Codex, or another `SKILL.md`-compatible tool, with provider-specific mechanics isolated to the dedicated reference files above.
