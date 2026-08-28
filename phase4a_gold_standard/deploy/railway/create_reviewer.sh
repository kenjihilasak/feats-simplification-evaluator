#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "Usage: $0 <language> <username> <display-name>" >&2
  exit 2
fi

language=$1
username=$2
display_name=$3

case "${language}" in
  ar|ca|de|en|es|fr|it|ja|pt-BR|ru|sl|ur) ;;
  *)
    echo "Unsupported language: ${language}" >&2
    exit 2
    ;;
esac

railway ssh -- python -m phase4a_gold_standard.backend create-user \
  --username "${username}" \
  --display-name "${display_name}" \
  --role reviewer \
  --language "${language}"
