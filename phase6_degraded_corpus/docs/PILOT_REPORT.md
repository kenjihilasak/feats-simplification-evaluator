# Phase 6 pilot report

This is the single report for all seven Phase 6 pilots: 50 human-audited Meaning degradations and 300 generated examples covering the other six dimensions.

## Interpretation

- **Accepted:** the Meaning degradation was manually audited and accepted.
- **Good:** all automatic structural checks passed, but semantic human review is still required.
- **Medium:** the text changed, but the declared changed/replacement span was not verified literally.
- **Failed:** no usable degradation was produced, usually because Simplified and Degraded are identical.

The Meaning acceptance rate and the automatic rates for the other dimensions are not directly comparable because their review bases differ.

## Summary

| Dimension | Accepted | Good | Medium | Failed | Review basis |
|---|---:|---:|---:|---:|---|
| MEANING | 50 | 0 | 0 | 0 | human audit |
| FLUENCY | 0 | 10 | 23 | 17 | automatic triage |
| OMIT | 0 | 8 | 14 | 28 | automatic triage |
| SYN | 0 | 6 | 16 | 28 | automatic triage |
| MOD | 0 | 23 | 27 | 0 | automatic triage |
| ILLOC | 0 | 33 | 15 | 2 | automatic triage |
| EXPL | 0 | 39 | 8 | 3 | automatic triage |
| **Total** | **50** | **119** | **103** | **78** | mixed |

## Main findings

- All 50 Meaning cases were manually audited; 19 required manual correction after both Qwen passes failed semantic audit.
- Explanation and Illocution have the strongest automatic results among the six new dimensions.
- Modulation changes every selected sentence, but many outputs have unverifiable span metadata.
- Fluency often claims an edit that is absent from the generated sentence.
- Omission and Synonymy have the most outright failures and require prompt, cue, and source-label review before scaling.
- The 12,140-pair full generation remains blocked until human review validates the six new dimensions.

## All 350 pilot examples

### MEANING

#### MEANING-01

- Pair: `pair:en:048b70c40b46c0adcc9465b11d30a7be17df3f0afede5bf6d64b1cc3e99b1132`
- Source strategy: `OMIT`
- Assigned operation: `entity_replacement`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: Daniele was born to a working-class family in Naples, his father being a harbor worker.
- Simplified: He was born in Naples, Italy.
- Degraded: He was born in Rome, Italy.
- Verification: The city of his birth is contradicted.

#### MEANING-02

- Pair: `pair:en:06a0a34e1fb4b053d900527b1470d52592bae3265de12c0468165ab268961fdc`
- Source strategy: `COMP`
- Assigned operation: `entity_replacement`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: Maroda is located 9 km ahead of Devprayag on the way to Sabdar Khal and Pauri.
- Simplified: It is only 9 km away from Devpryag, on the way to Pauri.
- Degraded: It is only 9 km away from Delhi, on the way to Pauri.
- Verification: Manually corrected after Qwen output failed semantic audit; the replacement directly contradicts the corresponding source fact.

#### MEANING-03

- Pair: `pair:en:0aaae7d734bc58c837541ed1d9b983ac66ac58f09cfe78cd4611723c0bce6490`
- Source strategy: `SYN`
- Assigned operation: `negation_reversal`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: The blue whale is the largest animal known to have ever lived.
- Simplified: The blue whale is the largest animal on Earth.
- Degraded: The blue whale is not the largest animal on Earth.
- Verification: The blue whale is no longer stated as the largest animal on Earth.

#### MEANING-04

- Pair: `pair:en:0b39cee30c199a3a857c20d2917cee52890baef57422c507adce3d276ea4b66b`
- Source strategy: `COMP`
- Assigned operation: `number_replacement`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: David Alan Coulier (born September 21, 1959) is an American stand-up comedian, actor, voice actor, impressionist television host and private pilot.
- Simplified: David Alan "Dave" Coulier (born September 21, 1959) is an American actor, voice actor, stand-up comedian, impressionist, and television host.
- Degraded: David Alan 'Dave' Coulier (born September 21, 1960) is an American actor, voice actor, stand-up comedian, impressionist, and television host.
- Verification: The year of birth is changed from 1959 to 1960.

#### MEANING-05

- Pair: `pair:en:0df8c52340f325ebff32f473e3f49411f0040f7ae83b0eabd3913a562615df90`
- Source strategy: `SYNT`
- Assigned operation: `relation_reversal`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: * Dark chocolate: sugar, cocoa butter, cocoa liquor, and (sometimes) vanilla
- Simplified: Dark or bittersweet chocolate is made from sugar, cocoa butter, and chocolate liquor.
- Degraded: Sugar, cocoa butter, and chocolate liquor are made from dark or bittersweet chocolate.
- Verification: Manually corrected after Qwen output failed semantic audit; the replacement directly contradicts the corresponding source fact.

#### MEANING-06

- Pair: `pair:en:13fa7af0c9d6ecc1804261afa85f8fc0c8b225f4e59d993856d038a06e21bd9d`
- Source strategy: `SYNT`
- Assigned operation: `negation_reversal`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: A spur is an outgrowth of bone covered in a sheath of horn found in various anatomical locations in some animals.
- Simplified: A spur is a bone covered in horn that grows out of an animal's body.
- Degraded: A spur is a bone covered in horn that does not grow out of an animal's body.
- Verification: The original statement indicates that a spur does grow out of an animal's body, which is negated in the distorted version.

#### MEANING-07

- Pair: `pair:en:16d85ffdf0bcb61331adf47448be7f08175e2306ce718c6380abe86c33dce380`
- Source strategy: `OMIT`
- Assigned operation: `number_replacement`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: The league currently consists of 12 teams.
- Simplified: It consists of 12 teams.
- Degraded: It consists of 11 teams.
- Verification: The original fact is that the league currently consists of 12 teams. The direct contradiction is that the league now consists of 11 teams.

#### MEANING-08

- Pair: `pair:en:19137fb62c8bc799aac9681e1ca62159f785fd6913ba68596d99fd87bb939d77`
- Source strategy: `OMIT`
- Assigned operation: `number_replacement`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: Michael Dibdin (21 March 1947 – 30 March 2007) was a British crime writer who was famous for inventing Aurelio Zen, the principal character in 11 crime novels set in Italy.
- Simplified: Michael Dibdin (21 March 1947 – 30 March 2007) was a British crime writer.
- Degraded: Michael Dibdin (2 March 1947 – 30 March 2007) was a British crime writer.
- Verification: The date of birth is changed, contradicting the original fact.

#### MEANING-09

- Pair: `pair:en:21c6819e3297786aa2dafad4692d0d41980abcc9925ab345e59e372892d430f2`
- Source strategy: `SYNT`
- Assigned operation: `event_replacement`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: A trainer is a class of aircraft designed specifically to facilitate flight training of pilots and aircrews.
- Simplified: A training aircraft, sometimes called a trainer, is an aircraft used to train future pilots and crews of aircraft.
- Degraded: A training aircraft, sometimes called a trainer, is an aircraft used to test future pilots and crews of aircraft.
- Verification: Manually corrected after Qwen output failed semantic audit; the replacement directly contradicts the corresponding source fact.

#### MEANING-10

- Pair: `pair:en:30c0c6c3dfc5fdeb03e6c046a218f4389f273dccebdbb8bc9e439d201d677d88`
- Source strategy: `EXPL`
- Assigned operation: `negation_reversal`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: VHD discs are 25 cm in diameter, and store up to 60 minutes of video per side.
- Simplified: VHD discs are 25 cm (9 5/6 inches) in diameter, and store up to 60 minutes of video per side.
- Degraded: VHD discs are 25 cm in diameter, and do not store up to 60 minutes of video per side.
- Verification: The storage capacity of VHD discs is contradicted.

#### MEANING-11

- Pair: `pair:en:35f3a73499ee1375f9c65c61a0d6ee07817f2ab36d2495d948350ea756d3e012`
- Source strategy: `MOD`
- Assigned operation: `entity_replacement`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: Mars is the fourth planet from the Sun and the second-smallest planet in the Solar System after Mercury.
- Simplified: Mars is a planet in the Solar System. It is the fourth-closest planet to the Sun.
- Degraded: Mars is a planet in the Alpha Centauri system. It is the fourth-closest planet to the Sun.
- Verification: Manually corrected after Qwen output failed semantic audit; the replacement directly contradicts the corresponding source fact.

#### MEANING-12

- Pair: `pair:en:375ab0961fbd3f11be93c17d5e5e748f34cdc1017ffba444cbf97157fffa1a0f`
- Source strategy: `SYN`
- Assigned operation: `property_replacement`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: Both symphonies were premiered in a long and under-rehearsed concert in the Theater an der Wien in Vienna on 22 December 1808.
- Simplified: The symphony was first performed in Vienna, Austria, at the Theater an der Wien on 22 December 1808.
- Degraded: The symphony was last performed in Vienna, Austria, at the Theater an der Wien on 22 December 1808.
- Verification: Manually corrected after Qwen output failed semantic audit; the replacement directly contradicts the corresponding source fact.

#### MEANING-13

- Pair: `pair:en:3e806d22087f2862616c7f391085dd084ebd66b199bd495c7b5d6381bb8f7b70`
- Source strategy: `SYNT`
- Assigned operation: `entity_replacement`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: The Sambre ] is a river in northern France and in Wallonia, Belgium.
- Simplified: The Sambre is a river that flows through France and Belgium.
- Degraded: The Sambre is a river that flows through Germany and Belgium.
- Verification: The original fact is that the Sambre flows through France. The direct contradiction is that the distorted sentence states the Sambre flows through Germany instead.

#### MEANING-14

- Pair: `pair:en:3fdebbf8cfccd910969d0672de754a8c9bcc0e4804f3d95bafa2b6670cebd0d6`
- Source strategy: `COMP`
- Assigned operation: `property_replacement`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: Norman Rockwell was born on February 3, 1894, in New York City, to Jarvis Waring Rockwell and Anne Mary "Nancy" Rockwell, born Hill.
- Simplified: Rockwell was born on February 3, 1894 in New York City to Jarvis Waring Rockwell and Anne Mary (Hill) Rockwell.
- Degraded: Rockwell was born on February 3, 1894 in a rural village to Jarvis Waring Rockwell and Anne Mary (Hill) Rockwell.
- Verification: Manually corrected after Qwen output failed semantic audit; the replacement directly contradicts the corresponding source fact.

#### MEANING-15

- Pair: `pair:en:4895db6ba263fb6c27a412308296547e2944ee4c3beaa43710366e6892d6d0be`
- Source strategy: `OMIT`
- Assigned operation: `negation_reversal`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: For its entire existence, it was a very safe Labor seat.
- Simplified: It was a very safe Labor seat.
- Degraded: For its entire existence, it was not a very safe Labor seat.
- Verification: The original sentence stated the seat was safe, which is negated in the distorted version.

#### MEANING-16

- Pair: `pair:en:52b59e2844fb4cd4bbe831c4f313ee0af4c4dd55242fa0d0868ca5b2041a47ac`
- Source strategy: `SYNT`
- Assigned operation: `negation_reversal`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: Meadow voles are an important prey for many hawks, owls, and mammalian carnivores, and they are also taken by some snakes.
- Simplified: The meadow vole is preyed upon by hawks, owls, snakes, and other predators.
- Degraded: The meadow vole is not preyed upon by hawks, owls, snakes, and other predators.
- Verification: The original fact is that meadow voles are preyed upon by hawks, owls, snakes, and other predators. The direct contradiction is that the distorted sentence states they are not preyed upon by these animals.

#### MEANING-17

- Pair: `pair:en:582cf88b3d5b304f339247c120075b72d8261bd2847ec68945afe1925fb476da`
- Source strategy: `SYN`
- Assigned operation: `number_replacement`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: He created roughly 900 oil paintings and more than 2,000 watercolors, as well as countless sketches and charcoal drawings.
- Simplified: During his career, he created about 900 oil paintings and more than 2,000 watercolors, as well as many sketches and charcoal drawings.
- Degraded: During his career, he created about 90 oil paintings and more than 2,000 watercolors, as well as many sketches and charcoal drawings.
- Verification: Manually corrected after Qwen output failed semantic audit; the replacement directly contradicts the corresponding source fact.

#### MEANING-18

- Pair: `pair:en:5896125799250fac9962084ef242e0fce4dbf195bb9386c274224c1b023f415f`
- Source strategy: `SYNT`
- Assigned operation: `negation_reversal`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: The most familiar carriers of electrical charge are the electron and proton.
- Simplified: Both electrons and protons carry a charge.
- Degraded: Neither electrons nor protons carry a charge.
- Verification: Manually corrected after Qwen output failed semantic audit; the replacement directly contradicts the corresponding source fact.

#### MEANING-19

- Pair: `pair:en:5f139d4a4d9cbc6baaaeaa52e023fdfab1e6e136eebc5420e250c29cbd935e21`
- Source strategy: `SYN`
- Assigned operation: `event_replacement`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: A meme ( ) is an idea, behavior, or style that spreads from person to person within a culture-often with the aim of conveying a particular phenomenon, theme, or meaning represented by the meme.
- Simplified: A meme (pronounced "meem") is an element of culture or behaviour that gets transmitted between individuals.
- Degraded: A meme (pronounced "meem") is an element of culture or behaviour that gets concealed from individuals.
- Verification: Manually corrected after Qwen output failed semantic audit; the replacement directly contradicts the corresponding source fact.

#### MEANING-20

- Pair: `pair:en:5f8b7908cb70f4c8970073b8ef1389d5620e24087cb9cf0d420504847a9b9269`
- Source strategy: `COMP`
- Assigned operation: `date_replacement`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: Federal elections were held in Germany on 24 September 2017 to elect the members of the 19th Bundestag.
- Simplified: The 2017 German federal election was held in Germany on 24 September 2017.
- Degraded: The 2017 German federal election was held in Germany on 24 September 2018.
- Verification: The date of the election was changed from 2017 to 2018.

#### MEANING-21

- Pair: `pair:en:6308f6712da886f31d7ae656d83c7ee8fab452b753b6d5a01c904ba86245363f`
- Source strategy: `MOD`
- Assigned operation: `relation_reversal`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: Metro is the second-busiest rapid transit system in the United States in number of passenger trips, after the New York City Subway.
- Simplified: It has the second busiest rapid transit system in the United States.The New York City Subway is the busiest.
- Degraded: The New York City Subway has the second busiest rapid transit system in the United States. Metro is the busiest.
- Verification: The original fact was that Metro has the second busiest rapid transit system, while the distorted sentence incorrectly states that the New York City Subway has the second busiest system and is the busiest, contradicting both points.

#### MEANING-22

- Pair: `pair:en:794ce5d3a2a5c1046735d1338d388261199b7506a5732e6eeb35286bf440232b`
- Source strategy: `SYNT`
- Assigned operation: `entity_replacement`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: The White House is the official residence and workplace of the president of the United States.
- Simplified: The White House is a building in Washington, D.C. where the president of the United States lives.
- Degraded: The White House is a building in New York City where the president of the United States lives.
- Verification: The location of the White House is contradicted.

#### MEANING-23

- Pair: `pair:en:857c4700237ec2c316e62bc03fbdd47eee55341d6e17cd9ce40665e8ea56e6a8`
- Source strategy: `SYN`
- Assigned operation: `event_replacement`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: Chemical biology is a scientific discipline spanning the fields of chemistry and biology.
- Simplified: Chemical biology is a science that combines the fields of chemistry and biology.
- Degraded: Chemical biology is a science that separates the fields of chemistry and biology.
- Verification: The original states that chemical biology spans both fields, while the distorted version claims it separates them, directly contradicting the original statement.

#### MEANING-24

- Pair: `pair:en:87fb34236414226e471fdef95c111e66b4fe089a0251817a681b00802ebf79c1`
- Source strategy: `COMP`
- Assigned operation: `date_replacement`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: Following the agreement, on 1 September 1939, Germany invaded Poland, marking the beginning of World War II in Europe.
- Simplified: In 1939 the German invasion of Poland, began World War II in Europe.
- Degraded: In 1949 the German invasion of Poland began World War II in Europe.
- Verification: Manually corrected after Qwen output failed semantic audit; the replacement directly contradicts the corresponding source fact.

#### MEANING-25

- Pair: `pair:en:8aab3013f5dba5c040dc410ccbbf6507a3b8e2f74e26557269e828a0d45110d1`
- Source strategy: `MOD`
- Assigned operation: `property_replacement`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: Cassowaries have three-toed feet with sharp claws.
- Simplified: Cassowaries have three toes on each foot. Each has a sharp claw.
- Degraded: Cassowaries have three toes on each foot. Each has a blunt claw.
- Verification: Manually corrected after Qwen output failed semantic audit; the replacement directly contradicts the corresponding source fact.

#### MEANING-26

- Pair: `pair:en:8d48bf8709c87728898ec556a46ee8027bf996bb3ea7efb0e297d8021a20d1b4`
- Source strategy: `SYN`
- Assigned operation: `event_replacement`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: Justinian's rule constitutes a distinct epoch in the history of the Later Roman empire, and his reign is marked by the ambitious but only partly realized renovatio imperii, or "restoration of the Empire".
- Simplified: Justinian also increased the territories of his Empire during his reign, for he tried to reconstruct the Roman Empire as it was in the second century.
- Degraded: Justinian also decreased the territories of his Empire during his reign, for he tried to reconstruct the Roman Empire as it was in the second century.
- Verification: The original sentence states that Justinian's reign was marked by an ambitious attempt to restore the Roman Empire, which implies expansion of territories, while the distorted sentence claims a decrease in territories, directly contradicting the original.

#### MEANING-27

- Pair: `pair:en:9351620b5913f84e73902189d44b855eb948bd4fbb70dd81c00c8386c12927db`
- Source strategy: `COMP`
- Assigned operation: `date_replacement`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: Harriet Elisabeth Beecher was born in Litchfield, Connecticut, on June 14, 1811.
- Simplified: She was born on June 14, 1811 in Litchfield, Connecticut.
- Degraded: She was born on June 14, 1711 in Litchfield, Connecticut.
- Verification: The year of Harriet Elisabeth Beecher's birth is contradicted.

#### MEANING-28

- Pair: `pair:en:980a9a8be40f9b6557e68f0b71957885d325bbed7e8f5f7f4f1857914afdc37c`
- Source strategy: `OMIT`
- Assigned operation: `date_replacement`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: Angelo Peruzzi (] ; born 16 February 1970) is an Italian football coach and former goalkeeper, and a three-time winner of the Serie A Goalkeeper of the Year award.
- Simplified: Angelo Peruzzi (born 16 February 1970) is a former Italian football player.
- Degraded: Angelo Peruzzi (born 16 February 1980) is a former Italian football player.
- Verification: Manually corrected after Qwen output failed semantic audit; the replacement directly contradicts the corresponding source fact.

#### MEANING-29

- Pair: `pair:en:98243871f32f5011048499e71f87a016241e346be264c31def6fd68d9a320570`
- Source strategy: `OMIT`
- Assigned operation: `number_replacement`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: The area of the country totals 22960 km2 , an area slightly larger than El Salvador, Israel, New Jersey or Wales.
- Simplified: The area of the country totals 22960 km2.
- Degraded: The area of the country totals 2296 km2.
- Verification: The area is significantly smaller than the original value.

#### MEANING-30

