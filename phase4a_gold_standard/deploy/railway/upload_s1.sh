#!/usr/bin/env bash
set -euo pipefail
if [[ $# -lt 3 || $# -gt 4 ]]; then
  echo "Usage: $0 <s1_items.jsonl> <s1_controls.jsonl> <english-reviewer-username> [suggestions.jsonl]" >&2
  exit 2
fi
items=$1; controls=$2; reviewer=$3; suggestions=${4:-}
for path in "${items}" "${controls}"; do [[ -s "${path}" ]] || { echo "Missing or empty: ${path}" >&2; exit 2; }; done
service=${PHASE4A_RAILWAY_SERVICE:-phase4a-review}
railway service files --service "${service}" upload --overwrite "${items}" /tmp/s1_items.jsonl
railway service files --service "${service}" upload --overwrite "${controls}" /tmp/s1_controls.jsonl
railway ssh --service "${service}" -- python -m phase4a_gold_standard.backend.s1_cli load /tmp/s1_items.jsonl /tmp/s1_controls.jsonl --reviewer "${reviewer}" --seed 4107
if [[ -n "${suggestions}" ]]; then
  [[ -s "${suggestions}" ]] || { echo "Missing or empty: ${suggestions}" >&2; exit 2; }
  railway service files --service "${service}" upload --overwrite "${suggestions}" /tmp/s1_suggestions.jsonl
  railway ssh --service "${service}" -- python -m phase4a_gold_standard.backend.s1_cli load-suggestions /tmp/s1_suggestions.jsonl
fi
railway ssh --service "${service}" -- python -m phase4a_gold_standard.backend.s1_cli progress
