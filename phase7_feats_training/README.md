# Phase 7 — FEATS axis models

One model per FEATS axis, trained on the Phase 6 corpora and evaluated on held-out human judgments. Design: [`internal_docs/FEATS_AXIS_MODELS_PLAN.md`](../internal_docs/FEATS_AXIS_MODELS_PLAN.md).

- Current plan: [Phase 7a — axis-model validation](docs/plans/axis_models_validation_v1_plan.md)
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
