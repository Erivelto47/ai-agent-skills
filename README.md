# AI Agent Skills

Reusable, public Agent Skills for Codex, Claude Code, and other tools that support the `SKILL.md` skill format.

## Skills

- `meeting-evidence-normalizer`: Turn local meeting recordings or existing transcript JSON files into traceable meeting evidence. Its main differentiator is glossary-aware normalization by canonical name, context, pronunciation, and observed ASR variants without rewriting uncertain audio as fact.
- `spring-docs`: Ground Spring Framework, Spring Boot, Spring Data, and Spring project guidance in a local documentation index exposed through `spring-docs-mcp`.

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

Project-scoped Claude Code skill:

```bash
mkdir -p .claude/skills
for skill in skills/*; do ln -sfn "$PWD/$skill" .claude/skills/"$(basename "$skill")"; done
```

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
