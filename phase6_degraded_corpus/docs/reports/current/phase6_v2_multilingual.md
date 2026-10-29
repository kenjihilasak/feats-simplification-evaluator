# Phase 6 v2: degradations for seven languages

**Date:** 28–29 October 2026 · **Scope:** all seven FEATS axes (MEANING, FLUENCY, OMIT, SYN, EXPL, MOD, ILLOC) in English, Spanish, French, Italian, Catalan, Russian and Arabic. English MEANING and FLUENCY are the validated v2 groups; the other languages get them from [`generate_meaning_fluency_ml.py`](../../../src/generation/generate_meaning_fluency_ml.py).

## What changed from v1

| Axis | v1 | v2 |
|---|---|---|
| ILLOC | Inject an act into a statement: statement → imperative, or a hedge ("is" → "might be") | **v4:** a direct act already in the text is made indirect: instruction → impersonal statement, question → embedded question, "you" → impersonal. Statements host nothing. |
| MOD | Mild = fronting **or** sentence reorder, at random; strong = both | Mild = fronting (secondary information first); strong = fronting + reorder |
| SYN, OMIT, EXPL | Any edit site | No pair whose edits touch a quoted span; no SYN site on a capitalised word inside a sentence |

Why:
- **ILLOC:** in the first English review the reviewer preferred the imperative in both items (a direct instruction is an Easy-to-Read improvement), and the hedge changes meaning (scored under MEANING, team decision). Definition and checks: [illocution.md](../../methodology/illocution.md).
- **MOD:** the review tied mild and strong; a reorder alone can be as disruptive as both edits ([modulation.md](../../methodology/modulation.md)).
- **SYN:** S019 restored "protagonist" correctly, but the pair also changed the title "Oedipus Rex", which the reviewer read as the degradation ([synonymy.md](../../methodology/synonymy.md)).

## Output

Valid items per language and axis. Files: `runs/s1_<lang>_v2/final/phase6_corpus.jsonl`, one record per original with a target score per version (pairs: clean 1.0, degraded 0.0; MOD and graded rule groups: clean 1.0, mild 0.5, strong 0.0; MEANING and FLUENCY: 1.0 / 0.67 / 0.33 / 0.0 as in English v2).

| Language | Corpora | MEANING | FLUENCY | OMIT | SYN | EXPL | MOD | ILLOC | Total |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| English | WikiAutoEN, ASSET | 4,514 | 7,813 | 137 | 98 | 65 | 147 | 105 | 12,879 |
| French | WikiLargeFR, CLEAR | 575 | 489 | 149 | 98 | 152 | 150 | 61 | 1,674 |
| Russian | RuWikiLarge, RSSE, RuAdapt | 591 | 369 | 145 | 107 | 59 | 159 | 165 | 1,595 |
| Italian | PaCCSS-IT, iDEM, Terence, Teacher, AdminIt… | 430 | 478 | 57 | 56 | 0 | 25 | 146 | 1,192 |
| Catalan | iDEM | 116 | 103 | 0 | 3 | 0 | 19 | 32 | 273 |
| Spanish | iDEM | 53 | 48 | 4 | 4 | 1 | 19 | 4 | 133 |
| Arabic | Saaq al-Bambuu | 41 | 32 | 25 | 6 | 0 | 0 | 0 | 104 |

These are pilot-scale allocations (MEANING and FLUENCY: 600 pairs per language; at most 300 MOD and 240 ILLOC candidates, as in v1); larger quotas in `configs/experiments/s1_<lang>_v2.json` and `--size` scale English, French, Russian and Italian. Zero cells mean the corpus has no eligible pair, not a failure: EXPL needs an inserted gloss, MOD a dependent sentence pair, ILLOC a direct act on the reader.

## MEANING and FLUENCY outside English

The English recipes, rebuilt on Universal Dependencies labels and per-language tables ([`generate_meaning_fluency_ml.py`](../../../src/generation/generate_meaning_fluency_ml.py)):