- Pair: `pair:en:9bdce3b79056bf381622bcda0a66ed4522f1198765e21267dfbf467e54296da6`
- Source strategy: `OMIT`
- Assigned operation: `negation_reversal`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: The Iraqi dinar (] ) (Arabic: دينار, (sign: د.ع; code: IQD) is the currency of Iraq.
- Simplified: The Iraqi dinar is the currency of Iraq.
- Degraded: The Iraqi dinar is not the currency of Iraq.
- Verification: The original fact that the Iraqi dinar is the currency of Iraq is contradicted.

#### MEANING-31

- Pair: `pair:en:9e32dda1de0dab2a1cd30d8afc75177189d2ec324d4cf98dca93ae9775d4d5b8`
- Source strategy: `OMIT`
- Assigned operation: `number_replacement`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: They have three children, a daughter born in July 2011 and two sons born in October 2013 and March 2016.
- Simplified: They have three children.
- Degraded: They have two children.
- Verification: Manually corrected after Qwen output failed semantic audit; the replacement directly contradicts the corresponding source fact.

#### MEANING-32

- Pair: `pair:en:a5f6a14ca796f0429acff0a4c25c4cfdc312c0dd45938c9cb803f690d0f86055`
- Source strategy: `OMIT`
- Assigned operation: `number_replacement`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: Beginning in a first competition in 486 BC each playwright submitted a comedy.
- Simplified: From 486 BC, each playwright also submitted a comedy.
- Degraded: From 386 BC, each playwright also submitted a comedy.
- Verification: The year when the first competition began is contradicted.

#### MEANING-33

- Pair: `pair:en:b1f83d5c68a6cce3b298c2856aec2f16a7302644c0a3c982bd38872831e2a0c1`
- Source strategy: `OMIT`
- Assigned operation: `event_replacement`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: Later she returned the award because of her own principles.
- Simplified: Later she returned the award.
- Degraded: Later she refused the award.
- Verification: The act of returning the award is replaced with refusing it.

#### MEANING-34

- Pair: `pair:en:b7d27644d6bd9def62b0afb330d543f39779a82bd8ce70d6bae29d22da27aa8e`
- Source strategy: `OMIT`
- Assigned operation: `relation_reversal`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: It is 302.4 km2 , measuring 28 km long and 22 km wide, making it the 4th largest island in South Korea.
- Simplified: The island measures 28 km long and 22 km wide, and is the 4th largest island in South Korea.
- Degraded: The island measures 28 km wide and 22 km long, and is the 4th largest island in South Korea.
- Verification: Manually corrected after Qwen output failed semantic audit; the replacement directly contradicts the corresponding source fact.

#### MEANING-35

- Pair: `pair:en:b8d469161b761f8125a1685843e3406d92288fb436ea30c9d5b5cb5b1db3b1d9`
- Source strategy: `OMIT`
- Assigned operation: `entity_replacement`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: She was born in Warsaw, in what was then the Kingdom of Poland, part of the Russian Empire.
- Simplified: She was born in Warsaw.
- Degraded: She was born in Warsaw, in what is now the United States.
- Verification: The original sentence states she was born in Warsaw within the Russian Empire, while the distorted sentence incorrectly places her birth in the United States.

#### MEANING-36

- Pair: `pair:en:bc11159233ea5a0dc46d48182d7f3ae5f79caa89a1ffd0b3e2861a6a70c00b3f`
- Source strategy: `OMIT`
- Assigned operation: `entity_replacement`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: The Paris Opera Ballet () is a French ballet company that is an integral part of the Paris Opera and the oldest national ballet company.
- Simplified: The Paris Opera Ballet (in french: Ballet de l'Opéra national de Paris) is the oldest national ballet company in the world.
- Degraded: The London Opera Ballet (in French: Ballet de l'Opéra national de Paris) is the oldest national ballet company in the world.
- Verification: Manually corrected after Qwen output failed semantic audit; the replacement directly contradicts the corresponding source fact.

#### MEANING-37

- Pair: `pair:en:bf795799fec2c94388abe65c47708e1b1377b0f3566660e8b1f84cdc72a60013`
- Source strategy: `SYN`
- Assigned operation: `event_replacement`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: Although larvae eat only milkweed, adult monarchs feed on the nectar of many plants including:
- Simplified: Its larvae feed on milkweed, but the adults feed on the nectar of many flowers.
- Degraded: Its larvae feed on milkweed, but the adults drink water from many flowers.
- Verification: Adults feeding on nectar is replaced with adults drinking water.

#### MEANING-38

- Pair: `pair:en:c3edc1c39452a170f44f3a0aafe1790e493121431fcfa9f565265b0fe7718fbe`
- Source strategy: `SYNT`
- Assigned operation: `entity_replacement`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: A scientist who works in the field of acoustics is an acoustician while someone working in the field of acoustics technology may be called an acoustical engineer.
- Simplified: A scientist who works in the field of acoustics is an acoustician.Someone who works with acoustics technology may be called an acoustical engineer.
- Degraded: A scientist who works in the field of acoustics is a botanist. Someone who works with acoustics technology may be called an acoustical engineer.
- Verification: Manually corrected after Qwen output failed semantic audit; the replacement directly contradicts the corresponding source fact.

#### MEANING-39

- Pair: `pair:en:c8c25d0948b690593a902738e1a2024b3debce7c78e623ff8354d6a69238b33c`
- Source strategy: `COMP`
- Assigned operation: `entity_replacement`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: The flag of the Republic of Turkey, often referred to as the Turkish flag is a red flag featuring a white star and crescent.
- Simplified: The flag of Turkey has a white crescent moon and a star on a red background.
- Degraded: The flag of Greece has a white crescent moon and a star on a red background.
- Verification: The country of the flag in the original sentence is Turkey, which is replaced with Greece in the simplified sentence.

#### MEANING-40

- Pair: `pair:en:cdb3f395b118000612b890da10d71023f4f1eb93d646a46582a83fc80b90c78a`
- Source strategy: `SYN`
- Assigned operation: `negation_reversal`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: The furcula works as a strut between a bird's shoulders, and articulates to each of the bird's scapulae.
- Simplified: It is a strut between a bird's shoulders, and connects to each of the bird's scapulae (shoulder blades).
- Degraded: It is not a strut between a bird's shoulders, and connects to each of the bird's scapulae (shoulder blades).
- Verification: The original fact that it works as a strut is contradicted.

#### MEANING-41

- Pair: `pair:en:d091e4eb93c0c1c90f60bba7f5656af0df893ead8a9ee84689df91ae5d06c854`
- Source strategy: `OMIT`
- Assigned operation: `number_replacement`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: The Blue Nile flows about 1,400 kilometres to Khartoum, where the Blue Nile and White Nile join to form the Nile.
- Simplified: The Blue Nile flows about 1,400 kilometres to Khartoum.
- Degraded: The Blue Nile flows about 140 kilometres to Khartoum.
- Verification: Manually corrected after Qwen output failed semantic audit; the replacement directly contradicts the corresponding source fact.

#### MEANING-42

- Pair: `pair:en:d71abf09cffb0bfab29029537f7feaa769d78886a96bd5c2f75e8c6ad2c21f73`
- Source strategy: `SYNT`
- Assigned operation: `entity_replacement`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: In the late 19th century, Japan was still largely unknown and exotic to Westerners.
- Simplified: In the late 19th century, Westerners knew little about Japan.
- Degraded: In the late 19th century, Japanese knew little about Japan.
- Verification: The knowledge level of Westerners about Japan is contradicted.

#### MEANING-43

- Pair: `pair:en:e313df9149034a0c5de0068a4c95c78c820c0e6f5789eefec64c4a802990e111`
- Source strategy: `OMIT`
- Assigned operation: `property_replacement`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: Destelbergen (] ) is a municipality located in the Belgian province of East Flanders.
- Simplified: Destelbergen is a municipality in the Belgian province of East Flanders.
- Degraded: Destelbergen is a municipality in the French province of East Flanders.
- Verification: The original fact is that Destelbergen is in the Belgian province of East Flanders, which is directly contradicted by stating it is in the French province of East Flanders.

#### MEANING-44

- Pair: `pair:en:e8ccfd28ae5bbd4083ece12c239272c5ff28cca18b6a02501d8ae687a5c905a0`
- Source strategy: `SYNT`
- Assigned operation: `negation_reversal`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: Osteoarthritis begins in the cartilage and eventually causes the two opposing bones to erode into each other.
- Simplified: Osteoarthritis is caused by cartilage between the bones wearing down.
- Degraded: Osteoarthritis is not caused by cartilage between the bones wearing down.
- Verification: The original fact is that osteoarthritis is caused by cartilage wearing down. The direct contradiction is that the distorted sentence states it is not caused by this process.

#### MEANING-45

- Pair: `pair:en:f0e577bd8f0b531d490e43eb514defead6cde8276783674d2cc939a4044a7ea9`
- Source strategy: `SYN`
- Assigned operation: `property_replacement`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: The original texts of the Tanakh were mainly in Hebrew, with some portions in Aramaic.
- Simplified: In the Old Testament, Tanakh was mostly written in Hebrew; a few parts were written in Aramaic.
- Degraded: In the Old Testament, Tanakh was mostly written in Hebrew; a few parts were written in Greek.
- Verification: The original fact that some portions of the Tanakh were written in Aramaic is contradicted.

#### MEANING-46

- Pair: `pair:en:f705c0ccf28f95b6f9ef8c77097a06636bb62b899a1c0631934cda5813a603a4`
- Source strategy: `COMP`
- Assigned operation: `relation_reversal`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: Dinosaurs laid eggs, some of which have been preserved as petrified fossils.
- Simplified: Dinosaurs also laid eggs, of which fossils have been found.
- Degraded: Fossilized eggs produced dinosaurs.
- Verification: Manually corrected after Qwen output failed semantic audit; the replacement directly contradicts the corresponding source fact.

#### MEANING-47

- Pair: `pair:en:f79f2ef73ffd68d9987a2a8b3ab7a2d084ab5828c88e276b4ee1a377ac431d32`
- Source strategy: `SYNT`
- Assigned operation: `relation_reversal`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: Some salamander species use tail autotomy to escape predators.
- Simplified: Salamanders can drop their tail to escape predators.
- Degraded: Predators can drop their tail to escape salamanders.
- Verification: Salamanders using tail autotomy to escape predators is reversed to predators dropping tails to escape salamanders, directly contradicting the original statement.

#### MEANING-48

- Pair: `pair:en:fbc3a088d1a0018070d3cff4e5c84ec1985a457e806a31738394be5e902d0a13`
- Source strategy: `MOD`
- Assigned operation: `relation_reversal`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: Nearly half of all the mud volcanoes on Earth are concentrated in Azerbaijan, these volcanoes were also among nominees for the New7Wonders of Nature.
- Simplified: Another interesting feature of Azerbaijan are the mud volcanoes - half of all mud volcanoes in the world are situated in Azerbaijan.
- Degraded: Another interesting feature of Azerbaijan are the mud volcanoes - half of all mud volcanoes in the world situate in other countries.
- Verification: The original fact is that half of all mud volcanoes are in Azerbaijan. The direct contradiction is that half of all mud volcanoes are in other countries.

#### MEANING-49

- Pair: `pair:en:fc0a5943accc4e7ff64065c9bfe4dc4a99d90b256d69868a7091c6ec94c31894`
- Source strategy: `COMP`
- Assigned operation: `relation_reversal`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: Cloning is the process of producing genetically identical individuals of an organism either naturally or artificially.
- Simplified: In biology, cloning is the process of producing one or more genetically-identical individuals.
- Degraded: In biology, cloning is produced by one or more genetically-identical individuals.
- Verification: Manually corrected after Qwen output failed semantic audit; the replacement directly contradicts the corresponding source fact.

#### MEANING-50

- Pair: `pair:en:fc14dd8791b3e40f955df18d79b6fa88d94b6cbb95a92ca7237fbf1a4f89f18e`
- Source strategy: `EXPL`
- Assigned operation: `number_replacement`
- Quality: **Accepted** (`human_audited_meaning_degradation`; human_audit)
- Original: The distance of the course (run counterclockwise around France) was 3657 km .
- Simplified: The distance of the race was 3657 km (2272 mi).
- Degraded: The distance of the course (run counterclockwise around France) was 2657 km.
- Verification: The distance of the course.

### FLUENCY

#### FLUENCY-01

- Pair: `pair:en:06ae391ca30d4dfecb0de5b991384bf45a7daf8c19288bcea7f1556d4c4eabef`
- Source strategy: `EXPL`
- Assigned operation: `local_word_order_error`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Theodoros Angelopoulos was born in Athens on 27 April 1935.
- Simplified: Angelopoulos was born in Athens, Greece on April 27, 1935 and studied at the University of Paris.
- Degraded: Angelopoulos was born in Athens, Greece on April 27, 1935 and studied at the University of Paris.
- Verification: The word order around 'born' has been altered to introduce an error while keeping the original meaning intact.

#### FLUENCY-02

- Pair: `pair:en:08810a2cf650a7fcb79299845f9d6bdf6b7473edede82c80dcdda9e59f223992`
- Source strategy: `EXPL`
- Assigned operation: `determiner_error`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: LaVey was born Howard Stanton Levey on April 11, 1930 in Chicago, Illinois.
- Simplified: LaVey was born with the name Howard Stanton Levey and was of Jewish descent.He was born in Chicago, Illinois.
- Degraded: LaVey was born with the name Howard Stanton Levey and was of Jewish descent. He was born in Chicago, Illinois.
- Verification: Changed 'He' to 'They' to introduce a determiner error.

#### FLUENCY-03

- Pair: `pair:en:1b9a7a528413aeb7cfce456e4b851abf05235cbdc358bda7f765e5674f58639f`
- Source strategy: `EXPL`
- Assigned operation: `determiner_error`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Willie Aames (born Albert William Upton on July 15, 1960) is an American actor, film and television director, television producer, and screenwriter.
- Simplified: Willie Aames (born Albert William Upton July 15, 1960 in Los Angeles, California) is an actor famous for the roles of Buddy Lembeck on "Charles in Charge", Tommy Bradford on "Eight is Enough" and the voice of Hank on "Dungeons & Dragons", the cartoon.
- Degraded: Willie Aames (born Albert William Upton July 15, 1960 in Los Angeles, California) is an actor famous for the roles of Buddy Lembeck on 'Charles in Charge', Tommy Bradford on 'Eight is Enough' and the voice of Hank on Dungeons & Dragons, the cartoon.
- Verification: Changed 'the' to 'a' to introduce a determiner error.

#### FLUENCY-04

- Pair: `pair:en:1dd5e9312f8bc0c4fc4947ed74cf47de0eb47b58bd2ec99dd39bab743755bfd4`
- Source strategy: `EXPL`
- Assigned operation: `local_word_order_error`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Sarah Victoria "Torri" Higginson is a Canadian actress.
- Simplified: Sarah Victoria "Torri" Higginson (born Burlington, Ontario, December 6, 1969) is a Canadian actress.
- Degraded: Sarah Victoria "Torri" Higginson (born Burlington, Ontario, December 6, 1969) is a Canadian actress.
- Verification: The order of 'Higginson' and '"Torri"' is swapped, creating a grammatical error.

#### FLUENCY-05

- Pair: `pair:en:1e163c9fc4f027c174ffc3d2a14221f606751c8c40daba2eecb7baf372256e7e`
- Source strategy: `EXPL`
- Assigned operation: `preposition_error`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: "Eat It" is a 1984 song by comedy music artist "Weird Al" Yankovic.
- Simplified: "Eat It" is a song by "Weird Al" Yankovic.It was released in 1984 for the album "Weird Al" Yankovic in 3-D".
- Degraded: "Eat It" is a song by "Weird Al" Yankovic. It was released 1984 for the album "Weird Al" Yankovic in 3-D.
- Verification: Changed 'for the album' to 'in 1984', introducing a preposition error.

#### FLUENCY-06

- Pair: `pair:en:202c495d716089aa9e7140561fcd5b9300f25269d4143ccef196a3c94e7eb4ed`
- Source strategy: `EXPL`
- Assigned operation: `local_word_order_error`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Summary An average Gregorian year is 365.2425 days (52.1775 weeks, hours, minutes or seconds).
- Simplified: In the most used calendar, called Gregorian calendar, a year is a period of 365 days starting from the first of January.
- Degraded: In the most used calendar, called Gregorian calendar, a year is a period of 365 days starting from the first of January.
- Verification: The words 'most used' have been swapped to create a grammatical error while preserving the original meaning.

#### FLUENCY-07

- Pair: `pair:en:210147a2f68e7302415eb7005c2121f2b50632e24d0e41565ad46446a40bed6a`
- Source strategy: `EXPL`
- Assigned operation: `local_word_order_error`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: "Sil" means "actual" or "practical," and "hak" means "studies" or "learning."
- Simplified: "Sil" means "actual" or "practical," and "hak" means "studies" or "learning".It also meant "practical learning", like teaching how to farm and about economy.
- Degraded: Sil means actual or practical, and hak means studies or learning. It also meant practical learning, like teaching how to farm and about economy.
- Verification: Swapped 'actual' and 'practical'

#### FLUENCY-08

- Pair: `pair:en:21d9dbafb59a7479e7d0d3bc1726b9555376eb0c80f5b21def2645eaeba6c5ec`
- Source strategy: `COMP`
- Assigned operation: `local_word_order_error`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: When three people have sex with each other, it is called a "threesome".
- Simplified: When three people have sex with each other, it is called a threesome.
- Degraded: When three people have sex with each other, it is called a threesomes.
- Verification: Changed the singular noun to plural, creating a grammatical error.

#### FLUENCY-09

- Pair: `pair:en:22a13e69082b169aa5d2b3ad9732d2828316aa97caf5ffedf6118a669dcc1018`
- Source strategy: `EXPL`
- Assigned operation: `determiner_error`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Mark Duggan was born on 15 September 1981 and grew up in Broadwater Farm, north London.
- Simplified: Duggan was born on 15 September 1981 to a white mother, Pamela Duggan, and a black father, Bruno Hall.He grew up in Broadwater Farm.
- Degraded: Duggan was born on 15 September 1981 to a white mother, Pamela Duggan, and a black father, Bruno Hall. He grew up in Broadwater Farm.
- Verification: Changed 'a' to 'the' to introduce a determiner error.

#### FLUENCY-10

- Pair: `pair:en:299fea736aada3c670e04bed71c99c89b43bdd20a95040776e2d27b05e64549c`
- Source strategy: `EXPL`
- Assigned operation: `local_word_order_error`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Robert William Corddry (born February 4, 1971) is an American actor and comedian.
- Simplified: Robert William "Rob" Corddry (born February 4, 1971) is an American movie, television, voice actor, television director and producer, writer and comedian who is known for his roles in "Hot Tub Time Machine" and in "Childrens Hospital".
- Degraded: Robert William 'Rob' Corddry (born February 4, 1971) is an American movie, television, voice actor, television director and producer, writer and comedian who is known for his roles in 'Hot Tub Time Machine' and in 'Childrens Hospital'.
- Verification: The order of 'Rob' and Corddry has been swapped.

#### FLUENCY-11

- Pair: `pair:en:2e83e98a00c7577c84bd7e39d581fcad9e7c56d564a9496cf283c22d0ef47b33`
- Source strategy: `EXPL`
- Assigned operation: `agreement_error`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: The judiciary of Germany is the system of courts that interprets and applies the law in Germany.
- Simplified: The judiciary, that is, the judges and Courts of Germany are independent.Federal law sets out the structure of the judiciary.
- Degraded: The judiciary, that is, the judges and Courts of Germany are independent. Federal law sets out the structure of the judiciary.
- Verification: Changed 'Courts' to 'court' to introduce a subject-verb disagreement.

#### FLUENCY-12

- Pair: `pair:en:3439ef04e2511c0cd71d47f3ca23f0be3a0989474050a9c70b9cc05ab0274c60`
- Source strategy: `SYNT`
- Assigned operation: `local_word_order_error`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: The population of the city is about 1 million people.
- Simplified: About 1 million people live there.
- Degraded: About 1 million lives there.
- Verification: The word order is altered to introduce a grammatical error while preserving the original meaning.

#### FLUENCY-13

- Pair: `pair:en:44118cbc6259530a0f46542e8934c93c5e4ec2cdaca570f9bd3bbb453a2e3465`
- Source strategy: `EXPL`
- Assigned operation: `agreement_error`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Chlorine dioxide is a chemical compound with the formula ClO.
- Simplified: Chlorine dioxide is a chemical compound (a thing made when two or more chemical elements attach to each other).Its chemical formula is ClO.
- Degraded: Chlorine dioxide is a chemical compound (a thing made when two or more chemical elements attach to each other). Its chemical formula is ClO.
- Verification: Changed 'Its' to 'It's' to introduce an agreement error.

#### FLUENCY-14

- Pair: `pair:en:44cf62197bc748111937482309d600a01be36c10013775214a38e60708fab720`
- Source strategy: `EXPL`
- Assigned operation: `local_word_order_error`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Alicia Gräfin "(Countess)" von Rittberg (born 10 December 1993) is a German actress.
- Simplified: Alicia Gräfin von Rittberg (born 10 December, 1993 in Munich, Bavaria) is a German actress.
- Degraded: Alicia Gräfin von Rittberg (born 10 December, Munich, Bavaria) is a German actress.
- Verification: The date order is correct but the city and state are incorrectly placed after the comma.

#### FLUENCY-15

- Pair: `pair:en:4a1ffccc1986c51b26242f703ac13cba48ce4f0d410c663e967287c61efb1d9f`
- Source strategy: `EXPL`
- Assigned operation: `preposition_error`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Married to actress Adela Gleijer, he was father of the actress Andrea Tenuta.
- Simplified: He was married to actress Adela Gleijer until his death in 2013.He was father of the actress Andrea Tenuta.
- Degraded: He was married to actress Adela Gleijer, he was father of the actress Andrea Tenuta.
- Verification: Changed 'to' to 'to' creating a redundant preposition.

#### FLUENCY-16

- Pair: `pair:en:4a3e46193f8c0a36cbcabe2242800c0e74cd89c882806c83d753cc5fc2b639fb`
- Source strategy: `EXPL`
- Assigned operation: `preposition_error`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Its full official name is International Statistical Classification of Diseases and Related Health Problems.
- Simplified: The International Statistical Classification of Diseases and Related Health Problems (also known as ICD) is a list of codes that classify diseases and medical problems.
- Degraded: Its full official name is International Statistical Classification of Diseases and Related Health Problems.
- Verification: The preposition 'of' was replaced with 'for' to introduce an error while maintaining the original meaning.

#### FLUENCY-17

- Pair: `pair:en:4ac4295d700d521c89d70dbcc47f84a5b7e69649b68509d3abf96d15363160de`
- Source strategy: `COMP`
- Assigned operation: `determiner_error`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: A modern bombilla design uses a straight tube with holes, or a spring sleeve to act as a sieve.
- Simplified: A modern "bombilla" uses a straight tube with holes, or spring sleeve to act as a sieve.
- Degraded: A modern 'bombilla' uses the a straight tube with holes, or spring sleeve to act as a sieve.
- Verification: Changed 'a' to 'the' to introduce a determiner error while preserving the original meaning.

#### FLUENCY-18

- Pair: `pair:en:4f75186ce9bc9cb4f57edf1b5ee8ed3d35be4396af445d9b5a42ca5fa47b220c`
- Source strategy: `EXPL`
- Assigned operation: `local_word_order_error`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: The Shoku Nihongi (続日本紀 ) is an imperially commissioned Japanese history text.
- Simplified: Shoku Nihongi (続日本紀) is an ancient history of Japan written in 797.
- Degraded: Shoku 続日本紀 is an ancient history of Japan written in 797.
- Verification: The word order error is introduced by swapping '續' and '日本紀', which are part of a compound title.

#### FLUENCY-19

- Pair: `pair:en:5203767b3a4cc5b5394c8e5bc3a4e6e51eed84f8b09b46264486afd30f6576a9`
- Source strategy: `EXPL`
- Assigned operation: `local_word_order_error`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: They were developed in the 19th century, but declined in popularity with the advent of cheap electric lighting.
- Simplified: They were much used in the late 19th and early 20th centuries when electric lighting was very expensive.
- Degraded: They were much used in the late 19th and early 20th centuries when electric lighting was very expensive.
- Verification: The words 'much' and 'used' have been swapped, creating a grammatical error.

#### FLUENCY-20

- Pair: `pair:en:53d87bb956fbb2408404e32242b69bf1a4e34c24dec21b35fb0836b81d7d0e56`
- Source strategy: `EXPL`
- Assigned operation: `preposition_error`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Pamela Denise Anderson (born July 1, 1967) is a Canadian-American actress, model and animal rights activist.
- Simplified: Pamela Denise Anderson (born July 1, 1967 in Ladysmith, British Columbia, Canada) is a Canadian-American actress, sex symbol, glamour model, producer, television personality, and author.
- Degraded: Pamela Denise Anderson (born July 1, 1967 in Ladysmith, British Columbia, Canada) is a Canadian-American actress, sex symbol, glamour model, producer, television personality, and author.
- Verification: Changed 'in' to 'from' to introduce a preposition error while preserving the original meaning.

#### FLUENCY-21

- Pair: `pair:en:5685a13fd9bf1d50807747ccd57074aa9db7cf2b81c62e12ec69ce3b4914bd46`
- Source strategy: `EXPL`
- Assigned operation: `local_word_order_error`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Richard William Farnsworth (September 1, 1920 – October 6, 2000) was an American actor and stuntman.
- Simplified: Richard W. Farnsworth (September 1, 1920 – October 6, 2000) was an American television, stage, radio, voice, and movie actor, and a stuntman.
- Degraded: Richard W. Farnsworth (September 1, 1920 – October 6, 2000) was an American television, stage, radio, voice, and movie actor and stuntman.
- Verification: The order of 'stuntman' and 'and' has been swapped to create a grammatical error.

#### FLUENCY-22

- Pair: `pair:en:5af53293add2f573cc60a1497fe0b8179934bab4623da7800090dba2df6e1718`
- Source strategy: `EXPL`
- Assigned operation: `preposition_error`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: The iron sand is put in a tatara, a clay tub furnace.
- Simplified: The iron sand is put in a clay tub (furnace) called a "tatara".
- Degraded: The iron sand is in a clay tub (furnace) called a 'tatara'.
- Verification: Changed 'in a' to 'put in' to introduce a preposition error while preserving the original meaning.

#### FLUENCY-23

- Pair: `pair:en:5f8627bf606710a389734e5c8684ed3adf7ebe6597b9d6f0bce05f9905d594a4`
- Source strategy: `EXPL`
- Assigned operation: `preposition_error`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Bryan Owen "Pete" Young (born March 19, 1968) is an American former professional baseball pitcher.
- Simplified: Bryan Owen "Pete" Young (born March 19 1968 in Meadville, Mississippi) is a former right-handed relief pitcher in Major League Baseball who played for the Montreal Expos in 1992 and 1993.
- Degraded: Bryan Owen "Pete" Young (born March 19 1968 in Meadville, Mississippi) is a former right-handed relief pitcher in Major League Baseball who played for the Montreal Expos on 1992 and 1993.
- Verification: Changed 'in' to 'on' to introduce a preposition error while preserving the original meaning.

#### FLUENCY-24

- Pair: `pair:en:61c6b42766b61720023fc62f467bd32cb421733c3e684aa9a783dfcb69b44d59`
- Source strategy: `EXPL`
- Assigned operation: `preposition_error`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Les Cayes has an airport, Antoine-Simon Airport.
- Simplified: There is also an airport, Antoine Simon Airport, with the name of a president of Haiti that was born in Les Cayes.
- Degraded: Les Cayes has an airport, Antoine-Simon Airport.
- Verification: Changed the preposition 'of' to 'with' to introduce a grammatical error while preserving the original meaning.

#### FLUENCY-25

- Pair: `pair:en:7043324323583ee4969658f72f13404e52475efccef2c93245fd6ce8cf868734`
- Source strategy: `EXPL`
- Assigned operation: `local_word_order_error`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: By 1700, however, the empire had broken up into areas controlled by many individual ethnic groups.
- Simplified: By 1700 the empire had broken up into areas that were controlled by individual groups of people which was known by the Portuguese by collecting information.
- Degraded: By 1700 the empire had broken up into areas that were controlled by individual groups of people which the Portuguese by collecting information.
- Verification: The word order around 'the Portuguese' has been altered to introduce a grammatical error while preserving the original meaning.

#### FLUENCY-26

- Pair: `pair:en:74f42b4445c6055d79f541d97c1085af30c490164c61e0fd130c30bd75be0438`
- Source strategy: `EXPL`
- Assigned operation: `determiner_error`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Jeff Bennett (born October 2, 1962) is an American voice actor and singer.
- Simplified: Jeffrey Glen "Jeff" Bennett (born October 2, 1962 in Houston, Texas) is an American voice actor and singer.
- Degraded: Jeff Bennett (born October 2, 1962) is a American voice actor and singer.
- Verification: Changed 'an' to 'a' before the adjective 'American'.

#### FLUENCY-27

- Pair: `pair:en:8023a2f712d2a9b34836f23d3b24115a847517ddc4769399b17051511df0a392`
- Source strategy: `EXPL`
- Assigned operation: `agreement_error`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Kawasaki Frontale (川崎フロンターレ , Kawasaki Furontāre ) is a J1 League association football club.
- Simplified: Kawasaki Frontale (川崎フロンターレ, Kawasaki Furontāre) is a Japanese professional football club in Kawasaki, which is south of Tokyo in Kanagawa Prefecture.
- Degraded: Kawasaki Frontale (川崎フロンターレ, Kawasaki Furontāre) is a Japanese professional football club in Kawasaki, which is south of Tokyo in Kanagawa Prefecture.
- Verification: The sentence now incorrectly suggests that the club plays in its city rather than being based there.

#### FLUENCY-28

- Pair: `pair:en:835c18713a3e04bc6bc087117db1b44f1437a495cfa993c12d60e6982383da89`
- Source strategy: `EXPL`
- Assigned operation: `determiner_error`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Isekai (Japanese: 異世界 , "different world") is the portal fantasy subgenre of Japanese light novels, manga, anime, and video games.
- Simplified: Isekai (Japanese: 異世界, "different world") is an anime that has a character from the real world go into a fantasy world via rebirth.
- Degraded: Isekai (Japanese: 異世界, "different world") is an anime that a character from the real world goes into a fantasy world via rebirth.
- Verification: Changed 'that' to 'a' to introduce a determiner error while preserving the core meaning.

#### FLUENCY-29

- Pair: `pair:en:8a06b839c36e4f886b1df47ddb6256f0a6b566350c9f9a8a2800ddc1ac049b4c`
- Source strategy: `EXPL`
- Assigned operation: `agreement_error`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Around this time she was living in France and studying psychology at the Sorbonne.
- Simplified: During the father's murder she was living in France and studying psychology at the Sorbonne University.
- Degraded: During the father's murder she was living in France and studying psychology at the Sorbonne University.
- Verification: The subject 'she' does not agree with the plural verb 'were'.

#### FLUENCY-30

- Pair: `pair:en:8a49192fca85c50ab142df7c0339ef1e91e9a923d8c9f3e4d3887fbff1261e91`
- Source strategy: `EXPL`
- Assigned operation: `local_word_order_error`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Climate is extremely arid albeit somewhat milder near the coast.
- Simplified: The climate of the region is extremely arid (a desert climate) but somewhat milder near the coast and the highest mountains.
- Degraded: The climate of the region is extremely arid (a desert climate) but somewhat milder near the coast and the highest mountains.
- Verification: Changed 'of the region' to 'the region of' to introduce a local word order error while preserving the original meaning.

#### FLUENCY-31

- Pair: `pair:en:8dc1480ee0737b0fe1ee5dee456c00f25d6f007e93545f489ad3fc9244d01a98`
- Source strategy: `EXPL`
- Assigned operation: `preposition_error`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Sulfur was used for fumigation in preclassical Greece; this is mentioned in the "Odyssey".
- Simplified: Sulfur was used in fumigation (making fumes) and medicine in ancient Greece.
- Degraded: Sulfur was used in fumigation (making fumes) and medicine in ancient Greece.
- Verification: Changed 'in' to 'during' to introduce a preposition error while preserving the original meaning.

#### FLUENCY-32

- Pair: `pair:en:9c0217b23f56b092877f9e7e239186fd27e4ec11d01eecdced8a92d785577016`
- Source strategy: `EXPL`
- Assigned operation: `preposition_error`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Serj Tankian (] ; ; born August 21, 1967) is an American musician, singer, songwriter, multi-instrumentalist, record producer, poet and political activist.
- Simplified: Serj Tankian (born on August 21, 1967 in Beirut, Lebanon) is an Armenian-American musician who lives in Los Angeles.
- Degraded: Serj Tankian (born on August 21, 1967 in Beirut, Lebanon) is an Armenian-American musician who lives in Los Angeles.
- Verification: Changed 'on' to 'in' to introduce a preposition error while preserving the original meaning.

#### FLUENCY-33

- Pair: `pair:en:9c29c9239ff1dcee00cb1f8f0e6c7cc3c482f02e4313cca03f0b9d404399e9a8`
- Source strategy: `EXPL`
- Assigned operation: `agreement_error`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Sol Polansky (November 7, 1926 – January 6, 2016) was an American diplomat.
- Simplified: Sol Polansky (November 7, 1926 – January 6, 2016) was an American diplomat.Polansky died after a long illness on January 6, 2016, aged 89.
- Degraded: Sol Polansky (November 7, 1926 – January 6, 2016) was an American diplomat.Polansky died after a long illness on January 6, 2016, aged 89.
- Verification: The subject 'Polansky' does not agree with the verb 'was' in the first sentence, but agrees with 'died' in the second sentence.

#### FLUENCY-34

- Pair: `pair:en:a38284406650663417f189f612e5aaa9f0dfd8178267c1ba95c4cd8e8f0e31af`
- Source strategy: `EXPL`
- Assigned operation: `preposition_error`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: William A. Thomas (October 21, 1948 – January 18, 2019) was an American football player and coach.
- Simplified: William A. Thomas (October 21, 1948 – January 18, 2019) was an American football player and coach.Thomas died on January 18, 2019 at the age of 70.
- Degraded: William A. Thomas (October 21, 1948 – January 18, 2019) was an American football player and coach.Thomas died on January 18, 2019 at the age of 70.
- Verification: The preposition 'on' has been replaced with 'in' to introduce a grammatical error while preserving the original meaning.

#### FLUENCY-35

- Pair: `pair:en:a5ca1009a954cc54dc19881d74c264547a64e1ffd3a7ce72c48bcf48f7a8bec4`
- Source strategy: `EXPL`
- Assigned operation: `preposition_error`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Penicillin was discovered in 1928 by Scottish scientist Alexander Fleming.
- Simplified: Penicillin was discovered by Scottish scientist Sir Alexander Fleming in 1928, but it was not mass-produced until 1940.Penicillin was discovered when Fleming noticed a mold that was stopping bacteria from growing in a petri dish.
- Degraded: Penicillin was discovered by Scottish scientist Sir Alexander Fleming in 1928, but it was not mass-produced until 1940.Penicillin was discovered when Fleming noticed a mold that was stopping bacteria from growing in a petri dish.
- Verification: Changed 'by' to 'in' which is a preposition error.

#### FLUENCY-36

- Pair: `pair:en:a9ba7eea4819c4993fe00fb56535eefd3bf95120436705092cf6338c501d73df`
- Source strategy: `SYNT`
- Assigned operation: `determiner_error`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: He was preparing to direct "Kite" at the time.
- Simplified: At the end of his life he was directing "Kite".
- Degraded: At the end of his life he was directing 'Kite'.
- Verification: Changed 'the end' to 'end', introducing a determiner error.

#### FLUENCY-37

- Pair: `pair:en:ac3bdbfe211175f9596491758d1f6eca6e7ac27a4ad70e8b8850c587128e9d2f`
- Source strategy: `EXPL`
- Assigned operation: `preposition_error`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: A spokeswoman for the Russian Academy of Sciences, announced that Ginzburg died in Moscow on 8 November 2009 from cardiac arrest.
- Simplified: Ginzburg died in Moscow on November 8, 2009 from cardiac arrest, aged 93.
- Degraded: Ginzburg died at Moscow on November 8, 2009 from cardiac arrest, aged 93.
- Verification: Changed 'in' to 'at' which is a preposition error.

#### FLUENCY-38

- Pair: `pair:en:ade5efad73c64621e06fbb2d778ec8134439b180154309abf85e5a879e38c7cd`
- Source strategy: `EXPL`
- Assigned operation: `preposition_error`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: The Battle of Crete ( , also "Unternehmen Merkur", "Operation Mercury," ) was fought during the Second World War on the Greek island of Crete.
- Simplified: The Battle of Crete was a battle fought in World War 2 between the Nazis and British Commonwealth soldiers with Greek support.The battle was fought on the Greek island of Crete.
- Degraded: The Battle of Crete was a battle fought in World War 2 between the Nazis and British Commonwealth soldiers with Greek support. The battle was fought on the Greek island of Crete.
- Verification: Changed 'during' to 'of' which is a preposition error.

#### FLUENCY-39

- Pair: `pair:en:adfcc73482ad4c45ba19ed229094d24c020bdb27632f23d50eba74793a491071`
- Source strategy: `EXPL`
- Assigned operation: `agreement_error`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Sonie Rajbhandari is a Nepalese model & beauty queen.
- Simplified: Sonie Rajbhandari born in Kathmandu, Nepal is a Nepali Model and the title winner of Miss Nepal International 2014.
- Degraded: Sonie Rajbhandari born in Kathmandu, Nepal is a Nepali Model and the title winner of Miss Nepal International 2014.
- Verification: The subject 'Sonie Rajbhandari' is third person singular, thus 'was' should replace 'is'.

#### FLUENCY-40

- Pair: `pair:en:c6bb736741c5a8094140eb10cb5e5362c61edc89a635ca11071df6f127187f3c`
- Source strategy: `EXPL`
- Assigned operation: `preposition_error`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: In 480 the Persians returned under a new ruler, Xerxes I.
- Simplified: In 480 BC the Persians arrived and attacked the Greeks, both on land and on sea.
- Degraded: In 480 BC the Persians arrived and attacked the Greeks, both on land and in sea.
- Verification: Changed 'on' to 'in' to introduce a preposition error while preserving the original meaning.

#### FLUENCY-41

- Pair: `pair:en:c80693c238cd932dd4969699dfad29a6b09024314d467babaa855100010cdc81`
- Source strategy: `EXPL`
- Assigned operation: `determiner_error`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: 2 is the second live album by the British rock band Slade.
- Simplified: 2 is a 1978 rock album by English band Slade.It was the band's second live album.Released during the band's period of low popularity, the album failed to chart or gain the same success as the first live album "Slade Alive!"
- Degraded: 2 is a 1978 rock album by English band Slade. It was the band's second live album. Released during the band's period of low popularity, the album failed to chart or gain the same success as the first live album 'Slade Alive!'
- Verification: Changed 'a' to 'the' before the year.

#### FLUENCY-42

- Pair: `pair:en:cbdbf1b766af3d14dd719ecfd68a650ba8fc3874f2347fff107b562d48ae1bf6`
- Source strategy: `EXPL`
- Assigned operation: `agreement_error`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Bahrain is a generally flat and arid archipelago in the Persian Gulf.
- Simplified: Bahrain is a flat and dry archipelago, with a low desert plain rising gently to a low central hill, in the Arabian Gulf, east of Saudi Arabia.
- Degraded: Bahrain is a flat and dry archipelago, with a low desert plain rising gently to a low central hill, in the Arabian Gulf, east of Saudi Arabia.
- Verification: The simplification changes 'generally' to 'and', which does not agree in form.

#### FLUENCY-43

- Pair: `pair:en:ccfbbe55b48ebb3c345b5472b0bc86871103ece6ea18ed3f0e66ad8235e53630`
- Source strategy: `COMP`
- Assigned operation: `determiner_error`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: The 50PLUS (] ), abbreviated to 50+, is a political party in the Netherlands that advocates pensioners' interests.
- Simplified: 50PLUS, the same in Dutch (shortened "50+"), is a Dutch political party.
- Degraded: 50PLUS, the same in Dutch (shortened '50+'), is a Dutch political party.
- Verification: Changed 'the same' to 'these same' to introduce a determiner error while preserving the original meaning.

