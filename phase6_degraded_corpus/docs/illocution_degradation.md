# Illocution degradation

[Methodology index](MULTI_AXIS_CORPUS.md) · [pilot report](PILOT_REPORT.md)

## Goal

Reverse one useful adaptation of speech act, modality, or certainty while preserving propositional facts. The simplified version receives `ILLOC = 1`; the degraded version receives `ILLOC = 0`.

## Eligible pairs

Any unassigned single-strategy pair with an explicit question, modal, request/communication, or certainty cue.

## Degradation workflow

```mermaid
flowchart LR
    A["Original + simplified"] --> B["Detect illocution cue"]
    B --> C["Choose one reversal"]
    C --> D["Qwen generation"]
    D --> E["Automatic checks"]
    E --> F["Human audit"]
```

The detector searches the simplified version first and then the original. Qwen reverses one cue with [`illoc_degradation_v1.json`](../prompts/illoc_degradation_v1.json).

## Acceptance checks

- a real speech-act, modality, or certainty adaptation is reversed
- propositional facts remain unchanged
- no second degradation is introduced

## Pilot evaluation

| Automatic result | Count | Rate |
|---|---:|---:|
| Good | 33 | 66% |
| Medium | 15 | 30% |
| Failed | 2 | 4% |

Automatic structural triage of 50 cases; semantic human audit is pending.

## What we learned

Explicit cues made this axis relatively reliable, but cue presence alone does not prove a useful adaptation.

**Next change:** Require an original–simplified cue contrast and add operation-specific checks for questions, modality, requests, and certainty.
