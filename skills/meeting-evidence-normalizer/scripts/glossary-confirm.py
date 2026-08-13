#!/usr/bin/env python3
"""Confirm glossary candidates using cross-source evidence."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment dependent
    raise SystemExit("PyYAML is required. Install it with: python3 -m pip install PyYAML") from exc


TOOL_VERSION = "1.0.0"
SCRIPT_DIR = Path(__file__).resolve().parent
HARVEST_SCRIPT = SCRIPT_DIR / "glossary-harvest.py"


class ConfirmError(Exception):
    def __init__(self, message: str, code: int = 2):
        super().__init__(message)
        self.code = code


def _load_harvest_module() -> Any:
    spec = importlib.util.spec_from_file_location("meeting_glossary_harvest", HARVEST_SCRIPT)
    if spec is None or spec.loader is None:
        raise ConfirmError(f"Unable to load harvest helpers from {HARVEST_SCRIPT}", 2)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_HARVEST = _load_harvest_module()
normalize_text = _HARVEST.normalize_text
dump_yaml = _HARVEST.dump_yaml
stable_generated_at = _HARVEST.stable_generated_at


@dataclass
class SourceTerm:
    candidate_file: Path
    canonical: str
    category: str
    aliases: list[str]
    observed_asr_variants: list[Any]
    sources: list[dict[str, Any]]
    score: float
    file_count: int
    spokenness: float
    commonness_penalty: float


@dataclass
class AggregatedTerm:
    key: str
    terms: list[SourceTerm] = field(default_factory=list)

    @property
    def source_repo_count(self) -> int:
        return len({term.candidate_file for term in self.terms})

    @property
    def total_file_count(self) -> int:
        return sum(term.file_count for term in self.terms)

    @property
    def max_spokenness(self) -> float:
        return max((term.spokenness for term in self.terms), default=0.0)

    @property
    def max_commonness_penalty(self) -> float:
        return max((term.commonness_penalty for term in self.terms), default=0.0)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        candidates = [Path(value).expanduser().resolve() for value in args.candidates]
        out_path = Path(args.out).expanduser().resolve()
        report_path = Path(args.report).expanduser().resolve()
        ensure_not_domain_glossary(out_path)
        ensure_not_domain_glossary(report_path)

        aggregated = load_candidates(candidates)
        confirmed, near_misses = confirm_terms(
            aggregated,
            source_threshold=args.source_threshold,
            file_count_threshold=args.file_count_threshold,
        )

        output = {
            "schema_version": 1,
            "generated_at": stable_generated_at(),
            "tool": {"name": "glossary-confirm", "version": TOOL_VERSION},
            "confirmation_rule": {
                "source_repo_count_threshold": args.source_threshold,
                "total_file_count_threshold": args.file_count_threshold,
                "max_spokenness_required": 1.0,
                "commonness_penalty_must_be_below": 0.75,
            },
            "terms": confirmed,
        }
        report = build_report(aggregated, confirmed, near_misses, args.source_threshold, args.file_count_threshold)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(dump_yaml(output), encoding="utf-8")
        report_path.write_text(report, encoding="utf-8")
        print(json.dumps({"status": "OK", "out": str(out_path), "report": str(report_path), "confirmed_count": len(confirmed)}, indent=2))
        return 0
    except ConfirmError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return exc.code


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Confirm glossary candidates across harvested sources.")
    parser.add_argument("--candidates", nargs="+", required=True, help="One or more glossary candidates YAML files")
    parser.add_argument("--out", required=True, help="Output YAML path for confirmed terms")
    parser.add_argument("--report", required=True, help="Output Markdown report path")
    parser.add_argument("--source-threshold", type=int, default=2, help="Minimum distinct candidate files for textual confirmation")
    parser.add_argument("--file-count-threshold", type=int, default=4, help="Minimum summed file_count across sources")
    return parser.parse_args(argv)


def ensure_not_domain_glossary(path: Path) -> None:
    if path.name == "domain-glossary.yaml":
        raise ConfirmError("glossary-confirm never writes to domain-glossary.yaml; choose a separate --out/--report path", 2)


def load_candidates(paths: list[Path]) -> dict[str, AggregatedTerm]:
    aggregated: dict[str, AggregatedTerm] = {}
    for path in paths:
        payload = read_candidate_file(path)
        terms = payload.get("terms")
        if not isinstance(terms, list):
            raise ConfirmError(f"Invalid candidates file {path}: terms must be a list", 2)
        for raw_term in terms:
            term = parse_term(path, raw_term)
            key = normalize_text(term.canonical)
            if not key:
                continue
            aggregated.setdefault(key, AggregatedTerm(key=key)).terms.append(term)
    return aggregated


def read_candidate_file(path: Path) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfirmError(f"Unable to read candidates file {path}: {exc}", 3) from exc
    except yaml.YAMLError as exc:
        raise ConfirmError(f"Invalid YAML candidates file {path}: {exc}", 2) from exc
    if not isinstance(payload, dict):
        raise ConfirmError(f"Invalid candidates file {path}: top-level YAML must be a map", 2)
    if payload.get("spokenness_active") is not True:
        raise ConfirmError(f"Candidates file {path} must have spokenness_active: true", 2)
    return payload


def parse_term(path: Path, raw_term: Any) -> SourceTerm:
    if not isinstance(raw_term, dict):
        raise ConfirmError(f"Invalid term in {path}: each term must be a map", 2)
    canonical = require_string(raw_term, "canonical", path)
    category = require_string(raw_term, "category", path)
    harvest = raw_term.get("harvest")
    if not isinstance(harvest, dict):
        raise ConfirmError(f"Invalid term {canonical!r} in {path}: harvest must be a map", 2)
    breakdown = harvest.get("breakdown")
    if not isinstance(breakdown, dict):
        raise ConfirmError(f"Invalid term {canonical!r} in {path}: harvest.breakdown must be a map", 2)
    sources = raw_term.get("sources") or []
    if not isinstance(sources, list):
        raise ConfirmError(f"Invalid term {canonical!r} in {path}: sources must be a list", 2)
    return SourceTerm(
        candidate_file=path,
        canonical=canonical,
        category=category,
        aliases=string_list(raw_term.get("aliases")),
        observed_asr_variants=list_value(raw_term.get("observed_asr_variants")),
        sources=[dict(item) for item in sources if isinstance(item, dict)],
        score=float(harvest.get("score") or 0.0),
        file_count=int(harvest.get("file_count") or 0),
        spokenness=float(breakdown.get("spokenness") or 0.0),
        commonness_penalty=float(breakdown.get("commonness_penalty") or 0.0),
    )


def require_string(data: dict[str, Any], key: str, path: Path) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfirmError(f"Invalid term in {path}: {key} must be a non-empty string", 2)
    return value.strip()


def string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def list_value(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def confirm_terms(
    aggregated: dict[str, AggregatedTerm],
    source_threshold: int,
    file_count_threshold: int,
) -> tuple[list[dict[str, Any]], list[AggregatedTerm]]:
    confirmed_terms: list[dict[str, Any]] = []
    near_misses: list[AggregatedTerm] = []
    for aggregate in sorted(aggregated.values(), key=lambda item: canonical_for_sort(item).lower()):
        if is_confirmed(aggregate, source_threshold, file_count_threshold):
            confirmed_terms.append(build_confirmed_entry(aggregate))
        elif is_near_miss(aggregate, source_threshold, file_count_threshold):
            near_misses.append(aggregate)
    return confirmed_terms, near_misses


def is_confirmed(aggregate: AggregatedTerm, source_threshold: int, file_count_threshold: int) -> bool:
    textual_threshold = aggregate.source_repo_count >= source_threshold or aggregate.total_file_count >= file_count_threshold
    return textual_threshold and aggregate.max_spokenness == 1.0 and all(
        term.commonness_penalty < 0.75 for term in aggregate.terms
    )


def is_near_miss(aggregate: AggregatedTerm, source_threshold: int, file_count_threshold: int) -> bool:
    if aggregate.max_spokenness < 1.0 and (aggregate.source_repo_count >= source_threshold or aggregate.total_file_count >= file_count_threshold):
        return True
    if aggregate.max_spokenness == 1.0 and (
        aggregate.source_repo_count == source_threshold - 1 or aggregate.total_file_count == file_count_threshold - 1
    ):
        return True
    return False


def build_confirmed_entry(aggregate: AggregatedTerm) -> dict[str, Any]:
    best = max(aggregate.terms, key=lambda term: (term.score, term.canonical))
    entry: dict[str, Any] = {
        "canonical": best.canonical,
        "category": best.category,
    }
    aliases = sorted({alias for term in aggregate.terms for alias in term.aliases})
    if aliases:
        entry["aliases"] = aliases
    variants = merge_observed_asr_variants(aggregate.terms)
    if variants:
        entry["observed_asr_variants"] = variants
    entry["sources"] = merge_sources(aggregate.terms)
    entry["confidence"] = "cross_source_confirmed"
    return entry


def merge_observed_asr_variants(terms: list[SourceTerm]) -> list[Any]:
    seen: set[str] = set()
    merged: list[Any] = []
    for value in [variant for term in terms for variant in term.observed_asr_variants]:
        key = json.dumps(value, sort_keys=True, ensure_ascii=False)
        if key in seen:
            continue
        seen.add(key)
        merged.append(value)
    return sorted(merged, key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=False))


def merge_sources(terms: list[SourceTerm]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    merged: list[dict[str, Any]] = []
    for term in sorted(terms, key=lambda item: str(item.candidate_file)):
        for source in term.sources:
            enriched = dict(source)
            enriched["candidate_file"] = str(term.candidate_file)
            key = json.dumps(enriched, sort_keys=True, ensure_ascii=False)
            if key in seen:
                continue
            seen.add(key)
            merged.append(enriched)
    return sorted(merged, key=lambda item: (str(item.get("candidate_file", "")), str(item.get("path", "")), int(item.get("line") or 0), str(item.get("evidence_type", ""))))


def canonical_for_sort(aggregate: AggregatedTerm) -> str:
    best = max(aggregate.terms, key=lambda term: (term.score, term.canonical))
    return best.canonical


def build_report(
    aggregated: dict[str, AggregatedTerm],
    confirmed: list[dict[str, Any]],
    near_misses: list[AggregatedTerm],
    source_threshold: int,
    file_count_threshold: int,
) -> str:
    by_key = {key: aggregate for key, aggregate in aggregated.items()}
    lines = [
        "# Glossary Confirm Report",
        "",
        f"- Tool version: {TOOL_VERSION}",
        f"- Rule: `(source_repo_count >= {source_threshold} OR total_file_count_across_sources >= {file_count_threshold}) AND max_spokenness_across_sources == 1.0 AND commonness_penalty < 0.75 in every source`",
        f"- Confirmed count: {len(confirmed)}",
        "",
        "## Confirmed Terms",
        "",
    ]
    if confirmed:
        for item in confirmed:
            aggregate = by_key[normalize_text(item["canonical"])]
            source_list = ", ".join(sorted({str(term.candidate_file) for term in aggregate.terms}))
            lines.append(
                f"- `{item['canonical']}`: sources={aggregate.source_repo_count} file_count={aggregate.total_file_count} "
                f"max_spokenness={aggregate.max_spokenness} max_commonness_penalty={aggregate.max_commonness_penalty} "
                f"threshold_met={'source_count' if aggregate.source_repo_count >= source_threshold else 'file_count'}"
            )
            lines.append(f"  - Candidate files: {source_list}")
            for source in item["sources"]:
                lines.append(f"  - {source['candidate_file']} :: {source.get('path')}:{source.get('line')}")
    else:
        lines.append("- No terms crossed the confirmation rule.")
    lines.extend(["", "## Near Misses", ""])
    if near_misses:
        for aggregate in near_misses:
            lines.append(
                f"- `{canonical_for_sort(aggregate)}`: sources={aggregate.source_repo_count} file_count={aggregate.total_file_count} "
                f"max_spokenness={aggregate.max_spokenness}"
            )
    else:
        lines.append("- No near misses.")
    lines.extend([
        "",
        "## Next Step",
        "",
        "Review the confirmed batch before merging into a private glossary. Continue the slower manual glossary procedure for unconfirmed candidates.",
        "",
    ])
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
