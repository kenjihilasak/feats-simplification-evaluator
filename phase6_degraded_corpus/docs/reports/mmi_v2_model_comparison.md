# MMI v2 model comparison (dev, automatic checks)

## Summary (2026-09-29)

**Status:** dev comparison complete; finalists chosen; blinded heldout audit ready in [`mmi_v2_heldout_review.md`](mmi_v2_heldout_review.md). **STOP** before Gemini (C4), which needs price/budget confirmation (plan §5.1.0), and before the human audit.

| Axis | Macro yield C0 (v1) | C1 Qwen bf16 v2 | C1_greedy | C2 Gemma-3-12B | Finalists | C1 vs C2 (paired) |
|---|---|---|---|---|---|---|
| MEANING (end-to-end) | 39% | 75% | 72% | 76% | C2, C1 | −1 pp, p = 1.0 |
| MEANING (LLM-only) | 36% | 67% | 62% | 68% | — | — |
| MOD | 6% | 85% | 75% | 85% | C1, C2 | −1 pp, p = 1.0 |
| ILLOC (question + directive) | 32% | 88% | 86% | 88% | C2, C1 | 0 pp, p = 1.0 |

- **The v2 pipeline is the main gain:** +36 to +80 pp over C0 on every axis (McNemar p < 0.001). No-op and copy-the-Original failures drop from 7–29% to about 0%.
- **Model choice matters little:** C1 (Qwen) and C2 (Gemma) are statistically indistinguishable on all three axes. C2 is weaker on `assertion_to_hedged` (29% vs 84%: "possibly is" constructions) and stronger on `assertion_to_directive` (97% vs 84%).
- **Sampling matters for MOD:** best-of-4 beats greedy by +9 pp (C1 vs C1_greedy, p = 0.004); elsewhere the difference is small.
- **Weakest MEANING operations:** negation and relation (≈ 60%). Part of this is a checker artifact: the CoLA acceptability model penalizes correct negations ("… is not Mount Olympus"), for every config alike.
- **Cost:** vLLM generates the whole dev split (330 pairs × 4 samples) in about 2 minutes per config on one L40S; C0 (v1 script, 4-bit, one pair at a time) took about 40 minutes.

### LLM judge: not used

Calibrated on the 73 human-labelled outputs of the frozen MEANING pilot: Qwen2.5-7B agrees with humans on 60%, Gemma-3-12B on 55%. Both accept almost everything (27 and 33 false positives). Both are far below the 85% required (§6.2), so the judge is not used for ranking on any axis. MOD/ILLOC have no human labels to calibrate against (1 and 0 cases).

### Blocked

- **C3 (Llama-3.1-8B):** Hugging Face returns 403 "not in the authorized list". Access must be requested on the model page by the account whose token is in `cache/huggingface/token`.
- **C4 (Gemini):** STOP §5.1.0, waiting for price and budget confirmation.

### Deviations from the plan (all applied equally to every config)

1. Clean-input NLI gate: **non-contradiction** (P(contradiction) < 0.5) instead of entailment ≥ 0.5, as agreed. It keeps 24,136 pairs instead of 14,810.
2. Sentence splitter no longer breaks after initials or titles (`Thomas E. Donilon`). It is shared by selection, planning and scoring.
3. Underpowered cells (all three Vikidia cells) are split ⅔ dev / ⅓ heldout, so that Vikidia also reaches the human audit. The macro average includes cells with ≥ 20 rows (MOD-Vikidia has 21).
4. MEANING planner: the factual span must appear in the Original. Number cues exclude days of the month, numbers inside names and range ends. Property cues must be lowercase words. Event spans include their auxiliary (`was born`). No relation flip on already-negated clauses.
5. Checks: acceptability for MOD/ILLOC is `≥ min(τ, clean − δ)` rather than `≥ τ`. Proper nouns are checked by text containment. Copy-the-Original is not applied to MOD (the no-Original-leak check covers it). Numbers with separators count as one token.
6. Few-shot examples are hand-written in Wikipedia style (not taken from WikiAutoEN).
7. Stack: vLLM 0.10.0 + transformers 4.55.4 (driver supports CUDA 12.6). The official Qwen tokenizer was downloaded for C1; C0 keeps the v1 adapter-repo tokenizer to stay faithful to v1.
8. Heldout was generated for the local finalists before the Gemini decision (it costs nothing). If C4 is approved and becomes a finalist, only its heldout is added.
9. In the blinded review, identical outputs of the two finalists for the same pair are shown once (222 cases instead of 290); the decision counts for both.

