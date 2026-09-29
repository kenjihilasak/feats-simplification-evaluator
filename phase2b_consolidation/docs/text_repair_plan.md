# Plan: Phase 2b text repair (glued sentences and PTB brackets)

## Execution status (2026-09-29, v1.1 rerun)

- Implemented and tested `feats-text-repair-v1.1`, including the R1 recall fix and R2 cleanup rules.
- Regenerated and validated `runs/2026-09-29_target_simple_textrepair_v1/`: 133,800 rows, 28,911 repaired rows, 10 retained repair-induced duplicates, and zero validation errors.
- English rows still matching `[a-z]{2,}[.!?][A-Z][a-z]`: 32 (down from approximately 5,989).
- Phase 2a LaBSE drift on 500 repaired English pairs: mean/max absolute delta 0.0; zero threshold crossings.
- LaBSE drift on 500 French pairs with R2: mean absolute delta 0.03171776, maximum 0.15902275, and 15 threshold crossings; reported only, with no re-filtering.
- **Audit approved (v1.1):** random-sample human review plus independent automatic verification (invariants; zero R1 edits other than inserted spaces; 32 remaining matches, consisting of protected abbreviations plus two `singer/…` cases protected by the URL guard). The 306 precision items were intentionally not checked one by one.
- Generated and validated `runs/2026-09-29_base_textrepair_v1/`: 854,486 rows, 105,559 repaired rows, 72 retained repair-induced duplicates, and zero validation errors. The base English file contains all 348,520 canonical pairs.


Execution plan. Variant id: **`textrepair_v1`**.

## 1. Problem

Some upstream corpora contain two sentences joined without a space, for example:

```text
Per Theodor Haugen (8 October 1932 – 14 October 2018) was a Norwegian actor.Haugen died in Oslo on 14 October 2018 at the age of 86.
```

The defect is **already in the raw data** (`raw/multisim/English/WikiAuto_train.csv`, row 79268). It is a MultiSim/WikiAuto artifact produced when several aligned simple sentences are concatenated. It is not a bug in Phase 1. Phases 1–2b preserve text faithfully, so the defect reaches Phase 2b and every downstream phase.

Why it matters:
- the Simplified side becomes ungrammatical, which invalidates clean `score = 1` labels;
- Phase 6 generators "fix" the space instead of degrading (pilot cases 03 and 21);
- sentence-split detection is wrong: MOD and Phase 3a strategy labels depend on sentence boundaries.

A second artifact appears in **WikiLargeFR**: Penn-Treebank bracket tokens (`-LRB-`, `-RRB-`) in 2,833 / 11,673 pairs (24%).

### 1.1 Measured extent in `runs/2026-09-02_target_simple_v1`

Detector of §3.1 (final rule), pairs with ≥ 1 repair:

| Language | Corpus | Pairs | Simple glued | % | Original glued |
|---|---|---:|---:|---:|---:|
| en | WikiAutoEN | 71,045 | 21,209 | 29.9% | 23 |
| en | ASSET | 1,864 | 2 | 0.1% | 0 |
| it | Teacher | 27 | 6 | 22.2% | 2 |
| it | Terence | 22 | 5 | 22.7% | 0 |
| ru | RuAdaptEncy | 130 | 16 | 12.3% | 0 |
| pt-BR | PorSimples | 85 | 6 | 7.1% | 0 |
| ru | RuAdaptFairytales | 16 | 1 | 6.2% | 0 |
| ru | RSSE | 347 | 2 | 0.6% | 1 |
| fr | Wikipedia-Vikidia | 19,295 | 7 | < 0.1% | 4 |
| fr | WikiLargeFR | 11,673 | 2 | < 0.1% | 2 |
| es / ru | Wikipedia-Vikidia, iDEM, RuWikiLarge | — | ≤ 1 each | — | ≤ 1 each |

