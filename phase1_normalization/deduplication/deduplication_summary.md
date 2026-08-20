# Phase 1 deduplication summary

Canonicalization: `feats-text-identity-v1` (Unicode NFC, collapsed whitespace, and trimming).
Case, punctuation, and lexical content are preserved.

| Measure | Count |
|---|---:|
| Source observations | 1,454,003 |
| Unique original texts | 1,270,239 |
| Unique original–simplification pairs | 1,440,168 |
| Redundant exact-pair observations | 13,835 (0.95%) |
| Exact duplicate pair groups | 11,530 |
| Originals with multiple simplifications | 73,853 |
| Exact pair groups spanning sources | 128 |
| Exact pair groups spanning corpora | 2,515 |

## By language

| Language | Observations | Unique pairs | Redundant observations | Redundant % | Multi-simplification originals |
|---|---:|---:|---:|---:|---:|
| ar | 348 | 348 | 0 | 0.00% | 1 |
| ca | 784 | 784 | 0 | 0.00% | 0 |
| de | 1,448 | 1,183 | 265 | 18.30% | 0 |
| en | 613,799 | 610,840 | 2,959 | 0.48% | 3,590 |
| es | 6,702 | 6,702 | 0 | 0.00% | 7 |
| fr | 396,827 | 395,045 | 1,782 | 0.45% | 30,520 |
| it | 74,602 | 74,572 | 30 | 0.04% | 10,026 |
| ja | 85,000 | 82,463 | 2,537 | 2.98% | 6,129 |
| pt-BR | 7,864 | 4,967 | 2,897 | 36.84% | 154 |
| ru | 264,954 | 261,591 | 3,363 | 1.27% | 23,240 |
| sl | 939 | 937 | 2 | 0.21% | 2 |
| ur | 736 | 736 | 0 | 0.00% | 184 |

`pair_identity.parquet` maps every Phase 1 observation to canonical IDs.
`duplicate_groups.jsonl` contains only originals occurring more than once and lists all source occurrences.
