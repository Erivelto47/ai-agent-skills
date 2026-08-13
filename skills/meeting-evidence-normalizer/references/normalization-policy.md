# Normalization Policy

Allowed:

- Fix punctuation and capitalization in derived artifacts.
- Join fragmented sentences when timestamps and raw references remain traceable.
- Group repeated statements by topic.
- Use the glossary as a hint when raw text and context support the correction.
- Use `context_keywords` to raise glossary candidates for review.
- Use `possible_contexts` to explain why a term may matter while keeping the context probabilistic.
- Use `phonetic_aliases` and `observed_asr_variants` to find possible mentions while preserving matched raw text.
- Preserve self-corrections, uncertainty words, contradictions, and validation promises.

Not allowed:

- Edit `transcription.raw.json` in place.
- Invent speakers or biometric identity.
- Replace uncertain terms solely because a known glossary term looks similar.
- Promote a context-only candidate to a corrected canonical term without reviewing the raw segment.
- Treat `possible_contexts` as exclusive or fixed truth.
- Remove contradictions because one version appears more plausible.
- Turn uncertainty words into verified facts.
- Send audio or transcript content to cloud services by default.

