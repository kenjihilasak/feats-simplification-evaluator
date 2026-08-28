# Phase 3a single-strategy gold candidates

Candidate set: 2026-08-26_single_strategy_majority_vote_v1. Source experiment: 2026-08-20_three_models_phase2b_full_v1.

Each strategy receives one binary vote from Qwen, E5, and XLM-R. A pair
is retained when exactly one strategy receives at least two votes.

## Overall

| Input pairs | Candidates | Candidate rate | No majority | Multiple majority labels |
|---:|---:|---:|---:|---:|
| 854,486 | 271,395 | 31.76% | 63,386 | 519,705 |

## Candidates by language

| Language | Input pairs | Candidates | Rate | 2 votes | 3 votes |
|---|---:|---:|---:|---:|---:|
| ar | 231 | 1 | 0.43% | 1 | 0 |
| ca | 727 | 244 | 33.56% | 83 | 161 |
| de | 529 | 94 | 17.77% | 61 | 33 |
| en | 348,520 | 128,114 | 36.76% | 102,216 | 25,898 |
| es | 6,489 | 267 | 4.11% | 142 | 125 |
| fr | 245,746 | 49,490 | 20.14% | 33,664 | 15,826 |
| it | 65,332 | 40,801 | 62.45% | 16,758 | 24,043 |
| ja | 35,081 | 26,569 | 75.74% | 18,718 | 7,851 |
| pt-BR | 1,113 | 176 | 15.81% | 101 | 75 |
| ru | 150,056 | 25,462 | 16.97% | 18,439 | 7,023 |
| sl | 407 | 32 | 7.86% | 14 | 18 |
| ur | 255 | 145 | 56.86% | 112 | 33 |

## Candidates by strategy

| Strategy | Candidates | Share | 2 votes | 3 votes |
|---|---:|---:|---:|---:|
| SYN (Synonymy) | 121,044 | 44.60% | 73,790 | 47,254 |
| MOD (Modulation) | 6,584 | 2.43% | 5,622 | 962 |
| COMP (Compression) | 10,988 | 4.05% | 10,807 | 181 |
| EXPL (Explanation) | 111,114 | 40.94% | 80,615 | 30,499 |
| SYNT (Syntactic Change) | 12,557 | 4.63% | 11,267 | 1,290 |
| OMIT (Omission) | 9,108 | 3.36% | 8,208 | 900 |

## Agreement tiers and review priority

- Unanimous exact-singleton: 10,305; all three models predict only the winning strategy.
- Majority exact-singleton: 71,547; at least two models predict only the winning strategy.
- Label-majority only: 189,543; the winning strategy receives at least two votes, but fewer than two models predict it as their complete singleton set.

The stricter exact-singleton majority subset contains 81,852 pairs (30.16% of this candidate pool). The label-majority-only tier is retained by the configured voting rule but should receive lower review priority.

These are model-consensus candidates, not verified gold labels. Human
annotation and adjudication are required before calling the dataset gold.
The pool is also unbalanced across languages and strategies; sampling or
stratification should be performed only when designing the reviewed test set.
