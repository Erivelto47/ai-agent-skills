# Glossary Harvest Guide

Use `scripts/glossary-harvest` to produce an anchored candidate list before enriching a private glossary.

The harvester is intentionally deterministic and offline. It does not call an LLM, does not use the network, and does not promote candidates above `confidence: candidate`.

For multiple repositories or evidence sources, the intended flow is:

```text
glossary-harvest per source -> glossary-confirm across generated candidates -> human review of confirmed batch -> slower manual review of remaining candidates
```

`glossary-confirm` is only a triage shortcut for terms with strong structural evidence and real speech confirmation. It does not replace the Agent Discovery Procedure in `glossary-guide.md` for terms that do not cross the confirmation threshold.

## Basic Usage

```bash
skills/meeting-evidence-normalizer/scripts/glossary-harvest --repo /path/to/repo
```

Useful options:

```bash
skills/meeting-evidence-normalizer/scripts/glossary-harvest \
  --repo /path/to/repo \
  --profile generic \
  --out /tmp/glossary-candidates.yaml \
  --report /tmp/glossary-harvest-report.md
```

Use `--transcripts /path/to/processed-meeting-outputs` to enable local spokenness scoring. This reads `transcription.raw.json` files and loosely compares spoken forms against harvested terms.

When transcripts are provided, `glossary-candidates.yaml` includes `spokenness_active: true`. Without transcripts it includes `spokenness_active: false`; such files are intentionally rejected by `glossary-confirm` because neutral spokenness scores are not evidence that people used the term in speech.

## Cross-Source Confirmation

Run `glossary-confirm` against already generated candidate files. It never reruns harvest and never writes to `domain-glossary.yaml`.

```bash
skills/meeting-evidence-normalizer/scripts/glossary-confirm \
  --candidates /tmp/source-a/candidates.yaml /tmp/source-b/candidates.yaml /tmp/source-c/candidates.yaml \
  --out /tmp/glossary-confirmed.yaml \
  --report /tmp/glossary-confirm-report.md
```

The default rule is:

```text
cross_source_confirmed =
    (source_repo_count >= 2 OR total_file_count_across_sources >= 4)
    AND max_spokenness_across_sources == 1.0
```

`source_repo_count` is the number of distinct `candidates.yaml` files containing the normalized term. `total_file_count_across_sources` is the sum of each term's `harvest.file_count`. `max_spokenness_across_sources` is the maximum `harvest.breakdown.spokenness` across those files.

The `2` and `4` thresholds can be changed with `--source-threshold` and `--file-count-threshold`, but the exact `max_spokenness == 1.0` gate is deliberate. Textual presence alone is not enough for automatic confirmation.

Confirmed output uses the glossary shape where the script has evidence: `canonical`, `category`, merged `aliases`, merged `observed_asr_variants` when present in the inputs, all source entries with their candidate-file provenance, and `confidence: cross_source_confirmed`. It deliberately omits enrichment fields such as `possible_contexts` and `ambiguity_note`.

The report explains why each confirmed term crossed the threshold and lists near misses for manual review. Terms that do not cross the threshold remain unchanged in their original `candidates.yaml` files.

## Output

`glossary-candidates.yaml` follows the glossary schema where possible, but only emits populated fields. Empty enrichment fields such as `possible_contexts`, `phonetic_aliases`, and `ambiguity_note` are deliberately omitted.

`glossary-harvest-report.md` summarizes profile selection, extractor counts, scoring, rejected examples, and next steps.

After reading each cited source, follow the Agent Discovery Procedure in `glossary-guide.md` to enrich accepted candidates. That procedure applies to code-harvested candidates the same way it applies to documentation-derived candidates.

## Scoring

The score is:

```text
distinctiveness x spokenness x extractor_weight x (1 - commonness_penalty)
```

`distinctiveness` uses a saturating curve based on the number of distinct files. The current curve is `log(1 + file_count) / log(1 + 8)`, capped at `1.0`. This rewards repeated concepts without letting large repositories dominate by raw count.

`spokenness` is `1.0` when no transcript root is provided. When transcripts are provided, spoken terms score higher than equally distinctive terms that never appear in meeting speech.

`commonness_penalty` reduces isolated ordinary words and short terms. Multi-word and compound terms are not penalized by the dictionary lists.

The cross-source confirmation commonness gate reduces but does not eliminate generic multi-word noise, because dictionary commonness only applies to one-word terms; treat `cross_source_confirmed` as a fast human-review batch before updating `domain-glossary.yaml`, not as final truth.

`extractor_weight` comes from the selected profile.

## Writing A Profile

Profiles live in `profiles/<name>.yaml` and contain only declarative extractors. The engine should not be patched for a new stack.

Example for a stack not bundled here:

```yaml
name: sample-framework
description: Example profile for a fictional framework.

detect:
  any_file_glob: ["sample.config"]
  weight: 10

exclude_glob: ["**/build/**", "**/vendor/**"]

extractors:
  - id: sample_status_constants
    category: status
    kind: content_regex
    file_glob: ["**/*.sample"]
    pattern: '^status\s+([A-Z][A-Z0-9_]{2,})$'
    capture: 1
    weight: 1.0

  - id: sample_rename_history
    category: alias_history
    kind: filename_regex
    file_glob: ["**/changes/*.sample"]
    pattern: 'rename_(?P<old>.+?)_to_(?P<new>.+?)\.sample$'
    emits: alias_pair
    weight: 1.5
```

Supported extractor kinds:

- `content_regex`: run a regex per line and emit the configured capture group.
- `filename_regex`: run a regex against the basename.
- `path_segment`: emit directory names at configured depths.
- `markdown_heading`: emit Markdown headings up to `max_level`.

Use `emits: alias_pair` when a filename or line records a rename. The regex must contain named groups `old` and `new`; the new name becomes the canonical candidate and the old name becomes an alias.

## Local Real-Repository Validation

Validation against a real repository is useful, but outputs can contain private vocabulary. Write them to `/tmp` or another ignored location and never commit them.