| Level | MEANING | FLUENCY |
|---|---|---|
| 1.0 | clean; original copy; neutral trim ("también", "aussi", "anche", "также"…, an empty parenthetical) | clean; original copy |
| 0.67 | mild loss: an adjective, appositive, adverb, short peripheral oblique, relative clause, final coordinated clause or intensifier deleted | minor: an article dropped or a preposition swapped (es "de"→"en", ru "в"→"на", ar "في"→"على") |
| 0.33 | major loss: a non-first sentence deleted | major: article agreement broken ("les problemes"), auxiliary+verb or preposition+noun swapped, or two minor errors |
| 0.0 | contradiction: a number or year changed by rule, or a negation/antonym from Qwen ("лучше" → "хуже"), NLI contradiction ≥ 0.5 | severe: three errors |

As in English, MEANING candidates must not contradict (except at 0.0) and must remove content; FLUENCY errors are not selected with the acceptability model (the baseline its scorer must beat), and NLI must confirm the meaning is kept. Russian and Arabic have no articles, so their FLUENCY errors are preposition swaps and word order.

## Shortcut audit

A cross-validated logistic model predicts which of two versions scores higher from shallow differences only (length, sentences, question mark, commas, overlap with the Original); AUC above 0.70 means a scorer could rank without reading ([`audit_phase6_corpus.py`](../../../src/evaluation/audit_phase6_corpus.py), results in [`phase6_v2_shortcut_audit.json`](phase6_v2_shortcut_audit.json)).

| Cue | Axes | Before | After | Action |
|---|---|---|---|---|
| Comma | MOD | 0.71–0.87 | 0.52–0.64 | Fronting added a comma after the fronted phrase; the surplus comma is removed at export (optional after a fronted adverbial in every v2 language). Fronted relative clauses are dropped. |
| Rewording / length | ILLOC | 0.70–0.94 | EN 0.68, RU 0.82, FR 0.85, IT 0.92 | A control version (score 1.0) rewords the sentence but keeps the act direct ("Note that…" → "Remember that…"); 373 of 513 ILLOC items have one. Question marks remain a cue by definition: a direct question *is* the direct act. |
| Commas | OMIT | 0.77–0.98 (gate without length) | unchanged | Mostly definitional: the omitted details are usually comma-delimited appositives and asides, so restoring one restores its commas. |
| Overlap with the Original | MEANING, FLUENCY, SYN, OMIT | 0.72–1.0 | unchanged | Definitional: losing content or adding errors lowers overlap, and SYN/OMIT degradations move back toward the Original. English MEANING, built the same way, beat NLI against human ratings. |

ILLOC therefore still carries a lexical cue in French, Italian and Russian; a scorer trained on it should be checked against the controls before use.

## Illocution examples

| Language | Clean | Degraded |
|---|---|---|
| EN | Use soap and warm water. | Soap and warm water should be used. |
| EN | Where did the name 'foxtrot' come from? | The question is where the name 'foxtrot' came from. |
| EN | Your nervous system compares your eye's response to light… | The nervous system compares the eye's response to light… |
| FR | Veuillez ne pas renommer ou supprimer ces classes. | Les classes ne doivent pas être renommées ou supprimées. |
| IT | Lavare e tritare il prezzemolo. | Il prezzemolo deve essere lavato e tritato. |
| IT | Come posso uscire da questa situazione? | Si chiede come si possa uscire da questa situazione. |
| CA | Podeu presentar una queixa quan penseu que… | Es pot presentar una queixa quan es pensa que… |
| RU | Используйте этот шаблон, когда вы ссылаетесь… | Этот шаблон следует использовать при ссылке… |

