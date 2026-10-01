# FOSE v1 report

Experiment: `fose_en_v1` · status: **STOP — blinded human audit pending**

## Inputs and exclusions

- Phase 2b: repaired `target_simple` English corpus (`63569397…`).
- Phase 3a: validated `2026-09-30_single_strategy_gemma_anchored_strict_textrepair_v1` candidates (`b60b79ef…`) for OMIT/SYN/EXPL.
- Reserved and audited originals were excluded by text: strong key plus word Jaccard ≥ 0.8. The structural pass excluded 300 reserved matches, 338 exact audited-text matches, and 8 near audited-text matches.
- `repaired_duplicate_of` rows were skipped. `wordfreq==3.1.1` is pinned in `.venv-phase6-vllm`.
- Per the 2026-10-01 amendment, Wikipedia-Vikidia is excluded before the quality gate: 480 FLUENCY, 1 OMIT, 5 SYN, and 8 EXPL structural candidates were dropped.

## Pools

The pre-amendment structural union contained 65,302 pairs, with 30,966 reused MMI checker records and 34,336 previously computed records. All 65,302 existing clean scores were reused without rerunning NLI. After the source exclusion, common quality gate, and FLUENCY cap:

| Axis | Total | WikiAutoEN | ASSET | Also in MMI |
|---|---:|---:|---:|---:|
| FLUENCY | 7,990 | 7,042 | 948 | 3,549 |
| OMIT | 808 | 789 | 19 | 794 |
| SYN | 431 | 413 | 18 | 419 |
| EXPL | 1,463 | 1,461 | 2 | 1,460 |

FLUENCY was capped at 7,990 pairs, the size of the largest of the other seven axes (ILLOC), using seeded source/error-type stratification. The machine-readable counts and hashes are in `runs/fose_en_v1/pool_report.json`.

## Sample rule yield

A seeded oversample was generated once; the amended two-source subset contains 339 rows, with no retry or LLM repair, and checked with the pinned NLI and acceptability stack.

| Axis | Checked | Passed | Yield |
|---|---:|---:|---:|
| FLUENCY | 120 | 44 | 36.7% |
| OMIT | 79 | 43 | 54.4% |
| SYN | 78 | 34 | 43.6% |
| EXPL | 62 | 54 | 87.1% |

The blinded review contains up to 20 passing outputs per axis × source, with fewer where the pool or automatic-check yield is smaller: 116 cases total. Review file: [`fose_v1_review.md`](fose_v1_review.md). The key is private under `runs/fose_en_v1/audit/review_key.json`.

## Human audit and corpus

Pending. Per the plan, work stops here until the blinded review is completed. Unsure will count as valid; each axis must reach macro valid ≥ 85% before full generation and materialization.