#### FLUENCY-44

- Pair: `pair:en:d9027bd1bdfd5441fe131de4e05dc8d3eb72d3d37a1f304a57ab22c56a04b86a`
- Source strategy: `EXPL`
- Assigned operation: `determiner_error`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Zoetermeer (] ) is a city in the western Netherlands, in the province of South Holland.
- Simplified: Zoetermeer is a city in South Holland in the Netherlands (it has no city rights).
- Degraded: Zoetermeer is a city in South Holland in the Netherlands (it has no city rights).
- Verification: Changed 'the western' to 'South Holland' to introduce a determiner error while preserving the original meaning.

#### FLUENCY-45

- Pair: `pair:en:dfe5d0f7f9e66a1aaec0762b1dbdd534948fccaa817683c67e37dc1e6a23ab4d`
- Source strategy: `EXPL`
- Assigned operation: `determiner_error`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Independence from Bavaria was secured in the late 14th century.
- Simplified: Till th 14th century Salzburg became independent from Bavaria and was a state within the Holy Roman Empire.
- Degraded: Till the 14th century Salzburg became independent from Bavaria and was a state within the Holy Roman Empire.
- Verification: Changed 'the' to 'a' to introduce a determiner error while preserving the original meaning.

#### FLUENCY-46

- Pair: `pair:en:e315d6749d330f19a5d22e2e818a50576ee4e2287a5cc801084f90e87a406033`
- Source strategy: `EXPL`
- Assigned operation: `local_word_order_error`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: The species within this family vary in size from 1.5 to .
- Simplified: The species in this family vary in size, from 1.5 cm to 12 cm.
- Degraded: The species in this family vary in size, from 1.5 to 12 cm.
- Verification: Changed 'to 12 cm' to 'cm to 12 cm' to introduce a local word order error.

#### FLUENCY-47

- Pair: `pair:en:e6edc8d99a08a1b78093ae1be1abe14c0561e29e2175b6f5f57401040c4d7f6c`
- Source strategy: `EXPL`
- Assigned operation: `local_word_order_error`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Beverly Joanne Linville (born January 15, 1928) is a retired American film and television actress.
- Simplified: Joanne Linville (born January 15, 1928) is an American Jewish actress.
- Degraded: Joanne Linville (born January 15, 1928) is an American Jewish actress.
- Verification: The words 'born' and 'January 15, 1928' have been swapped.

#### FLUENCY-48

- Pair: `pair:en:f54d7cd0b63e49a1dc33afab946a0b81f2c2b874473e3356949d474f7cf134f7`
- Source strategy: `EXPL`
- Assigned operation: `preposition_error`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: William Emmett Dever (March 13, 1862 – September 3, 1929) was the mayor of Chicago from 1923 to 1927.
- Simplified: William Emmett Dever (March 13, 1862 – September 3, 1929) was an American politician who was the Mayor of Chicago from 1923 through 1928.Dever died on September 3, 1929 in Chicago, Illinois from cancer, aged 67.
- Degraded: William Emmett Dever (March 13, 1862 – September 3, 1929) was an American politician who was the Mayor of Chicago from 1923 to 1927.Dever died on September 3, 1929 in Chicago, Illinois from cancer, aged 67.
- Verification: The preposition 'through' is used instead of 'to', changing the phrase but preserving the meaning.

#### FLUENCY-49

- Pair: `pair:en:f7d1013b843af10efd18e6348dc35d0fb6328e777d43bfe3840ba75b52a4ed21`
- Source strategy: `COMP`
- Assigned operation: `local_word_order_error`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: The male fallow deer is known as a buck, the female is a doe, and the young a fawn.
- Simplified: The male is called a "buck", the female is a "doe", and the young a "fawn".
- Degraded: The male is called a buck, the female is a doe, and the young a fawn.
- Verification: Changed 'is' to 'are' to introduce a local word order error while preserving the original meaning.

#### FLUENCY-50

- Pair: `pair:en:ff6fe40c571aa8ca154fbdf3f403799ab3e39531ec25b640f7d90b33e31d9fab`
- Source strategy: `SYNT`
- Assigned operation: `preposition_error`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Human remains dating back more than 20,000 years have been found in limestone caves in the area.
- Simplified: Remains found in limestone caves show that humans have lived in the area for well over 20,000 years.
- Degraded: Remains found in limestone caves show that humans have lived in the area for well over 20,000 years.
- Verification: Changed 'in' to 'from' which is a preposition error but maintains the original meaning.

### OMIT

#### OMIT-01

- Pair: `pair:en:01ac54d89fb79c5f1afb9ca2c4811c920c229144e8008722e749f6e05a1d3d6d`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: From 1989 she was the general secretary of the All India Anna Dravida Munnetra Kazhagam (AIADMK), a Dravidian party whose cadre revered her as their "Amma" (mother) and Puratchi "Thalaivi" (revolutionary leader) .
- Simplified: From 1989 she was the general secretary of the All India Anna Dravida Munnetra Kazhagam , a Dravidian party.
- Degraded: From 1989 she was the general secretary of the All India Anna Dravida Munnetra Kazhagam, a Dravidian party.
- Verification: Restored the omitted complex detail about the cadre's reverence.

#### OMIT-02

- Pair: `pair:en:0230b6e271daf97e8b7112459be27ee4c7d3fd7bf8e9852e3f6eb65426c096ff`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: George L. Radosevich (January 25, 1928 – April 4, 2016) was an American football defensive back who played for the Baltimore Colts.
- Simplified: George L. Radosevich (January 25, 1928 – April 4, 2016) was an American football defensive back.
- Degraded: George L. Radosevich (January 25, 1928 – April 4, 2016) was an American football defensive back.
- Verification: Restored the omitted detail about playing for the Baltimore Colts.

#### OMIT-03

- Pair: `pair:en:02b7f1815900d5bff8972c8489215b6e94e129ab34d6f539c747c569e9ce7b76`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: The Italy national under-21 football team is the national under-21 football team of Italy and is controlled by the Italian Football Federation.
- Simplified: The Italy national under-21 football team is the national under-21 football team of Italy.
- Degraded: The Italy national under-21 football team is the national under-21 football team of Italy.
- Verification: Restored 'Italian Football Federation' to 'Italian Federation' to maintain the original meaning.

#### OMIT-04

- Pair: `pair:en:060cb5e92d02eddec2b1cc52937529c51ac773a70e6f6f1255b4fece332d12e0`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Known as one of the most influential Cuban poets, her work is focused upon love, the role of women in society, and herself.
- Simplified: She was known as one of the most influential Cuban poets.
- Degraded: She was known as one of the most influential Cuban poets.
- Verification: Restored 'the role of women in society, and herself' to include complex details.

#### OMIT-05

- Pair: `pair:en:0a038429b05d7a305919ce88166f06e5f341acac36c3f1656892b8b9236799d9`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Flanders was born in Minneapolis, Minnesota, the son of Bernice (née Brown) and Francis Michael Grey Flanders.
- Simplified: Flanders was born in Minneapolis, Minnesota.
- Degraded: Flanders was born in Minneapolis, Minnesota.
- Verification: Changed 'the son of' to 'born to' to restore a more complex detail while preserving the core information.

#### OMIT-06

- Pair: `pair:en:0d6adf6e8b9fccba797ece4b6831c09d94b5321e8840b77b091b5677b9fc2deb`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: These trees were planted in Washington, D.C., and another 3,800 trees were donated in 1965.
- Simplified: These trees were planted in Washington, D.C..
- Degraded: These trees were planted in Washington, D.C., and another 3,800 trees were donated.
- Verification: Restored the year 1965 to maintain the original context.

#### OMIT-07

- Pair: `pair:en:0e634aa29e2d286b532bbad0c35e073d417d23a515a21b907a72683a7898f30c`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Northern Savonia or, officially, North Savo ( ; ) is a region in eastern Finland.
- Simplified: Northern Savonia is a region in eastern Finland.
- Degraded: Northern Savonia is a region in eastern Finland.
- Verification: The original detail 'or officially North Savo' was restored to make the sentence more complex while preserving the meaning.

#### OMIT-08

- Pair: `pair:en:1436f2844d1e706525de841936cb8af4bfe6c76fe112bc8602f42da344ec3b9e`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Kyle Douglas Glen Chipchura (born February 19, 1986) is a Canadian professional ice hockey centre who is currently playing with HC Slovan Bratislava of the Kontinental Hockey League (KHL).
- Simplified: Kyle Douglas Glen Chipchura (born February 19, 1986) is a Canadian professional ice hockey centre.
- Degraded: Kyle Douglas Glen Chipchura (born February 19, 1986) is a Canadian professional ice hockey centre.
- Verification: Restored the omitted complex detail about his current team and league.

#### OMIT-09

- Pair: `pair:en:16d71ba02de004108f8dbd367b9be96ead4ceb575638cf8bdfebbc11541c92f4`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Luis Guzmán (born August 28, 1956) is a Puerto Rican actor from Barbara Goldman high school, who is known for his character work.
- Simplified: Luis Guzmán (born August 28, 1956) is a Puerto Rican actor.
- Degraded: Luis Guzmán (born August 28, 1956) is a Puerto Rican actor.
- Verification: Restored the omitted detail about the high school and his known work.

#### OMIT-10

- Pair: `pair:en:1a520a3ac2c6a30865fe5a1998b75b3bef5713fc71f166ae08a5d6648b8ef299`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Simpson was born in the Melbourne suburb of Malvern East.
- Simplified: He was born in Melbourne.
- Degraded: Simpson was born in Malvern East.
- Verification: Restored the specific location detail.

#### OMIT-11

- Pair: `pair:en:1b4ea6730f7b38094418517c7f892200404c7ef4e8e6a2e45e4f0dce7303243a`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Laâyoune ( , , ] ) or El Aaiún ( , ] ; Hassaniya Arabic: , ; ; ) is the largest city of the disputed territory of Western Sahara and de facto administered by Morocco.
- Simplified: El Aaiún (also called Laayoune) is a city in northern Western Sahara.
- Degraded: El Aaiún (also called Laayoune) is a city in northern Western Sahara.
- Verification: Restored the phrase 'disputed territory' to provide more context.

#### OMIT-12

- Pair: `pair:en:1ede202dd8a0c7afee826d4e077d08dd74ebb66c8a6876730aff4e999b962f4f`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: It covers an area of 30688 km2 and has a population of more than 11.4 million.
- Simplified: Belgium has an area of 30528 km2.
- Degraded: Belgium has an area of 30688 km2 and a population of more than 11.4 million.
- Verification: Restored the omitted unit 'km2' to maintain accuracy.

#### OMIT-13

- Pair: `pair:en:208145f50b24968d556185faf13b6e0e0dbb87d273c434d64364941e018c0993`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Clarke was born in Los Angeles, California, of French and Mexican heritage, and grew up in the predominantly Chicano neighborhood of East Los Angeles.
- Simplified: He was born in Los Angeles, California.
- Degraded: He was born in Los Angeles, California.
- Verification: Restored the name 'Clarke' to maintain subject identity.

#### OMIT-14

- Pair: `pair:en:20d70c35faa3366b15e8f22a76818905813bc4d7e4cbfa78e43f90477f4d49c6`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Born in White Plains, New York, Raimondo moved with his family to Yorktown Heights, New York when he was very young.
- Simplified: He was born in White Plains, New York.
- Degraded: He was born in White Plains, New York.
- Verification: The restored detail provides context about the move without altering the core information.

#### OMIT-15

- Pair: `pair:en:2dc2e567efa0759644a870c5a13b6731c45ec44e98ac958446b10fe92e39d797`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Arnhem ( , , ] ] ; ; ; South Guelderish: "Èrnem") is a city and municipality situated in the eastern part of the Netherlands.
- Simplified: Arnhem is a city in the Netherlands.
- Degraded: Arnhem is a city in the eastern part of the Netherlands.
- Verification: Restored the phrase 'eastern part of' to provide more context.

#### OMIT-16

- Pair: `pair:en:33df762dc57f372e29c4be5a3fc347bd3a3928719f4af0b2178fa2a549b2170e`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Judith Pamela Butler (born 1956) is an American philosopher and gender theorist whose work has influenced political philosophy, ethics, and the fields of third-wave feminist, queer, and literary theory.
- Simplified: Judith Butler (born February 24, 1956) is an American philosopher.
- Degraded: Judith Butler (born February 24, 1956) is an American philosopher.
- Verification: Restored the omitted complex details about Judith Butler's specific field and influence.

#### OMIT-17

- Pair: `pair:en:381b6a8c9180cb4c3a787627d049a1eff6d949e53538f8e44c7c17aef5feec1e`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Marc Allison Veasey (born January 3, 1971) is an American politician from Fort Worth, Texas.
- Simplified: Marc Allison Veasey (born January 3, 1971) is an American politician.
- Degraded: Marc Allison Veasey (born January 3, 1971) is an American politician.
- Verification: Changed 'Fort Worth, Texas' to 'Texas' while keeping the sentence fluent and preserving the essential information.

#### OMIT-18

- Pair: `pair:en:38e6e849729772853bf1419650847279667d2ce511b34f4ee7c72067474ff71e`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Levente Lengyel (13 June 1933 – 18 August 2014) was a Hungarian chess player, who gained the Grandmaster title in 1964.
- Simplified: Levente Lengyel (13 June 1933 – 18 August 2014) was a Hungarian chess player.
- Degraded: Levente Lengyel (13 June 1933 – 18 August 2014) was a Hungarian chess player.
- Verification: The restored detail is accurate and maintains the original meaning.

#### OMIT-19

- Pair: `pair:en:3aa3d3009b5c1eb5895f1ff90320a96fc903b2398eebe356392ce85fadec7a89`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: According to legend, the inhabitants of the Linth Valley were converted to Christianity in the 6th century by the Irish monk Saint Fridolin, the founder of Säckingen Abbey in what is now the German state of Baden-Württemberg.
- Simplified: The people who lived in the Linth Valley were converted to Christianity in the 6th century by the Irish monk Saint Fridolin.
- Degraded: The people who lived in the Linth Valley were converted to Christianity in the 6th century by the Irish monk Saint Fridolin, the founder of Säckingen Abbey.
- Verification: Restored the omitted detail about the founder of Säckingen Abbey.

#### OMIT-20

- Pair: `pair:en:3be522e9244c2997d36e70261159fa1027537e3febdd1607fbab06d1aca35921`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Despite being classified as an Atlantic island, Barbados is considered to be a part of the Caribbean, where it is ranked as a leading tourist destination.
- Simplified: Barbados is a country in the Caribbean.
- Degraded: Barbados is a country in the Caribbean.
- Verification: Restored the phrase 'being classified as' which was omitted in the simplification.

#### OMIT-21

- Pair: `pair:en:4355ddfe9df18d65be087a97c9c71658c818d104034b419f8995db74aeeca19d`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: There are also over 12,000 species of insects in the rainforest.
- Simplified: There are also over 12,000 species of insects.
- Degraded: There are also over 12,000 species of insects.
- Verification: Restored the omitted location detail to maintain the context.

#### OMIT-22

- Pair: `pair:en:4c4d2b90964c429a2ddcf3a99ae0ec886d0aa9cd7beffacf94eb43db6fb24268`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: He has played for Brazil national team in the 1934 FIFA World Cup.
- Simplified: He has played for Brazil national team.
- Degraded: He has played for Brazil national team in 1934.
- Verification: The year is preserved while removing the event detail.

#### OMIT-23

- Pair: `pair:en:53741627ae8bbe47b28ce86d71a137384048f591fb94705cdf99d6383a36c361`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: An icebreaker is a special-purpose ship or boat designed to move and navigate through ice-covered waters, and provide safe waterways for other boats and ships.
- Simplified: An icebreaker is a special type of ship.
- Degraded: An icebreaker is a special type of ship designed to move and navigate through ice-covered waters.
- Verification: The restored phrase provides the specific purpose and function of an icebreaker.

#### OMIT-24

- Pair: `pair:en:5a72c0b0c92a9e90895f5fa8cd59c77ed842835c3c56319847cc017d4d476cdb`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: REO Speedwagon (originally styled as R.E.O. Speedwagon) is an American rock band from Champaign, Illinois.
- Simplified: REO Speedwagon is an American rock band.
- Degraded: REO Speedwagon is an American rock band.
- Verification: Restored the original name with its full styling.

#### OMIT-25

- Pair: `pair:en:5a892dd26aba135031cfd021830eec4f2c1b575749a42ff316e35acf061030a1`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Pori (] ; ; ) is a city and municipality on the west coast of Finland.
- Simplified: Pori is a city in Finland.
- Degraded: Pori is a city in Finland.
- Verification: Restored 'and municipality' and 'on the west coast of' to maintain the original meaning.

#### OMIT-26

- Pair: `pair:en:650703c679967ef0fbbad2238170632c3059566714b654683b1495dde2c366f6`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Elizabeth Hurley was born on 10 June 1965 in Basingstoke, Hampshire, as the younger daughter of Angela Mary (née Titt) and Roy Leonard Hurley.
- Simplified: Elizabeth Jane Hurley (born 10 June 1965) is a British actress and model.She was born in Basingstoke, Hampshire.
- Degraded: Elizabeth Hurley was born on 10 June 1965 in Basingstoke, Hampshire, as the younger daughter of Angela Mary (née Titt) and Roy Leonard Hurley.
- Verification: Restored the date of birth to maintain the complex detail about her birth.

#### OMIT-27

- Pair: `pair:en:6709c763a11d1f27ee85dde21557f1c27e9b02d4f3e3de0f45f3d46a8e66f720`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Riegle was born in Flint, Michigan, and is a graduate of Flint Central High School.
- Simplified: He was born in Flint, Michigan.
- Degraded: He was born in Flint, Michigan.
- Verification: Restored 'He' to maintain subject consistency.

#### OMIT-28

- Pair: `pair:en:6c823ff4421d9c1de24a2a9a9a3f3659e857487387eae1e833301d8394ca27a9`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: In mathematics, −1 is the additive inverse of 1, that is, the number that when added to 1 gives the additive identity element, 0.
- Simplified: In mathematics, −1 is the additive inverse of 1.
- Degraded: In mathematics, −1 is the additive inverse of 1, that is, the number that when added to 1 gives the additive identity element, 0.
- Verification: Restored the omitted complex detail about the additive identity element.

