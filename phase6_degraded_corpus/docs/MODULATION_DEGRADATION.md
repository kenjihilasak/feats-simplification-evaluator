# Modulation degradation

[Methodology index](MULTI_AXIS_CORPUS.md) · [pilot report](PILOT_REPORT.md)

## Goal

Undo one helpful information restructuring by restoring the original clause order or recombining a helpful split. The simplified version receives `MOD = 1`; the degraded version receives `MOD = 0`.

## Method

Only pairs with the single Phase 3a `source_strategy = MOD` are eligible. They receive `reverse_information_restructuring` and are protected from other axis assignments because MOD is scarce. The current detector does not locate the exact structural edit.

Using [`mod_degradation_v1.json`](../prompts/mod_degradation_v1.json), Qwen moves the simplified text closer to the original structure. Automatic checks verify structure, change, operation, and spans. Human review must confirm a real reversal while meaning, vocabulary, explanations, omissions, and fluency remain unchanged.

Pilot: 23 good, 27 medium, and 0 failed automatic results. Medium cases require span verification and semantic audit.