No hits in: ca, de, ja, sl, ur, en/Wikipedia-Vikidia, fr/CLEAR, it/AdminIt, it/SimpitikiWiki. Japanese, Urdu and Arabic do not use inter-sentence spaces, so the rule does **not** apply to them (§3.1).

A random sample of 30 WikiAutoEN hits was checked manually: 30/30 were true glued sentences. The remaining false positives found in non-English corpora were wiki file names (`… 01.JPG|`), which the final rule excludes. These numbers must be recomputed on the base consolidation `phase2b_consolidation/data/` (348,520 English pairs), which has not been measured.

## 2. Design decisions

1. **Scope: post-consolidation repair, as a new Phase 2b variant.** Do not modify Phase 1, Phase 2a, or existing Phase 2b outputs. Write new runs:
   - `phase2b_consolidation/runs/2026-09-29_target_simple_textrepair_v1/` built from `runs/2026-09-02_target_simple_v1/`;
   - `phase2b_consolidation/runs/2026-09-29_base_textrepair_v1/` built from `phase2b_consolidation/data/`.
2. **IDs stay unchanged.** `canonical_original_id` and `canonical_pair_id` remain the hashes of the **raw** text (`feats-text-identity-v1`), so Phase 3a predictions, Phase 4a gold, Phase 5 inputs and Phase 6 selections keep joining. Document that IDs identify upstream text, not repaired text.
3. **Text fields.** `original` and `simple` hold the **repaired** text. `original_raw` / `simple_raw` keep the Phase 2b text byte for byte. `text_repairs` lists every edit. Consumers that do not know about the repair automatically get clean text.
4. **Repair-induced duplicates are not merged.** If two rows become identical after repair (1 case in English), keep both rows and set `repaired_duplicate_of` on the one with the larger `canonical_pair_id`, pointing to the other. Merging would change IDs and counts.
5. **Phase 2a scores are not recomputed.** Phase 2a filters (LaBSE, complexity, `target_simple`) were computed on raw text. A missing space barely affects them. Measure the drift on a sample (§5.3) instead of re-filtering.
6. **Long term (out of scope):** at the next full rebuild, move the repair into Phase 1 normalization with a new identity version `feats-text-identity-v2`.

## 3. Repair rules

New module: `phase2b_consolidation/src/repair_text.py`. It must be pure (no model calls) and deterministic, with the same function used by all corpora.

### 3.1 R1: glued sentence boundary (insert one space)

Apply to languages `en, es, fr, it, ca, de, pt-BR, ru, sl`. Never apply to `ja`, `ur`, `ar`.

A match is `LEFT + PUNCT + RIGHT` with no whitespace between them:

