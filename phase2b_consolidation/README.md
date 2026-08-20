# Phase 2b: consolidation

Phase 2b converts the cleaned Phase 2 observations into one exact canonical
original–simplification pair per row. It does not apply another quality filter.

- Exact duplicate pairs are represented once and retain every surviving source
  occurrence in `provenance`.
- Different simplifications of the same original remain separate and share a
  `canonical_original_id`.
- A pair is included when at least one occurrence survived Phase 2. The
  `partially_retained` field records inconsistent outcomes among duplicates.
- Upstream train/validation/test labels remain provenance only.

The flat output is one file per language:

```text
data/<language>/feats_consolidated.jsonl
```

The derived cross-corpus review registry is:

```text
groups/cross_corpus_multi_simplifications.jsonl
groups/cross_corpus_multi_simplifications_summary.md
```

It contains post-cleaning originals with at least two distinct surviving
simplifications and provenance from at least two distinct `(source, corpus)`
combinations. Each row groups the original, its canonical pair IDs, the
simplification texts, and their complete surviving provenance.

Run with the environment that provides PyArrow:

```bash
/scratch/pjbd103/miniconda3/envs/uncertainty-benchmark/bin/python \
  phase2b_consolidation/src/consolidate_cleaned.py

/scratch/pjbd103/miniconda3/envs/uncertainty-benchmark/bin/python \
  phase2b_consolidation/src/validate_consolidation.py

/scratch/pjbd103/miniconda3/envs/uncertainty-benchmark/bin/python \
  phase2b_consolidation/src/build_cross_corpus_groups.py

/scratch/pjbd103/miniconda3/envs/uncertainty-benchmark/bin/python \
  phase2b_consolidation/src/package_consolidated.py \
  --output-dir /path/to/release-assets \
  --version v0.1.0-rc2 \
  --archive-date 2026-08-20
```

The default input is the validated full Phase 2 run. Reports are written to
`reports/`, including `consolidation_summary.{csv,md}` and `validation.json`.
The release ZIP embeds `CONSOLIDATED_MANIFEST.csv`. Phase 3 should infer once per
`canonical_pair_id`; source-level statistics can then be expanded through the
`provenance` array.
