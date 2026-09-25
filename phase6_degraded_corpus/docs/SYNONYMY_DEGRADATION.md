# Synonymy degradation

[Methodology index](MULTI_AXIS_CORPUS.md) · [pilot report](PILOT_REPORT.md)

## Goal

Undo one helpful lexical simplification by restoring a more complex original expression. The simplified version receives `SYN = 1`; the degraded version receives `SYN = 0`.

## Method

Only pairs with the single Phase 3a `source_strategy = SYN` are eligible. The detector proposes up to four original tokens absent from the simplified version; token difference alone does not establish synonymy.

Using [`syn_degradation_v1.json`](../prompts/syn_degradation_v1.json), Qwen restores one candidate expression. Automatic checks verify structure, change, operation, and spans. Human review must confirm that it comes from the original, is semantically equivalent, is more difficult, and is the only degradation.

Pilot: 6 good, 16 medium, and 28 failed automatic results. Detection and prompting require revision before scaling.
