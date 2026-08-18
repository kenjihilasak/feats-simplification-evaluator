# FEATS Simplification Evaluator

Data preparation and cleaning pipeline for training a fine-tuned multilingual
model that evaluates text simplifications.

## Data status

The canonical local corpus is fully processed:

- Phase 1: 29 JSONL files, 1,454,003 pairs, 12 languages.
- Phase 2: 859,550 retained pairs; 594,453 removed (40.88%).
- iDEM: 1,058 pairs normalized and cleaned in Catalan, Spanish, and Italian.
- Saaq al-Bambuu: 348 Arabic pairs normalized and cleaned.

The current public prerelease remains `v0.1.0-rc1`. It contains the 25 corpus
files whose processing preceded iDEM and Saaq al-Bambuu: 1,452,597 normalized
pairs and 858,388 cleaned pairs.

- [Release notes and all assets](https://github.com/kenjihilasak/feats-simplification-evaluator/releases/tag/v0.1.0-rc1)
- [Phase 1 normalized data (ZIP)](https://github.com/kenjihilasak/feats-simplification-evaluator/releases/download/v0.1.0-rc1/feats-phase1-normalized-v0.1.0-rc1.zip)
- [Normalized manifest](https://github.com/kenjihilasak/feats-simplification-evaluator/releases/download/v0.1.0-rc1/NORMALIZED_MANIFEST.csv)
- [Phase 2 cleaned data (ZIP)](https://github.com/kenjihilasak/feats-simplification-evaluator/releases/download/v0.1.0-rc1/feats-phase2-cleaned-v0.1.0-rc1.zip)
- [Cleaned manifest](https://github.com/kenjihilasak/feats-simplification-evaluator/releases/download/v0.1.0-rc1/CLEANED_MANIFEST.csv)

iDEM and Saaq are complete locally, but are not included in public Release
assets. The received iDEM package has no redistribution licence, while the
published description of Saaq states that the corpus is unavailable publicly
because of copyright restrictions. This is a distribution restriction, not
unfinished normalization or cleaning.

## Repository structure

```text
feats-simplification-evaluator/
├── README.md                         Project overview and data status
├── raw/                              Immutable upstream source snapshots
│   ├── multisim/                     MultiSim CSV files
│   ├── align_and_shine/              Selected Wikipedia–Vikidia alignments
│   ├── simplifyur/                   Urdu source corpus
│   └── idem_&_saaq_al_bambuu/        Received paired data and split CSVs
├── phase1_normalization/
│   ├── README.md                     Canonical JSONL schema and commands
│   ├── src/                          Source-specific converters and audit code
│   ├── tests/                        Phase 1 tests
│   └── data/<language>/*.jsonl       One flat file per source corpus
├── phase2_cleaning/
│   ├── README.md                     Filter definitions and commands
│   ├── src/                          Complexity, LaBSE, decisions, validation
│   ├── configs/                      Pinned experiment configurations
│   ├── jobs/                         Slurm submission scripts
│   ├── tests/                        Phase 2 tests
│   ├── logs/                         Local Slurm logs
│   └── runs/<run_id>/                Scores, decisions, data, and reports
├── metadata/
│   ├── inventories/                  Source and conversion inventories
│   └── conversion_reports/           Phase 1 validation reports
└── cache/huggingface/                Local model cache
```

Raw data, normalized JSONL, model caches, scores, decisions, cleaned JSONL, and
Slurm logs are excluded from Git. Versioned distributable data are attached to
GitHub Releases as ZIP files; manifests make every included file auditable.

## Canonical Phase 1 corpus

| Source | Languages | Local pairs | Included in public rc1 |
|---|---|---:|---|
| MultiSim | de, en, fr, it, ja, pt-BR, ru, sl | 1,337,793 | Yes |
| Align-and-Shine | ca, en, es, fr, it | 114,068 | Yes |
| SimplifyUR | ur | 736 | Yes |
| iDEM | ca, es, it | 1,058 | No |
| Saaq al-Bambuu | ar | 348 | No |
| **Total** | **12 languages** | **1,454,003** | **1,452,597 pairs** |

Each JSONL line represents one original–simplification pair and preserves its
source, corpus, language, upstream split, original text, simplified text, and
source-specific metadata. Upstream splits are provenance fields; they do not
define the eventual FEATS training/evaluation split.

## Phase 2 cleaning

A pair is rejected if the complexity classifier confidently predicts an
original-to-simplification inversion with SMP below `0.1`, or if LaBSE cosine
similarity is below `0.62` or above `0.95`. The full local run retained 59.12%
of the corpus. Because the 40.88% removal rate is much higher than the initial
expectation, this remains an experimental cleaning candidate rather than a
final training selection. Quantitative and qualitative reports are under
`phase2_cleaning/runs/2026-08-05_complexity_smp01_labse062_095_full_flat_v2/reports/`.

## Data sources and reuse

| Source | Upstream reference | Reuse information |
|---|---|---|
| MultiSim | [Repository and data card](https://github.com/XenonMolecule/MultiSim) | MIT repository licence; also cite and follow the terms of each constituent corpus. |
| Align-and-Shine | [Repository](https://github.com/kenjihilasak/Align-and-Shine) | Aligned corpus released under CC BY-SA 4.0; Wikipedia/Vikidia attribution and share-alike terms also apply. |
| SimplifyUR | [Repository](https://github.com/harisbinzia/SimplifyUR) | The README states CC BY 4.0, while `Data/LICENSE` states NonCommercial and ShareAlike; follow the more restrictive notice until clarified. |
| iDEM | [Corpus paper](https://arxiv.org/abs/2603.05345) | The received research snapshot contains no licence. Do not redistribute it from this repository without written confirmation from the corpus owners. |
| Saaq al-Bambuu | [Corpus paper](https://arxiv.org/abs/2204.09292) | The aligned novel corpus is described as non-public because of copyright restrictions; it is excluded from Release assets. |

FEATS changes representation and applies automatic filters; ownership and the
original terms of the upstream sentences remain unchanged.
