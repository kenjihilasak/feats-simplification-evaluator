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
| `gemma3_12b_pairwise_qlora` | `hannah-khallaf/e2r-strategy-gemma-3-12b-pairwise-qlora` | Six Gemma-formatted binary prompts per pair with label-specific thresholds. |

All revisions, thresholds, preprocessing, and batch settings are pinned under
`configs/models/`. XLM-R and E5 share `src/encoder_multilabel.py`; Qwen and
Gemma keep separate checkpoint-compatible prompt backends.

The Gemma adapter is public, but its `google/gemma-3-12b-it` base model is
gated. The Hugging Face account used on the cluster must accept the Gemma terms
and authenticate before either the smoke or full run can load the base weights.

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
  --output-dir /scratch/pjbd103/feats-release-assets/v0.2.0-rc2 \
  --version v0.2.0-rc2 \
  --archive-date 2026-08-24
```

The stable v1 sidecar schema identifiers retain their existing `feats-phase3-*`
names for compatibility; the repository stage and folder are Phase 3a.

## Full-run analysis

The full analysis joins each model's sidecars to Phase 2b provenance and
reports strategy cardinality separately by language and by source within each
language. A canonical pair is counted once per distinct source. It also reports
the complete 0–6 cardinality distribution, per-strategy prevalence and mean
scores, language/source/corpus breakdowns, and pairwise model agreement.

```bash
python phase3a_strategy_detection/src/analyze_full_run.py \
  --config phase3a_strategy_detection/configs/experiments/four_models_phase2b_full_v1.json
python phase3a_strategy_detection/src/analyze_gemma_anchored_consensus.py \
  --config phase3a_strategy_detection/configs/experiments/four_models_phase2b_full_v1.json
```

The principal answer is rendered in
[full_analysis.md](runs/2026-08-20_three_models_phase2b_full_v1/reports/full_analysis.md);
the underlying CSV tables are stored alongside it. These are descriptive output
statistics rather than accuracy estimates because the full corpus has no
verified gold strategy labels. The second command compares strict and inclusive
single-strategy consensus anchored in Gemma; it writes analysis reports only
and does not extract candidate JSONL data.

## Single-strategy gold candidates

The gold_candidates group derives reviewable candidates from the completed
three-model run. Majority voting is applied independently to each strategy:
Qwen, E5 and XLM-R each cast a binary vote using their pinned thresholds. A
pair is retained only when exactly one strategy receives at least two votes.

Run:

    python phase3a_strategy_detection/src/build_single_strategy_gold_candidates.py

Validate the generated records, counts and hashes independently:

    python phase3a_strategy_detection/src/validate_single_strategy_gold_candidates.py

The output includes the Phase 2b texts and provenance, the selected strategy,
vote count, supporting models, all individual model decisions/scores and a
quality tier. Reports break candidates down by language, strategy and source.
Generated data remain outside Git history. Model consensus makes these records
gold **candidates**; human annotation and adjudication are required before they
become a gold test dataset.

For review prioritization, the output distinguishes exact-singleton agreement
(at least two models predict only the winning strategy) from the broader
label-majority-only cases, where the winning label has a majority but
individual models may predict additional strategies.

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
