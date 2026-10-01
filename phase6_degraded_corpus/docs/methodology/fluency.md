# FLUENCY degradation (rule-based v1)

[Methodology index](README.md)

**Goal:** introduce one obvious local grammar error while preserving meaning and all other qualities.

**Generator:** deterministic rules; no LLM. One seeded site is selected for subject–verb agreement, article deletion, preposition confusion, or adjacent adjective/noun or auxiliary/verb order.

## Automatic checks

- exactly one edit block and no no-op;
- acceptability decreases by at least 0.10;
- NLI entailment is at least 0.5 in both directions.

## Evidence

Pending the blinded `fose_en_v1` human audit.
