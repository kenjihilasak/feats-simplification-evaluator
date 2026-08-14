# Phase 1: normalization

Converts the pinned MultiSim CSV files, SimplifyUR, and the selected
Align-and-Shine output into one flat JSONL file per language and corpus.

Each line is one original–simplification pair. Required fields are `id`,
`original_id`, `language`, `source`, `corpus`, `upstream_split`, `original`,
`simple`, and `reference_index`. `upstream_split` preserves upstream metadata;
it does not determine the FEATS training/evaluation split.

```bash
python phase1_normalization/src/prepare_feats_corpora.py all
python phase1_normalization/src/prepare_feats_corpora.py audit-all
```

