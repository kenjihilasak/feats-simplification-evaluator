# Phase 1: normalization

Phase 1 converts every supported raw format into one flat JSONL file per
language and source corpus. The canonical local output contains 29 files and
1,454,003 pairs across 12 languages, including the completed iDEM and Saaq
al-Bambuu conversions.

The latest private data package is the [v0.1.0-rc2 normalized ZIP](https://github.com/kenjihilasak/feats-simplification-evaluator/releases/download/v0.1.0-rc2/feats-phase1-normalized-v0.1.0-rc2.zip).
See the root README for the private-release access policy and source-specific
reuse restrictions.

## Canonical record

Each line is one original–simplification pair. Required fields are `id`,
`original_id`, `language`, `source`, `corpus`, `upstream_split`, `original`,
`simple`, and `reference_index`. `upstream_split` preserves upstream metadata;
it does not determine the FEATS training/evaluation split.

| Field | Description |
|---|---|
| `id` | Unique identifier for one original–simplification pair. |
| `original_id` | Identifier shared by all simplifications derived from the same original sentence. |
| `language` | Normalized language code, such as `en` or `pt-BR`. |
| `source` | Parent dataset collection or provider. |
| `corpus` | Specific corpus name within the parent source. |
| `upstream_split` | Original `train`, `validation`, or `test` split, or `null` when unavailable. |
| `original` | Original text, treated as the more complex side of the pair. |
| `simple` | Simplified text or reference corresponding to `original`. |
| `reference_index` | Zero-based position of the simplification among references for the same original. |

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
├── build_deduplication_registry.py  Cross-corpus exact-text identities
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

## Canonical identity and deduplication

Source-specific `id` and `original_id` values remain unchanged. The exact-text
registry adds cross-corpus identities using Unicode NFC, collapsed whitespace,
and trimming; it does not lowercase or remove punctuation:

- `canonical_original_id = original:<language>:<sha256>`
- `canonical_pair_id = pair:<language>:<sha256>`

```bash
/scratch/pjbd103/miniconda3/envs/uncertainty-benchmark/bin/python \
  phase1_normalization/src/build_deduplication_registry.py
```

Outputs are kept next to Phase 1 in `deduplication/`: the observation-level
`pair_identity.parquet`, human-readable `duplicate_groups.jsonl`, and compact
`deduplication_summary.{csv,md}` reports. Exact pair duplicates and originals
with several distinct simplifications are recorded separately rather than
silently deleting source observations.

`src/package_normalized.py` places `NORMALIZED_MANIFEST.csv` at the ZIP root
alongside the `data/` directory. Private collaborator releases include all
validated sources by default:

```bash
python phase1_normalization/src/package_normalized.py \
  --output-dir /path/to/release-assets \
  --version v0.1.0-rc2 \
  --archive-date 2026-08-18
```

`--exclude-source` remains available for intentionally restricted or tailored
exports, but it is not used for the current private release.
