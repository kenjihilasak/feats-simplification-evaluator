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
