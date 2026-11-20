# Audience × language smoke study: LLM simplifications and degradations

## Key findings

- **Audience wording changes the rewrites, but only with one of the two generators.** Gemini (gemini-3.5-flash-lite) shortened the rewrites for adults with intellectual disability much more than for B1 or children (mean length ratio 0.71 vs 0.88). GPT (gpt-5.4-mini) kept all three audiences close to the source length (0.99–1.04), and for 16 of 60 originals it produced the same text for at least two audiences.
- **The mix of simplification strategies hardly changes across audiences.** The differences are mainly length and wording, not a different set of strategies.
- **Generation stays in the source language** in 358 of 360 cases. The two failures were GPT rewrites of an Italian and a Chinese sentence that came back in English.
- **Degradation methods transfer only partly.** Meaning and Fluency work in English, Spanish, Italian, Russian and Arabic; Modulation and Illocution work in most of them. The rule-based Omission, Synonymy and Explanation methods produce almost nothing on free LLM rewrites outside English. Compression and Syntactic change exist only for English, and Chinese has no degradation support yet.

## Why

FEATS is intended to adapt to a target audience and to work across languages. The earlier English milestone used one B1 Easy-to-Read prompt and treated audience as metadata. This small, inspectable smoke study tests whether audience wording changes the rewrites, whether generation stays in the requested language, and which existing degradation methods transfer. It is a decision aid, not a benchmark.

## Setup

The study uses [60 originals](originals.csv): ten each in English, Spanish, Italian, Russian, Arabic and Chinese. Chinese comes from the pinned `20231101.zh` Wikipedia snapshot at revision `b04c8d1ceb2f5cd4588862100d08de323dccfbaa`; the other languages come from the consolidated simplification corpora. Evaluation and training originals were excluded exactly and at token Jaccard ≥ 0.8.

Each original was rewritten for [B1 adults](../../../prompts/simplify_etr_v2_b1.txt), [children aged 8–13](../../../prompts/simplify_etr_v2_children.txt), and [adults with intellectual disability](../../../prompts/simplify_etr_v2_intellectual_disability.txt) by two generators at temperature 0: **Gemini** (gemini-3.5-flash-lite) and **GPT** (gpt-5.4-mini). Only the audience sentence differs between the three prompts. The instructions are in English for every source language, with an explicit request to answer in the language of the original. All [simplification outputs](simplifications.csv) are included; `status` is `ok` or `wrong_language`.

Sources of the originals: English — ASSET, WikiAuto, Wikipedia–Vikidia; Spanish — Wikipedia–Vikidia, iDEM; Italian — Terence, Teacher, PaCCSS-IT, SIMPITIKI (Wikipedia), Wikipedia–Vikidia, iDEM, AdminIt; Russian — RuAdapt (encyclopedia and fairy tales), RuWikiLarge, RSSE; Arabic — the *Saaq al-Bambuu* simplification corpus; Chinese — Chinese Wikipedia. These are short excerpts for research discussion; each source keeps its own licence.

## What the audiences change

Across language–generator cells, mean length ratio was 0.93 for B1, 0.95 for children and 0.85 for adults with intellectual disability. Mean sentence-count change was +1.29, +1.01 and +1.30, respectively. The strongest length effect was generator-specific: Gemini shortened the intellectual-disability rewrites much more (length ratio 0.88 for B1 and children, 0.71 for intellectual disability), while GPT kept all three audiences near the source length (1.04, 1.02 and 0.99).

Audience sensitivity also differed by generator. At least two audience outputs were exactly equal for 3/60 originals with Gemini and 16/60 with GPT; mean pairwise word overlap (Jaccard) between audience versions was 0.46 for Gemini and 0.73 for GPT. Audience wording therefore changes outputs, but not equally across generators.

The audience effects were not a simple ladder. Children had the highest mean length ratio, while the intellectual-disability condition was shortest overall and triggered slightly less classifier-detected compression. Sentence splitting was almost unchanged between B1 and intellectual-disability outputs, and lowest for children. Classifier-detected explanation and synonym replacement were nearly constant across audiences, so the clearest differences were length and wording rather than a wholesale change in strategy mix.

The multilingual strategy classifier covers English, Spanish, Italian and Arabic, but not Russian or Chinese. It used the published pair format and thresholds. Its aggregate strategy rates are descriptive because each cell has only ten items.

- B1: Compression 90%, Explanation 52%, Modulation 66%, Omission 47%, Synonymy 95%, Syntactic Change 33%.
- Children: Compression 90%, Explanation 51%, Modulation 61%, Omission 50%, Synonymy 95%, Syntactic Change 29%.
- Intellectual Disability: Compression 84%, Explanation 50%, Modulation 66%, Omission 48%, Synonymy 95%, Syntactic Change 35%.

