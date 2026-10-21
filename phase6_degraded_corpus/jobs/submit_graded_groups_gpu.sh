#!/usr/bin/env bash
#SBATCH --job-name=phase6-graded
#SBATCH --partition=gpu
#SBATCH --gres=gpu:l40s:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --output=phase6_degraded_corpus/logs/graded_%j.out
#SBATCH --error=phase6_degraded_corpus/logs/graded_%j.err
# Usage (from the project root): sbatch phase6_degraded_corpus/jobs/submit_graded_groups_gpu.sh
set -euo pipefail
project_root=/scratch/pjbd103/feats-simplification-evaluator
cd "$project_root"
R=phase6_degraded_corpus/runs; run=$R/graded_en_v1; py=.venv-phase6-vllm/bin/python
mkdir -p "$run/generations" "$run/scored" "$run/plans"
export HF_HOME="$project_root/cache/huggingface" HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false VLLM_WORKER_MULTIPROC_METHOD=spawn
pools=phase6_degraded_corpus/configs/experiments/mmi_en_v3_pools.json
# MOD: LLM fronting (A), then rule reorder of the clean (B) and of the fronted text (AB).
[[ -s "$run/generations/mod_fronting.jsonl" ]] || $py -m phase6_degraded_corpus.src.generation.generate_mmi_v2 --plan "$run/plans/mod_graded_plan.jsonl" \
  --config phase6_degraded_corpus/configs/experiments/mmi_en_v3_generation.json --config-id MOD_C2 --output "$run/generations/mod_fronting.jsonl"
[[ -s "$run/scored/mod_fronting.jsonl" ]] || $py -m phase6_degraded_corpus.src.evaluation.score_mmi_candidates --generations "$run/generations/mod_fronting.jsonl" \
  --plan "$run/plans/mod_graded_plan.jsonl" --pools-config $pools --output "$run/scored/mod_fronting.jsonl" --device cuda
$py -m phase6_degraded_corpus.src.generation.combine_mod_graded prepare --scored "$run/scored/mod_fronting.jsonl" --plan "$run/plans/mod_graded_plan.jsonl" \
  --plan-out "$run/plans/mod_reorder_plan.jsonl" --generations-out "$run/generations/mod_reorder.jsonl"
[[ -s "$run/scored/mod_reorder.jsonl" ]] || $py -m phase6_degraded_corpus.src.evaluation.score_mmi_candidates --generations "$run/generations/mod_reorder.jsonl" \
  --plan "$run/plans/mod_reorder_plan.jsonl" --pools-config $pools --output "$run/scored/mod_reorder.jsonl" --device cuda
$py -m phase6_degraded_corpus.src.generation.combine_mod_graded finalize --fronting "$run/scored/mod_fronting.jsonl" \
  --reorders "$run/scored/mod_reorder.jsonl" --output "$run/mod_groups.jsonl"
# OMIT, SYN: two rule sites per pair.
$py -m phase6_degraded_corpus.src.generation.generate_graded_rule_groups --config phase6_degraded_corpus/configs/experiments/fose_en_v2.json \
  --exclude $R/fose_en_v2/review_key.json --exclude $R/mmi_en_v3/review_key.json --exclude $R/fose_en_v2/audit/sample.jsonl \
  --output "$run/fose_groups.jsonl" --device cuda
