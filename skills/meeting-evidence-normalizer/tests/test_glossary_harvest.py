#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "glossary-harvest.py"


class GlossaryHarvestCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.out = self.root / "glossary-candidates.yaml"
        self.report = self.root / "glossary-harvest-report.md"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write(self, path: str, text: str) -> Path:
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return target

    def run_cli(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--repo", str(self.repo), "--out", str(self.out), "--report", str(self.report), *args],
            text=True,
            capture_output=True,
            check=False,
        )
        if check:
            self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def load_terms(self) -> list[dict]:
        return yaml.safe_load(self.out.read_text(encoding="utf-8"))["terms"]

    def term(self, canonical: str) -> dict:
        for item in self.load_terms():
            if item["canonical"] == canonical:
                return item
        self.fail(f"Term not found: {canonical}")

    def test_generic_profile_generates_sensible_candidates(self) -> None:
        self.write("src/status.txt", "SAMPLE_READY\n")
        self.write("docs/overview.md", "# Billing Workflow\n")

        self.run_cli("--profile", "generic")

        names = {item["canonical"] for item in self.load_terms()}
        self.assertIn("SAMPLE READY", names)
        self.assertIn("Billing Workflow", names)

    def test_markdown_heading_preserves_accented_display_text(self) -> None:
        self.write("docs/overview.md", "# Pláçã Mévól Ánix\n")

        self.run_cli("--profile", "generic")

        names = {item["canonical"] for item in self.load_terms()}
        self.assertIn("Pláçã Mévól Ánix", names)
        self.assertNotIn("Pl M v l nix", names)

    def test_symlink_escape_outside_repo_is_excluded_without_crashing(self) -> None:
        self.write("src/status.txt", "INSIDE_SIGNAL\n")
        subprocess.run(["git", "init"], cwd=self.repo, text=True, capture_output=True, check=True)
        with tempfile.TemporaryDirectory() as outside_tmp:
            outside = Path(outside_tmp)
            (outside / "status.txt").write_text("OUTSIDE_SIGNAL\n", encoding="utf-8")
            try:
                (self.repo / "linked-status.txt").symlink_to(outside / "status.txt")
            except OSError as exc:
                self.skipTest(f"symlinks are not available: {exc}")

            self.run_cli("--profile", "generic")

        names = {item["canonical"] for item in self.load_terms()}
        source_paths = {source["path"] for item in self.load_terms() for source in item["sources"]}
        self.assertIn("INSIDE SIGNAL", names)
        self.assertNotIn("OUTSIDE SIGNAL", names)
        self.assertNotIn("linked-status.txt", source_paths)

    def test_auto_detects_java_kotlin_profile(self) -> None:
        self.write("pom.xml", "<project><modules><module>sample-service</module></modules></project>")
        self.write("src/main/kotlin/example/State.kt", "enum class State { SAMPLE_READY }\n")

        self.run_cli()

        payload = yaml.safe_load(self.out.read_text(encoding="utf-8"))
        self.assertEqual(payload["profile"], "java-kotlin")

    def test_falls_back_to_generic_when_no_profile_matches(self) -> None:
        self.write("notes/status.txt", "PUBLIC_SIGNAL_READY\n")

        self.run_cli()

        self.assertIn("generic fallback used", self.report.read_text(encoding="utf-8"))

    def test_generic_extractors_cover_content_filename_path_heading_and_alias_pair(self) -> None:
        self.write("docs/process.md", "## Review Queue\n")
        self.write("src/workflow/20260812_create_public_stage.sql", "-- PUBLIC_STAGE_READY\n")
        self.write("migrations/rename_old_stage_to_new_stage.sql", "-- rename\n")

        self.run_cli("--profile", "generic")

        names = {item["canonical"] for item in self.load_terms()}
        self.assertIn("PUBLIC STAGE READY", names)
        self.assertIn("create public stage", names)
        self.assertIn("workflow", names)
        self.assertIn("Review Queue", names)
        self.assertEqual(self.term("new stage")["aliases"], ["old stage"])

    def test_common_words_score_below_distinctive_terms(self) -> None:
        for index in range(4):
            self.write(f"src/module{index}/status.txt", "DISTINCTIVE_SIGNAL_READY\n")
        self.write("docs/active.md", "# Active\n")

        self.run_cli("--profile", "generic")

        distinctive = self.term("DISTINCTIVE SIGNAL READY")["harvest"]["score"]
        active = self.term("Active")["harvest"]["score"]
        self.assertGreater(distinctive, active)

    def test_transcripts_boost_spoken_term_against_equally_distinctive_term(self) -> None:
        self.write("src/a/status.txt", "SAMPLE_BRIDGE\n")
        self.write("src/b/status.txt", "PUBLIC_RIVER\n")
        transcripts = self.root / "outputs" / "meeting"
        transcripts.mkdir(parents=True)
        (transcripts / "transcription.raw.json").write_text(json.dumps({"text": "The team discussed sample bridge today."}), encoding="utf-8")

        self.run_cli("--profile", "generic", "--transcripts", str(self.root / "outputs"))

        spoken = self.term("SAMPLE BRIDGE")["harvest"]["score"]
        silent = self.term("PUBLIC RIVER")["harvest"]["score"]
        self.assertGreater(spoken, silent)

    def test_spokenness_does_not_match_across_word_boundaries_in_transcript_blob(self) -> None:
        self.write("src/status.txt", "ZABC\n")
        transcripts = self.root / "outputs" / "meeting"
        transcripts.mkdir(parents=True)
        (transcripts / "transcription.raw.json").write_text(
            json.dumps({"segments": [{"text": "alpha xyz abc beta"}]}),
            encoding="utf-8",
        )

        self.run_cli("--profile", "generic", "--transcripts", str(self.root / "outputs"))

        self.assertEqual(self.term("ZABC")["harvest"]["breakdown"]["spokenness"], 0.25)

    def test_spokenness_matches_single_word_as_whole_word(self) -> None:
        self.write("src/status.txt", "SIGNAL\n")
        transcripts = self.root / "outputs" / "meeting"
        transcripts.mkdir(parents=True)
        (transcripts / "transcription.raw.json").write_text(json.dumps({"text": "The signal is ready."}), encoding="utf-8")

        self.run_cli("--profile", "generic", "--transcripts", str(self.root / "outputs"))

        self.assertEqual(self.term("SIGNAL")["harvest"]["breakdown"]["spokenness"], 1.0)

    def test_spokenness_does_not_match_fragment_inside_word(self) -> None:
        self.write("src/status.txt", "MARK\n")
        transcripts = self.root / "outputs" / "meeting"
        transcripts.mkdir(parents=True)
        (transcripts / "transcription.raw.json").write_text(json.dumps({"text": "The benchmark started early."}), encoding="utf-8")

        self.run_cli("--profile", "generic", "--transcripts", str(self.root / "outputs"))

        self.assertEqual(self.term("MARK")["harvest"]["breakdown"]["spokenness"], 0.25)

    def test_transcript_matching_handles_spoken_word_boundaries(self) -> None:
        self.write("src/status.txt", "SAMPLE_BRIDGE\n")
        transcripts = self.root / "outputs" / "meeting"
        transcripts.mkdir(parents=True)
        (transcripts / "transcription.raw.json").write_text(
            json.dumps({"segments": [{"text": "sample bridge is still under review"}]}),
            encoding="utf-8",
        )

        self.run_cli("--profile", "generic", "--transcripts", str(self.root / "outputs"))

        self.assertEqual(self.term("SAMPLE BRIDGE")["harvest"]["breakdown"]["spokenness"], 1.0)

    def test_spokenness_matches_multi_word_phrase_with_spacing_variation(self) -> None:
        self.write("src/status.txt", "SAMPLE_PIPELINE\n")
        transcripts = self.root / "outputs" / "meeting"
        transcripts.mkdir(parents=True)
        (transcripts / "transcription.raw.json").write_text(
            json.dumps({"segments": [{"text": "Please review sample   pipeline setup."}]}),
            encoding="utf-8",
        )

        self.run_cli("--profile", "generic", "--transcripts", str(self.root / "outputs"))

        self.assertEqual(self.term("SAMPLE PIPELINE")["harvest"]["breakdown"]["spokenness"], 1.0)

    def test_spokenness_does_not_match_multi_word_phrase_when_only_one_word_appears(self) -> None:
        self.write("src/status.txt", "SAMPLE_PIPELINE\n")
        transcripts = self.root / "outputs" / "meeting"
        transcripts.mkdir(parents=True)
        (transcripts / "transcription.raw.json").write_text(json.dumps({"text": "The sample is ready."}), encoding="utf-8")

        self.run_cli("--profile", "generic", "--transcripts", str(self.root / "outputs"))

        self.assertEqual(self.term("SAMPLE PIPELINE")["harvest"]["breakdown"]["spokenness"], 0.25)

    def test_spokenness_without_transcripts_remains_neutral(self) -> None:
        self.write("src/status.txt", "SILENT_SIGNAL\n")

        self.run_cli("--profile", "generic")

        self.assertEqual(self.term("SILENT SIGNAL")["harvest"]["breakdown"]["spokenness"], 1.0)

    def test_unknown_profile_keys_fail_with_actionable_error(self) -> None:
        profile = self.root / "bad-profile.yaml"
        profile.write_text(
            """name: bad
description: Bad profile.
surprise: true
extractors:
  - id: constants
    category: status
    kind: content_regex
    pattern: '(SAMPLE)'
""",
            encoding="utf-8",
        )
        self.write("src/status.txt", "SAMPLE\n")

        result = self.run_cli("--profile", str(profile), check=False)

        self.assertEqual(result.returncode, 2)
        self.assertIn("unknown key", result.stderr)
        self.assertIn("valid keys", result.stderr)

    def test_output_is_byte_deterministic(self) -> None:
        self.write("src/status.txt", "SAMPLE_READY\n")

        self.run_cli("--profile", "generic")
        first = self.out.read_bytes()
        self.run_cli("--profile", "generic")
        second = self.out.read_bytes()

        self.assertEqual(first, second)

    def test_confidence_is_never_promoted_above_candidate(self) -> None:
        self.write("src/status.txt", "SAMPLE_READY\n")

        self.run_cli("--profile", "generic")

        self.assertEqual({item["confidence"] for item in self.load_terms()}, {"candidate"})

    def test_dry_run_writes_no_artifacts(self) -> None:
        self.write("src/status.txt", "SAMPLE_READY\n")

        result = self.run_cli("--profile", "generic", "--dry-run")

        self.assertEqual(json.loads(result.stdout)["status"], "DRY_RUN")
        self.assertFalse(self.out.exists())
        self.assertFalse(self.report.exists())

    def test_java_kotlin_profile_extracts_kotlin_enum_and_sealed_subtypes(self) -> None:
        self.write(
            "src/main/kotlin/example/State.kt",
            """sealed interface PublicState
object AwaitingReview : PublicState
enum class Stage {
    SAMPLE_READY,
}
""",
        )

        self.run_cli("--profile", "java-kotlin")

        names = {item["canonical"] for item in self.load_terms()}
        self.assertIn("SAMPLE READY", names)
        self.assertIn("Awaiting Review", names)

    def test_java_kotlin_profile_extracts_maven_and_gradle_modules(self) -> None:
        self.write("pom.xml", "<project><modules><module>sample-service</module></modules></project>")
        self.write("settings.gradle.kts", 'include(":sample-worker")\n')

        self.run_cli("--profile", "java-kotlin")

        names = {item["canonical"] for item in self.load_terms()}
        self.assertIn("sample service", names)
        self.assertIn("sample worker", names)

    def test_git_mode_respects_ignore_rules_while_including_untracked_allowed_files(self) -> None:
        subprocess.run(["git", "init"], cwd=self.repo, text=True, capture_output=True, check=True)
        self.write(".gitignore", "ignored.txt\n")
        self.write("ignored.txt", "IGNORED_SIGNAL\n")
        self.write("kept.txt", "KEPT_SIGNAL\n")

        self.run_cli("--profile", "generic")

        names = {item["canonical"] for item in self.load_terms()}
        self.assertIn("KEPT SIGNAL", names)
        self.assertNotIn("IGNORED SIGNAL", names)


if __name__ == "__main__":
    unittest.main()