## Language coverage

There were 358 valid outputs out of 360. Both wrong-language cases were full English rewrites: one Italian B1 output and one Chinese B1 output. There were no refusals, preambles or identical copies. The very short Italian output "È vero?" was kept after a manual-rule check, because automatic language identification is unreliable on such short text.

Two examples per language are shown below. All columns use Gemini, the generator that responded most to the audience.

### English

| Original | B1 | Children | Intellectual disability |
|---|---|---|---|
| The WWF consisted of Stone Cold Steve Austin, Kurt Angle, Chris Jericho, Kane, and the Undertaker, who all squared off against the team of DDP, Booker T, Rhyno, and the Dudley Boys. | Two wrestling teams fought against each other. One team had Stone Cold Steve Austin, Kurt Angle, Chris Jericho, Kane, and the Undertaker. The other team had DDP, Booker T, Rhyno, and the Dudley Boys. | Two groups of wrestling stars fought against each other. One team had Stone Cold Steve Austin, Kurt Angle, Chris Jericho, Kane, and the Undertaker. The other team had DDP, Booker T, Rhyno, and the Dudley Boys. | Two wrestling teams fought each other.<br><br>Team one had Stone Cold Steve Austin, Kurt Angle, Chris Jericho, Kane, and the Undertaker.<br><br>Team two had DDP, Booker T, Rhyno, and the Dudley Boys. |
| That changed, however, in January 1981; the NWA territory based in San Francisco folded, which was the last remaining promotion outside the Mid-Atlantic territory that recognized its own United States Champion, leaving the Mid-Atlantic version as the only remaining United States Championship. | In January 1981, things changed. The wrestling group in San Francisco closed. Because of this, the Mid-Atlantic championship became the only United States championship left. | In January 1981, wrestling in San Francisco shut down. This left only one United States Championship in the whole country. | In January 1981, the wrestling group in San Francisco closed. After that, there was only one United States Championship left. |

### Spanish

| Original | B1 | Children | Intellectual disability |
|---|---|---|---|
| Inició entonces estudios de pintura en los talleres de Antonio Cabral Bejarano, y más tarde en el de su tío paterno Joaquín Domínguez Bécquer, que le pronosticó «Tú no serás nunca un buen pintor, sino un mal literato», aunque le estimuló a los estudios y le pagó los de latín. | Entonces empezó a estudiar pintura. Primero fue con Antonio Cabral Bejarano. Después fue con su tío Joaquín Domínguez Bécquer. Su tío le dijo que nunca sería un buen pintor, sino un mal escritor. Pero le animó a estudiar y le pagó las clases de latín. | Entonces empezó a estudiar pintura con Antonio Cabral Bejarano y con su tío Joaquín Domínguez Bécquer. Su tío le dijo que nunca sería un buen pintor, sino un mal escritor, pero le animó a estudiar y le pagó las clases de latín. | Empezó a estudiar pintura con dos familiares. Su tío le dijo que sería mal pintor y buen escritor. Y le pagó los estudios de latín. |
| En 2015, el Ministerio del Interior había inadmitido la extensión de la residencia a Alvarado Ochoa, pero en 2016, coincidiendo con la contratación de Aliste y su colaboración con la Policía en contra de Podemos, la autorización fue renovada. | En 2015, el Ministerio del Interior no quiso renovar el permiso de residencia a Alvarado Ochoa. Pero en 2016, tras contratar a Aliste y colaborar con la Policía contra Podemos, le dieron el permiso de nuevo. | En 2015, el gobierno no quiso renovar el permiso de residencia a Alvarado Ochoa. Pero en 2016, justo cuando contrataron a Aliste y este empezó a colaborar con la Policía contra el partido Podemos, le dieron el permiso de nuevo. | En 2015, el Gobierno no quiso renovar el permiso de residencia a Alvarado Ochoa. Pero en 2016 se lo dieron de nuevo. Eso pasó al mismo tiempo que Aliste empezó a trabajar con la Policía contra el partido Podemos. |

### Italian

| Original | B1 | Children | Intellectual disability |
|---|---|---|---|
| Dopo una lunga consultazione, Ernesta e i suoi compagni conclusero che il modo migliore per gli abitanti della via era quello di realizzare un sistema per raffreddare la calda aria estiva. | Dopo una lunga riunione, Ernesta e i suoi amici decisero qual era la cosa migliore per le persone della via: creare un sistema per rinfrescare l'aria calda dell'estate. | Dopo una lunga riunione, Ernesta e i suoi amici decisero che il modo migliore per le persone della via era costruire un sistema per rinfrescare la calda aria d'estate. | Ernesta e i suoi amici hanno deciso una cosa importante. Per rinfrescare le case dal caldo dell'estate, volevano fare un impianto per l'aria fresca nella strada. |
| Che cosa farà dunque a costoro il padrone della vigna ? | Cosa farà il padrone della vigna a queste persone? | Cosa farà il padrone della vigna a queste persone? | Che cosa farà il padrone della vigna? |

