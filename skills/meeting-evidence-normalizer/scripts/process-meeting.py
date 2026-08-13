#!/usr/bin/env python3
"""Configurable local meeting evidence normalizer."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_CONFIG = {
    "recordings": {
        "root": str(Path.home() / "Meetings"),
        "extensions": [".mp4", ".m4a", ".mp3", ".wav"],
    },
    "outputs": {
        "root": "./outputs/meeting-evidence",
    },
    "transcription": {
        "provider": "none",
        "command": [],
        "output_name": "transcription.raw",
        "output_format": "json",
        "cloud_fallback": False,
    },
    "glossary": {
        "path": "",
        "mode": "hints_only",
    },
    "quality": {
        "repetition_min_run": 5,
        "asr_degeneration_segment_ratio": 0.15,
    },
}


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DEFAULT_CONFIG_PATH = SKILL_DIR / "config" / "profile.example.yaml"
PROJECT_CONFIG_CANDIDATES = (
    ".meeting-evidence-normalizer.yaml",
    ".meeting-evidence-normalizer/config.yaml",
    ".agents/meeting-evidence-normalizer/profile.yaml",
)
USER_CONFIG_CANDIDATES = (
    Path.home() / ".config" / "meeting-evidence-normalizer" / "profile.yaml",
    Path.home() / ".meeting-evidence-normalizer.yaml",
)
WORD_CHAR_CLASS = r"A-Za-zÀ-ÖØ-öø-ÿ0-9_"
SHORT_CANDIDATE_MIN_LENGTH = 5
DEFAULT_REPETITION_MIN_RUN = 5
DEFAULT_ASR_DEGENERATION_SEGMENT_RATIO = 0.15
EXCLUDED_TEXT_WORD_LIMIT = 16


class MeetingNormalizerError(Exception):
    """Base expected error."""


class BlockedTranscriberNotAvailable(MeetingNormalizerError):
    """Raised when audio needs transcription but no command is configured or available."""


@dataclass(frozen=True)
class SourceInfo:
    path: Path
    filename: str
    size_bytes: int
    mtime: str
    sha256: str
    kind: str


def deep_copy(value: Any) -> Any:
    return json.loads(json.dumps(value))


def load_simple_yaml(path: Path) -> dict[str, Any]:
    """Load the small config shape used by this skill without external dependencies."""
    config = deep_copy(DEFAULT_CONFIG)
    if not path.exists():
        return config

    current_section: str | None = None
    current_key: str | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if not line.startswith(" ") and line.endswith(":"):
            current_section = line[:-1].strip()
            config.setdefault(current_section, {})
            current_key = None
            continue
        if current_section is None:
            continue
        stripped = line.strip()
        if stripped.startswith("- ") and current_key:
            config[current_section].setdefault(current_key, []).append(coerce_scalar(stripped[2:]))
            continue
        if ":" in stripped:
            key, value = stripped.split(":", 1)
            key = key.strip()
            value = value.strip()
            current_key = key
            if value == "":
                config[current_section][key] = []
            else:
                config[current_section][key] = coerce_scalar(value)
                current_key = key if isinstance(config[current_section][key], list) else None
    return config


def discover_config_path(start: Path) -> Path:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for directory in (current, *current.parents):
        for candidate in PROJECT_CONFIG_CANDIDATES:
            path = directory / candidate
            if path.exists():
                return path
    for path in USER_CONFIG_CANDIDATES:
        if path.exists():
            return path
    return DEFAULT_CONFIG_PATH


def coerce_scalar(value: str) -> Any:
    if value == "[]":
        return []
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if value.lower() in {"null", "none"}:
        return None
    return value.strip("'\"")


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def source_info(path: Path, kind: str) -> SourceInfo:
    stat = path.stat()
    mtime = datetime.fromtimestamp(stat.st_mtime, timezone.utc).astimezone().isoformat(timespec="seconds")
    return SourceInfo(
        path=path.resolve(),
        filename=path.name,
        size_bytes=stat.st_size,
        mtime=mtime,
        sha256=sha256_file(path),
        kind=kind,
    )


def safe_stem(path: Path) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", path.stem).strip("-")
    return value[:80] or "meeting"


def output_dir_for(outputs_root: Path, source: SourceInfo) -> Path:
    return outputs_root / f"{source.sha256[:16]}-{safe_stem(source.path)}"


def discover_recordings(root: Path, extensions: set[str]) -> list[Path]:
    if not root.exists():
        return []
    return sorted(p.resolve() for p in root.rglob("*") if p.is_file() and p.suffix.lower() in extensions)


def find_existing_manifest(outputs_root: Path, source_hash: str) -> Path | None:
    if not outputs_root.exists():
        return None
    for manifest in outputs_root.glob("*/manifest.json"):
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if data.get("source", {}).get("sha256") == source_hash and data.get("status") == "COMPLETE":
            return manifest
    return None


def preflight(config: dict[str, Any], require_transcriber: bool = False) -> dict[str, Any]:
    command = config.get("transcription", {}).get("command") or []
    executable = command[0] if isinstance(command, list) and command else ""
    tools = {
        "python3": shutil.which("python3"),
        "transcriber_executable": shutil.which(str(executable)) if executable else None,
    }
    result = {
        "checked_at": now_iso(),
        "tools": tools,
        "status": "OK",
    }
    if require_transcriber and not command:
        result["status"] = "BLOCKED_TRANSCRIBER_NOT_CONFIGURED"
        raise BlockedTranscriberNotAvailable(json.dumps(result, indent=2))
    if require_transcriber and executable and not tools["transcriber_executable"]:
        result["status"] = "BLOCKED_TRANSCRIBER_NOT_AVAILABLE"
        raise BlockedTranscriberNotAvailable(json.dumps(result, indent=2))
    return result


def render_command(command: list[Any], audio: Path, output_dir: Path, output_name: str) -> list[str]:
    values = {
        "audio": str(audio),
        "output_dir": str(output_dir),
        "output_name": output_name,
    }
    return [str(part).format(**values) for part in command]


def run_transcriber(audio: Path, output_dir: Path, config: dict[str, Any]) -> Path:
    transcriber = config["transcription"]
    output_name = str(transcriber.get("output_name") or "transcription.raw")
    cmd = render_command(transcriber.get("command") or [], audio, output_dir, output_name)
    if not cmd:
        raise BlockedTranscriberNotAvailable("BLOCKED_TRANSCRIBER_NOT_CONFIGURED")
    log_path = output_dir / "transcription.log"
    with log_path.open("w", encoding="utf-8") as log:
        subprocess.run(cmd, check=True, stdout=log, stderr=subprocess.STDOUT)
    raw_path = output_dir / f"{output_name}.json"
    if not raw_path.exists():
        candidates = sorted(output_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if candidates:
            candidates[0].replace(raw_path)
    if not raw_path.exists():
        raise MeetingNormalizerError("BLOCKED_TRANSCRIPTION: raw json was not produced")
    return raw_path


def load_raw(raw_path: Path) -> dict[str, Any]:
    with raw_path.open(encoding="utf-8") as handle:
        raw = json.load(handle)
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, list):
        text = " ".join(str(s.get("text", "")) for s in raw if isinstance(s, dict))
        return {"segments": raw, "text": text}
    raise MeetingNormalizerError("INVALID_RAW_TRANSCRIPTION")


def raw_segments(raw: dict[str, Any]) -> list[dict[str, Any]]:
    segments = raw.get("segments") if isinstance(raw.get("segments"), list) else []
    normalized = []
    if segments:
        for index, segment in enumerate(segments):
            if not isinstance(segment, dict):
                continue
            normalized.append({
                "id": segment.get("id", index),
                "start": segment.get("start"),
                "end": segment.get("end"),
                "text": str(segment.get("text", "")).strip(),
                "avg_logprob": segment.get("avg_logprob"),
                "compression_ratio": segment.get("compression_ratio"),
                "no_speech_prob": segment.get("no_speech_prob"),
            })
    elif raw.get("text"):
        normalized.append({"id": 0, "start": None, "end": None, "text": str(raw.get("text", "")).strip()})
    return normalized


def analyze_transcript(
    raw: dict[str, Any],
    repetition_min_run: int = DEFAULT_REPETITION_MIN_RUN,
    asr_degeneration_segment_ratio: float = DEFAULT_ASR_DEGENERATION_SEGMENT_RATIO,
) -> dict[str, Any]:
    segments = raw_segments(raw)
    suspicious = []
    for segment in segments:
        reasons = []
        avg_logprob = segment.get("avg_logprob")
        compression_ratio = segment.get("compression_ratio")
        no_speech_prob = segment.get("no_speech_prob")
        if isinstance(avg_logprob, (int, float)) and avg_logprob < -1.0:
            reasons.append("low_avg_logprob")
        if isinstance(compression_ratio, (int, float)) and compression_ratio > 2.4:
            reasons.append("high_compression_ratio")
        if isinstance(no_speech_prob, (int, float)) and no_speech_prob > 0.6:
            reasons.append("high_no_speech_prob")
        if reasons:
            suspicious.append({
                "segment_id": segment["id"],
                "start": segment.get("start"),
                "end": segment.get("end"),
                "reasons": reasons,
            })
    repetition_runs = detect_repetition_runs(segments, repetition_min_run)
    duration = max((s.get("end") or 0 for s in segments), default=None)
    segments_excluded = sum(run["count"] for run in repetition_runs)
    asr_degeneration_suspected = any(
        len(segments) > 0 and (run["count"] / len(segments)) > asr_degeneration_segment_ratio
        for run in repetition_runs
    )
    return {
        "schema_version": 1,
        "segment_count": len(segments),
        "duration_seconds": duration,
        "low_confidence_ranges": suspicious,
        "repetition_runs": repetition_runs,
        "asr_degeneration_suspected": asr_degeneration_suspected,
        "segments_excluded": segments_excluded,
        "repetition_min_run": repetition_min_run,
        "asr_degeneration_segment_ratio": asr_degeneration_segment_ratio,
        "metrics_available": sorted({
            k for s in segments for k in ("avg_logprob", "compression_ratio", "no_speech_prob") if s.get(k) is not None
        }),
    }


def detect_repetition_runs(segments: list[dict[str, Any]], min_run: int) -> list[dict[str, Any]]:
    runs = []
    current_text = ""
    current_start = 0
    for index, segment in enumerate(segments + [{"text": None}]):
        text = normalize_repetition_text(str(segment.get("text", ""))) if index < len(segments) else None
        if text and text == current_text:
            continue
        if current_text:
            count = index - current_start
            if count >= min_run:
                first = segments[current_start]
                last = segments[index - 1]
                runs.append({
                    "text": collapse_spaces(str(first.get("text", ""))),
                    "start_segment_id": first.get("id"),
                    "end_segment_id": last.get("id"),
                    "count": count,
                    "start": first.get("start"),
                    "end": last.get("end"),
                })
        current_text = text or ""
        current_start = index
    return runs


def normalize_repetition_text(text: str) -> str:
    return collapse_spaces(text).casefold()


def collapse_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def load_glossary_terms(path_value: str) -> list[dict[str, Any]]:
    if not path_value:
        return []
    path = Path(path_value).expanduser()
    if not path.exists():
        raise MeetingNormalizerError(f"BLOCKED_GLOSSARY_NOT_FOUND: {path}")

    terms: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    list_key: str | None = None
    list_fields = {"aliases", "phonetic_aliases", "observed_asr_variants", "context_keywords", "languages"}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if stripped.startswith("- canonical:"):
            if current:
                terms.append(current)
            current = {"canonical": stripped.split(":", 1)[1].strip().strip("'\"")}
            list_key = None
        elif current is not None and list_key == "observed_asr_variants" and stripped.startswith("- value:"):
            current.setdefault("observed_asr_variants", []).append(stripped.split("value:", 1)[1].strip().strip("'\""))
        elif current is not None and indent >= 4 and stripped.startswith("- ") and list_key in list_fields:
            current.setdefault(list_key, []).append(stripped[2:].strip().strip("'\""))
        elif current is not None and indent == 4 and ":" in stripped:
            key, value = stripped.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value == "[]":
                current[key] = []
                list_key = key
            elif value:
                current[key] = value.strip("'\"")
                list_key = None
            else:
                current[key] = []
                list_key = key
    if current:
        terms.append(current)
    return terms


def normalize_transcript(raw: dict[str, Any], glossary_path: str) -> dict[str, Any]:
    terms = load_glossary_terms(glossary_path)
    term_hits = []
    term_candidates = []
    segments = []
    for segment in raw_segments(raw):
        text = re.sub(r"\s+", " ", segment.get("text", "")).strip()
        normalized_text = text[:1].upper() + text[1:] if text else ""
        hits = find_term_hits(normalized_text, terms)
        candidates = find_context_candidates(normalized_text, terms, hits)
        term_hits.extend({"segment_id": segment["id"], **hit} for hit in hits)
        term_candidates.extend({"segment_id": segment["id"], **candidate} for candidate in candidates)
        segments.append({
            "id": segment["id"],
            "start": segment.get("start"),
            "end": segment.get("end"),
            "text": normalized_text,
            "raw_segment_id": segment["id"],
            "glossary_hits": hits,
            "glossary_candidates": candidates,
        })
    return {
        "schema_version": 1,
        "glossary_configured": bool(terms),
        "normalization_policy": {
            "raw_preserved": True,
            "glossary_is_hint": True,
            "promote_meeting_claims_to_canonical": False,
        },
        "segments": segments,
        "glossary_hits": term_hits,
        "glossary_candidates": term_candidates,
    }


def find_term_hits(text: str, terms: list[dict[str, Any]]) -> list[dict[str, str]]:
    hits = []
    for term in terms:
        canonical = str(term.get("canonical", ""))
        candidates = [("canonical", canonical)]
        for key in ("aliases", "phonetic_aliases", "observed_asr_variants"):
            values = term.get(key)
            if isinstance(values, list):
                candidates.extend((key, str(v)) for v in values)
        for match_type, candidate in candidates:
            if candidate and candidate_matches(text, candidate):
                hit = {
                    "canonical": canonical,
                    "matched": candidate,
                    "match_type": match_type,
                    "confidence": str(term.get("confidence", "unknown")),
                }
                if is_short_candidate(candidate):
                    hit["confidence"] = "short_alias_review"
                    hit["action"] = "review_raw_before_normalizing"
                elif match_type == "observed_asr_variants":
                    hit["confidence"] = "variant_candidate"
                    hit["action"] = "review_raw_before_normalizing"
                hits.append(hit)
                break
    return hits


def find_context_candidates(text: str, terms: list[dict[str, Any]], hits: list[dict[str, str]]) -> list[dict[str, Any]]:
    hit_names = {hit["canonical"] for hit in hits}
    candidates = []
    for term in terms:
        canonical = str(term.get("canonical", ""))
        if canonical in hit_names:
            continue
        keywords = term.get("context_keywords")
        if not isinstance(keywords, list):
            continue
        matched = [str(keyword) for keyword in keywords if candidate_matches(text, str(keyword))]
        if matched:
            candidates.append({
                "canonical": canonical,
                "matched_context_keywords": matched,
                "match_type": "context_candidate",
                "confidence": "candidate",
                "action": "review_raw_before_normalizing",
            })
    return candidates


def candidate_matches(text: str, candidate: str) -> bool:
    pattern = candidate_pattern(candidate)
    return bool(pattern and pattern.search(text))


def candidate_pattern(candidate: str) -> re.Pattern[str] | None:
    candidate = collapse_spaces(str(candidate))
    if not candidate:
        return None
    escaped = re.escape(candidate)
    escaped = re.sub(r"(?:\\ |\\\t)+", r"\\s+", escaped)
    return re.compile(rf"(?<![{WORD_CHAR_CLASS}]){escaped}(?![{WORD_CHAR_CLASS}])", flags=re.IGNORECASE)


def is_short_candidate(candidate: str) -> bool:
    compact = re.sub(r"[\s-]+", "", collapse_spaces(candidate))
    return len(compact) < SHORT_CANDIDATE_MIN_LENGTH


UNCERTAINTY_PATTERNS = [
    r"\bmaybe\b",
    r"\bperhaps\b",
    r"\bnot sure\b",
    r"\bi think\b",
    r"\bwe should verify\b",
    r"\bto confirm\b",
    r"\bacho\b",
    r"\btalvez\b",
    r"\bnao tenho certeza\b",
    r"\bnão tenho certeza\b",
    r"\bprecisa validar\b",
]

CONTRADICTION_PATTERNS = [
    r"\bbut\b",
    r"\bhowever\b",
    r"\bactually\b",
    r"\bcorrection\b",
    r"\bmas\b",
    r"\bporém\b",
    r"\bporem\b",
    r"\bna verdade\b",
    r"\bcorrigindo\b",
]


def extract_evidence(normalized: dict[str, Any], analysis: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    claims = []
    actions = []
    uncertainties = []
    contradictions = []
    segments = normalized.get("segments", [])
    excluded_segment_ids = excluded_ids_from_repetition_runs(segments, analysis.get("repetition_runs", []))
    excluded_low_confidence = excluded_low_confidence_entries(analysis.get("repetition_runs", []))
    for index, segment in enumerate(segments):
        if segment.get("id") in excluded_segment_ids:
            continue
        text = segment.get("text", "")
        ref = {"segment_id": segment.get("id"), "start": segment.get("start"), "end": segment.get("end")}
        if text:
            claims.append({"classification": "meeting_evidence", "text": text, "source": ref, "confidence": "meeting_evidence"})
        if re.search(r"\b(i will|we will|need to|follow up|vou|vamos|preciso)\b", text, flags=re.IGNORECASE):
            actions.append({"type": "action_mentioned_in_meeting", "text": text, "source": ref, "approved_task": False})
        if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in UNCERTAINTY_PATTERNS):
            uncertainties.append({"type": "linguistic_uncertainty", "text": text, "source": ref})
        if is_contradiction_candidate(segments, index, normalized.get("glossary_configured", False), window=1):
            contradictions.append({
                "topic": "meeting-discussion",
                "status": "conflicting_meeting_evidence",
                "classification": ["meeting_evidence", "needs_validation"],
                "claims": [text],
                "source": ref,
                "resolution": None,
                "requires_external_validation": True,
            })
    uncertainty_doc = {
        "schema_version": 1,
        "low_confidence_ranges": analysis.get("low_confidence_ranges", []),
        "excluded_low_confidence": excluded_low_confidence,
        "uncertain_terms": [
            candidate for candidate in normalized.get("glossary_candidates", []) if candidate.get("segment_id") not in excluded_segment_ids
        ] + [
            hit for hit in normalized.get("glossary_hits", [])
            if hit.get("segment_id") not in excluded_segment_ids
            and (
                hit.get("match_type") == "observed_asr_variants"
                or hit.get("confidence") == "short_alias_review"
            )
        ],
        "linguistic_uncertainties": uncertainties,
        "contradictions": contradictions,
    }
    evidence_doc = {
        "schema_version": 1,
        "claims": claims,
        "actions_mentioned": actions,
        "contradictions": contradictions,
    }
    return evidence_doc, uncertainty_doc


def is_contradiction_candidate(segments: list[dict[str, Any]], index: int, glossary_configured: bool, window: int = 1) -> bool:
    text = str(segments[index].get("text", ""))
    if not any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in CONTRADICTION_PATTERNS):
        return False
    if not glossary_configured:
        return True
    start = max(0, index - window)
    end = min(len(segments), index + window + 1)
    for segment in segments[start:end]:
        if segment.get("glossary_hits") or segment.get("glossary_candidates"):
            return True
    return False


def excluded_ids_from_repetition_runs(segments: list[dict[str, Any]], runs: list[dict[str, Any]]) -> set[Any]:
    excluded: set[Any] = set()
    for run in runs:
        start_index = find_segment_index(segments, run.get("start_segment_id"))
        end_index = find_segment_index(segments, run.get("end_segment_id"))
        if start_index is None or end_index is None:
            continue
        for segment in segments[start_index:end_index + 1]:
            excluded.add(segment.get("id"))
    return excluded


def find_segment_index(segments: list[dict[str, Any]], segment_id: Any) -> int | None:
    for index, segment in enumerate(segments):
        if segment.get("id") == segment_id:
            return index
    return None


def excluded_low_confidence_entries(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    entries = []
    for run in runs:
        entries.append({
            "type": "asr_repetition_excluded",
            "text": first_words(str(run.get("text", "")), EXCLUDED_TEXT_WORD_LIMIT),
            "repeat_count": run.get("count"),
            "source": {
                "start_segment_id": run.get("start_segment_id"),
                "end_segment_id": run.get("end_segment_id"),
                "start": run.get("start"),
                "end": run.get("end"),
            },
        })
    return entries


def first_words(text: str, limit: int) -> str:
    words = collapse_spaces(text).split()
    return " ".join(words[:limit])


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_manifest(source: SourceInfo, output_dir: Path, config: dict[str, Any], status: str, transcription_status: str, analysis: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": status,
        "processed_at": now_iso(),
        "source": {
            "path": str(source.path),
            "kind": source.kind,
            "filename": source.filename,
            "size_bytes": source.size_bytes,
            "mtime": source.mtime,
            "sha256": source.sha256,
        },
        "transcription": {
            "provider": config["transcription"].get("provider", "none"),
            "status": transcription_status,
            "log": "transcription.log",
        },
        "glossary": {
            "configured": bool(config.get("glossary", {}).get("path")),
            "mode": config.get("glossary", {}).get("mode", "hints_only"),
        },
        "quality": {
            "asr_degeneration_suspected": bool(analysis.get("asr_degeneration_suspected", False)),
            "repetition_run_count": len(analysis.get("repetition_runs", [])),
            "segments_excluded": int(analysis.get("segments_excluded", 0) or 0),
        },
        "output": {"path": str(output_dir)},
    }


def write_meeting_md(path: Path, source: SourceInfo, manifest: dict[str, Any], analysis: dict[str, Any], evidence: dict[str, Any], uncertainties: dict[str, Any]) -> None:
    quality_warning = quality_warning_md(analysis)
    content = f"""# {source.path.stem}
{quality_warning}

