# OMIT degradation (rule-based v1)

[Methodology index](README.md)

**Goal:** make a clean simplification worse by restoring one detail that it usefully omitted.

**Generator:** deterministic word alignment; one seeded Original-only content span is reinserted at its aligned position. Spacing and a/an are repaired.

## Automatic checks

- the span occurs in the Original and makes the degraded text longer;
- NLI(degraded → clean) entailment is at least 0.5;
- acceptability is at least `min(τ, clean − δ)`.

## Evidence

Pending the blinded `fose_en_v1` human audit.