---

Split: `dev`. Configs: `C0`, `C1`, `C1_greedy`, `C2`. These are **automatic** results used to pick finalists (plan §6.3); the winner is decided by the blinded human audit on `heldout` (§6.4).

`yield` = share of pairs with at least one candidate passing every axis check (n=4 samples; C0 and C1_greedy have n=1, so for them yield = pass@1). Macro averages weigh sources equally and exclude cells with fewer than 20 rows. ILLOC ranking uses question + directive only; hedged is reported separately.

## Finalists per axis

| Axis | Finalist 1 | Finalist 2 | Basis |
|---|---|---|---|
| MEANING | `C2` | `C1` | macro end-to-end yield, then single-edit rate |
| MOD | `C1` | `C2` | macro end-to-end yield, then single-edit rate |
| ILLOC | `C2` | `C1` | macro end-to-end yield, then single-edit rate |

## MEANING — end-to-end (ranking)

| Config | Macro yield | Micro yield | pass@1 (macro) | single-edit (macro) | no-op (macro) | copy-Original (macro) | WikiAutoEN yield [95% CI] (n) | ASSET yield [95% CI] (n) | Wikipedia-Vikidia yield [95% CI] (n) |
|---|---|---|---|---|---|---|---|---|---|
| `C0` | **39%** | 39% | 39% | 56% | 7% | 12% | 33% [21%–49%] (39) | 50% [35%–65%] (38) | 33% [20%–50%] (36) |
| `C1` | **75%** | 75% | 73% | 100% | 0% | 0% | 72% [56%–83%] (39) | 74% [58%–85%] (38) | 81% [65%–90%] (36) |
| `C1_greedy` | **72%** | 72% | 72% | 100% | 0% | 0% | 69% [54%–81%] (39) | 68% [53%–81%] (38) | 78% [62%–88%] (36) |
| `C2` | **76%** | 76% | 76% | 100% | 0% | 0% | 72% [56%–83%] (39) | 82% [67%–91%] (38) | 75% [59%–86%] (36) |

## MEANING — LLM-only (rule number/date rows removed)

| Config | Macro yield | Micro yield | pass@1 (macro) | single-edit (macro) | no-op (macro) | copy-Original (macro) | WikiAutoEN yield [95% CI] (n) | ASSET yield [95% CI] (n) | Wikipedia-Vikidia yield [95% CI] (n) |
|---|---|---|---|---|---|---|---|---|---|
| `C0` | **36%** | 36% | 36% | 55% | 2% | 14% | 37% [22%–54%] (30) | 37% [22%–56%] (27) | 33% [19%–52%] (27) |
| `C1` | **67%** | 67% | 63% | 100% | 0% | 0% | 63% [46%–78%] (30) | 63% [44%–78%] (27) | 74% [55%–87%] (27) |
| `C1_greedy` | **62%** | 62% | 62% | 100% | 0% | 0% | 60% [42%–75%] (30) | 56% [37%–72%] (27) | 70% [52%–84%] (27) |
| `C2` | **68%** | 68% | 68% | 100% | 0% | 0% | 63% [46%–78%] (30) | 74% [55%–87%] (27) | 67% [48%–81%] (27) |

### MEANING — paired comparisons (yield, same pairs)

