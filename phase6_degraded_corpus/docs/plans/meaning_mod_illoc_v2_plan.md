# Plan: MEANING, MOD, ILLOC degradation v2 — per-source model comparison

Execution plan. Experiment id: **`mmi_en_v2`**. Language: English only.

## 0. Context and hard constraints

The v1 pilot (Qwen2.5-7B, 4-bit NF4, greedy, zero-shot prompts) produced unusable degradations: see [`../reports/pilot_random_review_assistant_audit.md`](../reports/pilot_random_review_assistant_audit.md). Failure modes: identical/format-only outputs, output copying the Original (MOD 10/50, ILLOC 5/50), edits in the wrong axis, multiple edits, broken Simplified inputs, and false cues (`May` in dates).

This plan fixes source selection and generation for **MEANING, MOD, ILLOC only**, compares **5 generation configs**, and reports every result **separately for the three English sources**: `WikiAutoEN`, `ASSET`, `Wikipedia-Vikidia`.

**Purpose: pipeline selection, not corpus production.** C0–C4 run on the same `dev` pairs. Automatic metrics pick two finalists per axis, and a blinded human audit on `heldout` picks the winner per axis. The winner may differ between MEANING, MOD and ILLOC. Full-pool generation happens only afterwards, in a separate plan.

Hard constraints:

1. Do **not** modify or regenerate: `runs/meaning_en_pilot_v1/`, `runs/multi_axis_en_v1/`, any `prompts/*_v1.json`, `prompts/meaning_severe_v*.json`, `prompts/retry_v2/`. New prompts are new files.
2. All run products go under `phase6_degraded_corpus/runs/mmi_en_v2/` (Git-ignored). Code, configs, prompts, jobs, tests, docs are committed.
3. **ASSET is usable, except the originals of the evaluation corpora.** ASSET has 2,359 originals (2,000 from the official validation split + 359 from the official test split). AssetAnn is the annotated subset of the official **test** originals. Other reserved corpora (Simplicity-DA, Human-Likert, SimpEval) may also rate outputs on ASSET/TurkCorpus test originals. Rules:
   - **Done (2026-09-30):** `src/selection/freeze_evaluation_originals.py` froze Simplicity-DA, Human-Likert, AssetAnn, SimpEval-2022 and the official `asset.test.orig`, with commits and SHA-256 recorded in `runs/mmi_en_v2/pools/evaluation_sources_manifest.json`. Do not match on ids: MultiSim re-splits ASSET, so the upstream split label cannot be trusted. (The 288 Phase 2b ASSET pairs that match are exactly the MultiSim `test` split.)
   - **Required fix to the matching key.** The current key (collapse whitespace + casefold) treats tokenized and detokenized copies as different sentences (`built later .` vs `built later.`): the 803 entries are only **419 distinct sentences**. Replace it with a **strong key**: NFKC → casefold → PTB brackets to `()` → keep only `\w` characters without `_`. Report both counts. On the current input, the strong key finds 291 reserved pairs (288 ASSET + 3 WikiAutoEN), one more than the weak key.
   - **Near duplicates.** Also exclude any pair whose original has word-set Jaccard ≥ 0.8 with a reserved original (same Wikipedia sentence, another revision). On the current input this is about 9 WikiAutoEN pairs. List them in the pool report with their best match.
   - Any excluded pair gets `"usage": "reserved_evaluation"` and `reserved_match: "exact" | "near"`, and is kept out of every pool, split and future training set.
   - All other ASSET pairs are used normally, for dev/held-out and later for training.
   - Add a test that pool selection excludes a reserved original, and that the materializer raises on `usage == "reserved_evaluation"`.
4. Reproducibility conventions as in v1: `stable_key(seed, ...)` from `src/common/contracts.py` for all sampling; record model id + revision, tokenizer revision, prompt id + sha256, decoding params, seed, library versions in every output row.
5. Split/exclude by `canonical_original_id`. One original appears in at most one cell (axis × source × split).
6. Stop and report to the user at each **STOP** marker.

## 1. Source pools per axis and source

