# SimpEval-2022 S1 items (English)

## Purpose

Per-axis human judgements on real system outputs, used to evaluate the FEATS scorers outside the synthetic
degradation corpus. SimpEval-2022 (60 originals, human ratings for six systems) is used for evaluation only and stays
out of every training and selection pool.

## Rules

1. **Versions per original (3).** The better human simplification (higher mean of `rating_1..3` between
   "Human 1 Writing" and "Human 2 Writing"; tie -> Human 1), "GPT-3-few-shot" and "Muss". The system name and mean
   rating of each are kept in the key.
2. **Strategy classification.** The 180 pairs (original -> version) are written in the Phase 2b consolidated schema
   (`id` = `canonical_pair_id` = `pair:en:simpeval2022:<original_id>:<system-slug>`) and classified by the four
   Phase 3a models (xlmr_large_focal, multilingual_e5_large_bce, qwen2p5_7b_pairwise_qlora,
   gemma3_12b_pairwise_qlora) with their pinned revisions and thresholds
   (experiment `phase3a_strategy_detection/configs/experiments/simpeval2022_s1_v1.json`).
3. **Confirmed strategies.** A strategy is confirmed for a pair when at least 2 of the 4 models predict it and Gemma
   (the most reliable classifier) is one of them; labels are non-exclusive, so a pair may keep several (as `build_strategy_consensus.py`).
4. **Item axis per original: the human version decides** (revised 2026-11-06). The best-rated human simplification
   is the reference; the two system outputs play the part of the degraded versions, except that nothing guarantees
   they are worse, which is what the reviewers' ranking measures. Candidate axes are the strategies confirmed in the
   human version, COMP and SYNT included (OMIT, SYN, MOD, EXPL, COMP, SYNT). Each original gives one item, so the
   choice balances the axes: the candidate whose axis has fewer items so far (originals in id order); ties go to the
   one most models predict, then to the one the system versions share least, then to the order OMIT, SYN, MOD,
   EXPL, COMP, SYNT. Result: MOD 14, SYN 13, COMP 11, OMIT 10, SYNT 8, EXPL 3, MEANING 1. Earlier rules, dropped: the
   axis confirmed in most of the three versions (it favoured what all systems share, SYN in 149 of 180 pairs, over
   what the reference did), then the human strategy with most votes (MOD won 26 of 60 items).
   Otherwise: ILLOC if the human simplification hosts a direct act
   (`illoc_host`, lang en); else MEANING and FLUENCY alternately, in the order of a stable hash of the original id
   (seed 20261105), so the two fallback axes stay balanced. Counts per axis and per reason are in `report.json`.
5. **Items.** One rank-3 item per original, case ids EN-SE001..EN-SE060 in original-id order, built with the S1
   `item()`/`displayed()` helpers: versions under X/Y/Z in a stable shuffled order, uniform spacing, items shuffled
   with a stable seed. Public items carry only `case_id, language, axis, format, original, versions`. The key records
   `source` ("simpeval_2022"), `original_id`, system, mean human rating and pair id per label, the confirmed
   strategies with supporting models per label, the human label, the chosen axis and the reason.

## How to run

```bash
# 1. Input (CPU; already done once, deterministic)
PYTHONPATH=$PWD .venv-phase6-vllm/bin/python -m phase6_degraded_corpus.src.annotation.build_simpeval_s1_items prepare
# 2. Four classifiers (GPU l40s)
sbatch phase3a_strategy_detection/jobs/submit_simpeval2022_s1_gpu.sh
# 3. Items, key, report (CPU) -> phase6_degraded_corpus/runs/simpeval2022_s1_v1/{items.jsonl,key.json,report.json}
PYTHONPATH=$PWD .venv-phase6-vllm/bin/python -m phase6_degraded_corpus.src.annotation.build_simpeval_s1_items build
# Tests
PYTHONPATH=$PWD .venv-phase6-vllm/bin/python -m pytest -q phase6_degraded_corpus/tests/test_build_simpeval_s1_items.py
```
