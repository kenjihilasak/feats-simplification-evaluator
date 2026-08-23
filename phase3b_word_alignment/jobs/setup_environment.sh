#!/bin/bash

set -euo pipefail

PYTHON_BIN=/scratch/pjbd103/miniconda3/envs/SimAlign/bin/python
PROJECT_ROOT=/scratch/pjbd103/feats-simplification-evaluator
CAMELTOOLS_DATA=${PROJECT_ROOT}/phase3b_word_alignment/cache/camel_tools
STANZA_RESOURCES_DIR=${PROJECT_ROOT}/phase3b_word_alignment/cache/stanza

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "Missing SimAlign environment: ${PYTHON_BIN}" >&2
  exit 1
fi

mkdir -p "${CAMELTOOLS_DATA}" "${STANZA_RESOURCES_DIR}"
"${PYTHON_BIN}" -m pip install -r \
  "${PROJECT_ROOT}/phase3b_word_alignment/requirements-runtime.txt"
CAMELTOOLS_DATA="${CAMELTOOLS_DATA}" \
  /scratch/pjbd103/miniconda3/envs/SimAlign/bin/camel_data \
  -i disambig-mle-calima-msa-r13
"${PYTHON_BIN}" -c \
  "import stanza; stanza.download('ur', package='udtb', processors='tokenize', model_dir='${STANZA_RESOURCES_DIR}'); stanza.download('sl', package='ssj', processors='tokenize', model_dir='${STANZA_RESOURCES_DIR}')"
CAMELTOOLS_DATA="${CAMELTOOLS_DATA}" STANZA_RESOURCES_DIR="${STANZA_RESOURCES_DIR}" \
  "${PYTHON_BIN}" -c \
  "import spacy, simalign, stanza; spacy.blank('ja'); from camel_tools.disambig.mle import MLEDisambiguator; MLEDisambiguator.pretrained('calima-msa-r13')"
