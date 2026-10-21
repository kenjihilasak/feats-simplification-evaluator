#!/bin/sh
set -eu

port=${PORT:-8000}
database=${PHASE4A_DATABASE:-/data/gemma_anchored_strict_v2.sqlite3}
campaign=${PHASE4A_CAMPAIGN_ID:-gemma-anchored-strict-v2}
s1_database=${S1_DATABASE:-/data/s1_validation_v1.sqlite3}
session_secret=${PHASE4A_SESSION_SECRET:-}

if [ "${#session_secret}" -lt 32 ]; then
  echo "PHASE4A_SESSION_SECRET must contain at least 32 characters" >&2
  exit 2
fi

if [ -n "${RAILWAY_ENVIRONMENT:-}" ] && [ "${RAILWAY_VOLUME_MOUNT_PATH:-}" != "/data" ]; then
  echo "Attach a Railway volume at /data before starting Phase 4a" >&2
  exit 2
fi

case "${database}" in
  /data/*) ;;
  *)
    if [ -n "${RAILWAY_ENVIRONMENT:-}" ]; then
      echo "PHASE4A_DATABASE must be stored under /data on Railway" >&2
      exit 2
    fi
    ;;
esac

export PHASE4A_DATABASE="${database}"
export PHASE4A_CAMPAIGN_ID="${campaign}"
export PHASE4A_COOKIE_SECURE="${PHASE4A_COOKIE_SECURE:-1}"
export S1_DATABASE="${s1_database}"
mkdir -p "$(dirname "${database}")" "$(dirname "${s1_database}")"

python -m phase4a_gold_standard.backend init
python -m phase4a_gold_standard.backend.s1_cli init
exec python -m phase4a_gold_standard.backend serve --host 0.0.0.0 --port "${port}"