| A | B | n | only A valid | only B valid | McNemar p | A−B [95% bootstrap CI] |
|---|---|---|---|---|---|---|
| `C0` | `C1` | 113 | 6 | 47 | 5.81e-09 | -36 pp [-47, -26] |
| `C0` | `C1_greedy` | 113 | 7 | 44 | 1.21e-07 | -33 pp [-43, -22] |
| `C0` | `C2` | 113 | 6 | 48 | 3.26e-09 | -37 pp [-48, -27] |
| `C1` | `C1_greedy` | 113 | 4 | 0 | 0.125 | +4 pp [+1, +7] |
| `C1` | `C2` | 113 | 2 | 3 | 1 | -1 pp [-4, +3] |
| `C1_greedy` | `C2` | 113 | 1 | 6 | 0.125 | -4 pp [-9, +0] |

## MOD — end-to-end (ranking)

| Config | Macro yield | Micro yield | pass@1 (macro) | single-edit (macro) | no-op (macro) | copy-Original (macro) | WikiAutoEN yield [95% CI] (n) | ASSET yield [95% CI] (n) | Wikipedia-Vikidia yield [95% CI] (n) |
|---|---|---|---|---|---|---|---|---|---|
| `C0` | **6%** | 6% | 6% | 59% | 1% | 0% | 5% [1%–17%] (40) | 8% [3%–20%] (40) | 5% [1%–23%] (21) |
| `C1` | **85%** | 85% | 75% | 98% | 3% | 0% | 78% [62%–88%] (40) | 92% [80%–97%] (40) | 86% [65%–95%] (21) |
| `C1_greedy` | **75%** | 76% | 75% | 98% | 3% | 0% | 68% [52%–80%] (40) | 90% [77%–96%] (40) | 67% [45%–83%] (21) |
| `C2` | **85%** | 86% | 81% | 98% | 5% | 0% | 88% [74%–95%] (40) | 90% [77%–96%] (40) | 76% [55%–89%] (21) |

### MOD — paired comparisons (yield, same pairs)

| A | B | n | only A valid | only B valid | McNemar p | A−B [95% bootstrap CI] |
|---|---|---|---|---|---|---|
| `C0` | `C1` | 101 | 1 | 81 | 3.43e-23 | -79 pp [-87, -70] |
| `C0` | `C1_greedy` | 101 | 3 | 74 | 1.01e-18 | -70 pp [-80, -60] |
| `C0` | `C2` | 101 | 0 | 81 | 8.27e-25 | -80 pp [-87, -72] |
| `C1` | `C1_greedy` | 101 | 9 | 0 | 0.00391 | +9 pp [+4, +15] |
| `C1` | `C2` | 101 | 7 | 8 | 1 | -1 pp [-9, +6] |
| `C1_greedy` | `C2` | 101 | 4 | 14 | 0.0309 | -10 pp [-18, -2] |

## ILLOC — end-to-end (ranking)

| Config | Macro yield | Micro yield | pass@1 (macro) | single-edit (macro) | no-op (macro) | copy-Original (macro) | WikiAutoEN yield [95% CI] (n) | ASSET yield [95% CI] (n) | Wikipedia-Vikidia yield [95% CI] (n) |
|---|---|---|---|---|---|---|---|---|---|
| `C0` | **32%** | 32% | 32% | 35% | 29% | 9% | 35% [22%–50%] (40) | 28% [16%–43%] (40) | 33% [20%–50%] (36) |
| `C1` | **88%** | 88% | 83% | 47% | 0% | 1% | 89% [72%–96%] (27) | 93% [77%–98%] (27) | 83% [64%–93%] (24) |
| `C1_greedy` | **86%** | 86% | 86% | 47% | 0% | 1% | 81% [63%–92%] (27) | 93% [77%–98%] (27) | 83% [64%–93%] (24) |
| `C2` | **88%** | 88% | 86% | 49% | 0% | 1% | 85% [68%–94%] (27) | 93% [77%–98%] (27) | 88% [69%–96%] (24) |

### ILLOC — paired comparisons (yield, same pairs)

