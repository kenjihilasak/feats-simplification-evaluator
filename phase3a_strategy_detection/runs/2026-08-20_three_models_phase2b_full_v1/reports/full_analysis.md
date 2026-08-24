# Phase 3a full-run analysis

Experiment: `2026-08-20_three_models_phase2b_full_v1`. Canonical pairs: 854,486.

All statistics are reported separately by model because their thresholds
differ. A canonical pair is counted once per language and once per distinct
Phase 2b source; a pair shared by two sources contributes once to each source.

## Mean strategies detected per pair, by language

| Language | Pairs | multilingual_e5_large_bce | qwen2p5_7b_pairwise_qlora | xlmr_large_focal |
|---|---:|---:|---:|---:|
| ar | 231 | 2.805 | 2.039 | 2.472 |
| ca | 727 | 1.725 | 2.216 | 2.187 |
| de | 529 | 3.429 | 2.853 | 2.325 |
| en | 348,520 | 2.655 | 1.573 | 1.771 |
| es | 6,489 | 3.337 | 2.629 | 2.439 |
| fr | 245,746 | 2.752 | 2.003 | 2.538 |
| it | 65,332 | 1.990 | 1.637 | 1.787 |
| ja | 35,081 | 2.116 | 1.177 | 0.554 |
| pt-BR | 1,113 | 2.530 | 2.066 | 3.740 |
| ru | 150,056 | 3.732 | 2.254 | 1.709 |
| sl | 407 | 3.292 | 2.737 | 2.713 |
| ur | 255 | 2.969 | 1.184 | 1.008 |

## Mean strategies detected per pair, by source within language

| Language | Source | Pairs | multilingual_e5_large_bce | qwen2p5_7b_pairwise_qlora | xlmr_large_focal |
|---|---|---:|---:|---:|---:|
| ar | Saaq al-Bambuu | 231 | 2.805 | 2.039 | 2.472 |
| ca | Align-and-Shine | 390 | 1.710 | 2.128 | 2.041 |
| ca | iDEM | 337 | 1.742 | 2.318 | 2.356 |
| de | MultiSim | 529 | 3.429 | 2.853 | 2.325 |
| en | Align-and-Shine | 2,432 | 2.756 | 1.673 | 1.913 |
| en | MultiSim | 346,194 | 2.654 | 1.573 | 1.770 |
| es | Align-and-Shine | 6,204 | 3.351 | 2.618 | 2.442 |
| es | iDEM | 285 | 3.042 | 2.863 | 2.386 |
| fr | Align-and-Shine | 93,489 | 2.873 | 2.027 | 2.504 |
| fr | MultiSim | 152,257 | 2.678 | 1.989 | 2.559 |
| it | Align-and-Shine | 8,602 | 3.508 | 2.626 | 4.012 |
| it | MultiSim | 56,421 | 1.745 | 1.474 | 1.434 |
| it | iDEM | 309 | 4.443 | 3.822 | 4.269 |
| ja | MultiSim | 35,081 | 2.116 | 1.177 | 0.554 |
| pt-BR | MultiSim | 1,113 | 2.530 | 2.066 | 3.740 |
| ru | MultiSim | 150,056 | 3.732 | 2.254 | 1.709 |
| sl | MultiSim | 407 | 3.292 | 2.737 | 2.713 |
| ur | SimplifyUR | 255 | 2.969 | 1.184 | 1.008 |

## Additional diagnostics

| Model | Mean strategies | Zero-strategy pairs | Multilabel pairs | Most frequent strategy |
|---|---:|---:|---:|---|
| `multilingual_e5_large_bce` | 2.804 | 0.80% | 84.26% | SYN (84.82%) |
| `qwen2p5_7b_pairwise_qlora` | 1.816 | 8.50% | 57.29% | COMP (46.34%) |
| `xlmr_large_focal` | 1.941 | 8.44% | 65.12% | EXPL (65.54%) |

### Pairwise model agreement

| Models | Exact strategy-set match | Mean Jaccard | Label agreement | Score MAE |
|---|---:|---:|---:|---:|
| `multilingual_e5_large_bce` / `qwen2p5_7b_pairwise_qlora` | 5.08% | 0.321 | 59.65% | 0.226 |
| `multilingual_e5_large_bce` / `xlmr_large_focal` | 8.96% | 0.364 | 60.56% | 0.204 |
| `qwen2p5_7b_pairwise_qlora` / `xlmr_large_focal` | 6.88% | 0.253 | 61.37% | 0.325 |

These are descriptive model-output statistics, not accuracy estimates:
the full corpus has no verified gold strategy labels. Detailed CSVs also
report the complete 0–6 cardinality distribution, per-strategy prevalence
and mean score, language/source/corpus breakdowns, and model agreement by
language and source.
