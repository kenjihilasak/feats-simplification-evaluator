# Phase 6 inputs

[Phase 6 overview](overview.md) · [MEANING/MOD/ILLOC v2 plan](plans/archive/meaning_mod_illoc_v2_plan.md) · [Phase 2b text repair](../../phase2b_consolidation/docs/text_repair_plan.md)

This page is the single source of truth for **which data Phase 6 reads**. Every Phase 6 config must point to the files listed here and record their SHA-256 in its run report.

## 1. Clean pairs (original + simplified)

From experiment `mmi_en_v2` onward, Phase 6 reads **only** the text-repaired `target_simple` variant of Phase 2b:

```text
phase2b_consolidation/runs/2026-09-29_target_simple_textrepair_v1/data/<language>/feats_consolidated.jsonl
```

For English: `…/data/en/feats_consolidated.jsonl`, 73,586 pairs (WikiAutoEN, ASSET, Wikipedia-Vikidia).

| Phase 2b field | Phase 6 field | Use |
|---|---|---|
| `canonical_pair_id`, `canonical_original_id` | same | Join keys and split unit. **Unchanged by the repair**: they are hashes of the raw upstream text, so they still join with Phase 3a, 4a and 5. |
| `original` | `original` | Repaired original text. Used in prompts and checks. |
| `simple` | `clean_simplification` | Repaired simplified text. It is the clean positive (`score = 1`) and the text that gets degraded. |
| `original_raw`, `simple_raw`, `*_raw_sha256` | `original_raw`, `clean_simplification_raw`, … | Provenance only. **Never** send them to a model or use them in checks. |
| `text_repaired` | `glue_repaired` | Flag for per-group reporting. |
| `repaired_duplicate_of` | — | Rows where this is not `null` are **skipped**: they are the same text as another pair. |
| `corpora`, `provenance`, `upstream_splits` | `source`, `corpus`, … | Source stratification. `upstream_splits` is not a reliable split for ASSET (MultiSim re-splits it). |

### Why the `target_simple` variant and not the base consolidation

Phase 6 needs clean positives. `target_simple` applies the stricter Phase 2a filter (`2026-09-02_complexity_target_simple_smp01_labse062_095_full_flat_v3`). The repaired **base** consolidation (`runs/2026-09-29_base_textrepair_v1/`) is the input for Phase 3a and Phase 5, not for Phase 6.

### Rules

- Phase 6 never repairs or rewrites text itself. If a new text defect is found, fix it in a new Phase 2b variant and update this page.
- Phase 6 never modifies Phase 2b files.
- **Reserved evaluation originals** are excluded before any selection: Simplicity-DA, Human-Likert, AssetAnn, SimpEval-2022 and the official ASSET test set, frozen by `src/selection/freeze_evaluation_originals.py` (manifest: `runs/mmi_en_v2/pools/evaluation_sources_manifest.json`; 419 distinct sentences). Matching uses the strong key (NFKC, casefold, alphanumerics only) plus near-duplicate exclusion (word Jaccard ≥ 0.8). See §0 item 3 of the [v2 plan](plans/archive/meaning_mod_illoc_v2_plan.md). This applies to every Phase 6 experiment and to any future training set.

## 2. Strategy labels (Phase 3a)

| Consumer | Phase 3a input | Role |
|---|---|---|
| `mmi_en_v2` (MEANING, MOD, ILLOC) | the text-repaired Phase 3a run once it is available (§3); until then, `2026-08-31_single_strategy_gemma_anchored_strict_v1` | **Metadata only** (`source_strategy`, may be `null`). None of the MEANING/MOD/ILLOC pools or checks depend on it; MOD pools are defined by sentence-split evidence from the repaired text. |
| Later plans for OMIT, SYN, EXPL, FLUENCY | **must** use the text-repaired Phase 3a candidate set | Selection gate: these axes require a single detected strategy. |

Phase 3a v1 labels were predicted on glued text. For about 21k English pairs, "two sentences" looked like one, which mainly affects `MOD` and `COMP`. That is why the axes that are gated on strategy wait for the re-run, while `mmi_en_v2` does not.

`mmi_en_v2` selection is cheap and deterministic. When the re-run lands, re-run only its selection step, which refreshes the `source_strategy` metadata. Pools and dev sets stay identical because they do not depend on Phase 3a.

## 3. Phase 3a re-run status

Plan: [`phase3a_strategy_detection/docs/textrepair_rerun_plan.md`](../../phase3a_strategy_detection/docs/textrepair_rerun_plan.md).

| Item | Path | Status |
|---|---|---|
| Predictions (delta re-run on repaired rows) | `phase3a_strategy_detection/runs/2026-09-30_four_models_textrepair_delta_v1/` | pending |
| Effective predictions (v1 + delta) | `phase3a_strategy_detection/runs/2026-09-30_four_models_textrepair_effective_v1/` | pending |
| Candidate set | `phase3a_strategy_detection/gold_candidates/2026-09-30_single_strategy_gemma_anchored_strict_textrepair_v1/` | pending |

Update this table when each item is validated.

## 4. Frozen historical inputs (do not regenerate)

| Experiment | Clean pairs | Strategy labels |
|---|---|---|
| `meaning_en_pilot_v1` | `phase2b_consolidation/runs/2026-09-02_target_simple_v1/` (raw text) + Phase 4a anchors | Phase 3a v1 |
| `multi_axis_en_v1` | `phase2b_consolidation/runs/2026-09-02_target_simple_v1/` (raw text) | `2026-08-31_single_strategy_gemma_anchored_strict_v1` |

Their results stay as they are and are only comparable to v2 with that caveat: v1 inputs contain glued sentences.
