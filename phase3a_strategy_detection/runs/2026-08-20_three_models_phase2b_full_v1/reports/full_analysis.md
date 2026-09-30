# Phase 3a full-run analysis

Experiment: `2026-08-20_three_models_phase2b_full_v1`. Canonical pairs: 854,486.

All statistics are reported separately by model because their thresholds
differ. A canonical pair is counted once per language and once per distinct
Phase 2b source; a pair shared by two sources contributes once to each source.

## Pairs with exactly one detected strategy, by language

| Language | Pairs | gemma3_12b_pairwise_qlora | multilingual_e5_large_bce | qwen2p5_7b_pairwise_qlora | xlmr_large_focal |
|---|---:|---:|---:|---:|---:|
| ar | 231 | 39 | 0 | 43 | 2 |
| ca | 727 | 229 | 368 | 161 | 94 |
| de | 529 | 110 | 37 | 68 | 124 |
| en | 348,520 | 145,147 | 63,888 | 138,322 | 96,095 |
| es | 6,489 | 1,605 | 161 | 1,059 | 245 |
| fr | 245,746 | 88,344 | 28,981 | 71,074 | 28,761 |
| it | 65,332 | 35,995 | 26,586 | 26,335 | 37,951 |
| ja | 35,081 | 26,816 | 6,979 | 22,795 | 11,797 |
| pt-BR | 1,113 | 461 | 143 | 364 | 93 |
| ru | 150,056 | 44,593 | 480 | 31,859 | 50,663 |
| sl | 407 | 48 | 20 | 58 | 29 |
| ur | 255 | 247 | 7 | 196 | 59 |
| **Total** | **854,486** | **343,634** | **127,650** | **292,334** | **225,913** |

## Mean strategies detected per pair, by language

| Language | Pairs | gemma3_12b_pairwise_qlora | multilingual_e5_large_bce | qwen2p5_7b_pairwise_qlora | xlmr_large_focal |
|---|---:|---:|---:|---:|---:|
| ar | 231 | 2.087 | 2.805 | 2.039 | 2.472 |
| ca | 727 | 1.957 | 1.725 | 2.216 | 2.187 |
| de | 529 | 2.469 | 3.429 | 2.853 | 2.325 |
| en | 348,520 | 1.493 | 2.655 | 1.573 | 1.771 |
| es | 6,489 | 2.137 | 3.337 | 2.629 | 2.439 |
| fr | 245,746 | 1.727 | 2.752 | 2.003 | 2.538 |
| it | 65,332 | 1.419 | 1.990 | 1.637 | 1.787 |
| ja | 35,081 | 1.146 | 2.116 | 1.177 | 0.554 |
| pt-BR | 1,113 | 1.801 | 2.530 | 2.066 | 3.740 |
| ru | 150,056 | 1.869 | 3.732 | 2.254 | 1.709 |
| sl | 407 | 2.366 | 3.292 | 2.737 | 2.713 |
| ur | 255 | 1.031 | 2.969 | 1.184 | 1.008 |

## Mean strategies detected per pair, by source within language

| Language | Source | Pairs | gemma3_12b_pairwise_qlora | multilingual_e5_large_bce | qwen2p5_7b_pairwise_qlora | xlmr_large_focal |
|---|---|---:|---:|---:|---:|---:|
| ar | Saaq al-Bambuu | 231 | 2.087 | 2.805 | 2.039 | 2.472 |
| ca | Align-and-Shine | 390 | 1.938 | 1.710 | 2.128 | 2.041 |
| ca | iDEM | 337 | 1.979 | 1.742 | 2.318 | 2.356 |
| de | MultiSim | 529 | 2.469 | 3.429 | 2.853 | 2.325 |
| en | Align-and-Shine | 2,432 | 1.542 | 2.756 | 1.673 | 1.913 |
| en | MultiSim | 346,194 | 1.493 | 2.654 | 1.573 | 1.770 |
| es | Align-and-Shine | 6,204 | 2.117 | 3.351 | 2.618 | 2.442 |
| es | iDEM | 285 | 2.575 | 3.042 | 2.863 | 2.386 |
| fr | Align-and-Shine | 93,489 | 1.703 | 2.873 | 2.027 | 2.504 |
| fr | MultiSim | 152,257 | 1.742 | 2.678 | 1.989 | 2.559 |
| it | Align-and-Shine | 8,602 | 2.447 | 3.508 | 2.626 | 4.012 |
| it | MultiSim | 56,421 | 1.249 | 1.745 | 1.474 | 1.434 |
| it | iDEM | 309 | 3.871 | 4.443 | 3.822 | 4.269 |
| ja | MultiSim | 35,081 | 1.146 | 2.116 | 1.177 | 0.554 |
| pt-BR | MultiSim | 1,113 | 1.801 | 2.530 | 2.066 | 3.740 |
| ru | MultiSim | 150,056 | 1.869 | 3.732 | 2.254 | 1.709 |
| sl | MultiSim | 407 | 2.366 | 3.292 | 2.737 | 2.713 |
| ur | SimplifyUR | 255 | 1.031 | 2.969 | 1.184 | 1.008 |

