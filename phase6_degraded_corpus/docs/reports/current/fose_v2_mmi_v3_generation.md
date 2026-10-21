# FOSE v2 / MMI v3 generation

## Status

Review samples are ready for all five axes: OMIT, SYN, EXPL (`runs/fose_en_v2/review_sample.jsonl`, 180 items) and MOD, ILLOC (`runs/mmi_en_v3/review_sample.jsonl`, 120 items). Each sample has a hidden `review_key.json`. No full-scale corpus was generated; that waits for the human review (≥85% valid per axis).

## FOSE v2 yield

| Axis | Eligible pool | Checked valid | Checked rejected | Review |
|---|---:|---:|---:|---:|
| OMIT | 522 | 310 | 212 | 60 |
| SYN | 177 | 109 | 68 | 60 |
| EXPL | 81 | 75 | 6 | 60 |

The review sample uses originals excluded from frozen evaluation data, MMI held-out splits, and the FOSE v1 audit. EXPL is stratified by `expl_pattern`; the other axes are stratified by corpus.

## Rejection reasons

- `EXPL/acceptable`: 3
- `EXPL/clean_to_degraded_not_contradiction`: 3
- `OMIT/acceptable`: 84
- `OMIT/inserted_from_original`: 168
- `SYN/acceptable`: 15
- `SYN/different_lemmas`: 1
- `SYN/entails_both_ways`: 53
- `SYN/zipf_gap_ge_0.5`: 12

## Shortcut audit (FOSE v2, corrected)

The first audit (AUC 0.97–1.00) was inflated by a leak: good examples had NLI and CoLA features fixed at 0. After the fix, gate features (sentence count, `?`, `!`, commas, CoLA, NLI) and definitional features (length, overlap with the original: the change itself for these rule axes) are reported separately. See `runs/fose_en_v2/reports/shortcut_audit.md`.

| Axis | Gate AUC (≤0.70) | Definitional AUC | Pass |
|---|---:|---:|:---:|
| OMIT | 0.611 | 0.957 | yes |
| SYN | 0.523 | 0.689 | yes |
| EXPL | 0.609 | 0.881 | yes (the `marker_gloss` pattern alone, 16 items, gives 0.906) |

## MMI v3 implementation

- Same-sentence-count MOD operations: `mod_front_heavy`, `mod_bury_topic`, and rule-based `mod_sentence_reorder`.
- Short ILLOC operations: imperative swap, hedge swap, exclamation, and question-to-statement.
- v3 strict-JSON prompts and hard checker gates are installed; selected models remain Gemma-3-12B-it for MOD and Qwen2.5-7B-Instruct for ILLOC.

## MMI v3 generation (2 October 2026)

Generated on L40S nodes (Slurm jobs 8074278, 8074279; scoring 8074324), plans from the v2 allocation on originals no review has seen (WikiAutoEN and ASSET only), 4 candidates per row.

Changes from the first v3 attempt (archived in `runs/mmi_en_v3/archive_v3a/`):

- The v3 prompt templates contained literal `\n`; they now use real line breaks.
- `illoc_exclaim` removed: it only replaced "." with "!", not a speech-act change, and "!" is a gate feature.
- `illoc_hedge_swap`: only modal hedges (may, might, could, probably…) count; approximators ("about", "around") and changed numbers are rejected, since they are MEANING changes.
- `illoc_imperative_swap`: only planned on sentences with a deontic modal (should, must, need to, have to), taken from all axes of the allocation because they are rare. The check requires an imperative root without a subject, allows the dropped subject (≤2 content words, ≤4 tokens) and no new content.
- Token limit for the other ILLOC operations: ±2 instead of ±1 ("is" → "may be", "was" → "might have been").
- MOD LLM operations receive one sentence only and the result is put back into the text: given the whole text, Gemma merged the sentences.
- New MOD checks: `mod_front_heavy` must front a phrase of at least 4 tokens; `mod_bury_topic` must place the original subject after the main verb.

| Operation | Valid / planned | In review sample |
|---|---:|---:|
| `mod_sentence_reorder` (rule) | 108 / 119 | 20 |
| `mod_front_heavy` (Gemma-3-12B) | 70 / 120 | 20 |
| `mod_bury_topic` (Gemma-3-12B) | 30 / 121 | 20 |
| `illoc_hedge_swap` (Qwen2.5-7B) | 229 / 270 | 45 |
| `illoc_imperative_swap` (Qwen2.5-7B) | 15 / 90 | 15 |

Main rejection reasons: `mod_bury_topic` topic not moved after the verb and CoLA drop; `mod_front_heavy` CoLA drop and fronted phrase too short; `illoc_imperative_swap` no imperative root or content changes.

### Shortcut audit, MOD and ILLOC (`runs/mmi_en_v3/reports/`)

| Operation | Gate AUC | Largest feature |
|---|---:|---|
| v3 `mod_sentence_reorder` | 0.661 | cola_delta |
| v3 `mod_front_heavy` | 0.738 | delta_commas |
| v3 `mod_bury_topic` | 0.634 | cola_delta |
| v3 `illoc_hedge_swap` | 0.696 | token_overlap |
| v3 `illoc_imperative_swap` | 0.507 | token_overlap |
| v2 `recombine_split` | 0.960 | delta_sentences |
| v2 `assertion_to_question` | 1.000 | has_question |
| v2 `assertion_to_hedged` | 0.713 | token_overlap |
| v2 `assertion_to_directive` | 0.691 | delta_characters |

The v3 operations alone pass the gate (MOD 0.663, ILLOC 0.691). Any share of the v2 data makes MOD and ILLOC fail, because `recombine_split` and `assertion_to_question` are separated by sentence count and the question mark. Rebalancing therefore kept no v2 rows (`reports/rebalanced/decisions.json`).

**Decision needed before full-scale generation:** either (a) train MOD/ILLOC on v3 operations only, generated at scale, or (b) keep the v2 operations as a capped minority, with the cap set by re-running the audit on the full-scale v3 data.

## Graded groups and the merged S1 round (2 October 2026)

`runs/graded_en_v1/` (Slurm job 8074654): one pair yields the clean text (1.0), one undone edit (0.5) and two undone edits (0.0). A group is valid only if both single edits and the combination pass the checks.

| Axis | How levels are built | Candidate groups | Valid |
|---|---|---:|---:|
| OMIT | two omitted spans restored | 612 | 163 |
| SYN | two harder words restored | 85 | 30 |
| MOD | fronting (Gemma) and/or reordering dependent sentences (rule) | 162 | 139 |

EXPL has no levels: only 5 English pairs have two explanatory insertions. ILLOC is binary by nature.

Fixes made while building them: `detokenize` now closes paired straight quotes (the FOSE v2 sample showed `" Help "`, which reads as a fluency error); a MOD fronting candidate is rejected when it strands the verb ("…, it was."); LLM outputs get the clean text's double quotes back.

The merged S1 round is `runs/annotation_v1/s1_items.jsonl` + `s1_key.json` (300 items): OMIT 60 and MOD 60 ranking groups, SYN 30 ranking groups + 30 pairs, EXPL 60 pairs, ILLOC 60 pairs. FOSE v2 pairs were regenerated from their pool rows with the fixed detokenizer (only whitespace changed). The annotation package itself is Task B.