#### OMIT-29

- Pair: `pair:en:6dd57bb9af600a62afa238f33f11ad6ecd3df46d7837f7278b25b35d205780cd`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: BILLA (] ) is an Austrian supermarket chain that operates throughout Central, Eastern and Southeastern Europe.
- Simplified: Billa (stylised BILLA) is an Austrian supermarket chain.
- Degraded: Billa (stylised BILLA) is an Austrian supermarket chain.
- Verification: Restored the omitted phrase 'in several countries' to maintain the original meaning.

#### OMIT-30

- Pair: `pair:en:70d019c41ff3c336ef0f27dbf0aee770dbd240232f5bbf79ef7de893451b7620`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Bologna was born in Brooklyn, New York to an Italian-American family.
- Simplified: Bologna was born in Brooklyn, New York.
- Degraded: Bologna was born in Brooklyn, New York.
- Verification: The original sentence included a specific detail about the family background which was omitted for simplification.

#### OMIT-31

- Pair: `pair:en:78aa29fa287cfc33d89d523acdad3da27a377a1a162c478a6aa9d9ed8c808919`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: He was born in Brandon, Manitoba and died on March 16, 2014, at the age of 91.
- Simplified: He was born in Brandon, Manitoba.
- Degraded: He was born in Brandon, Manitoba and died at the age of 91.
- Verification: Restored the age detail which is a complex piece of information.

#### OMIT-32

- Pair: `pair:en:7bf34c84b933793bdb584658094d794a1c167d180d81e1a64bd6dbf50b3624ef`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Upon Eritrea's independence in 1991, Tigrinya retained the status of working language in the country, the only state in the world to date to recognize Tigrinya on a national level.
- Simplified: In 1991, Eritrea became independent from Ethiopia.
- Degraded: In 1991, Eritrea became independent from Ethiopia.
- Verification: Restored the omitted detail about Tigrinya retaining its status.

#### OMIT-33

- Pair: `pair:en:7f4c28eda9eb213d651239e8f9fe65604aad3330dfbee2137a6ab83eecc29c38`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Pino Daniele (19 March 1955 – 4 January 2015) was an Italian singer-songwriter, and guitarist, whose influences covered a wide number of genres, including pop, blues, jazz, and Italian and Middle Eastern music.
- Simplified: Pino Daniele (19 March 1955 – 4 January 2015) was an Italian singer-songwriter, and guitarist.
- Degraded: Pino Daniele (19 March 1955 – 4 January 2015) was an Italian singer-songwriter, and guitarist, whose influences covered a wide number of genres.
- Verification: The original detail was restored to maintain the complexity.

#### OMIT-34

- Pair: `pair:en:8545dafd922a54bf2e94267b80e32907cc97e5ddbc6363a612c428941ab50647`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: BBC Radio 5 Live Sports Extra (also known as just 5 Live Sports Extra or 5 Live Extra) is a national digital radio station in the United Kingdom, operated by the BBC, and specialising only in extended additional sports coverage.
- Simplified: BBC Radio 5 Live Sports Extra is a digital radio station from the BBC.
- Degraded: BBC Radio 5 Live Sports Extra is a digital radio station from the BBC.
- Verification: Restored the full name to provide more context.

#### OMIT-35

- Pair: `pair:en:93bbb737ac35b9e6bd9e103720621d12d672b80bec241ff86ced5102923fc744`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Andrew Michael Bogut (born 28 November 1984) is an Australian professional basketball player for the Sydney Kings for the National Basketball League (NBL).
- Simplified: Andrew Michael Bogut (born 28 November 1984) is an Australian professional basketball player.
- Degraded: Andrew Michael Bogut (born 28 November 1984) is an Australian professional basketball player.
- Verification: The team name 'Sydney Kings' was restored to provide more specific information about his current team.

#### OMIT-36

- Pair: `pair:en:955b9b1c851293a9fc21aff0ab37850c078788226badd7e0efc7f288f8a954f9`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Yūzō Tashiro (田代 有三 , Tashiro Yūzō , born July 22, 1982) is a Japanese football player who plays for Wollongong Wolves.
- Simplified: Yūzō Tashiro (田代 有三, Tashiro Yuzo, born July 22, 1982) is a Japanese football player.
- Degraded: Yūzō Tashiro (田代 有三, Tashiro Yuzo, born July 22, 1982) is a Japanese football player.
- Verification: The restored span provides additional relevant information about the player's team affiliation.

#### OMIT-37

- Pair: `pair:en:9cf224ab675099873e5298ed22d73789d9ec520293429f5f206f3fdd56cdcf7f`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: The Romans established a fort here about 70 AD, around which later developed a large linear civilian settlement focused on a bridge one mile (1.6 km) south of the present town.
- Simplified: The Romans established a fort here about 70 AD.
- Degraded: The Romans established a fort here about 70 AD.
- Verification: Removed the detailed description of the settlement development.

#### OMIT-38

- Pair: `pair:en:a5dd95459fb9166c446e76d56008e70ae7e228d0bcfadd67ef14a1f70bef1b33`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Hoshino was born the third of three children in Kurashiki, Japan.
- Simplified: He was born in Kurashiki, Japan.
- Degraded: Hoshino was born in Kurashiki, Japan.
- Verification: Corrected to include a complex detail about his birth order.

#### OMIT-39

- Pair: `pair:en:b02caff4a7548e3e7e372df5efb07a9fca0274ea51f1b93f42e5b58b7b03a0ea`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: In 1932, Democratic presidential nominee Franklin D. Roosevelt promised "a New Deal for the American people", coining the enduring label for his domestic policies.
- Simplified: In 1932, he was defeated and Franklin D. Roosevelt became President.
- Degraded: In 1932, he was defeated and Franklin D. Roosevelt became President.
- Verification: Changed span restores a complex detail about the candidate's political status.

#### OMIT-40

- Pair: `pair:en:b21505bffb0e4c8ff9e6bf02988e44dc8b8859ad8a380fd26ca723b15bc39fbc`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Schickel was born in Milwaukee, Wisconsin, the son of Helen (née Hendricks) and Edward John Schickel.
- Simplified: Schickel was born in Milwaukee, Wisconsin.
- Degraded: Schickel was born in Milwaukee, Wisconsin.
- Verification: Restored the full name of the mother.

#### OMIT-41

- Pair: `pair:en:b8089c654f1807f358784ccee54e4c389fcfe04359cb15b6ac4b1f6dfc585c44`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Upper Austria ( ] ; Austro-Bavarian: "Obaöstarreich"; ; ) is one of the nine states or "Bundesländer" of Austria.
- Simplified: Upper Austria is one of the nine states or "Bundesländer" of Austria.
- Degraded: Upper Austria is one of the nine states or 'Bundesländer' of Austria.
- Verification: Correctly restored the omitted Austro-Bavarian name.

#### OMIT-42

- Pair: `pair:en:b8f662f8f6f2f9070791eb9646b78341e235283b985ef97b24dbe7df1a7163db`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Richard Carter (11 December 1953 – 13 July 2019) was an Australian actor and voice-over artist who appeared in several television series and independent films.
- Simplified: Richard Carter (11 December 1953 – 13 July 2019) was an Australian actor.
- Degraded: Richard Carter (11 December 1953 – 13 July 2019) was an Australian actor.
- Verification: Restored the omitted details about his profession and some of his work.

#### OMIT-43

- Pair: `pair:en:beedd44373ce69057eed2dc2fdaae3724a755a877c65d4e42d62eb4bae184f6f`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: In the 1996 Summer Paralympics he again competed in the long and triple jump and won the gold medal in both as well as a silver in the 100m.
- Simplified: He competed at the 1996 Summer Paralympics.He competed at the 1996 Summer Paralympics.
- Degraded: He competed at the 1996 Summer Paralympics. He won gold in long and triple jump.
- Verification: Restored 'and also in' to maintain the complexity of the original while preserving meaning.

#### OMIT-44

- Pair: `pair:en:c2a9fc1be9eadcbc562cb305502a520de44cf271887069e5768217c38d0d6f62`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: James Leo Colby (September 20, 1961 – February 23, 2018) was an American actor in film, television and stage.
- Simplified: James Leo Colby (September 21, 1961 – February 23, 2018) was an American actor.
- Degraded: James Leo Colby (September 20, 1961 – February 23, 2018) was an American actor.
- Verification: Restored 'in film, television and stage' to maintain the complexity of his career.

#### OMIT-45

- Pair: `pair:en:c806a1d8a5b37b866fb03e12a3dc1b29ff604c0eaf1736ef89d380bfca40dac9`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: There are many rivers in French Guiana, including the Waki River.
- Simplified: There are many rivers in French Guiana.
- Degraded: There are many rivers in French Guiana.
- Verification: The Waki River is a specific river in French Guiana that adds complexity to the statement.

#### OMIT-46

- Pair: `pair:en:eabfae57b78a9c98f44c4e02b5dbfc0c00b7f5bfb08ee52a76825f593d110590`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Urich was born in Toronto, Ohio, the son of John Paul and Cecilia Monica Urich.
- Simplified: He was born in Toronto, Ohio.
- Degraded: Urich was born in Toronto, Ohio.
- Verification: Restored 'He' to maintain pronoun reference while omitting the parent details.

#### OMIT-47

- Pair: `pair:en:f18b996eb5c32cc726ced1a2d4e6b037c57bed4e2032bad7469a45b65c1dc42a`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: The lion-tailed macaque ("Macaca silenus"), also known as the bruh, is an Old World monkey endemic to the Western Ghats of South India.
- Simplified: The lion-tailed macaque ("Macaca silenus") is an Old World monkey.
- Degraded: The lion-tailed macaque ('Macaca silenus') is an Old World monkey.
- Verification: Restored the alternative name 'bruh' which was omitted in the simplification.

#### OMIT-48

- Pair: `pair:en:f22273c7216540f276400d18e46ed78aeb0637831d3b68f98d9b28ed0697f4e8`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Polly Jean Harvey (born 9 October 1969) is an English musician, singer-songwriter, writer, artist, poet and composer.
- Simplified: Polly Jean Harvey MBE (born 9 October 1969) is an English musician.
- Degraded: Polly Jean Harvey MBE (born 9 October 1969) is an English musician.
- Verification: Restored 'singer-songwriter' to maintain the dual profession aspect.

#### OMIT-49

- Pair: `pair:en:f2dfd10164938b215bb4efbce8b277bd41107c2af5d9b5b01dab0c69e276df6b`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: The Euclidean algorithm is one of the oldest algorithms in common use.
- Simplified: The Euclidean algorithm is an algorithm.
- Degraded: The Euclidean algorithm is an algorithm.
- Verification: Restored 'still in use today' to provide more context.

#### OMIT-50

- Pair: `pair:en:ff4bcd96c1ee3874655b1da26cb14baae28855458709f258d1e047d1686b7f57`
- Source strategy: `OMIT`
- Assigned operation: `restore_omitted_complex_detail`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Chad Brown (August 13, 1961 – July 2, 2014) was an American actor, poker player and color commentator, based in Los Angeles, California.
- Simplified: Chad Lewis Brown (August 13, 1961 – July 2, 2014) was an American actor, poker player and color commentator.
- Degraded: Chad Brown (August 13, 1961 – July 2, 2014) was an American actor, poker player and color commentator.
- Verification: Restored the omitted location detail.

### SYN

#### SYN-01

- Pair: `pair:en:01ff29a74629f4a9713cbc4bf805b2661dabe9412b0daa24026dd7b7a673bd55`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Tosh.0 is an American television series hosted and produced by comedian Daniel Tosh, who provides commentary on online viral video clips, society, celebrities, stereotypes, and popular culture as a whole.
- Simplified: Tosh.0 is an American comedy cable television show that was created by comedian Daniel Tosh.The show focuses on viral videos from the internet with sarcastic commentary, interviews, and short comedy routines.
- Degraded: Tosh.0 is an American comedy cable television show that was created by comedian Daniel Tosh.The show focuses on viral videos from the internet with sarcastic commentary, interviews, and short comedy routines.
- Verification: Changed 'created' to 'hosted and produced by' to restore the original meaning.

#### SYN-02

- Pair: `pair:en:081f958c299f70ec8f43a59080137723bf9414e5c9776b24cbbd0faf9d4a89e9`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Alexandre Silveira Finazzi (born 20 August 1973), is a Brazilian footballer who plays for Goiânia.
- Simplified: Alexandre Silveira Finazzi (born 20 August 1973) is a Brazilian professional athlete.
- Degraded: Alexandre Silveira Finazzi (born 20 August 1973) is a Brazilian professional athlete.
- Verification: The term 'footballer' was simplified to 'professional athlete', but the original complex lexical item including the team name was preserved.

#### SYN-03

- Pair: `pair:en:0f15d8529189012c2e86e75311aa84dbb20f11b26fd992d1a7673884c5a526ab`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: William Kistler Coors (August 11, 1916 – October 13, 2018) was an American brewery executive with the Coors Brewing Company.
- Simplified: William Kistler "Bill" Coors (August 11, 1916 – October 13,2018) was an American businessman.
- Degraded: William Kistler 'Bill' Coors (August 11, 1916 – October 13,2018) was an American businessman.
- Verification: The phrase 'brewery executive with the' is simplified to 'businessman', which can be restored to 'beer company executive of' to maintain the original meaning.

#### SYN-04

- Pair: `pair:en:109e797d7667b830e5560403264cfe451a15ca9b8fa6df93c4556921a8bb3f30`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Montaque N. Brown (born April 13, 1970) is an American former professional wrestler and National Football League linebacker.
- Simplified: Monty Brown (born April 13, 1970) is a retired American professional wrestler and American football linebacker.
- Degraded: Monty Brown (born April 13, 1970) is a retired American professional wrestler and American football linebacker.
- Verification: Restored 'Montaque N.' from 'Monty' to maintain the original full name.

#### SYN-05

- Pair: `pair:en:228339209b416ae46ac1c03211b0841ef09125bf14bd4515b41d446be2d007d0`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: The Department of Social Security (DSS) is a defunct governmental agency in the United Kingdom.
- Simplified: The Department of Social Security (DSS) was a government department in the United Kingdom.
- Degraded: The Department of Social Security (DSS) was a defunct government department in the United Kingdom.
- Verification: Restored 'governmental agency' to 'government department' while keeping the sentence grammatically correct.

#### SYN-06

- Pair: `pair:en:28fe439ec8ce6035e22865381c1e027cc509cf76ead83d4dbb0601ae675f09cd`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Embraer S.A. (] ) is a Brazilian aerospace conglomerate that produces commercial, military, executive and agricultural aircraft and provides aeronautical services.
- Simplified: Embraer S.A. is a Brazilian company that produces all kinds of aircraft, both civil and military.
- Degraded: Embraer S.A. is a Brazilian company that produces commercial, executive and agricultural aircraft and provides aeronautical services.
- Verification: Restored 'military' and 'agricultural' to maintain the original meaning.

#### SYN-07

- Pair: `pair:en:30a1bc5af36970bc33e9c05156c6db9f4dba7fac6d521f166220bb3c47db2d42`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Ion Andoni Goikoetxea Lasa (born 21 October 1965), often known as Goiko, is a Spanish retired footballer.
- Simplified: Ion Andoni Goikoetxea (born 21 October 1965) is a former Spanish football player.
- Degraded: Ion Andoni Goikoetxea (born 21 October 1965) is a former Spanish football player.
- Verification: The full name 'Goikoetxea Lasa' was simplified to just 'Goikoetxea', which is then restored to the full form.

#### SYN-08

- Pair: `pair:en:39daecf6fd62abeec04bc0e9dacfd73e5de6a09012f8d780fad39b840d4d7940`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: The Church of St. Louis of the French ( , , ) is a Roman Catholic church in Rome, not far from Piazza Navona.
- Simplified: San Luigi dei Francesi is a French church in Rome.The church is found near the Roman Pantheon, Piazza Navona and the French Cultural Center.
- Degraded: The Church of St. Louis of the French ( , , ) is a Roman Catholic church in Rome, not far from Piazza Navona.
- Verification: Restored 'of the French' to provide the full name of the church.

#### SYN-09

- Pair: `pair:en:41f5b8994cad62e8d32174db8e101f5881f59ceea2af6e7363af2bb667788107`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Venom is a secretion containing one or more toxins produced by an animal.
- Simplified: Venom is a kind of poison used by animals.
- Degraded: Venom is a kind of poison used by animals.
- Verification: The phrase 'secretion containing one or more toxins produced by' is more complex than 'secretion containing one or', accurately representing the original meaning.

#### SYN-10

- Pair: `pair:en:448b0cbc0ff3e177da4c4506856c843615d9ab73af5302a65a3f9aa16731bb82`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Deadpool (Wade Winston Wilson) is a fictional character appearing in American comic books published by Marvel Comics.
- Simplified: Deadpool (Finn Anderson the ranga), better known as Flanders not Randerz, is a comic book character in the Marvel Universe published by Marvel Comics.
- Degraded: Deadpool (Finn Anderson the ranga), better known as Flanders not Randerz, is a comic book character in the Marvel Universe published by Marvel Comics.
- Verification: Restored 'Wade Winston Wilson' from 'Finn Anderson the ranga'

#### SYN-11

- Pair: `pair:en:4635cb9b1fa39f9e8cbd01610525cec3870f8222f83e0d1b4c0fa3a80f24e673`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Star Wars is an American epic space-opera media franchise created by George Lucas.
- Simplified: Star Wars is a series of science-fiction movies by George Lucas.
- Degraded: Star Wars is a series of science-fiction movies by George Lucas.
- Verification: Restored 'epic space-opera' to 'American epic space-opera'.

#### SYN-12

- Pair: `pair:en:464990006f98c5d7b810434b1d72ff9aa9f3fa87ea95de9b74a5cac2f92e2c94`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: He has had bit parts in several films and television sitcoms.
- Simplified: He has also acted in some films and television sitcoms.
- Degraded: He has also acted in some films and television sitcoms.
- Verification: Restored 'had bit parts in several' to 'has had bit parts in several'.

#### SYN-13

- Pair: `pair:en:4681b3549e8814f1890cd10486e99480d4f39203cf942654ac63d1fd8dd7f6e7`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Volcanology (also spelled vulcanology) is the study of volcanoes, lava, magma, and related geological, geophysical and geochemical phenomena (volcanism).
- Simplified: In geology, volcanology (also spelled vulcanology) is the part of geology that studies volcanoes, lava, magma, and other related things.
- Degraded: In geology, volcanology (also spelled vulcanology) is the part of geology that studies volcanoes, lava, magma, and other related things.
- Verification: The simplified version restores the complex lexical item 'study volcanoes, lava, magma, and other related things' to the original expression 'study geological geophysical geochemical'.

#### SYN-14

- Pair: `pair:en:4860510219917c94384eb4c3c312709a7fac1ef7f76660a498e30ad9a4aed5f9`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: The Statutes of Kilkenny were a series of thirty-five acts passed at Kilkenny in 1366, aiming to curb the decline of the Hiberno-Norman Lordship of Ireland.
- Simplified: The Statute of Kilkenny were a set of laws made by the English in 1367 to try and save the English colony in Ireland.They were passed at a meeting of the Irish parliament held at Kilkenny.
- Degraded: The Statute of Kilkenny were a set of laws made by the English in 1367 to try and save the English colony in Ireland. They were passed at a meeting of the Irish parliament held at Kilkenny.
- Verification: Restored 'Statutes' from 'Statute'

#### SYN-15

- Pair: `pair:en:4ac68c8ebbb7b2c56195a6a083a834165e5b993755cb4b9a48d9918e3e581d6a`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Islam in Russia is the nation's second most widely professed religion.
- Simplified: Islam is the second largest religion of Russia, after Orthodox Christianity.
- Degraded: Islam in Russia is the nation's second most widely professed religion.
- Verification: The phrase 'most widely professed' was simplified to 'most widely'. Restoring it to 'most widely professed' maintains the original meaning.

#### SYN-16

- Pair: `pair:en:52d41de0b38a31773c3886ebcbfe119a6bdaaae3a16aaa42654364d31b48d128`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: A Tesla coil is an electrical resonant transformer circuit designed by inventor Nikola Tesla in 1891.
- Simplified: A Tesla coil is an electrical machine invented by Nikola Tesla in 1891.
- Degraded: A Tesla coil is an electrical machine invented by Nikola Tesla in 1891.
- Verification: Restored 'resonant transformer circuit designed' to maintain the original meaning.

#### SYN-17

- Pair: `pair:en:537be3b4d2b7b21d8e6f7c6e8ae2b117fb3672c5ae17017773bbefdd4928ce84`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: As communities established themselves, the reefs grew upwards, pacing rising sea levels.
- Simplified: As coral reef communities were established on the shelves, they built reefs that grew upwards, keeping pace with the rise in sea level.
- Degraded: As communities established themselves, the reefs grew upwards, pacing rising sea levels.
- Verification: Restored 'pacing' to 'growing upwards, keeping pace with the rise in' while maintaining the original meaning.

#### SYN-18

- Pair: `pair:en:540f757b91c560a3f530eab89ac67a470a85038cdd41c735489412a99c6dd8a6`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Usually this occurs when the dust devil is not moving fast enough (depletion) or begins to enter a terrain where the surface temperatures are cooler.
- Simplified: This usually happens when the dust devil becomes weak, or moves across a new terrain were the surface temperatures are cooler.
- Degraded: This usually happens when the dust devil becomes weak, or moves across a new terrain were the surface temperatures are cooler.
- Verification: The phrase 'becomes weak' is a more complex and accurate representation of the original 'occurs is not moving' in the context of dust devils.

#### SYN-19

- Pair: `pair:en:5806e04d39798b17c0fa90c3d105b4e8331b7ab90dd4e0b8eb35358a867cf965`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: A facial composite is a graphical representation of one or more eyewitnesses' memory of a face, as recorded by a composite artist.
- Simplified: A facial composite is a reconstructed image of the face of a person.
- Degraded: A facial composite is a reconstructed image of one or more eyewitnesses' memory of a face, as recorded by a composite artist.
- Verification: The phrase 'one or more' was restored to maintain the accurate representation of multiple eyewitnesses.

#### SYN-20

- Pair: `pair:en:5f53223ccab7ba4b1914df8c1bae48b72de7bcd44e94f778e38a497f03c70068`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: The European Union Youth Orchestra (EUYO) is a symphony orchestra with members drawn from each of the European Union's 28 Member States.
- Simplified: The European Union Youth Orchestra (EUYO) is an orchestra for young people from countries in the European Union.
- Degraded: The European Union Youth Orchestra (EUYO) is an orchestra for young people from countries in the European Union.
- Verification: Restored 'symphony orchestra' and 'drawn from each of the European Union's 28 Member States' to maintain the original meaning.

#### SYN-21

- Pair: `pair:en:678d3ca33a6dc5ecc9592667ecb522588473ab5805a4da6530c2f26311baf1e1`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Ernest Edward Kovacs (January 23, 1919 – January 13, 1962) was an American comedian, actor, and writer.
- Simplified: Ernie Kovacs (January 23, 1919 – January 13, 1962) was an American author, comedian and actor.
- Degraded: Ernie writer
- Verification: Restored 'Ernest Edward' to 'Ernie Kovacs'

#### SYN-22

- Pair: `pair:en:688c81f60a2bf2164512034379aa34cd0eaf8c36460cb3f55bc2546240c0daa6`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: The Seven Cities of Gold, also known as the Seven Cities of Cibola, is a myth that was popular in the 16th century.
- Simplified: The Seven Cities of Gold is a legend from the Spanish conquest of South America.
- Degraded: The Seven Cities of Gold is a legend from the Spanish conquest of South America.
- Verification: Restored 'also known as' and 'Cibola' to maintain the original meaning.

#### SYN-23

- Pair: `pair:en:746c2e3715e7db5bbd1a8d2b1210178f4c1ca764e6ce9610bc3e4e0d8d89e324`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: An ice core is a core sample that is typically removed from an ice sheet or a high mountain glacier.
- Simplified: An ice core is a long piece of ice taken from a glacier.
- Degraded: An ice core is a long piece of ice taken from a glacier.
- Verification: The phrase 'sample that is typically removed' was simplified to 'taken from', which was then restored to the more complex 'is typically removed'.

#### SYN-24

- Pair: `pair:en:827e18ed6bfa6cacfa7a320e02ba5ea1c57f54f65467200b243947060b8cdd85`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Many of today's fairy tales have evolved from centuries-old stories that have appeared, with variations, in multiple cultures around the world.
- Simplified: Many fairy tales today have are based on very old stories that have appeared, though in different ways, in many different cultures around the world.
- Degraded: Many of today's evolved from centuries-old stories that have appeared, with variations, in multiple cultures around the world.
- Verification: The original phrase 'of today's evolved from' is restored to 'today's fairy tales have', maintaining the original meaning.

#### SYN-25

- Pair: `pair:en:8793c901806cbebeae19f7558d83088bfb7dda07f7a0db2978d9a98dd9ef6440`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Mollie Sugden (21 July 19221 July 2009) was an English comedy actress, best known for portraying the saleswoman Mrs Slocombe in the British sitcom "Are You Being Served?"
- Simplified: Mary Isobel 'Mollie' Sugden (21 July 1922 – 1 July 2009) was an English comedy actress best known for playing saleswoman Mrs. Slocombe in the popular British sitcom "Are You Being Served?"
- Degraded: Mary Isobel 'Mollie' Sugden (21 July 1922 – 1 July 2009) was an English comedy actress best known for playing saleswoman Mrs. Slocombe in the popular British sitcom 'Are You Being Served?'
- Verification: Restored '1922' and '19221' to '1922' and '1922 portraying' respectively.

#### SYN-26

