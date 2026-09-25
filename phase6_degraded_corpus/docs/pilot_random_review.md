# Phase 6 random pilot review

Deterministic stratified sample: **50 cases**, seed `20260925`, up to 3 examples per available dimension × automatic-result stratum.

For each case, select one decision. A valid case must contain exactly one degradation in the target dimension and preserve all other dimensions.

## Sample coverage

| Dimension | Good | Medium | Failed | Total |
|---|---:|---:|---:|---:|
| FLUENCY | 3 | 3 | 3 | 9 |
| OMIT | 3 | 3 | 3 | 9 |
| SYN | 3 | 3 | 3 | 9 |
| MOD | 3 | 3 | 0 | 6 |
| ILLOC | 3 | 3 | 2 | 8 |
| EXPL | 3 | 3 | 3 | 9 |

## Review cases

### Case 01

- **Target dimension:** `EXPL`
- **Automatic result:** `GOOD`
- **Pair:** `pair:en:edcd0c31c645c956b58c4f4f647cd5a919f1d2df619666089fe34ed119d5444d`
- **Original:** Ginger ale is a carbonated soft drink flavoured with ginger.
- **Simplified:** Ginger ale is a soft drink flavored with the root of a plant known as ginger.Ginger beer is a non-alcoholic soft drink that is also flavored with ginger root.
- **Degraded:** Ginger ale is a soft drink flavored with the root of a plant known as ginger. Ginger beer is a non-alcoholic soft drink that is also flavored with ginger root.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 02

- **Target dimension:** `EXPL`
- **Automatic result:** `FAILED`
- **Pair:** `pair:en:60f5f8fdde6f14d64a3629984d4eee1b7fdb7adbf39c2169c2ec58f48a915a09`
- **Original:** María José de Pablo Fernández, known professionally as Cote de Pablo (born November 12, 1979), is a Chilean-American actress and singer.
- **Simplified:** Maria Jose de Pablo Fernandez, also known as Cote de Pablo (born November 12, 1979 in Santiago, Chile), is a Chilean-American actress and singer.
- **Degraded:** Maria Jose de Pablo Fernandez, also known as Cote de Pablo (born November 12, 1979 in Santiago, Chile), is a Chilean-American actress and singer.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 03

- **Target dimension:** `FLUENCY`
- **Automatic result:** `GOOD`
- **Pair:** `pair:en:7043324323583ee4969658f72f13404e52475efccef2c93245fd6ce8cf868734`
- **Original:** By 1700, however, the empire had broken up into areas controlled by many individual ethnic groups.
- **Simplified:** By 1700 the empire had broken up into areas that were controlled by individual groups of people which was known by the Portuguese by collecting information.
- **Degraded:** By 1700 the empire had broken up into areas that were controlled by individual groups of people which the Portuguese by collecting information.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 04

- **Target dimension:** `EXPL`
- **Automatic result:** `FAILED`
- **Pair:** `pair:en:84de07d98a2f3e3cbfbf397f1c7ccc28090140f4a719203fdea5c3fb536dff7f`
- **Original:** Over 4,000 living species are known.
- **Simplified:** There are about 5,000 living species, and 15,000 fossil species are known.
- **Degraded:** There are about 5,000 living species, and 15,000 fossil species are known.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 05

- **Target dimension:** `ILLOC`
- **Automatic result:** `FAILED`
- **Pair:** `pair:en:d19a27838c8c35c4aa7e3a530f6e580d1abe2b10e3586f23cb771f75bb04b2a1`
- **Original:** In mathematics, magnitude is the size of a mathematical object, a property which determines whether the object is larger or smaller than other objects of the same kind.
- **Simplified:** The magnitude of a mathematical object is its size: a property by which it can be larger or smaller than other objects of the same kind.
- **Degraded:** The magnitude of a mathematical object is its size: a property by which it can be larger or smaller than other objects of the same kind.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 06

- **Target dimension:** `FLUENCY`
- **Automatic result:** `GOOD`
- **Pair:** `pair:en:21d9dbafb59a7479e7d0d3bc1726b9555376eb0c80f5b21def2645eaeba6c5ec`
- **Original:** When three people have sex with each other, it is called a "threesome".
- **Simplified:** When three people have sex with each other, it is called a threesome.
- **Degraded:** When three people have sex with each other, it is called a threesomes.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 07