| A | B | n | only A valid | only B valid | McNemar p | A−B [95% bootstrap CI] |
|---|---|---|---|---|---|---|
| `C0` | `C1` | 78 | 0 | 45 | 5.68e-14 | -58 pp [-68, -46] |
| `C0` | `C1_greedy` | 78 | 0 | 43 | 2.27e-13 | -55 pp [-67, -44] |
| `C0` | `C2` | 78 | 0 | 45 | 5.68e-14 | -58 pp [-68, -46] |
| `C1` | `C1_greedy` | 78 | 2 | 0 | 0.5 | +3 pp [+0, +6] |
| `C1` | `C2` | 78 | 5 | 5 | 1 | +0 pp [-8, +8] |
| `C1_greedy` | `C2` | 78 | 3 | 5 | 0.727 | -3 pp [-10, +4] |

## By operation (all sources)

| Operation | `C0` yield (n) | `C1` yield (n) | `C1_greedy` yield (n) | `C2` yield (n) |
|---|---|---|---|---|
| assertion_to_directive | — | 84% (38) | 84% (38) | 97% (38) |
| assertion_to_hedged | 100% (5) | 84% (38) | 82% (38) | 29% (38) |
| assertion_to_question | 100% (32) | 92% (40) | 88% (40) | 80% (40) |
| meaning:date | 47% (19) | 100% (19) | 100% (19) | 100% (19) |
| meaning:entity | 57% (21) | 81% (21) | 71% (21) | 76% (21) |
| meaning:event | 18% (11) | 64% (11) | 64% (11) | 64% (11) |
| meaning:negation | 54% (24) | 58% (24) | 58% (24) | 62% (24) |
| meaning:number | 50% (10) | 100% (10) | 100% (10) | 100% (10) |
| meaning:property | 50% (6) | 83% (6) | 83% (6) | 83% (6) |
| meaning:relation | 0% (22) | 59% (22) | 50% (22) | 64% (22) |
| none | 0% (79) | — | — | — |

## Examples (selected candidate, or first candidate when none passed)

### MEANING

**`C0`**

- ✅ *meaning_entity* (WikiAutoEN)  
  Clean: The Exploration of Neptune started on August 25, 1989, when "Voyager 2" became the first and so-far only spacecraft to visit the planet.  
  Degraded: The Exploration of Neptune started on August 25, 1989, when 'New Horizons' became the first and so-far only spacecraft to visit the planet.
- ✅ *meaning_date* (ASSET)  
  Clean: George Bernard Shaw was an Irish playwright. He lived from 26 July 1856 to 2 November 1950.  
  Degraded: George Bernard Shaw was an Irish playwright. He lived from 26 July 1856 to 2 November 1900.
- ❌ *meaning_date* (WikiAutoEN)  
  Clean: David Thewlis (born 20 March 1963) is an English actor.  
  Degraded: David Thewlis (born 1963), is an English actor. — failed: contradicts_original, fluency_kept, one_edit_block
- ❌ *meaning_entity* (Wikipedia-Vikidia)  
  Clean: In ancient Greece, Aphrodite was the goddess of love and beauty.  
  Degraded: In ancient Greece, Ares was the god of love and beauty. — failed: one_edit_block

**`C1`**

- ✅ *meaning_entity* (WikiAutoEN)  
  Clean: The Exploration of Neptune started on August 25, 1989, when "Voyager 2" became the first and so-far only spacecraft to visit the planet.  
  Degraded: The Exploration of Neptune started on August 25, 1989, when "Cassini 2" became the first and so-far only spacecraft to visit the planet.
- ✅ *meaning_date* (ASSET)  
  Clean: George Bernard Shaw was an Irish playwright. He lived from 26 July 1856 to 2 November 1950.  
  Degraded: George Bernard Shaw was an Irish playwright. He lived from 26 July 1856 to 2 November 1925.
- ❌ *meaning_negation* (WikiAutoEN)  
  Clean: The Grand Duchy of Baden (German: "Großherzogtum Baden") was a historical state in the southwest of Germany, on the east bank of the Rhine.  
  Degraded: The Grand Duchy of Baden (German: "Großherzogtum Baden") was not a historical state in the southwest of Germany, on the east bank of the Rhine. — failed: fluency_kept
- ❌ *meaning_negation* (ASSET)  
  Clean: This is a list of victims of Nazism who had successes.  
  Degraded: This is a list of victims of Nazism who had not successes. — failed: fluency_kept

