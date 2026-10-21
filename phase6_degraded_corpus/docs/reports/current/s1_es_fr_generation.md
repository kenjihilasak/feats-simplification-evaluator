# S1 Spanish and French rounds: generation

**Date:** 21 October 2026. **Status:** both review packages are built and blinded; human review has not started.

## Decisions (team, 21 October 2026)

- **Spanish:** iDEM only. Wikipedia-Vikidia stays excluded, as decided on 1 October.
- **French:** WikiLargeFR and CLEAR. WikiLargeFR is machine-translated from English WikiLarge.
- **Scope:** the full pipeline, matching English: rules, LLM edits, automatic checks, blinded S1 packages, a localized interface and guidelines.

## What differs from English

| Component | English | Spanish / French |
|---|---|---|
| Phase 2b input | target-simple variant | base variant: target-simple keeps only 49 iDEM pairs, and only 4 French EXPL sites |
| Rule gating by Phase 3a strategy | yes | French yes; Spanish no (iDEM has 12 single-strategy candidates, none OMIT or EXPL) |
| NLI | DeBERTa-v3-large MNLI (English) | mDeBERTa-v3-base XNLI multilingual, revision `b5113eb` |
| Acceptability | CoLA classifier, τ and δ from a manual sample | SLOR with Qwen2.5-7B-Instruct and wordfreq unigrams (no Spanish or French CoLA model exists); τ = 10th percentile of clean texts, δ = median − τ, computed over all candidates |
| spaCy | `en_core_web_sm` | `es_core_news_sm`, `fr_core_news_sm` 3.8.0 |
| Rule text output | detokenized tokens | the simplification's own string is edited, so pre-tokenized CLEAR spacing is kept |
| LLM prompts | `prompts/v3` | `prompts/v3_es`, `prompts/v3_fr`: same instructions, native few-shot examples |
| Imperative check | PTB tag `VB` | the sentence opens with its root verb (parsed with a lowercased first letter; French also needs an imperative ending) and the deontic modal is gone. The small models mis-tag sentence-initial imperatives |
| Controls | 15 identical + 15 known-valid | identical pairs only (10% of items): no validated degradation exists yet in these languages |
| Displayed text | as generated | uniform spacing for every version, so typography cannot reveal the degraded one |

Language resources (articles, gloss markers, hedges, negation, abbreviations, imperative cues) are in `src/common/languages.py`. English code paths are unchanged, and all 54 existing English tests still pass.

## Calibration

| | Spanish | French |
|---|---:|---:|
| Scored clean candidates | 212 | 7,160 |
| τ (SLOR) | 0.374 | −0.392 |
| δ | 1.607 | 2.442 |
| Dropped: acceptability below τ | 22 | 716 |
| Dropped: clean contradicts original | 3 | 436 |

## Allocation and yield

One task per original, scarcest first. "Allocated" counts candidates sent to generation; "items" counts what passed every check and entered S1.

| Axis | Spanish allocated → items | French allocated → items |
|---|---|---|
| OMIT | 4 pairs → 4 | 15 groups + 200 pairs → 60 pairs (no graded group passed) |
| SYN | 8 pairs → 4 | 93 groups + 150 pairs → 29 rank-3 + 31 pairs |
| EXPL | 1 pair → 1 | 163 pairs → 60 |
| MOD | 36 groups → 24 rank-3 + 2 pairs | 300 groups → 60 rank-3 (145 valid) |
| ILLOC | 138 → 60 (all hedges) | 240 → 60 (118 hedges, 14 imperatives valid) |
| **Total** | **95 items + 10 controls** | **300 items + 30 controls** |

## Known limits

- **Spanish rule axes are nearly empty** (9 items). iDEM rewrites sentences heavily, so token-aligned OMIT/SYN/EXPL sites rarely exist. Spanish validates MOD and ILLOC; the rule axes need another Spanish source or a different generator.
- **No Spanish imperative passed** (0 of 16). iDEM's modals rarely address the reader ("un país puede tener …").
- **French WikiLargeFR is noisy machine translation**; reviewers will see some awkward originals. The acceptability gate removes the worst.
- **LLM side edits:** Gemma occasionally fixes punctuation in the clean text while fronting a phrase, and Qwen produced "puede que suspendería". The side-effect question in S1 is meant to catch both.
- **SLOR thresholds** come from the clean distribution, not from a manual sample as in English.
- **No shortcut audit yet** for these rounds.
- **No Gemini suggestions yet**: the English prefill hit the free-tier quota.

## Files

- Configs: `configs/experiments/s1_{es,fr}_v1.json`, `s1_{es,fr}_v1_generation.json`
- Pipeline: `jobs/submit_s1_multilingual_gpu.sh es|fr` (resumable), `src/selection/select_multilingual_pools.py`, `src/generation/generate_s1_rules.py`
- Packages: `runs/annotation_{es,fr}_v1/` (`s1_items.jsonl`, `s1_controls.jsonl`, hidden `s1_key.json`, `s1_controls_key.json`), built by `src/annotation/build_s1_multilingual.py`
- Guidelines: `docs/methodology/s1_guidelines_{es,fr}.md`; web: `/s1/guidelines?lang=es|fr`
