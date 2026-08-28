# Manual UI smoke test — 2026-08-28

## Result

**Passed.** The standalone Phase 4a review flow was exercised manually in a
browser with the synthetic parsed fixture
`phase4a_gold_standard/tests/fixtures/ui_task.json`.

## Verified workflow

- nominal reviewer login restricted to English;
- candidate `SYN` task claimed and submitted;
- source evidence `physician` stored with lemma, UPOS, XPOS, features, head,
  and dependency relation;
- target evidence `doctor` stored with the same syntax metadata;
- SimAlign link `source[1] -> target[1]` marked `valid`;
- reviewer-facing task remained blinded, while model votes and selection tier
  were preserved in the administrative export;
- submitted annotation became immutable and the queue reached completion;
- deterministic JSONL export and quality report were generated successfully.

## Observed report values

| Measure | Value | Interpretation |
|---|---:|---|
| Submitted tasks | 1 | One fixture completed |
| Strategy correct | 1 | Candidate SYN accepted |
| Determinate correctness | 100% | 1/1 |
| Available SimAlign links | 6 | All fixture links |
| Judged links | 1 | Only the relevant tested link was judged |
| Valid links | 1 | The judged link was accepted |
| Alignment acceptance | 100% | 1 valid / 1 judged |
| Alignment coverage | 16.67% | 1 judged / 6 available |
| Selected evidence tokens | 2 | One source and one target token |

Acceptance and coverage intentionally use different denominators. The result
does not claim that all six links were validated.

## Export identity

- task: `review:en:syn:ui-smoke`
- canonical pair: `pair:en:ui-smoke`
- reviewer: `reviewer-en`
- annotation state: `submitted`
- candidate strategy: `SYN`
- verdict: `correct`
