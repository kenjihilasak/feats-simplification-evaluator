# SYN degradation (rule-based v1)

[Methodology index](README.md)

**Goal:** restore one harder Original word or short phrase that means the same as the simple wording.

**Generator:** deterministic word alignment; one seeded replacement block is restored when its mean English `wordfreq` Zipf score is at least 0.5 below the simple side.

## Automatic checks

- restored wording occurs in the Original and retains the 0.5 Zipf gap;
- NLI entailment is at least 0.5 in both directions;
- acceptability is at least `min(τ, clean − δ)`.

## Evidence

Pending the blinded `fose_en_v1` human audit.
