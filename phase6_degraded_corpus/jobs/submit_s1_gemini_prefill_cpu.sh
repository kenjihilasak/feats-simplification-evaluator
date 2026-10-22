#!/usr/bin/env bash
#SBATCH --job-name=feats-s1-gemini
#SBATCH --partition=nodes
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch/pjbd103/feats-simplification-evaluator/phase6_degraded_corpus/logs/s1_gemini_%j.out
#SBATCH --error=/scratch/pjbd103/feats-simplification-evaluator/phase6_degraded_corpus/logs/s1_gemini_%j.err
set -euo pipefail
project=/scratch/pjbd103/feats-simplification-evaluator
# Usage: sbatch submit_s1_gemini_prefill_cpu.sh [en|es|fr] [delay-seconds] [gemini|openai]; resumable.
lang=${1:-en}; delay=${2:-15}; provider=${3:-gemini}
case "${provider}" in gemini) out=s1_gemini_3p8_flash.jsonl ;; openai) out=s1_openai_gpt54mini.jsonl ;; *) echo "provider must be gemini or openai" >&2; exit 2 ;; esac
secret=/scratch/pjbd103/.secrets/${provider}_api_key
[[ -s "${secret}" ]] || { echo "Missing ${provider} key file" >&2; exit 2; }
[[ "$(stat -c %a "${secret}")" == "600" ]] || { echo "${provider} key must have mode 600" >&2; exit 2; }
case "${lang}" in en) run=annotation_v1 ;; es|fr) run=annotation_${lang}_v1 ;; *) echo "language must be en, es or fr" >&2; exit 2 ;; esac
cd "${project}"
export GEMINI_API_KEY_FILE="${secret}" OPENAI_API_KEY_FILE="${secret}"
.venv-phase4a/bin/python -m phase6_degraded_corpus.src.annotation.prefill_with_llm \
  --input "phase6_degraded_corpus/runs/${run}/s1_items.jsonl" \
  --input "phase6_degraded_corpus/runs/${run}/s1_controls.jsonl" \
  --provider "${provider}" \
  --output "phase6_degraded_corpus/runs/${run}/${out}" \
  --delay "${delay}"
