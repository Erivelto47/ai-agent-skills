# Spring Docs

Ground Spring Framework, Spring Boot, Spring Data, and other Spring project answers in a local, indexed documentation set exposed through an `spring-docs-mcp`-compatible server, instead of answering version-specific questions from model memory alone.

## Why use it?

Spring's API and recommended configuration shift across versions, and an agent answering from memory alone can confidently state behavior that does not match the project's actual dependency versions. This skill requires checking the index's health, detecting the project's actual Spring versions when a path is available, and searching before answering — with an explicit fallback that states when local evidence is insufficient instead of guessing.

## What it does

- Checks whether `spring-docs-mcp` tools are available and calls `spring_docs_health` before relying on the index.
- Calls `spring_project_detect` against the user's project root when one is supplied or implied, to ground answers in the actual versions in use.
- Searches with `spring_docs_search` for focused lookups, `spring_guidance` for implementation or migration recommendations, and `spring_docs_fetch` when a hit needs fuller context.
- Answers from indexed evidence first, citing retrieved sections, URLs, versions, and chunk ids when available.
- Falls back explicitly — general guidance with a stated caveat — when the MCP is unavailable, the index is empty, or match quality is low.

See [SKILL.md](SKILL.md) for the exact tool sequence. Key references:

- [references/mcp-usage.md](references/mcp-usage.md) — MCP tool names, expected call order, and fallback behavior.
- [references/answer-policy.md](references/answer-policy.md) — how to structure answers, confidence, citations, and refusals.
- [references/index-format.md](references/index-format.md) — JSONL index expectations and public/private packaging guidance.

## Boundaries

This skill never claims the MCP has checked runtime behavior, tests, build output, or live internet documentation, and it does not run Maven, Gradle, shell commands, database calls, or HTTP requests unless the user separately asks for implementation validation. It never invents version-specific behavior the index does not cover, and generated indexes are treated as local/private inputs unless their license and redistribution status are explicit.

## Cross-tool support

[agents/openai.yaml](agents/openai.yaml) exposes the same tool sequence and answer policy under Codex's agent interface, so the grounding behavior is identical whether the active agent is Claude Code, Codex, or another `SKILL.md`-compatible tool with access to a compatible `spring-docs-mcp` server.