## Additional diagnostics

| Model | Mean strategies | Zero-strategy pairs | Multilabel pairs | Most frequent strategy |
|---|---:|---:|---:|---|
| `gemma3_12b_pairwise_qlora` | 1.613 | 9.76% | 50.02% | SYN (44.87%) |
| `multilingual_e5_large_bce` | 2.804 | 0.80% | 84.26% | SYN (84.82%) |
| `qwen2p5_7b_pairwise_qlora` | 1.816 | 8.50% | 57.29% | COMP (46.34%) |
| `xlmr_large_focal` | 1.941 | 8.44% | 65.12% | EXPL (65.54%) |

### Gemma relative to the other models

| Other model | Exact strategy-set match | Mean Jaccard | Label agreement | Mean strategy-count difference |
|---|---:|---:|---:|---:|
| `multilingual_e5_large_bce` | 6.87% | 0.330 | 61.47% | 1.395 |
| `qwen2p5_7b_pairwise_qlora` | 30.14% | 0.536 | 80.23% | 0.742 |
| `xlmr_large_focal` | 7.26% | 0.208 | 58.22% | 0.950 |

Gemma detects a mean of 1.613 strategies per pair; 40.22% of pairs receive exactly one strategy and 9.76% receive none. Its closest output profile is `qwen2p5_7b_pairwise_qlora` (mean Jaccard 0.536). Agreement measures output compatibility, not accuracy, because these corpus-wide predictions do not have verified gold strategy labels.

### Pairwise model agreement

| Models | Exact strategy-set match | Mean Jaccard | Label agreement | Score MAE |
|---|---:|---:|---:|---:|
| `gemma3_12b_pairwise_qlora` / `multilingual_e5_large_bce` | 6.87% | 0.330 | 61.47% | 0.228 |
| `gemma3_12b_pairwise_qlora` / `qwen2p5_7b_pairwise_qlora` | 30.14% | 0.536 | 80.23% | 0.132 |
| `gemma3_12b_pairwise_qlora` / `xlmr_large_focal` | 7.26% | 0.208 | 58.22% | 0.344 |
| `multilingual_e5_large_bce` / `qwen2p5_7b_pairwise_qlora` | 5.08% | 0.321 | 59.65% | 0.226 |
| `multilingual_e5_large_bce` / `xlmr_large_focal` | 8.96% | 0.364 | 60.56% | 0.204 |
| `qwen2p5_7b_pairwise_qlora` / `xlmr_large_focal` | 6.88% | 0.253 | 61.37% | 0.325 |

These are descriptive model-output statistics, not accuracy estimates:
the full corpus has no verified gold strategy labels. Detailed CSVs also
report the complete 0–6 cardinality distribution, per-strategy prevalence
and mean score, language/source/corpus breakdowns, and model agreement by
language and source.

<!-- gemma-anchored-consensus:start -->
## Gemma-anchored single-strategy consensus

These are analysis counts only; no candidate dataset has been extracted.
Both variants require Gemma to predict exactly one strategy. The strict
variant requires another model to predict exactly the same singleton set;
the inclusive variant only requires another model to include Gemma's
strategy, even if that model predicts additional strategies.