## Metadata
- Source: {source.path}
- Source SHA-256: {source.sha256}
- Input kind: {source.kind}
- Recorded/modified at: {source.mtime}
- Duration: {analysis.get("duration_seconds")}
- Processed at: {manifest["processed_at"]}

## Processing Quality
- Coverage: {analysis.get("segment_count", 0)} segment(s)
- Low-confidence ranges: {len(analysis.get("low_confidence_ranges", []))}
- Known limitations: speaker diarization is not inferred; meeting claims are not canonical decisions.

## Evidence
- Claims extracted: {len(evidence.get("claims", []))}
- Actions mentioned: {len(evidence.get("actions_mentioned", []))}
- Contradictions or corrections detected: {len(uncertainties.get("contradictions", []))}
- Uncertain terms: {len(uncertainties.get("uncertain_terms", []))}

## Source Traceability
- Manifest: `manifest.json`
- Raw transcript: `transcription.raw.json`
- Analysis: `transcription.analysis.json`
- Normalized transcript: `transcription.normalized.json`
- Evidence: `evidence.json`
- Uncertainties: `uncertainties.json`
"""
    path.write_text(content, encoding="utf-8")


def quality_warning_md(analysis: dict[str, Any]) -> str:
    if not analysis.get("asr_degeneration_suspected"):
        return ""
    runs = analysis.get("repetition_runs", [])
    if not runs:
        return ""
    total_segments = max(1, int(analysis.get("segment_count", 0) or 0))
    excluded = int(analysis.get("segments_excluded", 0) or 0)
    first = runs[0]
    last = runs[-1]
    total_duration = analysis.get("duration_seconds")
    run_duration = sum((run.get("end") or 0) - (run.get("start") or 0) for run in runs)
    if isinstance(total_duration, (int, float)) and total_duration > 0 and run_duration > 0:
        percent = (run_duration / total_duration) * 100
        percent_label = "recording"
    else:
        percent = (excluded / total_segments) * 100
        percent_label = "segments"
    return f"""