- **Target dimension:** `SYN`
- **Automatic result:** `GOOD`
- **Pair:** `pair:en:4ac68c8ebbb7b2c56195a6a083a834165e5b993755cb4b9a48d9918e3e581d6a`
- **Original:** Islam in Russia is the nation's second most widely professed religion.
- **Simplified:** Islam is the second largest religion of Russia, after Orthodox Christianity.
- **Degraded:** Islam in Russia is the nation's second most widely professed religion.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 08

- **Target dimension:** `OMIT`
- **Automatic result:** `MEDIUM`
- **Pair:** `pair:en:01ac54d89fb79c5f1afb9ca2c4811c920c229144e8008722e749f6e05a1d3d6d`
- **Original:** From 1989 she was the general secretary of the All India Anna Dravida Munnetra Kazhagam (AIADMK), a Dravidian party whose cadre revered her as their "Amma" (mother) and Puratchi "Thalaivi" (revolutionary leader) .
- **Simplified:** From 1989 she was the general secretary of the All India Anna Dravida Munnetra Kazhagam , a Dravidian party.
- **Degraded:** From 1989 she was the general secretary of the All India Anna Dravida Munnetra Kazhagam, a Dravidian party.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 09

- **Target dimension:** `OMIT`
- **Automatic result:** `MEDIUM`
- **Pair:** `pair:en:0d6adf6e8b9fccba797ece4b6831c09d94b5321e8840b77b091b5677b9fc2deb`
- **Original:** These trees were planted in Washington, D.C., and another 3,800 trees were donated in 1965.
- **Simplified:** These trees were planted in Washington, D.C..
- **Degraded:** These trees were planted in Washington, D.C., and another 3,800 trees were donated.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 10

- **Target dimension:** `ILLOC`
- **Automatic result:** `GOOD`
- **Pair:** `pair:en:0265450034b45ee13af18624679d2611726b4d5535d2a096a862432f072bd0e2`
- **Original:** "Implicit atheism" is "the absence of theistic belief without a conscious rejection of it" and "explicit atheism" is the conscious rejection of belief.
- **Simplified:** "Implicit atheism" is when you do not believe in God because you do not know about the concept of God."Explicit atheism" is when you do not believe in God after learning about the idea.Those two quotes describe implicit atheism.
- **Degraded:** "Implicit atheism" is when you do not believe in God after knowing about the concept of God."Explicit atheism" is when you do not believe in God because you do not know about the idea.Those two quotes describe implicit atheism.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 11

- **Target dimension:** `SYN`
- **Automatic result:** `MEDIUM`
- **Pair:** `pair:en:678d3ca33a6dc5ecc9592667ecb522588473ab5805a4da6530c2f26311baf1e1`
- **Original:** Ernest Edward Kovacs (January 23, 1919 – January 13, 1962) was an American comedian, actor, and writer.
- **Simplified:** Ernie Kovacs (January 23, 1919 – January 13, 1962) was an American author, comedian and actor.
- **Degraded:** Ernie writer

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 12

- **Target dimension:** `SYN`
- **Automatic result:** `FAILED`
- **Pair:** `pair:en:52d41de0b38a31773c3886ebcbfe119a6bdaaae3a16aaa42654364d31b48d128`
- **Original:** A Tesla coil is an electrical resonant transformer circuit designed by inventor Nikola Tesla in 1891.
- **Simplified:** A Tesla coil is an electrical machine invented by Nikola Tesla in 1891.
- **Degraded:** A Tesla coil is an electrical machine invented by Nikola Tesla in 1891.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 13

- **Target dimension:** `EXPL`
- **Automatic result:** `GOOD`
- **Pair:** `pair:en:88aa77ad66e9522c173f5366d31625f318be7f31b042f3e10f21abd21e9b33a5`
- **Original:** A nutcracker is a tool designed to open nuts by cracking their shells.
- **Simplified:** A nutcracker is a mechanical device for cracking nuts.Nutcrackers are often used for breaking any types of nuts, using the mechanism in the tool itself.
- **Degraded:** A nutcracker is a mechanical device for cracking nuts. Nutcrackers are often used for breaking any types of nuts, using the mechanism in the tool itself.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 14

