# FEATS Simplification Evaluator

Data preparation and cleaning pipeline for training a fine-tuned multilingual
model that evaluates text simplifications.

```text
feats-simplification-evaluator/
├── README.md                         Project overview
├── raw/                              Immutable upstream source snapshots
│   ├── multisim/                     MultiSim CSV files (pinned Git revision)
│   ├── align_and_shine/              Selected aligned Wikipedia–Vikidia pairs
│   ├── simplifyur/                   Urdu source corpus (pinned Git revision)
│   └── contributed/{ar,es}/          Pending contributed corpora
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
SimplifyUR. Arabic and the additional Spanish corpus remain pending.

Large data, generated run artifacts, and model caches are excluded from Git.
They can be distributed separately as versioned release assets after checking
each upstream corpus licence.
