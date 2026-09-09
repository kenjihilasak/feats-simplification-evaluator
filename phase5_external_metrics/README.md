# Phase 5 — external simplification metrics

Phase 5 scores the 348,520 canonical English pairs from Phase 2b with two
reference-free external baselines: LENS-SALSA and REFEREE. It is an audit and
evaluation layer only. Its scores never filter the corpus and are not training
labels or FEATS features.

Both metrics are English models. Any non-English record fails before model
loading; Phase 5 does not translate or emit exploratory multilingual scores.

## Inputs and outputs

The full experiment reads
`phase2b_consolidation/data/en/feats_consolidated.jsonl`. Smoke and pilot files
are deterministic derived inputs under the ignored `inputs/` directory.

Each metric writes an independent sidecar:

```text
runs/<experiment_id>/
├── experiment_config.json
├── input_manifest.json
└── metrics/<metric_alias>/
    ├── run_config.json
    ├── predictions.jsonl
    ├── reports/validation.json
    └── shards/shard-NNNNN-of-NNNNN/  # full distributed runs
```

Every prediction contains `canonical_pair_id`, `language`, `metric_alias`, the
generic `score`, its native named field (`lens_salsa_score` or
`referee_score`), SHA-256 hashes of both exact texts, model provenance and
diagnostics. Scores remain on their native scales and must not be subtracted,
averaged or thresholded across metrics.

## Models and licensing

- LENS-SALSA uses `davidheineman/lens-salsa` at revision
  `cc04094d084493e68bcd3eb196ff74e894cca00d` and `lens-metric==0.2.0`.
  Full runs retain the scalar only; the smoke/pilot config also retains the
  recovered edit tags for qualitative review.
- REFEREE reproduces the official implementation: pinned
  `microsoft/deberta-v3-base`, `source + sep_token + target`, truncation at 512
  subwords, 13 linear heads, and raw head index 12. The separately distributed
  `pretrained.bin` is not committed or redistributed because the upstream
  repository does not state a license for it.

Download the official REFEREE checkpoint from the link in the upstream README,
place it at `cache/referee/pretrained.bin`, compute `sha256sum` and set the
result as `checkpoint_sha256` in `configs/models/referee.json`. The runner
records and enforces that checksum.

## Prepare smoke and pilot inputs

```bash
python phase5_external_metrics/src/prepare_inputs.py smoke \
  --input phase2b_consolidation/data/en/feats_consolidated.jsonl \
  --output phase5_external_metrics/inputs/smoke_en.jsonl

python phase5_external_metrics/src/prepare_inputs.py pilot \
  --input phase2b_consolidation/data/en/feats_consolidated.jsonl \
  --output phase5_external_metrics/inputs/pilot_en_2000.jsonl \
  --target 2000 --seed 20260908 \
  --decisions-root phase2a_cleaning/runs/2026-09-02_complexity_target_simple_smp01_labse062_095_full_flat_v3/decisions \
  --strategies phase3a_strategy_detection/runs/2026-08-20_three_models_phase2b_full_v1/models/gemma3_12b_pairwise_qlora/predictions/en/feats_consolidated.jsonl
```

The 32-case smoke input includes seven real simplifications, seven identity
pairs, six strong omissions, six synthetic contradictions and six long inputs.
The pilot round-robins deterministic strata formed from corpus, length, LaBSE
band and Phase 3a strategy.

## Run

Create the three isolated Python 3.10 environments:

```bash
bash phase5_external_metrics/jobs/setup_lens_environment.sh
bash phase5_external_metrics/jobs/setup_referee_environment.sh
bash phase5_external_metrics/jobs/setup_analysis_environment.sh
```

Run smoke or pilot once in each appropriate environment:

```bash
.venv-phase5-lens/bin/python phase5_external_metrics/src/run_external_metrics.py \
  --config phase5_external_metrics/configs/experiments/smoke_en_v1.json \
  --metric-alias lens_salsa --resume

.venv-phase5-referee/bin/python phase5_external_metrics/src/run_external_metrics.py \
  --config phase5_external_metrics/configs/experiments/smoke_en_v1.json \
  --metric-alias referee --resume
```

Validate each output with the same environment and arguments, replacing the
runner name with `validate_run.py`. A failed run retains a flushed `.partial`
file; `--resume` accepts it only when its IDs are an exact prefix of the
configured shard.

After reviewing the pilot's ranges, truncation and rank disagreements, submit
the full 32-shard jobs:

```bash
sbatch phase5_external_metrics/jobs/submit_metric_shards_gpu.sh lens_salsa
sbatch phase5_external_metrics/jobs/submit_metric_shards_gpu.sh referee
```

When every shard validates, consolidate each metric without overwriting any
existing canonical output:

```bash
sbatch phase5_external_metrics/jobs/consolidate_metric_cpu.sh lens_salsa
sbatch phase5_external_metrics/jobs/consolidate_metric_cpu.sh referee
```

## Analysis

`analyze_metrics.py` reports native-score distributions by corpus, Spearman and
Kendall rank agreement, and the 100 largest normalized rank gaps. With an
optional Phase 4a CSV/JSONL containing `canonical_pair_id` and
`judgment`/`decision`, it excludes `uncertain` from quality denominators and
adds AUROC, average precision and canonical-original grouped bootstrap
intervals.

```bash
python phase5_external_metrics/src/analyze_metrics.py \
  --input phase2b_consolidation/data/en/feats_consolidated.jsonl \
  --lens phase5_external_metrics/runs/full_en_v1/metrics/lens_salsa/predictions.jsonl \
  --referee phase5_external_metrics/runs/full_en_v1/metrics/referee/predictions.jsonl \
  --output-dir phase5_external_metrics/runs/full_en_v1/reports
```

For the full corpus, `analyze_strata.py` adds distributions by source/corpus,
Phase 3a strategy, length, LaBSE band and complexity direction, plus within-original
ranges for originals with multiple simplifications. Run `verify_official_examples.py`
in each metric environment before the pilot; for LENS it also reports the
difference from the score printed in the official model card.

## Verification

```bash
python -m pytest phase5_external_metrics/tests -q
bash -n phase5_external_metrics/jobs/*.sh
```

Tests use fake backends and require no checkpoint or network access. They cover
batching, hashes, native fields, immutable outputs, resume-prefix checks,
sharding/consolidation order, deterministic sampling, duplicate IDs,
English-only enforcement and non-finite scores.