- **Target dimension:** `FLUENCY`
- **Automatic result:** `FAILED`
- **Pair:** `pair:en:d9027bd1bdfd5441fe131de4e05dc8d3eb72d3d37a1f304a57ab22c56a04b86a`
- **Original:** Zoetermeer (] ) is a city in the western Netherlands, in the province of South Holland.
- **Simplified:** Zoetermeer is a city in South Holland in the Netherlands (it has no city rights).
- **Degraded:** Zoetermeer is a city in South Holland in the Netherlands (it has no city rights).

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 15

- **Target dimension:** `MOD`
- **Automatic result:** `GOOD`
- **Pair:** `pair:en:8391bc527645dc62051e4d2145a9e8988dbe3c6e7fc949afa118999b21a0b31c`
- **Original:** Mitchell Jay Feigenbaum (December 19, 1944 – June 30, 2019) was an American mathematical physicist whose pioneering studies in chaos theory led to the discovery of the Feigenbaum constants.
- **Simplified:** Mitchell Jay Feigenbaum (December 19, 1944 – June 30, 2019) was an American mathematical physicist.His studies in chaos theory led to the discovery of the Feigenbaum constants.Feigenbaum died on June 30, 2019 in New York City, at the age of 74.
- **Degraded:** Mitchell Jay Feigenbaum (December 19, 1944 – June 30, 2019) was an American mathematical physicist whose pioneering studies in chaos theory led to the discovery of the Feigenbaum constants. He died on June 30, 2019 in New York City, at the age of 74.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 16

- **Target dimension:** `FLUENCY`
- **Automatic result:** `MEDIUM`
- **Pair:** `pair:en:dfe5d0f7f9e66a1aaec0762b1dbdd534948fccaa817683c67e37dc1e6a23ab4d`
- **Original:** Independence from Bavaria was secured in the late 14th century.
- **Simplified:** Till th 14th century Salzburg became independent from Bavaria and was a state within the Holy Roman Empire.
- **Degraded:** Till the 14th century Salzburg became independent from Bavaria and was a state within the Holy Roman Empire.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 17

- **Target dimension:** `ILLOC`
- **Automatic result:** `FAILED`
- **Pair:** `pair:en:0f8332099f563f95c110476a357e5112e96777fa64fba63b9f450501409a6211`
- **Original:** Intelligibility between languages can be asymmetric, with speakers of one understanding more of the other than speakers of the other understanding the first.
- **Simplified:** When a speaker of one language can understand what a speaker of another language is saying but not the other way around, it is called asymmetric intelligibility.
- **Degraded:** When a speaker of one language can understand what a speaker of another language is saying but not the other way around, it is called asymmetric intelligibility.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 18

- **Target dimension:** `FLUENCY`
- **Automatic result:** `MEDIUM`
- **Pair:** `pair:en:4f75186ce9bc9cb4f57edf1b5ee8ed3d35be4396af445d9b5a42ca5fa47b220c`
- **Original:** The Shoku Nihongi (続日本紀 ) is an imperially commissioned Japanese history text.
- **Simplified:** Shoku Nihongi (続日本紀) is an ancient history of Japan written in 797.
- **Degraded:** Shoku 続日本紀 is an ancient history of Japan written in 797.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 19

- **Target dimension:** `OMIT`
- **Automatic result:** `GOOD`
- **Pair:** `pair:en:4c4d2b90964c429a2ddcf3a99ae0ec886d0aa9cd7beffacf94eb43db6fb24268`
- **Original:** He has played for Brazil national team in the 1934 FIFA World Cup.
- **Simplified:** He has played for Brazil national team.
- **Degraded:** He has played for Brazil national team in 1934.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 20

- **Target dimension:** `MOD`
- **Automatic result:** `GOOD`
- **Pair:** `pair:en:d5ba929bf123f3dd8375367bbe32d7ef4ff50b4dfb62a3fd94f3865778377265`
- **Original:** He was a pioneer in cochlear implants, and was the first person in the world to perform an eardrum transplant.
- **Simplified:** He was known for his work with cochlear implants.He was the first person in the world to perform an eardrum transplant.
- **Degraded:** He was a pioneer in cochlear implants. He was the first person in the world to perform an eardrum transplant.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 21

- **Target dimension:** `MOD`
- **Automatic result:** `MEDIUM`
- **Pair:** `pair:en:357e676a5a85d503934d51915ae798a038f3702677a0879ef6ec25ceb87728f3`
- **Original:** The Tri-State Tornado of Wednesday, March 18, 1925 was the deadliest tornado in United States history.
- **Simplified:** The Tri-State Tornado was the deadliest tornado in the history of the United States.It took place on Wednesday, March 18, 1925.
- **Degraded:** The Tri-State Tornado of Wednesday, March 18, 1925 was the deadliest tornado in the history of the United States.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 22

