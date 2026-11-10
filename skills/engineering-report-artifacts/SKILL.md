---
name: engineering-report-artifacts
description: Create a polished engineering status tracker or code-review report as a visual page or portable Markdown. Use when a human needs a scannable progress or review deliverable for a project, not a one-off chat answer.
---

# Engineering Report Artifacts

Two report shapes serve the same audience: someone tracking engineering work who wants a scannable deliverable instead of reconstructing status from a chat thread. Select the report shape, then select its delivery mode deliberately.

## Preconditions

- Confirm which shape fits: a status tracker for a multi-session, multi-phase implementation someone is following along with; a code review for evaluating a diff, PR, or existing implementation.
- Gather real content before writing the deliverable — actual phase names and their current state, or actual file paths, line numbers, and code snippets from the diff. Never fill a section with placeholder text.
- If `artifact-design` is available, load it before creating a visual page. If it is unavailable, continue: reuse the *information architecture* below, never a palette or type pairing lifted wholesale from a reference file.

## Delivery mode

- **Visual page:** Use when the user asks for a visual page, HTML, dashboard, status page, or review page.
  - **Claude Code:** Publish a private Claude Artifact.
  - **Codex:** Create a polished, standalone static HTML file in a durable, task-owned location outside the checked-out product repository. Keep it local by default and give the user its path or preview.
- **Markdown:** Use when the user explicitly asks for Markdown, documentation, a technical record, or content they can send to their team. This is available on both Claude Code and Codex. Write it to the surface's normal report location.
- **Published page:** Use only when the user explicitly asks to publish or share the report. On Codex, use Sites to build and host the visual page; do not infer publishing permission from a request for local HTML.

## Language

Write report prose in the language requested by the user or used in the conversation. Keep code snippets, identifiers, file paths, and commit or ticket references as they appear in the source.

## Status tracker

Use for a phased `implementation-from-discovery` run spanning multiple sessions, where a human wants to see progress without re-reading the whole thread.

Sections, in order:

- Eyebrow: ticket id and repo/project name.
- H1: the plain-language goal, not the raw ticket title.
- Dek: one short paragraph on why this work exists.
- Progress card: "N of M phases done" plus a progress bar.
- Phase list: numbered rows, each with a one-line plain-language title, a short note, and a done / active / pending / blocked status badge.
- Optional decision-map Mermaid diagram, scoped to business logic only — strip locking, transaction, and persistence jargon; show plain branching a non-engineer can follow.
- A callout for the current blocker or next step, when one exists.

When the visual page is updated, overwrite the same Artifact or static HTML file so the reader has one current status view.

Reference implementation: [references/status-tracker-template.html](references/status-tracker-template.html) — a full working example with generic content, deliberately in its own color and type pairing. For a visual page, read it for component patterns and create fresh colors and typography for the actual subject. Do not publish its example ticket, phases, or copy verbatim for a real project.

## Code review

Use for reviewing a diff, PR, or existing implementation where the reader needs more than a flat list of complaints — actual context per finding, the way a careful reviewer would explain it in person.

Sections, in order:

- Eyebrow: ticket id and repo/project name.
- H1 + dek: what is being reviewed and why.
- Summary strip: counts by severity (critical / major / minor / note), scannable at a glance.
- Finding list, one card per finding, each with four fixed parts:
  - The real code snippet, with the problematic line highlighted — never paraphrased.
  - Why it matters: the concrete consequence, not "this is bad."
  - Connections: what calls this, what it depends on, what else shares the same invariant.
  - Suggestion: an objective next step, or "does not block" when it is only a note.
- Severity is a color on the card's left edge, not an emoji or icon — the list should be scannable without reading every line.
- Findings without a real problem belong too — a good pattern worth calling out, a non-obvious invariant worth preserving — tagged as a note. A review that only lists complaints misses what should not be touched.
- Optional dependency-map Mermaid diagram for a finding whose blast radius needs a picture, not a paragraph.
- A closing callout is optional; use it for anything that does not block the merge but should stay tracked, or to summarize how the finding-card shape works for whoever reuses the page later.

Reference implementation: [references/code-review-template.html](references/code-review-template.html) — same rule: read it for structure and token architecture, not for its example findings.

## Boundaries

- Exclude credentials and unnecessary sensitive data. Respect the user’s requested location and sharing boundaries for any source content.
- Do not reuse a previous instance's palette or type pairing wholesale; calibrate the visual design to the subject whether or not `artifact-design` is available.
- Do not invent phases, findings, or code that is not in the actual diff or plan.
- Keep local HTML local. Invoke Sites only after the user explicitly requests publication or sharing.

## Example

Reviewing a document search feature: read the changed methods, identify evidence-backed findings, and build the code-review shape with real file paths and line numbers. The reference examples are fictional and must not be presented as findings in a real review.
