# Phase 3b: word alignment

Phase 3b aligns the words of every canonical Phase 2b `original`–`simple`
pair. It is named **3b**, rather than Phase 4, because it is a second,
independent analysis derived from the same consolidated Phase 2b corpus as
Phase 3a (strategy detection):

```text
Phase 2b canonical pairs
├── Phase 3a strategy detection
└── Phase 3b word alignment → features/edit operations for FEATS models
```

The alignment is a sidecar keyed by `canonical_pair_id`. It never copies or
modifies the canonical texts. Its input is exactly
`phase2b_consolidation/data/<language>/feats_consolidated.jsonl`; every run
stores the relative input path, line count and SHA-256 in `input_manifest.json`.

## v2 method

Word alignment uses SimAlign 0.4 with `xlm-roberta-large`, hidden layer 8, BPE
embeddings and `itermax` matching. Tokenization is selected per language:

| Languages | Tokenizer | Reason |
|---|---|---|
| `ar` | CAMeL Tools `calima-msa-r13`, ATB clitic boundaries | Arabic clitics need morphological segmentation. v2 applies only boundaries that match the literal surface, so normalized or misanalysed stems never replace corpus text. |
| `ja` | spaCy Japanese + Sudachi, explicit split mode A | Japanese cannot be reliably segmented on whitespace. |
| `ur` | Stanza UDTB tokenizer | Urdu requires a trained, script-aware tokenizer rather than generic spaCy rules. |
| `sl` | Stanza SSJ tokenizer | Uses a trained Slovenian tokenizer and separates punctuation consistently. |
| all others | language-specific `spacy.blank(...)` | The rule-based language tokenizers are suitable for the remaining covered languages. |

The aligner is unchanged from v1 so tokenization is the controlled correction.
The previous local v1 run remains a baseline; v2 writes to a new run directory
and never overwrites it.

## Output contract

One line in
`runs/<run_id>/<language>/alignments/feats_word_alignments.jsonl` represents one
Phase 2b canonical pair in input order. Important fields are:

| Field | Meaning |
|---|---|
| `id`, `canonical_pair_id` | Stable join key back to Phase 2b and forward to FEATS training data. |
| `input_schema`, `input_index`, `*_text_sha256` | Per-record provenance without duplicating the canonical text. |
| `tokenizer_id` | Exact language-specific tokenizer recorded for the pair. |
| `original_tokens`, `simple_tokens` | Surface-preserving tokens passed to SimAlign. |
| `*_token_offsets` | Exact half-open character offsets into the Phase 2b text. |
| `*_orthographic_tokens` | Unsplit surface tokens; identical to alignment tokens except where Arabic clitics are split. |
| `*_token_parent_indices` | Maps every alignment token to its orthographic parent. |
| `alignment` | Sorted unique `[original_index, simple_index]` links. |
| `alignment_pharaoh` | The same links as `i-j` pairs. |
| `unaligned_*_indices` | Tokens with no alignment link. |
| `n_*_subwords` | Encoder-length audit fields. |
| `status` | `aligned` or `skipped_model_length`. |

A side longer than 510 encoder subwords is recorded as
`skipped_model_length`; it is never silently interpreted as deletions. The v2
validator reconstructs every alignment and orthographic token from its Phase
2b character span, checks parent mappings, IDs/order, tokenizer identity,
alignment bounds and artifact hashes.

## Setup and tests

The runtime is pinned in `requirements-runtime.txt`. The setup script installs
the Python packages and downloads the CAMeL Arabic model plus the Stanza Urdu
and Slovenian tokenizers into the ignored local `cache/` directory:

```bash
bash phase3b_word_alignment/jobs/setup_environment.sh
/scratch/pjbd103/miniconda3/envs/SimAlign/bin/python -m pytest \
  phase3b_word_alignment/tests
```

## Smoke and full v2 runs

The smoke run aligns and validates two pairs in each of the 12 languages:

```bash
sbatch phase3b_word_alignment/jobs/submit_smoke_gpu.sh
```

After it passes, the full run uses one resumable GPU array task per language:

```bash
sbatch phase3b_word_alignment/jobs/submit_full_gpu.sh
```

The full configuration pins 854,486 Phase 2b pairs. English (348,520), French
(245,746) and Russian (150,056) are the largest tasks. Run artifacts, downloaded
models and Slurm logs are intentionally ignored by Git; code, configs, tests and
documentation are versioned.

## Completed v2 run

Run `2026-08-23_simalign_xlmr_large_itermax_full_v2` completed all 12 Slurm
array tasks and passed a second independent validation:

- 854,486/854,486 Phase 2b pairs observed with zero contract errors;
- 854,484 pairs aligned and two English pairs explicitly marked
  `skipped_model_length` (encoder sides of 518 and 933/751 subwords);
- 15,100,065 word-alignment links;
- exact source-span and orthographic-parent reconstruction for every token;
- no incomplete `.partial` outputs.

The ignored local run occupies 2.5 GB. Its per-language `input_manifest.json`,
`run_config.json`, `summary.json` and `validation.json` files contain hashes,
package versions, tokenizer identity and counts needed to audit or consume the
sidecars as FEATS model-training inputs.
