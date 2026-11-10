# AI Agent Skills

Reusable, public Agent Skills for Codex, Claude Code, and other tools that support the `SKILL.md` skill format.

## Skills

- `meeting-evidence-normalizer`: Turn local meeting recordings or existing transcript JSON files into traceable meeting evidence. Its main differentiator is glossary-aware normalization by canonical name, context, pronunciation, and observed ASR variants without rewriting uncertain audio as fact. It also includes a handoff standard (template, validator, and a generic prompt for non-technical readers) that turns processed evidence into a shareable document with a mandatory AI section.
- `spring-docs`: Ground Spring Framework, Spring Boot, Spring Data, and Spring project guidance in a local documentation index exposed through a compatible `spring-docs-mcp` server.
- `codebase-discovery`: Map existing code paths, data flow, integrations, persistence, tests, and evidence before implementation.
- `implementation-from-discovery`: Turn validated findings into minimal, tested, reviewable changes.
- `runtime-debugging`: Diagnose runtime failures through reproduction, evidence, hypotheses, fixes, and regression checks.
- `multi-agent-orchestration`: Coordinate bounded agent roles, capabilities, ownership, evidence, and validation gates.
- `engineering-report-artifacts`: Create a polished engineering status tracker or code-review report — a phase/status tracker for a multi-session implementation, or a code-review findings report with a real snippet, why it matters, and its connections per finding. Works on both Claude Code (a private Artifact) and Codex (a local static HTML file or Markdown, per its Delivery mode section).

## Install Locally

Clone this repository, then expose the skill folder to your agent.

Generic local skills folder:

```bash
mkdir -p ~/.agents/skills
for skill in skills/*; do ln -sfn "$PWD/$skill" ~/.agents/skills/"$(basename "$skill")"; done
```

Claude Code local skills:

```bash
mkdir -p ~/.claude/skills
for skill in skills/*; do ln -sfn "$PWD/$skill" ~/.claude/skills/"$(basename "$skill")"; done
```

Codex local skills:

```bash
mkdir -p ~/.codex/skills
for skill in skills/*; do ln -sfn "$PWD/$skill" ~/.codex/skills/"$(basename "$skill")"; done
```

Project-scoped Claude Code skill:

```bash
mkdir -p .claude/skills
for skill in skills/*; do ln -sfn "$PWD/$skill" .claude/skills/"$(basename "$skill")"; done
```

## Handoff Documents

After a meeting is normalized, `meeting-evidence-normalizer` can also help produce a **handoff**: a document for someone who was not there, and for that person's AI agent. It is built from `meeting.md`, `evidence.json`, and `uncertainties.json`, but it is a different artifact: shareable by default, with every point marked as said rather than validated, and with a mandatory AI section that tells an agent how to check the claims against a codebase.

A handoff has two readers. A (often non-technical) human reads the summary and the numbered sections. The reader's agent reads the AI section, goes to the repository, and answers the open questions. A generic prompt (`references/business-agent-prompt.md`) lets a non-technical reader hand the handoff to a capable agent that clones the repository, checks out the base branch, answers the research questions read-only, and then answers the reader's own follow-ups.

### What a handoff looks like

```text
---                                  front matter: format, date, type, audience, language,
handoff_format: 1                    shareable, revalidate_when, min_agent_tier,
...                                  repositories (name, clone_url, base_branch)
---

# Handoff: <title>
Names used here: ...                 only confirmed names; the rest omitted on purpose

## Summary                           one page of prose for a human (unnumbered)
## 1. Themes at a glance             table: theme, state after the meeting
## 2. <Theme section>                description, alternatives, what was chosen;
                                     every diagram has a text equivalent
## 3. Decisions and understandings   each marked: stated as agreed / tentative /
                                     unconfirmed / contradiction
## 4. Open questions                 table: question, who answers, verifiable in code
## 5. Actions mentioned              none approved
## 6. AI section (mandatory, last)
   ### 6.1 Code context              repository, base branch, modules, where specs live
   ### 6.2 Glossary term to code     conversation term vs. what the code calls it
   ### 6.3 Research questions        Q1, Q2, ... the agent's script
   ### 6.4 Pre-verification          what was already checked, at which commit and date
   ### 6.5 Traps and limits          what must not be promised
   ### 6.6 Implementation            "Not applicable" for business readers
```

A short excerpt of the AI section, from the generic example:

```markdown
### 6.2 Glossary term to code

| Term in the conversation | Meaning in the conversation | In the code | How confirmed |
|---|---|---|---|
| Export service | The single entry point for downloading reports | Not found; `exports/` has one class per report family | to confirm |

### 6.3 Research questions

| ID | Question (business terms) | Where to start | Why it matters |
|---|---|---|---|
| Q1 | How are exports produced today: one path per report family, or a shared path? | `exports/`, `docs/adr/` | Export architecture (section 2) |

### 6.5 Traps and limits

- Do not state that a single export service already exists: the code has one path per report family.
```

The full, neutral example, with a fictional meeting and repository, is in [`examples/neutral-handoff/handoff.md`](examples/neutral-handoff/handoff.md). The private companion file that keeps recording references and evidence ids out of the shared document is shown in [`examples/neutral-handoff/_private-sources.example.md`](examples/neutral-handoff/_private-sources.example.md).

### Using it

1. Read `skills/meeting-evidence-normalizer/references/handoff-guide.md` and start from `handoff-template.md` in the same folder.
2. Draft from the normalizer outputs, ask the user to confirm names and choices instead of inferring them, and keep recording references in the private companion file.
3. Validate the result:

   ```bash
   python3 skills/meeting-evidence-normalizer/scripts/validate-handoff.py path/to/handoff.md
   ```

   It checks the front matter, the numbered sections, and that the AI section is last and has research questions. When `shareable: true`, it also reports private paths and evidence file names as errors, and recording timestamps or mentions as warnings. The checks use numbering rather than heading words, so a handoff in another language validates the same way.
4. Give a non-technical reader the handoff and the fenced block of `references/business-agent-prompt.md`. They need read access to the repository and a capable agent that can read files on their machine; a small local model or a plain chat without file access is not enough.

A handoff authorizes no action. The prompt keeps the reader's agent read-only, but what enforces that is the agent's permission mode.

## Private Configuration

Do not commit real meeting outputs, private glossary files, credentials, or project-specific terminology to this public repository.

Use a private config file outside the repo:

```bash
cp skills/meeting-evidence-normalizer/config/profile.example.yaml ~/meeting-normalizer-profile.yaml
```

Then edit the private file with your local transcript command, output paths, and private glossary path.
For project-local use, place the private config at one of these paths in your project:

```text
.meeting-evidence-normalizer.yaml
.meeting-evidence-normalizer/config.yaml
.agents/meeting-evidence-normalizer/profile.yaml
```

For user-level use across projects, place or symlink the private config at:

```text
~/.config/meeting-evidence-normalizer/profile.yaml
~/.meeting-evidence-normalizer.yaml
```

## Validate

Run the repository checks:

```bash
python3 -m py_compile skills/meeting-evidence-normalizer/scripts/*.py
python3 -m unittest discover -s skills/meeting-evidence-normalizer/tests -v
python3 scripts/validate_skill.py skills/meeting-evidence-normalizer
```

`ffmpeg` is required to use `transcription.chunking.enabled: true` (see
`skills/meeting-evidence-normalizer/SKILL.md`) and to run the chunking test cases in
`test_process_meeting.py`. Those tests skip automatically when `ffmpeg` is not on `PATH`;
everything else in the suite runs without it.