### Russian

| Original | B1 | Children | Intellectual disability |
|---|---|---|---|
| Слава Тулы как города, где делают самовары, стала основанием для пословицы В Тулу со своим самоваром не ездят – не надо брать с собой то, чего и так много там, куда едешь, и возникшего на этой основе более распространенного фразеологизма – в Тулу со своим самоваром. | Тула известна как город самоваров. Из этого появилась пословица: «В Тулу со своим самоваром не ездят». Она значит, что не надо брать с собой то, чего и так много в месте, куда вы едете. | В Туле делают так много самоваров, что появилась пословица: «В Тулу со своим самоваром не ездят». Она означает, что не нужно брать с собой то, чего и так полно на месте. От неё появилась и другая короткая фраза: «ехать в Тулу со своим самоваром». | В Туле делают много самоваров.<br>Поэтому появилась пословица: в Тулу со своим самоваром не ездят.<br>Она означает, что не надо брать с собой то, чего и так много на месте. |
| Василиса Премудрая из кубка пьет — не допивает, остатки себе за левый рукав выливает.  | Василиса Премудрая пьет из кубка, но не допивает. Остатки она выливает себе за левый рукав. | Василиса Премудрая пьет из кубка, но не допивает. Остатки она выливает себе за левый рукав. | Василиса Премудрая пьет из кубка. Она не допивает. Остатки воды она выливает себе за левый рукав. |

### Arabic

| Original | B1 | Children | Intellectual disability |
|---|---|---|---|
| يوم أول أمضيته خلف الستارة في غرفتي أتلصص على زوّار عائلتي المتورطة بي. | قضيت اليوم الأول خلف الستارة في غرفتي. كنت أنظر سرّاً إلى زوار عائلتي الذين جاؤوا لرؤيتي وأنا مريض. | أول يوم لي خلف الستارة في غرفتي، كنت أتجسس على زوار عائلتي الذين جاؤوا من أجلي. | أول يوم قضيته وراء الستارة في غرفتي، أراقب زوار عائلتي الذين جاؤوا لرؤيتي. |
| لم يعد يتجشم عناء مداراة مشاعره تجاهي بعد انقطاع حوالات أبي المالية. | توقف عن إخفاء مشاعره الحقيقية تجاهي بعد أن توقف أبي عن إرسال المال. | توقف عن إخفاء مشاعره الحقيقية تجاهي بعد أن توقف أبي عن إرسال الأموال. | توقف عن إخفاء شعوره السيء نحوي، عندما توقف أبي عن إرسال المال. |

### Chinese

| Original | B1 | Children | Intellectual disability |
|---|---|---|---|
| 夫武昌揚靈於大江，東趨賓山（江蘇省），四日而極，足以轉輸矣，外鑑諸鄰國，柏林無海，江戶則曰海堧爾；內海雖咸，亦猶大江也……江沔之在上游，其通達等是矣，何必傅海！ | 武昌的軍隊在長江上很有威望。向東到江蘇的賓山，四天就到了。這條路用來運送物資很足夠了。看看外面的國家：柏林沒有海，江戶也只是靠海邊。內海雖然是鹹水，也跟長江一樣。長江和漢水在上游，交通一樣方便，為什麼一定要走到海邊呢？ | 武昌的船在大江上展現神威，四天就能抵達江蘇的賓山，運送物資非常足夠。看看外面的鄰國，柏林沒有海，江戶也只是靠著海邊。內海雖然是鹹水，但也像大江一樣。長江和漢水在上游一樣很通暢，為什麼一定要出海呢！ | 長江水路交通很好。我們不需要靠海。 |
| 古《尚書》說，脾，木也；肺，火也；心，土也；肝，金也；腎，水也。 | 古老《尚書》記載，脾是木，肺是火，心是土，肝是金，腎是水。 | 古書《尚書》說：脾臟就像木，肺就像火，心臟就像土，肝臟就像金，腎臟就像水。 | 古書說：脾是木，肺是火，心是土，肝是金，腎是水。 |

## Degradation coverage

The table reports whether at least one checked group was produced. “Failed” means the configured method ran but produced no surviving group; it does not mean the language is unsupported.

