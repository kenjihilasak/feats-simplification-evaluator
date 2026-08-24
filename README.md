# FEATS Simplification Evaluator

Data preparation and cleaning pipeline for training a fine-tuned multilingual
model that evaluates text simplifications.

## Current complete release

The private prerelease
[`v0.2.0-rc2`](https://github.com/kenjihilasak/feats-simplification-evaluator/releases/tag/v0.2.0-rc2)
contains the complete outputs of the FEATS data pipeline across 12 languages.
Each phase is distributed as an independent ZIP with an embedded audit
manifest.

| Phase | Product | Records | Download |
|---|---|---:|---|
| [Phase 1](phase1_normalization/README.md) | Normalized source observations | 1,454,003 | [ZIP](https://github.com/kenjihilasak/feats-simplification-evaluator/releases/download/v0.2.0-rc2/feats-phase1-normalized-v0.2.0-rc2.zip) |
| [Phase 2a](phase2a_cleaning/README.md) | Experimentally cleaned observations | 859,550 | [ZIP](https://github.com/kenjihilasak/feats-simplification-evaluator/releases/download/v0.2.0-rc2/feats-phase2a-cleaned-v0.2.0-rc2.zip) |
| [Phase 2b](phase2b_consolidation/README.md) | Consolidated canonical pairs | 854,486 | [ZIP](https://github.com/kenjihilasak/feats-simplification-evaluator/releases/download/v0.2.0-rc2/feats-phase2b-consolidated-v0.2.0-rc2.zip) |
| [Phase 3a](phase3a_strategy_detection/README.md) | Strategy predictions and full analysis | 2,563,458 | [ZIP](https://github.com/kenjihilasak/feats-simplification-evaluator/releases/download/v0.2.0-rc2/feats-phase3a-strategy-detection-v0.2.0-rc2.zip) |
| [Phase 3b](phase3b_word_alignment/README.md) | Word-alignment v2 sidecars | 854,486 | [ZIP](https://github.com/kenjihilasak/feats-simplification-evaluator/releases/download/v0.2.0-rc2/feats-phase3b-word-alignment-v0.2.0-rc2.zip) |

Repository access is required. Upstream reuse restrictions still apply,
particularly to iDEM and Saaq al-Bambuu. Previous releases remain available in
the [release history](https://github.com/kenjihilasak/feats-simplification-evaluator/releases).

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
│   ├── data/<language>/*.jsonl       One flat file per source corpus
│   └── deduplication/                Canonical identity registry and reports
├── phase2a_cleaning/
│   ├── README.md                     Filter definitions and commands
│   ├── src/                          Complexity, LaBSE, decisions, validation
│   ├── configs/                      Pinned experiment configurations
│   ├── jobs/                         Slurm submission scripts
│   ├── tests/                        Phase 2a tests
│   ├── logs/                         Local Slurm logs
│   └── runs/<run_id>/                Scores, decisions, data, and reports
├── phase2b_consolidation/
│   ├── src/                          Exact-pair consolidation
│   ├── tests/                        Consolidation tests
│   ├── data/<language>/              One consolidated JSONL per language
│   ├── groups/                       Cross-corpus multi-simplification registry
│   └── reports/                      Pair counts and retention diagnostics
├── phase3a_strategy_detection/
│   ├── README.md                     Model interface and output contract
│   ├── src/                          Batched backends, runner, and validation
│   ├── configs/                      Separate model and experiment configs
│   ├── jobs/                         Environment and Slurm scripts
│   ├── tests/                        Model-independent contract tests
│   └── runs/<experiment_id>/         Per-model predictions and reports
├── phase3b_word_alignment/
│   ├── README.md                     Tokenization and sidecar contract
│   ├── src/                          SimAlign runner and lossless validation
│   ├── configs/                      Pinned smoke/full v2 configurations
│   ├── jobs/                         Environment and Slurm array scripts
│   └── tests/                        Model-independent contract tests
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

## Phase 2a cleaning

A pair is rejected if the complexity classifier confidently predicts an
original-to-simplification inversion with SMP below `0.1`, or if LaBSE cosine
similarity is below `0.62` or above `0.95`. The full local run retained 59.12%
of the corpus. Because the 40.88% removal rate is much higher than the initial
expectation, this remains an experimental cleaning candidate rather than a
final training selection. Quantitative and qualitative reports are under
`phase2a_cleaning/runs/2026-08-05_complexity_smp01_labse062_095_full_flat_v2/reports/`.

## Phase 2b consolidation

Phase 2b maps the 859,550 cleaned observations to 854,486 exact canonical
pairs. It consolidates 5,064 redundant observations while preserving every
surviving source occurrence in `provenance`. Different simplifications of the
same original remain separate and share `canonical_original_id`.

The validated output contains one JSONL per language. The release ZIP embeds
`CONSOLIDATED_MANIFEST.csv` with counts, sizes, and SHA-256 hashes.

The derived
[`groups/cross_corpus_multi_simplifications.jsonl`](phase2b_consolidation/groups/cross_corpus_multi_simplifications.jsonl)
registry contains 3,086 post-cleaning canonical originals and their 7,215
distinct simplifications when at least two simplifications and two distinct
`(source, corpus)` combinations survive Phase 2a.

## Phase 3a strategy detection

Phase 3a reads the 854,486 canonical Phase 2b pairs and writes sidecar
predictions keyed by `canonical_pair_id`. It supports the released XLM-R Large
focal, multilingual-E5 Large BCE, and Qwen2.5-7B pairwise QLoRA classifiers
through one output contract. The completed full run contains 854,486 validated
predictions from each model (2,563,458 records in total).

The new deterministic pilot contains 859 unique canonical pairs covering all
29 `(language, source, corpus)` strata and 12 languages. The earlier 855-pair
Qwen pilot remains as historical validation of the original Phase 2a pipeline.
See `phase3a_strategy_detection/README.md` for the current layout and commands.

## Phase 3b word alignment

Phase 3b independently derives word-alignment sidecars from the same 854,486
canonical Phase 2b pairs used by Phase 3a. The validated v2 run combines
SimAlign with CAMeL ATB surface-preserving Arabic tokenization, Sudachi A for
Japanese, Stanza UDTB for Urdu, Stanza SSJ for Slovenian, and language-specific
spaCy tokenizers for the remaining languages. The sidecars preserve exact
character offsets and orthographic-parent mappings so they can feed FEATS
feature construction or edit-operation models. See
`phase3b_word_alignment/README.md` for the output contract and run results.

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
