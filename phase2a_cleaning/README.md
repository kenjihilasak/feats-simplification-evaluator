# Phase 2a: cleaning

Phase 2a scores every Phase 1 pair and removes it when any configured filter
rejects it. Models, revisions, thresholds, and per-file seeds are pinned in
`configs/`.

## Filters

| Rejection reason | Condition |
|---|---|
| `complexity_inversion` | Original predicted simple and simplification predicted complex, with SMP `< 0.1` on both sides. |
| `labse_below_min` | LaBSE similarity `< 0.62`. |
| `labse_above_max` | LaBSE similarity `> 0.95`. |

A pair is retained only when `rejection_reasons` is empty. Filter counts can
overlap.

## Outputs

| Path inside `runs/<run_id>/` | Content |
|---|---|
| `cleaned/<language>/*.jsonl` | Retained Phase 1 records. |
| `decisions/<language>/*.jsonl` | Final decision and rejection reasons for every pair. |
| `scores/complexity/<language>/*.jsonl` | Complexity predictions and SMP uncertainty. |
| `scores/labse/<language>/*.jsonl` | LaBSE similarity for every pair. |
| `reports/` | Quantitative, qualitative, and validation reports. |

## Cleaned JSONL fields

Cleaned records preserve the Phase 1 data unchanged.

| Field | Description |
|---|---|
| `id` | Unique source-pair occurrence ID. |
| `original_id` | Source-specific ID shared by references of one original. |
| `language` | Language code. |
| `source` | Dataset collection, such as MultiSim. |
| `corpus` | Corpus within the source. |
| `original` | Original sentence. |
| `simple` | Simplified sentence. |
| `reference_index` | Simplification index for the original. |
| `upstream_split` | Original split label, retained only as provenance. |
| `source_dataset` | Upstream dataset identifier. |
| `source_revision` | Upstream version or checksum. |
| `source_row` | Row number in the upstream snapshot. |

Optional source-specific metadata is also preserved unchanged.

## Audit JSONL fields

| File | Fields |
|---|---|
| `decisions` | `id`, `keep`, `rejection_reasons`, `labse_similarity`, and the complete `complexity` record. |
| `scores/labse` | `id` and `labse_similarity`. |
| `scores/complexity` | `id`, plus `original` and `simple` classifier results. |

Each complexity result stores the predicted label and ID, base probabilities,
Monte Carlo mean predictions and probabilities, and
`smp_max_mean_uncertainty`. SMP is `1 - max(mean probability)`; lower values
indicate higher confidence.

## Run and validate

```bash
CONFIG=phase2a_cleaning/configs/complexity_smp01_labse062_095_full_flat_v2.json

sbatch phase2a_cleaning/jobs/submit_cleaning_gpu.sh $CONFIG
python phase2a_cleaning/src/validate_run.py --config $CONFIG
```

Complete score files are reused after interruption. Validation checks all
inputs, scores, decisions, cleaned records, hashes, and summary rows.

## Current full run

| Measure | Pairs | Percent of input |
|---|---:|---:|
| Input | 1,454,003 | 100.00% |
| Retained | 859,550 | 59.12% |
| Removed by filter union | 594,453 | 40.88% |
| Complexity inversion | 14,044 | 0.97% |
| LaBSE below 0.62 | 218,570 | 15.03% |
| LaBSE above 0.95 | 367,399 | 25.27% |

The 40.88% removal rate is above the initial expectation, so this remains an
experimental cleaning candidate. Detailed results are under
`runs/2026-08-05_complexity_smp01_labse062_095_full_flat_v2/reports/`.

`src/package_cleaned.py` packages only successfully validated runs with
unchanged cleaned-file hashes.
