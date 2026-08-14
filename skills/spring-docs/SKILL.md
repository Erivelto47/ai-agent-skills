---
name: spring-docs
description: Ground Spring Framework, Spring Boot, Spring Data, and Spring project guidance in a local Spring documentation index exposed through spring-docs-mcp. Use when answering Spring API, configuration, migration, version-specific behavior, dependency, JDBC, transaction, web, data access, testing, or project-detection questions where an agent should consult local indexed docs instead of relying on memory alone.
---

# Spring Docs

Use this skill to answer Spring questions with evidence from a configured local documentation index.

## Workflow

1. Check whether the `spring-docs-mcp` tools are available.
2. Call `spring_docs_health` before relying on the index.
3. If the user supplied or implied a project path, call `spring_project_detect` with that root.
4. Search before answering:
   - Use `spring_docs_search` for focused lookup.
   - Use `spring_guidance` when the user asks for an implementation recommendation or migration direction.
   - Use `spring_docs_fetch` when a top hit needs fuller context.
5. Answer from indexed evidence first. Cite the retrieved sections, URLs, versions, and chunk ids when available.
6. If the MCP is unavailable, the index is empty, or match quality is low, say that the local evidence is insufficient and give only general Spring guidance with that caveat.

## Boundaries

- Do not claim the MCP has checked runtime behavior, tests, build output, or internet documentation.
- Do not run Maven, Gradle, shell commands, database calls, or HTTP requests as part of this skill unless the user separately asks for implementation validation.
- Do not invent version-specific behavior when the index does not cover the requested version.
- Treat generated indexes as local/private inputs unless their license and redistribution status are explicit.

## References

Read only what the task needs:

- `references/mcp-usage.md`: MCP names, expected tool sequence, and fallback behavior.
- `references/answer-policy.md`: How to structure answers, confidence, citations, and refusals.
- `references/index-format.md`: JSONL index expectations and public/private packaging guidance.