**`C1_greedy`**

- ✅ *meaning_date* (ASSET)  
  Clean: George Bernard Shaw was an Irish playwright. He lived from 26 July 1856 to 2 November 1950.  
  Degraded: George Bernard Shaw was an Irish playwright. He lived from 26 July 1856 to 2 November 1925.
- ✅ *meaning_date* (WikiAutoEN)  
  Clean: David Thewlis (born 20 March 1963) is an English actor.  
  Degraded: David Thewlis (born 20 March 1949) is an English actor.
- ❌ *meaning_entity* (WikiAutoEN)  
  Clean: The Exploration of Neptune started on August 25, 1989, when "Voyager 2" became the first and so-far only spacecraft to visit the planet.  
  Degraded: The Exploration of Neptune started on August 25, 1989, when "Mariner 11 2" became the first and so-far only spacecraft to visit the planet. — failed: contradicts_original
- ❌ *meaning_negation* (WikiAutoEN)  
  Clean: The Grand Duchy of Baden (German: "Großherzogtum Baden") was a historical state in the southwest of Germany, on the east bank of the Rhine.  
  Degraded: The Grand Duchy of Baden (German: "Großherzogtum Baden") was not a historical state in the southwest of Germany, on the east bank of the Rhine. — failed: fluency_kept

**`C2`**

- ✅ *meaning_entity* (WikiAutoEN)  
  Clean: The Exploration of Neptune started on August 25, 1989, when "Voyager 2" became the first and so-far only spacecraft to visit the planet.  
  Degraded: The Exploration of Neptune started on August 25, 1989, when "New Horizons 2" became the first and so-far only spacecraft to visit the planet.
- ✅ *meaning_date* (ASSET)  
  Clean: George Bernard Shaw was an Irish playwright. He lived from 26 July 1856 to 2 November 1950.  
  Degraded: George Bernard Shaw was an Irish playwright. He lived from 26 July 1856 to 2 November 1925.
- ❌ *meaning_negation* (WikiAutoEN)  
  Clean: The Grand Duchy of Baden (German: "Großherzogtum Baden") was a historical state in the southwest of Germany, on the east bank of the Rhine.  
  Degraded: The Grand Duchy of Baden (German: "Großherzogtum Baden") was not a historical state in the southwest of Germany, on the east bank of the Rhine. — failed: fluency_kept
- ❌ *meaning_entity* (ASSET)  
  Clean: Upper Austria is the fourth-largest Austrian state by land area. Its area is 11,980 km ². It has 1.3 million inhabitants. It is the third-largest by population.  
  Degraded: Upper Austria is the fourth-largest Austrian state by land area. Its area is 11,980 km ². It has 1.3 million inhabitants. Lower Austria is the third-largest by population. — failed: fluency_kept

### MOD

**`C0`**

- ✅ *recombine_split* (ASSET)  
  Clean: They use their tail to support their weight. That is why they are able deliver kicks with their powerful hind legs.  
  Degraded: Using their tail to support their weight, they deliver kicks with their powerful hind legs.
- ✅ *recombine_split* (WikiAutoEN)  
  Clean: The province has 12 districts. There are 21 municipalities.  
  Degraded: The province is made up of 12 districts and 21 municipalities.
- ❌ *recombine_split* (ASSET)  
  Clean: He tells the story of the Holy Grail. In this story he reveals himself as Lohengrin. Lohengrin is a Knight of the Holy Grail and the son of King Parsifal.  
  Degraded: He tells the story of the Holy Grail, and reveals himself as Lohengrin, who is a Knight of the Holy Grail and the son of King Parsifal. — failed: sentence_count_minus_one
- ❌ *recombine_split* (WikiAutoEN)  
  Clean: In June 2017 the app added "Snap Map". Snap Map is a feature that broadcasts the user's location on a map. This caused concerns over privacy and safety.  
  Degraded: The June 2017 release of 'Snap Map', a feature that broadcasts the user's location on a map, caused concerns over privacy and safety. This feature is called Snap Map and it was added in June 2017. — failed: no_original_leak, numbers_identical

**`C1`**

