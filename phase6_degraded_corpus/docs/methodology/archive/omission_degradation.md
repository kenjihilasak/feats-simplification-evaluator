# Omission degradation

[Documentation index](../../README.md) · [methodology overview](../../overview.md) · [pilot report](../../reports/archive/pilot_report.md)

## Goal

Undo one useful omission by restoring unnecessary or audience-inappropriate information. The simplified version receives `OMIT = 1`; the degraded version receives `OMIT = 0`.

## Eligible pairs

Only pairs with the single Phase 3a `source_strategy = OMIT`.

## Degradation workflow

```mermaid
flowchart LR
    A["OMIT pair"] --> B["Find omitted original span"]
    B --> C["Select one unnecessary detail"]
    C --> D["Qwen restores detail"]
    D --> E["Automatic checks"]
    E --> F["Human audit"]
```

### Workflow blocks

| Block | Main idea |
|---|---|
| A — Input | A pair whose only detected source strategy is OMIT. |
| B — Detect | Find original content absent from the Simplified sentence. |
| C — Select | Choose one omitted detail that was unnecessary for the target reader. |
| D — Generate | Qwen restores only that original detail. |
| E — Check | Verify a substantive change, matching operation, and literal restored span. |
| F — Audit | Confirm the detail was usefully omitted and no other axis changed. |

The detector currently proposes original tokens absent from the Simplified sentence. Qwen is asked to restore one candidate detail without inventing content.

## Labels and values sent to Qwen

| Field | Meaning | Example |
|---|---|---|
| `source_strategy` | Required Phase 3a label for this direct assignment. | `OMIT` |
| `target_axis` | Phase 6 dimension selected for degradation. | `OMIT` |
| `assigned_operation` | Instruction to restore omitted source content. | `restore_omitted_complex_detail` |
| `target_cue` | Candidate original detail absent from Simplified. | `in the 1934 FIFA World Cup` |

```text
source_strategy: OMIT
target_axis: OMIT
assigned_operation: restore_omitted_complex_detail
target_cue: in the 1934 FIFA World Cup
        ↓ prompt
Qwen restores one omitted original detail
```

This is a direct assignment: `source_strategy` must equal `OMIT`. Qwen receives Original, Simplified, `assigned_operation`, and `target_cue`, but not the strategy label itself.

### Implementation links

- [Attach `source_strategy`](../../../src/selection/select_multi_axis_inputs.py#L99-L101)
- [Build the Omission operation and cue](../../../src/planning/multi_axis.py#L102-L107)
- [Require matching strategy and target](../../../src/planning/multi_axis.py#L121-L139)
- [Choose and store operation and cue](../../../src/planning/multi_axis.py#L177-L207)
- [Insert operation and cue into the prompt](../../../src/generation/generate_degradations.py#L136-L152)
- [Versioned Omission prompt](../../../prompts/archive/v1/omit_degradation_v1.json)

## Prompt used in the pilot

Exact version: [`omit_degradation_v1.json`](../../../prompts/archive/v1/omit_degradation_v1.json).

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
Candidate original detail: {target_cue}

Undo only the useful omission by restoring one unnecessary or audience-inappropriate detail from the original. Preserve meaning, fluency, and every other simplification choice. Do not invent information and do not remove necessary content. Return keys degraded_simplification, changed_span, replacement_span, operation_type, and brief_verification. operation_type must be exactly {assigned_operation}.
```

</details>

## Acceptance checks

- restored text is present in the original
- the detail was usefully omitted
- no invented fact or second degradation

## Pilot evaluation

| Automatic result | Count | Rate |
|---|---:|---:|
| Good | 7 | 14% |
| Medium | 13 | 26% |
| Failed | 30 | 60% |

Automatic structural triage of 50 cases; semantic human audit is pending.

## What we learned

Token difference is a weak proxy for an omitted detail, and more than half of outputs failed.

**Next change:** Extract a contiguous source span, verify that it is absent from the simplified version, and require the restored span literally in the output.
