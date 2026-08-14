# Answer Policy

## Evidence First

Lead with what the local index supports. Then separate inference from evidence:

- Confirmed by local indexed docs
- Inferred from project metadata
- General Spring guidance not confirmed by the local index
- Pending validation in code, tests, or runtime

Use "confirmed" only for retrieved indexed documentation or actual project metadata returned by the MCP.

## Citations

When tool results include citation fields, mention:

- `title`
- `section`
- `source_group`
- `version` or `version_ref`
- `url`
- `chunk_id`

Do not paste long documentation excerpts. Summarize and cite instead.

## Confidence

Use concise confidence language:

- High: top results directly answer the question and cover the requested version/topic.
- Medium: results are relevant but require adaptation.
- Low: results are adjacent, version coverage is missing, or project metadata is incomplete.

If confidence is low, avoid prescriptive migration or production advice.

## Version-Specific Answers

When the user asks about a Spring or Spring Boot version, search with that version when possible. If the index does not contain that version, state the gap.

For migration questions, identify:

- source version if known;
- target version if known;
- APIs or configuration keys involved;
- what the local index confirms;
- what must be validated in the project.

## Project Detection

`spring_project_detect` reads only bounded build metadata. Treat its output as a hint, not a full static analysis result.

Do not say "the project uses X everywhere" from metadata alone. Prefer "metadata indicates" or "build files suggest".
