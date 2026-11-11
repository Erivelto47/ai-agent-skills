# Implementation From Discovery

Turn a validated [codebase-discovery](../codebase-discovery/README.md) report into a small, explicit, reviewable change. The skill exists to stop "discovery" and "implementation" from blurring into one unverified pass — it only starts writing code once the target behavior, affected files, tests, and open questions are already confirmed.

## Why use it?

A change built directly on assumption tends to widen scope, break an untested contract, or report validation that never actually ran. This skill requires a validated discovery as a precondition, keeps the change to the smallest coherent set of files, and demands that every check reported was actually executed — never claimed from unit tests alone when integration or runtime behavior is what matters.

## What it does

- Confirms the discovery is current and sufficient before any edit; sends the task back to discovery if it is stale, contradictory, or missing a critical fact.
- Restates the desired outcome, acceptance criteria, and explicit exclusions before writing code.
- Implements minimally, following existing architecture, naming, and test conventions, preserving public contracts unless the task explicitly changes them.
- Validates in layers: smallest relevant test first, then broader checks justified by the change, with the diff inspected for accidental scope expansion.
- Returns a validation report with changed paths, commands, results, evidence, and remaining uncertainty — before requesting review, commit, merge, or deployment.

See [SKILL.md](SKILL.md) for the full workflow and preconditions. See [references/implementation-checklist.md](references/implementation-checklist.md) for the exact output contract.

## Boundaries

This skill never infers permission to commit, push, deploy, or alter data — that authorization must come from the user separately. It does not reset or overwrite unrelated work, and it stops and escalates when the requested change conflicts with repository instructions, public contracts, or the discovery evidence itself.

## Cross-tool support

[agents/openai.yaml](agents/openai.yaml) exposes the same contract under Codex's agent interface, so the hand-off from discovery to implementation works the same regardless of which `SKILL.md`-compatible tool is driving it.
