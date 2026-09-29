# Phase 2b: consolidation

Phase 2b consolidates exact duplicate pairs from Phase 2a; it does not apply a
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
| `phase2_retained_occurrence_count` | Number of those occurrences retained by Phase 2a. |
| `partially_retained` | `true` when only some identical occurrences survived. |
| `sources` | Distinct surviving data sources. |
| `corpora` | Distinct surviving `(source, corpus)` combinations. |
| `upstream_splits` | Original split labels, kept only as provenance. |
| `provenance` | Original source records and their metadata. |

## Run

```bash
PY=/scratch/pjbd103/miniconda3/envs/uncertainty-benchmark/bin/python

$PY phase2b_consolidation/src/consolidate_cleaned.py
$PY phase2b_consolidation/src/validate_consolidation.py
$PY phase2b_consolidation/src/build_cross_corpus_groups.py
```

Phase 3a and Phase 3b should infer once per `canonical_pair_id`; statistics by source can be
expanded later through `provenance`.

## Text repair variants

Text-repair variants fix narrowly defined upstream tokenization artifacts after
consolidation without replacing an existing Phase 2b dataset. Version
`feats-text-repair-v1.1` repairs glued sentence boundaries and Penn Treebank
bracket tokens.

| Variant | Input | Rows | Repaired rows | Validation | Audit |
|---|---|---:|---:|---|---|
| `2026-09-29_target_simple_textrepair_v1` | `2026-09-02_target_simple_v1` | 133,800 | 28,911 | Passed | Approved |
| `2026-09-29_base_textrepair_v1` | Base Phase 2b consolidation | 854,486 | 105,559 | Passed | Covered by the approved v1.1 rule audit |

In a repaired variant, `original` and `simple` contain repaired text, while
`original_raw` and `simple_raw` preserve their Phase 2b inputs byte for byte.
`text_repairs` records the applied rule and `repaired_duplicate_of` marks, but
does not remove, pairs that become duplicates.

Canonical IDs remain unchanged and identify the upstream text. This preserves
joins with later phases; use the explicit raw fields when the text from which an
ID was originally derived is required.

Run the target-simple variant:

```bash
python phase2b_consolidation/src/repair_text.py \
  --input-root phase2b_consolidation/runs/2026-09-02_target_simple_v1/data \
  --output-root phase2b_consolidation/runs/2026-09-29_target_simple_textrepair_v1/data \
  --reports-root phase2b_consolidation/runs/2026-09-29_target_simple_textrepair_v1/reports

python phase2b_consolidation/src/validate_text_repair.py \
  --input-root phase2b_consolidation/runs/2026-09-02_target_simple_v1/data \
  --output-root phase2b_consolidation/runs/2026-09-29_target_simple_textrepair_v1/data \
  --report phase2b_consolidation/runs/2026-09-29_target_simple_textrepair_v1/reports/validation.json
```

Run the base variant:

```bash
python phase2b_consolidation/src/repair_text.py \
  --input-root phase2b_consolidation/data \
  --output-root phase2b_consolidation/runs/2026-09-29_base_textrepair_v1/data \
  --reports-root phase2b_consolidation/runs/2026-09-29_base_textrepair_v1/reports

python phase2b_consolidation/src/validate_text_repair.py \
  --input-root phase2b_consolidation/data \
  --output-root phase2b_consolidation/runs/2026-09-29_base_textrepair_v1/data \
  --report phase2b_consolidation/runs/2026-09-29_base_textrepair_v1/reports/validation.json
```

The v1.1 audit method and acceptance record are documented in
[`docs/text_repair_plan.md`](docs/text_repair_plan.md).
