# FEATS Simplification Evaluator

Data preparation and cleaning pipeline for training a fine-tuned multilingual
model that evaluates text simplifications.

## Data status

Current local status:

- Phase 1: 29 JSONL files, 1,454,003 pairs, 12 languages.
- Phase 2: 859,550 retained pairs; 594,453 removed (40.88%).
- Phase 3: model-agnostic strategy detection and completed Qwen stratified pilot.

The current private prerelease is `v0.1.0-rc2`. Its two access-controlled
assets contain all 29 corpus files: 1,454,003 normalized pairs and 859,550
cleaned pairs across 12 languages.

- [Release notes and all assets](https://github.com/kenjihilasak/feats-simplification-evaluator/releases/tag/v0.1.0-rc2)
- [Phase 1 normalized data (ZIP)](https://github.com/kenjihilasak/feats-simplification-evaluator/releases/download/v0.1.0-rc2/feats-phase1-normalized-v0.1.0-rc2.zip)
- [Phase 2 cleaned data (ZIP)](https://github.com/kenjihilasak/feats-simplification-evaluator/releases/download/v0.1.0-rc2/feats-phase2-cleaned-v0.1.0-rc2.zip)

Each ZIP embeds its corresponding manifest at the archive root.

iDEM and Saaq al-Bambuu are included because this repository and its Releases
are private and access-controlled. Their upstream copyright and reuse
restrictions still apply; do not redistribute the assets outside the project.

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
├── phase3_strategy_detection/
│   ├── README.md                     Model interface and output contract
│   ├── src/                          Shared runner, backends, and validation
│   ├── configs/                      Pinned model/run configurations
│   ├── jobs/                         Environment and Slurm scripts
│   ├── tests/                        Model-independent contract tests
│   └── runs/<run_id>/                Predictions, provenance, and reports
├── metadata/
│   ├── inventories/                  Source and conversion inventories
│   └── conversion_reports/           Phase 1 validation reports
└── cache/huggingface/                Local model cache
```

Raw data, normalized JSONL, model caches, scores, decisions, cleaned JSONL, and
Slurm logs are excluded from Git. Versioned data packages are attached to
GitHub Releases as ZIP files. Each newly built phase ZIP embeds its manifest at
the archive root so its contents remain auditable after download.

## Canonical Phase 1 corpus

| Source | Languages | Pairs | Included in private rc2 |
|---|---|---:|---|
| MultiSim | de, en, fr, it, ja, pt-BR, ru, sl | 1,337,793 | Yes |
| Align-and-Shine | ca, en, es, fr, it | 114,068 | Yes |
| SimplifyUR | ur | 736 | Yes |
| iDEM | ca, es, it | 1,058 | Yes |
| Saaq al-Bambuu | ar | 348 | Yes |
| **Total** | **12 languages** | **1,454,003** | **1,454,003 pairs** |

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

## Phase 3 strategy detection

Phase 3 adds multilabel strategy probabilities to the retained pairs without
changing or filtering Phase 2 data. The common runner supports interchangeable
model backends and writes sidecar JSONL predictions keyed by pair ID. The first
backend reproduces the released Qwen2.5-7B pairwise QLoRA classifier.

The smoke test and a stratified pilot of 855 pairs from all 29 files and 12
languages completed and passed validation. The report includes strategy
profiles, human-label agreement, examples, diagnostics, and a cost projection.
See `phase3_strategy_detection/README.md` for commands and results.

## Data sources and reuse

| Source | Upstream reference | Reuse information |
|---|---|---|
| MultiSim | [Repository and data card](https://github.com/XenonMolecule/MultiSim) | MIT repository licence; also cite and follow the terms of each constituent corpus. |
| Align-and-Shine | [Repository](https://github.com/kenjihilasak/Align-and-Shine) | Aligned corpus released under CC BY-SA 4.0; Wikipedia/Vikidia attribution and share-alike terms also apply. |
| SimplifyUR | [Repository](https://github.com/harisbinzia/SimplifyUR) | The README states CC BY 4.0, while `Data/LICENSE` states NonCommercial and ShareAlike; follow the more restrictive notice until clarified. |
| iDEM | [Corpus paper](https://arxiv.org/abs/2603.05345) | The received research snapshot contains no licence. It is included only in the private collaborator Release; do not redistribute it outside the project without written permission. |
| Saaq al-Bambuu | [Corpus paper](https://arxiv.org/abs/2204.09292) | The aligned novel corpus has copyright restrictions. It is included only in the access-controlled private Release and must not be redistributed publicly. |

FEATS changes representation and applies automatic filters; ownership and the
original terms of the upstream sentences remain unchanged.