Input: `phase2b_consolidation/runs/2026-09-29_target_simple_textrepair_v1/data/en/feats_consolidated.jsonl`, the text-repaired variant defined in [`phase2b_consolidation/docs/text_repair_plan.md`](../../../phase2b_consolidation/docs/text_repair_plan.md) (same 73,586 pairs and IDs as `runs/2026-09-02_target_simple_v1`). **Prerequisite:** that plan must be executed and its audit accepted first. The binding input contract is [`../inputs.md`](../inputs.md): read the fields listed there, and skip rows with `repaired_duplicate_of`. Do **not** require the Phase 3a strict single-strategy set. `source_strategy` is metadata only (`null` when absent), taken from the text-repaired Phase 3a candidate set if it is validated, otherwise from `2026-08-31_single_strategy_gemma_anchored_strict_v1`, and recorded in the pool report. This plan does not wait for the Phase 3a re-run.

**Scope of this decision:** admitting multi-strategy pairs applies to this pipeline-selection experiment. Each generated row still has exactly one `target_axis`. Whether the final training corpus also admits multi-strategy pairs (v1 policy: single-strategy only) is decided before materialization. Record the **real** Phase 3a strategy count so that either policy can be applied later without re-selecting. It must come from the full Phase 3a predictions (`phase3a_strategy_detection/runs/2026-08-20_three_models_phase2b_full_v1/models/<model>/predictions/en/`, or the text-repaired effective run once validated), **not** from membership in the strict candidate set. Per row, store `phase3a_predicted_codes` (dict model → list of codes), `gemma_strategy_count` (the anchor model's count), and `strict_single_strategy_candidate: bool`. `source_strategy_count` from candidate-set membership (0/1) is wrong: 0 means "not a strict candidate", which can mean 0, 2 or more strategies.

New module: `src/selection/select_mmi_pools.py`, config `configs/experiments/mmi_en_v2_pools.json`.

### 1.1 Common preprocessing and filters (all axes)

| Step | Rule |
|---|---|
| Single corpus | exactly one entry in `corpora`; corpus ∈ {WikiAutoEN, ASSET, Wikipedia-Vikidia} |
| Reserved originals | exclude originals listed in `reserved_original_texts.txt` (§0, item 3) |
| Glue repair | Done upstream by the Phase 2b text-repair variant: `simple`/`original` are already repaired, and `simple_raw`/`text_repairs` hold the provenance. Copy `text_repaired` into each Phase 6 row as `glue_repaired`. Do **not** reimplement the repair in Phase 6. |
| Length | original 8–45 tokens (`TOKEN` regex of `select_multi_axis_inputs.py`) |
| Non-identical | normalized original ≠ normalized simple |
| Markup | reject `File:`, `Category:`, `Template:`, `Image:` prefixes |
| ASSET dedup | ASSET has several references per original: keep one pair per `canonical_original_id`, chosen by `stable_key(seed, pair_id)` |
| Clean-input fluency | acceptability classifier (see §4.2) on the repaired Simplified ≥ threshold `tau_accept` |
| Clean-input meaning | NLI (§4.2): P(entailment \| premise=original, hypothesis=simple) ≥ 0.5 (MEANING and MOD only; for ILLOC also apply — injected changes need a meaning-preserving clean) |

Word-level alignment: `difflib.SequenceMatcher(None, orig_tokens_lower, simple_tokens_lower, autojunk=False)`; `overlap = ratio()`, `len_ratio = len(simple)/len(orig)`, `edit_blocks = non-equal opcodes`.

### 1.2 Axis-specific pools

| Axis | Structural rule | Pool before NLI/acceptability: WikiAutoEN / ASSET / Vikidia |
|---|---|---|
| MEANING | overlap ≥ 0.4, len_ratio 0.5–1.6, edit_blocks ≤ 4, **and** Simplified has ≥ 1 typed cue: number, date, named entity (not sentence-initial), or negation | 25,341 / 857 / 122 |
| MOD | Simplified has more sentences than Original, overlap ≥ 0.6, len_ratio 0.8–1.4 | 5,622 / 390 / **8** |
| ILLOC | overlap ≥ 0.4, len_ratio 0.5–1.6, edit_blocks ≤ 4, Simplified is declarative (ends with `.`, contains no `?`) | 28,796 / 1,171 / 151 |

The counts were computed before the ASSET dedup and the NLI/acceptability gates. Recompute them and write them to `runs/mmi_en_v2/pools/pool_report.json`, with counts per filter step per cell.

**Vikidia MOD fallback:** if fewer than 40 pairs remain, relax that cell only to overlap ≥ 0.4 and len_ratio 0.5–1.6. If it is still under 40, use everything available and mark the cell `underpowered: true` in all reports. Do not borrow pairs from other sources.

### 1.3 Pair allocation

Assign each pair to at most one axis, **per source**, in two passes:
1. **Split quota first.** Each cell needs `dev + heldout = 60` pairs. Fill all cells of a source together, taking first the pairs eligible for the fewest axes. Among cells that are still short, a pair goes to the cell with the largest remaining deficit relative to its eligible supply; break ties with `stable_key`. This prevents a large cell (MEANING) from draining a small one (ILLOC) in small sources: in v1 of this step, the fixed order MOD → MEANING → ILLOC left ILLOC-Vikidia with 22 pairs and ILLOC-ASSET with 68, while MEANING-Vikidia kept 101.
2. **Remainder.** The remaining eligible pairs go to the pools in the order MOD → MEANING → ILLOC. They are used only by the later full-generation plan.

A cell is `underpowered` only if it is still below 60 after pass 1. Output: `runs/mmi_en_v2/pools/{axis}_{source}.jsonl`, with `allocation_pass: 1 | 2` per row.

## 2. Dev and held-out sets

Module `src/selection/sample_mmi_devsets.py`. There are 9 cells (3 axes × 3 sources). For each cell:

| Split | Size | Use |
|---|---|---|
| `dev` | 40 | automatic metrics + judge, all configs |
| `gemini_pilot` | the first 10 of `dev` by stable key | Gemini cost/quality pilot (§5, config C4) |
| `heldout` | 20 | blinded human audit of the two best configs |

**Order:** the clean-input quality gates of §1.1 (acceptability and NLI) are applied to the pools **before** allocation and sampling. Splits sampled before the gates must be discarded and re-sampled; nothing has been generated on them, so this costs nothing. Dev and held-out are disjoint by `canonical_original_id`. When a cell has fewer than 60 pairs, fill `dev` first and then `heldout` with whatever remains. Stratify MEANING dev by cue type (number/date/entity/negation) as evenly as the cell allows.

MEANING also gets an extra `pilot50` set: the 50 frozen inputs from `runs/meaning_en_pilot_v1/selection/accepted_50.jsonl`. It is used only for the comparison with human-accepted outputs in §7.

Expected size: about 9 × 40 = 360 dev inputs (minus Vikidia MOD) and about 180 held-out inputs.

## 3. Generation design per axis (new prompts `*_v2.json`)

Shared principles:
- **The model returns only the edit, never a free rewrite of the sentence, where possible.** We build the degraded sentence ourselves and compute the changed span with our own diff. The model's declared spans are not trusted.
- The prompt contains **3 few-shot examples per operation**, hand-written from WikiAutoEN pairs that are *not* in any pool split. Store them in the prompt JSON.
- JSON output is enforced by the decoder: vLLM structured outputs locally, `response_schema` for Gemini.

### 3.1 MEANING — span-in / span-out

- The planner (reuse `plan_meaning_corruptions.detect`, with the fix that entities are not sentence-initial) picks **one target span** and a corruption type, balanced over `number | date | entity | negation | relation | event | property`.
- **number / date: deterministic, no LLM.** Year ± `k` with `k ∈ [3, 40]`, avoiding any year that appears in the Original. Other numbers are scaled by a factor ∈ {0.5, 2, 3, 10} and rounded to the same format. A month is replaced by another month. Record `generator: "rule"`. These rows are identical for C1–C4. They **stay in the main (end-to-end) ranking**, because that ranking chooses the pipeline we will actually use. They are removed only from the secondary **LLM-only** table (§6.1), which isolates model differences.
- **Other types: LLM.** Input: Original, Simplified, `target_span`, `corruption_type`. Output schema: `{"replacement": str, "rationale": str}`. Negation is handled as a span edit (insert/remove `not` or `never` around the auxiliary; the span is the auxiliary + verb). We splice the replacement into the Simplified sentence at the span offsets.
- Checks (all must pass): exactly one edit block vs. the clean text; replacement ≠ span (casefolded); NLI(original → degraded) contradiction ≥ 0.5; acceptability(degraded) ≥ acceptability(clean) − δ; the replacement does not appear in the Original (for entity/property swaps).

### 3.2 MOD — merge two sentences

- Operation `recombine_split`: merge **one** pair of adjacent Simplified sentences into one sentence (conjunction, relative clause, or participle).
- The model receives **only the Simplified text** and the index of the sentence pair to merge, **never the Original**. This removes the copy-the-Original failure.
- Output schema: `{"merged_sentence": str}`. We replace the two sentences with it.
- Checks: sentence count decreases by exactly 1; **content-lemma tolerance**: the symmetric difference of the content-lemma sets (spaCy lemma, non-stopword, ignoring connectives, relative pronouns and pronoun↔antecedent swaps) has ≤ 2 lemmas. Exact equality would reject valid merges because of inflection, contractions or spaCy errors. **Hard checks** that are separate and exact: named entities, numbers and negation markers must be identical to the Simplified; no token from the Original that is absent from the Simplified; NLI bidirectional entailment (degraded ↔ clean) ≥ 0.5 both ways; acceptability ≥ `tau_accept`.

### 3.3 ILLOC — speech-act injection on declarative clean text

v1 "reversal" cannot be sourced: only 16/73,586 pairs differ in whether they end with a question mark. v2 **injects** one change in communicative force while keeping the proposition. There are three operations, balanced within each cell and **always reported separately**:

| Operation | Example target form | Checks |
|---|---|---|
| `assertion_to_question` | "Is X a Y?" / "Did X …?" | ends with `?`; first token is an auxiliary/modal or wh-word; content-word set equal to the clean one |
| `assertion_to_directive` | "Note that …" / "Remember that …" / imperative | added tokens ⊆ directive lexicon; one edit block |
| `assertion_to_hedged` | "X might be …", "It is believed that …" | added tokens ⊆ hedge lexicon; one edit block |

Output schema: `{"degraded": str}`. It is a full rewrite here, but the checks constrain it tightly.

**Open decision (user):** whether `assertion_to_hedged` counts as illocution or as a meaning change under FEATS. Generate and report it separately; do not merge it into the ILLOC headline number.

## 4. Infrastructure

### 4.1 Environments

- New venv `.venv-phase6-vllm` (add it to `.gitignore`). Install a recent `vllm` and matching `torch`/`transformers` (Gemma 3 needs transformers ≥ 4.50), plus `spacy` + `en_core_web_sm`, and `google-genai`. Record the exact versions in `runs/mmi_en_v2/env_versions.json`.
- Config C0 runs with the **existing** `.venv-phase3` and the existing v1 scripts (see §5), so the baseline is the real v1 pipeline.
- Jobs: `jobs/submit_mmi_v2_{config}.sh`, Slurm `--partition=gpu --gres=gpu:1` (L40S 48 GB), array over the 9 cells. Keep `HF_HOME=${PROJECT_ROOT}/cache/huggingface`.

### 4.2 Checker models (not generators; pin revisions at download)

| Role | Model |
|---|---|
| NLI | `MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli` |
| Acceptability | a RoBERTa-large CoLA classifier (e.g. `cointegrated/roberta-large-cola-krishna2020`) |

Set `tau_accept` and `δ` from the WikiAutoEN dev clean inputs only: `tau_accept` = 10th percentile of accepted clean inputs after a manual spot-check of 20. Write them to the config and reuse them for every source.

### 4.3 Generator module

New `src/generation/generate_mmi_v2.py` with two backends: `vllm` and `gemini`.
- Sampling: `n=4`, `temperature=0.7`, `top_p=0.95`, per-row seed = `int(stable_key(seed, pair_id)[:8], 16)`. Keep all 4 candidates in the output row; the selected candidate is the **first** one (in sample order) that passes every check.
- Use the model's own tokenizer and chat template (v1 loaded the tokenizer from the QLoRA adapter repo; do not repeat that). For Gemma 3 there is no system role: prepend the system text to the user turn.
- Output schema `feats-phase6-mmi-generation-v2`: the provenance fields listed in §0, item 4, `candidates[]` with the per-candidate check results, `selected_index` (or null), `usage` (tokens in/out, and for Gemini the cost in USD).

## 5. Configs to compare

| ID | Model | Precision / backend | Prompts & decoding |
|---|---|---|---|
| **C0** | `Qwen/Qwen2.5-7B-Instruct` @ `a09a35458c702b33eeacc393d103063234e8bc28` | 4-bit NF4, transformers (`.venv-phase3`) | **v1 as is**: `generate_degradations.py` with the v1 prompts and v1 planner cues for MOD/ILLOC; `generate_meaning_degradations.py` with `meaning_severe_v2` for MEANING; greedy, n=1 |
| **C1** | `Qwen/Qwen2.5-7B-Instruct` (same revision) | bf16, vLLM | v2 prompts + checks, n=4 |
| **C2** | `google/gemma-3-12b-it` (cached snapshot `96b6f1eccf38110c56df3a15bffe176da04bfd80`) | bf16, vLLM | v2, n=4 |
| **C3** | `meta-llama/Llama-3.1-8B-Instruct` @ `0e9e39f249a16976918f6564b8830bc894c89659` (access confirmed 2026-09-30; download pending) | bf16, vLLM | v2, n=4 |
| **C4** | `gemini-2.5-flash` via API (`GEMINI_API_KEY`) | — | v2, n=4, **`gemini_pilot` split only** at first |

Notes:
- **C3 is a gated repo.** Access is confirmed; pin the revision above when downloading.
- **C0 inputs:** C0 gets the same dev pairs, but its prompts/planner are v1, so its MOD/ILLOC operation differs from v2's. Score C0 outputs with the v2 checks for the target axis anyway. It measures "the current pipeline on the new inputs".
- **C0 vs C1 is not a clean ablation.** Prompt, operation definition, precision (NF4 → bf16), decoding (greedy n=1 → sampling n=4) and checks all change at once. It measures "old pipeline vs new pipeline" only. C1 vs C2 vs C3 (vs C4) is the model effect under an identical pipeline. Optional and cheap (same model): **C1-greedy**, i.e. C1 with greedy n=1, which separates the sampling/best-of-4 gain from the prompt/operation gain. Report `check_pass@1` next to `yield@4` for every config for the same reason.

### 5.1 Gemini (C4) cost-controlled pilot

0. **STOP before the first API call.** The user must confirm (a) the price config (§5.1.2) filled in from the official page and (b) authorization to spend up to `max_usd`. No Gemini request is made before that confirmation.
1. Use `google-genai`, `response_mime_type="application/json"` + `response_schema`, **`thinking_config.thinking_budget=0`** (thinking tokens are billed as output), `temperature=0.7`, `candidate_count=4` if the model accepts it, otherwise 4 calls.
2. Put the per-token prices in `configs/experiments/mmi_en_v2_gemini.json`, taken from Google's **current official pricing page on the day of the run**, with the URL and date recorded. Do not hard-code prices from memory.
3. Log `usage_metadata` per request. Enforce a hard budget cap `max_usd` (default **5 USD**) by aborting when the running cost would exceed it.
4. Run C4 only on `gemini_pilot`: 10 pairs per cell, about 90 inputs, LLM-generated rows only.
5. Write `runs/mmi_en_v2/reports/gemini_pilot_cost.md` with: tokens and cost per input; the extrapolated cost for the full dev set and for a full-pool generation (per axis and source, using the pool sizes of §1.2); and a quality comparison against C1–C3 **on the same 10 pairs per cell**, using the metrics of §6.
6. **STOP.** The user decides whether C4 continues to the full dev set.

## 6. Evaluation

### 6.1 Automatic metrics (per config × axis × source cell; and per operation for ILLOC, per cue type for MEANING)

| Metric | Definition |
|---|---|
| parse_rate | candidates with valid JSON |
| noop_rate | degraded token signature (`\w+`, casefolded) == clean signature |
| copy_original_rate | degraded signature == original signature, or token overlap with original > overlap with clean + 0.1 |
| single_edit_rate | exactly one diff block vs clean (MEANING, ILLOC hedge/directive) / sentence-count −1 (MOD) |
| check_pass@1 | the first candidate passes all axis checks |
| yield@4 | ≥ 1 of 4 candidates passes (C0: same as @1) |
| judge_valid | LLM judge says valid (§6.2) on the selected candidate |
| cost | GPU-seconds per input (local); USD per input (C4) |

Aggregation and statistics:
- **Per cell:** rate with Wilson 95% CI (about ±15 pp at n=40; say so).
- **Per axis:** **macro** average (each source weighs equally; a cell marked `underpowered` is shown but excluded from the macro average) and **micro** average (each pair weighs equally). The ranking uses the macro average.
- **Two tables for MEANING:** *end-to-end* (all operations, including the rule-based number/date rows) is the ranking table; *LLM-only* (entity, negation, relation, event, property) is the model-difference table.
- **Paired comparisons between configs** (all configs see the same pairs): McNemar test on per-pair valid/invalid, and the difference in valid rate with a 95% CI from a bootstrap resampled by `canonical_original_id` (10,000 resamples, fixed seed). Wilson intervals are for single rates only and must not be used to compare two configs.

### 6.2 LLM judge (secondary signal)

- One checklist prompt per axis (`prompts/judge_{axis}_v2.json`), with output `{"valid": bool, "single_change": bool, "target_axis_changed": bool, "other_axes_preserved": bool, "reason": str}`.
- Cross-family only: Gemma-3-12B judges C0/C1/C3 outputs; Qwen2.5-7B bf16 judges C2 outputs; Gemma-3-12B judges C4 outputs. Greedy decoding.
- **Calibration before use:**
  - MEANING: the v1/retry outputs in `runs/meaning_en_pilot_v1/degradation/`. Outputs whose `accepted_source` is `qwen_v1` or `qwen_v2_retry` count as valid; the rejected model outputs of manually corrected rows count as invalid.
  - MOD/ILLOC: the human-marked cases in `docs/reports/pilot_random_review.md`.
  - If agreement is < 85% on an axis, the judge is **reported but not used for ranking** on that axis.

### 6.3 Ranking and human audit

1. Rank configs per axis by **macro** end-to-end `yield@4`, tie-broken by `judge_valid` (only if calibrated), then `single_edit_rate`. Only `assertion_to_question` and `assertion_to_directive` count for the ILLOC ranking; `assertion_to_hedged` is reported separately until the FEATS definition is settled. C4 enters the ranking only if the user approved its full dev run.
2. Take the **top 2 configs per axis** and generate on the `heldout` split.
3. Build a **blinded** review file (reuse `src/reporting/build_random_review.py` style; shuffle; hide config id; keep a private key file under `runs/`): `docs/reports/mmi_v2_heldout_review.md`, with Valid / Invalid / Unsure checkboxes and a Note, like `pilot_random_review.md`. Also show the `source` of each case.
4. **STOP** for the human audit.
5. After the audit: compute the valid rate per config × axis × source. **The human heldout result, not the LLM judge, decides the winner per axis**, using the paired statistics of §6.1. Gate (unchanged from v1): ≥ 85% valid single-axis degradations per axis. Per-source rates are diagnostic. A source cell that is systematically worse (> 15 pp below the axis mean) gets flagged in the report.

### 6.4 Decision rule per axis (after the human audit)

Apply the rule separately to MEANING, MOD and ILLOC. The primary metric is the **human valid rate on `heldout`**, macro-averaged over sources.

1. **Gate.** A finalist is eligible only if its macro human valid rate is ≥ 85%. If neither finalist reaches it, there is no winner: revise the prompts/checks for that axis and repeat §6.3 with a fresh held-out sample. Do not lower the gate.
2. **One eligible finalist:** it wins.
3. **Two eligible finalists:** compare them with the paired statistics of §6.1 (McNemar + bootstrap CI of the difference by `canonical_original_id`).
   - If the difference is significant (p < 0.05 and the bootstrap CI excludes 0), the better one wins.
   - Otherwise the two are treated as equivalent, and the tie-break is, in order: (a) **cost per valid output** (GPU-seconds, or USD for C4, divided by `yield@4`); (b) local over API (reproducibility, no data leaves the cluster, no per-call cost at full scale); (c) no source cell > 15 pp below the axis mean.
4. **Report** for each axis: the winner, the rule step that decided it, the valid rates with CIs, and the cost extrapolated to the full pool.

With about 60 paired held-out items per axis, only differences of roughly 15–20 pp are detectable, so ties are expected. The tie-break is therefore part of the decision, not an afterthought.

## 7. Deliverables

- `runs/mmi_en_v2/pools/pool_report.json`: per-filter counts per cell.
- `runs/mmi_en_v2/reports/gemini_pilot_cost.md` (§5.1).
- `docs/reports/mmi_v2_model_comparison.md`: tables per axis with rows = configs and columns = sources, for each metric in §6.1; an ILLOC per-operation table; a MEANING per-cue-type table; for MEANING `pilot50`, the rate at which each config reaches a valid output on inputs where v1 needed manual correction (19 cases); 5 examples per axis per config (good and bad); a recommendation per axis.
- `docs/reports/mmi_v2_heldout_review.md` (blinded audit file) and, after the audit, a results section appended to the comparison report.
- Update `docs/methodology/{meaning,modulation,illocution}_degradation.md` with a short "v2" section that links to the plan and the report. Do not rewrite the v1 description.
- Tests (unittest, under `phase6_degraded_corpus/tests/`): the pool filters on hand-made rows; per-cell disjointness by `canonical_original_id`; the reserved-original exclusion and materializer guard; span splicing for MEANING; MOD sentence-count and content-word checks; ILLOC form checks for each operation; the budget-cap abort in the Gemini backend (mock the client); deterministic dev sampling (same seed → same ids).

## Execution status (2026-09-29)

- Steps 0–5 done; step 8 prepared for the local finalists. Results: [`../reports/mmi_v2_model_comparison.md`](../reports/mmi_v2_model_comparison.md) (includes the deviations list).
- Finalists on all three axes: **C1** (Qwen2.5-7B bf16, v2) and **C2** (Gemma-3-12B, v2). The LLM judge failed calibration (55–60% agreement) and is not used.
- **Blocked:** C3 Llama (HF 403, access not granted); C4 Gemini (STOP §5.1.0).
- **Waiting for the human audit:** [`../reports/mmi_v2_heldout_review.md`](../reports/mmi_v2_heldout_review.md) (222 blinded cases). Score it with:
  `python -m phase6_degraded_corpus.src.reporting.build_mmi_heldout_review score --review phase6_degraded_corpus/docs/reports/mmi_v2_heldout_review.md --key phase6_degraded_corpus/runs/mmi_en_v2/reports/heldout_review_key.json --results-json phase6_degraded_corpus/runs/mmi_en_v2/reports/heldout_results.json --append-to phase6_degraded_corpus/docs/reports/mmi_v2_model_comparison.md`

## 8. Order of execution and STOP points

0. ✅ Freeze the evaluation originals and confirm Llama access (done). **Pending:** switch to the strong matching key + near-duplicate exclusion (§0, item 3) and re-emit the reserved list with both counts.
1. ✅ Structural pools + reserved exclusion (done, commit `5202bc4`). **Rework needed:** real Phase 3a strategy fields (§1) and two-pass allocation (§1.3).
2. Download the checker models (NLI, CoLA) with pinned revisions; set `tau_accept`/`δ`; apply the clean-input gates to the pools; **then** run allocation and dev/held-out sampling. Unit tests for the checks and the allocation.
3. Build the vLLM venv; download C3 at the pinned revision.
4. Run C0 (v1 scripts) and C1, C2, C3 on `dev`; compute the metrics.
5. Calibrate the judge; run the judge; write a draft of `mmi_v2_model_comparison.md`.
6. **STOP: user confirms prices and budget (§5.1.0).** Then run the C4 Gemini pilot on `gemini_pilot` and write the cost report. **STOP: user decides whether C4 continues.**
7. (If approved) run C4 on the full `dev`; update the comparison.
8. Run the top 2 configs per axis on `heldout`; build the blinded review file. **STOP for the human audit.**
9. Score the audit; finalize the report and the methodology updates.

## 9. Out of scope

FLUENCY, OMIT, SYN, EXPL (handled in a later plan, mostly with deterministic generators); full-pool generation; training-data materialization; non-English data.
