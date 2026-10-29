# ILLOC degradation (v4)

[Methodology index](README.md)

**Definition (28 Oct 2026):** Illocution is how directly a sentence expresses its communicative purpose (informing, instructing, asking, warning). A good Easy-to-Read text keeps the purpose of the original and makes it explicit: the reader knows at once what is stated, asked or required. A change of the purpose itself (a warning becoming a suggestion) is a fidelity error, not a simplification. Changes in the strength of a claim ("is" → "might be") are scored under MEANING.

**Goal:** keep the act and its content, and express it **less directly**, so the reader has to infer the purpose.

**Generator:** Qwen/Qwen2.5-7B-Instruct @ `a09a35458c702b33eeacc393d103063234e8bc28`, bf16. Prompts: `prompts/v4_<lang>/illoc_indirect_v4.json` (en, es, fr, it, ca, ru, ar). Only the host sentence is sent and replaced.

## Hosts

Only a sentence that already performs a direct act on the reader can host the degradation ([`illoc_host`](../../src/selection/select_multilingual_pools.py)):

| Kind | Detected by | Operation |
|---|---|---|
| Directive | imperative root without a subject | `illoc_directive_to_impersonal` |
| Question | four or more words, ends with a question mark | `illoc_question_to_indirect` |
| Address | a second-person word, or a parsed `Person=2` | `illoc_address_to_impersonal` |

Quoted spans are blanked before detection, so titles ("Curb Your Enthusiasm") and cited slogans do not count. Narrative corpora (Saaq al-Bambuu, Terence, RuAdaptFairytales) are excluded: there a question or "you" is a character speaking, not the text addressing its reader. Encyclopedic statements have no direct act and host no ILLOC item.

## Operations

| Operation | Example (clean → degraded) |
|---|---|
| `illoc_directive_to_impersonal` | "Bring your ID to the appointment." → "Identification is required at the appointment." |
| `illoc_question_to_indirect` | "Have you used these NHS services in the last year?" → "Use of these NHS services in the last year is the subject of this question." |
| `illoc_address_to_impersonal` | "You can only find it on Christmas Island." → "It is only found on Christmas Island." |

## Automatic checks

A candidate is kept only if it passes all of these ([`check_illoc_v4`](../../src/evaluation/score_mmi_candidates.py)):
- the checkers' own parse finds the act in the clean sentence (filters false hosts such as titles and names);
- exactly one sentence changed;
- the edited sentence asks no question, is not an imperative, does not address the reader and has no exclamation;
- an indirect question embeds the whole question under a verb of asking or "the question is" + if/wh-word;
- no hedge added; numbers identical; every proper noun kept; negation kept;
- at most two content lemmas added and two removed; at most five tokens longer or shorter (length is a shortcut a scorer could learn);
- no NLI contradiction in either direction (clean ↔ degraded);
- every new word exists in the language (wordfreq), Catalan elides "es"/"se" before a vowel, no accent-only repair, quotation marks unchanged;
- acceptability ≥ min(τ, clean − δ); not a copy of the Original.

## Control version

Every ILLOC degradation rewords its sentence, so without a control "reworded and longer" alone predicts the lower score. Each item therefore also gets, where the checks pass, a **direct paraphrase** scored 1.0 (`illoc_direct_paraphrase`, same prompt file): a few words change but the act stays ("Note that a suicide pact is different…" → "Remember that a suicide pact is distinct…"). Checks: the act is kept, NLI entailment ≥ 0.5 both ways, and the same surface checks as a degradation ([`check_illoc_paraphrase`](../../src/evaluation/score_mmi_candidates.py)).

## Why the earlier operations were retired

In the first English review (Carlo, 27 Oct 2026) the v3 operations failed as degradations:
- **Statement → imperative** (`illoc_imperative_swap`): the reviewer preferred the imperative in both items; a direct instruction is an improvement in Easy-to-Read practice.
- **Hedge** (`illoc_hedge_swap`, "X is Y" → "X might be Y"): changes what the reader takes to be true, which is MEANING (team decision).

v2 and v3 injected acts into encyclopedic statements because natural acts are rare. v4 accepts that scarcity: about 2% of the English pool (237 of 14,142 pairs) contains a direct act on the reader, and most of these are generic "you" (see [the v2 multilingual report](../reports/current/phase6_v2_multilingual.md)).
