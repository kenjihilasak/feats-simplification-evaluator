# MEANING degradation (v2.1)

[Methodology index](README.md)

**Goal:** one factual change that makes the Simplified text **contradict the Original**; everything else unchanged and fluent.

**Generator:** Qwen/Qwen2.5-7B-Instruct @ `a09a35458c702b33eeacc393d103063234e8bc28`, bf16. Prompt: [`meaning_span_v2.json`](../../prompts/v2/meaning_span_v2.json).

## Operation

The planner picks **one** span in the Simplified text. Each type is balanced within its source. The span must also appear in the Original, so that changing it can contradict the Original.

| Type | Who edits | Rule |
|---|---|---|
| number | rule | Scale ×2/×3/×10 (×0.5 when ≥ 1000), keep the format. Skip days of the month, numbers inside names ("Voyager 2") and range ends. |
| date | rule | Year ± 3–40 (not a year present in the Original); month → another month. |
| negation | rule | `was` → `was not`; `was also` → `was also not`; `has X` → `does not have X`; `there were X` → `there were no X`; delete `not` / `never`; `no X` → `some X`. |
| entity, event, property, relation | LLM | The model returns **only** the replacement for the span, which is spliced into the text. Event spans include their auxiliary (`was born` → `died`). No relation flip on already negated clauses. |

After splicing, a/an agreement is fixed.

## Automatic checks

A candidate is kept only if it passes all of these:
- exactly one edit block;
- NLI(Original → degraded) contradiction ≥ 0.5;
- acceptability ≥ clean − δ;
- for entity/property swaps, the new words are not in the Original;
- not a no-op, not a copy of the Original.

## Evidence

- **Dev (automatic):** v1 pipeline 39%, v2 75%.
- **Heldout (human, 57 fresh pairs):** **88%** (WikiAutoEN 90%, ASSET 75%, Vikidia 100%).
- **Residual errors:** LLM entity swaps that produce name hybrids or internal inconsistencies, and swaps whose surrounding predicate is not in the Original.
