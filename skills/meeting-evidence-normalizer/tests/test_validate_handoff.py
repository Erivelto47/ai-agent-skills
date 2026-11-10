#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "validate-handoff.py"
SPEC = importlib.util.spec_from_file_location("validate_handoff", SCRIPT)
validate_handoff = importlib.util.module_from_spec(SPEC)
sys.modules[str(SPEC.name)] = validate_handoff
assert SPEC.loader is not None
SPEC.loader.exec_module(validate_handoff)


FRONT_MATTER = """---
handoff_format: 1
title: Example sync about a fictional service
date: 2026-01-15
type: call
audience: business+ai
language: en
status: draft
shareable: true
revalidate_when: after the follow-up meeting
min_agent_tier: frontier
repositories:
  - name: example-repo
    clone_url: https://example.invalid/example-repo.git
    base_branch: main
---
"""

BODY = """
# Handoff: example

## Summary

A short prose summary of a fictional discussion.

## 1. Themes at a glance

| # | Theme | State |
|---|---|---|
| 1 | Billing | open |

## 2. Billing

Description of the topic.

## 3. Decisions and understandings

- [tentative] Use the new flow.

## 4. Open questions

| # | Question | Who answers | Verifiable in code |
|---|---|---|---|
| 1 | Is it enabled? | partner | in part |

## 5. Actions mentioned (none approved)

| Who (inferred) | Action | When |
|---|---|---|
| Our side | Test it | next week |

## 6. AI section (mandatory)

Read-only.

### 6.1 Code context

- Repository: example-repo.

### 6.2 Glossary term to code

| Term | Meaning | In the code | How confirmed |
|---|---|---|---|
| Plan | A tier | `PlanTier` | to confirm |

### 6.3 Research questions

| ID | Question | Where to start | Why it matters |
|---|---|---|---|
| Q1 | How are plans stored? | billing module | scope |

### 6.5 Traps and limits

- Do not promise it ships.

### 6.6 Implementation

Not applicable.
"""


def make(front: str = FRONT_MATTER, body: str = BODY) -> str:
    return front + body


class ValidateHandoffTest(unittest.TestCase):
    def test_valid_document_passes(self) -> None:
        result = validate_handoff.validate(make())
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["status"], "OK")

    def test_neutral_example_handoff_is_valid_and_warning_free(self) -> None:
        example = SKILL_DIR.parents[1] / "examples" / "neutral-handoff" / "handoff.md"
        result = validate_handoff.validate(example.read_text(encoding="utf-8"))
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["warnings"], [])

    def test_template_file_is_flagged_as_unfilled(self) -> None:
        template = (SKILL_DIR / "references" / "handoff-template.md").read_text(encoding="utf-8")
        result = validate_handoff.validate(template)
        self.assertEqual(result["status"], "INVALID")

    def test_missing_front_matter_fails(self) -> None:
        result = validate_handoff.validate(BODY)
        self.assertEqual(result["status"], "INVALID")
        self.assertTrue(any("front matter" in error for error in result["errors"]))

    def test_bad_enum_and_date_fail(self) -> None:
        front = FRONT_MATTER.replace("type: call", "type: meeting").replace("2026-01-15", "15/01/2026")
        result = validate_handoff.validate(make(front))
        joined = " ".join(result["errors"])
        self.assertIn("type 'meeting'", joined)
        self.assertIn("YYYY-MM-DD", joined)

    def test_missing_repository_branch_fails(self) -> None:
        front = FRONT_MATTER.replace("    base_branch: main\n", "")
        result = validate_handoff.validate(make(front))
        self.assertTrue(any("base_branch" in error for error in result["errors"]))

    def test_missing_summary_fails(self) -> None:
        body = BODY.replace("## Summary\n\nA short prose summary of a fictional discussion.\n\n", "")
        result = validate_handoff.validate(make(body=body))
        self.assertTrue(any("summary" in error for error in result["errors"]))

    def test_missing_ai_section_fails(self) -> None:
        body = BODY.split("## 6. AI section")[0]
        result = validate_handoff.validate(make(body=body))
        self.assertEqual(result["status"], "INVALID")

    def test_ai_section_without_research_questions_fails(self) -> None:
        body = BODY.replace("| Q1 |", "| R1 |")
        result = validate_handoff.validate(make(body=body))
        self.assertTrue(any("Q1" in error for error in result["errors"]))

    def test_ai_section_must_be_last_numbered_section(self) -> None:
        body = BODY + "\n## 7. Appendix\n\nExtra.\n"
        result = validate_handoff.validate(make(body=body))
        self.assertTrue(any("AI section" in error for error in result["errors"]))

    def test_non_consecutive_numbering_fails(self) -> None:
        body = BODY.replace("## 3. Decisions", "## 4. Decisions").replace("## 4. Open", "## 5. Open")
        result = validate_handoff.validate(make(body=body))
        self.assertTrue(any("consecutive" in error for error in result["errors"]))

    def test_shareable_flags_private_paths_and_evidence_files(self) -> None:
        body = BODY.replace("Description of the topic.", "See /Users/someone/outputs/evidence.json for detail.")
        result = validate_handoff.validate(make(body=body))
        joined = " ".join(result["errors"])
        self.assertIn("private or absolute path", joined)
        self.assertIn("evidence.json", joined)

    def test_non_shareable_allows_private_references(self) -> None:
        front = FRONT_MATTER.replace("shareable: true", "shareable: false")
        body = BODY.replace("Description of the topic.", "See /Users/someone/outputs/evidence.json for detail.")
        result = validate_handoff.validate(make(front, body))
        self.assertEqual(result["errors"], [])

    def test_shareable_warns_on_timestamps_and_recording_mentions(self) -> None:
        body = BODY.replace("Description of the topic.", "As said at 12:34 in the recording.")
        result = validate_handoff.validate(make(body=body))
        self.assertEqual(result["errors"], [])
        self.assertEqual(len(result["warnings"]), 2)

    def test_localized_headings_pass_because_checks_use_numbering(self) -> None:
        body = (
            BODY.replace("## Summary", "## Resumo")
            .replace("## 6. AI section (mandatory)", "## 6. Seção de IA (obrigatória)")
            .replace("### 6.1 Code context", "### 6.1 Contexto de código")
        )
        result = validate_handoff.validate(make(body=body))
        self.assertEqual(result["errors"], [])

    def test_cli_exit_codes_and_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp) / "good.md"
            bad = Path(tmp) / "bad.md"
            good.write_text(make(), encoding="utf-8")
            bad.write_text(BODY, encoding="utf-8")
            ok = subprocess.run([sys.executable, str(SCRIPT), str(good)], capture_output=True, text=True)
            self.assertEqual(ok.returncode, 0)
            self.assertEqual(json.loads(ok.stdout)["status"], "OK")
            invalid = subprocess.run([sys.executable, str(SCRIPT), str(bad)], capture_output=True, text=True)
            self.assertEqual(invalid.returncode, 1)
            self.assertEqual(json.loads(invalid.stdout)["status"], "INVALID")
            usage = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
            self.assertEqual(usage.returncode, 2)


if __name__ == "__main__":
    unittest.main()