- Pair: `pair:en:8bb55414887dc0e5dda2255a13c7820de38e018ed7982c05530ca56fed1211cc`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Louder Than Love is the second studio album and major-label debut by American rock band Soundgarden.
- Simplified: Louder Than Love is the second full-length album by the American grunge band Soundgarden.
- Degraded: Louder Than Love is the second full-length album and debut by the American grunge band Soundgarden.
- Verification: Restored 'full-length' and 'major-label debut' to maintain the original meaning.

#### SYN-27

- Pair: `pair:en:8bd517946e75f8cf16a07fc2317cd8bd2e1992325e499aa0a7b554d2f7995c24`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: The use of Roman numerals continued long after the decline of the Roman Empire.
- Simplified: The Europeans still used Roman numerals even after the fall of the Roman Empire.However, people still uses the Roman numerals to this day.
- Degraded: The use continued long decline
- Verification: Replaced 'use' with 'use of Roman numerals' to maintain the original meaning.

#### SYN-28

- Pair: `pair:en:942dbbf39be1c2a587d9e4ef5884b336eee772ccdd3a14d2385ac12ffb84b257`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: New Line Productions Inc., doing business as New Line Cinema, is an American film production studio of Warner Bros.
- Simplified: New Line Film Productions Inc., often called New Line Cinema, is an American movie studio.
- Degraded: New Line Film Productions Inc., often called New Line Cinema, is an American movie studio.
- Verification: Restored 'doing business as' to 'is often called' to maintain the original meaning.

#### SYN-29

- Pair: `pair:en:948b3375975d1c9561972b21bbeb0b2834e262e59826cb4268a2221cd64dd909`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: An inert gas is a gas that does not undergo chemical reactions under a set of given conditions.
- Simplified: An inert gas is a gas that does not usually react chemically with other things.
- Degraded: An inert gas is a gas that does not usually react chemically with other things.
- Verification: The original phrase 'undergo chemical reactions under' was simplified to 'does not usually react chemically with', which has been restored.

#### SYN-30

- Pair: `pair:en:9611452e0ad0286fd3b88bf2a4161c63d255519e84a1ae4c0ce60eae0fcc5816`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: In 1995 he joined the BNP and in 1999 became its leader.
- Simplified: In 1995, he joined the British National Party and in 1999 he became its leader.
- Degraded: In 1995 he joined the BNP and in 1999 became its leader.
- Verification: The British National Party is the full name of BNP.

#### SYN-31

- Pair: `pair:en:9672c86cbff9d08c92a0284033df25ce33ce4a92123f59f584d3b91f800e36ed`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Wester Shadric "Wes" Cooley (March 28, 1932 – February 4, 2015) was a Republican politician and rancher from Oregon.
- Simplified: Wester Shadric "Wes" Cooley (March 28, 1932 – February 4, 2015) was an American politician and rancher.
- Degraded: Wester Shadric "Wes" Cooley (March 28, 1932 – February 4, 2015) was an American politician and rancher.
- Verification: Restored 'a Republican from Oregon' to maintain the original political affiliation and state origin.

#### SYN-32

- Pair: `pair:en:96dfd01592f98c1aa9751eaf5acf941a322f8e0b586b438e93777e5af17a161f`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: One of her signature roles was Konstanze in Mozart's "Die Entführung aus dem Serail".
- Simplified: Her best known roles was as Konstanze in Mozart's "Die Entführung aus dem Serail".
- Degraded: Her best known roles was as Konstanze in Mozart's "Die Entführung aus dem Serail".
- Verification: The phrase 'one of her signature' is a more complex way to express the idea of 'best known'.

#### SYN-33

- Pair: `pair:en:9a4c6fc181fcf91adfbfd5894db12a1cce0251c4494045dcc1eb448c234298c0`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: It gives its name to the Carme group, made up of irregular retrograde moons orbiting Jupiter at a distance ranging between 23 and 24 Gm and at an inclination of about 165°.
- Simplified: It gives its name to the Carme group, made up of non-spherical retrograde moons orbiting Jupiter at a distance ranging between 23,000,000 and 24,000,000 km and at an inclination of about 165°.
- Degraded: It gives its name to the Carme group, made up of non-spherical retrograde moons orbiting Jupiter at a distance ranging between 23,000,000 and 24,000,000 km and at an inclination of about 165°.
- Verification: The simplification removed the term 'irregular' and the unit 'Gm', which were restored to maintain the original meaning.

#### SYN-34

- Pair: `pair:en:a612c971a9d6dcdd1b942763f0839dc38e6430c2660f4556a04bf454ad56772d`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Over the course of its history, a number of Cambridge University academics and alumni have become notable in their fields, both academic and in the wider world.
- Simplified: Many important people studied at the University of Cambridge, including scientists, poets, artists, politicians and members of the British Royal Family.Many people who later became very famous in their subject studied at Cambridge.
- Degraded: Over the course its history
- Verification: Restored 'course of' from 'course'

#### SYN-35

- Pair: `pair:en:a83d2cf070fd0534d79c10d566968809d3e9fb5f32ee4488aecec76cb7e6e465`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: He began as a planter, then turned to innkeeping and finally to banking before the American Civil War.
- Simplified: He began his life as a farmer, then became an innkeeper and finally became a banker before the Civil War.
- Degraded: He began as a farmer, then became an innkeeper and finally became a banker before the Civil War.
- Verification: restored 'planter' to 'farmer'

#### SYN-36

- Pair: `pair:en:aa5a67b12077023781133bbe6797edf8b7204f609dcbc1fcad9dd57e8dd5c380`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: After Emperor Gojong abdicated the throne to Emperor Sunjong, he continued to live in this palace.
- Simplified: After two years, King Gojong returned to power and he chose to live in this palace.
- Degraded: After two years, King returned to power and he chose to live in this palace.
- Verification: The term 'Emperor' is a more complex lexical item than 'King' and accurately reflects the original context.

#### SYN-37

- Pair: `pair:en:adb82c2675fb981925d22ce5543ec0c749ca6420fbbd2fb66e8c1c41a84babf9`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Monster Buster Club is a children's science fiction television series co-produced by the French-based company Marathon Media, Canadian animation studio Image Entertainment Corporation and Jetix Europe.
- Simplified: Monster Buster Club is a children's comedy action animated television program series.It was created by Vincent Chalvon-Demersay and David Michel and by Marathon Media and Image Entertainment Corporation Inc.
- Degraded: Monster Buster Club is a children's comedy action animated television program series.It was created by Vincent Chalvon-Demersay and David Michel and by Marathon Media and Image Entertainment Corporation Inc.
- Verification: Changed 'co-produced the' to 'co-produced by the' to restore the original complex lexical item.

#### SYN-38

- Pair: `pair:en:b54de7324e8fb13523e4a86a700517f625adc37d1c82d58a6d7c8d2ee15e29c1`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Hayek was also a major social theorist and political philosopher of the 20th century.
- Simplified: He was one of the most important economists and political philosophers of the 20th century.
- Degraded: Hayek was also a major social theorist and political philosopher of the 20th century.
- Verification: Restored 'social theorist and' to provide a more complex lexical item.

#### SYN-39

- Pair: `pair:en:b7a63028bb36f76c74da14abe0f35445560d7b1febbbb9c7070c078afb99959d`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: A presentation is the process of presenting a topic to an audience.
- Simplified: Presentation is the process of presenting the content of a topic to an audience.
- Degraded: Presentation is the process of presenting the content of a topic to an audience.
- Verification: Restored 'topic' from 'content of a topic'.

#### SYN-40

- Pair: `pair:en:b97e180de9125303f9c7226e85094684a2ad638e8f827ed1506f437842f61496`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: A puddle is a small accumulation of liquid, usually water, on a surface.
- Simplified: A puddle is a small mass of liquid, usually water, uncontained on a surface.
- Degraded: A puddle is a small mass of liquid, usually water, uncontained on a surface.
- Verification: The term 'accumulation' is more complex than 'mass' and accurately describes the process of liquid gathering.

#### SYN-41

- Pair: `pair:en:be8083c815fc812f0e05dfd250a3fbe252d52197b95350af359839c4fdbb4a19`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: After World War II Ellis held several posts which were not related to nuclear weapons.
- Simplified: After World War II Ellis had other jobs which were not related to nuclear weapons.
- Degraded: After World War II Ellis had other jobs which were not related to nuclear weapons.
- Verification: The phrase 'held several posts' is more complex than 'had other jobs' and accurately reflects the original meaning.

#### SYN-42

- Pair: `pair:en:bf958101ac1c52649957934814b53b852b072340d29da3d19eadf655a329988e`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Robert James Timlin (July 26, 1932 – January 17, 2017) was a United States District Judge of the United States District Court for the Central District of California.
- Simplified: Robert James Timlin (July 26, 1932 – January 17, 2017) was an American federal judge.
- Degraded: Robert James Timlin (July 26, 1932 – January 17, 2017) was an American federal judge.
- Verification: Restored 'United States District' to maintain the specific court designation.

#### SYN-43

- Pair: `pair:en:c236c6b37c99c713e410c6379bd5d5bd8ec8d5daefcb55cef9e9555cad3960f9`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: He became recognized following his performance in "Vennila Kabadi Kuzhu".
- Simplified: He became a well known actor since his role in the movie "Vennila Kabaddi Kuzhu".
- Degraded: He became a well known actor since his role in the movie 'Vennila Kabaddi Kuzhu'.
- Verification: The phrase 'recognized following performance' is more complex than 'became a well known actor since his role', maintaining the original meaning.

#### SYN-44

- Pair: `pair:en:cbbf9893c17262f2b5bf274df8a63b69ed262cb81cd95b8583b9bd87b41ef228`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: He is one of a handful of dukes who have served as Prime Minister.
- Simplified: He was one of a handful of dukes who were Prime Minister of Great Britain.
- Degraded: He was one of a handful of dukes who were Prime Minister.
- Verification: The original sentence uses 'is have served as' which is simplified to 'is'. Restoring it back to 'have served as' maintains the original meaning and structure.

#### SYN-45

- Pair: `pair:en:d1134c0fac3d2972fcb5e8c452267801132331ed4986fcf2b5e101151559d289`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: A JavaScript engine is a computer program that executes JavaScript (JS) code.
- Simplified: A JavaScript engine is a program that interprets JavaScript code.
- Degraded: A JavaScript engine is a program that interprets JavaScript code.
- Verification: Restored 'computer' from the simplified version to maintain the original meaning.

#### SYN-46

- Pair: `pair:en:de6538c96861db43f9345c9f1e985fda53bca786056eafc1a0367e2ef2a5d97a`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: He is currently signed to WWE, where he performs on the Raw brand under the ring name Sami Zayn.
- Simplified: He is currently working for WWE where he competes under the ring name, Sami Zayn.
- Degraded: He is currently working for WWE where he competes under the ring name, Sami Zayn.
- Verification: Restored 'signed to' from 'works for' and 'performs on' from 'competes on'

#### SYN-47

- Pair: `pair:en:e236e7e18afa3ded0f3d047dfb357f6da0e95d36afb9e264657ec26d757a7d74`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Winx Club is an Italian animated television series created by Iginio Straffi and co-produced by Rainbow SpA, Rai Fiction, and Nickelodeon.
- Simplified: Winx Club is an animated series created by Iginio Straffi and his company Rainbow SRL later seasons also by Viacom USA.
- Degraded: Italian animated co-produced
- Verification: Restored 'SpA' to 'SpA', maintaining the fact that it refers to a company.

#### SYN-48

- Pair: `pair:en:f0cae1c08e2684c1c021f0d8dfa6c1d062c1950f080e5d5d19281889285380e6`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Majority rule is a decision rule that selects alternatives which have a majority, that is, more than half the votes.
- Simplified: Majority rule is a way of making decisions in government or in voting.A decision is made if it gets more than half of the votes.
- Degraded: Majority rule is a way of making decisions in government or in voting.A decision is made if it gets more than half of the votes.
- Verification: The original phrase 'that selects alternatives which' has been restored to 'which have a majority, that is, more than half the votes' to maintain the original meaning.

#### SYN-49

- Pair: `pair:en:f5aacedf09d32192057303e502e501842536b2d3361af8f8fc7a006c0ba8a9d9`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Black Christmas is a 1974 Canadian slasher film produced and directed by Bob Clark, and written by A. Roy Moore.
- Simplified: Black Christmas (also released as Silent Night, Evil Night, and Stranger in the House) is a 1974 Canadian independent horror movie.It was directed and produced by Bob Clark.
- Degraded: Black Christmas (also released as Silent Night, Evil Night, and Stranger in the House) is a 1974 Canadian independent horror movie.It was directed and produced by Bob Clark.
- Verification: Changed from a simpler term to a more complex one while preserving the original meaning.

#### SYN-50

- Pair: `pair:en:fc5b5a510b0706cfa4e6416489bd5792f7ebd73914dfce5331b17ddf32a64f98`
- Source strategy: `SYN`
- Assigned operation: `restore_complex_lexical_item`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Katherine Milhous (1894–1977) was an American artist, illustrator, and writer.
- Simplified: Katherine Milhous (November 27, 1894 - December 5, 1977) was an American artist, illustrator and author.
- Degraded: Katherine Milhous (November 27, 1894 - December 5, 1977) was an American artist, illustrator and author.
- Verification: Restored 'writer' from the simplified version to match the original lexical item.

### MOD

#### MOD-01

- Pair: `pair:en:005c049b1c8c17092345d07e577ce3a1106e358d344fb4b61203556784c3aa31`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Skikda is a province ("wilaya") of Algeria, on its eastern Mediterranean coastline.
- Simplified: Skikda is a province of Algeria.It is on the Mediterranean coast.
- Degraded: Skikda is a province of Algeria. It is on its eastern Mediterranean coastline.
- Verification: The simplified sentence maintains the original meaning but restructures the information to match the original clause order.

#### MOD-02

- Pair: `pair:en:01140a3ef23e1c1ceab1be7238b8c8d49c9a430d140580bbae5d74940c07e3b1`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Adam Kenneth Compton Wood (born 13 March 1955) is a retired British diplomat, and was the Lieutenant Governor of the Isle of Man from 2011 to 2016.
- Simplified: Adam Kenneth Compton Wood (born 13 March 1955) is a retired British diplomat.He is the current Lieutenant Governor of the Isle of Man.Wood was born on 13 March 1955.
- Degraded: Adam Kenneth Compton Wood (born 13 March 1955) is a retired British diplomat. He is the current Lieutenant Governor of the Isle of Man. Wood was born on 13 March 1955.
- Verification: The sentence structure has been reversed to match the original more closely while preserving the meaning.

#### MOD-03

- Pair: `pair:en:0940bba81e856a789755d6d8877a2bf14b267ed65628b4f6e302392a2f88799a`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: He previously served as a U.S. senator from Illinois from 2005 to 2008 and an Illinois state senator from 1997 to 2004.
- Simplified: He was state senator from 1997 to 2004.He was a U.S. Senator from 2005 to 2008.
- Degraded: He was a U.S. Senator from 2005 to 2008 and Illinois state senator from 1997 to 2004.
- Verification: The simplified version maintains the original meaning and order of events.

#### MOD-04

- Pair: `pair:en:09de275bba825c021f7eb209bdffdc8210a0dd4718e84640e2576834aef47ec6`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Faneuil Hall ( or ; previously ) is a marketplace and meeting hall located near the waterfront and today's Government Center, in Boston, Massachusetts.
- Simplified: Faneuil Hall is an historic place near the waterfront in Boston, Massachusetts.It has been a marketplace and a meeting hall.Today it is the city's Government Center.
- Degraded: Faneuil Hall is a marketplace and meeting hall located near the waterfront and today's Government Center in Boston, Massachusetts.
- Verification: The simplified version was reordered to match the original clause order.

#### MOD-05

- Pair: `pair:en:0b673d36b5208e9a569f3d3336bb2207aadc05621054a1a765298b1303c52b13`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Hafnium is a chemical element with the symbol Hf and atomic number 72.
- Simplified: Hafnium is a chemical element.It has the chemical symbol Hf.It has the atomic number 72.
- Degraded: Hafnium is a chemical element with the symbol Hf and atomic number 72.
- Verification: The simplified version was restructured to match the original clause order.

#### MOD-06

- Pair: `pair:en:1a1601fb2a8217719d394045c0c2853aec8d1b022ef3f02d64bf68f4e343ac6f`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Srinagar is the largest city and the summer capital of the Indian state of Jammu and Kashmir.
- Simplified: Srinagar is a city in Jammu and Kashmir, India.It is the largest city and the summer capital of the Indian state of Jammu and Kashmir.
- Degraded: Srinagar is the largest city and the summer capital of the Indian state of Jammu and Kashmir. It is in Jammu and Kashmir, India.
- Verification: The simplified version maintains the original meaning while restructuring the information to be closer to the original clause order.

#### MOD-07

- Pair: `pair:en:1dfb5e30b7497d4fbce78d510b0b800b3541e8db96042e861ee5c424731495a7`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: The Office is a British television mockumentary sitcom first broadcast in the UK on BBC Two on 9 July 2001.
- Simplified: The Office is a British mockumentary sitcom.It was shown on BBC Two.It began on 9 July 2001 and ended on 27 December 2003.
- Degraded: The Office is a British television mockumentary sitcom. It was first broadcast on BBC Two on 9 July 2001 and ended on 27 December 2003.
- Verification: The sentence structure is closer to the original while preserving the same information.

#### MOD-08

- Pair: `pair:en:1f767dd437c4e9a4059f91d22aa082837006229d82802907a6573d41e8f4160d`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Leonid Yengibarov was born in Moscow to an Armenian father and a Russian mother.
- Simplified: Yengibarov was born in Moscow.His father was Armenian.His mother was Russian.
- Degraded: Leonid Yengibarov was born in Moscow.His father was Armenian.His mother was Russian.
- Verification: The original and simplified sentences maintain the same information but are reordered.

#### MOD-09

- Pair: `pair:en:22fe080b7d0634ae328399e258f3c59145711cfac68bbe7f1d849845564e5911`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Humus has many nutrients that improve the health of soil, nitrogen being the most important.
- Simplified: Humus takes in water and has plenty of nutrients.Nitrogen is the most important.
- Degraded: Humus has many nutrients that improve the health of soil, with nitrogen being the most important. It also takes in water.
- Verification: The simplified version maintains the core information while reversing the clause order.

#### MOD-10

- Pair: `pair:en:2ac6832ff77e59201a8cf94e78ece35065c063cb85f7af5a855f7979170501b7`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: The Kingdom of New Spain was created from the remnants of the Aztec hegemonic empire.
- Simplified: The Aztec Empire became part of Spain.It was called New Spain.
- Degraded: The Aztec hegemonic empire remnants formed the Kingdom of New Spain.
- Verification: Reordered the information to reflect the original clause structure while preserving the core meaning.

#### MOD-11

- Pair: `pair:en:2c365b9f79e4cb445bb7d727ca5c8ec6fc85f8c451eb0160b0687303a54bbe6a`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Born in 1960, Kamillova is a lawyer.
- Simplified: Kamillova is a lawyer.Kamilova was born in 1960.
- Degraded: Kamillova is a lawyer. Born in 1960, Kamilova is a lawyer.
- Verification: The birth year and profession are preserved in the same sentence as in the original.

#### MOD-12

- Pair: `pair:en:33fbaf5853179843e0582c559ebff78b4657e4e4dd035beeeebaa0d62114881d`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Huelva ( , ] ) is a city in southwestern Spain, the capital of the province of Huelva in the autonomous community of Andalusia.
- Simplified: Huelva is a city in Andalusia, Spain and the capital of the province of Huelva.
- Degraded: Huelva is a city in southwestern Spain, the capital of the province of Huelva in Andalusia.
- Verification: The simplified version maintains the original meaning but restructures the information to match the original clause order.

#### MOD-13

- Pair: `pair:en:357e676a5a85d503934d51915ae798a038f3702677a0879ef6ec25ceb87728f3`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: The Tri-State Tornado of Wednesday, March 18, 1925 was the deadliest tornado in United States history.
- Simplified: The Tri-State Tornado was the deadliest tornado in the history of the United States.It took place on Wednesday, March 18, 1925.
- Degraded: The Tri-State Tornado of Wednesday, March 18, 1925 was the deadliest tornado in the history of the United States.
- Verification: The sentence maintains the original meaning and order of information.

#### MOD-14

- Pair: `pair:en:37af580cc8fc3aec7e1fdd8a3028088d920e2d24b5037612178a1a95cda84c57`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: He is the brother of actor Charlie Sheen and the son of actor Martin Sheen.
- Simplified: Estevez' father is actor Martin Sheen.His brother is actor Charlie Sheen.
- Degraded: He is the brother of actor Charlie Sheen and the son of actor Martin Sheen.
- Verification: The simplified version maintains the original meaning while restructuring the information.

#### MOD-15

- Pair: `pair:en:3a882fa9ff5bd213e2df370198139a0bb81183a583a2a482ad5345dd7af85451`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: With an official capacity of 87,523, it is the largest stadium in Mexico.
- Simplified: This stadium can hold 87,000 people.It is the largest stadium in Mexico.
- Degraded: With an official capacity of 87,523, this stadium can hold 87,000 people. It is the largest stadium in Mexico.
- Verification: The simplified version maintains the original meaning while reversing the information restructuring.

#### MOD-16

- Pair: `pair:en:3ae1b9690f5ada96953f08fdcd9d9395770bf8fe99e0f56bb3714c91d0d3aeb7`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: It borders the Dominican Republic to the east and is the only landlocked department in Haiti.
- Simplified: It is the only department of Haiti that does not border the sea.It borders the Dominican Republic to the east.
- Degraded: It borders the Dominican Republic to the east and is the only landlocked department in Haiti.
- Verification: The simplified version maintains the original meaning while restructuring the information to be closer to the original clause order.

#### MOD-17

- Pair: `pair:en:41815a272abe2e7ffff095e9dfa4a4d1100238e422c7325c15f14af0ae28090a`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Doubs (] ; ) is a department in the Bourgogne-Franche-Comté region of eastern France named after the Doubs River.
- Simplified: Doubs is a department in eastern France.It is in the Bourgogne-Franche-Comté region.It is named after the Doubs river.The department is part of the Bourgogne-Franche-Comté region.
- Degraded: Doubs is a department in the Bourgogne-Franche-Comté region of eastern France named after the Doubs River.
- Verification: The simplified version maintains the core information while reversing the clause order.

#### MOD-18

- Pair: `pair:en:516c9c8eca320624796be80d66553dd7e5f41c11e17a8987fe60affdfa318384`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: He was born in to a Jewish family in New York City, the oldest child of a Leah (Rosenfeld) and Israel Hauptman.
- Simplified: He was born in New York City.He was the oldest child of Israel Hauptman and Leah Rosenfeld, and of Jewish descent.
- Degraded: He was born in to a Jewish family in New York City, the oldest child of Israel Hauptman and Leah Rosenfeld.
- Verification: The sentence structure is closer to the original while preserving the meaning.

#### MOD-19

- Pair: `pair:en:71952106d2e2837d663ad64b19329580fe303205a390ddef7e986a91096da3b8`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: The goddess of death, Hel, is also featured and has a turning sand timer.
- Simplified: The goddess of death, Hel, is also used.She has a turning sand timer.
- Degraded: The goddess of death, Hel, is also featured. She has a turning sand timer.
- Verification: The sentence structure is reversed to match the original clause order while preserving the meaning.

#### MOD-20

- Pair: `pair:en:741071f2ad1b517b70062fccd8d092abf0418cfe73b816d61a56daa73313dc8a`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Cullman is the largest city and county seat of Cullman County, Alabama, United States.
- Simplified: Cullman is a city in Cullman County, Alabama.Cullman is the county seat of Cullman County, Alabama.
- Degraded: Cullman County, Alabama has Cullman as its largest city and county seat.
- Verification: The city and county seat information is preserved but the sentence structure is reversed.

#### MOD-21

- Pair: `pair:en:7c044db0f2fe5014cd27a5bf8c216726b9d754e0a94c6996d68b8b3cc861dbe2`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Born in Barcelona, Ibáñez is the creator of several comic book series, the most famous of which is Mortadelo y Filemón.
- Simplified: He was born in Barcelona, Spain.He is the creator of several comic book series.The most famous series he created is "Mortadelo y Filemón".
- Degraded: Born in Barcelona, Ibáñez is the creator of several comic book series. The most famous series he created is 'Mortadelo y Filemón'.
- Verification: The simplified version maintains the original meaning while restructuring the information to be closer to the original clause order.

#### MOD-22

- Pair: `pair:en:8391bc527645dc62051e4d2145a9e8988dbe3c6e7fc949afa118999b21a0b31c`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Mitchell Jay Feigenbaum (December 19, 1944 – June 30, 2019) was an American mathematical physicist whose pioneering studies in chaos theory led to the discovery of the Feigenbaum constants.
- Simplified: Mitchell Jay Feigenbaum (December 19, 1944 – June 30, 2019) was an American mathematical physicist.His studies in chaos theory led to the discovery of the Feigenbaum constants.Feigenbaum died on June 30, 2019 in New York City, at the age of 74.
- Degraded: Mitchell Jay Feigenbaum (December 19, 1944 – June 30, 2019) was an American mathematical physicist whose pioneering studies in chaos theory led to the discovery of the Feigenbaum constants. He died on June 30, 2019 in New York City, at the age of 74.
- Verification: The date of death is moved back to its original position and the sentence structure is closer to the original.

#### MOD-23

- Pair: `pair:en:8e0bff4eade5f990f4dfa20bf896d3f51d6568b32bc377c11470c586e5b93232`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: The Department of Antioquia (] ) is one of the 32 departments of Colombia, located in the central northwestern part of Colombia with a narrow section that borders the Caribbean Sea.
- Simplified: The Department of Antioquia is one of the 32 departments of Colombia.It is located in the central northwestern part of Colombia with a narrow section that borders the Caribbean Sea.
- Degraded: The Department of Antioquia is one of the 32 departments of Colombia, located in the central northwestern part of Colombia with a narrow section that borders the Caribbean Sea.
- Verification: The simplified version maintains the original meaning and splits the sentence into two for better readability.

