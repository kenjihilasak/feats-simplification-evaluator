# MMI v2 full-corpus report

[Phase 6 documentation](../../README.md) · [Full-corpus plan](../../plans/full_corpus_mmi_v2_plan.md) · [Hedged review](mmi_full_spot_check.md)

## Status

The provisional English corpus has been materialized. MEANING, MOD, `assertion_to_question`, and `assertion_to_directive` reuse the approval obtained on the MMI v2 heldout audit because the full run uses the same planner, generator, prompts, and checks.

Only `assertion_to_hedged` remains gated. All **2,671** automatically selected hedged pairs are currently withheld. The blinded review contains 40 hedged cases. If at least 85% are `Valid` or `Unsure`, the materializer will include the withheld pairs and regenerate this report; otherwise they remain excluded.

## Allocation and generation

| Stage | Pairs |
|---|---:|
| Allocated, after excluding audited originals | 23,929 |
| Ready after planning | 23,867 |
| Automatically selected after generation and checks | 18,538 |
| Hedged pairs withheld pending review | 2,671 |
| Pairs in provisional corpus | **15,867** |

The planner dropped 61 pairs with no applicable factual cue and one pair whose rule-based corruption was impossible. The automatic checks rejected 5,329 of the 23,867 generated pairs. These failures are not materialized.

## Automatic selection yield

These are automatic pipeline yields, not human validity estimates.

| Axis | Source | Selected / generated | Yield |
|---|---|---:|---:|
| MEANING | ASSET | 67 / 85 | 78.8% |
| MEANING | WikiAutoEN | 6,884 / 9,793 | 70.3% |
| MEANING | Wikipedia–Vikidia | 23 / 34 | 67.6% |
| MOD | ASSET | 71 / 84 | 84.5% |
| MOD | WikiAutoEN | 3,484 / 3,875 | 89.9% |
| MOD | Wikipedia–Vikidia | 16 / 21 | 76.2% |
| ILLOC | ASSET | 74 / 88 | 84.1% |
| ILLOC | WikiAutoEN | 7,889 / 9,850 | 80.1% |
| ILLOC | Wikipedia–Vikidia | 30 / 37 | 81.1% |

The most frequent automatic rejection signals were failure to contradict the Original for MEANING, acceptability or semantic-equivalence checks for MOD, and operation-specific edit or content-lemma checks for ILLOC. Exact combinations are stored in `runs/mmi_en_v2_full/corpus/corpus_report.json`.

## Provisional corpus

Each accepted pair creates exactly two rows for one axis: its Simplified text with score `1`, and its Degraded text with score `0`. No scores are inferred for other axes.

| Axis | Pairs | Rows |
|---|---:|---:|
| MEANING | 6,974 | 13,948 |
| MOD | 3,571 | 7,142 |
| ILLOC, question + directive only | 5,322 | 10,644 |
| **Total** | **15,867** | **31,734** |

| Split | Rows |
|---|---:|
| Train | 28,472 |
| Validation | 3,262 |

The split is a stable 90/10 hash split by `canonical_original_id`; the Simplified and Degraded rows of a pair always remain together. Rows retain `gemma_strategy_count`, `phase3a_predicted_codes`, and `strict_single_strategy_candidate` for later filtering.

## Outputs and next decision

- Corpus: `runs/mmi_en_v2_full/corpus/train.jsonl` and `validation.jsonl`.
- Withheld IDs: `runs/mmi_en_v2_full/corpus/withheld_hedged.jsonl`.
- Machine-readable counts, drop reasons, and SHA-256 values: `runs/mmi_en_v2_full/corpus/corpus_report.json`.
- Human task: [40-case hedged review](mmi_full_spot_check.md).

No hedged row is present in the provisional train or validation files. The corpus will be regenerated only after the review gate is scored.
