# Phase 6 pilot quality analysis

This report is an **automatic triage**, not a final semantic evaluation. Human reviewers must still verify that the simplified version is valid and that the degradation changes only the target dimension.

## Quality levels

- **Good:** all automatic structural checks passed.
- **Medium:** the text changed and the assigned operation was declared, but the changed/replacement span was not verified literally.
- **Failed:** no usable degradation was produced, most commonly because Simplified and Degraded are identical.

## Results by dimension

| Dimension | Good | Medium | Failed | Good rate |
|---|---:|---:|---:|---:|
| EXPL | 39 | 8 | 3 | 78% |
| ILLOC | 33 | 15 | 2 | 66% |
| MOD | 23 | 27 | 0 | 46% |
| FLUENCY | 10 | 23 | 17 | 20% |
| OMIT | 8 | 14 | 28 | 16% |
| SYN | 6 | 16 | 28 | 12% |
| **Overall** | **119** | **103** | **78** | **40%** |

## Main findings

- Explanation and Illocution have the strongest automatic results.
- Modulation changes every selected sentence, but many outputs have unverifiable span metadata.
- Fluency frequently claims an edit that is absent from the generated sentence.
- Omission and Synonymy have the highest outright-failure counts; their prompts, cues, and Phase 3a source labels need review before scaling.
- Medium cases must not be discarded automatically: several may contain valid degradations with inaccurate model metadata.

## Failure reasons

- **EXPL:** `all_automatic_checks_passed`: 39, `simplified_and_degraded_are_identical`: 3, `text_changed_but_declared_span_not_verified`: 8
- **ILLOC:** `all_automatic_checks_passed`: 33, `simplified_and_degraded_are_identical`: 2, `text_changed_but_declared_span_not_verified`: 15
- **MOD:** `all_automatic_checks_passed`: 23, `text_changed_but_declared_span_not_verified`: 27
- **FLUENCY:** `all_automatic_checks_passed`: 10, `simplified_and_degraded_are_identical`: 17, `text_changed_but_declared_span_not_verified`: 23
- **OMIT:** `all_automatic_checks_passed`: 8, `simplified_and_degraded_are_identical`: 28, `text_changed_but_declared_span_not_verified`: 14
- **SYN:** `all_automatic_checks_passed`: 6, `simplified_and_degraded_are_identical`: 28, `text_changed_but_declared_span_not_verified`: 16

## Representative examples

### EXPL

#### Good

- Pair: `pair:en:0e3ea88d6ac576b1f152e65fe0f2ae818262d65a45956ce92ad5f5c7bc1eb237`
  - Reason: `all_automatic_checks_passed`
  - Original: In households, several types of fabric towels are used, including hand towels, bath towels and kitchen towels.
  - Simplified: There are many types of towels, such as the beach towel and the washcloth, a small towel used for cleaning dishes and bodies.
  - Degraded: There are many types of towels, such as the beach towel, a small towel used for cleaning dishes and bodies.
- Pair: `pair:en:154f557dcbaea15680359c30de7adfa0d61ecfaea34decc82c11284b96ab3826`
  - Reason: `all_automatic_checks_passed`
  - Original: This landslide, one of the three largest in Japan, impacted an area of 1.8 km, with an estimated volume of 120 million m.
  - Simplified: This landslide was one of the three largest in Japan and is called the Ohya Landslide.It covered an area of 1.8 km with an estimated volume of 120 million m.
  - Degraded: This landslide was one of the three largest in Japan. It covered an area of 1.8 km with an estimated volume of 120 million m.

#### Medium

- Pair: `pair:en:10a92aefbc40acc032eb7c25d3e0c7e4302131040aa231cb97b4c5afc9b3c5e2`
  - Reason: `text_changed_but_declared_span_not_verified`
  - Original: Bernstein was born in New York City in 1918 and was adopted by a Russian Jewish family.
  - Simplified: Bernstein was born in New York City, New York on August 12, 1918.
  - Degraded: Bernstein was born in New York City in 1918 and was adopted by a Russian Jewish family.
- Pair: `pair:en:2ba7be67def4c74833a20ec06e9a6c7edb3e440915759c62042ae6dbdd141b18`
  - Reason: `text_changed_but_declared_span_not_verified`
  - Original: Roanne (] ; Rouana in Arpitan) is a commune in the Loire department in central France.
  - Simplified: Roanne is a French commune, a "subprefecture" in the Loire department in central France.
  - Degraded: Roanne is a French commune in the Loire department in central France.

