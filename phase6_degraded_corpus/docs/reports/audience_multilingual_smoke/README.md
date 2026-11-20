# Audience × language smoke study

**Question.** FEATS should adapt to the target audience and work across languages. Before building audience-conditioned training data, we checked on a small sample: (1) do LLM simplifications change with the audience? (2) do they stay in the source language? (3) which of our degradation methods work in each language?

## Setup

- [60 originals](originals.csv): 10 each in English, Spanish, Italian, Russian, Arabic and Chinese (sources listed in the CSV; evaluation and training originals excluded).
- Three prompts, identical except for the audience sentence: [B1 adults](../../../prompts/simplify_etr_v2_b1.txt), [children aged 8–13](../../../prompts/simplify_etr_v2_children.txt), [adults with intellectual disability](../../../prompts/simplify_etr_v2_intellectual_disability.txt).
- Two generators at temperature 0: Gemini (gemini-3.5-flash-lite) and GPT (gpt-5.4-mini) → [360 simplifications](simplifications.csv).
- Degradations with our existing per-language methods → [degradations](degradations.csv).

## Findings

1. **Audience changes the output only with Gemini.** Mean length ratio (rewrite / original):

   | Generator | B1 | Children | Intellectual disability | Same text for ≥2 audiences |
   |---|---:|---:|---:|---:|
   | Gemini | 0.88 | 0.88 | 0.71 | 3 / 60 |
   | GPT | 1.04 | 1.02 | 0.99 | 16 / 60 |

2. **The strategy mix barely changes across audiences** (E2R strategy classifier, en/es/it/ar): the differences are length and wording, not different strategies.
3. **Language is kept in 358/360 outputs.** The 2 failures are GPT rewrites (Italian, Chinese) returned in English.
4. **Degradations transfer only partly** (✓ = at least one checked group produced):

   | | Meaning | Fluency | Omission | Synonymy | Explanation | Modulation | Illocution | Compression | Syntactic |
   |---|---|---|---|---|---|---|---|---|---|
   | en | ✓ | ✓ | ✓ | ✓ | – | ✓ | – | ✓ | ✓ |
   | es / it / ru | ✓ | ✓ | – | – | – | ✓ | ✓ | n/a | n/a |
   | ar | ✓ | ✓ | – | ✓ | – | – | ✓ | n/a | n/a |
   | zh | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |

   – = method ran but produced nothing; n/a = no method for that language yet. Omission, Synonymy and Explanation undo edits aligned with the original, which free LLM rewrites rarely allow.

## Examples (Gemini)

| Original | B1 | Children | Intellectual disability |
|---|---|---|---|
| That changed, however, in January 1981; the NWA territory based in San Francisco folded, which was the last remaining promotion outside the Mid-Atlantic territory that recognized its own United States Champion, leaving the Mid-Atlantic version as the only remaining United States Championship. | In January 1981, things changed. The wrestling group in San Francisco closed. Because of this, the Mid-Atlantic championship became the only United States championship left. | In January 1981, wrestling in San Francisco shut down. This left only one United States Championship in the whole country. | In January 1981, the wrestling group in San Francisco closed. After that, there was only one United States Championship left. |
| Inició entonces estudios de pintura en los talleres de Antonio Cabral Bejarano, y más tarde en el de su tío paterno Joaquín Domínguez Bécquer, que le pronosticó «Tú no serás nunca un buen pintor, sino un mal literato», aunque le estimuló a los estudios y le pagó los de latín. | Entonces empezó a estudiar pintura. Primero fue con Antonio Cabral Bejarano. Después fue con su tío Joaquín Domínguez Bécquer. Su tío le dijo que nunca sería un buen pintor, sino un mal escritor. Pero le animó a estudiar y le pagó las clases de latín. | Entonces empezó a estudiar pintura con Antonio Cabral Bejarano y con su tío Joaquín Domínguez Bécquer. Su tío le dijo que nunca sería un buen pintor, sino un mal escritor, pero le animó a estudiar y le pagó las clases de latín. | Empezó a estudiar pintura con dos familiares. Su tío le dijo que sería mal pintor y buen escritor. Y le pagó los estudios de latín. |

More in [simplifications.csv](simplifications.csv).

## Limitations

Small convenience sample (10 per language); uneven domains (Arabic: one novel; Chinese: Wikipedia). Prompts are in English for all languages, and the B1 prompt says "B1-level English" even for non-English input. Strategy detection does not cover Russian or Chinese.

## Next step

- Use a language-neutral B1 wording and Gemini (or another audience-sensitive generator) for any audience-conditioned data.
- Pilot audience in the scorer input on a small, human-reviewed set before scaling.
- Add language-specific degradation rules (Omission, Synonymy, Explanation, Compression, Syntactic change) and a Chinese configuration.