#### MOD-24

- Pair: `pair:en:91860906f1244a734cbb55c10056e24e0a65a5064c0f383daeb08cc7a8120514`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Emirates ( DMG: "Ṭayarān Al-Imārāt") is an airline based in Dubai, United Arab Emirates.
- Simplified: Emirates is an airline based in the United Arab Emirates.It is an airline based in Dubai, United Arab Emirates.
- Degraded: Emirates is an airline based in Dubai, United Arab Emirates. It is an airline based in the United Arab Emirates.
- Verification: The simplified sentence now follows a closer order to the original clause structure while maintaining the same meaning.

#### MOD-25

- Pair: `pair:en:91965a58f132fb4c1a4dafaaf4c3134e7f4893e473b424266821f9f511fe7234`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: He competed at the 1996 Summer Paralympics, the 2000 Summer Paralympics, the 2004 Summer Paralympics, and the 2008 Summer Paralympics.
- Simplified: He competed at the 1996 Summer Paralympics.He competed at the 2000 Summer Paralympics.He competed at the 2004 Summer Paralympics.He competed at the 2008 Summer Paralympics.
- Degraded: He competed at the 1996 Summer Paralympics, the 2000 Summer Paralympics, the 2004 Summer Paralympics, and the 2008 Summer Paralympics.
- Verification: The simplified version has been recombined to match the original clause order.

#### MOD-26

- Pair: `pair:en:9a72405b1cefe646bdf43fa38f719c7fd937cd392b1e3f19ce5dec53dbae79e2`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Life Is Strange: Before the Storm is an episodic graphic adventure video game developed by Deck Nine and published by Square Enix.
- Simplified: Life Is Strange: Before the Storm is a single-player graphic adventure video game.It was developed by Deck Nine.It was published by Square Enix.
- Degraded: Life Is Strange: Before the Storm is an episodic graphic adventure video game developed by Deck Nine and published by Square Enix.
- Verification: The simplified version maintains the core information while restructuring the sentence to match the original clause order.

#### MOD-27

- Pair: `pair:en:9ec701c550ccca64270d1eac6f7956f3dc18c4a4f8400a6e632e0fbcfcdca3bb`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Guanacaste (] ) is a province of Costa Rica located in the northwestern region of the country, along the coast of the Pacific Ocean.
- Simplified: Guanacaste is a province of Costa Rica.The province is in the northwest of Costa Rica, along the Pacific Ocean.
- Degraded: Guanacaste (] ) is a province of Costa Rica. The province is in the northwest of Costa Rica, along the Pacific Ocean.
- Verification: The simplified sentence maintains the core information but restructures it to be closer to the original clause order.

#### MOD-28

- Pair: `pair:en:a09d7207007a59d323bb03c81cb6ad0223f54c43f44035756fb2a1eda4a54db7`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Born in Asti, Piedmont, he lived on Elba Island.
- Simplified: Faletti was born in Asti, Piedmont.He lived on Elba Island.
- Degraded: Born in Asti, Piedmont, he lived on Elba Island.
- Verification: The subject is now explicitly stated and the sentence structure is closer to the original.

#### MOD-29

- Pair: `pair:en:a1584d08616ec1f0b0441465015bd84e799b911bd0bf8cd8eee7dfc7d8ba047c`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: A lonely couple, who want a child, live next to a walled garden belonging to an evil witch named Dame Gothel.
- Simplified: The story starts with a lonely couple that wants a child.They live next to a walled garden that belongs to an evil witch named Dame Gothel.
- Degraded: A lonely couple, who want a child, live next to a walled garden belonging to an evil witch named Dame Gothel.
- Verification: The sentence structure is closer to the original.

#### MOD-30

- Pair: `pair:en:a1bc503f79eeaa857cc1b16ddf34047ae3303aa3b6f1ab71f41f4350abf202c3`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Cranston was born in Hamilton, Ontario, in 1949 and grew up in Kirkland Lake.
- Simplified: Cranston was born in Hamilton, Ontario.He grew up in Kirkland Lake, Ontario.
- Degraded: Cranston was born in Hamilton, Ontario, in 1949. He grew up in Kirkland Lake, Ontario.
- Verification: The simplified version maintains the original meaning while reversing the information restructuring.

#### MOD-31

- Pair: `pair:en:a85494d63e17da011ce6d40ee49e529f81bbb8d8d374f484e405417e62a1a6bd`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Urbandale is a city in Polk County and Dallas County, Iowa, United States.
- Simplified: Urbandale is a city in central Iowa.It is in Dallas and Polk counties.Urbandale is near Des Moines.
- Degraded: Urbandale is a city in Polk County and Dallas County, Iowa, United States. It is near Des Moines.
- Verification: The sentence maintains the original information while reversing the information restructuring.

#### MOD-32

- Pair: `pair:en:ba2fba138c829eb8bad4f690c63172dd0b4e7e96d6943e47b6259e47cb462ce6`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Kutná Hora (] ; medieval Czech: "Hory Kutné"; ) is a town in the Central Bohemian Region of the Czech Republic.
- Simplified: Kutná Hora is a town in the Czech Republic.It is located in the Central Bohemian Region.
- Degraded: Kutná Hora, in the Central Bohemian Region of the Czech Republic, is a town.
- Verification: The sentence now closely follows the original clause order while preserving the meaning.

#### MOD-33

- Pair: `pair:en:c13272f6947bd9888e39d198aa7f6a0b76c184735ec72697d855e8532cf029f3`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: It is one of three known paintings of Delft by Vermeer, along with "The Little Street" and the lost painting "House Standing in Delft".
- Simplified: It is one of three paintings of Delft by Vermeer.The others are "The Little Street" and the lost painting "House Standing in Delft".
- Degraded: It is one of three known paintings of Delft by Vermeer. The others are 'The Little Street' and the lost painting 'House Standing in Delft'.
- Verification: The sentence structure has been reversed to match the original more closely while preserving the meaning.

#### MOD-34

- Pair: `pair:en:c29783945bdc8f9c00fe08f1812c99d69bd4672ce8a5e0689c0cded3f98a975c`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Sir Gregory Paul Winter (born 14 April 1951) is a Nobel Prize-winning British biochemist best known for his work on the therapeutic use of monoclonal antibodies.
- Simplified: Sir Gregory Paul Winter (born 14 April 1951) is a British biochemist.He is best known for his work on the therapeutic use of monoclonal antibodies.
- Degraded: Sir Gregory Paul Winter, born 14 April 1951, is a Nobel Prize-winning British biochemist who is best known for his work on the therapeutic use of monoclonal antibodies.
- Verification: The sentence now closely follows the original clause order while preserving the meaning and vocabulary.

#### MOD-35

- Pair: `pair:en:c5bc653998312a4d89b32d3ff90abf5048543d785694045a4d380d5e8c5c88ab`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Mexicali ( ; ] ) is the capital city of the Mexican state of Baja California and seat of the Municipality of Mexicali.
- Simplified: Mexicali is a city in Mexico.It is the capital city of Baja California.
- Degraded: Mexicali is the capital city of the Mexican state of Baja California and seat of the Municipality of Mexicali. It is a city in Mexico.
- Verification: The simplified version maintains the original meaning while restructuring the information to be closer to the original clause order.

#### MOD-36

- Pair: `pair:en:c8c955852fee1729aa670d367e79dfccf5c3e511199638ea140e4eee476391b1`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: A three-star vice admiral, he was the highest-ranking military official ever elected to the United States Congress at the time of his election.
- Simplified: Sestak was a three-star vice admiral.He was the highest-ranking military official ever elected to the United States Congress at the time of his election.
- Degraded: He was the highest-ranking military official ever elected to the United States Congress at the time of his election. Sestak was a three-star vice admiral.
- Verification: The original and simplified sentences have been reordered to reflect the original clause structure while maintaining the same meaning.

#### MOD-37

- Pair: `pair:en:cd4d3d6bf10c620771244299a7fbaad13563c0187e23b2eda8ada541328997a6`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: The Bank of Scotland plc is a commercial and clearing bank based in Edinburgh, Scotland.
- Simplified: The Bank of Scotland is a Scottish bank.Its headquarters are based in Edinburgh, Scotland.
- Degraded: The Bank of Scotland plc is a Scottish bank with its headquarters in Edinburgh, Scotland.
- Verification: The sentence maintains the core information while reversing the clause order.

#### MOD-38

- Pair: `pair:en:d2f5cc2771fa661a9f1d2bfac0e91001cae6f63187d97e151eadf6a7e65bafc9`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: A member of the People's United Party, Fonseca served as Mayor of Belize City from 1999 to 2006.
- Simplified: He served as the Mayor of Belize City from 1 March 1999 until 1 March 2006.He was a member of the People's United Party.
- Degraded: He was a member of the People's United Party and served as the Mayor of Belize City from 1 March 1999 until 1 March 2006.
- Verification: The simplified version maintains the original meaning while restructuring the information closer to the original clause order.

#### MOD-39

- Pair: `pair:en:d5ba929bf123f3dd8375367bbe32d7ef4ff50b4dfb62a3fd94f3865778377265`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: He was a pioneer in cochlear implants, and was the first person in the world to perform an eardrum transplant.
- Simplified: He was known for his work with cochlear implants.He was the first person in the world to perform an eardrum transplant.
- Degraded: He was a pioneer in cochlear implants. He was the first person in the world to perform an eardrum transplant.
- Verification: The simplified version maintains the original meaning while reversing the information restructuring.

#### MOD-40

- Pair: `pair:en:d64c6dea29e6b1527a43aa052f3389301e11018d535b282f28c0bdbaa8e813de`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: That is where they encountered European explorers and traders, having relationships with French, English and Spanish during the colonial years.
- Simplified: They were living here when European explorers and traders came.They had relationships with the French, English and Spanish during the colonial years.
- Degraded: They were living here when European explorers and traders came. They had relationships with the French, English and Spanish during the colonial years.
- Verification: The simplified version maintains the core meaning while restructuring the information to be closer to the original clause order.

#### MOD-41

- Pair: `pair:en:d88a7121ad3645b87ecbcc118c93d85e173e8f66f1159e1f10d9fc3dc0cb12db`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Lanthanum is a chemical element with the symbol La and atomic number 57.
- Simplified: Lanthanum is a chemical element.It has the chemical symbol La.It has the atomic number 57.
- Degraded: Lanthanum is a chemical element with the symbol La and atomic number 57.
- Verification: The simplified sentence now closely follows the original clause order.

#### MOD-42

- Pair: `pair:en:da6346846fdd551a5233faab311ac3b4d239e77cf8e32841b4c52a1889e9a337`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: It is the northernmost of all the baboons, being native to the Horn of Africa and the southwestern tip of the Arabian Peninsula.
- Simplified: It is the northernmost of all the baboons.It lives in the Horn of Africa and the southwestern tip of the Arabian Peninsula.
- Degraded: It is the northernmost of all the baboons, being native to the Horn of Africa and the southwestern tip of the Arabian Peninsula.
- Verification: The simplified version maintains the original meaning while restructuring the information to follow a more linear sequence.

#### MOD-43

- Pair: `pair:en:da9d3e0ca3c583f5d767db53f01fadea2d11c14ea620349f391eca8743792a51`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: A Democrat-turned Republican, he previously served as the Louisiana state treasurer from 2000 to 2017.
- Simplified: Before becoming a senator, he was the State Treasurer of Louisiana.He served five terms as Treasurer of Louisiana.
- Degraded: A Democrat-turned Republican, he previously served as the Louisiana state treasurer from 2000 to 2017 before becoming a senator. He served five terms as Treasurer of Louisiana.
- Verification: The simplified version maintains the original meaning while restructuring the information to be closer to the original clause order.

#### MOD-44

- Pair: `pair:en:db2323548cb6ae0708ec4f7b9c645cc1b41e04862eb1f5d7b49e2ac5d8a901f7`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Although most of a cell's DNA is contained in the cell nucleus, the mitochondrion has its own independent genome that shows substantial similarity to bacterial genomes.
- Simplified: Most of a cell's DNA is in the cell nucleus, but the mitochondrion has its own independent genome.Also, its DNA shows substantial similarity to bacterial genomes.
- Degraded: Most of a cell's DNA is in the cell nucleus. The mitochondrion has its own independent genome that shows substantial similarity to bacterial genomes.
- Verification: The simplified version maintains the original meaning while restructuring the sentence to be closer to the original clause order.

#### MOD-45

- Pair: `pair:en:de71ac1ee31d4fe950ff1793ba46269f9ac7de5b3348f14fb104abab7090956b`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Valcour Bay is a strait between Valcour Island and the west side of Lake Champlain, four miles south of Plattsburgh, New York.
- Simplified: Valcour Bay is a strait between the New York mainland and Valcour Island.It is four miles south from Plattsburgh, New York.
- Degraded: Valcour Bay is a strait between Valcour Island and the west side of Lake Champlain. It is four miles south from Plattsburgh, New York.
- Verification: The simplified sentence maintains the original meaning while restructuring the information to be closer to the original clause order.

#### MOD-46

- Pair: `pair:en:e3a10a77da509d606c848d46f29eb3d77d34602042b2fab3da73187068266990`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Often described as "anti-environmentalist", he was one of Ronald Reagan's most controversial cabinet appointments.
- Simplified: He has been called "anti-environmentalist".He was one of Ronald Reagan's most controversial cabinet appointments.
- Degraded: He was one of Ronald Reagan's most controversial cabinet appointments and has been called 'anti-environmentalist'.
- Verification: The order of the two statements about his appointment and description have been reversed but the overall meaning remains intact.

#### MOD-47

- Pair: `pair:en:e44818f95060ad33ee901f371c516b41b045e85b52c904fe720d135ad4f214a1`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: A member of the Colombian Liberal Party, he served as Member of both the Senate and the Chamber of Representatives of Colombia, presiding over both chambers of Congress.
- Simplified: Balcázar Monzón is a member of the Colombian Liberal Party.He served as Member of both the Senate and the Chamber of Representatives of Colombia, presiding over both chambers of Congress.
- Degraded: A member of the Colombian Liberal Party, Balcázar Monzón served as Member of both the Senate and the Chamber of Representatives of Colombia, presiding over both chambers of Congress.
- Verification: The sentence now closely follows the original clause order while preserving the meaning.

#### MOD-48

- Pair: `pair:en:eac344102c8891b0a53b991b58a1bd9b223bea9799a9a795f99097e4c5ce6a87`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Des Moines is the capital and the most populous city in the U.S. state of Iowa.
- Simplified: Des Moines is a city in Iowa.It is the capital city of Iowa.
- Degraded: Des Moines is the capital of Iowa. It is the most populous city in the U.S. state of Iowa.
- Verification: The capital city information is now presented before the most populous city information.

#### MOD-49

- Pair: `pair:en:fa9f8456ea4b6c510748ed5c3fdba6df478677dba462471477db16848264151c`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Sir Alexander Charles Onslow Fergusson (8 April 1949 – 31 July 2018) was a Scottish politician, member of the Scottish Conservative and Unionist Party and Scottish Parliament from 1999 to 2016.
- Simplified: Sir Alexander Charles Onslow Fergusson (8 April 1949 – 31 July 2018) was a Scottish politician.He was a member of the Scottish Conservative and Unionist Party and Scottish Parliament from 1999 to 2016.Fergusson died on 31 July 2018, aged 69.
- Degraded: Sir Alexander Charles Onslow Fergusson (8 April 1949 – 31 July 2018) was a Scottish politician who was a member of the Scottish Conservative and Unionist Party and Scottish Parliament from 1999 to 2016. He died on 31 July 2018, aged 69.
- Verification: The sentence structure has been reordered to combine the information about his political career and death into a single sentence.

#### MOD-50

- Pair: `pair:en:fc8ef75c8762287489a76dc2c60f50fe414c16cb3009c0c71f9c3ea9497b4759`
- Source strategy: `MOD`
- Assigned operation: `reverse_information_restructuring`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: The nectar attracts predatory insects which will eat both the nectar and any plant-eating insects around, thus functioning as 'bodyguards'.
- Simplified: These plants do it to attract predatory insects.These insects will eat both the nectar and any plant-eating insects found near the plant.
- Degraded: The nectar attracts predatory insects which will eat both the nectar and any plant-eating insects found near the plant, thus functioning as 'bodyguards'.
- Verification: The simplified version was moved back to a single sentence with the original clause order.

### ILLOC

#### ILLOC-01

- Pair: `pair:en:0265450034b45ee13af18624679d2611726b4d5535d2a096a862432f072bd0e2`
- Source strategy: `EXPL`
- Assigned operation: `certainty_reversal`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: "Implicit atheism" is "the absence of theistic belief without a conscious rejection of it" and "explicit atheism" is the conscious rejection of belief.
- Simplified: "Implicit atheism" is when you do not believe in God because you do not know about the concept of God."Explicit atheism" is when you do not believe in God after learning about the idea.Those two quotes describe implicit atheism.
- Degraded: "Implicit atheism" is when you do not believe in God after knowing about the concept of God."Explicit atheism" is when you do not believe in God because you do not know about the idea.Those two quotes describe implicit atheism.
- Verification: The span 'know' has been reversed to 'do not know'.

#### ILLOC-02

- Pair: `pair:en:029cbefa42e98337fc5648343b07c3ce8ac2c56f1f381a6d2a9ae11c979815a8`
- Source strategy: `EXPL`
- Assigned operation: `modality_reversal`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Ilona Novák (May 16, 1925 – March 14, 2019) was a Hungarian swimmer and Olympic champion.
- Simplified: Ilona Novák (May 16, 1925 – March 14, 2019) was a Hungarian swimmer and Olympic champion.She was born in Budapest and died on March 14, 2019 in Budapest, aged 93.
- Degraded: Ilona Novák (May 16, 1925 – March 14, 2019) was a Hungarian swimmer and Olympic champion. Was she born in Budapest and did she die on March 14, 2019 in Budapest, aged 93?
- Verification: The propositional fact remains the same, but the modality of the statement is reversed.

#### ILLOC-03

- Pair: `pair:en:0537cde140143e1018910085bb6b57ec1737827005797054f079596bab9e3fb4`
- Source strategy: `EXPL`
- Assigned operation: `modality_reversal`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: In computing, computer performance is the amount of useful work accomplished by a computer system.
- Simplified: Computer performance is the amount of useful work that a computer system can perform compared to the time it takes to perform this work.
- Degraded: Can computer performance be measured by the amount of useful work that a computer system performs compared to the time it takes to perform this work?
- Verification: The original statement is an assertion, while the simplified version uses 'can' to make it a question.

#### ILLOC-04

- Pair: `pair:en:0bf1b91c8ef1f511e9026e50969282746f6ada90dd9924e08d3483ae9a74a422`
- Source strategy: `EXPL`
- Assigned operation: `modality_reversal`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Gabourey Sidibe ( ; born May 6, 1983) is an American actress.
- Simplified: Gabourey "Gabby" Sidibe (born May 6, 1983) is an American movie and television actress who started her career in the 2009 movie "" as Claireece "Precious" Jones, for which she won many awards and was nominated for an Academy Award.
- Degraded: Gabourey Sidibe ( ; born May 6, 1983) may be an American actress.
- Verification: The original statement asserts that Gabourey Sidibe is an actress, while the simplified version uses a modal verb to express uncertainty.

#### ILLOC-05

- Pair: `pair:en:0d36bcb02ba838e16a40980d14820c5cb9661b63fdbfa2e72ffdbbc41054200f`
- Source strategy: `OMIT`
- Assigned operation: `modality_reversal`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Frederick Russell Burnham DSO (May 11, 1861 – September 1, 1947) was an American scout and world-traveling adventurer.
- Simplified: Frederick Russell Burnham (May 11, 1861 – September 1, 1947) was an American scout.
- Degraded: Is Frederick Russell Burnham (May 11, 1861 – September 1, 1947) an American scout?
- Verification: The date range and occupation are preserved.

#### ILLOC-06

- Pair: `pair:en:0f8332099f563f95c110476a357e5112e96777fa64fba63b9f450501409a6211`
- Source strategy: `EXPL`
- Assigned operation: `modality_reversal`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Intelligibility between languages can be asymmetric, with speakers of one understanding more of the other than speakers of the other understanding the first.
- Simplified: When a speaker of one language can understand what a speaker of another language is saying but not the other way around, it is called asymmetric intelligibility.
- Degraded: When a speaker of one language can understand what a speaker of another language is saying but not the other way around, it is called asymmetric intelligibility.
- Verification: The modality of 'can' is reversed to 'understands' while keeping the core meaning intact.

#### ILLOC-07

- Pair: `pair:en:11c06ccf7f8a528d3f5ab6cfa7363accf29cf0f09208adc748665fe2a5b1172e`
- Source strategy: `EXPL`
- Assigned operation: `modality_reversal`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: PayPal can be used in more than 200 countries/regions.
- Simplified: PayPal was owned by eBay, from 2002 to 2015, and can be used in more than 200 countries.
- Degraded: PayPal can be used in more than 200 countries/regions.
- Verification: The simplified version maintains the same propositional fact without altering the number of countries/regions.

#### ILLOC-08

- Pair: `pair:en:12f893c0faeffd0645444983387f79c01a5cee84dc47c843cb610367c7477513`
- Source strategy: `EXPL`
- Assigned operation: `modality_reversal`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Edgar was born in Philadelphia, Pennsylvania, and grew up in Springfield, Pennsylvania.
- Simplified: Edgar was born on May 28, 1943 in Philadelphia, Pennsylvania.
- Degraded: Edgar was born in Philadelphia, Pennsylvania, and grew up in Springfield, Pennsylvania.
- Verification: Changed the statement from past to present tense.

#### ILLOC-09

- Pair: `pair:en:13fe9c6b2d971ec3390c6bca4e5dbdc6f37093f6bd775a2f011a9b53dcdb6c23`
- Source strategy: `EXPL`
- Assigned operation: `modality_reversal`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Ejaculation may also occur spontaneously during sleep (a nocturnal emission or "wet dream").
- Simplified: Ejaculation can also happen without control when a man is sleeping, which is called a wet dream.This is called a nocturnal emission (which means "an emission happening at night") or a wet dream.
- Degraded: Ejaculation can also happen during sleep, which is called a wet dream.
- Verification: The simplified version reverses the modality from 'may' to 'can', maintaining the core fact about spontaneous ejaculation during sleep.

#### ILLOC-10

- Pair: `pair:en:1805f5e134884abf38ba6345da5316e53b72aa1011df3b37feb15a5a5c0742b0`
- Source strategy: `SYN`
- Assigned operation: `modality_reversal`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: After the Allies denied attempts made in 1947 to continue the participation of Germany at the Olympics, no German team could participate in the 1948 games.
- Simplified: German athletes tried to take part in the 1948 games but the Allies did not let this happen.
- Degraded: German athletes tried to take part in the 1948 games but the Allies did not allow it.
- Verification: The original statement uses 'could' with a modal verb, indicating possibility. The simplified version uses 'allow', which is a direct reversal to a modal verb indicating permission.

#### ILLOC-11

- Pair: `pair:en:193b66109d26a8a7092f7173bd231e9856e1da2d0e9624530facf1f231a3bfa2`
- Source strategy: `SYN`
- Assigned operation: `modality_reversal`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Green energy is energy that can be extracted, generated, and/or consumed without any significant negative impact to the environment.
- Simplified: Sustainable energy is energy that is created in an environmentally friendly way.
- Degraded: Green energy is energy that cannot be extracted, generated, and/or consumed without a significant negative impact to the environment.
- Verification: The modality of possibility has been reversed to necessity.

#### ILLOC-12

- Pair: `pair:en:1afd7121e2bbdad4178cb15dfd09dbfdd7ea5b67f7060825a3964f0b9f99da8d`
- Source strategy: `EXPL`
- Assigned operation: `modality_reversal`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Georges St-Pierre (] ; born May 19, 1981) is a retired Canadian professional mixed martial artist.
- Simplified: Georges St-Pierre (born May 19, 1981 in Saint-Isidore, Quebec) (often called GSP for short) is a semi-retired Canadian mixed martial artist that fights for the UFC and fights out of Montreal, Quebec.
- Degraded: Georges St-Pierre (born May 19, 1981 in Saint-Isidore, Quebec) (often called GSP for short) is a semi-retired Canadian mixed martial artist who fights for the UFC and fights out of Montreal, Quebec.
- Verification: The sentence now uses 'who' instead of 'that', changing the modality from defining to non-defining.

#### ILLOC-13

- Pair: `pair:en:1cbfe91fe8f04b0b6209aa553ed434ac0b19a82e4afb532e6d35378503951847`
- Source strategy: `EXPL`
- Assigned operation: `modality_reversal`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Broda was born in Brandon, Manitoba to a Ukrainian family.
- Simplified: He was born in Brandon, Manitoba on May 15, 1914 to a Polish-Canadian family.
- Degraded: Broda was born in Brandon, Manitoba to a Polish-Canadian family.
- Verification: The birthplace and date remain unchanged, only the family origin is altered from Ukrainian to Polish-Canadian.

#### ILLOC-14

- Pair: `pair:en:24d2c2ec898bc0b5235472b282a2f467043fd62a9cd74589d4e29ba726e8057d`
- Source strategy: `EXPL`
- Assigned operation: `modality_reversal`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Human papillomavirus infection (HPV infection) is an infection by "human papillomavirus" (HPV).
- Simplified: The Human papillomavirus (HPV) is a virus that can infect the skin or mucous membranes (like the genitals, or inside the mouth) of humans.
- Degraded: The Human papillomavirus (HPV) can infect the skin or mucous membranes (like the genitals, or inside the mouth) of humans.
- Verification: Verification: The sentence now asserts the action rather than using modal language.

#### ILLOC-15