#### Failed

- Pair: `pair:en:60f5f8fdde6f14d64a3629984d4eee1b7fdb7adbf39c2169c2ec58f48a915a09`
  - Reason: `simplified_and_degraded_are_identical`
  - Original: María José de Pablo Fernández, known professionally as Cote de Pablo (born November 12, 1979), is a Chilean-American actress and singer.
  - Simplified: Maria Jose de Pablo Fernandez, also known as Cote de Pablo (born November 12, 1979 in Santiago, Chile), is a Chilean-American actress and singer.
  - Degraded: Maria Jose de Pablo Fernandez, also known as Cote de Pablo (born November 12, 1979 in Santiago, Chile), is a Chilean-American actress and singer.
- Pair: `pair:en:84de07d98a2f3e3cbfbf397f1c7ccc28090140f4a719203fdea5c3fb536dff7f`
  - Reason: `simplified_and_degraded_are_identical`
  - Original: Over 4,000 living species are known.
  - Simplified: There are about 5,000 living species, and 15,000 fossil species are known.
  - Degraded: There are about 5,000 living species, and 15,000 fossil species are known.

### ILLOC

#### Good

- Pair: `pair:en:0265450034b45ee13af18624679d2611726b4d5535d2a096a862432f072bd0e2`
  - Reason: `all_automatic_checks_passed`
  - Original: "Implicit atheism" is "the absence of theistic belief without a conscious rejection of it" and "explicit atheism" is the conscious rejection of belief.
  - Simplified: "Implicit atheism" is when you do not believe in God because you do not know about the concept of God."Explicit atheism" is when you do not believe in God after learning about the idea.Those two quotes describe implicit atheism.
  - Degraded: "Implicit atheism" is when you do not believe in God after knowing about the concept of God."Explicit atheism" is when you do not believe in God because you do not know about the idea.Those two quotes describe implicit atheism.
- Pair: `pair:en:029cbefa42e98337fc5648343b07c3ce8ac2c56f1f381a6d2a9ae11c979815a8`
  - Reason: `all_automatic_checks_passed`
  - Original: Ilona Novák (May 16, 1925 – March 14, 2019) was a Hungarian swimmer and Olympic champion.
  - Simplified: Ilona Novák (May 16, 1925 – March 14, 2019) was a Hungarian swimmer and Olympic champion.She was born in Budapest and died on March 14, 2019 in Budapest, aged 93.
  - Degraded: Ilona Novák (May 16, 1925 – March 14, 2019) was a Hungarian swimmer and Olympic champion. Was she born in Budapest and did she die on March 14, 2019 in Budapest, aged 93?

#### Medium

- Pair: `pair:en:0d36bcb02ba838e16a40980d14820c5cb9661b63fdbfa2e72ffdbbc41054200f`
  - Reason: `text_changed_but_declared_span_not_verified`
  - Original: Frederick Russell Burnham DSO (May 11, 1861 – September 1, 1947) was an American scout and world-traveling adventurer.
  - Simplified: Frederick Russell Burnham (May 11, 1861 – September 1, 1947) was an American scout.
  - Degraded: Is Frederick Russell Burnham (May 11, 1861 – September 1, 1947) an American scout?
- Pair: `pair:en:11c06ccf7f8a528d3f5ab6cfa7363accf29cf0f09208adc748665fe2a5b1172e`
  - Reason: `text_changed_but_declared_span_not_verified`
  - Original: PayPal can be used in more than 200 countries/regions.
  - Simplified: PayPal was owned by eBay, from 2002 to 2015, and can be used in more than 200 countries.
  - Degraded: PayPal can be used in more than 200 countries/regions.

#### Failed

- Pair: `pair:en:0f8332099f563f95c110476a357e5112e96777fa64fba63b9f450501409a6211`
  - Reason: `simplified_and_degraded_are_identical`
  - Original: Intelligibility between languages can be asymmetric, with speakers of one understanding more of the other than speakers of the other understanding the first.
  - Simplified: When a speaker of one language can understand what a speaker of another language is saying but not the other way around, it is called asymmetric intelligibility.
  - Degraded: When a speaker of one language can understand what a speaker of another language is saying but not the other way around, it is called asymmetric intelligibility.
