#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "process-meeting.py"


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


if __name__ == "__main__":
    unittest.main()
