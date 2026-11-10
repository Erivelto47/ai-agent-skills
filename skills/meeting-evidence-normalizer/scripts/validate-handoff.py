#!/usr/bin/env python3
"""Validate the structure and shareability of a handoff document.

Checks the front matter, the numbered body sections, the mandatory AI section
(always the last numbered section, with research questions), and, when the
handoff is marked shareable, that it carries no private paths or references to
meeting evidence files. Structure checks are language-neutral: they rely on
numbering, not on heading words.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


REQUIRED_KEYS = [
    "handoff_format",
    "title",
    "date",
    "type",
    "audience",
    "language",
    "status",
    "shareable",
    "revalidate_when",
    "min_agent_tier",
]
ENUMS = {
    "type": {"call", "discovery", "work-in-progress"},
    "audience": {"business+ai", "technical+ai"},
    "status": {"draft", "shared", "superseded"},
    "shareable": {"true", "false"},
    "min_agent_tier": {"frontier"},
}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$")
H2_RE = re.compile(r"^##\s+(?:(\d+)\.\s+)?(.+?)\s*$")
H3_RE = re.compile(r"^###\s+(\d+)\.(\d+)\b")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
PLACEHOLDER_RE = re.compile(r"<[A-Za-z][^<>\n]{1,60}>")

PRIVATE_PATH_RE = re.compile(r"(?:/Users/|/home/|[A-Za-z]:\\|~/)")
EVIDENCE_FILE_RE = re.compile(
    r"\b(?:evidence\.json|uncertainties\.json|manifest\.json|meeting\.md|"
    r"transcription\.(?:raw|normalized|analysis)\.json)\b"
)
TIMESTAMP_RE = re.compile(r"\b\d{1,2}:\d{2}:\d{2}\b|(?:\bat\b|@)\s*\d{1,2}:\d{2}\b", re.IGNORECASE)
RECORDING_RE = re.compile(r"\b(?:recording|recorded|transcript|transcription)\b", re.IGNORECASE)


def split_front_matter(text: str) -> tuple[list[str] | None, list[str]]:
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None, lines
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return lines[1:index], lines[index + 1 :]
    return None, lines


def parse_front_matter(lines: list[str]) -> tuple[dict[str, str], list[dict[str, str]]]:
    fields: dict[str, str] = {}
    repositories: list[dict[str, str]] = []
    in_repositories = False
    for raw in lines:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if not raw.startswith((" ", "\t")):
            in_repositories = False
            match = KEY_RE.match(raw)
            if match:
                key, value = match.group(1), match.group(2).strip()
                if key == "repositories":
                    in_repositories = True
                else:
                    fields[key] = value.strip("'\"")
            continue
        if not in_repositories:
            continue
        stripped = raw.strip()
        if stripped.startswith("- "):
            repositories.append({})
            stripped = stripped[2:].strip()
        match = KEY_RE.match(stripped)
        if match and repositories:
            repositories[-1][match.group(1)] = match.group(2).strip().strip("'\"")
    return fields, repositories


def outside_fences(lines: list[str]) -> list[tuple[int, str]]:
    result: list[tuple[int, str]] = []
    fenced = False
    for number, line in enumerate(lines, start=1):
        if FENCE_RE.match(line):
            fenced = not fenced
            continue
        if not fenced:
            result.append((number, line))
    return result


def check_front_matter(fields: dict[str, str], repositories: list[dict[str, str]], errors: list[str]) -> None:
    for key in REQUIRED_KEYS:
        if not fields.get(key):
            errors.append(f"front matter: missing or empty '{key}'")
    if fields.get("handoff_format") and fields["handoff_format"] != "1":
        errors.append(f"front matter: unsupported handoff_format {fields['handoff_format']!r} (expected 1)")
    if fields.get("date") and not DATE_RE.match(fields["date"]):
        errors.append(f"front matter: date {fields['date']!r} must be YYYY-MM-DD")
    for key, allowed in ENUMS.items():
        value = fields.get(key)
        if value and value not in allowed:
            errors.append(f"front matter: {key} {value!r} must be one of {sorted(allowed)}")
    if not repositories:
        errors.append("front matter: 'repositories' needs at least one entry with name and base_branch")
    for index, repo in enumerate(repositories, start=1):
        for key in ("name", "base_branch"):
            value = repo.get(key, "")
            if not value or PLACEHOLDER_RE.fullmatch(value):
                errors.append(f"front matter: repositories[{index}] is missing a real '{key}'")


def check_body(body: list[str], errors: list[str], warnings: list[str]) -> None:
    visible = outside_fences(body)
    headings: list[tuple[int, int | None, str]] = []
    for number, line in visible:
        match = H2_RE.match(line)
        if match:
            headings.append((number, int(match.group(1)) if match.group(1) else None, match.group(2)))

    numbered = [(line, num) for line, num, _ in headings if num is not None]
    first_numbered_line = numbered[0][0] if numbered else None
    has_summary = any(
        num is None and (first_numbered_line is None or line < first_numbered_line) for line, num, _ in headings
    )
    if not has_summary:
        errors.append("body: missing the unnumbered summary section before section 1")
    if len(numbered) < 4:
        errors.append("body: expected at least four numbered sections (themes, decisions, open questions, AI section)")
        return
    numbers = [num for _, num in numbered]
    if numbers != list(range(1, len(numbers) + 1)):
        errors.append(f"body: numbered sections must be consecutive from 1, found {numbers}")
    if numbers[0] != 1:
        return

    ai_line, ai_number = numbered[-1]
    ai_text_lines = [text for number, text in visible if number > ai_line]
    subsections = [
        match for match in (H3_RE.match(text) for text in ai_text_lines) if match and int(match.group(1)) == ai_number
    ]
    if len(subsections) < 4:
        errors.append(
            f"AI section (last numbered section, {ai_number}): expected at least four '### {ai_number}.N' subsections "
            "(code context, glossary, research questions, traps and limits)"
        )
    ai_blob = "\n".join(ai_text_lines)
    if not re.search(r"\bQ1\b", ai_blob):
        errors.append(f"AI section ({ai_number}): no research question 'Q1' found")

    prose = [text for _, text in visible]
    unresolved = [text.strip() for text in prose if PLACEHOLDER_RE.search(re.sub(r"`[^`]*`", "", text))]
    if unresolved:
        warnings.append(f"body: possible unresolved placeholder, for example: {unresolved[0][:80]!r}")


def check_shareable(text: str, errors: list[str], warnings: list[str]) -> None:
    if PRIVATE_PATH_RE.search(text):
        errors.append("shareable: contains what looks like a private or absolute path")
    match = EVIDENCE_FILE_RE.search(text)
    if match:
        errors.append(f"shareable: references a meeting evidence file ({match.group(0)}); keep it in the private companion file")
    if TIMESTAMP_RE.search(text):
        warnings.append("shareable: contains something that looks like a recording timestamp")
    if RECORDING_RE.search(text):
        warnings.append("shareable: mentions a recording or transcript; the reader may not have it")


def validate(text: str) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    front, body = split_front_matter(text)
    fields: dict[str, str] = {}
    if front is None:
        errors.append("front matter: the document must start with a '---' delimited front matter block")
    else:
        fields, repositories = parse_front_matter(front)
        check_front_matter(fields, repositories, errors)
    check_body(body, errors, warnings)
    if fields.get("shareable") == "true":
        check_shareable(text, errors, warnings)
    return {"status": "INVALID" if errors else "OK", "errors": errors, "warnings": warnings}


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("Usage: validate-handoff.py <handoff.md>", file=sys.stderr)
        return 2
    path = Path(argv[0])
    if not path.is_file():
        print(json.dumps({"status": "INVALID", "errors": [f"file not found: {path}"], "warnings": []}, indent=2))
        return 1
    result = validate(path.read_text(encoding="utf-8"))
    result["file"] = str(path)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