- Pair: `pair:en:d19a27838c8c35c4aa7e3a530f6e580d1abe2b10e3586f23cb771f75bb04b2a1`
  - Reason: `simplified_and_degraded_are_identical`
  - Original: In mathematics, magnitude is the size of a mathematical object, a property which determines whether the object is larger or smaller than other objects of the same kind.
  - Simplified: The magnitude of a mathematical object is its size: a property by which it can be larger or smaller than other objects of the same kind.
  - Degraded: The magnitude of a mathematical object is its size: a property by which it can be larger or smaller than other objects of the same kind.

### MOD

#### Good

- Pair: `pair:en:005c049b1c8c17092345d07e577ce3a1106e358d344fb4b61203556784c3aa31`
  - Reason: `all_automatic_checks_passed`
  - Original: Skikda is a province ("wilaya") of Algeria, on its eastern Mediterranean coastline.
  - Simplified: Skikda is a province of Algeria.It is on the Mediterranean coast.
  - Degraded: Skikda is a province of Algeria. It is on its eastern Mediterranean coastline.
- Pair: `pair:en:0940bba81e856a789755d6d8877a2bf14b267ed65628b4f6e302392a2f88799a`
  - Reason: `all_automatic_checks_passed`
  - Original: He previously served as a U.S. senator from Illinois from 2005 to 2008 and an Illinois state senator from 1997 to 2004.
  - Simplified: He was state senator from 1997 to 2004.He was a U.S. Senator from 2005 to 2008.
  - Degraded: He was a U.S. Senator from 2005 to 2008 and Illinois state senator from 1997 to 2004.

#### Medium

- Pair: `pair:en:01140a3ef23e1c1ceab1be7238b8c8d49c9a430d140580bbae5d74940c07e3b1`
  - Reason: `text_changed_but_declared_span_not_verified`
  - Original: Adam Kenneth Compton Wood (born 13 March 1955) is a retired British diplomat, and was the Lieutenant Governor of the Isle of Man from 2011 to 2016.
  - Simplified: Adam Kenneth Compton Wood (born 13 March 1955) is a retired British diplomat.He is the current Lieutenant Governor of the Isle of Man.Wood was born on 13 March 1955.
  - Degraded: Adam Kenneth Compton Wood (born 13 March 1955) is a retired British diplomat. He is the current Lieutenant Governor of the Isle of Man. Wood was born on 13 March 1955.
- Pair: `pair:en:09de275bba825c021f7eb209bdffdc8210a0dd4718e84640e2576834aef47ec6`
  - Reason: `text_changed_but_declared_span_not_verified`
  - Original: Faneuil Hall ( or ; previously ) is a marketplace and meeting hall located near the waterfront and today's Government Center, in Boston, Massachusetts.
  - Simplified: Faneuil Hall is an historic place near the waterfront in Boston, Massachusetts.It has been a marketplace and a meeting hall.Today it is the city's Government Center.
  - Degraded: Faneuil Hall is a marketplace and meeting hall located near the waterfront and today's Government Center in Boston, Massachusetts.

### FLUENCY

#### Good

- Pair: `pair:en:21d9dbafb59a7479e7d0d3bc1726b9555376eb0c80f5b21def2645eaeba6c5ec`
  - Reason: `all_automatic_checks_passed`
  - Original: When three people have sex with each other, it is called a "threesome".
  - Simplified: When three people have sex with each other, it is called a threesome.
  - Degraded: When three people have sex with each other, it is called a threesomes.
- Pair: `pair:en:3439ef04e2511c0cd71d47f3ca23f0be3a0989474050a9c70b9cc05ab0274c60`
  - Reason: `all_automatic_checks_passed`
  - Original: The population of the city is about 1 million people.
  - Simplified: About 1 million people live there.
  - Degraded: About 1 million lives there.

#### Medium

- Pair: `pair:en:08810a2cf650a7fcb79299845f9d6bdf6b7473edede82c80dcdda9e59f223992`
  - Reason: `text_changed_but_declared_span_not_verified`
  - Original: LaVey was born Howard Stanton Levey on April 11, 1930 in Chicago, Illinois.
  - Simplified: LaVey was born with the name Howard Stanton Levey and was of Jewish descent.He was born in Chicago, Illinois.
  - Degraded: LaVey was born with the name Howard Stanton Levey and was of Jewish descent. He was born in Chicago, Illinois.
