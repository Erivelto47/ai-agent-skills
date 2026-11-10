---
handoff_format: 1
title: <short title>
date: <YYYY-MM-DD>
type: call | discovery | work-in-progress
audience: business+ai
language: en
status: draft
shareable: true
revalidate_when: <event or date>
min_agent_tier: frontier
repositories:
  - name: <repository>
    clone_url: <clone address or "ask the team">
    base_branch: <branch>
---

# Handoff: <title>

**Names used here:** <naming rule: only names confirmed by a diagram, document, or code are written; the rest were omitted.> Treat every statement as "said", not as validated.

## Summary

<One page at most, in prose: context, what was discussed, what was decided or left open, what happens next. No timestamps and no unexplained jargon.>

## 1. Themes at a glance

| # | Theme | State |
|---|---|---|
| 1 | | |

## 2. <Main theme>

<Description, alternatives, what was chosen, arguments.>

<Image, if any, followed by its text equivalent:>
![Short description](file.png)

**What the image shows:** <complete text equivalent.>

## 3. Decisions and understandings

Status: **stated as agreed** / **tentative** / **unconfirmed** / **contradiction**.

- [stated as agreed] ...
- [tentative] ...

## 4. Open questions

| # | Question | Who answers | Verifiable in code |
|---|---|---|---|
| 1 | | code/docs, partner, legal, internal | yes / in part / no |

## 5. Actions mentioned (none approved)

| Who (inferred) | Action | When |
|---|---|---|

## 6. AI section (mandatory)

Read-only. No action in this document is authorized.

### 6.1 Code context

- Repository: <name>; base branch: <branch>.
- Relevant modules: <list, one sentence each>.
- Where specs and ADRs live: <paths>.
- Does not exist in the repository: <what the agent should not look for>.
- Work outside the base branch: <branches or "none known">.

### 6.2 Glossary term to code

| Term in the conversation | Meaning in the conversation | In the code | How confirmed |
|---|---|---|---|

### 6.3 Research questions

| ID | Question (business terms) | Where to start | Why it matters |
|---|---|---|---|
| Q1 | | | |

### 6.4 Pre-verification (optional)

Checked in <repository>@<commit> on <date>: <what was seen>. Not reviewed by the owner; to be confirmed.

### 6.5 Traps and limits

- <What the business reader must not promise.>
- <Likely false positives.>
- "Not found on the base branch" does not mean "does not exist".

### 6.6 Implementation

<"Not applicable: no change was approved." Or, only for a technical audience and `shareable: false`, the working rules for whoever changes code.>