### Overall

| Variant | All pairs | Gemma singleton | Retained | % all pairs | % Gemma singleton |
|---|---:|---:|---:|---:|---:|
| strict | 854,486 | 343,634 | 167,238 | 19.57% | 48.67% |
| inclusive | 854,486 | 343,634 | 310,000 | 36.28% | 90.21% |

### Retained pairs by language

| Language | Gemma singleton | Strict | Inclusive |
|---|---:|---:|---:|
| ar | 39 | 20 | 37 |
| ca | 229 | 149 | 204 |
| de | 110 | 48 | 101 |
| en | 145,147 | 66,768 | 125,027 |
| es | 1,605 | 375 | 1,438 |
| fr | 88,344 | 35,404 | 80,422 |
| it | 35,995 | 26,771 | 34,070 |
| ja | 26,816 | 20,181 | 25,563 |
| pt-BR | 461 | 250 | 445 |
| ru | 44,593 | 17,050 | 42,403 |
| sl | 48 | 18 | 43 |
| ur | 247 | 204 | 247 |

### Retained pairs by source within language

| Language | Source | Gemma singleton | Strict | Inclusive |
|---|---|---:|---:|---:|
| ar | Saaq al-Bambuu | 39 | 20 | 37 |
| ca | Align-and-Shine | 106 | 54 | 83 |
| ca | iDEM | 123 | 95 | 121 |
| de | MultiSim | 110 | 48 | 101 |
| en | Align-and-Shine | 993 | 444 | 835 |
| en | MultiSim | 144,196 | 66,341 | 124,226 |
| es | Align-and-Shine | 1,577 | 363 | 1,410 |
| es | iDEM | 28 | 12 | 28 |
| fr | Align-and-Shine | 35,193 | 13,875 | 32,144 |
| fr | MultiSim | 53,151 | 21,529 | 48,278 |
| it | Align-and-Shine | 1,966 | 804 | 1,775 |
| it | MultiSim | 34,001 | 25,945 | 32,267 |
| it | iDEM | 28 | 22 | 28 |
| ja | MultiSim | 26,816 | 20,181 | 25,563 |
| pt-BR | MultiSim | 461 | 250 | 445 |
| ru | MultiSim | 44,593 | 17,050 | 42,403 |
| sl | MultiSim | 48 | 18 | 43 |
| ur | SimplifyUR | 247 | 204 | 247 |

### Retained pairs by Gemma strategy

| Strategy | Gemma singleton | Strict | Inclusive |
|---|---:|---:|---:|
| SYN (Synonymy) | 159,800 | 90,249 | 153,183 |
| MOD (Modulation) | 9,352 | 2,225 | 6,968 |
| COMP (Compression) | 23,219 | 4,494 | 18,377 |
| EXPL (Explanation) | 80,002 | 47,322 | 76,256 |
| SYNT (Syntactic Change) | 7,872 | 2,779 | 7,102 |
| OMIT (Omission) | 63,389 | 20,169 | 48,114 |

### Confirming models

Counts are non-exclusive: a retained pair may be confirmed by multiple models.

| Variant | Confirming model | Confirmed pairs | % retained |
|---|---|---:|---:|
| strict | multilingual_e5_large_bce | 35,486 | 21.22% |
| strict | qwen2p5_7b_pairwise_qlora | 137,623 | 82.29% |
| strict | xlmr_large_focal | 46,059 | 27.54% |
| inclusive | multilingual_e5_large_bce | 229,688 | 74.09% |
| inclusive | qwen2p5_7b_pairwise_qlora | 255,996 | 82.58% |
| inclusive | xlmr_large_focal | 148,995 | 48.06% |

### Number of confirming models

| Variant | Confirmers | Retained pairs | % retained |
|---|---:|---:|---:|
| strict | 1 | 123,249 | 73.70% |
| strict | 2 | 36,048 | 21.55% |
| strict | 3 | 7,941 | 4.75% |
| inclusive | 1 | 86,609 | 27.94% |
| inclusive | 2 | 122,103 | 39.39% |
| inclusive | 3 | 101,288 | 32.67% |
<!-- gemma-anchored-consensus:end -->
