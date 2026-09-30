# Explanation degradation

[Documentation index](../../README.md) · [methodology overview](../../overview.md) · [pilot report](../../reports/archive/pilot_report.md)

## Goal

Remove exactly one helpful explanation added by the simplified version. The simplified version receives `EXPL = 1`; the degraded version receives `EXPL = 0`.

## Eligible pairs

Only pairs with the single Phase 3a `source_strategy = EXPL`.

## Degradation workflow

```mermaid
flowchart LR
    A["EXPL pair"] --> B["Find added simplified span"]
    B --> C["Select one explanation"]
    C --> D["Qwen removes it"]
    D --> E["Automatic checks"]
    E --> F["Human audit"]
```

### Workflow blocks

| Block | Main idea |
|---|---|
| A — Input | A pair whose only detected source strategy is EXPL. |
| B — Detect | Find content added in the Simplified sentence but absent from the Original. |
| C — Select | Choose one added span that genuinely explains an original concept. |
| D — Generate | Qwen removes only that explanation. |
| E — Check | Verify substantive deletion, matching operation, and declared span. |
| F — Audit | Confirm explanatory support decreased while necessary facts and grammar remained. |

The pilot detector proposes Simplified tokens absent from the Original. Qwen removes one candidate span; human review determines whether it was truly explanatory.

## Labels and values sent to Qwen

| Field | Meaning | Example |
|---|---|---|
| `source_strategy` | Required Phase 3a label for this direct assignment. | `EXPL` |
| `target_axis` | Phase 6 dimension selected for degradation. | `EXPL` |
| `assigned_operation` | Instruction to remove an added explanation. | `remove_added_explanation` |
| `target_cue` | Candidate explanatory text added in Simplified. | `the root of a plant known as ginger` |

```text
source_strategy: EXPL
target_axis: EXPL
assigned_operation: remove_added_explanation
target_cue: the root of a plant known as ginger
        ↓ prompt
Qwen removes one added explanation
```

This is a direct assignment: `source_strategy` must equal `EXPL`. Qwen receives Original, Simplified, `assigned_operation`, and `target_cue`, but not the strategy label itself.

### Implementation links

- [Attach `source_strategy`](../../../src/selection/select_multi_axis_inputs.py#L99-L101)
- [Build the Explanation operation and cue](../../../src/planning/multi_axis.py#L114-L117)
- [Require matching strategy and target](../../../src/planning/multi_axis.py#L121-L139)
- [Choose and store operation and cue](../../../src/planning/multi_axis.py#L177-L207)
- [Insert operation and cue into the prompt](../../../src/generation/generate_degradations.py#L136-L152)
- [Versioned Explanation prompt](../../../prompts/archive/v1/expl_degradation_v1.json)

## Prompt used in the pilot

Exact version: [`expl_degradation_v1.json`](../../../prompts/archive/v1/expl_degradation_v1.json).

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
Candidate explanation: {target_cue}

Remove exactly one helpful explanation added by the clean simplification. Keep the remaining sentence grammatical and preserve meaning, omission, synonymy, modulation, and illocution. Do not introduce new facts. Return keys degraded_simplification, changed_span, replacement_span, operation_type, and brief_verification. operation_type must be exactly {assigned_operation}.
```

</details>

## Acceptance checks

- removed material is a helpful explanation
- necessary facts and grammar remain intact
- no other simplification operation changes

## Pilot evaluation

| Automatic result | Count | Rate |
|---|---:|---:|
| Good | 35 | 70% |
| Medium | 8 | 16% |
| Failed | 7 | 14% |

Automatic structural triage of 50 cases; semantic human audit is pending.

## What we learned

This axis had the strongest automatic result, although added tokens are not always explanatory.

**Next change:** Detect contiguous added spans and classify explanatory function before deletion.
