# Plan: FLUENCY, OMIT, SYN, EXPL degradations (rule-based)

Execution plan. Experiment id: **`fose_en_v1`**. English only.

## 0. Context

MEANING, MOD and ILLOC are finished ([methodology](../methodology/README.md); corpus in `runs/mmi_en_v2_full/corpus/`, 18,538 pairs). The v1 LLM pilot for the other four axes failed: 30–60% of outputs were copies or empty edits (see [archive](../methodology/archive/)).

In v2, these axes are generated **by rule**. OMIT, SYN and EXPL can be recovered from the word alignment between Original and Simplified; FLUENCY uses controlled grammar-error injection. No model comparison is needed. The gate is one blinded human audit, followed by full generation.

## 1. Hard constraints

1. Input contract: [`../inputs.md`](../inputs.md) (text-repaired `target_simple` Phase 2b; reserved evaluation originals excluded, exact and near duplicates; skip `repaired_duplicate_of`).
2. **Pairs may be reused across axes** (decision 2026-09-30). One model will be trained **per axis** (as recommended in the E2R TACL paper), so each model sees a pair at most once, and reuse across axis models introduces no conflicting labels. Rules:
   - at most **one degradation per (pair, axis)**;
   - **split consistency:** the train/validation split is a function of `canonical_original_id` only, using `split_for()` from `src/evaluation/materialize_mmi_full.py` with the **same seed (20260930) and fraction (0.1)**. An original is therefore in the same split for every axis, including MMI. Import the function; do not copy it;
   - still excluded everywhere: reserved evaluation originals (exact + near) and every original in `runs/mmi_en_v2_full/allocation/excluded_audited_originals.txt` (human-audited heldout).
3. **OMIT, SYN, EXPL require Phase 3a:** use the text-repaired candidate set `phase3a_strategy_detection/gold_candidates/2026-09-30_single_strategy_gemma_anchored_strict_textrepair_v1/` (the strategy must equal the axis). **STOP** if it is not validated yet. FLUENCY does not depend on Phase 3a and can run first.
4. Install and pin `wordfreq` in `.venv-phase6-vllm` (not installed yet); record its version. Reuse the MMI checker stack unchanged: NLI and acceptability revisions, τ, δ and scorer utilities from `configs/experiments/mmi_en_v2_pools.json`, and the `.venv-phase6-vllm` venv. No LLM generation.
5. All outputs go under `runs/fose_en_v1/`. Stop at every **STOP**.

## 2. Source pools

Common gate (as in MMI): Original 8–45 tokens, non-identical, acceptability(clean) ≥ τ, NLI P(contradiction | Original, Simplified) < 0.5. Then, per axis:

| Axis | Eligibility (word-level `difflib` alignment of lowercased tokens) |
|---|---|
| FLUENCY | Any remaining pair. The Simplified text has ≥ 1 applicable error site (§3.1). |
| OMIT | Single strategy OMIT. Overlap ≥ 0.4; length ratio 0.5–1.6; ≤ 4 edit blocks; ≥ 1 **deleted** block containing a content word; no insertion blocks. |
| SYN | Single strategy SYN. Same structural limits. ≥ 1 **replace** block of 1–4 Original tokens → 1–3 Simplified tokens, all word tokens, with the Original side **rarer**: mean `wordfreq` Zipf (en) of the content words at least 0.5 lower than the Simplified side. |
| EXPL | Single strategy EXPL. Same limits, except length ratio up to 1.6. ≥ 1 **insert** block of ≥ 2 tokens with a content word. |

Allocation: **none needed.** Each axis takes every eligible pair independently, whether or not MMI already used it. Record `also_in_mmi: bool` per row. OMIT, SYN and EXPL do not compete with each other, because Phase 3a gives one strategy per pair. **FLUENCY** gets many more eligible pairs than the other axes. Cap it at the size of the largest of the other seven axes (MEANING, MOD, ILLOC, OMIT, SYN, EXPL), sampling by `stable_key` stratified by source and error type, so it does not dominate.

**Step 1 deliverable:** `pool_report.json` with counts per filter step × axis × source, and the overlap with MMI. Report only; no STOP on size.

## 3. Generation rules (deterministic, seeded with `stable_key`)

Each rule makes **exactly one** edit. The chosen site is picked by `stable_key` among the eligible sites.

### 3.1 FLUENCY: one local grammar error

Error types, balanced within each source:

| Type | Rule | Example |
|---|---|---|
| `agreement` | Flip the number of a finite `be`/`have` form (is↔are, was↔were, has↔have) when its subject is not ambiguous. | "The birds **was** …" |
| `determiner_drop` | Delete an article before a singular common noun. | "He is **∅** famous singer." |
| `preposition_swap` | Replace one preposition from a fixed confusion table (in↔on, at↔in, of↔for, to↔at). | "She was born **on** Paris." |
| `word_order` | Swap two adjacent tokens: adjective+noun or auxiliary+verb; never names or numbers. | "a singer **famous**" |

