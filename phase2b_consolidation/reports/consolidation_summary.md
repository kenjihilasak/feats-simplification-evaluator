# Phase 2b consolidation summary

Input: `/mnt/scratch/pjbd103/feats-simplification-evaluator/phase2a_cleaning/runs/2026-08-05_complexity_smp01_labse062_095_full_flat_v2/cleaned`.

| Language | Cleaned observations | Unique pairs | Exact duplicates removed | Partially retained pairs |
|---|---:|---:|---:|---:|
| **All** | **859,550** | **854,486** | **5,064** | **22** |
| ar | 231 | 231 | 0 | 0 |
| ca | 727 | 727 | 0 | 0 |
| de | 610 | 529 | 81 | 0 |
| en | 349,268 | 348,520 | 748 | 1 |
| es | 6,489 | 6,489 | 0 | 0 |
| fr | 246,993 | 245,746 | 1,247 | 7 |
| it | 65,357 | 65,332 | 25 | 0 |
| ja | 35,685 | 35,081 | 604 | 0 |
| pt-BR | 1,805 | 1,113 | 692 | 1 |
| ru | 151,721 | 150,056 | 1,665 | 13 |
| sl | 409 | 407 | 2 | 0 |
| ur | 255 | 255 | 0 | 0 |

Each output row is one canonical original–simplification pair. Different simplifications
of the same original remain separate and share `canonical_original_id`. A partially retained
pair survived Phase 2a in at least one, but not all, of its Phase 1 source occurrences.
