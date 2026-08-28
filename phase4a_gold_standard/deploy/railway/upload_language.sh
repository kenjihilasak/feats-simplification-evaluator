#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <language> <materialized-annotation_tasks.jsonl>" >&2
  exit 2
fi

language=$1
payload=$2

case "${language}" in
  ar|ca|de|en|es|fr|it|ja|pt-BR|ru|sl|ur) ;;
  *)
    echo "Unsupported language: ${language}" >&2
    exit 2
    ;;
esac

if [[ ! -s "${payload}" ]]; then
  echo "Payload is missing or empty: ${payload}" >&2
  exit 2
fi

if ! command -v railway >/dev/null 2>&1; then
  echo "Railway CLI is required" >&2
  exit 2
fi

service=${PHASE4A_RAILWAY_SERVICE:-phase4a-review}
remote_path="/tmp/phase4a-annotation_tasks.jsonl"
railway service files --service "${service}" upload --overwrite \
  "${payload}" "${remote_path}"
railway ssh --service "${service}" -- \
  python -m phase4a_gold_standard.backend import-tasks "${remote_path}"
railway ssh -- python -m phase4a_gold_standard.backend progress
