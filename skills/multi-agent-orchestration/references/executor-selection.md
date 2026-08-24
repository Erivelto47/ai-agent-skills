# Executor selection

Read this reference when orchestration can use more than one provider, model tier, reasoning or compute level, quota pool, or task surface.

## Optimize the portfolio, not one call

Treat available executors as a portfolio with different strengths, limits, reset horizons, latency, context, tools, and isolation. The objective is to complete the global task reliably without consuming scarce capable capacity on work that a cheaper executor or deterministic tool can prove.

- Keep the coordinator capable enough to preserve global intent, resolve conflicts, and run the final gate.
- Reserve capacity from at least one suitable executor for repair, synthesis, or independent review when quotas are constrained.
- Route routine work away from a constrained provider only when the alternate executor has the required tools, context, and verifier.
- Do not infer exact remaining quota from successful calls. Record `unknown` when the provider does not expose usage.
- Include coordination overhead: many cheap workers can cost more and produce worse results than one well-scoped capable worker.

## Match difficulty and verification

Choose the executor from the front's ambiguity, risk, context size, tool needs, and verification surface.

| Work shape | Suitable executor characteristics |
|---|---|
| Deterministic search, build, test, formatting, or extraction | Direct tool first; agent only for interpretation |
| Clear, repetitive, independently checked work | Economical model or runtime with the minimum sufficient context |
| Narrow but subtle analysis with strong verification | Economical or mid-tier executor using any supported reasoning level justified by the difficulty |
| Complex coding, ambiguous debugging, or cross-component reasoning | Capable implementation executor with enough context and tool access; it may differ from the coordinator's provider |
| Architecture, prioritization, synthesis, or conflicting evidence | Strong coordinator or specialist with global context |
| High-risk acceptance | Independent reviewer plus deterministic gates |

Do not reduce selection to fixed labels such as low, medium, or high. Resolve from the executor's full supported reasoning or compute range. Increasing effort is useful only when the same executor remains suitable; otherwise switch model tier, provider, task surface, or context strategy.

## Choose a task surface

- Use an in-session delegated agent for bounded work whose result should return directly to the coordinator.
- Use an isolated task, thread, process, or worktree for long-running work, independent inspection, different model availability, or write isolation.
- Use an external agent runtime or CLI when the active coordinator can supervise it and the alternate provider is better suited or has healthier quota.
- Use a specialist service or deterministic tool when agent reasoning is unnecessary.

Account for context transfer. A fresh task needs a self-contained context packet; a forked task may carry useful history but can also inherit noise. Include authoritative revisions, paths, decisions, ownership, and verifiers regardless of the surface.

## Escalation and fallback

Start at the least expensive adequate point, not automatically the smallest model or lowest effort.

Escalate only from concrete evidence such as failed validation, unresolved ambiguity, context overflow, missing tools, poor output structure, or exhausted quota. Depending on the failure, increase reasoning or compute, choose a more capable model, switch providers, improve the context packet, or move to an isolated surface. Limit retries in the same tier and preserve the failure evidence for the next executor.

A fallback is valid only when it preserves required capabilities, authorization, ownership, and validation. Record provider changes and their effect on budget, latency, and confidence.