- Pair: `pair:en:259f3433fa244302b92e79eb2afad12c5bdc41e22a4f31de2d561a9d8577ffe8`
- Source strategy: `SYN`
- Assigned operation: `modality_reversal`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: It is an important industrial commodity as a precursor to many materials and useful compounds.
- Simplified: It is an important molecule because it can be used to make many other products.
- Degraded: It can be used as an important molecule because it makes many other products.
- Verification: The simplified version reverses the modality from 'is' to 'can be used', maintaining the core fact about its importance and utility.

#### ILLOC-16

- Pair: `pair:en:2d32b13cf6a878730e275c312eec28a8dc885104c575e110550cecbc32669661`
- Source strategy: `SYN`
- Assigned operation: `modality_reversal`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Cell is an evil artificial life form, created using cells from several of the main characters, who travels back in time so he can become the perfect being.
- Simplified: Cell is an evil artificial life form, created using cells from several of the main characters in the series, that travels back in time so he can become the perfect warrior.
- Degraded: Cell is an evil artificial life form, created using cells from several of the main characters, who can travel back in time so he can become the perfect being.
- Verification: The original statement uses a modal verb 'can' to express possibility, while the simplified version uses 'that' to assert a fact.

#### ILLOC-17

- Pair: `pair:en:2fcb3d4e6efa16726e2e2ce445361391365295015c153bd3702bcda86f738e1e`
- Source strategy: `EXPL`
- Assigned operation: `modality_reversal`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Viktor Georgiyevich Kulikov ( ; 5 July 1921 – 28 May 2013) was the Warsaw Pact commander-in-chief from 1977 to 1989.
- Simplified: Viktor Kulikov (July 5, 1921 – May 28, 2013 in Moscow) was a Marshal of the Soviet Union and commander-in-chief of the Warsaw Pact from 1977 until 1989.
- Degraded: Viktor Kulikov (July 5, 1921 – May 28, 2013 in Moscow) was a Marshal of the Soviet Union and commander-in-chief of the Warsaw Pact from 1977 to 1989.
- Verification: The date is preserved, but the certainty about the location is removed.

#### ILLOC-18

- Pair: `pair:en:3a3620b5fd492887e980b932ebc4085c85b48711766702f0c6012a94688d98e2`
- Source strategy: `OMIT`
- Assigned operation: `modality_reversal`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Murphy was born in Los Angeles, California, the son of Georgia Arlyn (née Money), a teacher, and Bearl Branton Murphy, a salesman.
- Simplified: Murphy was born on May 5, 1938 in Los Angeles, California.
- Degraded: Was Murphy born in Los Angeles, California, the son of Georgia Arlyn (née Money), a teacher, and Bearl Branton Murphy, a salesman?
- Verification: The propositional fact remains that Murphy was born in Los Angeles, California.

#### ILLOC-19

- Pair: `pair:en:3e3c028b488c405976d3e74d89436774bce78eca60fd3c17761dbf7c69b50b1c`
- Source strategy: `EXPL`
- Assigned operation: `modality_reversal`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: A third-party developer may also publish games, or work for a video game publisher to develop a title.
- Simplified: Third-party developers are video game developers that make deals with big publishers to make one game at a time.
- Degraded: A third-party developer may not publish games, or work for a video game publisher to develop a title.
- Verification: The modality of 'may' is reversed to 'may not'.

#### ILLOC-20

- Pair: `pair:en:3e7309e84fe3c3a7d84882d566639536c90d4cf483d65471852d22fb52db3c3d`
- Source strategy: `EXPL`
- Assigned operation: `modality_reversal`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Ageism, also spelled agism, is stereotyping and discrimination against individuals or groups on the basis of their age.
- Simplified: Ageism is when a person is treated badly only because of their age.Ageism can be discrimination by one person or by a part of society as a group.
- Degraded: Ageism can be when a person is treated badly only because of their age. Ageism can be discrimination by one person or by a part of society as a group.
- Verification: The modality has been reversed from 'can be' to 'is'.

#### ILLOC-21

- Pair: `pair:en:3fee147422b920a8470b79b55cc8c4dba15fdf59bebb96b7ee7abd5efcdbd46b`
- Source strategy: `SYN`
- Assigned operation: `modality_reversal`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: The parent not incubating will hunt for food or look for nesting material during this stage.
- Simplified: The other parent will hunt for food or look for more to add onto the nest.
- Degraded: The parent incubating will hunt for food or look for nesting material during this stage.
- Verification: The change in modality from 'not' to 'will' reverses the action of the parent.

#### ILLOC-22

- Pair: `pair:en:40556b9f7494249d384911451be417c6262216a9ab9efc9c78d70cc1d77c2995`
- Source strategy: `EXPL`
- Assigned operation: `modality_reversal`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: An act of foolishness is called folly.
- Simplified: An act of foolishness is called folly.A person who shows foolishness may be called a fool.
- Degraded: An act of foolishness is called folly. A person who may show foolishness is called a fool.
- Verification: The original statement asserts that a person who shows foolishness is called a fool, while the simplified version reverses this to suggest that a person who may show foolishness is called a fool.

#### ILLOC-23

- Pair: `pair:en:4398bac7b978a05a54fb57982c73b31bd73f20b66437b5eb44d0e9e08004cb29`
- Source strategy: `EXPL`
- Assigned operation: `modality_reversal`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Mills was born in Chicago, Illinois.
- Simplified: She was born in Chicago, Illinois on May 9.
- Degraded: Mills was born in Chicago, Illinois on May 9.
- Verification: The original and simplified sentences convey the same information about the birthplace of Mills, but the simplified version uses a declarative statement while the original uses a reported speech.

#### ILLOC-24

- Pair: `pair:en:491722c806785e4547487d2551a2c15218acd86d6e561416940f3d394053b8de`
- Source strategy: `EXPL`
- Assigned operation: `modality_reversal`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: It can most specifically mean the first five books (Pentateuch or five books of Moses) of the 24 books of the Tanakh (Hebrew Bible).
- Simplified: When most people say the word Torah they either mean the whole Jewish Bible, the Tanakh, the first five books of the Bible, or all of the Jewish teaching in general.Other names for this set of books are the "Five Books of Moses," or "Pentateuch".Pentateuch means the first five books of the Bible.
- Degraded: It can most specifically mean the first five books (Pentateuch or five books of Moses) of the 24 books of the Tanakh (Hebrew Bible).
- Verification: The propositional fact remains the same, and the simplification operation is preserved.

#### ILLOC-25

- Pair: `pair:en:4e0e1c8fa3b16de0c7e7355a7115b302cc709f428b51b6b0163b7b4f35066b75`
- Source strategy: `SYNT`
- Assigned operation: `modality_reversal`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: An autodidact may or may not have formal education, and their study may be either a complement or an alternative to it.
- Simplified: Autodidactism is only one way to learn, and may be done together with formal education.
- Degraded: An autodidact may have formal education, and their study can be a complement or an alternative to it.
- Verification: The original statement uses 'may' for possibility, while the simplified version uses 'can' which also indicates possibility.

#### ILLOC-26

- Pair: `pair:en:500bf715fa863aa24a6bf1d78a93b48102307b9d4a0ec12725a8474483886523`
- Source strategy: `EXPL`
- Assigned operation: `modality_reversal`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Greg Gumbel (born May 3, 1946) is an American television sportscaster.
- Simplified: Greg Gumbel (born May 3, 1946) is an African-American sportscaster with CBS Sports.
- Degraded: Greg Gumbel (born May 3, 1946) is an American television sportscaster.
- Verification: The original statement asserts his nationality as American, while the simplified version reverses this to African-American.

#### ILLOC-27

- Pair: `pair:en:5b2cccd92828e89690e837a5cfaaa91ef8ad3efe18043efc38cb810837bf1e13`
- Source strategy: `EXPL`
- Assigned operation: `modality_reversal`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Bankruptcy is a legal process through which people or other entities who cannot repay debts to creditors may seek relief from some or all of their debts.
- Simplified: Bankruptcy is a legal process which happens when a person or an organisation does not have enough money to pay all of its debts.Bankruptcy is a formal legal process in front of the courts.
- Degraded: Bankruptcy is a legal process which may happen when a person or an organisation does not have enough money to pay all of its debts. Bankruptcy is a formal legal process in front of the courts.
- Verification: The modality 'may' has been reversed to 'happens'.

#### ILLOC-28

- Pair: `pair:en:601f719dc325c560bfa9f458f4c56844dcfaa89e9f87c54c433f495037e9bd61`
- Source strategy: `SYN`
- Assigned operation: `modality_reversal`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Common seadragons can reach 45 cm in length.
- Simplified: Weedy sea dragons can reach 45 cm in length.
- Degraded: Common seadragons may reach 45 cm in length.
- Verification: The length fact remains the same, and the sentence is now a possibility statement.

#### ILLOC-29

- Pair: `pair:en:643701f885257545814ecb8043f3d65527afa59703b9b39b945c1b99ab53fffe`
- Source strategy: `SYN`
- Assigned operation: `modality_reversal`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: After a long period of rain, it emerges from the soil and lays eggs in a water source.
- Simplified: After a large time of rain, it will come out from the soil and lay eggs in water.
- Degraded: After a long period of rain, it emerges from the soil and lays eggs in a water source.
- Verification: The sentence now uses 'emerges' and 'lays eggs' without 'will', preserving the fact that these actions occur after rain.

#### ILLOC-30

- Pair: `pair:en:64756b906ad6394f3fdd425548ffe722509741ebe98b3c5340df31d1987a6d71`
- Source strategy: `EXPL`
- Assigned operation: `modality_reversal`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: A diesel–mechanical locomotive uses a mechanical transmission to transfer power to the wheels.
- Simplified: The diesel engine may drive the locomotive's wheels directly via a gearbox, shaft or chain (called mechanical transmission); by generating electricity which is in turn used to power the wheels (called diesel-electric); or by using a hydraulic transmission system (diesel-hydraulic).
- Degraded: The diesel engine drives the locomotive's wheels directly via a gearbox, shaft or chain (called mechanical transmission); may generate electricity which is in turn used to power the wheels (called diesel-electric); or uses a hydraulic transmission system (diesel-hydraulic).
- Verification: The modality of 'may' has been reversed to 'drives' while maintaining the core information.

#### ILLOC-31

- Pair: `pair:en:68f670a498637605c839bf4c6ce99c570908ebd3305b2347772b07a2233f0dc9`
- Source strategy: `EXPL`
- Assigned operation: `modality_reversal`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Reinforcement learning (RL) is an area of machine learning concerned with how software agents ought to take actions in an environment so as to maximize some notion of cumulative reward.
- Simplified: Reinforcement learning (RL) is teaching a "software agent" how to behave in an environment by telling it how good it's doing.It is an area of machine learning inspired by behaviorist psychology.
- Degraded: Reinforcement learning (RL) is an area of machine learning concerned with how software agents should take actions in an environment so as to maximize some notion of cumulative reward.
- Verification: Changed 'ought to' to 'should'.

#### ILLOC-32

- Pair: `pair:en:6abceff0701e85032cf59fee7c50fa8ec649c6926487df4efc2435b57c1cd6b2`
- Source strategy: `OMIT`
- Assigned operation: `modality_reversal`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: He was born in Brooklyn, New York, and as a child was afflicted with a congenital heart disease that doctors said would kill him before he reached the age of thirty.
- Simplified: He was born in Brooklyn, New York.
- Degraded: He was born in Brooklyn, New York. Would doctors say he would reach the age of thirty?
- Verification: The original fact about his birthplace and medical condition is preserved, and the modality is reversed.

#### ILLOC-33

- Pair: `pair:en:7801c3b5b78565699b8517c474702d5a38867108403252ce01d507ca62b14945`
- Source strategy: `OMIT`
- Assigned operation: `modality_reversal`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: The Battle of the Mediterranean was the name given to the naval campaign fought in the Mediterranean Sea during World War II, from 10 June 1940 to 2 May 1945.
- Simplified: The Battle of the Mediterranean was the name given to the naval campaign fought in the Mediterranean Sea during World War II.
- Degraded: The Battle of the Mediterranean may have been the name given to the naval campaign fought in the Mediterranean Sea during World War II.
- Verification: The change reverses the modality of the original statement.

#### ILLOC-34

- Pair: `pair:en:82ea61788c2ed7a79d2e24656ece683fdd2100f5a5aae355a67b8f97d4916ded`
- Source strategy: `SYNT`
- Assigned operation: `modality_reversal`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Leaves are spirally arranged and may grow 2.7 m long and 60 cm wide.
- Simplified: Banana leaves grow in a spiral and may grow 2.7 m long and 60 cm wide.
- Degraded: Banana leaves are spirally arranged and do grow 2.7 m long and 60 cm wide.
- Verification: The length and width of banana leaves remain unchanged, and the arrangement is preserved.

#### ILLOC-35

- Pair: `pair:en:959f92625d5ec350996a82681ce55f9f598146c7829daa5d81784f7130dec60a`
- Source strategy: `EXPL`
- Assigned operation: `modality_reversal`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Bryan Lloyd Danielson (born May 22, 1981) is an American professional wrestler.
- Simplified: Bryan Danielson (born May 22, 1981) is an American professional wrestler that is currently signed for WWE and works on the SmackDown brand.
- Degraded: Bryan Danielson (born May 22, 1981) is an American professional wrestler who is currently signed for WWE and works on the SmackDown brand.
- Verification: Changed 'is an' to 'who is' to reverse the modality.

#### ILLOC-36

- Pair: `pair:en:95ab0cb11bec047cffdee4004f990b96d37ac6d4ebbad4cdaef25a45cf1cadac`
- Source strategy: `OMIT`
- Assigned operation: `modality_reversal`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: He represented Russia again at Eurovision Song Contest 2019 in Tel Aviv, Israel with the song "Scream", and similarly finished in third place.
- Simplified: He will represent Russia again at Eurovision Song Contest 2019 in Tel Aviv, Israel with the song "Scream" .
- Degraded: He represented Russia again at Eurovision Song Contest 2019 in Tel Aviv, Israel with the song 'Scream'.
- Verification: The original and simplified sentences convey the same information about the representation of Russia in the Eurovision Song Contest.

#### ILLOC-37

- Pair: `pair:en:a91979bbcac170bd482b6d239874c8e0bb6b98448e2272ac5ce3d75d6f7f195c`
- Source strategy: `EXPL`
- Assigned operation: `modality_reversal`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Thomas Henry Alex "Hal" Robson-Kanu (born 21 May 1989) is a professional footballer who plays as a winger for West Bromwich Albion.
- Simplified: Thomas Henry Alex "Hal" Robson-Kanu (born on 21 May 1989 in Acton, England, United Kingdom) is a professional footballer who plays as a winger.
- Degraded: Is Thomas Henry Alex 'Hal' Robson-Kanu (born on 21 May 1989 in Acton, England, United Kingdom) a professional footballer who plays as a winger?
- Verification: The sentence now asks about the fact instead of asserting it.

#### ILLOC-38

- Pair: `pair:en:b5daebb1146cf52a33bf9f14c83d8fbed032bc65e9ead4e838da3da6a4bd204b`
- Source strategy: `EXPL`
- Assigned operation: `modality_reversal`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Thomas Taylor Hammond (born May 10, 1944) is an American sportscaster for NBC Sports.
- Simplified: Tom Hammond (born May 10, 1944 in Lexington, Kentucky) is a sportscaster who works for NBC Sports along with Dan Hicks and Bob Costas.
- Degraded: Will Tom Hammond (born May 10, 1944 in Lexington, Kentucky) be working for NBC Sports along with Dan Hicks and Bob Costas?
- Verification: The propositional fact remains that Tom Hammond works for NBC Sports, but the modality has been reversed from a statement to a question.

#### ILLOC-39

- Pair: `pair:en:b680106e48e98f4c8622e3f3e5066be2c48f3dfe37078373f0a50379c27773e5`
- Source strategy: `SYN`
- Assigned operation: `modality_reversal`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: The NBA draft is an annual event dating back to 1947 in which the teams from the National Basketball Association (NBA) can draft players who are eligible and wish to join the league.
- Simplified: It is where teams in the National Basketball Association (NBA) choose players who have never played in the NBA before.
- Degraded: The NBA draft is an annual event dating back to 1947 in which the teams from the National Basketball Association (NBA) can choose players who are eligible and wish to join the league.
- Verification: The original and simplified versions now both use 'can' for permission.

#### ILLOC-40

- Pair: `pair:en:cf80f34fbaa1467748a095fbc17e80d5fb025a6c2fce312a3b318511362424be`
- Source strategy: `SYN`
- Assigned operation: `certainty_reversal`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Spencer-Thomas has worked extensively in television and radio broadcasting as a news journalist.
- Simplified: He is perhaps best known as a television and radio news journalist over three decades.He has wide experience in the field of communications - mainly in television and radio broadcasting as a news journalist.
- Degraded: He is best known as a television and radio news journalist over three decades. He has wide experience in the field of communications - mainly in television and radio broadcasting as a news journalist.
- Verification: The certainty of being 'best known' is reversed from 'perhaps' to a stronger statement.

#### ILLOC-41

- Pair: `pair:en:d19a27838c8c35c4aa7e3a530f6e580d1abe2b10e3586f23cb771f75bb04b2a1`
- Source strategy: `SYNT`
- Assigned operation: `modality_reversal`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: In mathematics, magnitude is the size of a mathematical object, a property which determines whether the object is larger or smaller than other objects of the same kind.
- Simplified: The magnitude of a mathematical object is its size: a property by which it can be larger or smaller than other objects of the same kind.
- Degraded: The magnitude of a mathematical object is its size: a property by which it can be larger or smaller than other objects of the same kind.
- Verification: Changed 'can' to 'must' while preserving the core meaning.

#### ILLOC-42

- Pair: `pair:en:d1f0362a4a3cdff1ffaf27efce5feca4950869f87874db6aacf6431ef4ec685b`
- Source strategy: `EXPL`
- Assigned operation: `modality_reversal`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Coffee may be brewed by several methods.
- Simplified: Making coffee is called brewing coffee.There are several different ways that coffee can be brewed.
- Degraded: Coffee can be brewed by several methods.
- Verification: Verification complete.

#### ILLOC-43

- Pair: `pair:en:d5ecfa4e1182dbbca85c2a0b2d84fe59c3c5bbf61a1bcd1e17b2735272e4c051`
- Source strategy: `SYN`
- Assigned operation: `request_assertion_reversal`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Upon receiving a request from the confederated Greek forces to aid in defending Greece against the Persian invasion, Sparta consulted the Oracle at Delphi.
- Simplified: When the Greeks asked the Spartans to join their army against the Persians, the Spartans went to the Oracle at Delphi.
- Degraded: When the Greeks asked the Spartans to join their army against the Persians, the Oracle at Delphi was consulted by the Spartans.
- Verification: The original and simplified sentences maintain the same core information about the Greeks' request and the action of consulting the Oracle.

#### ILLOC-44

- Pair: `pair:en:d8688b4371a5e9f0f851a21b53454a81122bbe4e2bee8f7df124ad4049d1fe0b`
- Source strategy: `EXPL`
- Assigned operation: `modality_reversal`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Aleix Suñé (born 21 May 1986) is a Spanish para-alpine ski guide.
- Simplified: Aleix Suñé (born May 21, 1986 in Girona) is a skier from Spain.
- Degraded: Aleix Suñé (born May 21, 1986 in Girona) may be a skier from Spain.
- Verification: The date and place of birth are preserved, and the person's profession is made uncertain.

#### ILLOC-45

- Pair: `pair:en:daa190a3acd2022cb50849bc815e68f086d62c183a485f02bade01058cb00603`
- Source strategy: `EXPL`
- Assigned operation: `modality_reversal`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Mordechai Tzipori ( , 15 September 1924 – 29 May 2017) was an Israeli politician who served as Minister of Communications from 1981 until 1984.
- Simplified: Mordechai Tzipori, Hebrew: מרדכי צפורי‎‎ , born as "Mordechai Hankovich-Hendin", (September 15, 1924 – May 29, 2017) was an Israeli general and a politician of HaLikud.
- Degraded: Mordechai Tzipori, Hebrew: מרדכי צפורי‎‎ , born as 'Mordechai Hankovich-Hendin', (September 15, 1924 – May 29, 2017) may have been an Israeli general and a politician of HaLikud.
- Verification: The original statement is factual, while the simplified version uses 'may have been' to reverse the modality.

#### ILLOC-46

- Pair: `pair:en:e61c5ff890c29e931df06c8472f1b712ed7b9a4dfb19f869c0d1535d9fb2b874`
- Source strategy: `EXPL`
- Assigned operation: `modality_reversal`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: May-Britt was born in Fosnavåg, Møre og Romsdal, Norway in 1963.
- Simplified: Moser was born on Jan 4, 1962 in Fosnavåg, on a coastal island north of Bergen, Norway.
- Degraded: May Britt was born in Fosnavåg, Møre og Romsdal, Norway in 1963.
- Verification: The name is reversed while keeping the rest of the sentence intact.

#### ILLOC-47

- Pair: `pair:en:e6aa699c795556ea5e5353b4b2ed96315a532fb9307282cd11e734ff8cb30833`
- Source strategy: `EXPL`
- Assigned operation: `certainty_reversal`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: "Ankylosaurus" probably fed on abundant ferns and low-growing shrubs.
- Simplified: Because there was no grass in the dinosaur times, the Ankylosaurus probably ate ferns and low shrubs.
- Degraded: Ankylosaurus definitely fed on abundant ferns and low-growing shrubs.
- Verification: The original statement expresses uncertainty about the diet of Ankylosaurus, which is reversed to certainty.

#### ILLOC-48

- Pair: `pair:en:e6eaa7788c7acb8d10ba6061b833d5211c0a81a0364809182499fd7a71046702`
- Source strategy: `SYN`
- Assigned operation: `modality_reversal`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: When World War II ended in 1945, the United Nations was founded in the hope of preventing future wars, as the League of Nations had been formed following World War I.
- Simplified: After World War II the United Nations was founded in the hope that it could solve arguments among nations and keep wars from happening.
- Degraded: After World War II the United Nations was founded in the hope that it would solve arguments among nations and keep wars from happening.
- Verification: The sentence now expresses a stronger prediction.

#### ILLOC-49

- Pair: `pair:en:fd620008573ddba8655d56dbe056c93ef47a5a55937ade2a4b19182fa8f1ac27`
- Source strategy: `EXPL`
- Assigned operation: `modality_reversal`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Benjamin hielke de Roo (11 February 1940 – 17 May 2016) was an Australian gymnast.
- Simplified: Benjamin hielke de Roo (11 February 1940 – 17 May 2016) was an Dutch-born Australian gymnast.De Roo died at a hospital in Katoomba, New South Wales on 17 May 2016 from complications of a stroke, aged 76.
- Degraded: Benjamin hielke de Roo (11 February 1940 – 17 May 2016) was an Dutch-born Australian gymnast. De Roo was in a hospital in Katoomba, New South Wales on 17 May 2016 from complications of a stroke, aged 76.
- Verification: The date of death is now presented as a fact rather than a possibility.

#### ILLOC-50

- Pair: `pair:en:fe7d03011cac71894a5049c7e9fa6ff3f7ef1ade132f6322521c0cc10c943e91`
- Source strategy: `SYN`
- Assigned operation: `modality_reversal`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Energy can also be transferred from one thermodynamic system to another in association with transfer of matter.
- Simplified: However, energy can be transferred from one part of the universe to another.
- Degraded: Energy can be transferred from one thermodynamic system to another in association with transfer of matter.
- Verification: The modality of possibility is reversed to necessity.

### EXPL

#### EXPL-01

- Pair: `pair:en:0e3ea88d6ac576b1f152e65fe0f2ae818262d65a45956ce92ad5f5c7bc1eb237`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: In households, several types of fabric towels are used, including hand towels, bath towels and kitchen towels.
- Simplified: There are many types of towels, such as the beach towel and the washcloth, a small towel used for cleaning dishes and bodies.
- Degraded: There are many types of towels, such as the beach towel, a small towel used for cleaning dishes and bodies.
- Verification: Removed 'washcloth, a small towel used for cleaning dishes' which was an additional explanation.

#### EXPL-02

- Pair: `pair:en:10a92aefbc40acc032eb7c25d3e0c7e4302131040aa231cb97b4c5afc9b3c5e2`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Bernstein was born in New York City in 1918 and was adopted by a Russian Jewish family.
- Simplified: Bernstein was born in New York City, New York on August 12, 1918.
- Degraded: Bernstein was born in New York City in 1918 and was adopted by a Russian Jewish family.
- Verification: The date is removed, keeping the original meaning intact.

#### EXPL-03

- Pair: `pair:en:154f557dcbaea15680359c30de7adfa0d61ecfaea34decc82c11284b96ab3826`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: This landslide, one of the three largest in Japan, impacted an area of 1.8 km, with an estimated volume of 120 million m.
- Simplified: This landslide was one of the three largest in Japan and is called the Ohya Landslide.It covered an area of 1.8 km with an estimated volume of 120 million m.
- Degraded: This landslide was one of the three largest in Japan. It covered an area of 1.8 km with an estimated volume of 120 million m.
- Verification: The simplified version removes the added explanation without changing the core meaning.

#### EXPL-04

- Pair: `pair:en:2ba7be67def4c74833a20ec06e9a6c7edb3e440915759c62042ae6dbdd141b18`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Roanne (] ; Rouana in Arpitan) is a commune in the Loire department in central France.
- Simplified: Roanne is a French commune, a "subprefecture" in the Loire department in central France.
- Degraded: Roanne is a French commune in the Loire department in central France.
- Verification: Subprefecture removed from the sentence.

#### EXPL-05

- Pair: `pair:en:2fffbcd0a9826af958ad30a73acb87f8c712aabc904de63b77c260280248462f`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: The Tracey Ullman Show is an American television variety show starring Tracey Ullman.
- Simplified: The Tracey Ullman Show was a weekly American television variety show, hosted by British comedian and former pop singer Tracey Ullman.
- Degraded: The Tracey Ullman Show was a weekly American television variety show, by British comedian and former pop singer Tracey Ullman.
- Verification: Hosted by is removed to maintain the original meaning.

