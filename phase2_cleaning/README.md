# Phase 2: cleaning

The pipeline removes a pair if at least one condition is true:

- the original is confidently classified as simple and its simplification as
  complex (`SMP < 0.1` on both sides);
- LaBSE cosine similarity is below `0.62`;
- LaBSE cosine similarity is above `0.95`.

The model checkpoints and thresholds are pinned in `configs/`. Run a pilot or
the full configuration with:

```bash
sbatch phase2_cleaning/jobs/submit_cleaning_gpu.sh \
  phase2_cleaning/configs/complexity_smp01_labse062_095_pilot_flat_v2.json
```

Each run contains flat language-level `cleaned/`, `decisions/`, `scores/`, and
`reports/` directories. Existing complete score files are reused, allowing a
stopped job to resume.

Validate a completed run before packaging it:

```bash
python phase2_cleaning/src/validate_run.py \
  --config phase2_cleaning/configs/complexity_smp01_labse062_095_full_flat_v2.json
```

The validator checks every input, score, decision, cleaned record, and summary
row. It writes `reports/validation.json` and returns a non-zero status if the
run is incomplete or inconsistent. `src/package_cleaned.py` refuses to package
a run without a successful validation report or when a cleaned file has changed
after validation.

The first full run retained 858,388 of 1,452,597 pairs (59.09%). It removed
594,209 pairs (40.91%): 14,039 complexity inversions, 218,463 pairs below the
LaBSE minimum, and 367,264 above the LaBSE maximum. Filter counts overlap, so
their sum can differ from the union removed. This removal rate is substantially
above the initial expectation and must be treated as an experimental cleaning
candidate. See the versioned summary in
`runs/2026-08-05_complexity_smp01_labse062_095_full_flat_v2/reports/`.
