# Degradation methodology

Current, selected configurations (2026-09-30). The rationale and evidence are in [the model comparison](../reports/current/mmi_v2_model_comparison.md).

| Axis | Page | Generator | Human valid (heldout) |
|---|---|---|---|
| MEANING | [meaning.md](meaning.md) | Qwen2.5-7B-Instruct bf16, v2.1 | 88% |
| MOD | [modulation.md](modulation.md) | Gemma-3-12B-it bf16; graded v4 (28 Oct 2026) | 95% (v2 merge) |
| ILLOC | [illocution.md](illocution.md) | Qwen2.5-7B-Instruct bf16, v4 (28 Oct 2026): a direct act made indirect | v2: 90% (question + directive), 95% (hedged); v2/v3 operations retired |
| FLUENCY | [fluency.md](fluency.md) | Deterministic grammar rules | Audit pending |
| OMIT | [omission.md](omission.md) | Deterministic alignment rule | Audit pending |
| SYN | [synonymy.md](synonymy.md) | Deterministic alignment + `wordfreq` | Audit pending |
| EXPL | [explanation.md](explanation.md) | Deterministic alignment rule | Audit pending |

**Shared to all three axes:**
- **Inputs:** [`../inputs.md`](../inputs.md).
- **Decoding:** vLLM 0.10.0 with a JSON schema enforced during decoding, 4 samples (temperature 0.7, top-p 0.95) and a per-pair seed.
- **Selection:** the first sample that passes every automatic check of its axis is kept; pairs with no passing sample are discarded.
- **Checkers:** NLI `MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli@b3546ea`, acceptability `cointegrated/roberta-large-cola-krishna2020@efffc0d` (τ = 0.946, δ = 0.042).
- **Labels:** each pair yields the clean simplification (score 1) and the degraded text (score 0) for its target axis only.

## Shared workflow

1. Select a usable Phase 2b clean simplification and exclude reserved evaluation originals.
2. Choose one target axis and one eligible operation for that pair.
3. Generate four constrained candidates with the selected model and JSON schema.
4. Run the axis-specific structural, meaning, and acceptability checks.
5. Keep the first passing candidate; otherwise discard the pair.
6. Materialize the clean text as label `1` and its accepted degradation as label `0` for that axis only.

**Code:**
- Planner: [`plan_mmi_operations.py`](../../src/planning/plan_mmi_operations.py).
- Generator: [`generate_mmi_v2.py`](../../src/generation/generate_mmi_v2.py).
- Checks: [`score_mmi_candidates.py`](../../src/evaluation/score_mmi_candidates.py).

**Other languages (v2, 28–29 Oct 2026):** Spanish, French, Italian, Catalan, Russian and Arabic use the same axes through [`select_multilingual_pools.py`](../../src/selection/select_multilingual_pools.py) (pools, rules, MOD, ILLOC) and [`generate_meaning_fluency_ml.py`](../../src/generation/generate_meaning_fluency_ml.py) (MEANING, FLUENCY); outputs, checks and the shortcut audit are in [the v2 report](../reports/current/phase6_v2_multilingual.md).

The failed LLM-pilot methodology for FLUENCY, OMIT, SYN and EXPL remains in [`archive/`](archive/).