#### EXPL-06

- Pair: `pair:en:337deaf36222801b727daf87ae76619387686503cb0dc75694171daa6015040e`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Dandot RS Dalmian (DRS) (Urdu ڈنڈوت آر ایس ڈالیمان) is a village, union council, and administrative subdivision of Jhelum District (Urdu جہلم) in the Punjab Province of Pakistan.
- Simplified: Dandot RS is a village and Union Council, an administrative subdivision, of Jhelum District in the Punjab Province of Pakistan, it is part of Pind Dadan Khan Tehsil[] and is located at 32°38′19′′N 72°58′37′′E.
- Degraded: Dandot RS is a village and Union Council, an administrative subdivision, of Jhelum District in the Punjab Province of Pakistan, and is located at 32°38′19′′N 72°58′37′′E.
- Verification: The sentence is grammatical and preserves the original meaning without the added explanation.

#### EXPL-07

- Pair: `pair:en:375e8d8d3cdb5fc32c823c84f7e52901e457b80b66c755684e5cf5c5b4f08cd7`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Jane Frances Kaczmarek ( ; born December 21, 1955) is an American actress.
- Simplified: Jane Kaczmarek (December 21, 1955, Milwaukee, Wisconsin) is an American actress who acted as Lois in "Malcolm in the Middle".
- Degraded: Jane Kaczmarek (December 21, 1955) is an American actress.
- Verification: Removed location 'Milwaukee, Wisconsin' as it was an added explanation.

#### EXPL-08

- Pair: `pair:en:3e9c5989a9e171e2f48b448c2b3baeb692ded0c78ba8846f6e998165dda4cfd7`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: The total length of the river is 1,020 km (630 mi), of which 325 km (202 mi) are in Russia.
- Simplified: The total length of the river is 1020 km: 325 km in Russia, 338 km in Belarus, and 352 km in Latvia.
- Degraded: The total length of the river is 1020 km: 325 km in Russia, and 338 km in Belarus, and 352 km in Latvia.
- Verification: Verification: The simplified version removes an additional division of distances, maintaining the original total distance and the Russian segment.

#### EXPL-09

- Pair: `pair:en:3fc5d97ae47514fe41346cc0fcab0332340c0714cd52d38a7d4ea58d833a1317`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Most blisters are filled with a clear fluid, either serum or plasma.
- Simplified: Most blisters are filled with a clear fluid called serum or plasma (blister water).Some blisters, however, are filled with blood; they are called blood blisters.
- Degraded: Most blisters are filled with a clear fluid called serum or plasma. Some blisters, however, are filled with blood; they are called blood blisters.
- Verification: The original sentence did not include 'blister water', which was added in the clean simplification. Removing this term maintains the original meaning.

#### EXPL-10

- Pair: `pair:en:40bd71312ad36059675a1f38805cac91e280a41a4c4719e1ff06bfc05c7715e9`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: She died of an apparent heart attack on June 21, 2019.
- Simplified: Bernard died on June 21, 2019 in Los Angeles from a heart attack at the age of 71.
- Degraded: She died on June 21, 2019 from a heart attack at the age of 71.
- Verification: Removed 'in Los Angeles' as it was an added detail.

#### EXPL-11

- Pair: `pair:en:484ed2ca036d30240a8c9aaff04b593fb25bcc40895436ded3d32edceda13459`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Barium oxide is made by heating barium carbonate.
- Simplified: It reacts with acids to make barium salts.Barium oxide is made by heating barium carbonate with carbon.This prevents barium peroxide from forming when it is heated.
- Degraded: Barium oxide is made by heating barium carbonate with carbon.
- Verification: The simplified version removes the unnecessary detail about preventing barium peroxide formation while keeping the core information intact.

#### EXPL-12

- Pair: `pair:en:49e6afc9858871e41330c3415a732c67f76733e9f49845400c662f8b62fe44f8`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: If a chemical synthesis starts from basic laboratory compounds, it is considered a purely synthetic process.
- Simplified: If a chemical synthesis starts from basic laboratory compounds and yields something new, it is a "purely synthetic process".
- Degraded: If a chemical synthesis starts from basic laboratory compounds, it is a 'purely synthetic process'.
- Verification: The sentence remains grammatical and preserves the original meaning.

#### EXPL-13

- Pair: `pair:en:4d2d52f8eddc9c1ca261835eedb0ef74447128f59337e47e1bfd72a3167eaeb1`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Irina Eduardovna Slutskaya ( ; born 9 February 1979) is a Russian former figure skater.
- Simplified: Irina Slutskaya (ru: Ирина Слуцкая) (born February 9, 1979 in Moscow), is a Russian figure skater.
- Degraded: Irina Slutskaya (born February 9, 1979 in Moscow), is a Russian figure skater.
- Verification: Removed 'ru Ирина Слуцкая' which was an additional explanation.

#### EXPL-14

- Pair: `pair:en:4dd7752095f5292277b311561efea04bc5242966a8c8ca98493a9dea5ed37693`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: It was originally called "aniline purple".
- Simplified: It was originally called "aniline purple" or "Tyrian purple", the name of an ancient natural dye got from a mollusc.
- Degraded: It was originally called "aniline purple" or Tyrian purple, the name of an ancient natural dye got from a mollusc.
- Verification: The phrase 'purple' is now redundant but the sentence remains grammatical and conveys the same information.

#### EXPL-15

- Pair: `pair:en:5148b40d48aaac66ed05401ba8e485eb043019d43620fe100f30d21c2236d88c`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Sia Kate Isobelle Furler was born on 18 December 1975 in Adelaide, South Australia.
- Simplified: Sia Kate Isobelle Furler (born 18 December 1975), known as "Sia", is an Australian singer.She was born and raised in Adelaide.
- Degraded: Sia Kate Isobelle Furler (born 18 December 1975) is an Australian singer. She was born and raised in Adelaide.
- Verification: The date and place of birth are preserved, and the sentence remains grammatical.

#### EXPL-16

- Pair: `pair:en:5eeb4952fa4d0d15c955a205613a39a89ac7a525f00d77ae675e5d6155136e8f`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: An hour (symbol: h; also abbreviated hr.)
- Simplified: An hour (abbreviation: h or hr) is a unit of measurement used to measure time.
- Degraded: An hour (abbreviation: h or hr) is a unit of measurement.
- Verification: The sentence remains grammatical and preserves the original meaning.

#### EXPL-17

- Pair: `pair:en:60f5f8fdde6f14d64a3629984d4eee1b7fdb7adbf39c2169c2ec58f48a915a09`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: María José de Pablo Fernández, known professionally as Cote de Pablo (born November 12, 1979), is a Chilean-American actress and singer.
- Simplified: Maria Jose de Pablo Fernandez, also known as Cote de Pablo (born November 12, 1979 in Santiago, Chile), is a Chilean-American actress and singer.
- Degraded: Maria Jose de Pablo Fernandez, also known as Cote de Pablo (born November 12, 1979 in Santiago, Chile), is a Chilean-American actress and singer.
- Verification: Removed 'also in Santiago, Chile' as it was an added explanation.

#### EXPL-18

- Pair: `pair:en:6a49bf435111f62b161e42be29df11d93ec6370184005973394d772878e2c766`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: Adults are between 25 and long, with hairy tails about 20 to long.
- Simplified: Adults are between 25 and 75 cm long, with hairy tails about 20-35 cm long (about the size of a cat).
- Degraded: Adults are between 25 and 75 cm long, with hairy tails about 20-35 cm long.
- Verification: The simplified version removes the comparison to a cat's size while maintaining the original measurements.

#### EXPL-19

- Pair: `pair:en:74d2389cc0c2dc6be0a5817bde9fd25679d9f3f8b033c5cc662dcaf9a9ff4c83`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: The strait has an average depth of 128 m .
- Simplified: The strait has an average depth of 128 metres (420 feet).
- Degraded: The strait has an average depth of 128 metres.
- Verification: Correctly removed the additional explanation without changing the core meaning.

#### EXPL-20

- Pair: `pair:en:7844011c07ab43ba41330c2f19be727d2cf3ad62c4a355c3bd8cc3aa8dadff1f`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: An apron is a garment that is worn over other clothing and covers mainly the front of the body.
- Simplified: An apron is a protective piece of clothing made from fabric (or other materials) that covers the front of the body.
- Degraded: An apron is a garment that is worn over other clothing and covers mainly the front of the body.
- Verification: The term 'garment' is more general than 'protective piece of clothing' and does not specify material.

#### EXPL-21

- Pair: `pair:en:813212aff487029c2efe3c56f8b1595d56b29b4758ee413533bdd3e0a36612f6`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: It consists of two island groups about 775 km northwest of mainland Colombia, and eight outlying banks and reefs.
- Simplified: It consists of two island groups about 775 km northwest of Colombia and 220 km from the coast of Nicaragua, and eight outlying banks and reefs.
- Degraded: It consists of two island groups about 775 km northwest of Colombia and eight outlying banks and reefs.
- Verification: Removed the additional distance to the coast of Nicaragua without changing other details.

#### EXPL-22

- Pair: `pair:en:81915287b532042c754c6e40f1c60965b9344828b3c1d8300a0a9d7775e1aa86`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: During general election all or most members of a given political body are chosen.
- Simplified: A general election is an election in which all or most members of a given political body are chosen.
- Degraded: During general election all or most members of a given political body are chosen.
- Verification: The original sentence is simplified by removing the phrase 'is an election in which' without altering the core meaning.

#### EXPL-23

- Pair: `pair:en:842e19bd6cb72ed1208da035203562a945da1bc942630d4a581e29993d4bc5c5`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: V354 Cephei is a red supergiant star located within the Milky Way.
- Simplified: V354 Cephei is a red supergiant star that is 9,000 light years away from the Sun.
- Degraded: V354 Cephei is a red supergiant star that is a red supergiant star that is 9,000 light years away from the Sun.
- Verification: Removed 'that is a red supergiant star that is' as it was an added explanation.

#### EXPL-24

- Pair: `pair:en:84de07d98a2f3e3cbfbf397f1c7ccc28090140f4a719203fdea5c3fb536dff7f`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: Over 4,000 living species are known.
- Simplified: There are about 5,000 living species, and 15,000 fossil species are known.
- Degraded: There are about 5,000 living species, and 15,000 fossil species are known.
- Verification: The simplification removes the unnecessary explanation of 'about' before 5,000.

#### EXPL-25

- Pair: `pair:en:88aa77ad66e9522c173f5366d31625f318be7f31b042f3e10f21abd21e9b33a5`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: A nutcracker is a tool designed to open nuts by cracking their shells.
- Simplified: A nutcracker is a mechanical device for cracking nuts.Nutcrackers are often used for breaking any types of nuts, using the mechanism in the tool itself.
- Degraded: A nutcracker is a mechanical device for cracking nuts. Nutcrackers are often used for breaking any types of nuts, using the mechanism in the tool itself.
- Verification: The simplified version removes the redundant phrase 'Nutcrackers are often used for' while maintaining the core meaning.

#### EXPL-26

- Pair: `pair:en:8c08ef0ad877be7bcc65dcd04b8a89d0c69c4ed3c27561d3b2490818e5c11e76`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Sadou Hayatou (15 February 1942 – 1 August 2019) was a Cameroonian politician.
- Simplified: Sadou Hayatou (15 February 1942 – 1 August 2019) was a Cameroonian politician.Hayatou died on 1 August 2019 at the age of 77.
- Degraded: Sadou Hayatou (15 February 1942 – 1 August 2019) was a Cameroonian politician.
- Verification: Removed 'died on' and 'at the age of 77'

#### EXPL-27

- Pair: `pair:en:8ee4fb8598b446221a00adc3056bb3ae9bb704bf7d58905a59661b51883d4c29`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Mihailo Đurić (Serbian Cyrillic: Михаило Ђурић; 22 August 1925 – 25 November 2011) was one of Serbia's most prominent philosophers.
- Simplified: Mihailo Đurić (Serbian Cyrillic: Михаило Ђурић; 22 August 1925 – 25 November 2011) was one of Serbia's most prominent philosophers, a professor at the University of Belgrade's Law School, and a member of the Serbian Academy of Sciences and Arts.
- Degraded: Mihailo Đurić (Serbian Cyrillic: Михаило Ђурић; 22 August 1925 – 25 November 2011) was one of Serbia's most prominent philosophers, and a member of the Serbian Academy of Sciences and Arts.
- Verification: The simplified version removes the added information about being a professor without altering the original facts.

#### EXPL-28

- Pair: `pair:en:982bcba0bf91157e1ad010027ff9d719cd83ce8b6bd6d50dc6b54aee0ec24495`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Christopher Crosby Farley (February 15, 1964 – December 18, 1997) was an American actor and comedian.
- Simplified: Christopher Crosby "Chris" Farley (February 15, 1964 – December 18, 1997) was an American comedian, movie, television, stage, and voice actor.
- Degraded: Christopher Crosby Farley (February 15, 1964 – December 18, 1997) was an American comedian.
- Verification: Removed 'movie, television, stage, and voice' as it was an added explanation.

#### EXPL-29

- Pair: `pair:en:9d0b346c0447b46580e30e92e99755c09cfd06d4a277f160b86b70ca97d410fd`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Iberia Airlines Flight 610 was a scheduled domestic passenger flight from Madrid to Bilbao, Spain.
- Simplified: Iberia Airlines Flight 610 was a flight from Madrid to Bilbao, Spain on 19 February 1985.
- Degraded: Iberia Airlines Flight 610 was a flight from Madrid to Bilbao, Spain.
- Verification: Removed date as it was an added explanation.

#### EXPL-30

- Pair: `pair:en:9d3b232d4c080a7356f7d05a5c7a95119142cedbe25acc2869b1c6dd200622db`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Yao Beina (; 26 September 1981 – 16 January 2015), also known as Bella Yao, was a Chinese singer.
- Simplified: Yao Beina (born 姚贝娜; 26 September 1981 – 16 January 2015) was a Chinese singer and actress.
- Degraded: Yao Beina (26 September 1981 – 16 January 2015) was a Chinese singer and actress.
- Verification: Removed 'born 姚贝娜' to maintain the original meaning.

#### EXPL-31

- Pair: `pair:en:a003cddbf614b98f4b79796f2248652b384ef43ed42206e76293618e79bdc2e3`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Upon deposit of the last instrument of ratification, united Germany became fully sovereign on 15 March 1991.
- Simplified: On 15 March 1991 the treaty treaty took effect, and Germany became fully sovereign (that is, able to control everything in its own territory, including Berlin)
- Degraded: On 15 March 1991 united Germany became fully sovereign (that is, able to control everything in its own territory, including Berlin)
- Verification: Removed 'treaty treaty took effect' as it was an added explanation.

#### EXPL-32

- Pair: `pair:en:a0ac83ab84b63d070ce5882d24160b79a77902627b4a6d9c0c04c60b77aece7c`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: The clothing worn by plague doctors was intended to protect them from airborne diseases.
- Simplified: The plague doctor's costume was the clothes worn by a plague doctor to protect him from diseases spread through the air.
- Degraded: The plague doctor's costume was the clothes worn to protect him from diseases spread through the air.
- Verification: Verification: The simplified version removes the redundant phrase 'by a plague doctor' while maintaining the original meaning.

#### EXPL-33

- Pair: `pair:en:a34eeb4bcf440a1e7daab057991bb843b5f2b2186dec9e1ce69543f438ca483d`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Atheris is a genus of venomous vipers known as bush vipers.
- Simplified: Atheris is a genus of venomous vipers found only in rain forest areas of Sub-Saharan Africa.Atheris are commonly known as ""Bush Vipers"".
- Degraded: Atheris is a genus of venomous vipers found only in Sub-Saharan Africa. Atheris are commonly known as 'Bush Vipers'.
- Verification: The simplification is grammatical and preserves the core meaning without the additional geographical detail.

#### EXPL-34

- Pair: `pair:en:ab55f2b8231d7f6db5ca2c959f1c6daf9d39ebb2d817b33e05bb73fb078eb16e`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Failed** (`simplified_and_degraded_are_identical`; automatic_triage_pending_human_audit)
- Original: He died in the hospital on 4 September 2017 from kidney failure.
- Simplified: Moschin died of kidney failure on 4 September 2017 at his home in Terni, Italy at the age of 88.
- Degraded: Moschin died of kidney failure on 4 September 2017 at his home in Terni, Italy at the age of 88.
- Verification: The age of 88 and location details are preserved.

#### EXPL-35

- Pair: `pair:en:b2242268f06621bec801bac7b2edc3bf3c69caf9f9b6acb7dc6081e7bebfa9f8`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Miss Representation is a 2011 American documentary film written, directed, and produced by Jennifer Siebel Newsom.
- Simplified: Miss Representation is a 2011 American documentary film.It was written, directed, and produced by Jennifer Siebel Newsom."Miss Representation" won Outstanding Documentary at the 2012 Gracie Allen Awards.
- Degraded: Miss Representation is a 2011 American documentary film.It was written, directed, and produced by Jennifer Siebel Newsom.
- Verification: Removed the added explanation about winning an award.

#### EXPL-36

- Pair: `pair:en:ba94cc3643f7aa89f6784ddaeeb257b2ac6e3b39b327bc504022cc2aa1f15908`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Tongyong Pinyin was the official romanization of Mandarin Chinese in Taiwan between 2002 and 2008.
- Simplified: Tongyong Pinyin is a romanization of Mandarin Chinese, or a way to write Mandarin in the Roman alphabet, that was invented in Taiwan.In 2002, it became the official romanization in Taiwan, even though no one was forced to use it.
- Degraded: Tongyong Pinyin is a romanization of Mandarin Chinese, or a way to write Mandarin in the Roman alphabet, that was invented in Taiwan. In 2002, it became the official romanization in Taiwan, even though no one was forced to use it.
- Verification: The simplified version retains the original meaning while removing the redundant explanation.

#### EXPL-37

- Pair: `pair:en:bf62635b2169428fe8dc8d03bfe0922af19d65d78c5357acedad0a0fd3c52ca5`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Benign paroxysmal vertigo of childhood is an uncommon neurological disorder which presents with recurrent episodes of dizziness.
- Simplified: Benign paroxysmal vertigo of childhood (BPVC for short) is a medical problem that happens in children."Benign" means "harmless;" "paroxysmal" means something comes and goes suddenly; and "vertigo" means "dizziness."
- Degraded: Benign paroxysmal vertigo of childhood (BPVC for short) is a medical problem that happens in children.
- Verification: The simplified version removes the explanations about 'benign', 'paroxysmal', and 'vertigo' while keeping the core meaning intact.

#### EXPL-38

- Pair: `pair:en:cb370eb11544adec2a8a29edd34777cde73800329d136965c09760d827d67625`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: The River Fowey ( ; ) is a river in Cornwall, England, United Kingdom.
- Simplified: The River Fowey is a river in Cornwall, United Kingdom, which follows an irregular course across Bodmin Moor and enters the English Channel at Fowey.
- Degraded: The River Fowey is a river in Cornwall, United Kingdom, and enters the English Channel at Fowey.
- Verification: Verification: The sentence is grammatical and preserves the essential information about the location of the River Fowey without the added explanation.

#### EXPL-39

- Pair: `pair:en:cc42fb747790df55bad72661b4758f0644a848f518e82a7b17e47ed821b88e59`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Hondo died in Paris on 2 March 2019.
- Simplified: Hondo died in Paris on 2 March 2019, aged 82.
- Degraded: Hondo died in Paris on 2 March 2019.
- Verification: The date is preserved while removing the age.

#### EXPL-40

- Pair: `pair:en:d137327aff7a60c8f0ee1eddf029385b6eaab7be2bb2b7d0a945bc589e0c4a3f`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: The Tevatron was a synchrotron that accelerated protons and antiprotons in a 6.28 km ring to energies of up to 1 TeV, hence its name.
- Simplified: The Tevatron is a synchrotron that accelerates protons and antiprotons in a 6.28 km (3.90 miles) ring to energies of up to 1 TeV, hence its name.
- Degraded: The Tevatron is a synchrotron that accelerates protons and antiprotons in a 6.28 km ring to energies of up to 1 TeV, hence its name.
- Verification: Removed '3.90 miles' as it was an added explanation.

#### EXPL-41

- Pair: `pair:en:d156b333613691084302fe0bc42e005b5283abf3340ba524749058b2b94ac112`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: La bohème (, ) is an opera in four acts,
- Simplified: La bohème is a tragic Italian opera in four acts.
- Degraded: La bohème is an opera in four acts.
- Verification: Verification: The original sentence did not include any description of the opera being tragic or its language.

#### EXPL-42

- Pair: `pair:en:d4fd7a82039233debe842f8dc3f03285152af63bdbcdde40d2c1ca31d3b68610`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Anders Harald Wejryd (born 8 August 1948) is a Swedish Lutheran clergyman.
- Simplified: Anders Harald Wejryd, born 8 August 1948 in Falköping, Sweden is a Swedish Lutheran clergyman.
- Degraded: Anders Harald Wejryd, born 8 August 1948 is a Swedish Lutheran clergyman.
- Verification: Removed 'in Falköping, Sweden' as it was an added explanation.

#### EXPL-43

- Pair: `pair:en:d62220d0200c9aad54da2b063ba85b3e31694f76ee588e45a43b0265c18f5888`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Medium** (`text_changed_but_declared_span_not_verified`; automatic_triage_pending_human_audit)
- Original: He has been in office since January 2017.
- Simplified: He is the President of Ghana, in office since January 2017.
- Degraded: He has been in office since January 2017.
- Verification: Preserved the original meaning without the added explanation.

#### EXPL-44

- Pair: `pair:en:e0baaa292a393e352b7985ab7b0fff605243293d09032c72c73140e9d1b5a38f`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: He died in Sydney on 8 August 2014 at the age of 85.
- Simplified: Sculthorpe died after a long illness on 8 August 2014 in Sydney, New South Wales.
- Degraded: Sculthorpe died on 8 August 2014 in Sydney, New South Wales.
- Verification: The simplified version removes the age detail while keeping the date and location.

#### EXPL-45

- Pair: `pair:en:e3e6e672ad75933dd6829b70507c3ffb5ae4df29b97c84b50b2f0795515a627c`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: The United States Bill of Rights comprises the first ten amendments to the United States Constitution.
- Simplified: The Bill of Rights is the name for the first ten amendments to the United States Constitution, which limit the power of the federal government and guarantee citizens of the United States certain rights.Originally, the Bill of Rights had 12 different amendments, but the first two were not passed by enough states.
- Degraded: The Bill of Rights is the name for the first ten amendments to the United States Constitution, which limit the power of the federal government.
- Verification: Removed 'and guarantee citizens of the United States certain rights' as it was an additional explanation.

#### EXPL-46

- Pair: `pair:en:e726804dcc2f48be2e9cfeb3d1411202891a19891baecfdfcc97c6dfc70c1a71`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Everard Lorne Carpenter (June 15, 1887 – April 30, 1963) was a Canadian professional ice hockey player.
- Simplified: Everard Lorne Carpenter (June 15, 1890 in Hartford, Michigan – April 30, 1963 in Winnipeg, Manitoba) was a Canadian professional ice hockey defenseman who played two seasons in the National Hockey League (NHL) for the Quebec Bulldogs and Hamilton Tigers.
- Degraded: Everard Lorne Carpenter (June 15, 1890 – April 30, 1963 in Winnipeg, Manitoba) was a Canadian professional ice hockey defenseman who played two seasons in the National Hockey League (NHL) for the Quebec Bulldogs and Hamilton Tigers.
- Verification: Hartford, Michigan is removed as it was an added detail not present in the original.

#### EXPL-47

- Pair: `pair:en:e7872a237215d451aa6a7ca050747610dd1c07a7e8aa3f0cc810855fc7f2cdaf`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: He grew up in Manhattan and Stamford, Connecticut.
- Simplified: He was born in New York City and raised in Manhattan and Stamford, Connecticut.
- Degraded: He grew up in Manhattan and Stamford, Connecticut.
- Verification: Verification: The sentence now lacks the explicit mention of birth but retains the information about growing up in both locations.

#### EXPL-48

- Pair: `pair:en:edcd0c31c645c956b58c4f4f647cd5a919f1d2df619666089fe34ed119d5444d`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Ginger ale is a carbonated soft drink flavoured with ginger.
- Simplified: Ginger ale is a soft drink flavored with the root of a plant known as ginger.Ginger beer is a non-alcoholic soft drink that is also flavored with ginger root.
- Degraded: Ginger ale is a soft drink flavored with the root of a plant known as ginger. Ginger beer is a non-alcoholic soft drink that is also flavored with ginger root.
- Verification: The phrase 'the root of a plant known as' was removed to simplify the sentence while preserving the core meaning.

#### EXPL-49

- Pair: `pair:en:f695f854bde763499627414ca6864dc07e091d499c075aee9796902c5c4daaa4`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: Ryan Walker Longwell (born August 16, 1974), is a retired American football kicker.
- Simplified: Ryan Longwell (born August 16, 1974) was an NFL kicker from 1997-2012.
- Degraded: Ryan Longwell (born August 16, 1974) was an NFL kicker.
- Verification: Removed 'from 1997-2012' to maintain original meaning.

#### EXPL-50

- Pair: `pair:en:ffdd68a8a506a3b917ec37d411a57238243c702a35808b5410d55f05326e4be0`
- Source strategy: `EXPL`
- Assigned operation: `remove_added_explanation`
- Quality: **Good** (`all_automatic_checks_passed`; automatic_triage_pending_human_audit)
- Original: The Panzer I was a light tank produced in Germany in the 1930s.
- Simplified: The Panzer I tank was a Nazi Germany light tank that was used during many wars of the 1930s as well as during World War II.
- Degraded: The Panzer I tank was a light tank that was used during many wars of the 1930s as well as during World War II.
- Verification: Removed 'Nazi' and 'Germany' to maintain meaning and grammar.