- **Target dimension:** `ILLOC`
- **Automatic result:** `MEDIUM`
- **Pair:** `pair:en:24d2c2ec898bc0b5235472b282a2f467043fd62a9cd74589d4e29ba726e8057d`
- **Original:** Human papillomavirus infection (HPV infection) is an infection by "human papillomavirus" (HPV).
- **Simplified:** The Human papillomavirus (HPV) is a virus that can infect the skin or mucous membranes (like the genitals, or inside the mouth) of humans.
- **Degraded:** The Human papillomavirus (HPV) can infect the skin or mucous membranes (like the genitals, or inside the mouth) of humans.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 23

- **Target dimension:** `OMIT`
- **Automatic result:** `GOOD`
- **Pair:** `pair:en:f18b996eb5c32cc726ced1a2d4e6b037c57bed4e2032bad7469a45b65c1dc42a`
- **Original:** The lion-tailed macaque ("Macaca silenus"), also known as the bruh, is an Old World monkey endemic to the Western Ghats of South India.
- **Simplified:** The lion-tailed macaque ("Macaca silenus") is an Old World monkey.
- **Degraded:** The lion-tailed macaque ('Macaca silenus') is an Old World monkey.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 24

- **Target dimension:** `FLUENCY`
- **Automatic result:** `MEDIUM`
- **Pair:** `pair:en:44118cbc6259530a0f46542e8934c93c5e4ec2cdaca570f9bd3bbb453a2e3465`
- **Original:** Chlorine dioxide is a chemical compound with the formula ClO.
- **Simplified:** Chlorine dioxide is a chemical compound (a thing made when two or more chemical elements attach to each other).Its chemical formula is ClO.
- **Degraded:** Chlorine dioxide is a chemical compound (a thing made when two or more chemical elements attach to each other). Its chemical formula is ClO.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 25

- **Target dimension:** `MOD`
- **Automatic result:** `MEDIUM`
- **Pair:** `pair:en:33fbaf5853179843e0582c559ebff78b4657e4e4dd035beeeebaa0d62114881d`
- **Original:** Huelva ( , ] ) is a city in southwestern Spain, the capital of the province of Huelva in the autonomous community of Andalusia.
- **Simplified:** Huelva is a city in Andalusia, Spain and the capital of the province of Huelva.
- **Degraded:** Huelva is a city in southwestern Spain, the capital of the province of Huelva in Andalusia.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 26

- **Target dimension:** `ILLOC`
- **Automatic result:** `GOOD`
- **Pair:** `pair:en:1cbfe91fe8f04b0b6209aa553ed434ac0b19a82e4afb532e6d35378503951847`
- **Original:** Broda was born in Brandon, Manitoba to a Ukrainian family.
- **Simplified:** He was born in Brandon, Manitoba on May 15, 1914 to a Polish-Canadian family.
- **Degraded:** Broda was born in Brandon, Manitoba to a Polish-Canadian family.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 27

- **Target dimension:** `FLUENCY`
- **Automatic result:** `GOOD`
- **Pair:** `pair:en:c6bb736741c5a8094140eb10cb5e5362c61edc89a635ca11071df6f127187f3c`
- **Original:** In 480 the Persians returned under a new ruler, Xerxes I.
- **Simplified:** In 480 BC the Persians arrived and attacked the Greeks, both on land and on sea.
- **Degraded:** In 480 BC the Persians arrived and attacked the Greeks, both on land and in sea.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 28

- **Target dimension:** `SYN`
- **Automatic result:** `FAILED`
- **Pair:** `pair:en:f0cae1c08e2684c1c021f0d8dfa6c1d062c1950f080e5d5d19281889285380e6`
- **Original:** Majority rule is a decision rule that selects alternatives which have a majority, that is, more than half the votes.
- **Simplified:** Majority rule is a way of making decisions in government or in voting.A decision is made if it gets more than half of the votes.
- **Degraded:** Majority rule is a way of making decisions in government or in voting.A decision is made if it gets more than half of the votes.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 29

