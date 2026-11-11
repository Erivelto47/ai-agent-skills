# Engineering Report Artifacts

Turn an engineering status update or code review into a polished, scannable deliverable — a visual page or portable Markdown — instead of leaving the reader to reconstruct status from a chat thread. The skill covers two distinct report shapes built on the same information architecture.

## Why use it?

A phased implementation or a code review buried in chat forces every reader to re-read the whole thread to find out what matters. This skill gives each shape a fixed, deliberate structure — a progress tracker with phase status badges and a decision map, or a code review with real snippets, consequence, and connections per finding — and requires real content (actual phase names, actual file paths and line numbers) rather than placeholder text.

## What it does

- Confirms which shape fits before writing anything: a **status tracker** for a multi-session, multi-phase implementation, or a **code review** for evaluating a diff, PR, or existing implementation.
- Selects a delivery mode deliberately: a visual page (private Claude Artifact, or a standalone static HTML file on Codex), portable Markdown, or — only on explicit request — a published page.
- Builds the status tracker from eyebrow, goal, progress card, numbered phase list with status badges, and an optional plain-language decision-map diagram.
- Builds the code review from a severity summary strip and one finding card per issue — real snippet, why it matters, connections, and suggestion — including notes for good patterns worth preserving, not only complaints.
- Overwrites the same Artifact or file on update, so the reader always has one current view instead of a pile of stale snapshots.

See [SKILL.md](SKILL.md) for the full section-by-section contract and delivery-mode rules. Reference implementations:

- [references/status-tracker-template.html](references/status-tracker-template.html) — a full working status-tracker example with generic content and its own color/type pairing.
- [references/code-review-template.html](references/code-review-template.html) — a full working code-review example, same rule: read for structure, not for its example findings.

## Boundaries

This skill never invents phases, findings, or code absent from the actual diff or plan, and it never reuses a previous instance's palette or type pairing wholesale — visual design is calibrated to the subject each time, with or without `artifact-design` available. It excludes credentials and unnecessary sensitive data, keeps local HTML local, and invokes a publishing step (such as Codex Sites) only after the user explicitly requests publication or sharing.

## Fits after

This skill is a natural last step after [meeting-evidence-normalizer](../meeting-evidence-normalizer/README.md)'s code-investigation stage, or after [implementation-from-discovery](../implementation-from-discovery/README.md) produces a validation report worth presenting — it formats already-verified findings, it does not generate them.