| Part | Rule |
|---|---|
| `LEFT` | either (a) an alphanumeric token of ≥ 2 characters (Unicode letters/digits) whose **last character is a lowercase letter or a digit** and that is not in the abbreviation list; this covers `actor`, `Paris`, `1960s`, `49ers`, `2Pac`, `km2`, `TV5`, `DragonForce` (v1.1: the camelCase exclusion was removed, because `.Net`-style domains are already caught by the extension list); or (b) a number (`1994.Ricardo`); or (c) a closing bracket/quote `) ] ” » "` |
| `PUNCT` | `.`, `!` or `?`, optionally followed by a closing quote `" ” »` |
| `RIGHT` | an optional opening quote/bracket, then a **capitalized word**: an uppercase letter followed by ≥ 1 lowercase letter (Latin or Cyrillic), or a single `A`/`I` (en) or single-letter Cyrillic preposition (`В С К О У Я`) followed by whitespace |
| Not preceded by | `/`, `@`, `\` (URLs, paths, LaTeX) |
| Not followed by | `.` + letter right after `RIGHT`'s first token (abbreviation chains like `a.C.B.`) |
| `RIGHT` not in | the extension list: `net com org edu gov exe txt html php jpg jpeg png svg gif pdf` (case-insensitive). **v1.1 fix:** two-letter country codes (`de fr it ru uk io js`) were removed. In v1, `it` blocked every `…Australia.It …` repair (≈ 6,200 misses in English) and `de` blocked `De`. |

Repair: insert exactly one ASCII space after `PUNCT`.

The abbreviation list must be versioned in the module and covered by tests. It needs at least:
- English: `Dr Mr Mrs Ms Jr Sr St Mt Ft Prof Gen Col Lt Capt Sgt Rev Hon Gov Sen Rep Inc Ltd Co Corp Vol Fig No Nr Art pp vs etc cf ca approx Jan Feb Mar Apr Jun Jul Aug Sep Sept Oct Nov Dec`;
- Romance: `av ap Sig Sra Sr Dña Dott Ing Avv`, and the single-letter era markers `a.C. d.C.`, which are already excluded by the ≥ 2-letter rule;
- Russian: `ул г гг др им т св`.

Known cases that must **not** be changed (unit tests):

```text
U.S.The   J.R.R.Tolkien   St.Louis   Dr.Smith   Fokker Dr.I   a.C. Durante   av.J.C.
B.A.   750 куб.см   IslamAnswers.Net   todosjuntos.eu   insieme-per.eu   France.tv   Musical.ly
Kheops-Pyramid.jpg|   DD 01.JPG|   http://x.org/A.Html   4.essiccamento   3.5 GHz
```

Known cases that **must** be changed (unit tests):

```text
actor.Haugen → actor. Haugen            Paris.He → Paris. He
in 1994.Ricardo → in 1994. Ricardo      (yeux).Un → (yeux). Un
Prendete il burattino!Prendete → Prendete il burattino! Prendete
tem 35 anos.No sábado → tem 35 anos. No sábado
Новый Эрмитаж.С XVIII → Новый Эрмитаж. С XVIII
reporters.A "press → reporters. A "press
```

### 3.2 R2: Penn-Treebank bracket tokens (WikiLargeFR and any corpus where they occur)

- `-LRB-` → `(`, `-RRB-` → `)`, `-LSB-` → `[`, `-RSB-` → `]`, `-LCB-` → `{`, `-RCB-` → `}`.
- Then remove the tokenizer spaces inside the brackets: `( x )` → `(x)`, only at bracket positions created by R2.
- Remove empty bracket pairs created by R2 (`()` / `( )`) together with their preceding space.
- Remove an initial comma or semicolon inside an opening bracket created by R2 (`(, né` / `(; né` → `(né`).
- Insert a space when an opening bracket created by R2 directly follows a word (`Karl(Charly)` → `Karl (Charly)`).
- Apply R2 before R1.

### 3.3 Not auto-repaired: report only

A heuristic counted "space before punctuation" (`word .` / `word ,` / `( x`) in several corpora: WikiAutoEN 7,883, fr/Wikipedia-Vikidia 3,123, it/PaCCSS-IT 2,197, fr/CLEAR 66/74. French typography legitimately puts a space before `; : ! ?`, so this must not be auto-fixed in v1. Produce `reports/detokenization_audit.md` with per-corpus counts by pattern and 10 examples each, for a later decision.

## 4. Output schema

Each row keeps every existing Phase 2b field and adds:

```json
{
  "original": "<repaired>",
  "simple": "<repaired>",
  "original_raw": "<Phase 2b text>",
  "simple_raw": "<Phase 2b text>",
  "original_raw_sha256": "…",
  "simple_raw_sha256": "…",
  "text_repair_version": "feats-text-repair-v1",
  "text_repairs": [
    {"field": "simple", "rule": "R1_glued_sentence", "offset_raw": 88, "left": "actor.", "right": "Haugen"}
  ],
  "text_repaired": true,
  "repaired_duplicate_of": null
}
```

Rows with no repair still get `*_raw` fields, `text_repairs: []` and `text_repaired: false`, so the schema is uniform.

## 5. Validation and reports

Programs:
- `phase2b_consolidation/src/repair_text.py --input-root … --output-root … --reports-root …`;
- `phase2b_consolidation/src/validate_text_repair.py` with the same roots.

### 5.1 Hard invariants (the validator fails otherwise)

- The row count and the sets of `canonical_pair_id` / `canonical_original_id` are identical to the input, per language file.
- For every row: `*_raw` equals the input text byte for byte.
- Removing the inserted spaces and reversing R2 reproduces the raw text exactly (round-trip test on every repaired row).
- R1 only ever inserts spaces: the repaired text without whitespace equals the raw text without whitespace, for R1-only rows.
- No repairs in `ja`, `ur`, `ar`.
- Output sorted like the input; `validation.json` written.

### 5.2 Precision audit (human)

Build `reports/text_repair_audit.md` with:
- 200 random R1 repairs from en/WikiAutoEN;
- **all** R1 repairs from other corpora (currently about 70);
- 50 R2 repairs.

Each item shows the ±40-character context before and after the repair, with a Correct / Wrong checkbox. **STOP** for the human audit. Acceptance: ≥ 99% correct on WikiAutoEN and ≥ 95% elsewhere. If an audit fails, add the failing pattern to the tests, fix the rule and rerun.

### 5.3 Recall and drift checks (automatic, reported)

- **Recall probe:** a sample of 200 unrepaired rows that still match the loose pattern `\w[.!?][A-ZА-Я]`. List them in the audit file under "possibly missed", for review.
- **Phase 2a drift:** for 500 random repaired English pairs, recompute the Phase 2a LaBSE similarity on raw and repaired text (same model and revision as Phase 2a). Repeat for 500 French pairs containing R2 repairs. Report the mean and maximum absolute delta, and how many pairs would cross the 0.62/0.95 thresholds. Report only; no re-filtering.

### 5.4 Summary report

Write `reports/text_repair_summary.md`: per language × corpus, the pairs, repaired originals/simples, the number of repairs by rule, the duplicates created, and the audit results. Also update `phase2b_consolidation/README.md` with a "Text repair variants" section: what they are, the field semantics, the ID policy, and the run commands.

## 6. Tests (unittest, `phase2b_consolidation/tests/test_repair_text.py`)

- All must-change and must-not-change strings of §3.1.
- R2 conversion and bracket-space cleanup; R2 applied before R1.
- Round-trip invariant on synthetic rows.
- Language gating (`ja`, `ur`, `ar` untouched).
- Duplicate marking: two rows that become identical get `repaired_duplicate_of` on the larger id only.
- Idempotence: `repair(repair(x)) == repair(x)`.

## 7. Downstream follow-up (listed, not executed in this plan)

| Phase | Action |
|---|---|
| Phase 3a | Strategy predictions were made on raw text. Re-infer only the rows with `text_repaired: true` (21k English rows, plus a handful elsewhere) and report label changes, especially MOD, which depends on sentence splits. Decide after that report whether the Phase 3a candidate sets are regenerated. |
| Phase 4a | Gold decisions are keyed by `canonical_pair_id`, which is unchanged. Flag reviewed pairs with `text_repaired: true` for a quick re-look. |
| Phase 5 | Rebuild inputs from the repaired variant; metrics on glued text are slightly pessimistic for fluency. |
| Phase 6 | Point `phase2b_file` in the `mmi_en_v2` configs to `runs/2026-09-29_target_simple_textrepair_v1/…`. The read-time glue repair in `phase6_degraded_corpus/docs/plans/meaning_mod_illoc_v2_plan.md` becomes a fallback only. |

## 8. Order of execution

1. Implement `repair_text.py` + the tests (§6).
2. Run on the `target_simple_v1` variant; run the validator (§5.1).
3. Build the audit file (§5.2) and the drift check (§5.3). **STOP** for the human audit.
4. Fix any audited failures; rerun.
5. Run on the base consolidation `phase2b_consolidation/data/`; validate.
6. Write the summary report and the README section; commit code, tests and docs. Run outputs follow the existing Git-ignore rules for Phase 2b data.