Checks:
- exactly one edit block;
- acceptability(degraded) ≤ acceptability(clean) − 0.10 (it must really be worse);
- NLI entailment ≥ 0.5 in both directions (meaning kept);
- no-op impossible by construction.

### 3.2 OMIT: restore one usefully omitted detail

Take one **deleted** block (content words) and re-insert its Original tokens at the aligned position in the Simplified text. Detokenize and fix spacing and a/an.

Checks:
- the inserted text appears literally in the Original;
- the degraded text is longer than the clean text;
- acceptability ≥ min(τ, clean − δ);
- NLI(degraded → clean) entailment ≥ 0.5 (only information was added).

### 3.3 SYN: restore one complex word

Replace the Simplified side of one qualifying **replace** block (§2) with its Original tokens, and fix a/an.

Checks:
- the restored words appear in the Original;
- Zipf(restored) ≤ Zipf(simple) − 0.5;
- NLI entailment ≥ 0.5 in both directions;
- acceptability ≥ min(τ, clean − δ).

### 3.4 EXPL: remove one added explanation

Delete one **insert** block (≥ 2 tokens). Clean up the orphan punctuation it leaves: double commas, `( )`, a dangling `, which` or `, a`.

Checks:
- acceptability ≥ min(τ, clean − δ);
- NLI(clean → degraded) entailment ≥ 0.5 (only information was removed);
- the degraded text is shorter;
- the removed span is absent from the Original.

A pair whose rule output fails the checks is dropped, with the reason recorded. There is no retry and no LLM repair.

## 4. Human gate

1. Blinded review built with the existing `build_mmi_heldout_review.py` style: **20 outputs per axis × source** (fewer if the cell is smaller), shuffled. Each case states the required change **and the validity criterion**. Valid = the rule applied correctly **and** the degraded text is a clearly *worse simplification on that axis* than the clean text, with everything else unchanged:
   - FLUENCY: an obvious grammar error; the meaning is intact.
   - OMIT: the restored detail is unnecessary or too hard for the target reader. A detail that the simplification *should* have kept counts as invalid.
   - SYN: the restored word is harder than the simple one and means the same.
   - EXPL: the removed span actually helped understanding (an explanation or definition), not just any extra fact. File: `docs/reports/current/fose_v1_review.md`. Key under `runs/`.
2. **STOP** for the human audit.
3. Score it (Unsure counts as valid). **Gate:** macro valid ≥ 85% per axis.
   - An axis that passes is generated in full.
   - An axis that fails: report the errors per type and STOP. Its fix is a rule or check change followed by a new review of that axis only.

## 5. Full generation and materialization

For each axis that passes: apply the rules to its whole pool, keep the rows that pass the checks, and materialize them exactly as MMI does:
- two rows per pair (clean = 1, degraded = 0), labels for the target axis only;
- 90/10 split by `canonical_original_id`;
- Phase 3a metadata kept;
- guard against reserved and audited originals.

Output: **one corpus per axis**, `runs/fose_en_v1/corpus/{axis}/{train,validation}.jsonl`. Also split the MMI corpus into per-axis files under `runs/mmi_en_v2_full/corpus/by_axis/` (read-only derivation), so every axis model reads the same layout. Then write a combined manifest `runs/phase6_corpus_manifest.json` that lists all seven axis corpora with their SHA-256 and counts, and verifies that:
- every original has the same split in every axis;
- no reserved or audited original appears anywhere.

**Shortcut diagnostic (reported, not a gate):** for each axis, the accuracy on the validation split of trivial baselines that tell clean from degraded using only (a) the length ratio simplified/original and (b) the acceptability score. Accuracy near 100% means an axis model could learn the shortcut instead of the axis. By construction OMIT is always longer and EXPL always shorter, and FLUENCY always has lower acceptability.

## 6. Deliverables

- Modules:
  - `src/selection/select_fose_pools.py`;
  - `src/generation/generate_fose_rules.py` (one function per axis);
  - `src/evaluation/score_fose_candidates.py`;
  - `src/evaluation/materialize_fose.py`.
- Unit tests for every rule, with hand-written must-change and must-not-change cases per error type, plus tests for the pool filters, one-degradation-per-(pair, axis), and split consistency with MMI.
- Methodology pages `docs/methodology/{fluency,omission,synonymy,explanation}.md`, in the same concise format as `meaning.md`, and new rows in `methodology/README.md`.
- Report `docs/reports/current/fose_v1_report.md`: pool counts, rule yield and drop reasons, audit results, and corpus counts.
- Local commit. **No push.**

## 7. Order and STOP points

1. FLUENCY pools, rules, checks and tests (no Phase 3a needed).
2. Once Phase 3a is validated: OMIT, SYN and EXPL pools → pool report.
3. Rules and checks for all four axes on a sample; build the review. **STOP for the human audit.**
4. Score it; full generation for the axes that pass; materialize; combined manifest; report; commit.