- ✅ *recombine_split* (ASSET)  
  Clean: He tells the story of the Holy Grail. In this story he reveals himself as Lohengrin. Lohengrin is a Knight of the Holy Grail and the son of King Parsifal.  
  Degraded: He tells the story of the Holy Grail. In this story he reveals himself as Lohengrin, a Knight of the Holy Grail and the son of King Parsifal.
- ✅ *recombine_split* (WikiAutoEN)  
  Clean: In June 2017 the app added "Snap Map". Snap Map is a feature that broadcasts the user's location on a map. This caused concerns over privacy and safety.  
  Degraded: In June 2017 the app added "Snap Map". Snap Map, a feature that broadcasts the user's location on a map, caused concerns over privacy and safety.
- ❌ *recombine_split* (WikiAutoEN)  
  Clean: Some jugglers use more dangerous-looking objects such as knives, fire torches and chainsaws. Some jugglers use bouncing objects.  
  Degraded: Some jugglers use more dangerous-looking objects such as knives, fire torches and chainsaws, which can also include bouncing objects. — failed: acceptable, entails_both_ways
- ❌ *recombine_split* (Wikipedia-Vikidia)  
  Clean: In 1687, EnglishmathematicianIsaac Newton wrote the Principia. In this book, he wrote about the inverse-square law of gravitation.  
  Degraded: In 1687, English mathematician Isaac Newton wrote the Principia, in which he wrote about the inverse-square law of gravitation. — failed: content_lemmas_within_2, no_original_leak, proper_nouns_kept

**`C1_greedy`**

- ✅ *recombine_split* (ASSET)  
  Clean: He tells the story of the Holy Grail. In this story he reveals himself as Lohengrin. Lohengrin is a Knight of the Holy Grail and the son of King Parsifal.  
  Degraded: He tells the story of the Holy Grail. In this story he reveals himself as Lohengrin, a Knight of the Holy Grail and the son of King Parsifal.
- ✅ *recombine_split* (WikiAutoEN)  
  Clean: In June 2017 the app added "Snap Map". Snap Map is a feature that broadcasts the user's location on a map. This caused concerns over privacy and safety.  
  Degraded: In June 2017 the app added "Snap Map". Snap Map, a feature that broadcasts the user's location on a map, caused concerns over privacy and safety.
- ❌ *recombine_split* (WikiAutoEN)  
  Clean: Some jugglers use more dangerous-looking objects such as knives, fire torches and chainsaws. Some jugglers use bouncing objects.  
  Degraded: Some jugglers use more dangerous-looking objects such as knives, fire torches and chainsaws, which can also include bouncing objects. — failed: acceptable, entails_both_ways
- ❌ *recombine_split* (Wikipedia-Vikidia)  
  Clean: Neptune is a planet in the Solar System. It is the eighth-closest and farthest planet from the Sun.  
  Degraded: Neptune is a planet in the Solar System, which is the eighth-closest and farthest planet from the Sun. — failed: acceptable

**`C2`**

- ✅ *recombine_split* (ASSET)  
  Clean: He tells the story of the Holy Grail. In this story he reveals himself as Lohengrin. Lohengrin is a Knight of the Holy Grail and the son of King Parsifal.  
  Degraded: He tells the story of the Holy Grail. In this story he reveals himself as Lohengrin, who is a Knight of the Holy Grail and the son of King Parsifal.
- ✅ *recombine_split* (WikiAutoEN)  
  Clean: In June 2017 the app added "Snap Map". Snap Map is a feature that broadcasts the user's location on a map. This caused concerns over privacy and safety.  
  Degraded: In June 2017 the app added "Snap Map". Snap Map is a feature that broadcasts the user's location on a map, which caused concerns over privacy and safety.
- ❌ *recombine_split* (WikiAutoEN)  
  Clean: The ẓuhr prayer ( "" ], "noon prayer") is the prayer offered at midday. Practicing Muslims make this prayer daily. It is the second of the five daily prayers ("salat").  
  Degraded: The ẓuhr prayer ( "" ], "noon prayer") is the prayer offered at midday. Practicing Muslims make this prayer daily, which is the second of the five daily prayers ('salat'). — failed: acceptable
