# Phase 2: cleaning

The pipeline removes a pair if at least one condition is true:

- the original is confidently classified as simple and its simplification as
  complex (`SMP < 0.1` on both sides);
- LaBSE cosine similarity is below `0.62`;
- LaBSE cosine similarity is above `0.95`.

Model checkpoints, revisions, thresholds, and per-file random seeds are pinned
in `configs/`. The explicit seed map keeps existing complexity scores
reproducible when new corpus files are added.

## Run and validate

```bash
sbatch phase2_cleaning/jobs/submit_cleaning_gpu.sh \
  phase2_cleaning/configs/complexity_smp01_labse062_095_full_flat_v2.json

python phase2_cleaning/src/validate_run.py \
  --config phase2_cleaning/configs/complexity_smp01_labse062_095_full_flat_v2.json
```

Each run uses flat language-level `cleaned/`, `decisions/`, and
`scores/{complexity,labse}/` directories. Complete score files are reused, so a
stopped job can resume without recomputing them. The validator checks every
input, score, decision, cleaned record, hash, and summary row and writes
`reports/validation.json`.

## Current full run

The validated run covers all 29 Phase 1 files:

| Measure | Pairs | Percent of input |
|---|---:|---:|
| Input | 1,454,003 | 100.00% |
| Retained | 859,550 | 59.12% |
| Removed by filter union | 594,453 | 40.88% |
| Complexity inversion | 14,044 | 0.97% |
| LaBSE below 0.62 | 218,570 | 15.03% |
| LaBSE above 0.95 | 367,399 | 25.27% |

Filter counts overlap. The removal rate is substantially above the initial
expectation, so this is an experimental candidate rather than the final FEATS
training selection. The quantitative summary and qualitative checks are in
`runs/2026-08-05_complexity_smp01_labse062_095_full_flat_v2/reports/`.

The Markdown summary suppresses repeated consecutive language, source, and
corpus labels for readability. The CSV keeps every value on every row for
machine processing.

`src/package_cleaned.py` only packages a run with a successful validation
report and unchanged cleaned-file hashes. It embeds `CLEANED_MANIFEST.csv` at
the ZIP root. Public distribution remains subject to the source-specific
restrictions documented in the root README.
