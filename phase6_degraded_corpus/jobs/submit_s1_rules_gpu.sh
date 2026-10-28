#!/usr/bin/env bash
#SBATCH --job-name=phase6-s1-rules
#SBATCH --partition=gpu
#SBATCH --gres=gpu:l40s:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=phase6_degraded_corpus/logs/s1_rules_%j.out
#SBATCH --error=phase6_degraded_corpus/logs/s1_rules_%j.err
# Re-run only the OMIT/SYN/EXPL rule step of existing runs, e.g. after a fix to the rules.
# Usage (from the project root): sbatch phase6_degraded_corpus/jobs/submit_s1_rules_gpu.sh VERSION LANG [LANG...]
set -euo pipefail
project_root=/scratch/pjbd103/feats-simplification-evaluator
cd "$project_root"
ver=${1:?usage: submit_s1_rules_gpu.sh VERSION LANG [LANG...]}; shift
py=.venv-phase6-vllm/bin/python
export HF_HOME="$project_root/cache/huggingface" HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false
for lang in "$@"; do
  run=phase6_degraded_corpus/runs/s1_${lang}_${ver}
  echo "[$(date -Is)] rules $lang"
  $py -m phase6_degraded_corpus.src.generation.generate_s1_rules --run-dir "$run" --device cuda
done
echo "[$(date -Is)] done"
