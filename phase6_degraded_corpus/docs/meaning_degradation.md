# Meaning degradation

[Methodology index](MULTI_AXIS_CORPUS.md) · [pilot report](PILOT_REPORT.md)

## Goal

Create one fluent but factually incorrect version while preserving every other simplification property. The simplified version receives `MEANING = 1`; the degraded version receives `MEANING = 0`.

## Eligible pairs

Any reviewed English pair with one source strategy and an explicit entity, number, date, negation, property, relation, or event cue. Evaluation corpora are excluded.

## Degradation workflow

```mermaid
flowchart LR
    A["Reviewed simplified pair"] --> B["Detect factual cue"]
    B --> C["Assign one contradiction type"]
    C --> D["Qwen generation"]
    D --> E["Structural validation"]
    E --> F["Human semantic audit"]
```

### Workflow blocks

| Block | Main idea |
|---|---|
| A — Input | A reviewed Simplified sentence and its Original. |
| B — Detect | Find one explicit factual cue: entity, number, date, negation, property, relation, or event. |
| C — Assign | Choose one applicable contradiction type while balancing the pilot. |
| D — Generate | Qwen rewrites only the Simplified sentence and introduces that contradiction. |
| E — Validate | Check JSON, changed span, replacement span, operation, and a substantive text change. |
| F — Audit | Verify a direct contradiction and reject any second change. |

The detector proposes a factual cue and the allocator selects one applicable corruption. Qwen generates the negative example; a reviewer accepts, retries, corrects, or rejects it.

## Prompt used in the pilot

Exact version: [`meaning_severe_v2.json`](../prompts/meaning_severe_v2.json).

<details>
<summary>Show prompt</summary>

**System**

```text
You create controlled negative examples for a text-simplification quality dataset. Rewrite only the valid simplified sentence. Introduce exactly one severe factual error of the assigned type. The distorted sentence MUST be factually incompatible with the original, MUST differ in meaning from the valid simplification, and MUST contain the replacement_span you report. It is not enough to paraphrase, omit detail, reduce specificity, fix grammar, or make a true statement weaker. Keep all other facts unchanged, preserve fluency, approximate length, and the simplification strategy. Return valid JSON only.
```

**User template**

```text
Original:
{original}

Valid simplified sentence:
{clean_simplification}

Assigned corruption type:
{corruption_type}

Suggested target cue:
{target_span}

First identify one central fact explicitly supported by the original. Replace or reverse that fact according to the assigned type. Verify that the final sentence directly contradicts the original and that replacement_span occurs verbatim in distorted_simplification. Return exactly:
{"distorted_simplification":"...","changed_clean_span":"exact text removed from the valid simplification","replacement_span":"exact new text present in the distorted sentence","corruption_type":"{corruption_type}","brief_verification":"Name the original fact and explain the direct contradiction."}
```

</details>

## Acceptance checks

- exactly one factual contradiction
- all other facts and the source strategy remain unchanged
- fluent output with a verifiable replacement

## Pilot evaluation

| Result | Count | Rate |
|---|---:|---:|
| Accepted first pass | 20 | 40% |
| Accepted stricter retry | 11 | 22% |
| Manually corrected | 19 | 38% |
| **Final accepted** | **50** | **100%** |

Human audit. The final 100% follows correction; it is not the model's unaided success rate.

## What we learned

Structural validation was insufficient: 19/50 cases still required manual correction after two model passes.

**Next change:** Constrain replacements to detector-provided candidates, verify contradiction against the original, and reject outputs whose declared edit is absent.
