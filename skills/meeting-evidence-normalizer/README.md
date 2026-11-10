# Meeting Evidence Normalizer

Turn a local meeting recording or an existing transcript into a traceable evidence package for humans and AI agents. The skill helps teams understand what was discussed, retain uncertainty, and prepare evidence for subsequent investigation.

## Why use it?

A meeting summary alone can lose the context behind a decision or turn an uncertain transcription into an apparent fact. This skill preserves the original transcription and produces structured material that can be checked against the source and used in later technical work.

It can be used for personal initiatives as well as team work. The skill itself is reusable; meeting contents and private terminology stay outside this public repository.

## What it does

- Processes an audio or video recording with a configured local transcriber, or starts from an existing transcript JSON.
- Preserves the raw transcription and produces a normalized transcript, meeting notes, structured evidence, uncertainty records, and a manifest.
- Uses an optional private glossary to flag possible domain terms and transcription variants for review; it does not treat a glossary match as proof of what was said.
- Can collect candidate glossary terms from a repository for human review.
- Provides validation for the generated evidence package.

See [SKILL.md](SKILL.md) for the agent workflow, configuration, commands, and safeguards. See [output-contract.md](references/output-contract.md) for the output formats.

## From meeting to code and architecture

Normalization is the first step in a broader, agent-assisted workflow:

1. **Meeting evidence:** capture the discussion, decisions stated, open questions, and uncertain passages with their source context.
2. **Code investigation:** ask an agent to compare relevant claims and terminology with a specific repository and revision, citing the actual implementation and tests. Record gaps and questions separately from verified behavior.
3. **Architecture:** use the verified findings and meeting context to prepare current-state diagrams or proposed designs, for example with a Figma plugin. Label proposals and unresolved decisions clearly.
4. **Communication:** present the findings in documentation or an engineering report. The separate [engineering-report-artifacts](../engineering-report-artifacts/SKILL.md) skill can help format a status tracker or code-review report.

These steps require the relevant repository access, tools, and human review. The normalizer does not independently verify the code, create an architecture, or establish that a proposal is deployed or approved.

## Handoff for a reader and their AI agent

After normalization, the skill can also help turn the evidence into a **handoff**: a shareable document for someone who was not in the meeting and for that person's AI agent. Every point is marked as said rather than validated, and a mandatory AI section tells the agent how to check the claims against a repository.

- [handoff-guide.md](references/handoff-guide.md) defines the format, and [handoff-template.md](references/handoff-template.md) is the skeleton.
- [validate-handoff.py](scripts/validate-handoff.py) checks the structure and, for shareable handoffs, flags private paths and evidence file names.
- [business-agent-prompt.md](references/business-agent-prompt.md) is a read-only prompt for a non-technical reader whose agent will research the handoff in a repository.
- A fictional, validated [example](../../examples/neutral-handoff/handoff.md) shows the result.

A handoff authorizes no action, and both producing and using it call for a high-capability agent. See [SKILL.md](SKILL.md) for the workflow.

## Getting started

From the repository root, configure a private profile based on [profile.example.yaml](config/profile.example.yaml). Then run a preflight or dry run before processing a recording. For example:

```bash
skills/meeting-evidence-normalizer/scripts/meeting-normalizer "/absolute/path/to/meeting.mp4" --config "/absolute/path/to/profile.yaml" --dry-run
```

To process an existing transcript, use `--raw-transcript` instead of the recording argument. A local transcriber must be configured for audio transcription; no particular provider is assumed. Optional audio chunking requires `ffmpeg`. See [SKILL.md](SKILL.md) for the complete commands and configuration lookup rules.

## Privacy and evidence boundaries

Processing is local by default. Do not upload recordings, transcripts, or glossary content without explicit authorization, or commit real meeting outputs and private configuration to this public repository. Access to a repository or external design service should follow the applicable permissions and the user's instructions.

Transcription can be wrong: review uncertain passages against the original audio. Statements and actions mentioned in a meeting are evidence of the discussion, not automatically confirmed facts, approved work, or implemented behavior.
