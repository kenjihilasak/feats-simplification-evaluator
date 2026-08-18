# Phase 1: normalization

Phase 1 converts every supported raw format into one flat JSONL file per
language and source corpus. The canonical local output contains 29 files and
1,454,003 pairs across 12 languages, including the completed iDEM and Saaq
al-Bambuu conversions.

The latest public data package is the earlier [v0.1.0-rc1 normalized ZIP](https://github.com/kenjihilasak/feats-simplification-evaluator/releases/download/v0.1.0-rc1/feats-phase1-normalized-v0.1.0-rc1.zip).
See the root README for the difference between complete local processing and
the sources that may be redistributed publicly.

## Canonical record

Each line is one original–simplification pair. Required fields are `id`,
`original_id`, `language`, `source`, `corpus`, `upstream_split`, `original`,
`simple`, and `reference_index`. `upstream_split` preserves upstream metadata;
it does not determine the FEATS training/evaluation split.

## Implementation

Each raw source has its own converter, while shared paths, validation, and
writing utilities remain centralized:

```text
src/
├── common.py                    Shared paths and atomic writers
├── convert_multisim.py          MultiSim CSV converter
├── convert_align_and_shine.py   Align-and-Shine CSV converter
├── convert_simplifyur.py        SimplifyUR grouped-text converter
├── convert_idem_saaq.py         Received iDEM/Saaq CSV converter
├── audit_corpora.py             Global schema, count, and ID audit
├── package_normalized.py        Deterministic ZIP and manifest builder
└── prepare_feats_corpora.py     Coordinator for all sources
```

Run one converter or the complete preparation:

```bash
python phase1_normalization/src/convert_multisim.py
python phase1_normalization/src/convert_align_and_shine.py
python phase1_normalization/src/convert_simplifyur.py
python phase1_normalization/src/convert_idem_saaq.py
python phase1_normalization/src/prepare_feats_corpora.py all
python phase1_normalization/src/audit_corpora.py
```

The iDEM/Saaq converter writes directly to canonical `data/`. The received
package also contains 370 RBTL rows; they remain in raw storage and are
intentionally outside this two-source conversion.

The global audit currently verifies 29 files, 1,454,003 unique pair IDs, no
duplicate IDs, valid JSON, the flat `<language>/<source>__<corpus>.jsonl`
layout, and required identity/text fields.

`src/package_normalized.py` places `NORMALIZED_MANIFEST.csv` at the ZIP root
alongside the `data/` directory.