Direct acts are rare in encyclopedic text: about 2% of the English pool (237 of 14,142 pairs), mostly generic "you". Administrative texts (Catalan iDEM, Italian AdminIt), recipes and instructions (PaCCSS-IT) and Wikipedia help pages (French, Russian) supply most of the other languages' items. Narrative corpora (Saaq al-Bambuu, Terence, RuAdaptFairytales) are excluded: there a question or "you" is a character speaking.

## Problems found and fixed while building v2

| Problem | Effect | Fix |
|---|---|---|
| English bare-VB roots ("There can also be…") taken as imperatives | false ILLOC hosts | an imperative has no subject, expletive or modal; only adverbials precede it |
| Spanish/Italian pro-drop ("Declarará…", "Terminan…") taken as imperatives | false hosts | no future/past/conditional or plural indicative; the tú form only when the text addresses the reader |
| French names ("Simmons", "Duracell", "Xena") tagged as imperatives once lowercased | false hosts | lexical tests; every proper noun of the clean text must survive the edit |
| The model answered questions ("Does any subset sum to zero?" → "A subset sums to zero.") or used them as subjects | meaning change, ungrammatical | prompts show embedded questions; the check requires a verb of asking + if/wh-word |
| The model repaired the clean text ("esta" → "está", "evalúa" → "evalúan") or changed every `"` into `'` | a cue unrelated to the axis | checks reject accent-only edits and changed quotation marks |
| Broken Catalan from the 7B model ("es demdement", "heuen", "es utilitzen") | fluency errors in ILLOC | every new word must exist (wordfreq); Catalan elision check |
| Few-shot examples serialised with `\u` escapes | Russian MOD output ran out of tokens (1 group of 300) | plain Unicode; Russian MOD now 164 groups |
| OMIT restored a span before the final period without a space ("sentieret", "1979en") | glued words in the degraded text | `splice` adds the leading space |
| English "an United", "an university", "an 1843" → "a 1843" | article errors in the degraded text | article rule follows the spoken sound |

## Affects the live v1 rounds

The glued-word bug is in the **French S1 round already in the interface**: 21 of the 60 French OMIT items have one degraded version with a glued word (for example FR-S015 "sentieret", FR-S016 "1979en", FR-S008 "reliefou"), and one Spanish item (ES-S086 "directasde"). A reviewer can spot the degraded version from the typo alone, so those answers measure fluency, not omission. The live interface is left unchanged (replacing items under a reviewer would change what earlier answers refer to); instead the 22 case ids are listed in `runs/annotation_{fr,es}_v1/excluded_glued_items.json`, and `ingest_annotations.py` skips them in every analysis.

## Limits

- **No human validation of v2.** Every item passed the automatic checks; in spot checks most ILLOC and MOD items are correct, but some Russian and Catalan outputs stay awkward ("Во-время не приходящую менструацию следует…"), and some MOD fronting drops a connective ("но"). Earlier human audits found 85–95% validity for comparable checked LLM edits in English.
- **Small languages:** Spanish (iDEM, 285 pairs), Catalan (337) and Arabic (231) are too small to train scorers; they serve validation only. Arabic has no MOD (no dependent sentence pairs were found) and no ILLOC (narrative text).
- **Recall over precision:** imperative detection rejects some real imperatives that the small parsers tag as indicative ("Llame…", "Compili…") unless the text addresses the reader elsewhere.
- **MEANING and FLUENCY outside English** follow the English recipe, but its level mapping (which deletions count as "Some" vs "A lot") was set by English human reviews only.

## Reproduce

```bash
sbatch phase6_degraded_corpus/jobs/submit_s1_multilingual_gpu.sh <lang> v2   # pools, checkers, rules, MOD, ILLOC
python -m phase6_degraded_corpus.src.generation.export_phase6_corpus --run-dir phase6_degraded_corpus/runs/s1_<lang>_v2
```

New dependencies in `.venv-phase6-vllm`: spaCy `it_core_news_sm`, `ca_core_news_sm`, `ru_core_news_sm` 3.8.0, and Stanza 1.15.0 with its Arabic model in `cache/stanza`.
