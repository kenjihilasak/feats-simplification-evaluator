# Phase 2b: consolidation

Phase 2b consolidates exact duplicate pairs from Phase 2; it does not apply a
new quality filter. Each canonical pair is stored once, while all surviving
source occurrences remain in `provenance`. Different simplifications of the
same original share `canonical_original_id`.

## Outputs

| Path | One JSONL row represents |
|---|---|
| `data/<language>/feats_consolidated.jsonl` | One canonical original–simplification pair. |
| `groups/cross_corpus_multi_simplifications.jsonl` | One original with multiple surviving simplifications across corpora. |
| `groups/cross_corpus_multi_simplifications_summary.md` | Counts for the grouped registry. |
| `reports/` | Consolidation counts and validation results. |

## Consolidated pair fields

| Field | Description |
|---|---|
| `id` | Alias of `canonical_pair_id`. |
| `original_id` | Alias of `canonical_original_id`. |
| `canonical_original_id` | Stable ID derived from language and normalized original text. |
| `canonical_pair_id` | Stable ID derived from language, original, and simplification. |
| `language` | Language code. |
| `original` | Original sentence. |
| `simple` | Simplified sentence. |
| `phase1_occurrence_count` | Number of identical pair occurrences before cleaning. |
| `phase2_retained_occurrence_count` | Number of those occurrences retained by Phase 2. |
| `partially_retained` | `true` when only some identical occurrences survived. |
| `sources` | Distinct surviving data sources. |
| `corpora` | Distinct surviving `(source, corpus)` combinations. |
| `upstream_splits` | Original split labels, kept only as provenance. |
| `provenance` | Original source records and their metadata. |

## Cross-corpus group fields

The grouped file contains only originals with at least two distinct retained
pairs and at least two distinct `(source, corpus)` combinations.

| Field | Description |
|---|---|
| `group_id` | Alias of `canonical_original_id`. |
| `canonical_original_id` | Shared ID of the original sentence. |
| `language` | Language code. |
| `original` | Canonicalized original sentence. |
| `distinct_simplification_count` | Number of retained simplifications in the group. |
| `source_count` | Number of distinct sources represented. |
| `corpus_count` | Number of distinct `(source, corpus)` combinations. |
| `sources` | Sources represented in the group. |
| `corpora` | Corpus combinations represented in the group. |
| `simplifications` | Simplified texts, pair IDs, retention counts, and provenance. |

Each `simplifications[]` item reuses `canonical_pair_id`, `simple`, the two
occurrence counts, `partially_retained`, `sources`, `corpora`,
`upstream_splits`, and `provenance` with the meanings above.

## Run

```bash
PY=/scratch/pjbd103/miniconda3/envs/uncertainty-benchmark/bin/python

$PY phase2b_consolidation/src/consolidate_cleaned.py
$PY phase2b_consolidation/src/validate_consolidation.py
$PY phase2b_consolidation/src/build_cross_corpus_groups.py
```

Phase 3 should infer once per `canonical_pair_id`; statistics by source can be
expanded later through `provenance`.
