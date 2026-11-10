# Handoff Guide

A handoff turns a meeting (or any investigation) into a document that another person and that person's AI agent can act on. It is built from the normalizer outputs (`evidence.json`, `uncertainties.json`, `meeting.md`), but it is a different artifact: `meeting.md` summarizes evidence for whoever processed the meeting; a handoff is written for someone who was not there and may never see the recording.

Use `references/handoff-template.md` as the skeleton and `references/business-agent-prompt.md` when the reader is a non-technical person who will use an agent to check the handoff against a codebase.

## 1. Readers

- **Human reader**, often not technical, who wants to understand the topic and speak about it with confidence. Reads the summary and the numbered sections.
- **AI agent** of that person (or of a developer), who must go to the code and documentation, check what was said, and answer the open questions. Reads the mandatory AI section.
- **Implementing agent** (optional, technical audience only). Kept separate and never included in a handoff meant for business readers (see 5.6).

## 2. Principles

1. **Claims, not facts.** What was said in a meeting is not a decision and not true until checked. Every point carries a status (see 4.1).
2. **Shareable by default.** The handoff does not cite recordings, audio timestamps, local paths, or files the reader does not have. Segment ids, the recording reference, and output directories go in a separate private companion file (`_private-sources.md`) that is never sent.
3. **Names only when confirmed.** People, companies, and products appear only if a confirmable artifact supports them (a diagram, a document, the code) or the user confirmed them in chat. Never infer a name from a voice or a guess. When unsure, use neutral role labels such as "our side" and "their side" and say the split is inferred.
4. **Every drawing has text.** Each image comes with a complete text equivalent, for agents that cannot read images and for audit.
5. **Tied vocabulary.** Terms from the conversation that mean something else in the code go in the glossary of the AI section, with the meaning on each side.
6. **Every open question says who answers it.** Code and docs, a partner, legal, or internal. The agent routes by that field.
7. **Dated state.** The handoff says when it was written and what event makes it suspect.

## 3. Required front matter

```yaml
---
handoff_format: 1
title: <short title>
date: <YYYY-MM-DD>
type: call | discovery | work-in-progress
audience: business+ai | technical+ai
language: <language code, e.g. en, pt-BR>
status: draft | shared | superseded
shareable: true | false
revalidate_when: <event or date that makes the content suspect>
min_agent_tier: frontier
repositories:
  - name: <repository name>
    clone_url: <clone address, if shareable>
    base_branch: <branch to research on>
---
```

`min_agent_tier: frontier` means the agent must be a high-capability model (for example Claude, Codex, Gemini, or equivalent), not a small local model. The task requires reading code, cross-checking specs, and not inventing. If the user only has a small local model, say so and suggest a stronger agent instead of proceeding.

## 4. Body structure

Fixed order. Numbers are stable so an agent can cite "section 5".

0. **Summary** (unnumbered, before everything). One page at most, in prose, for a human to understand the whole subject: context, what was discussed, what was decided or left open, what happens next. No timestamps and no unexplained jargon.
1. **Themes at a glance.** Table: theme, state.
2. **Theme sections** (as many as the subject needs): description, alternatives, what was chosen, arguments. Diagrams here, each with its text equivalent.
3. **Decisions and understandings.** List with a status (4.1).
4. **Open questions.** Table: question, **who answers**, **verifiable in code** (yes, in part, no).
5. **Actions mentioned.** Who (inferred), action, when. None is approved.
6. **AI section** (mandatory, always the last numbered section, see 5).

### 4.1 Status vocabulary

- **stated as agreed**: both sides confirmed it.
- **tentative**: said by one side only, or with a caveat.
- **unconfirmed**: inferred, or heard ambiguously.
- **contradiction**: two points that oppose each other; keep both.

Actions are always "mentioned in the meeting", never "approved". Labels may be localized to the handoff language; keep the four meanings.

## 5. AI section (mandatory)

It holds only what is specific to the topic. General rules (read-only, no secrets, how to clone) live in the business-agent prompt, not here. In the template it is section 6; with more theme sections it takes the next number, but it stays last.

- **5.1 Code context.** Repository, base branch, modules, where specs and ADRs live, what does not exist in the repository (for example an unversioned code map). If relevant work lives outside the base branch, name the branch and say that "not found on the base branch" does not mean "does not exist".
- **5.2 Glossary term to code.** Table: term in the conversation, meaning in the conversation, term or entity in the code (if known), how it was confirmed. This prevents confusing, for example, an entity named in the conversation with a different thing of the same name in the code.
- **5.3 Research questions.** Numbered list (`Q1`, `Q2`, ...), each with the question in business terms, where to start looking, and why it matters. This is the agent's script. If the handoff does not list them, the agent must not invent them.
- **5.4 Pre-verification (optional).** If someone already checked something in the code, record what, at which commit, on which date. Without it the reader assumes nothing was checked.
- **5.5 Traps and limits.** What the business reader must not promise, likely false positives (same name, other meaning), known contradictions.
- **5.6 Implementation (optional, technical audience only).** Working rules for whoever changes code: commits, specs, builds. Never in a handoff with `shareable: true` aimed at business readers; write "Not applicable: no change was approved" instead. Nothing in a handoff authorizes an action.

If the handoff has no AI section it is incomplete, and a generic business-agent prompt cannot work with it.

## 6. How to produce one

1. Process the meeting with the normalizer and validate the output directory.
2. Read `meeting.md`, `evidence.json`, and `uncertainties.json`. Do not re-listen or re-transcribe unless the user asks.
3. Ask the user about anything the handoff needs and the evidence cannot settle: which names are confirmed, which diagram was chosen, who the two sides are. Do not guess.
4. Draft from `references/handoff-template.md`. Carry claims over with a status; carry contradictions and "will validate later" promises over as open questions with a "who answers".
5. Write the research questions and glossary from what the user and the code say, not from the meeting alone. If the code is not at hand, mark the glossary column "to confirm" instead of filling it from memory.
6. Write the private companion file with the recording reference, output directory, and segment ids behind each section. Keep it out of anything shared.
7. Validate: `python3 scripts/validate-handoff.py <handoff.md>`. Fix every error; read each warning.
8. Do not commit or send the handoff without the user's explicit go-ahead.

## 7. Delivery checklist

- No private paths, no recording or timestamp references, no evidence file names (the validator flags these when `shareable: true`).
- No names that were not confirmed.
- Every image has its text equivalent next to it.
- The AI section is last and has the research questions.
- `revalidate_when` is concrete.
- The reader has what the prompt needs: read access to the repository, an agent with file access, and the handoff plus the prompt.
