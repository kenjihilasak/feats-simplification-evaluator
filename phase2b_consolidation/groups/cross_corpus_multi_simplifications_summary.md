# Cross-corpus originals with multiple simplifications

Input: `phase2b_consolidation/data` (post-cleaning Phase 2b data).

A group is included when the same `canonical_original_id` retains at least two distinct
`canonical_pair_id` values and provenance from at least two distinct `(source, corpus)`
combinations after Phase 2a cleaning.

- Phase 2b pairs scanned: **854,486**
- Qualifying canonical originals: **3,086**
- Distinct simplifications in those groups: **7,215**

| Language | Canonical originals | Distinct simplifications |
|---|---:|---:|
| en | 449 | 1,898 |
| fr | 2 | 6 |
| ja | 2,635 | 5,311 |

## Fields

| Field | Description |
|---|---|
| `group_id` | Alias of `canonical_original_id`. |
| `canonical_original_id` | Shared ID of the original sentence. |
| `language` | Language code. |
| `original` | Canonicalized original sentence. |
| `distinct_simplification_count` | Number of retained simplifications in the group. |
| `source_count` | Number of distinct sources represented. |
| `corpus_count` | Number of distinct `(source, corpus)` combinations. |
| `sources` | Sources represented in the group. |
| `corpora` | Corpus combinations represented in the group. |
| `simplifications` | Simplified texts, pair IDs, retention counts, and provenance. |

Each `simplifications[]` item contains `canonical_pair_id`, `simple`, the two
occurrence counts, `partially_retained`, `sources`, `corpora`,
`upstream_splits`, and `provenance` with the meanings documented in
`phase2b_consolidation/README.md`.
