# Glossary Guide

Use a private glossary to help agents find likely domain terms in noisy meeting transcripts.

The glossary is not a replacement dictionary. It is a review aid. Every term should help answer:

- What is the canonical name?
- What might people say instead?
- How might the ASR spell it?
- What nearby words make the term plausible?
- What roles could the term have in different contexts?
- What source supports adding it?

## What To Add

Add terms that are repeatedly important in meetings:

- Product, feature, plan, or package names.
- Provider, integration, or external system names.
- Internal module or service names.
- Database entities, event names, status values, or workflow states.
- Region, market, locale, currency, or compliance vocabulary.
- Acronyms that people pronounce letter by letter.
- Names that ASR often misspells.

## What Not To Add

Do not add:

- Private terms to a public repository.
- One-off words with no recurring value.
- Business rules or decisions as glossary terms.
- Corrections that have no source, transcript example, or user confirmation.
- Terms whose only support is a guess by the agent.

## Field Guidance

`canonical`: Stable display name used in derived artifacts.

`category`: Broad type such as `product`, `provider`, `integration`, `database_entity`, `status`, `region`, `person_or_team`, `process`, or `unresolved_vocabulary`.

`aliases`: Orthographic or naming variants.

`phonetic_aliases`: Pronunciation approximations, useful for acronyms, brand names, mixed-language calls, and repeated ASR mistakes.

`observed_asr_variants`: Transcript spellings that were seen in real ASR output or explicitly marked as hypotheses. Include the source and confidence.

`context_keywords`: Nearby words that raise a candidate for review. These should not trigger automatic rewriting.

`possible_contexts`: Plausible roles for the term. Keep them probabilistic because a term can be a product in one call, a database object in another, and a process state in a third.

`ambiguity_note`: Explain how the term can be confused.

`sources`: Link to local docs, code files, prior transcript segment IDs, tickets, or user-provided notes.

`confidence`: Use `high`, `medium`, `low`, or `candidate`.

## Agent Discovery Procedure

When asked to create a private glossary:

1. Ask the user which local sources may be inspected.
2. Search only authorized sources.
3. Prefer structured sources first: docs, READMEs, schemas, enums, API specs, migration names, and previous transcript artifacts.
4. Extract candidates with their evidence path and category.
5. Add pronunciation aliases only when the term is likely to be spoken ambiguously or the user/transcript provides evidence.
6. Add observed ASR variants only when a transcript contains the variant or mark it clearly as `hypothesis`.
7. Keep unresolved terms as `unresolved_vocabulary` rather than forcing a false category.
8. Show the user a review summary before treating a candidate as high confidence.