## Quality Warning
Suspected ASR degeneration: {excluded} segment(s) ({percent:.1f}% of {percent_label}) excluded as repeated/hallucinated block(s) from {first.get("start")} to {last.get("end")}. Treat this range as unreliable. See `uncertainties.json.excluded_low_confidence` for detail.
"""


def process_input(source_path: Path, source_kind: str, config: dict[str, Any], force: bool = False, dry_run: bool = False, reuse_raw: bool = False) -> dict[str, Any]:
    outputs_root = Path(str(config["outputs"]["root"])).expanduser()
    source = source_info(source_path, source_kind)
    output_dir = output_dir_for(outputs_root, source)
    raw_path = output_dir / "transcription.raw.json"
    existing = find_existing_manifest(outputs_root, source.sha256)
    if existing and not force:
        return {"status": "SKIPPED_ALREADY_PROCESSED", "source": str(source.path), "manifest": str(existing)}
    if dry_run:
        return {"status": "WOULD_PROCESS", "source": str(source.path), "output": str(output_dir), "sha256": source.sha256}

    output_dir.mkdir(parents=True, exist_ok=True)
    transcription_status = "provided"
    if source_kind == "raw_transcript":
        shutil.copyfile(source_path, raw_path)
    else:
        needs_transcription = not raw_path.exists() or (force and not reuse_raw)
        preflight(config, require_transcriber=needs_transcription)
        if needs_transcription:
            raw_path = run_transcriber(source_path, output_dir, config)
            transcription_status = "complete"
        else:
            transcription_status = "reused_raw"

    raw = load_raw(raw_path)
    quality_config = config.get("quality", {})
    analysis = analyze_transcript(
        raw,
        repetition_min_run=int(quality_config.get("repetition_min_run", DEFAULT_REPETITION_MIN_RUN) or DEFAULT_REPETITION_MIN_RUN),
        asr_degeneration_segment_ratio=float(
            quality_config.get("asr_degeneration_segment_ratio", DEFAULT_ASR_DEGENERATION_SEGMENT_RATIO)
            or DEFAULT_ASR_DEGENERATION_SEGMENT_RATIO
        ),
    )
    normalized = normalize_transcript(raw, str(config.get("glossary", {}).get("path") or ""))
    evidence, uncertainties = extract_evidence(normalized, analysis)
    manifest = build_manifest(source, output_dir, config, "COMPLETE", transcription_status, analysis)

    write_json(output_dir / "transcription.analysis.json", analysis)
    write_json(output_dir / "transcription.normalized.json", normalized)
    write_json(output_dir / "evidence.json", evidence)
    write_json(output_dir / "uncertainties.json", uncertainties)
    write_json(output_dir / "manifest.json", manifest)
    write_meeting_md(output_dir / "meeting.md", source, manifest, analysis, evidence, uncertainties)
    return {"status": "COMPLETE", "source": str(source.path), "manifest": str(output_dir / "manifest.json"), "output": str(output_dir), "sha256": source.sha256}


def process_many(config: dict[str, Any], force: bool = False, dry_run: bool = False, reuse_raw: bool = False) -> dict[str, Any]:
    root = Path(str(config["recordings"]["root"])).expanduser()
    extensions = {str(e).lower() for e in config["recordings"]["extensions"]}
    recordings = discover_recordings(root, extensions)
    results = []
    for recording in recordings:
        try:
            results.append(process_input(recording, "recording", config, force=force, dry_run=dry_run, reuse_raw=reuse_raw))
        except MeetingNormalizerError as exc:
            results.append({"status": "ERROR", "source": str(recording), "error": str(exc)})
    if not recordings:
        status = "NOTHING_TO_PROCESS"
    elif any(r["status"] == "ERROR" for r in results):
        status = "COMPLETE_WITH_ERRORS"
    elif all(r["status"] == "SKIPPED_ALREADY_PROCESSED" for r in results):
        status = "NOTHING_TO_PROCESS"
    else:
        status = "COMPLETE"
    return {"status": status, "results": results}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize local meeting recordings or raw transcript JSON into traceable evidence.")
    parser.add_argument("recording", nargs="?", help="Audio/video file path. Omit to scan recordings.root.")
    parser.add_argument("--raw-transcript", help="Existing transcript JSON to process without transcription")
    parser.add_argument("--config", help="Path to profile YAML. If omitted, search for a project-local profile before using the bundled example")
    parser.add_argument("--recordings-root", help="Override recordings.root")
    parser.add_argument("--output-root", help="Override outputs.root")
    parser.add_argument("--glossary", help="Override glossary.path")
    parser.add_argument("--force", action="store_true", help="Reprocess even when an existing manifest matches the source sha256")
    parser.add_argument("--reuse-raw", action="store_true", help="With --force, regenerate derived artifacts from existing transcription.raw.json without rerunning transcription")
    parser.add_argument("--dry-run", action="store_true", help="Only show what would be processed")
    parser.add_argument("--preflight", action="store_true", help="Run local tool preflight and exit")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    config_path = Path(args.config).expanduser() if args.config else discover_config_path(Path.cwd())
    config = load_simple_yaml(config_path)
    if args.recordings_root:
        config.setdefault("recordings", {})["root"] = args.recordings_root
    if args.output_root:
        config.setdefault("outputs", {})["root"] = args.output_root
    if args.glossary:
        config.setdefault("glossary", {})["path"] = args.glossary
    try:
        if args.preflight:
            print(json.dumps(preflight(config, require_transcriber=False), ensure_ascii=False, indent=2))
            return 0
        if args.raw_transcript:
            result = process_input(Path(args.raw_transcript).expanduser().resolve(), "raw_transcript", config, force=args.force, dry_run=args.dry_run)
        elif args.recording:
            result = process_input(Path(args.recording).expanduser().resolve(), "recording", config, force=args.force, dry_run=args.dry_run, reuse_raw=args.reuse_raw)
        else:
            result = process_many(config, force=args.force, dry_run=args.dry_run, reuse_raw=args.reuse_raw)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("status") not in {"COMPLETE_WITH_ERRORS", "ERROR"} else 2
    except BlockedTranscriberNotAvailable as exc:
        print(str(exc), file=sys.stderr)
        return 3
    except (MeetingNormalizerError, subprocess.CalledProcessError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