- **Target dimension:** `EXPL`
- **Automatic result:** `MEDIUM`
- **Pair:** `pair:en:d62220d0200c9aad54da2b063ba85b3e31694f76ee588e45a43b0265c18f5888`
- **Original:** He has been in office since January 2017.
- **Simplified:** He is the President of Ghana, in office since January 2017.
- **Degraded:** He has been in office since January 2017.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 30

- **Target dimension:** `FLUENCY`
- **Automatic result:** `FAILED`
- **Pair:** `pair:en:ff6fe40c571aa8ca154fbdf3f403799ab3e39531ec25b640f7d90b33e31d9fab`
- **Original:** Human remains dating back more than 20,000 years have been found in limestone caves in the area.
- **Simplified:** Remains found in limestone caves show that humans have lived in the area for well over 20,000 years.
- **Degraded:** Remains found in limestone caves show that humans have lived in the area for well over 20,000 years.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 31

- **Target dimension:** `SYN`
- **Automatic result:** `GOOD`
- **Pair:** `pair:en:5806e04d39798b17c0fa90c3d105b4e8331b7ab90dd4e0b8eb35358a867cf965`
- **Original:** A facial composite is a graphical representation of one or more eyewitnesses' memory of a face, as recorded by a composite artist.
- **Simplified:** A facial composite is a reconstructed image of the face of a person.
- **Degraded:** A facial composite is a reconstructed image of one or more eyewitnesses' memory of a face, as recorded by a composite artist.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 32

- **Target dimension:** `ILLOC`
- **Automatic result:** `GOOD`
- **Pair:** `pair:en:3fee147422b920a8470b79b55cc8c4dba15fdf59bebb96b7ee7abd5efcdbd46b`
- **Original:** The parent not incubating will hunt for food or look for nesting material during this stage.
- **Simplified:** The other parent will hunt for food or look for more to add onto the nest.
- **Degraded:** The parent incubating will hunt for food or look for nesting material during this stage.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 33

- **Target dimension:** `SYN`
- **Automatic result:** `GOOD`
- **Pair:** `pair:en:a83d2cf070fd0534d79c10d566968809d3e9fb5f32ee4488aecec76cb7e6e465`
- **Original:** He began as a planter, then turned to innkeeping and finally to banking before the American Civil War.
- **Simplified:** He began his life as a farmer, then became an innkeeper and finally became a banker before the Civil War.
- **Degraded:** He began as a farmer, then became an innkeeper and finally became a banker before the Civil War.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 34

- **Target dimension:** `OMIT`
- **Automatic result:** `MEDIUM`
- **Pair:** `pair:en:955b9b1c851293a9fc21aff0ab37850c078788226badd7e0efc7f288f8a954f9`
- **Original:** Yūzō Tashiro (田代 有三 , Tashiro Yūzō , born July 22, 1982) is a Japanese football player who plays for Wollongong Wolves.
- **Simplified:** Yūzō Tashiro (田代 有三, Tashiro Yuzo, born July 22, 1982) is a Japanese football player.
- **Degraded:** Yūzō Tashiro (田代 有三, Tashiro Yuzo, born July 22, 1982) is a Japanese football player.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 35

- **Target dimension:** `FLUENCY`
- **Automatic result:** `FAILED`
- **Pair:** `pair:en:9c0217b23f56b092877f9e7e239186fd27e4ec11d01eecdced8a92d785577016`
- **Original:** Serj Tankian (] ; ; born August 21, 1967) is an American musician, singer, songwriter, multi-instrumentalist, record producer, poet and political activist.
- **Simplified:** Serj Tankian (born on August 21, 1967 in Beirut, Lebanon) is an Armenian-American musician who lives in Los Angeles.
- **Degraded:** Serj Tankian (born on August 21, 1967 in Beirut, Lebanon) is an Armenian-American musician who lives in Los Angeles.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 36

- **Target dimension:** `EXPL`
- **Automatic result:** `MEDIUM`
- **Pair:** `pair:en:40bd71312ad36059675a1f38805cac91e280a41a4c4719e1ff06bfc05c7715e9`
- **Original:** She died of an apparent heart attack on June 21, 2019.
- **Simplified:** Bernard died on June 21, 2019 in Los Angeles from a heart attack at the age of 71.
- **Degraded:** She died on June 21, 2019 from a heart attack at the age of 71.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 37