| Language | MEANING | FLUENCY | OMIT | SYN | EXPL | MOD | ILLOC | COMP | SYNT |
|---|---|---|---|---|---|---|---|---|---|
| en | ✓ | ✓ | ✓ | ✓ | failed | ✓ | failed | ✓ | ✓ |
| es | ✓ | ✓ | failed | failed | failed | ✓ | ✓ | not supported | not supported |
| it | ✓ | ✓ | failed | failed | failed | ✓ | ✓ | not supported | not supported |
| ru | ✓ | ✓ | failed | failed | failed | ✓ | ✓ | not supported | not supported |
| ar | ✓ | ✓ | failed | ✓ | failed | failed | ✓ | not supported | not supported |
| zh | not supported | not supported | not supported | not supported | not supported | not supported | not supported | not supported | not supported |

Surviving groups and group pass rates (surviving/attempted) are:

| Language | MEANING | FLUENCY | OMIT | SYN | EXPL | MOD | ILLOC | COMP | SYNT |
|---|---|---|---|---|---|---|---|---|---|
| en | 60/60 (100%) | 56/60 (93%) | 3/3 (100%) | 1/4 (25%) | 0/0 | 5/28 (18%) | 0/0 | 13/73 (18%) | 31/47 (66%) |
| es | 53/54 (98%) | 44/54 (82%) | 0/0 | 0/0 | 0/0 | 10/27 (37%) | 1/1 (100%) | — | — |
| it | 47/53 (89%) | 52/53 (98%) | 0/0 | 0/3 (0%) | 0/0 | 2/3 (67%) | 13/13 (100%) | — | — |
| ru | 53/53 (100%) | 37/53 (70%) | 0/0 | 0/0 | 0/0 | 5/25 (20%) | 4/4 (100%) | — | — |
| ar | 53/53 (100%) | 50/53 (94%) | 0/0 | 2/3 (67%) | 0/0 | 0/0 | 3/10 (30%) | — | — |
| zh | — | — | — | — | — | — | — | — | — |

Emitted rows by level for each surviving language–axis cell are:

- en: MEANING: clean 60, contradiction 18, major_loss 50, mild_loss 57, neutral_trim 1; FLUENCY: clean 56, major 97, minor 52, severe 44; OMIT: clean 3, major 3; SYN: clean 1, major 1; MOD: clean 5, major 5, mild 5; COMP: clean 13, major 13, mild 1; SYNT: clean 31, major 7, mild 24
- es: MEANING: clean 53, contradiction 41, major_loss 33, mild_loss 51, neutral_trim 5; FLUENCY: clean 44, major 66, minor 26, severe 33; MOD: clean 10, major 10, mild 10; ILLOC: clean 1, indirect 1
- it: MEANING: clean 47, contradiction 44, major_loss 25, mild_loss 40, neutral_trim 5; FLUENCY: clean 52, major 86, minor 41, severe 29; MOD: clean 2, major 2, mild 2; ILLOC: clean 13, indirect 13
- ru: MEANING: clean 53, contradiction 39, major_loss 32, mild_loss 53, neutral_trim 5; FLUENCY: clean 37, major 54, minor 22, severe 15; MOD: clean 5, major 5, mild 5; ILLOC: clean 4, indirect 4
- ar: MEANING: clean 53, contradiction 48, major_loss 14, mild_loss 40; FLUENCY: clean 50, major 61, minor 22, severe 10; SYN: clean 2, major 2; ILLOC: clean 3, indirect 3
- zh: none (not supported).

The [degradation rows](degradations.csv) include clean controls and every surviving level. Candidate checks use the existing multilingual entailment and acceptability thresholds; only passing groups were materialized.

## Limitations

This is a deliberately small convenience sample. Corpora and domains are uneven: Arabic is literary narrative only and Chinese is Wikipedia only. The prompts are English even when the input is not, and the B1 prompt names "B1-level English" for every language; the next run should say "B1 level in the language of the text". The language check combines a statistical identifier for Latin-script outputs with script ratios for Russian, Arabic and Chinese; very short text needs marker-based handling. Strategy detection does not cover Russian or Chinese. The rule-based Omission, Synonymy and Explanation degradations restore material aligned with the original, so free LLM rewrites often offer no place where such an edit can be undone. Chinese has no Phase 6 language configuration, so no degradation axis is claimed for it.

## What this suggests for the next step

Audience conditioning is worth retaining in a targeted next pilot, but this smoke does not justify scaling a full audience-conditioned corpus yet. Audience wording changed length and lexical choices, while strategy rates were broadly similar and sensitivity depended strongly on the generator. The next pilot should add audience to the scorer input and use a balanced, human-reviewed set to test whether readers actually prefer the matched condition. Before scaling multilingual degradations, improve or add language-specific structural rules—especially for freely generated rewrites—and add a Chinese configuration rather than treating multilingual entailment alone as sufficient.
