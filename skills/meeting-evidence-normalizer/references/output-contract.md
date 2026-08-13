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

`manifest.json` records source path, filename, size, mtime, sha256, input kind, transcription status, and processing timestamps.

`transcription.raw.json` preserves the ASR output or supplied transcript exactly as received.

`transcription.log` captures local transcriber progress/debug output so agent call logs stay quiet.

`transcription.analysis.json` contains deterministic metrics from raw segments, including suspicious ranges when ASR metrics are available.

`transcription.normalized.json` contains derived segments linked back to raw segment IDs and timestamps. It may include `glossary_hits` for direct canonical/alias/phonetic matches and `glossary_candidates` for context-only candidates that require raw review.

`evidence.json` stores extracted claims and actions as meeting evidence with raw segment references.

`uncertainties.json` stores low-confidence acoustic ranges, uncertain terms, context-only glossary candidates, ASR variant candidates, contradictions, self-corrections, and validation promises.

`meeting.md` is the human and agent handoff summary. It must not include full raw transcript text.

