# Phase 4a annotation guide

## Unit of review

Each task is one original–simplification pair with exactly one candidate
strategy. Judge the candidate from the sentence pair itself. Model votes and
confidence tiers are intentionally hidden.

## Strategy evidence

| Code | Question | Required evidence |
|---|---|---|
| SYN | Was a complex/specific expression replaced by a simpler equivalent? | replaced source expression + target replacement |
| MOD | Was the same information reorganized or reframed? | source information + redistributed target information |
| COMP | Was content preserved in a shorter construction? | expanded source content + compressed target content |
| EXPL | Was an expression or implicit content made explicit? | source anchor + explanatory target content |
| SYNT | Did the construction change while content was preserved? | source construction + corresponding target construction |
| OMIT | Was source material removed? | omitted source material only |

Select the smallest complete span that supports the judgment. Multi-token
evidence is allowed. POS and dependency information are collected
automatically from the selected tokens.

## Verdicts

- **Correct:** the candidate strategy is present. Select its required evidence.
- **Incorrect:** the candidate is absent. Select a corrected strategy when one
  clear alternative applies; use `NONE`, `MULTIPLE`, or `OTHER` when
  appropriate. If the correction is one of the six defined strategies, select
  its evidence.
- **Uncertain:** the evidence is genuinely ambiguous or specialist/contextual
  information is missing. Explain the ambiguity briefly in notes.
- **Skip:** use only for a technical or adjudication blocker such as corrupted
  text, unusable parse, wrong language, or a pair requiring escalation.

Do not use `uncertain` merely because the example is difficult, and do not
use `skip` as a negative strategy judgment.

## Alignment review

Existing curves are SimAlign suggestions:

- mark a curve **valid** when it connects corresponding words or spans;
- mark it **invalid** when the correspondence is wrong;
- add a human link when a relevant correspondence is missing.

Only judged links enter the acceptance-rate denominator. Coverage is reported
separately as judged SimAlign links divided by all available SimAlign links.
This distinction prevents unreviewed links from being counted as correct.

Evidence and link judgments are related but independent: select every word
needed to justify the strategy even when no SimAlign link connects it.

## Dependency displays

The upper tree belongs to the original sentence and the mirrored lower tree to
the simplification. A parse warning means the syntax should not be trusted;
review the text and links, add a note, and skip only when the task cannot be
judged responsibly. Arabic and Urdu render right-to-left; Japanese tokens are
shown without injected spaces.

## Saving and submission

Drafts autosave and remain editable. Submission is final in campaign v1 and
creates an immutable revision/audit event. Before submitting, check:

1. the verdict matches the candidate strategy;
2. required source/target evidence is selected;
3. relevant SimAlign links have been judged;
4. any missing correspondence has been added;
5. notes explain uncertainty, unusual syntax, or a correction when useful.

Use one named account only. Never share credentials or review a language not
assigned to that account.
