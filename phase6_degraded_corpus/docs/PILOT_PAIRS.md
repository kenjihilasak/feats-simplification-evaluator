# Phase 6 meaning-degradation pilot: 50 audited pairs

[Automation and methodology](DEGRADATION_AUTOMATION.md) · [Phase 6 README](../README.md)

Each example contains a source sentence, an accepted clean simplification, and a deliberately incorrect simplification with one severe meaning error. Bold text marks the recorded change when the span occurs literally.

## Summary

- Pairs: **50**
- Qwen pass 1: **20**
- Qwen pass 2: **11**
- Manual corrections after model audit failure: **19**

| Corruption | Count |
|---|---:|
| date replacement | 4 |
| entity replacement | 10 |
| event replacement | 6 |
| negation reversal | 9 |
| number replacement | 9 |
| property replacement | 5 |
| relation reversal | 7 |

## Pairs

### 1. Date Replacement

- **Pair ID:** `pair:en:5f8b7908cb70f4c8970073b8ef1389d5620e24087cb9cf0d420504847a9b9269`
- **Simplification strategy:** `COMP`
- **Accepted from:** Qwen pass 1
- **Original:** Federal elections were held in Germany on 24 September 2017 to elect the members of the 19th Bundestag.
- **Clean simplification:** The **2017** German federal election was held in Germany on 24 September 2017.
- **Degraded simplification:** The 2017 German federal election was held in Germany on 24 September **2018**.
- **Recorded change:** `2017` → `2018`

### 2. Date Replacement

- **Pair ID:** `pair:en:87fb34236414226e471fdef95c111e66b4fe089a0251817a681b00802ebf79c1`
- **Simplification strategy:** `COMP`
- **Accepted from:** Manual correction after Qwen audit failure
- **Original:** Following the agreement, on 1 September 1939, Germany invaded Poland, marking the beginning of World War II in Europe.
- **Clean simplification:** In **1939** the German invasion of Poland, began World War II in Europe.
- **Degraded simplification:** In **1949** the German invasion of Poland began World War II in Europe.
- **Recorded change:** `1939` → `1949`

### 3. Date Replacement

- **Pair ID:** `pair:en:9351620b5913f84e73902189d44b855eb948bd4fbb70dd81c00c8386c12927db`
- **Simplification strategy:** `COMP`
- **Accepted from:** Qwen pass 1
- **Original:** Harriet Elisabeth Beecher was born in Litchfield, Connecticut, on June 14, 1811.
- **Clean simplification:** She was born on June 14, **1811** in Litchfield, Connecticut.
- **Degraded simplification:** She was born on June 14, **1711** in Litchfield, Connecticut.
- **Recorded change:** `1811` → `1711`

### 4. Date Replacement

- **Pair ID:** `pair:en:980a9a8be40f9b6557e68f0b71957885d325bbed7e8f5f7f4f1857914afdc37c`
- **Simplification strategy:** `OMIT`
- **Accepted from:** Manual correction after Qwen audit failure
- **Original:** Angelo Peruzzi (] ; born 16 February 1970) is an Italian football coach and former goalkeeper, and a three-time winner of the Serie A Goalkeeper of the Year award.
- **Clean simplification:** Angelo Peruzzi (born **16 February 1970**) is a former Italian football player.
- **Degraded simplification:** Angelo Peruzzi (born **16 February 1980**) is a former Italian football player.
- **Recorded change:** `16 February 1970` → `16 February 1980`

### 5. Entity Replacement

- **Pair ID:** `pair:en:048b70c40b46c0adcc9465b11d30a7be17df3f0afede5bf6d64b1cc3e99b1132`
- **Simplification strategy:** `OMIT`
- **Accepted from:** Qwen pass 1
- **Original:** Daniele was born to a working-class family in Naples, his father being a harbor worker.
- **Clean simplification:** He was born in **Naples, Italy**.
- **Degraded simplification:** He was born in **Rome, Italy**.
- **Recorded change:** `Naples, Italy` → `Rome, Italy`

### 6. Entity Replacement

