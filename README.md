# AI Agent Skills

Reusable, public Agent Skills for Codex, Claude Code, and other tools that support the `SKILL.md` skill format.

## Skills

- `meeting-evidence-normalizer`: Turn local meeting recordings or existing transcript JSON files into traceable meeting evidence. Its main differentiator is glossary-aware normalization by canonical name, context, pronunciation, and observed ASR variants without rewriting uncertain audio as fact.

## Install Locally

Clone this repository, then expose the skill folder to your agent.

Codex-compatible local skills:

```bash
mkdir -p ~/.agents/skills
ln -s "$PWD/skills/meeting-evidence-normalizer" ~/.agents/skills/meeting-evidence-normalizer
```

Claude Code local skills:

```bash
mkdir -p ~/.claude/skills
ln -s "$PWD/skills/meeting-evidence-normalizer" ~/.claude/skills/meeting-evidence-normalizer
```

Project-scoped Claude Code skill:

```bash
mkdir -p .claude/skills
ln -s "$PWD/skills/meeting-evidence-normalizer" .claude/skills/meeting-evidence-normalizer
```

## Private Configuration

Do not commit real meeting outputs, private glossary files, credentials, or project-specific terminology to this public repository.

Use a private config file outside the repo:

```bash
cp skills/meeting-evidence-normalizer/config/profile.example.yaml ~/meeting-normalizer-profile.yaml
```

Then edit the private file with your local transcript command, output paths, and private glossary path.

## Validate

Run the repository checks:

```bash
python3 -m py_compile skills/meeting-evidence-normalizer/scripts/*.py
python3 -m unittest discover -s skills/meeting-evidence-normalizer/tests -v
python3 scripts/validate_skill.py skills/meeting-evidence-normalizer
```

