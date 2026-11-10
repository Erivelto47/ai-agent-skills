---
handoff_format: 1
title: Sync about a fictional report-export feature
date: 2026-01-15
type: call
audience: business+ai
language: en
status: shared
shareable: true
revalidate_when: after the vendor confirms the export limits, or after any change to the export module
min_agent_tier: frontier
repositories:
  - name: example-app
    clone_url: https://example.invalid/example-org/example-app.git
    base_branch: main
---

# Handoff: sync about a fictional report-export feature

**Names used here:** only names that appear in the shared diagram are written. People are not named. The two sides of the conversation are called **our side** (the team that builds the app) and **their side** (the vendor that provides the export service); that split is inferred from what was said. Treat every statement as "said in the meeting", not as validated fact or a signed decision.

## Summary

Our side and the vendor met to agree how customers will download their monthly reports. Two designs were discussed: one export per report type, each with its own settings, or a single export service that every report type goes through. The single service was chosen, because it avoids duplicated settings and keeps one place to apply limits. The consequence is mostly contractual: the usage limits now belong to the whole service instead of each report type, so both legal teams need to review the agreement.

Two points stayed open. The first is whether very large reports can be delivered in one file or must be split; the vendor will check with its storage provider and answer within the week. The second is how a customer is told that an export is still being prepared. Nothing in this document is approved work: the actions below were only mentioned.

## 1. Themes at a glance

| # | Theme | State after the meeting |
|---|---|---|
| 1 | Export architecture (per report type or single service) | Single service chosen; contract impact open |
| 2 | Large reports (size limit, splitting) | Open; depends on the vendor's storage provider |
| 3 | Notifying the customer that an export is ready | Informational; approach not agreed |

## 2. Export architecture (theme 1)

The diagram was shared on screen as a quick sketch, halfway through the discussion. The topic started earlier: how to support a second report family without duplicating settings.

```text
Option A (not chosen)                 Option B (CHOSEN)

Vendor ── Export 1 ── Reports X       Vendor ── Export service ──┬─ Reports X
   └──── Export 2 ── Reports Y                                   └─ Reports Y
```

**What the diagram shows.**
- **Option A, not chosen:** the vendor exposes one export per report family. Each export has its own settings and its own limits, so a customer who uses both families ends up with two sets of settings.
- **Option B, chosen:** one export service sits in front of both report families. Settings and limits are defined once, at the service level.

**How the choice appeared in the conversation** (there was no formal "decision" sentence; this is the sequence that supports it):
- Their side said that a single entry point would be simpler to operate.
- Our side said it preferred one set of limits for the whole service.
- Both sides confirmed that Option B is the one they are working toward.

**Arguments raised**
- Technical: one set of settings avoids drift between report families.
- Legal: the usage limits in the agreement are written per report type today and would have to be rewritten for the whole service.

## 3. Decisions and understandings (as said in the meeting)

Not signed, not validated by legal. Status: **stated as agreed** / **tentative** / **unconfirmed** / **contradiction**.

- [stated as agreed] The single export service (Option B) is the target design.
- [tentative] Limits will be defined once for the whole service. Their side said the agreement would need an amendment; our side has not reviewed this.
- [unconfirmed] Reports above a certain size may need to be split into several files. The size was mentioned but not stated clearly.
- [contradiction] Early in the meeting, the status endpoint was described as "not available yet"; later it was described as "already in the test environment". Both are kept; the later statement is more specific.

## 4. Open questions

| # | Question | Who answers | Verifiable in code |
|---|---|---|---|
| 1 | What is the maximum report size for a single file, and what happens above it? | partner (vendor, after checking its storage provider) | no |
| 2 | Does the existing export module already split large reports? | code/docs | yes |
| 3 | How does a customer learn an export is ready: email, in-app message, or polling? | internal | in part |
| 4 | Does the amendment to the agreement change the limits we already rely on? | legal | no |

## 5. Actions mentioned (none approved)

| Who (inferred) | Action | When |
|---|---|---|
| Their side | Check size limits with the storage provider and reply | within the week |
| Our side | Try the new status endpoint in the test environment and report oddities | now |
| Both sides | Ask their legal teams to schedule a joint session on the amendment | no date |

## 6. AI section (mandatory)

Read-only. No action in this document is authorized and no code change was approved.

### 6.1 Code context

- Repository: `example-app`; base branch: `main`.
- Relevant modules:
  - `exports/`: builds and delivers report files.
  - `notifications/`: tells customers about events.
  - `vendor-client/`: calls the vendor's service.
- Specs and ADRs live under `docs/specs/` and `docs/adr/`.
- Does not exist in the repository: a generated code map; do not look for one.
- Work outside the base branch: none known. "Not found on the base branch" does not mean "does not exist".

### 6.2 Glossary term to code

| Term in the conversation | Meaning in the conversation | In the code | How confirmed |
|---|---|---|---|
| Export service | The single entry point for downloading reports | Not found; the module `exports/` has one class per report family | to confirm |
| Report family | A group of reports that share a layout | `ReportKind` enum | to confirm |
| Ready | The file can be downloaded | `ExportStatus.COMPLETED` (the code also has `PENDING` and `FAILED`) | to confirm |

### 6.3 Research questions

| ID | Question (business terms) | Where to start | Why it matters |
|---|---|---|---|
| Q1 | How are exports produced today: one path per report family, or already a shared path? What would change for a single service? | `exports/`, `docs/adr/` | Export architecture (section 2) |
| Q2 | Is there any size limit or file splitting? Where is the limit configured? | `exports/`, configuration files | Open question 2 |
| Q3 | How is a customer told that an export is ready today? | `notifications/`, `exports/` | Open question 3 |

### 6.4 Pre-verification

Checked in `example-app@a1b2c3d` on 2026-01-15: the module has one exporter class per report family and no shared entry point. Nothing else was checked. Not reviewed by the owner; to be confirmed.

### 6.5 Traps and limits

- Do not state that a single export service already exists: the code has one path per report family.
- Do not promise a maximum file size; it depends on the vendor's answer.
- Do not confuse "report family" (conversation) with `ReportKind` (code) without checking they cover the same reports.

### 6.6 Implementation

Not applicable: no change was approved. Any implementation needs its own discovery and the owner's approval.
