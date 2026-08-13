# Normalization Policy

Allowed:

- Fix punctuation and capitalization in derived artifacts.
- Join fragmented sentences when timestamps and raw references remain traceable.
- Group repeated statements by topic.
- Use the glossary as a hint when raw text and context support the correction.
- Use `context_keywords` to raise glossary candidates for review.
- Use `possible_contexts` to explain why a term may matter while keeping the context probabilistic.
- Use `phonetic_aliases` and `observed_asr_variants` to find possible mentions while preserving matched raw text.
- Match glossary terms only on word boundaries. Short canonical names, aliases, phonetic aliases, or ASR variants below five normalized characters must be treated as review-only hits with `confidence: short_alias_review`.
- Mark contradiction/correction patterns as contradictions only when a glossary hit or context candidate appears in the segment or a small neighboring window. If no glossary is configured, connector-only contradiction detection remains a known weak heuristic.
- Detect consecutive repeated ASR text runs and exclude those segments from evidence counts while preserving an audit summary in `uncertainties.json`.
- Preserve self-corrections, uncertainty words, contradictions, and validation promises.

Not allowed:

- Edit `transcription.raw.json` in place.
- Invent speakers or biometric identity.
- Replace uncertain terms solely because a known glossary term looks similar.
- Match short aliases as substrings inside unrelated words.
- Promote a context-only candidate to a corrected canonical term without reviewing the raw segment.
- Treat `possible_contexts` as exclusive or fixed truth.
- Remove contradictions because one version appears more plausible.
- Hide ASR degeneration or repeated hallucinated transcript blocks. Surface them as quality warnings and excluded low-confidence ranges.
- Turn uncertainty words into verified facts.
- Send audio or transcript content to cloud services by default.

Limitations:

- Glossary-anchored contradiction detection reduces connector-only false positives, but it is not a full contradiction classifier. A connector near an unrelated glossary term can still require human review.
