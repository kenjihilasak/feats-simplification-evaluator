# Phase 6 — Controlled degraded corpus

Phase 6 creates immutable synthetic sidecars from simplified versions. Each record targets one FEATS axis and one controlled distortion. It never modifies Phase 2b.

## Current scope

The seven-axis weak-supervision expansion is implemented for `MEANING`,
`FLUENCY`, `OMIT`, `SYN`, `MOD`, `ILLOC`, and `EXPL`. See
[`docs/MULTI_AXIS_CORPUS.md`](docs/MULTI_AXIS_CORPUS.md) for the full pipeline.

The original Meaning pilot below remains frozen and reproducible. The single
combined report, [`docs/PILOT_REPORT.md`](docs/PILOT_REPORT.md), covers all 350
pilot cases: the 50 audited Meaning cases and the 300 automatically triaged
cases from the other six axes.

The first pilot covers English meaning preservation. Selection is deterministic and precedes generation:

- reserve evaluation corpora and originals;
- include eligible Phase 4a `submitted + correct` anchors;
- fill the pilot with candidates from Wikipedia–Vikidia and WikiAutoEN;
- require exactly one Gemma-predicted strategy per pair;
- stratify by length, source, and that single strategy;
- sample 50 primary records plus 150 deterministic backups;
- manually approve the simplified primary inputs before generating distortions.

ASSET is excluded by default because it is a candidate evaluation corpus. The current selection combines six non-ASSET Phase 4a reviewed anchors from official Phase 2b with 44 candidates from the validated `2026-09-02_target_simple_v1` consolidation. All backups also come from that target-simple variant.

## Select the pilot candidates

```bash
python -m phase6_degraded_corpus.src.selection.select_pilot_inputs \
  --config phase6_degraded_corpus/configs/experiments/meaning_en_pilot_v1.json
```

Outputs are written below `phase6_degraded_corpus/runs/meaning_en_pilot_v1/selection/` and are ignored by Git.

The selector does not declare candidates correct. The pilot review accepted 27 primary records, rejected 23, and filled those positions with accepted backups. Only the resulting `accepted_50.jsonl` enters generation.

## Plan the corruptions

```bash
python -m phase6_degraded_corpus.src.planning.plan_meaning_corruptions \
  --config phase6_degraded_corpus/configs/experiments/meaning_corruption_assignment_v1.json
```

This detects applicable corruption types and assigns one type and target cue to each pair reproducibly. Assignment can run before review, but generation remains `blocked_clean_review` until the corresponding simplified version is accepted. The completed pilot contains 50 reviewed simplified versions and 50 audited meaning degradations.

## Tests

```bash
python -m unittest discover -s phase6_degraded_corpus/tests -v
```

## Data policy

Split and exclude by `canonical_original_id`. Keep every generated variant of one original in one split. Store exact prompts, model revision, decoding configuration, seed, hashes, validation, and reviewer provenance.

See [`docs/DEGRADATION_AUTOMATION.md`](docs/DEGRADATION_AUTOMATION.md) for the methodology and [`docs/PILOT_REPORT.md`](docs/PILOT_REPORT.md) for the combined pilot results and examples.
