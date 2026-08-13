#!/usr/bin/env python3
from __future__ import annotations

import json
import importlib.util
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


FFMPEG_AVAILABLE = shutil.which("ffmpeg") is not None


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "process-meeting.py"
SPEC = importlib.util.spec_from_file_location("process_meeting", SCRIPT)
process_meeting = importlib.util.module_from_spec(SPEC)
sys.modules[str(SPEC.name)] = process_meeting
assert SPEC.loader is not None
SPEC.loader.exec_module(process_meeting)


class MeetingNormalizerCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.outputs = self.root / "outputs"
        self.fake_bin = self.root / "bin"
        self.fake_bin.mkdir()
        self.outputs.mkdir()
        self.glossary = self.root / "glossary.yaml"
        self.config = self.root / "profile.yaml"
        self.create_glossary()
        self.create_config()
        self.create_fake_transcriber()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def create_glossary(self) -> None:
        self.glossary.write_text(
            """schema_version: 1
terms:
  - canonical: ExampleProduct
    category: product
    aliases:
      - Example Product
    phonetic_aliases:
      - example prod
    observed_asr_variants:
      - value: egg sample product
        source: fixture
        confidence: hypothesis
    context_keywords:
      - subscription
      - plan
      - customer
    possible_contexts:
      - role: product
        confidence: candidate
        cues:
          - subscription
    confidence: candidate
  - canonical: ExampleRegion
    category: region
    aliases:
      - Example Region
    phonetic_aliases: []
    observed_asr_variants: []
    context_keywords:
      - country
      - market
      - locale
    possible_contexts:
      - role: region
        confidence: candidate
        cues:
          - market
    confidence: candidate
""",
            encoding="utf-8",
        )

    def create_config(self) -> None:
        self.config.write_text(
            f"""outputs:
  root: {self.outputs}
transcription:
  provider: custom_command
  command:
    - fake_transcriber
    - "{{audio}}"
    - "{{output_dir}}"
    - "{{output_name}}"
  output_name: transcription.raw
glossary:
  path: {self.glossary}
  mode: hints_only
""",
            encoding="utf-8",
        )

    def create_fake_transcriber(self) -> None:
        fake = self.fake_bin / "fake_transcriber"
        fake.write_text(
            """#!/usr/bin/env python3
import json
import sys
from pathlib import Path

_, audio, output_dir, output_name = sys.argv
out = Path(output_dir)
out.mkdir(parents=True, exist_ok=True)
print("FAKE_PROGRESS_SHOULD_BE_CAPTURED")
payload = {
  "text": "i think egg sample product needs review, but the customer plan in this market should be confirmed.",
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 3.0,
      "text": "i think egg sample product needs review, but the customer plan in this market should be confirmed.",
      "avg_logprob": -1.2,
      "compression_ratio": 1.1,
      "no_speech_prob": 0.1
    }
  ]
}
(out / f"{output_name}.json").write_text(json.dumps(payload))
""",
            encoding="utf-8",
        )
        fake.chmod(fake.stat().st_mode | stat.S_IXUSR)

    def create_chunk_fake_transcriber(self) -> Path:
        fake = self.fake_bin / "fake_chunk_transcriber"
        calls = self.root / "chunk-calls.jsonl"
        fake.write_text(
            f"""#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

_, audio, output_dir, output_name = sys.argv
out = Path(output_dir)
out.mkdir(parents=True, exist_ok=True)
match = re.search(r"chunk-(\\d{{4}})", str(audio))
index = int(match.group(1)) if match else 0
Path({str(calls)!r}).open("a", encoding="utf-8").write(json.dumps({{"index": index, "audio": audio, "output_dir": output_dir, "output_name": output_name}}) + "\\n")
payload = {{
  "text": f"chunk {{index}} first chunk {{index}} overlap",
  "segments": [
    {{"id": 0, "start": 0.0, "end": 1.0, "text": f"chunk {{index}} first", "avg_logprob": -0.2, "compression_ratio": 1.1, "no_speech_prob": 0.1}},
    {{"id": 1, "start": 2.0, "end": 3.0, "text": f"chunk {{index}} overlap", "avg_logprob": -0.2, "compression_ratio": 1.1, "no_speech_prob": 0.1}}
  ]
}}
(out / f"{{output_name}}.json").write_text(json.dumps(payload), encoding="utf-8")
""",
            encoding="utf-8",
        )
        fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
        return calls

    def env(self) -> dict[str, str]:
        env = os.environ.copy()
        env["PATH"] = str(self.fake_bin) + os.pathsep + env.get("PATH", "")
        return env

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args, "--config", str(self.config)],
            text=True,
            capture_output=True,
            env=self.env(),
            check=False,
        )

    def write_raw(self, segments: list[dict]) -> Path:
        raw = self.root / "raw.json"
        raw.write_text(json.dumps({"text": " ".join(segment["text"] for segment in segments), "segments": segments}), encoding="utf-8")
        return raw

    def segment(self, index: int, text: str, compression_ratio: float = 1.1) -> dict:
        return {
            "id": index,
            "start": float(index),
            "end": float(index + 1),
            "text": text,
            "avg_logprob": -0.2,
            "compression_ratio": compression_ratio,
            "no_speech_prob": 0.1,
        }

    def write_test_audio(self, seconds: float = 12.0) -> Path:
        audio = self.root / "tone.wav"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                f"sine=frequency=440:duration={seconds}",
                "-ar",
                "16000",
                "-ac",
                "1",
                str(audio),
            ],
            check=True,
        )
        return audio

    def test_recording_generates_outputs_with_glossary_candidates(self) -> None:
        audio = self.root / "meeting.mp4"
        audio.write_bytes(b"fake")

        result = self.run_cli(str(audio))

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        out = Path(payload["output"])
        self.assertEqual(payload["status"], "COMPLETE")
        self.assertIn("FAKE_PROGRESS_SHOULD_BE_CAPTURED", (out / "transcription.log").read_text())
        self.assertNotIn("FAKE_PROGRESS_SHOULD_BE_CAPTURED", result.stdout)
        normalized = json.loads((out / "transcription.normalized.json").read_text())
        hit = normalized["segments"][0]["glossary_hits"][0]
        self.assertEqual(hit["canonical"], "ExampleProduct")
        self.assertEqual(hit["match_type"], "observed_asr_variants")
        self.assertEqual(hit["confidence"], "variant_candidate")
        candidates = normalized["segments"][0]["glossary_candidates"]
        self.assertEqual(candidates[0]["canonical"], "ExampleRegion")
        uncertainties = json.loads((out / "uncertainties.json").read_text())
        self.assertTrue(uncertainties["uncertain_terms"])
        self.assertTrue(uncertainties["linguistic_uncertainties"])
        self.assertTrue(uncertainties["contradictions"])

    def test_chunking_disabled_uses_single_transcriber_without_chunks(self) -> None:
        audio = self.root / "meeting.mp4"
        audio.write_bytes(b"fake")

        result = self.run_cli(str(audio), "--force")

        self.assertEqual(result.returncode, 0, result.stderr)
        out = Path(json.loads(result.stdout)["output"])
        self.assertFalse((out / "transcription.raw.chunks").exists())
        self.assertIn("FAKE_PROGRESS_SHOULD_BE_CAPTURED", (out / "transcription.log").read_text())

    @unittest.skipUnless(FFMPEG_AVAILABLE, "ffmpeg not installed")
    def test_chunking_splits_audio_calls_transcriber_and_reassembles_offsets(self) -> None:
        calls = self.create_chunk_fake_transcriber()
        audio = self.write_test_audio(seconds=12.0)
        self.config.write_text(
            f"""outputs:
  root: {self.outputs}
transcription:
  provider: custom_command
  command:
    - fake_chunk_transcriber
    - "{{audio}}"
    - "{{output_dir}}"
    - "{{output_name}}"
  output_name: transcription.raw
  chunking:
    enabled: true
    chunk_seconds: 5
    overlap_seconds: 1
glossary:
  path: {self.glossary}
  mode: hints_only
""",
            encoding="utf-8",
        )

        result = self.run_cli(str(audio), "--force")

        self.assertEqual(result.returncode, 0, result.stderr)
        out = Path(json.loads(result.stdout)["output"])
        call_lines = [json.loads(line) for line in calls.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([line["index"] for line in call_lines], [0, 1, 2])
        raw = json.loads((out / "transcription.raw.json").read_text())
        self.assertTrue(raw["chunking"]["enabled"])
        self.assertEqual(raw["chunking"]["chunk_count"], 3)
        self.assertEqual([segment["start"] for segment in raw["segments"]], [0.0, 2.0, 6.0, 10.0])
        self.assertEqual([segment["id"] for segment in raw["segments"]], [0, 1, 2, 3])
        self.assertTrue((out / "transcription.raw.chunks" / "chunk-0000.wav").exists())
        self.assertTrue((out / "transcription.raw.chunks" / "chunk-0000.log").exists())

    @unittest.skipUnless(FFMPEG_AVAILABLE, "ffmpeg not installed")
    def test_chunking_final_raw_shape_remains_consumable(self) -> None:
        self.create_chunk_fake_transcriber()
        audio = self.write_test_audio(seconds=7.0)
        self.config.write_text(
            f"""outputs:
  root: {self.outputs}
transcription:
  provider: custom_command
  command:
    - fake_chunk_transcriber
    - "{{audio}}"
    - "{{output_dir}}"
    - "{{output_name}}"
  output_name: transcription.raw
  chunking:
    enabled: true
    chunk_seconds: 5
    overlap_seconds: 1
glossary:
  path: {self.glossary}
  mode: hints_only
""",
            encoding="utf-8",
        )

        result = self.run_cli(str(audio), "--force")

        self.assertEqual(result.returncode, 0, result.stderr)
        out = Path(json.loads(result.stdout)["output"])
        raw = json.loads((out / "transcription.raw.json").read_text())
        analysis = json.loads((out / "transcription.analysis.json").read_text())
        normalized = json.loads((out / "transcription.normalized.json").read_text())
        self.assertTrue(all({"id", "start", "end", "text"} <= set(segment) for segment in raw["segments"]))
        self.assertEqual(analysis["segment_count"], len(raw["segments"]))
        self.assertEqual(len(normalized["segments"]), len(raw["segments"]))

    @unittest.skipUnless(FFMPEG_AVAILABLE, "ffmpeg not installed")
    def test_chunking_enabled_without_ffmpeg_fails_actionably(self) -> None:
        audio = self.write_test_audio(seconds=2.0)
        self.config.write_text(
            f"""outputs:
  root: {self.outputs}
transcription:
  provider: custom_command
  command:
    - fake_transcriber
    - "{{audio}}"
    - "{{output_dir}}"
    - "{{output_name}}"
  output_name: transcription.raw
  chunking:
    enabled: true
    chunk_seconds: 5
    overlap_seconds: 1
glossary:
  path: {self.glossary}
  mode: hints_only
""",
            encoding="utf-8",
        )
        env = self.env()
        env["PATH"] = str(self.fake_bin)

        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(audio), "--config", str(self.config), "--force"],
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

        self.assertEqual(result.returncode, 3)
        self.assertIn("BLOCKED_CHUNKING_FFMPEG_NOT_AVAILABLE", result.stderr)

    def test_raw_transcript_does_not_require_transcriber(self) -> None:
        raw = self.root / "raw.json"
        raw.write_text(json.dumps({"text": "The subscription plan is tied to a market.", "segments": []}), encoding="utf-8")

        result = self.run_cli("--raw-transcript", str(raw))

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        out = Path(payload["output"])
        manifest = json.loads((out / "manifest.json").read_text())
        self.assertEqual(manifest["source"]["kind"], "raw_transcript")
        self.assertEqual(manifest["transcription"]["status"], "provided")

    def test_plain_observed_asr_variant_list_is_supported(self) -> None:
        self.glossary.write_text(
            """schema_version: 1
terms:
  - canonical: ExampleProduct
    category: product
    aliases: []
    phonetic_aliases: []
    observed_asr_variants:
      - egg sample product
    context_keywords: []
    confidence: candidate
""",
            encoding="utf-8",
        )
        raw = self.root / "raw.json"
        raw.write_text(json.dumps({"text": "egg sample product needs review.", "segments": []}), encoding="utf-8")

        result = self.run_cli("--raw-transcript", str(raw), "--force")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        out = Path(payload["output"])
        normalized = json.loads((out / "transcription.normalized.json").read_text())
        self.assertEqual(normalized["segments"][0]["glossary_hits"][0]["match_type"], "observed_asr_variants")

    def test_discovers_project_local_config(self) -> None:
        project = self.root / "project"
        nested = project / "nested"
        nested.mkdir(parents=True)
        (project / ".meeting-evidence-normalizer.yaml").write_text(self.config.read_text(encoding="utf-8"), encoding="utf-8")
        raw = nested / "raw.json"
        raw.write_text(json.dumps({"text": "The customer plan belongs to this market.", "segments": []}), encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--raw-transcript", str(raw)],
            text=True,
            capture_output=True,
            cwd=nested,
            env=self.env(),
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(Path(payload["output"]).exists())

    def test_discovers_user_config_when_project_config_is_absent(self) -> None:
        home = self.root / "home"
        home_config_dir = home / ".config" / "meeting-evidence-normalizer"
        home_config_dir.mkdir(parents=True)
        (home_config_dir / "profile.yaml").write_text(self.config.read_text(encoding="utf-8"), encoding="utf-8")
        workspace = self.root / "workspace"
        workspace.mkdir()
        raw = workspace / "raw.json"
        raw.write_text(json.dumps({"text": "The customer plan belongs to this market.", "segments": []}), encoding="utf-8")
        env = self.env()
        env["HOME"] = str(home)

        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--raw-transcript", str(raw)],
            text=True,
            capture_output=True,
            cwd=workspace,
            env=env,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(Path(payload["output"]).exists())

    def test_short_alias_does_not_match_fragment_inside_neutral_word(self) -> None:
        terms = [{"canonical": "SampleConcept", "aliases": ["ray"], "confidence": "candidate"}]

        hits = process_meeting.find_term_hits("The graybox workflow is ready.", terms)

        self.assertEqual(hits, [])

    def test_short_alias_matches_isolated_word_with_review_confidence(self) -> None:
        terms = [{"canonical": "SampleConcept", "aliases": ["ray"], "confidence": "candidate"}]

        hits = process_meeting.find_term_hits("Please review ray before release.", terms)

        self.assertEqual(hits[0]["canonical"], "SampleConcept")
        self.assertEqual(hits[0]["confidence"], "short_alias_review")
        self.assertEqual(hits[0]["action"], "review_raw_before_normalizing")

    def test_short_canonical_uses_word_boundary_and_review_confidence(self) -> None:
        terms = [{"canonical": "QX", "aliases": [], "confidence": "candidate"}]

        self.assertEqual(process_meeting.find_term_hits("The aqxbox task moved.", terms), [])
        hits = process_meeting.find_term_hits("QX moved to review.", terms)
        self.assertEqual(hits[0]["match_type"], "canonical")
        self.assertEqual(hits[0]["confidence"], "short_alias_review")

    def test_long_alias_still_matches_with_boundary_without_review_downgrade(self) -> None:
        terms = [{"canonical": "SampleConcept", "aliases": ["sample alias"], "confidence": "candidate"}]

        hits = process_meeting.find_term_hits("The sample alias, is ready.", terms)

        self.assertEqual(hits[0]["matched"], "sample alias")
        self.assertEqual(hits[0]["confidence"], "candidate")
        self.assertNotIn("action", hits[0])

    def test_contradiction_connector_without_glossary_anchor_does_not_fire(self) -> None:
        normalized = {
            "glossary_configured": True,
            "segments": [{"id": 0, "start": 0.0, "end": 1.0, "text": "The team paused, but continued later.", "glossary_hits": [], "glossary_candidates": []}],
            "glossary_hits": [],
            "glossary_candidates": [],
        }

        _, uncertainties = process_meeting.extract_evidence(normalized, {"repetition_runs": []})

        self.assertEqual(uncertainties["contradictions"], [])

    def test_contradiction_connector_with_nearby_glossary_anchor_fires(self) -> None:
        normalized = {
            "glossary_configured": True,
            "segments": [
                {"id": 0, "start": 0.0, "end": 1.0, "text": "SampleProduct is ready.", "glossary_hits": [{"canonical": "SampleProduct"}], "glossary_candidates": []},
                {"id": 1, "start": 1.0, "end": 2.0, "text": "But we should verify the rollout.", "glossary_hits": [], "glossary_candidates": []},
            ],
            "glossary_hits": [{"segment_id": 0, "canonical": "SampleProduct"}],
            "glossary_candidates": [],
        }

        _, uncertainties = process_meeting.extract_evidence(normalized, {"repetition_runs": []})

        self.assertEqual(len(uncertainties["contradictions"]), 1)

    def test_repetition_run_of_five_segments_is_detected(self) -> None:
        raw = {"segments": [self.segment(index, "We will review the sample item.", compression_ratio=2.8) for index in range(5)]}

        analysis = process_meeting.analyze_transcript(raw)

        self.assertEqual(len(analysis["repetition_runs"]), 1)
        run = analysis["repetition_runs"][0]
        self.assertEqual(run["start_segment_id"], 0)
        self.assertEqual(run["end_segment_id"], 4)
        self.assertEqual(run["count"], 5)
        self.assertEqual(run["start"], 0.0)
        self.assertEqual(run["end"], 5.0)

    def test_repetition_run_below_minimum_is_not_detected(self) -> None:
        raw = {"segments": [self.segment(index, "We will review the sample item.") for index in range(4)]}

        analysis = process_meeting.analyze_transcript(raw)

        self.assertEqual(analysis["repetition_runs"], [])
        self.assertFalse(analysis["asr_degeneration_suspected"])

    def test_asr_degeneration_suspected_uses_proportional_threshold(self) -> None:
        high_ratio = {"segments": [self.segment(index, "Repeated sample phrase.") for index in range(5)] + [self.segment(5, "Unique sample phrase.")]}
        low_ratio = {"segments": [self.segment(index, "Repeated sample phrase.") for index in range(5)] + [self.segment(index, f"Unique sample phrase {index}.") for index in range(5, 45)]}

        self.assertTrue(process_meeting.analyze_transcript(high_ratio)["asr_degeneration_suspected"])
        self.assertFalse(process_meeting.analyze_transcript(low_ratio)["asr_degeneration_suspected"])

    def test_repetition_run_segments_are_excluded_from_evidence_and_summarized(self) -> None:
        repeated = "We will review the sample item."
        raw = {"segments": [self.segment(index, repeated) for index in range(5)] + [self.segment(5, "Maybe the sample item is ready.")]}
        analysis = process_meeting.analyze_transcript(raw)
        normalized = {
            "glossary_configured": True,
            "segments": [
                {
                    "id": segment["id"],
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"],
                    "glossary_hits": [{"canonical": "SampleItem"}],
                    "glossary_candidates": [],
                }
                for segment in raw["segments"]
            ],
            "glossary_hits": [{"segment_id": index, "canonical": "SampleItem", "match_type": "observed_asr_variants"} for index in range(6)],
            "glossary_candidates": [],
        }

        evidence, uncertainties = process_meeting.extract_evidence(normalized, analysis)

        self.assertEqual(len(evidence["claims"]), 1)
        self.assertEqual(evidence["claims"][0]["source"]["segment_id"], 5)
        self.assertEqual(evidence["actions_mentioned"], [])
        self.assertEqual(len(uncertainties["linguistic_uncertainties"]), 1)
        self.assertEqual(uncertainties["contradictions"], [])
        self.assertEqual(len(uncertainties["uncertain_terms"]), 1)
        self.assertEqual(len(uncertainties["excluded_low_confidence"]), 1)
        self.assertEqual(uncertainties["excluded_low_confidence"][0]["type"], "asr_repetition_excluded")
        self.assertEqual(uncertainties["excluded_low_confidence"][0]["repeat_count"], 5)

    def test_manifest_quality_reflects_repetition_fields(self) -> None:
        raw = self.write_raw([self.segment(index, "We will review the sample item.") for index in range(5)] + [self.segment(5, "Unique sample item.")])

        result = self.run_cli("--raw-transcript", str(raw), "--force")

        self.assertEqual(result.returncode, 0, result.stderr)
        out = Path(json.loads(result.stdout)["output"])
        manifest = json.loads((out / "manifest.json").read_text())
        self.assertEqual(manifest["quality"]["repetition_run_count"], 1)
        self.assertEqual(manifest["quality"]["segments_excluded"], 5)
        self.assertTrue(manifest["quality"]["asr_degeneration_suspected"])

    def test_meeting_md_includes_quality_warning_only_when_degeneration_is_suspected(self) -> None:
        raw = self.write_raw([self.segment(index, "We will review the sample item.") for index in range(5)] + [self.segment(5, "Unique sample item.")])

        result = self.run_cli("--raw-transcript", str(raw), "--force")

        self.assertEqual(result.returncode, 0, result.stderr)
        out = Path(json.loads(result.stdout)["output"])
        meeting = (out / "meeting.md").read_text()
        self.assertIn("## Quality Warning", meeting)
        self.assertLess(meeting.index("## Quality Warning"), meeting.index("## Metadata"))

        raw2 = self.root / "raw-no-warning.json"
        raw2.write_text(json.dumps({"segments": [self.segment(index, f"Unique sample item {index}.") for index in range(6)]}), encoding="utf-8")
        result2 = self.run_cli("--raw-transcript", str(raw2), "--force")
        self.assertEqual(result2.returncode, 0, result2.stderr)
        out2 = Path(json.loads(result2.stdout)["output"])
        self.assertNotIn("## Quality Warning", (out2 / "meeting.md").read_text())

    def test_meeting_md_counts_reflect_post_exclusion_totals(self) -> None:
        raw = self.write_raw([self.segment(index, "We will review the sample item.") for index in range(5)] + [self.segment(5, "We will review the final sample item.")])

        result = self.run_cli("--raw-transcript", str(raw), "--force")

        self.assertEqual(result.returncode, 0, result.stderr)
        out = Path(json.loads(result.stdout)["output"])
        meeting = (out / "meeting.md").read_text()
        self.assertIn("- Claims extracted: 1", meeting)
        self.assertIn("- Actions mentioned: 1", meeting)


if __name__ == "__main__":
    unittest.main()
