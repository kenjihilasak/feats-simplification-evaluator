# Omission degradation

[Methodology index](MULTI_AXIS_CORPUS.md) · [pilot report](PILOT_REPORT.md)

## Goal

Undo one useful omission by restoring unnecessary or audience-inappropriate information. The simplified version receives `OMIT = 1`; the degraded version receives `OMIT = 0`.

## Method

Only pairs with the single Phase 3a `source_strategy = OMIT` are eligible. The detector proposes up to eight original tokens absent from the simplified version; this lexical cue is not proof of a valid omission.

Using [`omit_degradation_v1.json`](../prompts/omit_degradation_v1.json), Qwen restores exactly one original detail. Automatic checks verify structure, change, operation, and spans. Human review must confirm that the detail comes from the original, was usefully omitted, is unnecessary for the audience, and introduces no other main error.

Pilot: 8 good, 14 medium, and 28 failed automatic results. Cue extraction and prompting require revision before scaling.
