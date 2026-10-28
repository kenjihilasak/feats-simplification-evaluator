# MOD degradation (v2, graded v4)

[Methodology index](README.md)

**Graded groups v4 (28 Oct 2026):** a clean simplification gets two degraded versions of increasing severity.

| Level | Version | Operation |
|---|---|---|
| 1.0 | clean | the human simplification |
| 0.5 (mild) | A | `mod_front_heavy`: a phrase of four or more words is moved before the subject and main verb, so secondary information comes before the main idea (LLM, only that sentence is sent) |
| 0.0 (strong) | AB | A plus `mod_sentence_reorder`: two adjacent sentences where the second depends on the first are swapped, reversing the logical order (rule) |

In v3 the mild version was A or B (reorder alone) at random. The first English review tied mild and strong; a reorder alone can be as disruptive as both edits, so v4 always uses A as the mild version. B is still generated and recorded but not used ([`combine_mod_graded.py`](../../src/generation/combine_mod_graded.py)). Prompts: `prompts/v4_<lang>/` (the English, Spanish and French fronting prompts are unchanged from v3).

The rest of this page describes the earlier v2 pair operation (merge two sentences).

**Goal:** undo one helpful split: **merge two adjacent Simplified sentences into one**, with no change of facts or wording beyond joining words.

**Generator:** google/gemma-3-12b-it @ `96b6f1eccf38110c56df3a15bffe176da04bfd80`, bf16. It has no system role, so the system text is merged into the first user turn. Prompt: [`mod_merge_v2.json`](../../prompts/v2/mod_merge_v2.json).

## Operation

- **Eligible pairs:** the Simplified text has more sentences than the Original, word overlap ≥ 0.6, and length ratio 0.8–1.4. This is structural evidence, not the Phase 3a label.
- **Sentences:** the splitter does not cut after initials or titles.
- **Which pair:** one adjacent sentence pair is chosen by stable hash.
- **What the model sees:** only the two sentences, **never the Original**. It returns `merged_sentence`, which replaces the pair.

## Workflow

1. Start from a clean Simplified text with more sentences than its Original.
2. Choose one adjacent Simplified-sentence pair by stable hash.
3. Send only that pair to Gemma and request one merged sentence.
4. Replace exactly those two sentences with the returned sentence.
5. Keep the result only if it reduces the sentence count by one and preserves wording, facts, names, numbers, negation, and fluency.

## Automatic checks

A candidate is kept only if it passes all of these:
- one sentence fewer;
- the content-lemma symmetric difference is ≤ 2;
- numbers and negation identical;
- every proper noun is kept;
- no Original-only lemma leaks in;
- NLI entailment ≥ 0.5 in both directions (clean ↔ degraded);
- acceptability ≥ min(τ, clean − δ).

## Evidence

- **Dev (automatic):** v1 pipeline 6%, v2 85% (Qwen and Gemma tied).
- **Heldout (human):** **Gemma 95%** vs Qwen 89% (not significant, p = 0.38). Gemma wins the tie-break: same GPU time, more valid outputs.
