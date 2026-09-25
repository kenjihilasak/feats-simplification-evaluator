# Fluency degradation

[Methodology index](MULTI_AXIS_CORPUS.md) · [pilot report](PILOT_REPORT.md)

## Goal

Introduce exactly one local grammatical error while preserving meaning and all simplification operations. The simplified version receives `FLUENCY = 1`; the degraded version receives `FLUENCY = 0`.

## Method

Any unassigned English pair with one `source_strategy` is eligible when its simplified version contains an auxiliary, determiner, preposition, or at least five words. These cues permit one agreement, determiner, preposition, or local word-order error.

Qwen2.5-7B-Instruct receives both texts, the assigned operation, and its cue through [`fluency_degradation_v1.json`](../prompts/fluency_degradation_v1.json). Automatic checks require valid JSON, changed text, the assigned operation, and declared spans. Human review must confirm one grammatical error, unchanged meaning, and no second degradation.

Pilot: 10 good, 23 medium, and 17 failed automatic results. Revision and human audit are required before scaling.
