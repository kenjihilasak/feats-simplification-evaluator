# Phase 3a: strategy detection

Phase 3a assigns six simplification-strategy probabilities to each canonical
pair retained by Phase 2b. It does not modify or filter the corpus.

## Input

The current experiments read the 854,486 canonical pairs from:

```text
phase2b_consolidation/data/<language>/feats_consolidated.jsonl
```

Each model runs once per `canonical_pair_id`. Source- and corpus-level reports
can later be expanded through the Phase 2b `provenance` field.

## Models

| Alias | Checkpoint | Inference |
|---|---|---|
| `xlmr_large_focal` | `hannah-khallaf/e2r-strategy-xlmr-large-focal` | Batched pair encoder, sigmoid, threshold `0.46`. |
| `multilingual_e5_large_bce` | `hannah-khallaf/e2r-strategy-multilingual-e5-large-bce` | Batched pair encoder with `query: ` on both inputs, threshold `0.23`. |
| `qwen2p5_7b_pairwise_qlora` | `hannah-khallaf/e2r-strategy-qwen2.5-7b-pairwise-qlora` | Six binary prompts per pair with label-specific thresholds. |

All revisions, thresholds, preprocessing, and batch settings are pinned under
`configs/models/`. XLM-R and E5 share `src/encoder_multilabel.py`; Qwen keeps
its prompt-based backend.

The fixed output order is:

1. Synonymy (`SYN`)
2. Modulation (`MOD`)
3. Compression (`COMP`)
4. Explanation (`EXPL`)
5. Syntactic Change (`SYNT`)
6. Omission (`OMIT`)

## Experiment layout

Input selection is defined once under `configs/experiments/`. Each model then
writes an independent sidecar prediction set:

```text
runs/<experiment_id>/
├── experiment_config.json
├── input_manifest.csv
└── models/<model_alias>/
    ├── run_config.json
    ├── predictions/<language>/feats_consolidated.jsonl
    └── reports/
```

Historical Qwen-only runs retain their original layout and remain readable.

## Completed full run

Run `2026-08-20_three_models_phase2b_full_v1` completed and passed validation
for all 12 languages and all three configured classifiers:

| Model | Validated predictions |
|---|---:|
| `xlmr_large_focal` | 854,486 |
| `multilingual_e5_large_bce` | 854,486 |
| `qwen2p5_7b_pairwise_qlora` | 854,486 |
| **Total** | **2,563,458** |

The release package contains the consolidated prediction JSONL files, run
configuration and JSON reports for every model. Temporary Qwen shards are not
included. `PHASE3A_MANIFEST.csv` records the count, byte size and SHA-256 of
every released prediction file.

```bash
python phase3a_strategy_detection/src/package_full_release.py \
  --output-dir /scratch/pjbd103/feats-release-assets/v0.2.0-rc1 \
  --version v0.2.0-rc1 \
  --archive-date 2026-08-23
```

The stable v1 sidecar schema identifiers retain their existing `feats-phase3-*`
names for compatibility; the repository stage and folder are Phase 3a.

## Prediction fields

| Field | Description |
|---|---|
| `id` | Canonical pair ID. |
| `canonical_pair_id` | Explicit copy of the canonical pair ID. |
| `model_alias` | Model configuration used. |
| `strategy_scores` | Six probabilities keyed by strategy code. |
| `predicted_codes` | Codes meeting their thresholds. |
| `predicted_labels` | Full names meeting their thresholds. |
| `strategy_count` | Number of predicted strategies. |
| `diagnostics` | Model-specific token or truncation information. |

Texts and corpus metadata are not duplicated; join predictions to Phase 2b by
`canonical_pair_id`.

## Canonical pilot

The deterministic pilot selects 25 random and 5 longest pairs from each
`(language, source, corpus)` stratum, then deduplicates by canonical pair ID.
The current sample contains 859 pairs from 29 strata and all 12 languages.

```bash
python phase3a_strategy_detection/src/prepare_canonical_pilot.py \
  --output-root phase3a_strategy_detection/samples/2026-08-20_phase2b_stratified_25_random_5_longest_v1 \
  --random-per-stratum 25 \
  --longest-per-stratum 5 \
  --seed 2026
```

Run one model:

```bash
python phase3a_strategy_detection/src/run_strategy_detection.py \
  --config phase3a_strategy_detection/configs/experiments/three_models_phase2b_pilot_v1.json \
  --model-alias xlmr_large_focal

python phase3a_strategy_detection/src/validate_run.py \
  --config phase3a_strategy_detection/configs/experiments/three_models_phase2b_pilot_v1.json \
  --model-alias xlmr_large_focal
```

Submit all three models as a Slurm array:

```bash
sbatch phase3a_strategy_detection/jobs/submit_three_models_pilot_gpu.sh
```

The earlier 855-pair Qwen pilot used Phase 2a occurrence IDs and remains a
historical pipeline validation. New comparisons and full runs use the canonical
Phase 2b experiment configs.
