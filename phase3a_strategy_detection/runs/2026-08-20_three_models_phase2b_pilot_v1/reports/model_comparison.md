# Phase 3 canonical pilot: three-model comparison

All three runs passed structural validation on the same 859 canonical Phase 2b pairs.

## Prediction profile

| Model | Mean strategies | Zero | Multilabel | Full GPU-hours (projected) |
|---|---:|---:|---:|---:|
| XLM-R Large focal | 2.653 | 8.27% | 76.14% | 1.60 |
| Multilingual-E5 Large BCE | 3.193 | 0.35% | 88.13% | 1.61 |
| Qwen2.5-7B pairwise QLoRA | 2.400 | 4.89% | 71.01% | 128.38 |

## Pairwise agreement

| Models | Exact label set | Hamming disagreement | Mean Jaccard |
|---|---:|---:|---:|
| xlmr_large_focal vs multilingual_e5_large_bce | 19.67% | 27.78% | 0.543 |
| xlmr_large_focal vs qwen2p5_7b_pairwise_qlora | 16.07% | 30.25% | 0.457 |
| multilingual_e5_large_bce vs qwen2p5_7b_pairwise_qlora | 10.13% | 32.27% | 0.476 |

The checkpoints are not interchangeable: exact agreement is only 10–20%.

## Existing upstream labels

- Consistent labelled pairs: 118
- Conflicting labelled pairs excluded: 0
- Provenance: unverified; these comparisons are not gold evaluation.

| Model | Exact label set | Hamming disagreement | Mean Jaccard |
|---|---:|---:|---:|
| XLM-R Large focal | 25.42% | 20.48% | 0.648 |
| Multilingual-E5 Large BCE | 27.97% | 20.48% | 0.670 |
| Qwen2.5-7B pairwise QLoRA | 36.44% | 15.11% | 0.739 |

## Interpretation

- Multilingual-E5 predicts the most labels, especially SYN, COMP and OMIT.
- XLM-R and Qwen are less label-dense, but still disagree substantially.
- The pilot includes six zero-shot languages outside the checkpoints’ documented training languages: de, ja, pt-BR, ru, sl and ur.
- Full-corpus inference would describe model behaviour; it would not determine which model is correct.
- Encoder full runs are inexpensive (~1.6 GPU-hours each). Qwen requires ~128 GPU-hours and internal sharding.

Official checkpoint evidence also differs: the released model cards report three-seed test Macro-F1 of 59.20 for XLM-R and 61.35 for E5. The Qwen checkpoint currently has no model card with an equivalent test result.

## Recommendation

Run the two encoder checkpoints over the full corpus after adding resumable output. Do not spend ~128 Qwen GPU-hours until the intended primary checkpoint and treatment of zero-shot languages are confirmed with Nouran.

## Detailed files

- `model_comparison.csv`
- `model_comparison_by_language.csv`
- `model_comparison_by_language_source_corpus.csv`
- `pairwise_model_agreement.csv`
- `upstream_label_comparison.csv`
- [Qualitative disagreements](qualitative_model_disagreements.md)
