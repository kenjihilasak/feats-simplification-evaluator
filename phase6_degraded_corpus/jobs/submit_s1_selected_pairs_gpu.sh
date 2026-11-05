#!/usr/bin/env bash
#SBATCH --job-name=phase6-s1-sel
#SBATCH --partition=gpu
#SBATCH --gres=gpu:l40s:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=02:00:00
#SBATCH --output=phase6_degraded_corpus/logs/s1_sel_%j.out
#SBATCH --error=phase6_degraded_corpus/logs/s1_sel_%j.err
# v2 degradations for pairs chosen in an earlier round (after build_selected_pairs_run.py prepare).
# Usage: sbatch phase6_degraded_corpus/jobs/submit_s1_selected_pairs_gpu.sh RUN_NAME BASE_RUN_NAME
# The clean texts are scored with the base run's checkers; its thresholds are kept (not recalibrated on a few pairs).
set -euo pipefail
project_root=/scratch/pjbd103/feats-simplification-evaluator
cd "$project_root"
name=${1:?usage: RUN_NAME BASE_RUN_NAME}; base=${2:?}
R=phase6_degraded_corpus/runs; run=$R/$name
cfg=phase6_degraded_corpus/configs/experiments/$name.json
gen=phase6_degraded_corpus/configs/experiments/${base}_generation.json
py=.venv-phase6-vllm/bin/python
export HF_HOME="$project_root/cache/huggingface" HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false VLLM_WORKER_MULTIPROC_METHOD=spawn
mkdir -p "$run/generations" "$run/scored" "$run/plans"
step() { echo "[$(date -Is)] $*"; }
[[ -s "$run/pools/clean_quality_scores.jsonl" ]] || { step score; $py -m phase6_degraded_corpus.src.selection.select_multilingual_pools score --config "$cfg" --device cuda; }
cp "$R/$base/checker_config.json" "$run/checker_config.json"
step allocate; $py -m phase6_degraded_corpus.src.annotation.build_selected_pairs_run allocate --config "$cfg" --chosen "$run/chosen_pairs.json" --run-dir "$run"
checkers="$run/checker_config.json"
step rules; $py -m phase6_degraded_corpus.src.generation.generate_s1_rules --run-dir "$run" --device cuda
if [[ -s "$run/allocation/mod_graded.jsonl" ]]; then
  $py -m phase6_degraded_corpus.src.generation.generate_mmi_v2 --plan "$run/allocation/mod_graded.jsonl" --config "$gen" --config-id MOD_C2 --output "$run/generations/mod_fronting.jsonl"
  $py -m phase6_degraded_corpus.src.evaluation.score_mmi_candidates --generations "$run/generations/mod_fronting.jsonl" --plan "$run/allocation/mod_graded.jsonl" --pools-config "$checkers" --output "$run/scored/mod_fronting.jsonl" --device cuda
  $py -m phase6_degraded_corpus.src.generation.combine_mod_graded prepare --scored "$run/scored/mod_fronting.jsonl" --plan "$run/allocation/mod_graded.jsonl" --plan-out "$run/plans/mod_reorder_plan.jsonl" --generations-out "$run/generations/mod_reorder.jsonl"
  $py -m phase6_degraded_corpus.src.evaluation.score_mmi_candidates --generations "$run/generations/mod_reorder.jsonl" --plan "$run/plans/mod_reorder_plan.jsonl" --pools-config "$checkers" --output "$run/scored/mod_reorder.jsonl" --device cuda
  $py -m phase6_degraded_corpus.src.generation.combine_mod_graded finalize --fronting "$run/scored/mod_fronting.jsonl" --reorders "$run/scored/mod_reorder.jsonl" --output "$run/scored/mod_groups.jsonl"
fi
if grep -q -E '"(MEANING|FLUENCY)"' "$run/chosen_pairs.json"; then
  m=phase6_degraded_corpus.src.generation.generate_meaning_fluency_ml
  step mf-candidates; $py -m $m candidates --run-dir "$run"
  [[ -s "$run/meaning_fluency/contradict_plan.jsonl" ]] && $py -m phase6_degraded_corpus.src.generation.generate_mmi_v2 \
    --plan "$run/meaning_fluency/contradict_plan.jsonl" --config "$gen" --config-id ILLOC_C1 --output "$run/generations/contradict.jsonl"
  step mf-score; $py -m $m score --run-dir "$run" --device cuda
  step mf-select; $py -m $m select --run-dir "$run"
fi
step done