- Pair: `pair:en:1b9a7a528413aeb7cfce456e4b851abf05235cbdc358bda7f765e5674f58639f`
  - Reason: `text_changed_but_declared_span_not_verified`
  - Original: Willie Aames (born Albert William Upton on July 15, 1960) is an American actor, film and television director, television producer, and screenwriter.
  - Simplified: Willie Aames (born Albert William Upton July 15, 1960 in Los Angeles, California) is an actor famous for the roles of Buddy Lembeck on "Charles in Charge", Tommy Bradford on "Eight is Enough" and the voice of Hank on "Dungeons & Dragons", the cartoon.
  - Degraded: Willie Aames (born Albert William Upton July 15, 1960 in Los Angeles, California) is an actor famous for the roles of Buddy Lembeck on 'Charles in Charge', Tommy Bradford on 'Eight is Enough' and the voice of Hank on Dungeons & Dragons, the cartoon.

#### Failed

- Pair: `pair:en:06ae391ca30d4dfecb0de5b991384bf45a7daf8c19288bcea7f1556d4c4eabef`
  - Reason: `simplified_and_degraded_are_identical`
  - Original: Theodoros Angelopoulos was born in Athens on 27 April 1935.
  - Simplified: Angelopoulos was born in Athens, Greece on April 27, 1935 and studied at the University of Paris.
  - Degraded: Angelopoulos was born in Athens, Greece on April 27, 1935 and studied at the University of Paris.
- Pair: `pair:en:1dd5e9312f8bc0c4fc4947ed74cf47de0eb47b58bd2ec99dd39bab743755bfd4`
  - Reason: `simplified_and_degraded_are_identical`
  - Original: Sarah Victoria "Torri" Higginson is a Canadian actress.
  - Simplified: Sarah Victoria "Torri" Higginson (born Burlington, Ontario, December 6, 1969) is a Canadian actress.
  - Degraded: Sarah Victoria "Torri" Higginson (born Burlington, Ontario, December 6, 1969) is a Canadian actress.

### OMIT

#### Good

- Pair: `pair:en:1ede202dd8a0c7afee826d4e077d08dd74ebb66c8a6876730aff4e999b962f4f`
  - Reason: `all_automatic_checks_passed`
  - Original: It covers an area of 30688 km2 and has a population of more than 11.4 million.
  - Simplified: Belgium has an area of 30528 km2.
  - Degraded: Belgium has an area of 30688 km2 and a population of more than 11.4 million.
- Pair: `pair:en:2dc2e567efa0759644a870c5a13b6731c45ec44e98ac958446b10fe92e39d797`
  - Reason: `all_automatic_checks_passed`
  - Original: Arnhem ( , , ] ] ; ; ; South Guelderish: "Èrnem") is a city and municipality situated in the eastern part of the Netherlands.
  - Simplified: Arnhem is a city in the Netherlands.
  - Degraded: Arnhem is a city in the eastern part of the Netherlands.

#### Medium

- Pair: `pair:en:01ac54d89fb79c5f1afb9ca2c4811c920c229144e8008722e749f6e05a1d3d6d`
  - Reason: `text_changed_but_declared_span_not_verified`
  - Original: From 1989 she was the general secretary of the All India Anna Dravida Munnetra Kazhagam (AIADMK), a Dravidian party whose cadre revered her as their "Amma" (mother) and Puratchi "Thalaivi" (revolutionary leader) .
  - Simplified: From 1989 she was the general secretary of the All India Anna Dravida Munnetra Kazhagam , a Dravidian party.
  - Degraded: From 1989 she was the general secretary of the All India Anna Dravida Munnetra Kazhagam, a Dravidian party.
- Pair: `pair:en:0d6adf6e8b9fccba797ece4b6831c09d94b5321e8840b77b091b5677b9fc2deb`
  - Reason: `text_changed_but_declared_span_not_verified`
  - Original: These trees were planted in Washington, D.C., and another 3,800 trees were donated in 1965.
  - Simplified: These trees were planted in Washington, D.C..
  - Degraded: These trees were planted in Washington, D.C., and another 3,800 trees were donated.

#### Failed

- Pair: `pair:en:0230b6e271daf97e8b7112459be27ee4c7d3fd7bf8e9852e3f6eb65426c096ff`
  - Reason: `simplified_and_degraded_are_identical`
  - Original: George L. Radosevich (January 25, 1928 – April 4, 2016) was an American football defensive back who played for the Baltimore Colts.
  - Simplified: George L. Radosevich (January 25, 1928 – April 4, 2016) was an American football defensive back.
  - Degraded: George L. Radosevich (January 25, 1928 – April 4, 2016) was an American football defensive back.
