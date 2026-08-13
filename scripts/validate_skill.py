#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("Usage: validate_skill.py <skill-dir>", file=sys.stderr)
        return 2
    skill_dir = Path(argv[0])
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        print("INVALID: SKILL.md missing", file=sys.stderr)
        return 1
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        print("INVALID: SKILL.md must start with YAML frontmatter", file=sys.stderr)
        return 1
    try:
        _, frontmatter, _ = text.split("---", 2)
    except ValueError:
        print("INVALID: frontmatter must be closed", file=sys.stderr)
        return 1
    fields: dict[str, str] = {}
    for line in frontmatter.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    name = fields.get("name", "")
    description = fields.get("description", "")
    if not NAME_RE.match(name):
        print(f"INVALID: bad skill name {name!r}", file=sys.stderr)
        return 1
    if name != skill_dir.name:
        print(f"INVALID: skill name {name!r} must match directory {skill_dir.name!r}", file=sys.stderr)
        return 1
    if not description:
        print("INVALID: description missing", file=sys.stderr)
        return 1
    print("Skill is valid!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

