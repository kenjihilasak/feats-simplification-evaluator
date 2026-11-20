# Audience × language smoke study

**Question.** FEATS should adapt to the target audience and work across languages. Before building audience-conditioned training data, we checked on a small sample: (1) do LLM simplifications change with the audience? (2) do they stay in the source language? (3) which of our degradation methods work in each language?

## Setup

- [60 originals](originals.csv): 10 each in English, Spanish, Italian, Russian, Arabic and Chinese (sources listed in the CSV; evaluation and training originals excluded).
- Three prompts, identical except for the audience sentence: [B1 adults](../../../prompts/simplify_etr_v2_b1.txt), [children aged 8–13](../../../prompts/simplify_etr_v2_children.txt), [adults with intellectual disability](../../../prompts/simplify_etr_v2_intellectual_disability.txt).
- Two generators at temperature 0: Gemini (gemini-3.5-flash-lite) and GPT (gpt-5.4-mini).
- **Side-by-side view per language** (original, then each audience × generator): [English](by_language/en.md) · [Spanish](by_language/es.md) · [Italian](by_language/it.md) · [Russian](by_language/ru.md) · [Arabic](by_language/ar.md) · [Chinese](by_language/zh.md).
- Degradations with our existing per-language methods → [degradations](degradations.csv).

## Findings

1. **Audience changes the output only with Gemini.** Mean length ratio (rewrite / original):

   | Generator | B1 | Children | Intellectual disability | Same text for ≥2 audiences |
   |---|---:|---:|---:|---:|
   | Gemini | 0.88 | 0.88 | 0.71 | 3 / 60 |
   | GPT | 1.04 | 1.02 | 0.99 | 16 / 60 |

2. **Strategies change little, except Gemini's rewrites for intellectual disability**, which omit more and rewrite syntax less. Share of rewrites with each confirmed strategy (English, Spanish, Italian, Arabic; 40 rewrites per cell; confirmed when ≥2 of the 4 E2R classifiers agree, including Gemma, as in the pipeline):

   | Generator · audience | Omission | Compression | Synonymy | Explanation | Modulation | Syntactic change |
   |---|---:|---:|---:|---:|---:|---:|
   | Gemini · B1 | 42% | 78% | 92% | 5% | 60% | 22% |
   | Gemini · children | 42% | 62% | 92% | 2% | 50% | 18% |
   | Gemini · intellectual disability | 55% | 75% | 70% | 5% | 58% | 12% |
   | GPT · B1 | 36% | 62% | 90% | 0% | 59% | 15% |
   | GPT · children | 28% | 68% | 95% | 5% | 52% | 18% |
   | GPT · intellectual disability | 35% | 78% | 90% | 0% | 55% | 18% |

   Neither generator explains terms (Explanation ≤ 5%), even for the intellectual-disability audience. Illocution is not covered by the classifiers.
3. **Language is kept in 358/360 outputs.** The 2 failures are GPT rewrites (Italian, Chinese) returned in English.
4. **Degradations transfer only partly** (✓ = at least one checked group produced):

   | | Meaning | Fluency | Omission | Synonymy | Explanation | Modulation | Illocution | Compression | Syntactic |
   |---|---|---|---|---|---|---|---|---|---|
   | en | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ |
   | es / it / ru | ✓ | ✓ | – | – | – | ✓ | ✓ | n/a | n/a |
   | ar | ✓ | ✓ | – | ✓ | – | – | ✓ | n/a | n/a |
   | zh | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |

   – = method ran but produced nothing; n/a = no method for that language yet. Each language uses the same methods as our pipeline: English uses the training-corpus methods (tolerant alignment for Omission, Synonymy and Explanation, which yields 8, 30 and 1 groups here); Spanish, Italian, Russian and Arabic use the Phase 6 multilingual methods, whose Omission, Synonymy and Explanation rules need a word-by-word alignment with the original that free LLM rewrites rarely allow. English Illocution produced nothing because none of the English rewrites contains a question or instruction to make indirect.

## Examples (Gemini)

| Original | B1 | Children | Intellectual disability |
|---|---|---|---|
| That changed, however, in January 1981; the NWA territory based in San Francisco folded, which was the last remaining promotion outside the Mid-Atlantic territory that recognized its own United States Champion, leaving the Mid-Atlantic version as the only remaining United States Championship. | In January 1981, things changed. The wrestling group in San Francisco closed. Because of this, the Mid-Atlantic championship became the only United States championship left. | In January 1981, wrestling in San Francisco shut down. This left only one United States Championship in the whole country. | In January 1981, the wrestling group in San Francisco closed. After that, there was only one United States Championship left. |
| Inició entonces estudios de pintura en los talleres de Antonio Cabral Bejarano, y más tarde en el de su tío paterno Joaquín Domínguez Bécquer, que le pronosticó «Tú no serás nunca un buen pintor, sino un mal literato», aunque le estimuló a los estudios y le pagó los de latín. | Entonces empezó a estudiar pintura. Primero fue con Antonio Cabral Bejarano. Después fue con su tío Joaquín Domínguez Bécquer. Su tío le dijo que nunca sería un buen pintor, sino un mal escritor. Pero le animó a estudiar y le pagó las clases de latín. | Entonces empezó a estudiar pintura con Antonio Cabral Bejarano y con su tío Joaquín Domínguez Bécquer. Su tío le dijo que nunca sería un buen pintor, sino un mal escritor, pero le animó a estudiar y le pagó las clases de latín. | Empezó a estudiar pintura con dos familiares. Su tío le dijo que sería mal pintor y buen escritor. Y le pagó los estudios de latín. |

All 60 originals, side by side: [English](by_language/en.md) · [Spanish](by_language/es.md) · [Italian](by_language/it.md) · [Russian](by_language/ru.md) · [Arabic](by_language/ar.md) · [Chinese](by_language/zh.md).

## Limitations

Small convenience sample (10 per language); uneven domains (Arabic: one novel; Chinese: Wikipedia). Prompts are in English for all languages, and the B1 prompt says "B1-level English" even for non-English input. Strategy detection does not cover Russian or Chinese.

## Next step

- Check whether the audience-specific rewrites really suit their audience: human reviewers judge the Gemini rewrites we already have (10 sentences per language, each rewritten for B1 adults, children and adults with intellectual disability) in English, Spanish, Italian, Russian and Arabic.
- If reviewers prefer the matched version, add the audience to the scorer's input (e.g. "Audience: children aged 8–13") and generate audience-specific training data at scale with Gemini and a B1 prompt that does not name English ("B1 level in the language of the text").
