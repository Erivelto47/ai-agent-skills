---
name: meeting-evidence-normalizer
description: Transform local meeting recordings or transcript JSON files into traceable meeting knowledge. Use when an agent needs to transcribe or normalize a meeting, preserve raw ASR output, generate evidence.json, uncertainties.json, meeting.md, and manifest.json, or use a configurable glossary to identify domain terms by canonical name, aliases, context keywords, pronunciation, and observed ASR variants without promoting uncertain audio to fact.
---

# Meeting Evidence Normalizer

## Quick Start

Run the deterministic entrypoint with either an audio file or an existing transcript JSON:

```bash
skills/meeting-evidence-normalizer/scripts/meeting-normalizer "/absolute/path/to/meeting.mp4" --config "/absolute/path/to/profile.yaml"
skills/meeting-evidence-normalizer/scripts/meeting-normalizer --raw-transcript "/absolute/path/to/transcription.raw.json" --config "/absolute/path/to/profile.yaml"
```

If `--config` is omitted, the script searches upward from the current directory for `.meeting-evidence-normalizer.yaml`, `.meeting-evidence-normalizer/config.yaml`, or `.agents/meeting-evidence-normalizer/profile.yaml`, then checks `~/.config/meeting-evidence-normalizer/profile.yaml` and `~/.meeting-evidence-normalizer.yaml`.
If no config exists, ask the user where meeting outputs should be written, whether a transcriber command is available, and whether a private glossary should be used.

Use `--dry-run` before processing real audio. Use `--preflight` to verify local tools and configuration.
Use `--force --reuse-raw` when `transcription.raw.json` already exists and only derived artifacts need to be regenerated after glossary or policy changes.

Harvest glossary candidates from a repository before a human or higher-level agent enriches a private glossary:

```bash
skills/meeting-evidence-normalizer/scripts/glossary-harvest --repo "/absolute/path/to/repo"
```

Cross-check multiple transcript-scored harvest outputs before a human reviews the confirmed batch:

```bash
skills/meeting-evidence-normalizer/scripts/glossary-confirm \
  --candidates "/path/to/source-a/candidates.yaml" "/path/to/source-b/candidates.yaml" \
  --out "/path/to/glossary-confirmed.yaml" \
  --report "/path/to/glossary-confirm-report.md"
```

The harvest output is candidate-only. The confirm output is a triage shortcut for strong cross-source evidence; do not merge either artifact into a private glossary without review.

## Workflow

1. Load config from `--config`, then project-local config discovery, then user-level config discovery, then safe defaults.
2. Resolve the input as either an audio/video file or `--raw-transcript`.
3. Compute source metadata and create a deterministic output directory.
4. Skip already processed inputs when a complete manifest exists, unless `--force` is requested.
5. If a raw transcript already exists and `--force --reuse-raw` is used, regenerate derived artifacts without rerunning transcription.
6. If audio transcription is needed, use the configured local transcriber command. Do not assume any specific provider is installed.
7. Capture transcriber stdout/stderr to `transcription.log` so agent call logs stay quiet.
8. Preserve `transcription.raw.json`. Never edit raw ASR output in place.
9. Generate deterministic analysis, normalized transcript, evidence, uncertainties, manifest, and `meeting.md`.
10. Validate the output directory with `scripts/validate-output.py <output-dir>`.

## Configuration

Read `config/profile.example.yaml` when the user needs setup help.

Important config fields:

- `outputs.root`: directory where runtime artifacts are written.
- `transcription.command`: optional command template for local transcription.
- `transcription.output_format`: expected raw transcript format, currently Whisper-style JSON or simple segment JSON.
- `transcription.chunking.enabled`: optional long-audio mitigation. When true, the script requires `ffmpeg`, splits audio into overlapping chunks, runs the configured transcriber once per chunk, adjusts timestamps, and writes one merged `transcription.raw.json`.
- `glossary.path`: optional private glossary path.
- `glossary.mode`: use `hints_only` unless the user explicitly wants stricter behavior.

Never write private glossary content into this public skill. Keep real project terms in a user-owned config or private repository.

## Glossary Behavior

Read `references/glossary-guide.md` before creating or editing a glossary.
Read `references/glossary-harvest-guide.md` before harvesting glossary candidates from code.
Read `references/glossary.schema.yaml` when validating a glossary shape.
Use `references/glossary.example.yaml` only as neutral examples.

The glossary is a hint source, not a license to rewrite uncertain audio.

- `aliases` catch known spelling/name variants.
- `phonetic_aliases` catch pronunciation patterns.
- `observed_asr_variants` catch transcript spellings that were actually observed or explicitly marked as hypotheses.
- `context_keywords` raise review candidates when nearby words suggest a term may be present.
- `possible_contexts` explain plausible roles such as product, integration, region, database object, status, or process state.

For context-only or ASR-variant matches, mark results as review candidates and preserve the matched raw text.
Do not promote meeting claims or glossary candidates to canonical facts without user or source validation.

## Glossary Harvest

Use `scripts/glossary-harvest` when a user wants to bootstrap or refresh a private glossary from a code repository.

- Keep harvest deterministic, offline, and local.
- Use declarative profiles from `profiles/`; do not add stack-specific logic to scripts.
- Emit `glossary-candidates.yaml` and `glossary-harvest-report.md` as review artifacts.
- Treat every harvested term as `confidence: candidate`.
- Keep real repository validation outputs outside Git.
- Use `--transcripts <dir>` only when processed meeting outputs are available and the user authorizes using them for local spokenness scoring.
- Use `scripts/glossary-confirm` only after each input `candidates.yaml` was generated with `--transcripts`; it requires `spokenness_active: true`.
- Treat `confidence: cross_source_confirmed` as a review batch, not as permission to write directly to `domain-glossary.yaml`.

## Safety Rules

- Keep processing local unless the user explicitly authorizes a cloud service.
- If `transcription.chunking.enabled` is true, require `ffmpeg` and fail clearly when it is missing.
- Do not upload audio, transcripts, or glossary content by default.
- Do not copy meeting audio into Git.
- Do not version runtime outputs.
- Do not invent speakers or biometric identity.
- Treat actions mentioned in a meeting as `action_mentioned_in_meeting`, not approved tasks.
- Preserve contradictions, corrections, uncertainty words, and promises to validate later.

## References

Read only what the task needs:

- `references/output-contract.md` for artifact shapes.
- `references/normalization-policy.md` for allowed and forbidden normalization behavior.
- `references/glossary-guide.md` for how to build a private glossary.
- `references/glossary-harvest-guide.md` for deterministic repository harvesting.
- `references/glossary.schema.yaml` for glossary fields.
- `references/glossary.example.yaml` for neutral examples.
