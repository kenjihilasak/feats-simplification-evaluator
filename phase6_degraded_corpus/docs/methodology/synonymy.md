# SYN degradation (rule-based v1)

[Methodology index](README.md)

**Goal:** restore one harder Original word or short phrase that means the same as the simple wording.

**Generator:** deterministic word alignment; one seeded replacement block is restored when its mean English `wordfreq` Zipf score is at least 0.5 below the simple side.

**Site exclusions (v2, 28 Oct 2026):** no rule axis uses a pair whose edits touch a quoted span (titles, cited names), and a SYN site is skipped when either side has a capitalised word that does not open a sentence. In the first English review, S019 restored "protagonist" correctly, but the pair also changed the title "Oedipus Rex" to "Oedipus the King", and the reviewer read that as the degradation ([`select_fose_pools.py`](../../src/selection/select_fose_pools.py)).

## Automatic checks

- restored wording occurs in the Original and retains the 0.5 Zipf gap;
- NLI entailment is at least 0.5 in both directions;
- acceptability is at least `min(τ, clean − δ)`.

## Evidence

Pending the blinded `fose_en_v1` human audit.
