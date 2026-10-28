#!/usr/bin/env bash
#SBATCH --job-name=phase6-s1-ml
#SBATCH --partition=gpu
#SBATCH --gres=gpu:l40s:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=06:00:00
#SBATCH --output=phase6_degraded_corpus/logs/s1_ml_%j.out
#SBATCH --error=phase6_degraded_corpus/logs/s1_ml_%j.err
# Phase 6 candidates for one language: pools, checker calibration, rules, MOD and ILLOC generation, scoring.
# Usage (from the project root): sbatch phase6_degraded_corpus/jobs/submit_s1_multilingual_gpu.sh LANG [VERSION]
# LANG is en|es|fr|it|ca|ru|ar; VERSION defaults to v1 (Spanish/French S1 round). v2 uses ILLOC v4 and MOD v4.
# Every step is skipped when its output exists, so a resubmission resumes.
set -euo pipefail
project_root=/scratch/pjbd103/feats-simplification-evaluator
cd "$project_root"
lang=${1:?usage: submit_s1_multilingual_gpu.sh LANG [VERSION]}
ver=${2:-v1}
cfg=phase6_degraded_corpus/configs/experiments/s1_${lang}_${ver}.json
gen=phase6_degraded_corpus/configs/experiments/s1_${lang}_${ver}_generation.json
run=phase6_degraded_corpus/runs/s1_${lang}_${ver}
py=.venv-phase6-vllm/bin/python
export HF_HOME="$project_root/cache/huggingface" HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false VLLM_WORKER_MULTIPROC_METHOD=spawn
mkdir -p "$run/generations" "$run/scored" "$run/plans"
step() { echo "[$(date -Is)] $*"; }

[[ -s "$run/pools/structural_candidates.jsonl" ]] || { step prepare; $py -m phase6_degraded_corpus.src.selection.select_multilingual_pools prepare --config "$cfg"; }
[[ -s "$run/checker_config.json" ]] || { step score; $py -m phase6_degraded_corpus.src.selection.select_multilingual_pools score --config "$cfg" --device cuda; }
step allocate; $py -m phase6_degraded_corpus.src.selection.select_multilingual_pools allocate --config "$cfg"
checkers="$run/checker_config.json"

[[ -s "$run/scored/fose_groups.jsonl" ]] || { step rules; $py -m phase6_degraded_corpus.src.generation.generate_s1_rules --run-dir "$run" --device cuda; }

# MOD: LLM fronting (A), then rule reorder of the clean text (B) and of the fronted text (AB).
if [[ -s "$run/allocation/mod_graded.jsonl" ]]; then
  [[ -s "$run/generations/mod_fronting.jsonl" ]] || { step mod-generate; $py -m phase6_degraded_corpus.src.generation.generate_mmi_v2 \
    --plan "$run/allocation/mod_graded.jsonl" --config "$gen" --config-id MOD_C2 --output "$run/generations/mod_fronting.jsonl"; }
  [[ -s "$run/scored/mod_fronting.jsonl" ]] || { step mod-score; $py -m phase6_degraded_corpus.src.evaluation.score_mmi_candidates \
    --generations "$run/generations/mod_fronting.jsonl" --plan "$run/allocation/mod_graded.jsonl" --pools-config "$checkers" \
    --output "$run/scored/mod_fronting.jsonl" --device cuda; }
  $py -m phase6_degraded_corpus.src.generation.combine_mod_graded prepare --scored "$run/scored/mod_fronting.jsonl" \
    --plan "$run/allocation/mod_graded.jsonl" --plan-out "$run/plans/mod_reorder_plan.jsonl" --generations-out "$run/generations/mod_reorder.jsonl"
  [[ -s "$run/scored/mod_reorder.jsonl" ]] || { step mod-reorder-score; $py -m phase6_degraded_corpus.src.evaluation.score_mmi_candidates \
    --generations "$run/generations/mod_reorder.jsonl" --plan "$run/plans/mod_reorder_plan.jsonl" --pools-config "$checkers" \
    --output "$run/scored/mod_reorder.jsonl" --device cuda; }
  $py -m phase6_degraded_corpus.src.generation.combine_mod_graded finalize --fronting "$run/scored/mod_fronting.jsonl" \
    --reorders "$run/scored/mod_reorder.jsonl" --output "$run/scored/mod_groups.jsonl"
fi

if [[ -s "$run/allocation/illoc_pair.jsonl" ]]; then
  [[ -s "$run/generations/illoc.jsonl" ]] || { step illoc-generate; $py -m phase6_degraded_corpus.src.generation.generate_mmi_v2 \
    --plan "$run/allocation/illoc_pair.jsonl" --config "$gen" --config-id ILLOC_C1 --output "$run/generations/illoc.jsonl"; }
  [[ -s "$run/scored/illoc.jsonl" ]] || { step illoc-score; $py -m phase6_degraded_corpus.src.evaluation.score_mmi_candidates \
    --generations "$run/generations/illoc.jsonl" --plan "$run/allocation/illoc_pair.jsonl" --pools-config "$checkers" \
    --output "$run/scored/illoc.jsonl" --device cuda; }
fi
step done
