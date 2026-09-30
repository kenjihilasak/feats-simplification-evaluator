# Plan: FLUENCY, OMIT, SYN, EXPL degradations (rule-based)

Execution plan. Experiment id: **`fose_en_v1`**. English only.

## 0. Context

MEANING, MOD and ILLOC are finished ([methodology](../methodology/README.md); corpus in `runs/mmi_en_v2_full/corpus/`, 18,538 pairs). The v1 LLM pilot for the other four axes failed: 30–60% of outputs were copies or empty edits (see [archive](../methodology/archive/)).

In v2, these axes are generated **by rule**. OMIT, SYN and EXPL can be recovered from the word alignment between Original and Simplified; FLUENCY uses controlled grammar-error injection. No model comparison is needed. The gate is one blinded human audit, followed by full generation.

## 1. Hard constraints

1. Input contract: [`../inputs.md`](../inputs.md) (text-repaired `target_simple` Phase 2b; reserved evaluation originals excluded, exact and near duplicates; skip `repaired_duplicate_of`).
2. **No reuse of originals:** exclude every `canonical_original_id` already used by `runs/mmi_en_v2_full` (its corpus, allocation and `excluded_audited_originals.txt`) and every original in `runs/mmi_en_v2/splits/*`. One original → one axis in the whole Phase 6 corpus.
3. **OMIT, SYN, EXPL require Phase 3a:** use the text-repaired candidate set `phase3a_strategy_detection/gold_candidates/2026-09-30_single_strategy_gemma_anchored_strict_textrepair_v1/` (the strategy must equal the axis). **STOP** if it is not validated yet. FLUENCY does not depend on Phase 3a and can run first.
4. Reuse the MMI checker stack unchanged: NLI and acceptability revisions, τ, δ and scorer utilities from `configs/experiments/mmi_en_v2_pools.json`, and the `.venv-phase6-vllm` venv. No LLM generation.
5. All outputs go under `runs/fose_en_v1/`. Stop at every **STOP**.

## 2. Source pools

Common gate (as in MMI): Original 8–45 tokens, non-identical, acceptability(clean) ≥ τ, NLI P(contradiction | Original, Simplified) < 0.5. Then, per axis:

| Axis | Eligibility (word-level `difflib` alignment of lowercased tokens) |
|---|---|
| FLUENCY | Any remaining pair. The Simplified text has ≥ 1 applicable error site (§3.1). |
| OMIT | Single strategy OMIT. Overlap ≥ 0.4; length ratio 0.5–1.6; ≤ 4 edit blocks; ≥ 1 **deleted** block containing a content word; no insertion blocks. |
| SYN | Single strategy SYN. Same structural limits. ≥ 1 **replace** block of 1–4 Original tokens → 1–3 Simplified tokens, all word tokens, with the Original side **rarer**: mean `wordfreq` Zipf (en) of the content words at least 0.5 lower than the Simplified side. |
| EXPL | Single strategy EXPL. Same limits, except length ratio up to 1.6. ≥ 1 **insert** block of ≥ 2 tokens with a content word. |

Allocation: OMIT, SYN and EXPL first (Phase 3a gives one strategy per pair, so they don't compete); FLUENCY takes pairs not used by any axis. Balance sources as in MMI.

**Step 1 deliverable:** `pool_report.json` with counts per filter step × axis × source. **STOP** if any axis has fewer than 500 pairs, and report.

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

1. Blinded review built with the existing `build_mmi_heldout_review.py` style: **20 outputs per axis × source** (fewer if the cell is smaller), shuffled. Each case states the required change. File: `docs/reports/current/fose_v1_review.md`. Key under `runs/`.
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

Output: `runs/fose_en_v1/corpus/{train,validation}.jsonl`. Then write a combined manifest `runs/phase6_corpus_manifest.json` that lists the MMI and FOSE corpus files with their SHA-256 and counts per axis, and verifies that **no original appears in both**.

## 6. Deliverables

- Modules:
  - `src/selection/select_fose_pools.py`;
  - `src/generation/generate_fose_rules.py` (one function per axis);
  - `src/evaluation/score_fose_candidates.py`;
  - `src/evaluation/materialize_fose.py`.
- Unit tests for every rule, with hand-written must-change and must-not-change cases per error type, plus tests for the pool filters and the cross-corpus original disjointness.
- Methodology pages `docs/methodology/{fluency,omission,synonymy,explanation}.md`, in the same concise format as `meaning.md`, and new rows in `methodology/README.md`.
- Report `docs/reports/current/fose_v1_report.md`: pool counts, rule yield and drop reasons, audit results, and corpus counts.
- Local commit. **No push.**

## 7. Order and STOP points

1. FLUENCY pools, rules, checks and tests (no Phase 3a needed).
2. Once Phase 3a is validated: OMIT, SYN and EXPL pools → pool report. **STOP if < 500 pairs.**
3. Rules and checks for all four axes on a sample; build the review. **STOP for the human audit.**
4. Score it; full generation for the axes that pass; materialize; combined manifest; report; commit.
