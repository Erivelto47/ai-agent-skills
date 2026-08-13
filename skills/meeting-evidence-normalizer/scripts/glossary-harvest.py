#!/usr/bin/env python3
"""Harvest glossary candidates from a repository using declarative profiles."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment dependent
    raise SystemExit("PyYAML is required. Install it with: python3 -m pip install PyYAML") from exc


TOOL_VERSION = "1.0.0"
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
PROFILES_DIR = SKILL_DIR / "profiles"
COMMON_WORDS_DIR = SKILL_DIR / "references" / "common-words"
WORD_CHAR_CLASS = r"A-Za-zÀ-ÖØ-öø-ÿ0-9_"
ALWAYS_EXCLUDE_GLOB = (
    "**/glossary-candidates*.yaml",
    "**/glossary-harvest-report*.md",
    "**/glossary-confirmed*.yaml",
    "**/glossary-confirm-report*.md",
)

VALID_PROFILE_KEYS = {"name", "description", "detect", "exclude_glob", "extractors"}
VALID_DETECT_KEYS = {"any_file_glob", "weight"}
VALID_EXTRACTOR_KEYS = {
    "id",
    "category",
    "kind",
    "file_glob",
    "pattern",
    "capture",
    "weight",
    "emits",
    "depths",
    "max_level",
}
VALID_KINDS = {"content_regex", "filename_regex", "path_segment", "markdown_heading"}
VALID_EMITS = {None, "term", "alias_pair"}

class HarvestError(Exception):
    def __init__(self, message: str, code: int = 2):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class Extractor:
    id: str
    category: str
    kind: str
    file_glob: tuple[str, ...] = ("**/*",)
    pattern: str | None = None
    capture: str | int | None = 1
    weight: float = 1.0
    emits: str = "term"
    depths: tuple[int, ...] = ()
    max_level: int = 3


@dataclass(frozen=True)
class Profile:
    name: str
    description: str
    detect: dict[str, Any]
    exclude_glob: tuple[str, ...]
    extractors: tuple[Extractor, ...]
    path: Path


@dataclass(frozen=True)
class Observation:
    term: str
    category: str
    file: str
    line: int
    extractor_id: str
    extractor_weight: float
    evidence_type: str
    alias: str | None = None


@dataclass
class Aggregate:
    canonical: str
    category: str
    aliases: set[str] = field(default_factory=set)
    observations: list[Observation] = field(default_factory=list)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        profiles = load_profiles(PROFILES_DIR)
        if args.list_profiles:
            print(json.dumps({"profiles": sorted(profiles)}, indent=2))
            return 0
        repo = Path(args.repo).expanduser().resolve() if args.repo else None
        if not repo:
            raise HarvestError("--repo is required", 2)
        if not repo.exists() or not repo.is_dir():
            raise HarvestError(f"Repository is not readable: {repo}", 3)
        selected, detection = resolve_profile(args.profile, profiles, repo)
        out_path = Path(args.out).expanduser().resolve()
        report_path = Path(args.report).expanduser().resolve() if args.report else out_path.with_name("glossary-harvest-report.md")
        candidates, report = harvest(
            repo=repo,
            profile=selected,
            detection=detection,
            transcripts=Path(args.transcripts).expanduser().resolve() if args.transcripts else None,
            min_score=args.min_score,
            max_candidates=args.max_candidates,
        )
        if args.dry_run:
            print(json.dumps({"status": "DRY_RUN", "profile": selected.name, "candidate_count": len(candidates["terms"])}, indent=2))
            return 0
        out_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(dump_yaml(candidates), encoding="utf-8")
        report_path.write_text(report, encoding="utf-8")
        print(json.dumps({"status": "OK", "profile": selected.name, "out": str(out_path), "report": str(report_path)}, indent=2))
        return 0
    except HarvestError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return exc.code


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Harvest glossary candidates from a repository.")
    parser.add_argument("--repo", help="Repository to harvest")
    parser.add_argument("--profile", help="Profile name from profiles/ or path to a custom profile")
    parser.add_argument("--transcripts", help="Optional processed transcript output root")
    parser.add_argument("--out", default="./glossary-candidates.yaml", help="Output YAML path")
    parser.add_argument("--report", help="Report path. Defaults next to --out")
    parser.add_argument("--min-score", type=float, default=0.0)
    parser.add_argument("--max-candidates", type=int, default=500)
    parser.add_argument("--list-profiles", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def load_profiles(root: Path) -> dict[str, Profile]:
    profiles: dict[str, Profile] = {}
    for path in sorted(root.glob("*.yaml")):
        if path.name == "profile.schema.yaml":
            continue
        profile = load_profile(path)
        profiles[profile.name] = profile
    return profiles


def load_profile(path: Path) -> Profile:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise HarvestError(f"Invalid YAML profile {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise HarvestError(f"Invalid profile {path}: top-level YAML must be a map")
    unknown = set(data) - VALID_PROFILE_KEYS
    if unknown:
        raise HarvestError(f"Invalid profile {path}: unknown key {sorted(unknown)[0]}; valid keys are {sorted(VALID_PROFILE_KEYS)}")

    name = require_string(data, "name", path)
    description = require_string(data, "description", path)
    detect = data.get("detect") or {}
    if not isinstance(detect, dict):
        raise HarvestError(f"Invalid profile {path}: detect must be a map")
    unknown_detect = set(detect) - VALID_DETECT_KEYS
    if unknown_detect:
        raise HarvestError(f"Invalid profile {path}: unknown key detect.{sorted(unknown_detect)[0]}; valid keys are {sorted(VALID_DETECT_KEYS)}")
    exclude_glob = tuple(str(v) for v in data.get("exclude_glob") or [])
    raw_extractors = data.get("extractors")
    if not isinstance(raw_extractors, list) or not raw_extractors:
        raise HarvestError(f"Invalid profile {path}: extractors must be a non-empty list")
    extractors = tuple(load_extractor(path, item) for item in raw_extractors)
    return Profile(name=name, description=description, detect=detect, exclude_glob=exclude_glob, extractors=extractors, path=path)


def require_string(data: dict[str, Any], key: str, path: Path) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise HarvestError(f"Invalid profile {path}: {key} must be a non-empty string")
    return value.strip()


def load_extractor(path: Path, data: Any) -> Extractor:
    if not isinstance(data, dict):
        raise HarvestError(f"Invalid profile {path}: extractor must be a map")
    unknown = set(data) - VALID_EXTRACTOR_KEYS
    if unknown:
        raise HarvestError(f"Invalid profile {path}: unknown key extractors[].{sorted(unknown)[0]}; valid keys are {sorted(VALID_EXTRACTOR_KEYS)}")
    kind = require_extractor_string(data, "kind", path)
    if kind not in VALID_KINDS:
        raise HarvestError(f"Invalid profile {path}: extractor kind {kind!r} must be one of {sorted(VALID_KINDS)}")
    emits = str(data.get("emits") or "term")
    if emits not in VALID_EMITS:
        raise HarvestError(f"Invalid profile {path}: emits {emits!r} must be one of {sorted(v for v in VALID_EMITS if v)}")
    return Extractor(
        id=require_extractor_string(data, "id", path),
        category=require_extractor_string(data, "category", path),
        kind=kind,
        file_glob=tuple(str(v) for v in data.get("file_glob") or ["**/*"]),
        pattern=str(data["pattern"]) if "pattern" in data else None,
        capture=data.get("capture", 1),
        weight=float(data.get("weight", 1.0)),
        emits=emits,
        depths=tuple(int(v) for v in data.get("depths") or []),
        max_level=int(data.get("max_level", 3)),
    )


def require_extractor_string(data: dict[str, Any], key: str, path: Path) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise HarvestError(f"Invalid profile {path}: extractors[].{key} must be a non-empty string")
    return value.strip()


def resolve_profile(profile_arg: str | None, profiles: dict[str, Profile], repo: Path) -> tuple[Profile, dict[str, Any]]:
    if profile_arg:
        custom = Path(profile_arg).expanduser()
        if custom.exists():
            profile = load_profile(custom.resolve())
            return profile, {"mode": "explicit_path", "reason": str(custom)}
        if profile_arg not in profiles:
            raise HarvestError(f"Unknown profile {profile_arg!r}. Available profiles: {', '.join(sorted(profiles))}")
        return profiles[profile_arg], {"mode": "explicit_name", "reason": profile_arg}

    best: tuple[int, str, Profile] | None = None
    for profile in profiles.values():
        score = detect_profile(profile, repo)
        if score > 0:
            candidate = (score, profile.name, profile)
            if best is None or candidate > best:
                best = candidate
    if best:
        score, _, profile = best
        return profile, {"mode": "auto", "score": score, "reason": "profile detect matched"}
    if "generic" not in profiles:
        raise HarvestError("No profile detected and generic profile is missing")
    return profiles["generic"], {"mode": "fallback", "score": 0, "reason": "no profile matched; generic fallback used"}


def detect_profile(profile: Profile, repo: Path) -> int:
    patterns = profile.detect.get("any_file_glob") or []
    weight = int(profile.detect.get("weight") or 1)
    for pattern in patterns:
        if any(repo.glob(str(pattern))):
            return weight
    return 0


def harvest(repo: Path, profile: Profile, detection: dict[str, Any], transcripts: Path | None, min_score: float, max_candidates: int) -> tuple[dict[str, Any], str]:
    files = list_repo_files(repo, profile.exclude_glob)
    observations: list[Observation] = []
    extractor_counts: Counter[str] = Counter()
    rejected: list[dict[str, Any]] = []
    for extractor in profile.extractors:
        for obs in run_extractor(repo, files, extractor):
            observations.append(obs)
            extractor_counts[obs.extractor_id] += 1
    aggregates = aggregate_observations(observations)
    spoken_index = build_spoken_index(transcripts)
    common_words = load_common_words(COMMON_WORDS_DIR)
    scored = []
    for aggregate in aggregates.values():
        candidate = score_candidate(aggregate, common_words, spoken_index)
        if candidate["harvest"]["score"] >= min_score:
            scored.append(candidate)
        else:
            rejected.append({"canonical": aggregate.canonical, "reason": "below_min_score", "score": candidate["harvest"]["score"]})
    scored.sort(key=lambda item: (-item["harvest"]["score"], item["canonical"]))
    scored = scored[:max_candidates]
    generated_at = stable_generated_at()
    output = {
        "schema_version": 1,
        "generated_at": generated_at,
        "profile": profile.name,
        "repo_fingerprint": repo_fingerprint(repo),
        "spokenness_active": spoken_index is not None,
        "tool": {"name": "glossary-harvest", "version": TOOL_VERSION},
        "terms": scored,
    }
    report = build_report(profile, detection, extractor_counts, scored, rejected, spoken_index is not None)
    return output, report


def list_repo_files(repo: Path, exclude_glob: tuple[str, ...]) -> list[Path]:
    exclude_patterns = ALWAYS_EXCLUDE_GLOB + exclude_glob
    git_files = git_tracked_files(repo)
    if git_files is None:
        paths = [p for p in repo.rglob("*") if p.is_file() and ".git" not in p.parts]
    else:
        paths = [repo / rel for rel in git_files]
    repo_root = repo.resolve()
    repo_paths: list[tuple[str, Path]] = []
    for path in paths:
        try:
            rel = path.resolve().relative_to(repo_root).as_posix()
        except (OSError, ValueError):
            continue
        repo_paths.append((rel, path))
    filtered = []
    for rel, path in sorted(repo_paths):
        if any(match_glob(rel, pattern) for pattern in exclude_patterns):
            continue
        if is_probably_text(path):
            filtered.append(path)
    return filtered


def git_tracked_files(repo: Path) -> list[Path] | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "ls-files", "--cached", "--others", "--exclude-standard"],
            text=True,
            capture_output=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return [Path(line) for line in result.stdout.splitlines() if line]


def is_probably_text(path: Path) -> bool:
    try:
        sample = path.read_bytes()[:1024]
    except OSError:
        return False
    if b"\0" in sample:
        return False
    try:
        sample.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def run_extractor(repo: Path, files: list[Path], extractor: Extractor) -> list[Observation]:
    if extractor.kind == "path_segment":
        return extract_path_segments(repo, files, extractor)
    matched_files = [p for p in files if any(match_glob(relative_posix(repo, p), pattern) for pattern in extractor.file_glob)]
    if extractor.kind == "content_regex":
        return extract_content_regex(repo, matched_files, extractor)
    if extractor.kind == "filename_regex":
        return extract_filename_regex(repo, matched_files, extractor)
    if extractor.kind == "markdown_heading":
        return extract_markdown_headings(repo, matched_files, extractor)
    raise HarvestError(f"Unsupported extractor kind {extractor.kind!r}")


def extract_content_regex(repo: Path, files: list[Path], extractor: Extractor) -> list[Observation]:
    if not extractor.pattern:
        raise HarvestError(f"Extractor {extractor.id} requires pattern")
    regex = re.compile(extractor.pattern)
    observations = []
    for path in files:
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for line_no, line in enumerate(lines, 1):
            for match in regex.finditer(line):
                observations.extend(observations_from_match(repo, path, line_no, match, extractor))
    return observations


def extract_filename_regex(repo: Path, files: list[Path], extractor: Extractor) -> list[Observation]:
    if not extractor.pattern:
        raise HarvestError(f"Extractor {extractor.id} requires pattern")
    regex = re.compile(extractor.pattern)
    observations = []
    for path in files:
        match = regex.search(path.name)
        if match:
            observations.extend(observations_from_match(repo, path, 1, match, extractor))
    return observations


def extract_path_segments(repo: Path, files: list[Path], extractor: Extractor) -> list[Observation]:
    seen: set[tuple[str, str]] = set()
    observations = []
    depths = extractor.depths or (1, 2)
    for path in files:
        rel_parts = Path(relative_posix(repo, path)).parts
        for depth in depths:
            index = depth - 1
            if 0 <= index < len(rel_parts) - 1:
                segment = rel_parts[index]
                key = (segment, relative_posix(repo, path))
                if key in seen:
                    continue
                seen.add(key)
                term = humanize(segment)
                if term:
                    observations.append(Observation(term, extractor.category, relative_posix(repo, path), 1, extractor.id, extractor.weight, extractor.id))
    return observations


def extract_markdown_headings(repo: Path, files: list[Path], extractor: Extractor) -> list[Observation]:
    observations = []
    regex = re.compile(r"^(#{1,%d})\s+(.+?)\s*$" % extractor.max_level)
    for path in files:
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for line_no, line in enumerate(lines, 1):
            match = regex.match(line)
            if match:
                term = clean_term(match.group(2))
                if term:
                    observations.append(Observation(term, extractor.category, relative_posix(repo, path), line_no, extractor.id, extractor.weight, extractor.id))
    return observations


def observations_from_match(repo: Path, path: Path, line_no: int, match: re.Match[str], extractor: Extractor) -> list[Observation]:
    if extractor.emits == "alias_pair":
        groups = match.groupdict()
        if "old" not in groups or "new" not in groups:
            raise HarvestError(f"Extractor {extractor.id} emits alias_pair but pattern lacks old/new named groups")
        old = humanize(groups["old"])
        new = humanize(groups["new"])
        if not old or not new:
            return []
        return [Observation(new, extractor.category, relative_posix(repo, path), line_no, extractor.id, extractor.weight, "rename_history", old)]
    value = capture_value(match, extractor.capture)
    term = humanize(value)
    if not term:
        return []
    return [Observation(term, extractor.category, relative_posix(repo, path), line_no, extractor.id, extractor.weight, extractor.id)]


def capture_value(match: re.Match[str], capture: str | int | None) -> str:
    if capture is None:
        return match.group(0)
    if isinstance(capture, int):
        return match.group(capture)
    if str(capture).isdigit():
        return match.group(int(str(capture)))
    return match.group(str(capture))


def aggregate_observations(observations: list[Observation]) -> dict[str, Aggregate]:
    aggregates: dict[str, Aggregate] = {}
    for obs in observations:
        key = normalized_key(obs.term)
        if not key:
            continue
        if key not in aggregates:
            aggregates[key] = Aggregate(canonical=obs.term, category=obs.category)
        aggregate = aggregates[key]
        aggregate.observations.append(obs)
        if obs.alias:
            aggregate.aliases.add(obs.alias)
    return aggregates


def score_candidate(aggregate: Aggregate, common_words: set[str], spoken_index: set[str] | None) -> dict[str, Any]:
    files = sorted({obs.file for obs in aggregate.observations})
    extractor_ids = sorted({obs.extractor_id for obs in aggregate.observations})
    extractor_weight = max(obs.extractor_weight for obs in aggregate.observations)
    distinctiveness = min(1.0, math.log1p(len(files)) / math.log1p(8))
    spokenness = spoken_score(aggregate.canonical, spoken_index)
    commonness_penalty = commonness(aggregate.canonical, common_words)
    score = distinctiveness * spokenness * extractor_weight * (1.0 - commonness_penalty)
    sources = sorted(
        {
            (obs.file, obs.line, obs.evidence_type)
            for obs in aggregate.observations
        }
    )
    item: dict[str, Any] = {
        "canonical": aggregate.canonical,
        "category": aggregate.category,
        "sources": [{"path": path, "line": line, "evidence_type": evidence_type} for path, line, evidence_type in sources],
        "confidence": "candidate",
        "harvest": {
            "score": round(score, 6),
            "breakdown": {
                "distinctiveness": round(distinctiveness, 6),
                "spokenness": round(spokenness, 6),
                "extractor_weight": round(extractor_weight, 6),
                "commonness_penalty": round(commonness_penalty, 6),
            },
            "file_count": len(files),
            "extractor_ids": extractor_ids,
        },
    }
    if aggregate.aliases:
        item["aliases"] = sorted(aggregate.aliases)
    return item


def spoken_score(term: str, spoken_index: set[str] | None) -> float:
    if spoken_index is None:
        return 1.0
    patterns = spoken_patterns(term)
    return 1.0 if any(pattern.search(entry) for pattern in patterns for entry in spoken_index) else 0.25


def commonness(term: str, common_words: set[str]) -> float:
    words = split_words(term)
    compact = normalize_text(term)
    if len(compact) <= 2:
        return 0.8
    if len(words) <= 1 and words and words[0] in common_words:
        return 0.75
    if len(words) <= 1 and len(compact) <= 4:
        return 0.45
    return 0.0


def build_spoken_index(transcripts: Path | None) -> set[str] | None:
    if transcripts is None:
        return None
    index: set[str] = set()
    if not transcripts.exists():
        return index
    for raw_path in sorted(transcripts.rglob("transcription.raw.json")):
        try:
            payload = json.loads(raw_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        texts = []
        if isinstance(payload, dict):
            if isinstance(payload.get("text"), str):
                texts.append(payload["text"])
            if isinstance(payload.get("segments"), list):
                texts.extend(str(item.get("text", "")) for item in payload["segments"] if isinstance(item, dict))
        for text in texts:
            normalized = normalize_spoken_text(text)
            index.add(normalized)
    return index


def load_common_words(root: Path) -> set[str]:
    words: set[str] = set()
    for path in sorted(root.glob("*.txt")):
        words.update(line.strip().lower() for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    return words


def build_report(profile: Profile, detection: dict[str, Any], extractor_counts: Counter[str], candidates: list[dict[str, Any]], rejected: list[dict[str, Any]], spoken_active: bool) -> str:
    lines = [
        "# Glossary Harvest Report",
        "",
        f"- Tool version: {TOOL_VERSION}",
        f"- Profile: `{profile.name}`",
        f"- Profile selection: {detection.get('mode')} ({detection.get('reason')})",
        f"- Spokenness filter: {'active' if spoken_active else 'inactive; pass --transcripts to enable loose ASR-aware matching'}",
        f"- Candidate count: {len(candidates)}",
        "",
        "## Extractor Counts",
        "",
    ]
    if extractor_counts:
        for extractor_id, count in sorted(extractor_counts.items()):
            lines.append(f"- `{extractor_id}`: {count}")
    else:
        lines.append("- No observations emitted.")
    lines.extend(["", "## Top Candidates", ""])
    for item in candidates[:25]:
        breakdown = item["harvest"]["breakdown"]
        source = item["sources"][0]
        lines.append(
            f"- `{item['canonical']}` ({item['category']}): score={item['harvest']['score']} "
            f"distinctiveness={breakdown['distinctiveness']} spokenness={breakdown['spokenness']} "
            f"weight={breakdown['extractor_weight']} commonness_penalty={breakdown['commonness_penalty']} "
            f"source={source['path']}:{source['line']}"
        )
    lines.extend(["", "## Rejected Examples", ""])
    if rejected:
        for item in rejected[:25]:
            lines.append(f"- `{item['canonical']}`: {item['reason']} (score={item['score']})")
    else:
        lines.append("- No candidates were rejected by score.")
    lines.extend([
        "",
        "## Next Step",
        "",
        "Use this anchored list as review input. Enrich accepted terms with aliases, pronunciation hints, possible contexts, and ambiguity notes only after reading the cited sources. Propose terms not backed by these sources separately as `no_code_anchor` candidates.",
        "",
    ])
    return "\n".join(lines)


def dump_yaml(data: dict[str, Any]) -> str:
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=120)


def stable_generated_at() -> str:
    return "1970-01-01T00:00:00+00:00"


def repo_fingerprint(repo: Path) -> str:
    return hashlib.sha256(str(repo.resolve()).encode("utf-8")).hexdigest()


def relative_posix(repo: Path, path: Path) -> str:
    return path.resolve().relative_to(repo.resolve()).as_posix()


def match_glob(path: str, pattern: str) -> bool:
    patterns = {pattern}
    collapsed = pattern
    while "**/" in collapsed:
        collapsed = collapsed.replace("**/", "", 1)
        patterns.add(collapsed)
    return any(fnmatch.fnmatch(path, item) or fnmatch.fnmatch("/" + path, item) for item in patterns)


def clean_term(value: str) -> str:
    value = re.sub(r"`([^`]+)`", r"\1", value)
    value = re.sub(r"\[[^\]]+\]\([^)]+\)", "", value)
    value = re.sub(rf"[^{WORD_CHAR_CLASS}./:-]+", " ", value).strip()
    return humanize(value)


def humanize(value: str) -> str:
    value = value.strip().strip("'\"`")
    value = re.sub(r"\.[A-Za-z0-9]+$", "", value)
    value = value.replace(":", " ").replace("/", " ").replace("-", " ").replace("_", " ")
    words = [word for word in value.split() if word]
    if not words:
        return ""
    return " ".join(word if word.isupper() else split_camel(word) for word in words).strip()


def split_camel(value: str) -> str:
    value = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", value)
    return value.strip()


def normalized_key(value: str) -> str:
    return normalize_text(value)


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def normalize_spoken_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^A-Za-z0-9]+", " ", value.lower())
    return re.sub(r"\s+", " ", value).strip()


def split_words(value: str) -> list[str]:
    value = humanize(value)
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return [word.lower() for word in re.split(r"[^A-Za-z0-9]+", value) if word]


def normalized_spoken_variant(term: str) -> str:
    words = split_words(term)
    return " ".join(words)


def spoken_patterns(term: str) -> list[re.Pattern[str]]:
    variant = normalized_spoken_variant(term)
    if not variant:
        return []
    escaped = re.escape(variant)
    escaped = re.sub(r"(?:\\ |\\\t)+", r"\\s+", escaped)
    return [re.compile(rf"(?<![{WORD_CHAR_CLASS}]){escaped}(?![{WORD_CHAR_CLASS}])", flags=re.IGNORECASE)]


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
