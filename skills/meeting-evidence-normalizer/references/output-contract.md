# Output Contract

Each processed input writes one output directory:

```text
<outputs.root>/<sha256-prefix>-<safe-source-stem>/
├── manifest.json
├── transcription.raw.json
├── transcription.log
├── transcription.analysis.json
├── transcription.normalized.json
├── evidence.json
├── uncertainties.json
└── meeting.md
```

`manifest.json` records source path, filename, size, mtime, sha256, input kind, transcription status, processing timestamps, and quality summary fields:

- `quality.asr_degeneration_suspected`: true when a consecutive repeated transcript run exceeds the configured segment-ratio threshold.
- `quality.repetition_run_count`: number of detected consecutive repeated text runs.
- `quality.segments_excluded`: number of segments excluded from evidence extraction because they belong to repeated ASR runs.

`transcription.raw.json` preserves the ASR output or supplied transcript exactly as received.

`transcription.log` captures local transcriber progress/debug output so agent call logs stay quiet.

`transcription.analysis.json` contains deterministic metrics from raw segments, including suspicious ranges when ASR metrics are available. It also contains:

- `repetition_runs`: consecutive identical normalized text runs with `text`, start/end segment IDs, count, and timestamps.
- `asr_degeneration_suspected`: true when any run exceeds the configured segment-ratio threshold.
- `segments_excluded`: total segments covered by repetition runs.
- `repetition_min_run` and `asr_degeneration_segment_ratio`: thresholds used for the run analysis.

`transcription.normalized.json` contains derived segments linked back to raw segment IDs and timestamps. It may include `glossary_hits` for direct canonical/alias/phonetic matches and `glossary_candidates` for context-only candidates that require raw review. Short glossary matches below five normalized characters are emitted as review-only hits with `confidence: short_alias_review` and `action: review_raw_before_normalizing`.

`evidence.json` stores extracted claims and actions as meeting evidence with raw segment references. Segments covered by detected repeated ASR runs are excluded from claims, actions, and contradictions.

`uncertainties.json` stores low-confidence acoustic ranges, excluded repeated ASR runs, uncertain terms, context-only glossary candidates, ASR variant candidates, contradictions, self-corrections, and validation promises. Excluded repeated ASR runs appear in `excluded_low_confidence` with `type: asr_repetition_excluded`, a shortened text sample, repeat count, and timestamp/segment range.

`meeting.md` is the human and agent handoff summary. It must not include full raw transcript text. When ASR degeneration is suspected, it includes a top-level `Quality Warning` before counts so readers treat the repeated range as unreliable.
