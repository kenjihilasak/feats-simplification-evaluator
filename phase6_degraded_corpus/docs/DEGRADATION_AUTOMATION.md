# Meaning-degradation pilot and automation

[Phase 6 README](../README.md)

## Goal

Create one fluent but factually wrong simplification for each of 50 English pairs. The pilot changes **Meaning Preservation only**: clean = `1`, severe distortion = `0`. Each clean input has one predicted simplification strategy, which the degradation should preserve.

## Pipeline

1. **Select:** choose 50 unique originals; exclude evaluation corpora; stratify by corpus, length, and single strategy. Keep 150 deterministic backups.
2. **Review clean inputs:** require faithfulness, no unsupported content, fluency, and meaningful simplification. Replace every rejection with an accepted backup.
3. **Detect:** identify applicable entity, number, date, negation, property, relation, and event cues.
4. **Assign:** choose one applicable corruption by minimizing `assigned_count / target_count`; break ties with a seeded hash.
5. **Generate:** prompt the pinned Qwen model with the original, clean simplification, assigned type, and cue.
6. **Validate:** require valid JSON, changed text, matching type, and literal application of the declared replacement.
7. **Audit:** accept, retry, manually correct, or reject each output. Only an explicit contradiction with one meaning error enters the pilot corpus.

## Detector and allocator

| Corruption | Cue |
|---|---|
| entity replacement | named-entity/capitalized span |
| number replacement | numeric span excluding dates |
| date replacement | four-digit year or capitalized month |
| negation reversal | negation or auxiliary verb |
| property replacement | controlled adjective/direction lexicon |
| relation reversal | event verb or auxiliary; dependency relation at scale |
| event replacement | event verb or central-event fallback |

At scale, the detector builds an applicability matrix first. The allocator balances only among applicable types, so a human does not select a corruption for every pair. Automatic assignments remain proposals and can be corrected during audit.

## Prompt and inference

Model: `Qwen/Qwen2.5-7B-Instruct` at revision `a09a35458c702b33eeacc393d103063234e8bc28`. Inference uses 4-bit NF4, bfloat16 computation, greedy decoding, batch size 1, and at most 256 new tokens.

The prompt requires exactly one severe factual error, preservation of all other facts and the simplification strategy, and JSON fields:

- `distorted_simplification`
- `changed_clean_span`
- `replacement_span`
- `corruption_type`
- `brief_verification`

Exact prompts are versioned in [`meaning_severe_v1.json`](../prompts/meaning_severe_v1.json) and [`meaning_severe_v2.json`](../prompts/meaning_severe_v2.json). V2 additionally rejects paraphrases, omissions, weaker true statements, and declared replacements that do not appear in the output.

## Pilot outcome

Clean-input review:

- 50 primary candidates reviewed;
- 27 accepted directly;
- 23 rejected with reasons;
- 23 accepted backups inserted;
- 50 final clean pairs with unique `canonical_pair_id` and `canonical_original_id`.

Generation audit:

- 20 outputs accepted from the first Qwen pass;
- 11 outputs accepted from the stricter retry;
- 19 outputs manually corrected after both model passes failed semantic audit;
- 50 final severe meaning degradations.

The high correction rate is a pilot result: syntactically valid JSON and a changed sentence do not prove that a controlled contradiction was produced. Human audit remains mandatory until the validators and detector are improved.

Final effective distribution:

| Corruption | Count |
|---|---:|
| entity replacement | 10 |
| number replacement | 9 |
| negation reversal | 9 |
| relation reversal | 7 |
| event replacement | 6 |
| property replacement | 5 |
| date replacement | 4 |

## Reproduction

```bash
python phase6_degraded_corpus/src/select_pilot_inputs.py \
  --config phase6_degraded_corpus/configs/experiments/meaning_en_pilot_v1.json

python phase6_degraded_corpus/src/plan_meaning_corruptions.py \
  --config phase6_degraded_corpus/configs/experiments/meaning_corruption_assignment_v1.json
```

Generated data, review decisions, raw responses, retries, and audit reports live under `phase6_degraded_corpus/runs/meaning_en_pilot_v1/` and are intentionally ignored by Git. Code, configs, prompts, tests, and this methodology are versioned.