- Pair: `pair:en:02b7f1815900d5bff8972c8489215b6e94e129ab34d6f539c747c569e9ce7b76`
  - Reason: `simplified_and_degraded_are_identical`
  - Original: The Italy national under-21 football team is the national under-21 football team of Italy and is controlled by the Italian Football Federation.
  - Simplified: The Italy national under-21 football team is the national under-21 football team of Italy.
  - Degraded: The Italy national under-21 football team is the national under-21 football team of Italy.

### SYN

#### Good

- Pair: `pair:en:39daecf6fd62abeec04bc0e9dacfd73e5de6a09012f8d780fad39b840d4d7940`
  - Reason: `all_automatic_checks_passed`
  - Original: The Church of St. Louis of the French ( , , ) is a Roman Catholic church in Rome, not far from Piazza Navona.
  - Simplified: San Luigi dei Francesi is a French church in Rome.The church is found near the Roman Pantheon, Piazza Navona and the French Cultural Center.
  - Degraded: The Church of St. Louis of the French ( , , ) is a Roman Catholic church in Rome, not far from Piazza Navona.
- Pair: `pair:en:4ac68c8ebbb7b2c56195a6a083a834165e5b993755cb4b9a48d9918e3e581d6a`
  - Reason: `all_automatic_checks_passed`
  - Original: Islam in Russia is the nation's second most widely professed religion.
  - Simplified: Islam is the second largest religion of Russia, after Orthodox Christianity.
  - Degraded: Islam in Russia is the nation's second most widely professed religion.

#### Medium

- Pair: `pair:en:0f15d8529189012c2e86e75311aa84dbb20f11b26fd992d1a7673884c5a526ab`
  - Reason: `text_changed_but_declared_span_not_verified`
  - Original: William Kistler Coors (August 11, 1916 – October 13, 2018) was an American brewery executive with the Coors Brewing Company.
  - Simplified: William Kistler "Bill" Coors (August 11, 1916 – October 13,2018) was an American businessman.
  - Degraded: William Kistler 'Bill' Coors (August 11, 1916 – October 13,2018) was an American businessman.
- Pair: `pair:en:228339209b416ae46ac1c03211b0841ef09125bf14bd4515b41d446be2d007d0`
  - Reason: `text_changed_but_declared_span_not_verified`
  - Original: The Department of Social Security (DSS) is a defunct governmental agency in the United Kingdom.
  - Simplified: The Department of Social Security (DSS) was a government department in the United Kingdom.
  - Degraded: The Department of Social Security (DSS) was a defunct government department in the United Kingdom.

#### Failed

- Pair: `pair:en:01ff29a74629f4a9713cbc4bf805b2661dabe9412b0daa24026dd7b7a673bd55`
  - Reason: `simplified_and_degraded_are_identical`
  - Original: Tosh.0 is an American television series hosted and produced by comedian Daniel Tosh, who provides commentary on online viral video clips, society, celebrities, stereotypes, and popular culture as a whole.
  - Simplified: Tosh.0 is an American comedy cable television show that was created by comedian Daniel Tosh.The show focuses on viral videos from the internet with sarcastic commentary, interviews, and short comedy routines.
  - Degraded: Tosh.0 is an American comedy cable television show that was created by comedian Daniel Tosh.The show focuses on viral videos from the internet with sarcastic commentary, interviews, and short comedy routines.
- Pair: `pair:en:081f958c299f70ec8f43a59080137723bf9414e5c9776b24cbbd0faf9d4a89e9`
  - Reason: `simplified_and_degraded_are_identical`
  - Original: Alexandre Silveira Finazzi (born 20 August 1973), is a Brazilian footballer who plays for Goiânia.
  - Simplified: Alexandre Silveira Finazzi (born 20 August 1973) is a Brazilian professional athlete.
  - Degraded: Alexandre Silveira Finazzi (born 20 August 1973) is a Brazilian professional athlete.

## Decision

The 12,140-pair full generation remains blocked. First, human reviewers must adjudicate the 300 pilot examples and prompts/detectors must be revised for every dimension below the agreed 85% valid-degradation threshold.
