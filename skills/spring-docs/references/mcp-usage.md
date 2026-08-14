# MCP Usage

## Server

Use any MCP server that exposes the Spring Docs tool contract below.

One public npm implementation is:

```text
@erivelto_muller/spring-docs-mcp
```

Typical config variable:

```text
SPRING_DOCS_MCP_CONFIG=/path/to/spring-docs.yaml
```

The MCP server reads a local JSONL index. It does not execute build tools, run tests, or bundle Spring documentation.

The public package can also bootstrap a local index from official Spring HTML documentation:

```bash
spring-docs-mcp init --allowed-root /path/to/projects
spring-docs-mcp index --source spring-boot --version 3.4
spring-docs-mcp index --source spring-framework --version 6.2
spring-docs-mcp serve
```

Use those commands as setup guidance when `spring_docs_health` reports a missing or empty index.

## Tools

- `spring_docs_health`: Check config, loaded chunks, source groups, versions, and warnings.
- `spring_docs_search`: Search local indexed Spring documentation.
- `spring_docs_fetch`: Fetch one indexed chunk by `chunk_id`.
- `spring_project_detect`: Read bounded Maven/Gradle metadata below configured `allowed_roots`.
- `spring_guidance`: Return a grounded recommendation skeleton from docs plus optional project metadata.

## Sequence

For most questions:

1. `spring_docs_health`
2. `spring_docs_search` with the user's terms and likely source groups.
3. `spring_docs_fetch` for the best chunk if the snippet is not enough.
4. Answer with citations and confidence.

For project-specific questions:

1. `spring_docs_health`
2. `spring_project_detect` when a project root is available.
3. `spring_guidance` with `project_root`, or `spring_docs_search` plus a manual answer.

## Fallbacks

If tools are unavailable, say the Spring Docs MCP is not available in this session. Do not pretend that local indexed docs were consulted.

If health returns warnings or zero chunks, explain that the MCP is configured but lacks usable local evidence. Suggest `spring-docs-mcp index` for the relevant Spring source and version when the package CLI is available.

If search has low or no match quality, ask for a narrower topic, a version, or an expanded index when that would change the answer.