- **Target dimension:** `OMIT`
- **Automatic result:** `FAILED`
- **Pair:** `pair:en:b02caff4a7548e3e7e372df5efb07a9fca0274ea51f1b93f42e5b58b7b03a0ea`
- **Original:** In 1932, Democratic presidential nominee Franklin D. Roosevelt promised "a New Deal for the American people", coining the enduring label for his domestic policies.
- **Simplified:** In 1932, he was defeated and Franklin D. Roosevelt became President.
- **Degraded:** In 1932, he was defeated and Franklin D. Roosevelt became President.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 38

- **Target dimension:** `OMIT`
- **Automatic result:** `FAILED`
- **Pair:** `pair:en:20d70c35faa3366b15e8f22a76818905813bc4d7e4cbfa78e43f90477f4d49c6`
- **Original:** Born in White Plains, New York, Raimondo moved with his family to Yorktown Heights, New York when he was very young.
- **Simplified:** He was born in White Plains, New York.
- **Degraded:** He was born in White Plains, New York.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 39

- **Target dimension:** `EXPL`
- **Automatic result:** `FAILED`
- **Pair:** `pair:en:ab55f2b8231d7f6db5ca2c959f1c6daf9d39ebb2d817b33e05bb73fb078eb16e`
- **Original:** He died in the hospital on 4 September 2017 from kidney failure.
- **Simplified:** Moschin died of kidney failure on 4 September 2017 at his home in Terni, Italy at the age of 88.
- **Degraded:** Moschin died of kidney failure on 4 September 2017 at his home in Terni, Italy at the age of 88.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 40

- **Target dimension:** `EXPL`
- **Automatic result:** `GOOD`
- **Pair:** `pair:en:cb370eb11544adec2a8a29edd34777cde73800329d136965c09760d827d67625`
- **Original:** The River Fowey ( ; ) is a river in Cornwall, England, United Kingdom.
- **Simplified:** The River Fowey is a river in Cornwall, United Kingdom, which follows an irregular course across Bodmin Moor and enters the English Channel at Fowey.
- **Degraded:** The River Fowey is a river in Cornwall, United Kingdom, and enters the English Channel at Fowey.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 41

- **Target dimension:** `SYN`
- **Automatic result:** `FAILED`
- **Pair:** `pair:en:109e797d7667b830e5560403264cfe451a15ca9b8fa6df93c4556921a8bb3f30`
- **Original:** Montaque N. Brown (born April 13, 1970) is an American former professional wrestler and National Football League linebacker.
- **Simplified:** Monty Brown (born April 13, 1970) is a retired American professional wrestler and American football linebacker.
- **Degraded:** Monty Brown (born April 13, 1970) is a retired American professional wrestler and American football linebacker.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 42

- **Target dimension:** `OMIT`
- **Automatic result:** `FAILED`
- **Pair:** `pair:en:f22273c7216540f276400d18e46ed78aeb0637831d3b68f98d9b28ed0697f4e8`
- **Original:** Polly Jean Harvey (born 9 October 1969) is an English musician, singer-songwriter, writer, artist, poet and composer.
- **Simplified:** Polly Jean Harvey MBE (born 9 October 1969) is an English musician.
- **Degraded:** Polly Jean Harvey MBE (born 9 October 1969) is an English musician.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 43

- **Target dimension:** `MOD`
- **Automatic result:** `MEDIUM`
- **Pair:** `pair:en:fc8ef75c8762287489a76dc2c60f50fe414c16cb3009c0c71f9c3ea9497b4759`
- **Original:** The nectar attracts predatory insects which will eat both the nectar and any plant-eating insects around, thus functioning as 'bodyguards'.
- **Simplified:** These plants do it to attract predatory insects.These insects will eat both the nectar and any plant-eating insects found near the plant.
- **Degraded:** The nectar attracts predatory insects which will eat both the nectar and any plant-eating insects found near the plant, thus functioning as 'bodyguards'.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 44

- **Target dimension:** `SYN`
- **Automatic result:** `MEDIUM`
- **Pair:** `pair:en:9611452e0ad0286fd3b88bf2a4161c63d255519e84a1ae4c0ce60eae0fcc5816`
- **Original:** In 1995 he joined the BNP and in 1999 became its leader.
- **Simplified:** In 1995, he joined the British National Party and in 1999 he became its leader.
- **Degraded:** In 1995 he joined the BNP and in 1999 became its leader.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 45

