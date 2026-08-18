# Phase 3: strategy detection

Phase 3 annotates the sentence pairs retained by Phase 2. It does not remove
pairs and it never modifies the Phase 2 JSONL files.

The pipeline is model-agnostic. A run config selects a backend, model revisions,
input files, and output location. The first implemented backend is the released
Qwen2.5 pairwise QLoRA classifier, but corpus reading, output JSONL, validation,
and future reports are shared by all models.

## Current input

The first smoke run reads two records from the validated Phase 2 run:

`phase2_cleaning/runs/2026-08-05_complexity_smp01_labse062_095_full_flat_v2/cleaned`

The eventual full run contains 859,550 retained pairs in 29 JSONL files and 12
languages. It should be launched only after that Phase 2 selection is frozen.

## Output contract

Predictions are sidecar JSONL records joined to the cleaned corpus by `id`.
Each record contains the pair ID, model alias, six strategy probabilities,
thresholded strategy codes and labels, strategy count, and token diagnostics.

Model identifiers, revisions, thresholds, quantisation, taxonomy fingerprint,
environment versions, and input hashes are stored once in `run_config.json`.

Final files remain flat within each language:

```text
runs/<run_id>/predictions/en/multisim__ASSET.jsonl
runs/<run_id>/predictions/es/idem__iDEM.jsonl
```

`shards/` is reserved for resumable full runs. It is not part of the final
data layout.

## Model interface

Every backend implements the interface in `src/strategy_backend.py`:

- `prepare()`: resolve released metadata without loading model weights;
- `load()`: load the model once per process;
- `predict_pair(original, simple)`: return six probabilities and diagnostics;
- `provenance()`: describe the exact model and inference settings;
- `close()`: release model resources.

New models are registered in `src/model_registry.py`. They do not need changes
to the corpus runner or validator as long as they implement this interface.

## Qwen reference implementation

Backend: `qwen_pairwise`

Checkpoint:
`hannah-khallaf/e2r-strategy-qwen2.5-7b-pairwise-qlora`

The backend uses the checkpoint's pinned `inference_config.json`,
`thresholds.json`, taxonomy, and reference implementation. It performs six
binary decisions per sentence pair in this fixed order:

1. Synonymy (`SYN`)
2. Modulation (`MOD`)
3. Compression (`COMP`)
4. Explanation (`EXPL`)
5. Syntactic Change (`SYNT`)
6. Omission (`OMIT`)

It requires a CUDA GPU with bfloat16 support and loads the base model in 4-bit
NF4. The maximum prompt length is the released value of 2048 tokens.

## Environment and smoke run

The setup script creates an isolated virtual environment that reuses the tested
PyTorch/Transformers stack from `uncertainty-benchmark` without modifying that
Phase 2 environment:

```bash
bash phase3_strategy_detection/jobs/setup_environment.sh
```

Submit the smoke run:

```bash
sbatch phase3_strategy_detection/jobs/submit_smoke_gpu.sh
```

The job runs inference and then validates IDs, score ranges, label decisions,
counts, and hashes. Its report is written under the smoke run's `reports/`
directory.

## Stratified Qwen pilot

The deterministic pilot uses up to 25 random pairs and the 5 longest pairs
from every cleaned JSONL file. Overlaps are removed. This gives 855 pairs from
all 29 files and all 12 languages; the random seed is 2026.

Rebuild the sample only when its output directory does not already exist:

```bash
python phase3_strategy_detection/src/prepare_pilot_sample.py \
  --source-root phase2_cleaning/runs/2026-08-05_complexity_smp01_labse062_095_full_flat_v2/cleaned \
  --output-root phase3_strategy_detection/samples/2026-08-18_stratified_25_random_5_longest_v1 \
  --random-per-file 25 \
  --longest-per-file 5 \
  --seed 2026
```

Submit inference, validation, and report generation together:

```bash
sbatch phase3_strategy_detection/jobs/submit_pilot_gpu.sh
```

Slurm job 7274135 completed on one NVIDIA L40S in 14 minutes 51 seconds.
Inference itself took 467.18 seconds for 855 pairs, or 0.5464 seconds per pair.
At that measured rate, 859,550 pairs would require approximately 130.46
single-GPU hours. The estimate is conservative because the pilot intentionally
oversamples long pairs.

On the 117 pilot pairs that already have human labels, Qwen obtained micro F1
0.816 and macro F1 0.779. It predicted 3.154 strategies per pair versus 2.564
in the human annotations. Synonymy and Modulation were strongest; Syntactic
Change and Compression produced the most false positives. No prompt was
truncated.

The principal outputs are:

- `reports/pilot_quality_cost.md`: concise quantitative interpretation;
- `reports/qualitative_examples.md`: readable source/simplification examples;
- `reports/strategy_summary_language_source_corpus.csv`: per-corpus profile;
- `reports/human_label_agreement.csv`: per-label agreement;
- `reports/human_label_agreement_by_language.csv`: labelled-subset comparison;
- `reports/prediction_diagnostics.json`: prompt-length and truncation checks.

These results validate the pipeline, but not equal calibration across
languages. Before a full-corpus run, perform a small language-balanced manual
review and compare the two released encoder checkpoints with Qwen.
