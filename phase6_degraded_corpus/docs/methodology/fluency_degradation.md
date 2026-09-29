# Fluency degradation

[Documentation index](../README.md) · [methodology overview](../overview.md) · [pilot report](../reports/pilot_report.md)

## Goal

Introduce exactly one local grammatical error without changing meaning or another simplification operation. The simplified version receives `FLUENCY = 1`; the degraded version receives `FLUENCY = 0`.

## Eligible pairs

Any unassigned single-strategy pair whose simplified version contains an auxiliary, determiner, preposition, or at least five words.

## Degradation workflow

```mermaid
flowchart LR
    A["Simplified pair"] --> B["Detect grammar site"]
    B --> C["Choose one local error"]
    C --> D["Qwen generation"]
    D --> E["Automatic checks"]
    E --> F["Human audit"]
```

### Workflow blocks

| Block | Main idea |
|---|---|
| A — Input | A Simplified sentence from an unassigned single-strategy pair. |
| B — Detect | Locate an auxiliary, determiner, preposition, or safe local word-order site. |
| C — Choose | Assign exactly one grammatical error type. |
| D — Generate | Qwen changes only that local form, not the facts or vocabulary meaning. |
| E — Check | Reject copies, formatting-only edits, wrong operations, or unverifiable spans. |
| F — Audit | Confirm one visible grammar error and unchanged meaning. |

The detector selects an agreement, determiner, preposition, or local word-order site. The prompt asks Qwen to apply one error at that site.

## Labels and values sent to Qwen

| Field | Meaning | Example |
|---|---|---|
| `source_strategy` | Phase 3a label already present in the pair. | `EXPL` |
| `target_axis` | Phase 6 dimension selected for degradation. | `FLUENCY` |
| `assigned_operation` | Specific grammatical error to introduce. | `preposition_error` |
| `target_cue` | Local form selected for editing. | `on` |

```text
source_strategy: EXPL
target_axis: FLUENCY
assigned_operation: preposition_error
target_cue: on
        ↓ prompt
Qwen introduces one local preposition error
```

Qwen receives Original, Simplified, `assigned_operation`, and `target_cue`. It does **not** receive `source_strategy` directly; `target_axis` selects the Fluency prompt.

### Implementation links

- [Attach `source_strategy`](../../src/selection/select_multi_axis_inputs.py#L99-L101)
- [Detect Fluency operations and cues](../../src/planning/multi_axis.py#L48-L69)
- [Choose axis, operation, and cue](../../src/planning/multi_axis.py#L177-L207)
- [Insert operation and cue into the prompt](../../src/generation/generate_degradations.py#L136-L152)
- [Versioned Fluency prompt](../../prompts/fluency_degradation_v1.json)

## Prompt used in the pilot

Exact version: [`fluency_degradation_v1.json`](../../prompts/fluency_degradation_v1.json).

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
Target cue: {target_cue}

Introduce exactly one obvious local grammatical error of the assigned type. Preserve every fact, word meaning, and simplification operation. Do not add, remove, or contradict content. Return keys degraded_simplification, changed_span, replacement_span, operation_type, and brief_verification. operation_type must be exactly {assigned_operation}.
```

</details>

## Acceptance checks

- one visible grammatical error
- unchanged propositions and lexical meaning
- declared edit occurs in the output

## Pilot evaluation

| Automatic result | Count | Rate |
|---|---:|---:|
| Good | 9 | 18% |
| Medium | 12 | 24% |
| Failed | 29 | 58% |

Automatic structural triage of 50 cases; semantic human audit is pending.

## What we learned

The model often declared a fluency edit without actually changing the sentence.

**Next change:** Use deterministic local edits where possible and compare the declared source and replacement spans directly.
