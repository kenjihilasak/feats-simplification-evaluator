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

