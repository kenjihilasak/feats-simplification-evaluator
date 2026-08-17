# Cleaning summary

- Input pairs: **1,452,597**
- Retained: **858,388** (59.09%)
- Removed by the union of filters: **594,209** (40.91%)
- Confident complexity inversions: 14,039 (0.97%)
- LaBSE < 0.62: 218,463 (15.04%)
- LaBSE > 0.95: 367,264 (25.28%)

## Qualitative spot check

A small EN/ES audit found that English pairs just above 0.95 generally have
minimal changes, while pairs just below 0.62 mix useful rejections with valid
compressions. The lower boundary should therefore be calibrated per source.
All Spanish rejections came from complexity inversions; inspected cases include
clear classifier false positives such as the Ollanta Humala example.

See [the English and Spanish examples](qualitative_examples_en_es.md) for the
original and simplified texts, LaBSE scores, and corpus sources.

## By language and corpus

| Language | Source | Corpus | Input | Kept | Removed | Removed % | Complexity inversion % | LaBSE low % | LaBSE high % |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| ca | Align-and-Shine | Wikipedia-Vikidia | 420 | 390 | 30 | 7.14 | 1.67 | 5.71 | 0.00 |
| de | MultiSim | GEOLinoTest | 1,198 | 397 | 801 | 66.86 | 0.08 | 1.34 | 65.53 |
| de | MultiSim | TextComplexityDE | 250 | 213 | 37 | 14.80 | 0.80 | 2.80 | 11.20 |
| en | Align-and-Shine | Wikipedia-Vikidia | 4,059 | 2,433 | 1,626 | 40.06 | 1.31 | 38.70 | 0.76 |
| en | MultiSim | ASSET | 23,590 | 14,524 | 9,066 | 38.43 | 0.67 | 1.67 | 36.17 |
| en | MultiSim | WikiAutoEN | 586,150 | 332,311 | 253,839 | 43.31 | 0.67 | 12.67 | 30.15 |
| es | Align-and-Shine | Wikipedia-Vikidia | 6,347 | 6,204 | 143 | 2.25 | 2.25 | 0.00 | 0.00 |
| fr | Align-and-Shine | Wikipedia-Vikidia | 94,478 | 93,903 | 575 | 0.61 | 0.61 | 0.00 | 0.00 |
| fr | MultiSim | CLEAR | 4,596 | 3,333 | 1,263 | 27.48 | 1.07 | 0.37 | 26.37 |
| fr | MultiSim | WikiLargeFR | 297,753 | 149,757 | 147,996 | 49.70 | 1.49 | 29.78 | 19.30 |
| it | Align-and-Shine | Wikipedia-Vikidia | 8,764 | 8,616 | 148 | 1.69 | 1.69 | 0.00 | 0.00 |
| it | MultiSim | AdminIt | 736 | 135 | 601 | 81.66 | 0.00 | 0.82 | 80.84 |
| it | MultiSim | PaCCSS-IT | 63,006 | 55,751 | 7,255 | 11.51 | 0.66 | 5.08 | 5.90 |
| it | MultiSim | SimpitikiWiki | 575 | 26 | 549 | 95.48 | 0.70 | 0.17 | 94.96 |
| it | MultiSim | Teacher | 170 | 117 | 53 | 31.18 | 1.18 | 11.76 | 18.24 |
| it | MultiSim | Terence | 1,012 | 403 | 609 | 60.18 | 0.20 | 1.38 | 58.60 |
| ja | MultiSim | EasyJapanese | 50,000 | 13,779 | 36,221 | 72.44 | 0.04 | 1.08 | 71.33 |
| ja | MultiSim | EasyJapaneseExtended | 35,000 | 21,906 | 13,094 | 37.41 | 0.14 | 5.58 | 31.74 |
| pt-BR | MultiSim | PorSimples | 7,864 | 1,805 | 6,059 | 77.05 | 0.18 | 5.60 | 71.41 |
| ru | MultiSim | RSSE | 6,804 | 5,790 | 1,014 | 14.90 | 0.16 | 6.69 | 8.05 |
| ru | MultiSim | RuAdaptEncy | 9,729 | 1,767 | 7,962 | 81.84 | 0.15 | 2.21 | 79.49 |
| ru | MultiSim | RuAdaptFairytales | 310 | 171 | 139 | 44.84 | 0.00 | 36.45 | 8.39 |
| ru | MultiSim | RuWikiLarge | 248,111 | 143,993 | 104,118 | 41.96 | 1.62 | 18.56 | 22.48 |
| sl | MultiSim | TSSlovene | 939 | 409 | 530 | 56.44 | 0.53 | 53.78 | 2.45 |
| ur | SimplifyUR | SimplifyUR | 736 | 255 | 481 | 65.35 | 0.14 | 0.00 | 65.35 |
