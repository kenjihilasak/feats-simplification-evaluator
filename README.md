# FEATS Simplification Evaluator

Data preparation and cleaning pipeline for training a fine-tuned multilingual
model that evaluates text simplifications.

## Data download

The current prerelease contains both the normalized Phase 1 corpus and the
first experimental Phase 2 cleaning run:

- [Release notes and all assets (v0.1.0-rc1)](https://github.com/kenjihilasak/feats-simplification-evaluator/releases/tag/v0.1.0-rc1)
- [Download Phase 1 normalized data (ZIP)](https://github.com/kenjihilasak/feats-simplification-evaluator/releases/download/v0.1.0-rc1/feats-phase1-normalized-v0.1.0-rc1.zip)
- [Download Phase 2 cleaned data (ZIP)](https://github.com/kenjihilasak/feats-simplification-evaluator/releases/download/v0.1.0-rc1/feats-phase2-cleaned-v0.1.0-rc1.zip)
- [Download Phase 1 manifest](https://github.com/kenjihilasak/feats-simplification-evaluator/releases/download/v0.1.0-rc1/NORMALIZED_MANIFEST.csv)
- [Download Phase 2 manifest](https://github.com/kenjihilasak/feats-simplification-evaluator/releases/download/v0.1.0-rc1/CLEANED_MANIFEST.csv)

Phase 1 contains 1,452,597 pairs from MultiSim, Align-and-Shine, and
SimplifyUR. Phase 2 retains 858,388 pairs and removes 594,209 (40.91%) with
the configured complexity-inversion and LaBSE filters. Because this is much
higher than the initial expectation, Phase 2 is an experimental cleaning
candidate rather than a final recommended training selection. Neither package
includes iDEM or Saaq al-Bambuu yet.

```text
feats-simplification-evaluator/
├── README.md                         Project overview
├── raw/                              Immutable upstream source snapshots
│   ├── multisim/                     MultiSim CSV files (pinned Git revision)
│   ├── align_and_shine/              Selected aligned Wikipedia–Vikidia pairs
│   ├── simplifyur/                   Urdu source corpus (pinned Git revision)
│   └── idem_&_saaq_al_bambuu/        Received paired dataset and split CSVs
├── phase1_normalization/
│   ├── README.md                     Canonical JSONL schema and commands
│   ├── src/                          Conversion and audit code
│   └── data/<language>/*.jsonl       One flat file per source corpus
├── phase2_cleaning/
│   ├── README.md                     Filter definitions and usage
│   ├── src/                          Independent SMP, LaBSE, and report code
│   ├── configs/                      Pinned pilot and full configurations
│   ├── jobs/                         Slurm submission scripts
│   ├── tests/                        Lightweight tests
│   ├── logs/                         Slurm logs
│   └── runs/<run_id>/                Scores, decisions, cleaned data, reports
├── metadata/
│   ├── inventories/                  Raw-source inventories
│   └── conversion_reports/           Phase 1 validation reports
└── cache/huggingface/                Downloaded model cache
```

Phase 1 currently contains 25 JSONL files and 1,452,597 pairs across 11
languages: 1,337,793 from MultiSim, 114,068 from Align-and-Shine, and 736 from
SimplifyUR. The received raw package contains another 1,406 selected pairs:
1,058 from iDEM and 348 from Saaq al-Bambuu; their normalization remains
pending and they are not part of the current release.

Large data, generated run artifacts, and model caches are excluded from Git.
Versioned data packages are distributed through GitHub Releases.

## Data sources and reuse

| Source | Upstream | Reuse information |
|---|---|---|
| MultiSim | [Repository and data card](https://github.com/XenonMolecule/MultiSim) | MIT; cite MultiSim and the individual corpora used. |
| Align-and-Shine | [Repository](https://github.com/kenjihilasak/Align-and-Shine) | Aligned corpus released under CC BY-SA 4.0; Wikipedia/Vikidia attribution and share-alike terms also apply. |
| SimplifyUR | [Repository](https://github.com/harisbinzia/SimplifyUR) | The README states CC BY 4.0, while `Data/LICENSE` also states NonCommercial and ShareAlike; follow the more restrictive notice until clarified. |

FEATS changes representation and applies automatic filters; ownership and the
original terms of the upstream sentences remain unchanged.
