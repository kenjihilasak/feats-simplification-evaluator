# ILLOC degradation (v2)

[Methodology index](README.md)

**Goal:** change **only the communicative force** of a declarative Simplified sentence; the proposition and all facts stay the same.

**Generator:** Qwen/Qwen2.5-7B-Instruct @ `a09a35458c702b33eeacc393d103063234e8bc28`, bf16. Prompt: [`illoc_inject_v2.json`](../../prompts/v2/illoc_inject_v2.json).

## Operations

The three operations are balanced within each source.

| Operation | Example | Checks |
|---|---|---|
| `assertion_to_question` | "Was the tower built in 1889?" | Ends with `?`; question opening; content lemmas within 1. |
| `assertion_to_directive` | "Note that the tower was built in 1889." | ≤ 2 edit blocks; added words from the directive lexicon; only auxiliaries deleted. |
| `assertion_to_hedged` | "The tower was probably built in 1889." | ≤ 2 edit blocks; added words from the hedge lexicon; only auxiliaries deleted. |

All operations also require: acceptability ≥ min(τ, clean − δ), not a no-op, not a copy of the Original.

**Why injection instead of reversal (v1):** real illocution changes almost never occur in the source data (16 question-mark differences in 73,586 pairs).

## Workflow

1. Start from a clean declarative Simplified sentence.
2. Select one operation: question, directive, or hedged assertion.
3. Ask Qwen to change the communicative force while retaining the proposition.
4. Reject outputs that add factual content, copy the Original, make no change, or fail the operation-specific form checks.
5. Keep the first fluent candidate that passes all checks.

**Decision (2026-09-30):** hedging counts as **ILLOC**, not MEANING. It changes the force (certain → uncertain) while keeping the proposition; MEANING is reserved for contradictions.

## Evidence

- **Dev (automatic):** v1 pipeline 32%, v2 88%. By operation: question 93%, directive 84%, hedged 84%.
- **Heldout (human, question + directive):** **Qwen 90%** vs Gemma 89% (tie). Qwen wins the tie-break: smaller model, and much better at `hedged` (Gemma 29%).
- **Hedged (human, 40 full-run outputs):** **95%** valid (38/40). Included in the corpus.
