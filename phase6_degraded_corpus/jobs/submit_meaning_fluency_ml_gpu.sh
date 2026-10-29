#!/usr/bin/env bash
#SBATCH --job-name=phase6-mf-ml
#SBATCH --partition=gpu
#SBATCH --gres=gpu:l40s:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=03:00:00
#SBATCH --output=phase6_degraded_corpus/logs/mf_ml_%j.out
#SBATCH --error=phase6_degraded_corpus/logs/mf_ml_%j.err
# Graded MEANING and FLUENCY groups for one non-English language, from its v2 pool.
# Usage (from the project root): sbatch phase6_degraded_corpus/jobs/submit_meaning_fluency_ml_gpu.sh LANG [VERSION]
set -euo pipefail
project_root=/scratch/pjbd103/feats-simplification-evaluator
cd "$project_root"
lang=${1:?usage: submit_meaning_fluency_ml_gpu.sh LANG [VERSION]}
ver=${2:-v2}
run=phase6_degraded_corpus/runs/s1_${lang}_${ver}
gen=phase6_degraded_corpus/configs/experiments/s1_${lang}_${ver}_generation.json
py=.venv-phase6-vllm/bin/python
export HF_HOME="$project_root/cache/huggingface" HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false VLLM_WORKER_MULTIPROC_METHOD=spawn
mkdir -p "$run/generations" "$run/scored"
step() { echo "[$(date -Is)] $*"; }
m=phase6_degraded_corpus.src.generation.generate_meaning_fluency_ml
step candidates; $py -m $m candidates --run-dir "$run"
# Contradictions from the LLM (Qwen, the English MEANING generator) for pairs without a number to change.
[[ -s "$run/generations/contradict.jsonl" ]] || { step contradict; $py -m phase6_degraded_corpus.src.generation.generate_mmi_v2 \
  --plan "$run/meaning_fluency/contradict_plan.jsonl" --config "$gen" --config-id ILLOC_C1 --output "$run/generations/contradict.jsonl"; }
step score; $py -m $m score --run-dir "$run" --device cuda
step select; $py -m $m select --run-dir "$run"
step done
