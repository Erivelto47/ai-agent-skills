# Index Format

The MCP expects JSONL: one JSON object per line.

Minimal useful fields:

```json
{
  "chunk_id": "spring-framework-jdbc-rowmapper",
  "title": "Spring Framework Reference Documentation",
  "url": "https://docs.spring.io/spring-framework/reference/data-access/jdbc.html",
  "source_group": "spring-framework",
  "section": "JdbcTemplate and RowMapper",
  "version": "current",
  "tags": ["jdbc", "row-mapper"],
  "keywords": ["JdbcTemplate", "RowMapper"],
  "summary": "JdbcTemplate delegates row mapping to RowMapper callbacks.",
  "text": "Short curated excerpt or summary used for local search."
}
```

Useful optional fields:

- `version_ref`
- `heading_path`
- `topics`
- `apis`
- `repository`
- `commit_sha`
- `public_url`
- `content_hash`

## Public Packaging

Keep generated indexes out of public repositories unless redistribution rights are clear.

Prefer public packages to include:

- MCP code;
- schema documentation;
- tiny synthetic fixtures for tests;
- scripts or instructions for users to generate their own local index.

Do not commit machine-specific paths, private project names, generated private indexes, credentials, or local MCP client config.
