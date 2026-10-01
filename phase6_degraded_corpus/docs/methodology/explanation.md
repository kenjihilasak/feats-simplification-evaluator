# EXPL degradation (rule-based v1)

[Methodology index](README.md)

**Goal:** make a clean simplification worse by removing one helpful explanation or definition.

**Generator:** deterministic word alignment; one seeded Simplified-only span of at least two tokens containing a content word is deleted, with orphan punctuation cleaned up.

## Automatic checks

- the removed span is absent from the Original and the degraded text is shorter;
- NLI(clean → degraded) entailment is at least 0.5;
- acceptability is at least `min(τ, clean − δ)`.

## Evidence

Pending the blinded `fose_en_v1` human audit.