- ❌ *recombine_split* (Wikipedia-Vikidia)  
  Clean: In 1687, EnglishmathematicianIsaac Newton wrote the Principia. In this book, he wrote about the inverse-square law of gravitation.  
  Degraded: In 1687, English mathematician Isaac Newton wrote the Principia, in which he wrote about the inverse-square law of gravitation. — failed: content_lemmas_within_2, no_original_leak, proper_nouns_kept

### ILLOC

**`C0`**

- ✅ *assertion_to_directive* (WikiAutoEN)  
  Clean: A headset is a headphone with a microphone.  
  Degraded: Is a headset a combination of a headphone with a microphone?
- ✅ *assertion_to_question* (WikiAutoEN)  
  Clean: Almost all mammal species give birth to live young.  
  Degraded: Almost all mammal species might give birth to live young.
- ❌ *assertion_to_hedged* (WikiAutoEN)  
  Clean: The explosives are also dangerous for the fishermen, causing accidents and injuries.  
  Degraded: The explosives are also dangerous for the fishermen, but accidents and injuries do not occur. — failed: deleted_only_auxiliaries_or_final_punct, inserted_in_lexicon
- ❌ *assertion_to_directive* (ASSET)  
  Clean: Earth is the only place where we know life exists.  
  Degraded: Earth is the only place where life exists. — failed: deleted_only_auxiliaries_or_final_punct, inserted_in_lexicon

**`C1`**

- ✅ *assertion_to_directive* (WikiAutoEN)  
  Clean: A headset is a headphone with a microphone.  
  Degraded: Remember that a headset is a headphone with a microphone.
- ✅ *assertion_to_question* (WikiAutoEN)  
  Clean: Almost all mammal species give birth to live young.  
  Degraded: Do almost all mammal species give birth to live young?
- ❌ *assertion_to_hedged* (WikiAutoEN)  
  Clean: The explosives are also dangerous for the fishermen, causing accidents and injuries.  
  Degraded: The explosives might be dangerous for the fishermen, causing accidents and injuries. — failed: deleted_only_auxiliaries_or_final_punct
- ❌ *assertion_to_directive* (ASSET)  
  Clean: It is really famous for the harvest of kiwifruit.  
  Degraded: Remember that it is really famous for the harvest of kiwifruit. — failed: acceptable

**`C1_greedy`**

- ✅ *assertion_to_directive* (WikiAutoEN)  
  Clean: A headset is a headphone with a microphone.  
  Degraded: Remember that a headset is a headphone with a microphone.
- ✅ *assertion_to_question* (WikiAutoEN)  
  Clean: Almost all mammal species give birth to live young.  
  Degraded: Do almost all mammal species give birth to live young?
- ❌ *assertion_to_hedged* (WikiAutoEN)  
  Clean: The explosives are also dangerous for the fishermen, causing accidents and injuries.  
  Degraded: The explosives might be dangerous for the fishermen, causing accidents and injuries. — failed: deleted_only_auxiliaries_or_final_punct
- ❌ *assertion_to_question* (WikiAutoEN)  
  Clean: Garden forks were made of wood, but now most are made of steel.  
  Degraded: Were garden forks made of wood, but now are most made of steel? — failed: acceptable

**`C2`**

- ✅ *assertion_to_directive* (WikiAutoEN)  
  Clean: A headset is a headphone with a microphone.  
  Degraded: Note that a headset is a headphone with a microphone.
- ✅ *assertion_to_hedged* (WikiAutoEN)  
  Clean: The explosives are also dangerous for the fishermen, causing accidents and injuries.  
  Degraded: The explosives are possibly also dangerous for the fishermen, causing accidents and injuries.
- ❌ *assertion_to_hedged* (Wikipedia-Vikidia)  
  Clean: A forest is an area of land with many trees.  
  Degraded: A forest possibly is an area of land with many trees. — failed: acceptable
- ❌ *assertion_to_hedged* (WikiAutoEN)  
  Clean: The endometrium is the innermost membrane of the uterus.  
  Degraded: The endometrium possibly is the innermost membrane of the uterus. — failed: acceptable


