# FOSE v1 report

Experiment: `fose_en_v1` · status: **STOP — blinded human audit pending**

## Inputs and exclusions

- Phase 2b: repaired `target_simple` English corpus (`63569397…`).
- Phase 3a: validated `2026-09-30_single_strategy_gemma_anchored_strict_textrepair_v1` candidates (`b60b79ef…`) for OMIT/SYN/EXPL.
- Reserved and audited originals were excluded by text: strong key plus word Jaccard ≥ 0.8. The structural pass excluded 300 reserved matches, 338 exact audited-text matches, and 8 near audited-text matches.
- `repaired_duplicate_of` rows were skipped. `wordfreq==3.1.1` is pinned in `.venv-phase6-vllm`.

## Pools

The structural union contained 65,302 pairs. Clean acceptability/NLI scores were available for every row: 30,966 reused unchanged MMI scores and 34,336 newly computed scores with the pinned checker revisions. After the common quality gate and the FLUENCY cap:

| Axis | Total | WikiAutoEN | ASSET | Wikipedia–Vikidia | Also in MMI |
|---|---:|---:|---:|---:|---:|
| FLUENCY | 7,990 | 6,686 | 948 | 356 | 3,462 |
| OMIT | 809 | 789 | 19 | 1 | 795 |
| SYN | 434 | 413 | 18 | 3 | 422 |
| EXPL | 1,467 | 1,461 | 2 | 4 | 1,464 |

FLUENCY was capped at 7,990 pairs, the size of the largest of the other seven axes (ILLOC), using seeded source/error-type stratification. The machine-readable counts and hashes are in `runs/fose_en_v1/pool_report.json`.

## Sample rule yield

A seeded oversample of 407 pool rows was generated once, with no retry or LLM repair, and checked with the pinned NLI and acceptability stack.

| Axis | Checked | Passed | Yield |
|---|---:|---:|---:|
| FLUENCY | 180 | 69 | 38.3% |
| OMIT | 80 | 43 | 53.8% |
| SYN | 81 | 36 | 44.4% |
| EXPL | 66 | 57 | 86.4% |

The blinded review contains up to 20 passing outputs per axis × source, with fewer where the pool or automatic-check yield is smaller: 141 cases total. Review file: [`fose_v1_review.md`](fose_v1_review.md). The key is private under `runs/fose_en_v1/audit/review_key.json`.

## Human audit and corpus

Pending. Per the plan, work stops here until the blinded review is completed. Unsure will count as valid; each axis must reach macro valid ≥ 85% before full generation and materialization.
