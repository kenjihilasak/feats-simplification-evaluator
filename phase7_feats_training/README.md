# Phase 7 — FEATS axis models

FEATS axis scorers, trained on the Phase 6 synthetic corpora and evaluated on held-out human judgments (S1, SimpEval, iDEM).

- **Current design (`pipeline_v1`)**: several backbones (E5, Octen-8B, ezjev-4b-s3, Gemma-3-12B, Llama-8B), full fine-tuning for E5 and QLoRA for >= 4B, regression head with the axis in the prompt (A) or one head per axis (B). Input data: `phase6_degraded_corpus/runs/training_corpus_v1/`.
- **Earlier experiments (below)**: one model per axis (DeBERTa / XLM-R).

Layout: `src/` code, `configs/{models,axes,experiments}/`, `jobs/` SLURM scripts, `docs/plans/` and `docs/reports/` per experiment, `runs/<experiment>/` outputs (gitignored). Design: [`internal_docs/FINETUNING_PIPELINE.md`](../internal_docs/FINETUNING_PIPELINE.md).

- [Phase 7a — axis-model validation](docs/plans/axis_models_validation_v1_plan.md) ([result](docs/reports/axis_validation_v1.md): MEANING Q1 fails)
- [MEANING recipe v2 — graded meaning loss](docs/plans/meaning_recipe_v2_plan.md) ([result](docs/reports/meaning_v2.md): beats NLI on Simplicity-DA, system r 0.97; Q1 inconclusive on Human-Likert)
- FLUENCY v2 (graded) — [result](docs/reports/fluency_v2.md): does not beat CoLA (0.71 vs 0.76); graded = binary
- Current report: [axis_validation_v1](docs/reports/axis_validation_v1.md)

## Reproduce the pre-training gate

```bash
python -m unittest discover -s phase7_feats_training/tests -v
python phase7_feats_training/src/build_axis_dataset.py \
  --config phase7_feats_training/configs/experiments/axis_validation_v1.json \
  --output-root phase7_feats_training/runs/axis_validation_v1/data
```

The builder validates the data contract, aggregates the frozen human sets, joins reviews to their keys, writes SHA-256 provenance, and refuses to materialize training data if an evaluation original is an exact or Jaccard ≥ 0.8 match. Run artifacts are Git-ignored.

`axis_validation_v1` is stopped at that gate because five Phase 6 training originals overlap human-audited heldout originals. See the report before attempting training.
