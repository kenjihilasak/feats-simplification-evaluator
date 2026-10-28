# Phase 6 v2: degradations for seven languages

**Date:** 28 October 2026 · **Scope:** the five strategy axes (OMIT, SYN, EXPL, MOD, ILLOC) in English, Spanish, French, Italian, Catalan, Russian and Arabic. MEANING and FLUENCY are unchanged (English only).

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

Valid items per language and axis. Files: `runs/s1_<lang>_v2/final/phase6_corpus.jsonl`, one record per original with a target score per version (pairs: clean 1.0, degraded 0.0; graded: clean 1.0, mild 0.5, strong 0.0).

| Language | Corpora | OMIT | SYN | EXPL | MOD | ILLOC | Total |
|---|---|---:|---:|---:|---:|---:|---:|
| English | WikiAutoEN, ASSET | 137 | 98 | 65 | 147 | 105 | 552 |
| French | WikiLargeFR, CLEAR | 149 | 98 | 152 | 161 | 61 | 621 |
| Russian | RuWikiLarge, RSSE, RuAdapt | 145 | 107 | 59 | 164 | 165 | 640 |
| Italian | PaCCSS-IT, iDEM, Terence, Teacher, AdminIt… | 57 | 56 | 0 | 25 | 146 | 284 |
| Catalan | iDEM | 0 | 3 | 0 | 22 | 32 | 57 |
| Spanish | iDEM | 4 | 4 | 1 | 25 | 4 | 38 |
| Arabic | Saaq al-Bambuu | 25 | 6 | 0 | 0 | 0 | 31 |

These are pilot-scale allocations (at most 300 MOD and 240 ILLOC candidates per language, as in v1); larger quotas in `configs/experiments/s1_<lang>_v2.json` scale English, French, Russian and Italian.

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

The glued-word bug is in the **French S1 round already in the interface**: 21 of the 60 French OMIT items have one degraded version with a glued word (for example FR-S015 "sentieret", FR-S016 "1979en", FR-S008 "reliefou"), and one Spanish item (ES-S086 "directasde"). A reviewer can spot the degraded version from the typo alone, so those answers measure fluency, not omission. Recommended: replace those 22 items with the v2 outputs before they are annotated, or exclude them from analysis.

## Limits

- **No human validation of v2.** Every item passed the automatic checks; in spot checks most ILLOC and MOD items are correct, but some Russian and Catalan outputs stay awkward ("Во-время не приходящую менструацию следует…"), and some MOD fronting drops a connective ("но"). Earlier human audits found 85–95% validity for comparable checked LLM edits in English.
- **Small languages:** Spanish (iDEM, 285 pairs), Catalan (337) and Arabic (231) are too small to train scorers; they serve validation only. Arabic has no MOD (no dependent sentence pairs were found) and no ILLOC (narrative text).
- **Recall over precision:** imperative detection rejects some real imperatives that the small parsers tag as indicative ("Llame…", "Compili…") unless the text addresses the reader elsewhere.
- **MEANING and FLUENCY** are generated for English only.

## Reproduce

```bash
sbatch phase6_degraded_corpus/jobs/submit_s1_multilingual_gpu.sh <lang> v2   # pools, checkers, rules, MOD, ILLOC
python -m phase6_degraded_corpus.src.generation.export_phase6_corpus --run-dir phase6_degraded_corpus/runs/s1_<lang>_v2
```

New dependencies in `.venv-phase6-vllm`: spaCy `it_core_news_sm`, `ca_core_news_sm`, `ru_core_news_sm` 3.8.0, and Stanza 1.15.0 with its Arabic model in `cache/stanza`.