- **Pair ID:** `pair:en:06a0a34e1fb4b053d900527b1470d52592bae3265de12c0468165ab268961fdc`
- **Simplification strategy:** `COMP`
- **Accepted from:** Manual correction after Qwen audit failure
- **Original:** Maroda is located 9 km ahead of Devprayag on the way to Sabdar Khal and Pauri.
- **Clean simplification:** It is only 9 km away from **Devpryag**, on the way to Pauri.
- **Degraded simplification:** It is only 9 km away from **Delhi**, on the way to Pauri.
- **Recorded change:** `Devpryag` → `Delhi`

### 7. Entity Replacement

- **Pair ID:** `pair:en:35f3a73499ee1375f9c65c61a0d6ee07817f2ab36d2495d948350ea756d3e012`
- **Simplification strategy:** `MOD`
- **Accepted from:** Manual correction after Qwen audit failure
- **Original:** Mars is the fourth planet from the Sun and the second-smallest planet in the Solar System after Mercury.
- **Clean simplification:** Mars is a planet in the **Solar System**. It is the fourth-closest planet to the Sun.
- **Degraded simplification:** Mars is a planet in the **Alpha Centauri system**. It is the fourth-closest planet to the Sun.
- **Recorded change:** `Solar System` → `Alpha Centauri system`

### 8. Entity Replacement

- **Pair ID:** `pair:en:3e806d22087f2862616c7f391085dd084ebd66b199bd495c7b5d6381bb8f7b70`
- **Simplification strategy:** `SYNT`
- **Accepted from:** Qwen pass 2
- **Original:** The Sambre ] is a river in northern France and in Wallonia, Belgium.
- **Clean simplification:** The Sambre is a river that flows through **France** and Belgium.
- **Degraded simplification:** The Sambre is a river that flows through **Germany** and Belgium.
- **Recorded change:** `France` → `Germany`

### 9. Entity Replacement

- **Pair ID:** `pair:en:794ce5d3a2a5c1046735d1338d388261199b7506a5732e6eeb35286bf440232b`
- **Simplification strategy:** `SYNT`
- **Accepted from:** Qwen pass 1
- **Original:** The White House is the official residence and workplace of the president of the United States.
- **Clean simplification:** The White House is a building in **Washington, D.C.** where the president of the United States lives.
- **Degraded simplification:** The White House is a building in **New York City** where the president of the United States lives.
- **Recorded change:** `Washington, D.C.` → `New York City`

### 10. Entity Replacement

- **Pair ID:** `pair:en:b8d469161b761f8125a1685843e3406d92288fb436ea30c9d5b5cb5b1db3b1d9`
- **Simplification strategy:** `OMIT`
- **Accepted from:** Qwen pass 2
- **Original:** She was born in Warsaw, in what was then the Kingdom of Poland, part of the Russian Empire.
- **Clean simplification:** She was born in **Warsaw**.
- **Degraded simplification:** She was born in **Warsaw, in what is now the United States**.
- **Recorded change:** `Warsaw` → `Warsaw, in what is now the United States`

### 11. Entity Replacement

