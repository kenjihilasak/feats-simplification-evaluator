# Illocution degradation

[Methodology index](MULTI_AXIS_CORPUS.md) · [pilot report](PILOT_REPORT.md)

## Goal

Reverse one useful adaptation of speech act, modality, or certainty while preserving propositional facts. The simplified version receives `ILLOC = 1`; the degraded version receives `ILLOC = 0`.

## Eligible pairs

Any unassigned single-strategy pair with an explicit question, modal, request/communication, or certainty cue.

## Degradation workflow

```mermaid
flowchart LR
    A["Original + simplified"] --> B["Regex cue search"]
    B --> C["Seeded cue selection"]
    C --> D["Qwen generation"]
    D --> E["Automatic checks"]
    E --> F["Human audit"]
```

### Workflow blocks

| Block | Main idea |
|---|---|
| A — Input | An unassigned pair with an explicit speech-act, modality, or certainty cue. |
| B — Detect | Compare final question marks; otherwise search cue words in Simplified first and Original only if none are found. Exclude `May` followed by a date. |
| C — Choose | If the pair is assigned to ILLOC, select one detected cue by stable seeded hash. This is deterministic, not a semantic ranking. |
| D — Generate | Qwen changes only the selected communicative force. |
| E — Check | Verify substantive change, matching operation, and declared spans. |
| F — Audit | Confirm the illocution changed while propositional facts remained stable. |

The pilot compares Original and Simplified only for final question-mark mismatch. For modality, request, and certainty, it searches a fixed keyword list in Simplified first and falls back to Original. The allocator selects one cue reproducibly with the experiment seed; Qwen then attempts the reversal.

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
