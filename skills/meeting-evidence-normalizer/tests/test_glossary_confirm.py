#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "glossary-confirm.py"


class GlossaryConfirmCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.out = self.root / "glossary-confirmed.yaml"
        self.report = self.root / "glossary-confirm-report.md"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def candidate(
        self,
        name: str,
        terms: list[dict],
        *,
        spokenness_active: bool | None = True,
    ) -> Path:
        payload = {
            "schema_version": 1,
            "generated_at": "1970-01-01T00:00:00+00:00",
            "profile": "generic",
            "repo_fingerprint": name,
            "tool": {"name": "glossary-harvest", "version": "1.0.0"},
            "terms": terms,
        }
        if spokenness_active is not None:
            payload["spokenness_active"] = spokenness_active
        path = self.root / name / "candidates.yaml"
        path.parent.mkdir(parents=True)
        path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
        return path

    def term(
        self,
        canonical: str,
        *,
        file_count: int = 1,
        spokenness: float = 1.0,
        commonness_penalty: float = 0.0,
        score: float = 0.5,
        aliases: list[str] | None = None,
        variants: list[dict] | None = None,
        source_path: str | None = None,
    ) -> dict:
        item = {
            "canonical": canonical,
            "category": "neutral_object",
            "sources": [
                {
                    "path": source_path or f"docs/{canonical.lower().replace(' ', '-')}.md",
                    "line": 3,
                    "evidence_type": "neutral_fixture",
                }
            ],
            "confidence": "candidate",
            "harvest": {
                "score": score,
                "breakdown": {
                    "distinctiveness": 0.5,
                    "spokenness": spokenness,
                    "extractor_weight": 1.0,
                    "commonness_penalty": commonness_penalty,
                },
                "file_count": file_count,
                "extractor_ids": ["neutral_fixture"],
            },
        }
        if aliases:
            item["aliases"] = aliases
        if variants:
            item["observed_asr_variants"] = variants
        return item

    def run_cli(self, *candidates: Path, check: bool = True, out: Path | None = None) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--candidates",
                *(str(path) for path in candidates),
                "--out",
                str(out or self.out),
                "--report",
                str(self.report),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if check:
            self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def confirmed_terms(self) -> list[dict]:
        return yaml.safe_load(self.out.read_text(encoding="utf-8"))["terms"]

    def confirmed_names(self) -> set[str]:
        return {term["canonical"] for term in self.confirmed_terms()}

    def test_term_in_two_candidate_files_with_spokenness_one_is_confirmed(self) -> None:
        first = self.candidate("repo-one", [self.term("Amber Loom")])
        second = self.candidate("repo-two", [self.term("Amber Loom")])

        self.run_cli(first, second)

        self.assertIn("Amber Loom", self.confirmed_names())

    def test_single_candidate_file_with_four_files_and_spokenness_one_is_confirmed(self) -> None:
        path = self.candidate("repo-one", [self.term("Brisk Lantern", file_count=4)])

        self.run_cli(path)

        self.assertIn("Brisk Lantern", self.confirmed_names())

    def test_single_candidate_file_below_file_threshold_is_not_confirmed(self) -> None:
        path = self.candidate("repo-one", [self.term("Copper Orchard", file_count=1)])

        self.run_cli(path)

        self.assertNotIn("Copper Orchard", self.confirmed_names())

    def test_two_candidate_files_with_low_spokenness_are_not_confirmed(self) -> None:
        first = self.candidate("repo-one", [self.term("Delta Meadow", spokenness=0.25)])
        second = self.candidate("repo-two", [self.term("Delta Meadow", spokenness=0.25)])

        self.run_cli(first, second)

        self.assertNotIn("Delta Meadow", self.confirmed_names())

    def test_single_common_word_penalty_blocks_file_threshold_confirmation(self) -> None:
        path = self.candidate("repo-one", [self.term("Plain", file_count=4, commonness_penalty=0.75)])

        self.run_cli(path)

        self.assertNotIn("Plain", self.confirmed_names())

    def test_common_word_penalty_blocks_source_threshold_confirmation(self) -> None:
        first = self.candidate("repo-one", [self.term("Marker", commonness_penalty=0.75)])
        second = self.candidate("repo-two", [self.term("Marker", commonness_penalty=0.75)])

        self.run_cli(first, second)

        self.assertNotIn("Marker", self.confirmed_names())

    def test_short_token_penalty_does_not_block_confirmation(self) -> None:
        first = self.candidate("repo-one", [self.term("QZK", commonness_penalty=0.45)])
        second = self.candidate("repo-two", [self.term("QZK", commonness_penalty=0.45)])

        self.run_cli(first, second)

        self.assertIn("QZK", self.confirmed_names())

    def test_zero_commonness_penalty_preserves_existing_confirmation_behavior(self) -> None:
        first = self.candidate("repo-one", [self.term("Silver Beacon", commonness_penalty=0.0)])
        second = self.candidate("repo-two", [self.term("Silver Beacon", commonness_penalty=0.0)])

        self.run_cli(first, second)

        self.assertIn("Silver Beacon", self.confirmed_names())

    def test_common_word_penalty_in_any_source_blocks_confirmation(self) -> None:
        first = self.candidate("repo-one", [self.term("Granite", commonness_penalty=0.0)])
        second = self.candidate("repo-two", [self.term("Granite", commonness_penalty=0.75)])

        self.run_cli(first, second)

        self.assertNotIn("Granite", self.confirmed_names())

    def test_candidates_without_active_spokenness_fail_clearly(self) -> None:
        inactive = self.candidate("repo-one", [self.term("Echo Thread")], spokenness_active=False)

        result = self.run_cli(inactive, check=False)

        self.assertEqual(result.returncode, 2)
        self.assertIn(str(inactive), result.stderr)
        self.assertIn("spokenness_active: true", result.stderr)
        self.assertFalse(self.out.exists())

    def test_confirmed_confidence_is_cross_source_confirmed_only(self) -> None:
        first = self.candidate("repo-one", [self.term("Frost Harbor")])
        second = self.candidate("repo-two", [self.term("Frost Harbor")])

        self.run_cli(first, second)

        self.assertEqual({term["confidence"] for term in self.confirmed_terms()}, {"cross_source_confirmed"})

    def test_sources_preserve_all_candidate_file_provenance(self) -> None:
        first = self.candidate("repo-one", [self.term("Golden Relay", source_path="src/relay-one.txt")])
        second = self.candidate("repo-two", [self.term("Golden Relay", source_path="src/relay-two.txt")])

        self.run_cli(first, second)

        sources = self.confirmed_terms()[0]["sources"]
        self.assertEqual({source["path"] for source in sources}, {"src/relay-one.txt", "src/relay-two.txt"})
        self.assertEqual({source["candidate_file"] for source in sources}, {str(first.resolve()), str(second.resolve())})

    def test_aliases_and_observed_asr_variants_are_merged_without_duplicates(self) -> None:
        first = self.candidate(
            "repo-one",
            [
                self.term(
                    "Ivory Compass",
                    aliases=["ivory pointer", "old compass"],
                    variants=[{"value": "ivory compas", "source": "neutral-one.json", "confidence": "observed"}],
                )
            ],
        )
        second = self.candidate(
            "repo-two",
            [
                self.term(
                    "Ivory Compass",
                    aliases=["old compass", "pale compass"],
                    variants=[
                        {"value": "ivory compas", "source": "neutral-one.json", "confidence": "observed"},
                        {"value": "ivory com pass", "source": "neutral-two.json", "confidence": "hypothesis"},
                    ],
                )
            ],
        )

        self.run_cli(first, second)

        item = self.confirmed_terms()[0]
        self.assertEqual(item["aliases"], ["ivory pointer", "old compass", "pale compass"])
        self.assertEqual(len(item["observed_asr_variants"]), 2)

    def test_unconfirmed_terms_do_not_modify_original_candidates(self) -> None:
        path = self.candidate("repo-one", [self.term("Jade Crossing", file_count=1)])
        before = path.read_bytes()

        self.run_cli(path)

        self.assertEqual(path.read_bytes(), before)
        self.assertNotIn("Jade Crossing", self.confirmed_names())

    def test_domain_glossary_path_is_never_written(self) -> None:
        first = self.candidate("repo-one", [self.term("Kilo Plaza")])
        second = self.candidate("repo-two", [self.term("Kilo Plaza")])
        forbidden = self.root / "domain-glossary.yaml"
        forbidden.write_text("keep: original\n", encoding="utf-8")

        result = self.run_cli(first, second, check=False, out=forbidden)

        self.assertEqual(result.returncode, 2)
        self.assertEqual(forbidden.read_text(encoding="utf-8"), "keep: original\n")

    def test_output_is_byte_deterministic(self) -> None:
        first = self.candidate("repo-one", [self.term("Lunar Archive")])
        second = self.candidate("repo-two", [self.term("Lunar Archive")])

        self.run_cli(first, second)
        first_bytes = self.out.read_bytes()
        self.run_cli(first, second)
        second_bytes = self.out.read_bytes()

        self.assertEqual(first_bytes, second_bytes)


if __name__ == "__main__":
    unittest.main()