- **Pair ID:** `pair:en:bc11159233ea5a0dc46d48182d7f3ae5f79caa89a1ffd0b3e2861a6a70c00b3f`
- **Simplification strategy:** `OMIT`
- **Accepted from:** Manual correction after Qwen audit failure
- **Original:** The Paris Opera Ballet () is a French ballet company that is an integral part of the Paris Opera and the oldest national ballet company.
- **Clean simplification:** The **Paris Opera Ballet** (in french: Ballet de l'Opéra national de Paris) is the oldest national ballet company in the world.
- **Degraded simplification:** The **London Opera Ballet** (in French: Ballet de l'Opéra national de Paris) is the oldest national ballet company in the world.
- **Recorded change:** `Paris Opera Ballet` → `London Opera Ballet`

### 12. Entity Replacement

- **Pair ID:** `pair:en:c3edc1c39452a170f44f3a0aafe1790e493121431fcfa9f565265b0fe7718fbe`
- **Simplification strategy:** `SYNT`
- **Accepted from:** Manual correction after Qwen audit failure
- **Original:** A scientist who works in the field of acoustics is an acoustician while someone working in the field of acoustics technology may be called an acoustical engineer.
- **Clean simplification:** A scientist who works in the field of acoustics is **an acoustician**.Someone who works with acoustics technology may be called an acoustical engineer.
- **Degraded simplification:** A scientist who works in the field of acoustics is **a botanist**. Someone who works with acoustics technology may be called an acoustical engineer.
- **Recorded change:** `an acoustician` → `a botanist`

### 13. Entity Replacement

- **Pair ID:** `pair:en:c8c25d0948b690593a902738e1a2024b3debce7c78e623ff8354d6a69238b33c`
- **Simplification strategy:** `COMP`
- **Accepted from:** Qwen pass 1
- **Original:** The flag of the Republic of Turkey, often referred to as the Turkish flag is a red flag featuring a white star and crescent.
- **Clean simplification:** The flag of **Turkey** has a white crescent moon and a star on a red background.
- **Degraded simplification:** The flag of **Greece** has a white crescent moon and a star on a red background.
- **Recorded change:** `Turkey` → `Greece`

### 14. Entity Replacement

- **Pair ID:** `pair:en:d71abf09cffb0bfab29029537f7feaa769d78886a96bd5c2f75e8c6ad2c21f73`
- **Simplification strategy:** `SYNT`
- **Accepted from:** Qwen pass 1
- **Original:** In the late 19th century, Japan was still largely unknown and exotic to Westerners.
- **Clean simplification:** In the late 19th century, **Westerners** knew little about Japan.
- **Degraded simplification:** In the late 19th century, **Japanese** knew little about Japan.
- **Recorded change:** `Westerners` → `Japanese`

### 15. Event Replacement

- **Pair ID:** `pair:en:21c6819e3297786aa2dafad4692d0d41980abcc9925ab345e59e372892d430f2`
- **Simplification strategy:** `SYNT`
- **Accepted from:** Manual correction after Qwen audit failure
- **Original:** A trainer is a class of aircraft designed specifically to facilitate flight training of pilots and aircrews.
- **Clean simplification:** A **train**ing aircraft, sometimes called a trainer, is an aircraft used to train future pilots and crews of aircraft.
- **Degraded simplification:** A training aircraft, sometimes called a trainer, is an aircraft used to **test** future pilots and crews of aircraft.
- **Recorded change:** `train` → `test`

### 16. Event Replacement

- **Pair ID:** `pair:en:5f139d4a4d9cbc6baaaeaa52e023fdfab1e6e136eebc5420e250c29cbd935e21`
- **Simplification strategy:** `SYN`
- **Accepted from:** Manual correction after Qwen audit failure
- **Original:** A meme ( ) is an idea, behavior, or style that spreads from person to person within a culture-often with the aim of conveying a particular phenomenon, theme, or meaning represented by the meme.
- **Clean simplification:** A meme (pronounced "meem") is an element of culture or behaviour that **gets transmitted between** individuals.
- **Degraded simplification:** A meme (pronounced "meem") is an element of culture or behaviour that **gets concealed from** individuals.
- **Recorded change:** `gets transmitted between` → `gets concealed from`

### 17. Event Replacement

- **Pair ID:** `pair:en:857c4700237ec2c316e62bc03fbdd47eee55341d6e17cd9ce40665e8ea56e6a8`
- **Simplification strategy:** `SYN`
- **Accepted from:** Qwen pass 2
- **Original:** Chemical biology is a scientific discipline spanning the fields of chemistry and biology.
- **Clean simplification:** Chemical biology is a science that **combines the fields of chemistry and biology**.
- **Degraded simplification:** Chemical biology is a science that **separates the fields of chemistry and biology**.
- **Recorded change:** `combines the fields of chemistry and biology` → `separates the fields of chemistry and biology`

### 18. Event Replacement

- **Pair ID:** `pair:en:8d48bf8709c87728898ec556a46ee8027bf996bb3ea7efb0e297d8021a20d1b4`
- **Simplification strategy:** `SYN`
- **Accepted from:** Qwen pass 2
- **Original:** Justinian's rule constitutes a distinct epoch in the history of the Later Roman empire, and his reign is marked by the ambitious but only partly realized renovatio imperii, or "restoration of the Empire".
- **Clean simplification:** Justinian also **increased the territories of his Empire** during his reign, for he tried to reconstruct the Roman Empire as it was in the second century.
- **Degraded simplification:** Justinian also **decreased the territories of his Empire** during his reign, for he tried to reconstruct the Roman Empire as it was in the second century.
- **Recorded change:** `increased the territories of his Empire` → `decreased the territories of his Empire`

### 19. Event Replacement

- **Pair ID:** `pair:en:b1f83d5c68a6cce3b298c2856aec2f16a7302644c0a3c982bd38872831e2a0c1`
- **Simplification strategy:** `OMIT`
- **Accepted from:** Qwen pass 1
- **Original:** Later she returned the award because of her own principles.
- **Clean simplification:** Later she **returned the award**.
- **Degraded simplification:** Later she **refused the award**.
- **Recorded change:** `returned the award` → `refused the award`

### 20. Event Replacement

- **Pair ID:** `pair:en:bf795799fec2c94388abe65c47708e1b1377b0f3566660e8b1f84cdc72a60013`
- **Simplification strategy:** `SYN`
- **Accepted from:** Qwen pass 1
- **Original:** Although larvae eat only milkweed, adult monarchs feed on the nectar of many plants including:
- **Clean simplification:** Its larvae feed on milkweed, but the **adults feed on the nectar of many flowers**.
- **Degraded simplification:** Its larvae feed on milkweed, but the **adults drink water from many flowers**.
- **Recorded change:** `adults feed on the nectar of many flowers` → `adults drink water from many flowers`

### 21. Negation Reversal

- **Pair ID:** `pair:en:0aaae7d734bc58c837541ed1d9b983ac66ac58f09cfe78cd4611723c0bce6490`
- **Simplification strategy:** `SYN`
- **Accepted from:** Qwen pass 1
- **Original:** The blue whale is the largest animal known to have ever lived.
- **Clean simplification:** The blue whale **is the largest animal on Earth**.
- **Degraded simplification:** The blue whale is **not the largest animal on Earth**.
- **Recorded change:** `is the largest animal on Earth` → `not the largest animal on Earth`

### 22. Negation Reversal

- **Pair ID:** `pair:en:13fa7af0c9d6ecc1804261afa85f8fc0c8b225f4e59d993856d038a06e21bd9d`
- **Simplification strategy:** `SYNT`
- **Accepted from:** Qwen pass 1
- **Original:** A spur is an outgrowth of bone covered in a sheath of horn found in various anatomical locations in some animals.
- **Clean simplification:** A spur **is a bone covered in horn that grows out of an animal's body.**
- **Degraded simplification:** A spur is a bone covered in horn that **does not grow out of an animal's body.**
- **Recorded change:** `is a bone covered in horn that grows out of an animal's body.` → `does not grow out of an animal's body.`

### 23. Negation Reversal

- **Pair ID:** `pair:en:30c0c6c3dfc5fdeb03e6c046a218f4389f273dccebdbb8bc9e439d201d677d88`
- **Simplification strategy:** `EXPL`
- **Accepted from:** Qwen pass 1
- **Original:** VHD discs are 25 cm in diameter, and store up to 60 minutes of video per side.
- **Clean simplification:** VHD discs **are** 25 cm (9 5/6 inches) in diameter, and store up to 60 minutes of video per side.
- **Degraded simplification:** VHD discs are 25 cm in diameter, and **do not store** up to 60 minutes of video per side.
- **Recorded change:** `are` → `do not store`

### 24. Negation Reversal

- **Pair ID:** `pair:en:4895db6ba263fb6c27a412308296547e2944ee4c3beaa43710366e6892d6d0be`
- **Simplification strategy:** `OMIT`
- **Accepted from:** Qwen pass 1
- **Original:** For its entire existence, it was a very safe Labor seat.
- **Clean simplification:** It **was a very safe** Labor seat.
- **Degraded simplification:** For its entire existence, it was **not a very safe** Labor seat.
- **Recorded change:** `was a very safe` → `not a very safe`

### 25. Negation Reversal

- **Pair ID:** `pair:en:52b59e2844fb4cd4bbe831c4f313ee0af4c4dd55242fa0d0868ca5b2041a47ac`
- **Simplification strategy:** `SYNT`
- **Accepted from:** Qwen pass 2
- **Original:** Meadow voles are an important prey for many hawks, owls, and mammalian carnivores, and they are also taken by some snakes.
- **Clean simplification:** The meadow vole **is preyed upon** by hawks, owls, snakes, and other predators.
- **Degraded simplification:** The meadow vole is **not preyed upon** by hawks, owls, snakes, and other predators.
- **Recorded change:** `is preyed upon` → `not preyed upon`

### 26. Negation Reversal

- **Pair ID:** `pair:en:5896125799250fac9962084ef242e0fce4dbf195bb9386c274224c1b023f415f`
- **Simplification strategy:** `SYNT`
- **Accepted from:** Manual correction after Qwen audit failure
- **Original:** The most familiar carriers of electrical charge are the electron and proton.
- **Clean simplification:** **Both electrons and protons carry** a charge.
- **Degraded simplification:** **Neither electrons nor protons carry** a charge.
- **Recorded change:** `Both electrons and protons carry` → `Neither electrons nor protons carry`

### 27. Negation Reversal

- **Pair ID:** `pair:en:9bdce3b79056bf381622bcda0a66ed4522f1198765e21267dfbf467e54296da6`
- **Simplification strategy:** `OMIT`
- **Accepted from:** Qwen pass 1
- **Original:** The Iraqi dinar (] ) (Arabic: دينار, (sign: د.ع; code: IQD) is the currency of Iraq.
- **Clean simplification:** The Iraqi dinar **is the currency of Iraq**.
- **Degraded simplification:** The Iraqi dinar is **not the currency of Iraq**.
- **Recorded change:** `is the currency of Iraq` → `not the currency of Iraq`

### 28. Negation Reversal

- **Pair ID:** `pair:en:cdb3f395b118000612b890da10d71023f4f1eb93d646a46582a83fc80b90c78a`
- **Simplification strategy:** `SYN`
- **Accepted from:** Qwen pass 1
- **Original:** The furcula works as a strut between a bird's shoulders, and articulates to each of the bird's scapulae.
- **Clean simplification:** It **is a strut** between a bird's shoulders, and connects to each of the bird's scapulae (shoulder blades).
- **Degraded simplification:** It **is not a strut** between a bird's shoulders, and connects to each of the bird's scapulae (shoulder blades).
- **Recorded change:** `is a strut` → `is not a strut`

### 29. Negation Reversal

- **Pair ID:** `pair:en:e8ccfd28ae5bbd4083ece12c239272c5ff28cca18b6a02501d8ae687a5c905a0`
- **Simplification strategy:** `SYNT`
- **Accepted from:** Qwen pass 2
- **Original:** Osteoarthritis begins in the cartilage and eventually causes the two opposing bones to erode into each other.
- **Clean simplification:** Osteoarthritis **is caused by cartilage between the bones wearing down.**
- **Degraded simplification:** Osteoarthritis is **not caused by cartilage between the bones wearing down**.
- **Recorded change:** `is caused by cartilage between the bones wearing down.` → `not caused by cartilage between the bones wearing down`

### 30. Number Replacement

- **Pair ID:** `pair:en:0b39cee30c199a3a857c20d2917cee52890baef57422c507adce3d276ea4b66b`
- **Simplification strategy:** `COMP`
- **Accepted from:** Qwen pass 1
- **Original:** David Alan Coulier (born September 21, 1959) is an American stand-up comedian, actor, voice actor, impressionist television host and private pilot.
- **Clean simplification:** David Alan "Dave" Coulier (born September 21, **1959**) is an American actor, voice actor, stand-up comedian, impressionist, and television host.
- **Degraded simplification:** David Alan 'Dave' Coulier (born September 21, **1960**) is an American actor, voice actor, stand-up comedian, impressionist, and television host.
- **Recorded change:** `1959` → `1960`

### 31. Number Replacement

- **Pair ID:** `pair:en:16d85ffdf0bcb61331adf47448be7f08175e2306ce718c6380abe86c33dce380`
- **Simplification strategy:** `OMIT`
- **Accepted from:** Qwen pass 2
- **Original:** The league currently consists of 12 teams.
- **Clean simplification:** It consists of **12** teams.
- **Degraded simplification:** It consists of **11** teams.
- **Recorded change:** `12` → `11`

### 32. Number Replacement

- **Pair ID:** `pair:en:19137fb62c8bc799aac9681e1ca62159f785fd6913ba68596d99fd87bb939d77`
- **Simplification strategy:** `OMIT`
- **Accepted from:** Qwen pass 1
- **Original:** Michael Dibdin (21 March 1947 – 30 March 2007) was a British crime writer who was famous for inventing Aurelio Zen, the principal character in 11 crime novels set in Italy.
- **Clean simplification:** Michael Dibdin (**21 March** 1947 – 30 March 2007) was a British crime writer.
- **Degraded simplification:** Michael Dibdin (**2 March** 1947 – 30 March 2007) was a British crime writer.
- **Recorded change:** `21 March` → `2 March`

### 33. Number Replacement

- **Pair ID:** `pair:en:582cf88b3d5b304f339247c120075b72d8261bd2847ec68945afe1925fb476da`
- **Simplification strategy:** `SYN`
- **Accepted from:** Manual correction after Qwen audit failure
- **Original:** He created roughly 900 oil paintings and more than 2,000 watercolors, as well as countless sketches and charcoal drawings.
- **Clean simplification:** During his career, he created about **900** oil paintings and more than 2,000 watercolors, as well as many sketches and charcoal drawings.
- **Degraded simplification:** During his career, he created about **90** oil paintings and more than 2,000 watercolors, as well as many sketches and charcoal drawings.
- **Recorded change:** `900` → `90`

### 34. Number Replacement

- **Pair ID:** `pair:en:98243871f32f5011048499e71f87a016241e346be264c31def6fd68d9a320570`
- **Simplification strategy:** `OMIT`
- **Accepted from:** Qwen pass 1
- **Original:** The area of the country totals 22960 km2 , an area slightly larger than El Salvador, Israel, New Jersey or Wales.
- **Clean simplification:** The area of the country totals **22960** km2.
- **Degraded simplification:** The area of the country totals **2296** km2.
- **Recorded change:** `22960` → `2296`

### 35. Number Replacement

- **Pair ID:** `pair:en:9e32dda1de0dab2a1cd30d8afc75177189d2ec324d4cf98dca93ae9775d4d5b8`
- **Simplification strategy:** `OMIT`
- **Accepted from:** Manual correction after Qwen audit failure
- **Original:** They have three children, a daughter born in July 2011 and two sons born in October 2013 and March 2016.
- **Clean simplification:** They have **three** children.
- **Degraded simplification:** They have **two** children.
- **Recorded change:** `three` → `two`

### 36. Number Replacement

- **Pair ID:** `pair:en:a5f6a14ca796f0429acff0a4c25c4cfdc312c0dd45938c9cb803f690d0f86055`
- **Simplification strategy:** `OMIT`
- **Accepted from:** Qwen pass 1
- **Original:** Beginning in a first competition in 486 BC each playwright submitted a comedy.
- **Clean simplification:** From **486** BC, each playwright also submitted a comedy.
- **Degraded simplification:** From **386** BC, each playwright also submitted a comedy.
- **Recorded change:** `486` → `386`

### 37. Number Replacement

- **Pair ID:** `pair:en:d091e4eb93c0c1c90f60bba7f5656af0df893ead8a9ee84689df91ae5d06c854`
- **Simplification strategy:** `OMIT`
- **Accepted from:** Manual correction after Qwen audit failure
- **Original:** The Blue Nile flows about 1,400 kilometres to Khartoum, where the Blue Nile and White Nile join to form the Nile.
- **Clean simplification:** The Blue Nile flows about **1,400** kilometres to Khartoum.
- **Degraded simplification:** The Blue Nile flows about **140** kilometres to Khartoum.
- **Recorded change:** `1,400` → `140`

### 38. Number Replacement

- **Pair ID:** `pair:en:fc14dd8791b3e40f955df18d79b6fa88d94b6cbb95a92ca7237fbf1a4f89f18e`
- **Simplification strategy:** `EXPL`
- **Accepted from:** Qwen pass 1
- **Original:** The distance of the course (run counterclockwise around France) was 3657 km .
- **Clean simplification:** The distance of the race was **3657** km (2272 mi).
- **Degraded simplification:** The distance of the course (run counterclockwise around France) was **2657** km.
- **Recorded change:** `3657` → `2657`

### 39. Property Replacement

- **Pair ID:** `pair:en:375ab0961fbd3f11be93c17d5e5e748f34cdc1017ffba444cbf97157fffa1a0f`
- **Simplification strategy:** `SYN`
- **Accepted from:** Manual correction after Qwen audit failure
- **Original:** Both symphonies were premiered in a long and under-rehearsed concert in the Theater an der Wien in Vienna on 22 December 1808.
- **Clean simplification:** The symphony was **first** performed in Vienna, Austria, at the Theater an der Wien on 22 December 1808.
- **Degraded simplification:** The symphony was **last** performed in Vienna, Austria, at the Theater an der Wien on 22 December 1808.
- **Recorded change:** `first` → `last`

### 40. Property Replacement

- **Pair ID:** `pair:en:3fdebbf8cfccd910969d0672de754a8c9bcc0e4804f3d95bafa2b6670cebd0d6`
- **Simplification strategy:** `COMP`
- **Accepted from:** Manual correction after Qwen audit failure
- **Original:** Norman Rockwell was born on February 3, 1894, in New York City, to Jarvis Waring Rockwell and Anne Mary "Nancy" Rockwell, born Hill.
- **Clean simplification:** Rockwell was born on February 3, 1894 in **New York City** to Jarvis Waring Rockwell and Anne Mary (Hill) Rockwell.
- **Degraded simplification:** Rockwell was born on February 3, 1894 in **a rural village** to Jarvis Waring Rockwell and Anne Mary (Hill) Rockwell.
- **Recorded change:** `New York City` → `a rural village`

### 41. Property Replacement

- **Pair ID:** `pair:en:8aab3013f5dba5c040dc410ccbbf6507a3b8e2f74e26557269e828a0d45110d1`
- **Simplification strategy:** `MOD`
- **Accepted from:** Manual correction after Qwen audit failure
- **Original:** Cassowaries have three-toed feet with sharp claws.
- **Clean simplification:** Cassowaries have three toes on each foot. Each has a **sharp** claw.
- **Degraded simplification:** Cassowaries have three toes on each foot. Each has a **blunt** claw.
- **Recorded change:** `sharp` → `blunt`

### 42. Property Replacement

- **Pair ID:** `pair:en:e313df9149034a0c5de0068a4c95c78c820c0e6f5789eefec64c4a802990e111`
- **Simplification strategy:** `OMIT`
- **Accepted from:** Qwen pass 2
- **Original:** Destelbergen (] ) is a municipality located in the Belgian province of East Flanders.
- **Clean simplification:** Destelbergen is a municipality in the **Belgian province of East Flanders**.
- **Degraded simplification:** Destelbergen is a municipality in the **French province of East Flanders**.
- **Recorded change:** `Belgian province of East Flanders` → `French province of East Flanders`

### 43. Property Replacement

- **Pair ID:** `pair:en:f0e577bd8f0b531d490e43eb514defead6cde8276783674d2cc939a4044a7ea9`
- **Simplification strategy:** `SYN`
- **Accepted from:** Qwen pass 1
- **Original:** The original texts of the Tanakh were mainly in Hebrew, with some portions in Aramaic.
- **Clean simplification:** In the Old Testament, Tanakh was mostly written in Hebrew; a few parts were written in **Aramaic**.
- **Degraded simplification:** In the Old Testament, Tanakh was mostly written in Hebrew; a few parts were written in **Greek**.
- **Recorded change:** `Aramaic` → `Greek`

### 44. Relation Reversal

- **Pair ID:** `pair:en:0df8c52340f325ebff32f473e3f49411f0040f7ae83b0eabd3913a562615df90`
- **Simplification strategy:** `SYNT`
- **Accepted from:** Manual correction after Qwen audit failure
- **Original:** * Dark chocolate: sugar, cocoa butter, cocoa liquor, and (sometimes) vanilla
- **Clean simplification:** **Dark or bittersweet chocolate is made from sugar, cocoa butter, and chocolate liquor**.
- **Degraded simplification:** **Sugar, cocoa butter, and chocolate liquor are made from dark or bittersweet chocolate**.
- **Recorded change:** `Dark or bittersweet chocolate is made from sugar, cocoa butter, and chocolate liquor` → `Sugar, cocoa butter, and chocolate liquor are made from dark or bittersweet chocolate`

### 45. Relation Reversal

- **Pair ID:** `pair:en:6308f6712da886f31d7ae656d83c7ee8fab452b753b6d5a01c904ba86245363f`
- **Simplification strategy:** `MOD`
- **Accepted from:** Qwen pass 2
- **Original:** Metro is the second-busiest rapid transit system in the United States in number of passenger trips, after the New York City Subway.
- **Clean simplification:** **It has the second busiest rapid transit system in the United States.The New York City Subway is the busiest.**
- **Degraded simplification:** **The New York City Subway has the second busiest rapid transit system in the United States. Metro is the busiest.**
- **Recorded change:** `It has the second busiest rapid transit system in the United States.The New York City Subway is the busiest.` → `The New York City Subway has the second busiest rapid transit system in the United States. Metro is the busiest.`

### 46. Relation Reversal

- **Pair ID:** `pair:en:b7d27644d6bd9def62b0afb330d543f39779a82bd8ce70d6bae29d22da27aa8e`
- **Simplification strategy:** `OMIT`
- **Accepted from:** Manual correction after Qwen audit failure
- **Original:** It is 302.4 km2 , measuring 28 km long and 22 km wide, making it the 4th largest island in South Korea.
- **Clean simplification:** The island measures **28 km long and 22 km wide**, and is the 4th largest island in South Korea.
- **Degraded simplification:** The island measures **28 km wide and 22 km long**, and is the 4th largest island in South Korea.
- **Recorded change:** `28 km long and 22 km wide` → `28 km wide and 22 km long`

### 47. Relation Reversal

- **Pair ID:** `pair:en:f705c0ccf28f95b6f9ef8c77097a06636bb62b899a1c0631934cda5813a603a4`
- **Simplification strategy:** `COMP`
- **Accepted from:** Manual correction after Qwen audit failure
- **Original:** Dinosaurs laid eggs, some of which have been preserved as petrified fossils.
- **Clean simplification:** **Dinosaurs also laid eggs**, of which fossils have been found.
- **Degraded simplification:** **Fossilized eggs produced dinosaurs**.
- **Recorded change:** `Dinosaurs also laid eggs` → `Fossilized eggs produced dinosaurs`

### 48. Relation Reversal

- **Pair ID:** `pair:en:f79f2ef73ffd68d9987a2a8b3ab7a2d084ab5828c88e276b4ee1a377ac431d32`
- **Simplification strategy:** `SYNT`
- **Accepted from:** Qwen pass 2
- **Original:** Some salamander species use tail autotomy to escape predators.
- **Clean simplification:** Salamanders **can drop their tail to escape** predators.
- **Degraded simplification:** **Predators can drop their tail to escape** salamanders.
- **Recorded change:** `can drop their tail to escape` → `Predators can drop their tail to escape`

### 49. Relation Reversal

- **Pair ID:** `pair:en:fbc3a088d1a0018070d3cff4e5c84ec1985a457e806a31738394be5e902d0a13`
- **Simplification strategy:** `MOD`
- **Accepted from:** Qwen pass 2
- **Original:** Nearly half of all the mud volcanoes on Earth are concentrated in Azerbaijan, these volcanoes were also among nominees for the New7Wonders of Nature.
- **Clean simplification:** Another interesting feature of Azerbaijan are the mud volcanoes - half of all mud volcanoes in the world are **situated in Azerbaijan**.
- **Degraded simplification:** Another interesting feature of Azerbaijan are the mud volcanoes - half of all mud volcanoes in the world **situate in other countries**.
- **Recorded change:** `situated in Azerbaijan` → `situate in other countries`

### 50. Relation Reversal

- **Pair ID:** `pair:en:fc0a5943accc4e7ff64065c9bfe4dc4a99d90b256d69868a7091c6ec94c31894`
- **Simplification strategy:** `COMP`
- **Accepted from:** Manual correction after Qwen audit failure
- **Original:** Cloning is the process of producing genetically identical individuals of an organism either naturally or artificially.
- **Clean simplification:** In biology, **cloning is the process of producing one or more genetically-identical individuals**.
- **Degraded simplification:** In biology, **cloning is produced by one or more genetically-identical individuals**.
- **Recorded change:** `cloning is the process of producing one or more genetically-identical individuals` → `cloning is produced by one or more genetically-identical individuals`