## Heldout human audit results

Cases: 222; unmarked or multiple marks: 0. Unsure counts as not valid.

### ILLOC

| Config | Macro valid | WikiAutoEN (n) | ASSET (n) | Wikipedia-Vikidia (n) | Unsure | Auto–human agreement |
|---|---|---|---|---|---|---|
| `C1` | **90%** | 93% (14) | 93% (14) | 83% (12) | 0 | 85% |
| `C2` | **89%** | 93% (14) | 100% (14) | 75% (12) | 0 | 90% |

Decision: **no automatic winner** — equivalent: apply the cost / local / per-source tie-break (§6.4.3).

### MEANING

| Config | Macro valid | WikiAutoEN (n) | ASSET (n) | Wikipedia-Vikidia (n) | Unsure | Auto–human agreement |
|---|---|---|---|---|---|---|
| `C1` | **84%** | 80% (20) | 82% (17) | 88% (17) | 0 | 69% |
| `C2` | **82%** | 75% (20) | 82% (17) | 88% (17) | 0 | 67% |

Decision: **no automatic winner** — no finalist reaches 85%: revise and repeat (§6.4.1).

### MOD

| Config | Macro valid | WikiAutoEN (n) | ASSET (n) | Wikipedia-Vikidia (n) | Unsure | Auto–human agreement |
|---|---|---|---|---|---|---|
| `C1` | **79%** | 85% (20) | 80% (20) | 73% (11) | 5 | 76% |
| `C2` | **92%** | 95% (20) | 100% (20) | 82% (11) | 1 | 88% |

Decision: **C2** — only eligible finalist (§6.4.2).


## Final configuration per axis (2026-09-30)

Reviewer instruction: count **Unsure as Valid**. Macro human valid rate on heldout:

| Axis | C1 (Qwen2.5-7B, v2) | C2 (Gemma-3-12B, v2) | Paired (McNemar) | Decision |
|---|---|---|---|---|
| MEANING | 84% | 82% | p = 1.0 | **C1, provisional**: neither reaches 85%; fix negation (rule-based) and a/an agreement, then re-audit a fresh heldout sample |
| MOD | 89% | **95%** | p = 0.38 | **C2**: both eligible and equivalent; tie-break §6.4.3(a), cost per valid output (same GPU time, more valid outputs) |
| ILLOC | **90%** | 89% | p = 1.0 | **C1**: equivalent; tie-break §6.4.3(a), smaller model (7B vs 12B) for the same valid rate; also far better on `hedged` in dev (84% vs 29%) |

## MEANING v2.1 re-audit (2026-09-30)

Changes: rule-based negation, a/an agreement. Fresh blinded heldout of 57 cases, C1 only ([`mmi_v21_meaning_heldout_review.md`](mmi_v21_meaning_heldout_review.md)): 20 new WikiAutoEN + 20 new ASSET pairs, plus the 18 Vikidia heldout pairs reused with new outputs (Vikidia has no unused pairs). Unsure counts as valid; case H026 has two marks and counts as not valid.

| Source | Valid |
|---|---|
| WikiAutoEN | 18/20 (90%) |
| ASSET | 15/20 (75%) |
| Wikipedia-Vikidia | 17/17 (100%, reused pairs) |
| **Macro** | **88%** (micro 50/57) |

**Decision: C1 (Qwen2.5-7B, v2.1) is approved for MEANING** (≥ 85%). Residual errors: entity/relation swaps that produce hybrids or internal inconsistencies, and one plural "A Chronicles". Known follow-up: require the predicate around a swapped entity to be supported by the Original (case "Second Battle of Lille").

### Final configuration

| Axis | Config |
|---|---|
| MEANING | C1: Qwen2.5-7B bf16, v2.1 (rule-based number/date/negation, LLM for the rest) |
| MOD | C2: Gemma-3-12B bf16, v2 |
| ILLOC | C1: Qwen2.5-7B bf16, v2 (question + directive; hedged pending the FEATS definition) |
