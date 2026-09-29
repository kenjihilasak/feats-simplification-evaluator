# Preliminary automated audit of the random pilot sample

This is a preliminary automated diagnostic review, **not human gold annotation**. It reviews the fixed 50-case sample in [`pilot_random_review.md`](pilot_random_review.md).

## Summary

| Decision | Count | Rate |
|---|---:|---:|
| Valid | 8 | 16% |
| Invalid | 37 | 74% |
| Unsure | 5 | 10% |

Only clear `Valid` decisions should count as provisionally successful. The five `Unsure` cases require a project reviewer.

### Results by dimension

| Dimension | Valid | Invalid | Unsure | Clear-valid rate |
|---|---:|---:|---:|---:|
| EXPL | 2 | 6 | 1 | 22% |
| FLUENCY | 2 | 7 | 0 | 22% |
| ILLOC | 1 | 7 | 0 | 13% |
| MOD | 0 | 3 | 3 | 0% |
| OMIT | 2 | 6 | 1 | 22% |
| SYN | 1 | 8 | 0 | 11% |

**Best so far:** EXPL, FLUENCY, and OMIT are tied at 2 clearly valid cases out of 9 (22%). This comparison applies only to the deliberately stratified diagnostic sample; it does not estimate full-pilot accuracy.

## Case decisions

| Case | Dimension | Automatic result | Decision | Reason |
|---:|---|---|---|---|
| 01 | EXPL | GOOD | **Invalid** | Formatting-only change; no explanation was removed. |
| 02 | EXPL | FAILED | **Invalid** | Simplified and Degraded are identical. |
| 03 | FLUENCY | GOOD | **Invalid** | The Simplified input is already ungrammatical; the edit is not a controlled single error. |
| 04 | EXPL | FAILED | **Invalid** | Simplified and Degraded are identical. |
| 05 | ILLOC | FAILED | **Invalid** | Simplified and Degraded are identical. |
| 06 | FLUENCY | GOOD | **Valid** | One local number-agreement error is introduced. |
| 07 | SYN | GOOD | **Invalid** | The whole sentence is restored, changing more than one lexical choice. |
| 08 | OMIT | MEDIUM | **Invalid** | Only punctuation spacing changed; omitted content was not restored. |
| 09 | OMIT | MEDIUM | **Valid** | One omitted original detail is restored. |
| 10 | ILLOC | GOOD | **Invalid** | Definitions are swapped, changing meaning rather than illocution. |
| 11 | SYN | MEDIUM | **Invalid** | The output is fragmentary and ungrammatical. |
| 12 | SYN | FAILED | **Invalid** | Simplified and Degraded are identical. |
| 13 | EXPL | GOOD | **Invalid** | Only sentence spacing changed; no explanation was removed. |
| 14 | FLUENCY | FAILED | **Invalid** | Simplified and Degraded are identical. |
| 15 | MOD | GOOD | **Unsure** | Sentence recombination is present, but lexical wording also changes. |
| 16 | FLUENCY | MEDIUM | **Invalid** | The model corrects an existing typo instead of degrading fluency. |
| 17 | ILLOC | FAILED | **Invalid** | Simplified and Degraded are identical. |
| 18 | FLUENCY | MEDIUM | **Invalid** | The edit corrupts a proper title and may change content. |
| 19 | OMIT | GOOD | **Unsure** | Only part of the omitted World Cup detail is restored. |
| 20 | MOD | GOOD | **Invalid** | The split is retained; the main change is lexical. |
| 21 | MOD | MEDIUM | **Invalid** | The MOD reversal is plausible, but the Simplified input already contains the `States.It` fluency error. |
| 22 | ILLOC | MEDIUM | **Invalid** | The modal remains; this is not a modality reversal. |
| 23 | OMIT | GOOD | **Invalid** | Only quotation style changes; omitted content is not restored. |
| 24 | FLUENCY | MEDIUM | **Invalid** | Only sentence spacing changes; no grammatical error is introduced. |
| 25 | MOD | MEDIUM | **Unsure** | Clause order moves toward the original, but extra source information is also restored. |
| 26 | ILLOC | GOOD | **Invalid** | May in a date was misdetected as a modal; family information changes. |
| 27 | FLUENCY | GOOD | **Valid** | One local preposition error is introduced without changing facts. |
| 28 | SYN | FAILED | **Invalid** | Simplified and Degraded are identical. |
| 29 | EXPL | MEDIUM | **Valid** | One explanatory addition is removed, returning to the original statement. |
| 30 | FLUENCY | FAILED | **Invalid** | Simplified and Degraded are identical. |
| 31 | SYN | GOOD | **Invalid** | Substantial original information is restored; this is not one synonym reversal. |
| 32 | ILLOC | GOOD | **Invalid** | The edit reverses which parent incubates, changing meaning. |
| 33 | SYN | GOOD | **Invalid** | The complex original term is not restored. |
| 34 | OMIT | MEDIUM | **Invalid** | Only Unicode normalization changes; omitted content is not restored. |
| 35 | FLUENCY | FAILED | **Invalid** | Simplified and Degraded are identical. |
| 36 | EXPL | MEDIUM | **Unsure** | An added location is removed, but the subject form also changes. |
| 37 | OMIT | FAILED | **Invalid** | Simplified and Degraded are identical. |
| 38 | OMIT | FAILED | **Invalid** | Simplified and Degraded are identical. |
| 39 | EXPL | FAILED | **Invalid** | Simplified and Degraded are identical. |
| 40 | EXPL | GOOD | **Valid** | One added descriptive clause is removed while core facts remain. |
| 41 | SYN | FAILED | **Invalid** | Simplified and Degraded are identical. |
| 42 | OMIT | FAILED | **Invalid** | Simplified and Degraded are identical. |
| 43 | MOD | MEDIUM | **Unsure** | The split is reversed, but omitted content is also reintroduced. |
| 44 | SYN | MEDIUM | **Valid** | The expanded simple name is replaced with the harder original acronym. |
| 45 | OMIT | GOOD | **Valid** | One omitted original detail is restored. |
| 46 | ILLOC | MEDIUM | **Valid** | An assertion is changed into a question while retaining its proposition. |
| 47 | SYN | MEDIUM | **Invalid** | Only quotation marks change; no complex synonym is restored. |
| 48 | EXPL | MEDIUM | **Invalid** | Multiple facts are removed and added; this is not one explanation deletion. |
| 49 | ILLOC | MEDIUM | **Invalid** | The whole simplified content is replaced; this is not one illocution change. |
| 50 | MOD | GOOD | **Invalid** | Only spacing and quotation style change; the split is not reversed. |

## Main failure patterns

- exact copies or formatting-only edits;
- a change in the wrong dimension;
- multiple changes instead of one controlled degradation;
- invalid Simplified input;
- incorrect detector cues, especially lexical differences and `May` in dates.
