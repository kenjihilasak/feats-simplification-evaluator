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

### Workflow blocks

| Block | Main idea |
|---|---|
| A — Input | An unassigned pair with an explicit speech-act, modality, or certainty cue. |
| B — Detect | Compare Original and Simplified cues; exclude false cues such as May in dates. |
| C — Choose | Select one question, request, assertion, modality, or certainty reversal. |
| D — Generate | Qwen changes only the selected communicative force. |
| E — Check | Verify substantive change, matching operation, and declared spans. |
| F — Audit | Confirm the illocution changed while propositional facts remained stable. |

The detector searches the Simplified sentence first and then the Original for an explicit contrast. Qwen reverses one selected cue.

## Prompt used in the pilot

Exact version: [`illoc_degradation_v1.json`](../prompts/illoc_degradation_v1.json).

<details>
<summary>Show prompt</summary>

**System**

```text
You create controlled negative examples for text-simplification research. Return only one valid JSON object. Do not add commentary.
```

**User template**

```text
Original: {original}
Clean simplification: {clean_simplification}
Assigned operation: {assigned_operation}
Speech-act cue: {target_cue}

Reverse exactly one useful illocutionary adaptation involving question, request, assertion, modality, or certainty. Preserve the propositional facts, fluency, and all other simplification operations. Return keys degraded_simplification, changed_span, replacement_span, operation_type, and brief_verification. operation_type must be exactly {assigned_operation}.
```

</details>

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
