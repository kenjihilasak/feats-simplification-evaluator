# Explanation degradation

[Methodology index](MULTI_AXIS_CORPUS.md) · [pilot report](PILOT_REPORT.md)

## Goal

Remove exactly one helpful explanation added by the simplified version. The simplified version receives `EXPL = 1`; the degraded version receives `EXPL = 0`.

## Method

Only pairs with the single Phase 3a `source_strategy = EXPL` are eligible. The detector proposes up to eight simplified-version tokens absent from the original; added wording alone does not prove explanation.

Using [`expl_degradation_v1.json`](../prompts/expl_degradation_v1.json), Qwen removes one candidate explanation. Automatic checks verify structure, change, operation, and spans. Human review must confirm that the removed material was helpful explanation, its removal reduces explanatory support, and necessary facts remain.

Pilot: 39 good, 8 medium, and 3 failed automatic results. Human semantic review remains required before scaling.
