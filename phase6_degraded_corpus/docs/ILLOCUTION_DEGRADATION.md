# Illocution degradation

[Methodology index](MULTI_AXIS_CORPUS.md) · [pilot report](PILOT_REPORT.md)

## Goal

Reverse one useful adaptation of speech act, modality, or certainty while preserving propositional content. The simplified version receives `ILLOC = 1`; the degraded version receives `ILLOC = 0`.

## Method

Any unassigned English pair with one `source_strategy` is eligible when the original–simplified contrast contains an explicit cue: a question-mark mismatch, modal verb, request or communication verb, or certainty marker. The detector searches the simplified version first and then the original; it does not infer implicit speech acts.

Using [`illoc_degradation_v1.json`](../prompts/illoc_degradation_v1.json), Qwen reverses exactly one detected adaptation. Automatic checks verify structure, change, operation, and spans. Human review must confirm a real illocutionary change, unchanged facts, and no second degradation.

Pilot: 33 good, 15 medium, and 2 failed automatic results. Human semantic review remains required before scaling.
