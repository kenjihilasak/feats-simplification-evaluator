# Phase 6 — Controlled degraded corpus

Phase 6 builds synthetic clean/degraded pairs for FEATS without modifying Phase 2b. Each generated row targets one FEATS axis and preserves full provenance.

## Current work

The active experiment is **MMI v2** (MEANING, MOD, ILLOC; English). Its model comparison and blinded held-out review are kept together under [docs/reports/current/](docs/reports/current/). The selected configuration will be used in a separate full-generation/materialization step.

- [MMI v2 model comparison](docs/reports/current/mmi_v2_model_comparison.md)
- [MMI v2 held-out review](docs/reports/current/mmi_v2_heldout_review.md)
- [MMI v2 inputs and exclusion policy](docs/inputs.md)
- [Current MMI configs](configs/experiments/)
- [Current MMI prompts](prompts/v2/)

## Archived experiments

The frozen Meaning pilot and the multi-axis v1 pilot are retained for provenance only. Their reports, prompts, jobs, configs, and run products live under archive directories. They are not the operational workflow.

- [Archived reports](docs/reports/archive/)
- [Archived v1 plan](docs/plans/archive/meaning_mod_illoc_v2_plan.md)
- `configs/archive/`, `prompts/archive/`, `jobs/archive/`, `runs/archive/`

## Repository layout

```text
docs/reports/current/  active decision evidence
docs/reports/archive/  historical pilots
configs/experiments/   active MMI configuration
prompts/v2/            active MMI prompts
runs/mmi_en_v2/        active experiment products
runs/archive/          historical run products
```

## Data policy

Split and exclude by `canonical_original_id`. Keep every generated variant of one original in one split. Store prompts, model revision, decoding configuration, seed, hashes, validation, and reviewer provenance.

## Tests

```bash
python -m unittest discover -s phase6_degraded_corpus/tests -v
```
