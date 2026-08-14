# Phase 1: normalization

Converts the pinned MultiSim CSV files, SimplifyUR, and the selected
Align-and-Shine output into one flat JSONL file per language and corpus.

Each line is one original–simplification pair. Required fields are `id`,
`original_id`, `language`, `source`, `corpus`, `upstream_split`, `original`,
`simple`, and `reference_index`. `upstream_split` preserves upstream metadata;
it does not determine the FEATS training/evaluation split.

The implementation is separated by source because each raw format requires a
different parser. All scripts remain together in `src/`:

```text
src/
├── common.py                    Shared paths and atomic writers
├── convert_multisim.py          MultiSim CSV converter
├── convert_align_and_shine.py   Align-and-Shine CSV converter
├── convert_simplifyur.py        SimplifyUR grouped-text converter
├── audit_corpora.py             Global schema/count/ID audit
└── prepare_feats_corpora.py     Small coordinator for all sources
```

Run an individual converter or the complete preparation:

```bash
python phase1_normalization/src/convert_multisim.py
python phase1_normalization/src/convert_align_and_shine.py
python phase1_normalization/src/convert_simplifyur.py
python phase1_normalization/src/prepare_feats_corpora.py all
python phase1_normalization/src/audit_corpora.py
```