- **Target dimension:** `OMIT`
- **Automatic result:** `GOOD`
- **Pair:** `pair:en:7f4c28eda9eb213d651239e8f9fe65604aad3330dfbee2137a6ab83eecc29c38`
- **Original:** Pino Daniele (19 March 1955 – 4 January 2015) was an Italian singer-songwriter, and guitarist, whose influences covered a wide number of genres, including pop, blues, jazz, and Italian and Middle Eastern music.
- **Simplified:** Pino Daniele (19 March 1955 – 4 January 2015) was an Italian singer-songwriter, and guitarist.
- **Degraded:** Pino Daniele (19 March 1955 – 4 January 2015) was an Italian singer-songwriter, and guitarist, whose influences covered a wide number of genres.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 46

- **Target dimension:** `ILLOC`
- **Automatic result:** `MEDIUM`
- **Pair:** `pair:en:b5daebb1146cf52a33bf9f14c83d8fbed032bc65e9ead4e838da3da6a4bd204b`
- **Original:** Thomas Taylor Hammond (born May 10, 1944) is an American sportscaster for NBC Sports.
- **Simplified:** Tom Hammond (born May 10, 1944 in Lexington, Kentucky) is a sportscaster who works for NBC Sports along with Dan Hicks and Bob Costas.
- **Degraded:** Will Tom Hammond (born May 10, 1944 in Lexington, Kentucky) be working for NBC Sports along with Dan Hicks and Bob Costas?

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 47

- **Target dimension:** `SYN`
- **Automatic result:** `MEDIUM`
- **Pair:** `pair:en:8793c901806cbebeae19f7558d83088bfb7dda07f7a0db2978d9a98dd9ef6440`
- **Original:** Mollie Sugden (21 July 19221 July 2009) was an English comedy actress, best known for portraying the saleswoman Mrs Slocombe in the British sitcom "Are You Being Served?"
- **Simplified:** Mary Isobel 'Mollie' Sugden (21 July 1922 – 1 July 2009) was an English comedy actress best known for playing saleswoman Mrs. Slocombe in the popular British sitcom "Are You Being Served?"
- **Degraded:** Mary Isobel 'Mollie' Sugden (21 July 1922 – 1 July 2009) was an English comedy actress best known for playing saleswoman Mrs. Slocombe in the popular British sitcom 'Are You Being Served?'

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 48

- **Target dimension:** `EXPL`
- **Automatic result:** `MEDIUM`
- **Pair:** `pair:en:10a92aefbc40acc032eb7c25d3e0c7e4302131040aa231cb97b4c5afc9b3c5e2`
- **Original:** Bernstein was born in New York City in 1918 and was adopted by a Russian Jewish family.
- **Simplified:** Bernstein was born in New York City, New York on August 12, 1918.
- **Degraded:** Bernstein was born in New York City in 1918 and was adopted by a Russian Jewish family.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 49

- **Target dimension:** `ILLOC`
- **Automatic result:** `MEDIUM`
- **Pair:** `pair:en:491722c806785e4547487d2551a2c15218acd86d6e561416940f3d394053b8de`
- **Original:** It can most specifically mean the first five books (Pentateuch or five books of Moses) of the 24 books of the Tanakh (Hebrew Bible).
- **Simplified:** When most people say the word Torah they either mean the whole Jewish Bible, the Tanakh, the first five books of the Bible, or all of the Jewish teaching in general.Other names for this set of books are the "Five Books of Moses," or "Pentateuch".Pentateuch means the first five books of the Bible.
- **Degraded:** It can most specifically mean the first five books (Pentateuch or five books of Moses) of the 24 books of the Tanakh (Hebrew Bible).

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**

### Case 50

- **Target dimension:** `MOD`
- **Automatic result:** `GOOD`
- **Pair:** `pair:en:c13272f6947bd9888e39d198aa7f6a0b76c184735ec72697d855e8532cf029f3`
- **Original:** It is one of three known paintings of Delft by Vermeer, along with "The Little Street" and the lost painting "House Standing in Delft".
- **Simplified:** It is one of three paintings of Delft by Vermeer.The others are "The Little Street" and the lost painting "House Standing in Delft".
- **Degraded:** It is one of three known paintings of Delft by Vermeer. The others are 'The Little Street' and the lost painting 'House Standing in Delft'.

- [ ] Valid
- [ ] Invalid
- [ ] Unsure
- **Note:**
