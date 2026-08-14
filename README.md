# FEATS Simplification Evaluator

Data preparation and cleaning pipeline for training a fine-tuned multilingual
model that evaluates text simplifications.

## Data download

The current preview contains the normalized Phase 1 corpus before cleaning:

- [Release notes and all assets (v0.1.0-rc1)](https://github.com/kenjihilasak/feats-simplification-evaluator/releases/tag/v0.1.0-rc1)
- [Download Phase 1 normalized data](https://github.com/kenjihilasak/feats-simplification-evaluator/releases/download/v0.1.0-rc1/feats-phase1-normalized-v0.1.0-rc1.tar.zst)
- [Download file manifest](https://github.com/kenjihilasak/feats-simplification-evaluator/releases/download/v0.1.0-rc1/MANIFEST.csv)

This preview contains 1,452,597 pairs from MultiSim, Align-and-Shine, and
SimplifyUR. It does not yet include iDEM, Saaq al-Bambuu, or Phase 2 cleaned
data.

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
│   ├── jobs/                         Slurm submission script
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
1,058 from iDEM and 348 from Saaq al-Bambuu. They will be normalized directly
into canonical `data/` after the running base cleaning job finishes.

Large data, generated run artifacts, and model caches are excluded from Git.
They can be distributed separately as versioned release assets after checking
each upstream corpus licence.
