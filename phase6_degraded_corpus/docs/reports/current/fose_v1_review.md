# FOSE v1 blinded human review

Mark exactly one box per case. **Unsure counts as valid.** Valid means the stated rule was applied correctly and the Degraded text is clearly a worse simplification on that axis, with everything else unchanged.

### Case F001

* **Axis:** `SYN`
* **Required change and validity criterion:** Restore one harder Original word or phrase with the same meaning as the simple wording.
* **Source:** WikiAutoEN
* **Original:** Radiology is the medical specialty that uses medical imaging to diagnose and treat diseases within the bodies of both humans and animals.
* **Simplified:** Radiology is a field of medicine that uses medical imaging methods to detect and treat diseases.
* **Degraded:** Radiology is a field of medicine that uses medical imaging methods to diagnose and treat diseases.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** "diagnose" from the Original correctly restores a more complex/specialized term in place of "detect".

### Case F002

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** ASSET
* **Original:** The Miss USA beauty contest has been held annually since 1952 to select the United States entrant in the Miss Universe pageant.
* **Simplified:** Miss USA is a yearly beauty contest that started in 1952. The winner enters the Miss Universe pageant.
* **Degraded:** Miss USA is a yearly beauty contest that started in 1952. winner enters the Miss Universe pageant.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Dropping the article ("winner enters") introduces an obvious local grammatical error while preserving meaning.

### Case F003

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** ASSET
* **Original:** About 2,000 to 3,000 cocoons are required to make a pound of silk.
* **Simplified:** 2,000 to 3,000 cocoons make a pound of silk.
* **Degraded:** 2,000 to 3,000 cocoons make a pound for silk.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Changing preposition "of" to "for" creates a local grammatical error while preserving meaning.

### Case F004

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** ASSET
* **Original:** These flies are clothed in black or pale (white or golden) hairs, and are themselves either black or metallic green or blue.
* **Simplified:** The flies are clothed in black or pale colored hairs. They are either black, metallic green, or metallic blue.
* **Degraded:** The flies are clothed on black or pale colored hairs. They are either black, metallic green, or metallic blue.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Incorrect preposition "clothed on" instead of "clothed in".

### Case F005

* **Axis:** `SYN`
* **Required change and validity criterion:** Restore one harder Original word or phrase with the same meaning as the simple wording.
* **Source:** WikiAutoEN
* **Original:** The margin of error is a statistic expressing the amount of random sampling error in a survey's results.
* **Simplified:** The margin of error is a way to measure the sampling error in the results of a statistical survey.
* **Degraded:** The margin of error is a statistic expressing the sampling error in the results of a statistical survey.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores the harder phrase "a statistic expressing" from the Original over the simpler "a way to measure".

### Case F006

* **Axis:** `OMIT`
* **Required change and validity criterion:** Restore one detail that was usefully omitted; it must be unnecessary or too hard for the target reader.
* **Source:** WikiAutoEN
* **Original:** Robert Sacre (born June 6, 1989) is a former professional basketball player who last played for the Sun Rockers Shibuya of the Japanese B.League.
* **Simplified:** Robert Sacre (born June 6, 1989) is an American-Canadian basketball player.
* **Degraded:** Robert Sacre (born June 6, 1989) is an American-Canadian basketball player who last played for the Sun Rockers Shibuya of the Japanese B.
* [ ] Valid
* [x] Invalid
* [ ] Unsure
* **Note:** Truncated/corrupted restoration ("Japanese B." instead of "Japanese B.League"), introducing a fluency/broken text defect rather than a clean restoration of omitted information.

### Case F007

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** ASSET
* **Original:** Most owners of zombie computers are unaware that their system is being used in this way.
* **Simplified:** Most owners of zombie computers are not aware that their computer has a virus or has been hacked in some way.
* **Degraded:** Most owners of zombie computers are not aware that their computer have a virus or has been hacked in some way.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Subject-verb agreement error ("their computer have").

### Case F008

* **Axis:** `SYN`
* **Required change and validity criterion:** Restore one harder Original word or phrase with the same meaning as the simple wording.
* **Source:** WikiAutoEN
* **Original:** The Dutch tried on several occasions to act as an intermediary to reach a negotiated peace settlement between the Entente and Germany.
* **Simplified:** The Dutch tried to organize a peace settlement between the Allies and Germany.
* **Degraded:** The Dutch tried to organize a peace settlement between the Entente and Germany.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores historical/low-frequency term "Entente" in place of "Allies".

### Case F009

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** WikiAutoEN
* **Original:** Maureen Reillette "Rebbie" Jackson-Brown ( ; born May 29, 1950) is an American singer.
* **Simplified:** Maureen Reillette "Rebbie" Jackson (born May 29, 1950 in Gary, Indiana) is an American singer.
* **Degraded:** Maureen Reillette " Rebbie " Jackson (born May 29, 1950 on Gary, Indiana) is an American singer.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Preposition error ("on Gary, Indiana" instead of "in").

### Case F010

* **Axis:** `SYN`
* **Required change and validity criterion:** Restore one harder Original word or phrase with the same meaning as the simple wording.
* **Source:** ASSET
* **Original:** Extinction Non-avian dinosaurs suddenly became extinct approximately 65 million years ago.
* **Simplified:** Flightless dinosaurs suddenly died out around 65 million years ago.
* **Degraded:** Flightless dinosaurs suddenly became extinct approximately 65 million years ago.
* [ ] Valid
* [x] Invalid
* [ ] Unsure
* **Note:** Restores two separate phrases ("became extinct" and "approximately") instead of "one harder Original word or phrase".

### Case F011

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** WikiAutoEN
* **Original:** Yusuke Tasaka (田坂 祐介 , Tasaka Yusuke , born 8 July 1985 in Hiroshima, Hiroshima) is a Japanese football midfielder.
* **Simplified:** Yusuke Tasaka (born 8 July 1985) is a Japanese football player.
* **Degraded:** Yusuke Tasaka (born 8 July 1985) are a Japanese football player.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Clear subject-verb agreement error ("are").

### Case F012

* **Axis:** `SYN`
* **Required change and validity criterion:** Restore one harder Original word or phrase with the same meaning as the simple wording.
* **Source:** WikiAutoEN
* **Original:** The soft parts of the animal occupied the cavity between the two shells, just like modern oysters.
* **Simplified:** The soft parts of the animal lived in the gap between the two shells, just like modern oysters.
* **Degraded:** The soft parts of the animal occupied the gap between the two shells, just like modern oysters.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores harder verb "occupied" in place of "lived in".

### Case F013

* **Axis:** `SYN`
* **Required change and validity criterion:** Restore one harder Original word or phrase with the same meaning as the simple wording.
* **Source:** WikiAutoEN
* **Original:** This gives time for the projectile to penetrate the target before the explosive warhead detonates.
* **Simplified:** This gives time for the darts to get inside the target before the explosives go off.
* **Degraded:** This gives time for the darts to penetrate the target before the explosives go off.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores "penetrate" in place of "get inside".

### Case F014

* **Axis:** `EXPL`
* **Required change and validity criterion:** Remove one explanation or definition that genuinely helped understanding, changing nothing else.
* **Source:** WikiAutoEN
* **Original:** During World War II, Nawrocka-Dońska was a soldier of the Home Army and took part in the Warsaw Uprising.
* **Simplified:** She served as a soldier of the Home Army and took part in the Warsaw Uprising as a nurse during World War II.
* **Degraded:** She served as a soldier of the Home Army and took part in the Warsaw Uprising.
* [ ] Valid
* [x] Invalid
* [ ] Unsure
* **Note:** The phrase "as a nurse during World War II" is not an explanation or definition of an unfamiliar term/concept; it is biographical background fact, and its removal also drops the time setting ("during World War II").

### Case F015

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** WikiAutoEN
* **Original:** Most food has always been obtained through agriculture.
* **Simplified:** Food for humans is mostly made through farming or gardening.
* **Degraded:** Food of humans is mostly made through farming or gardening.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Unnatural/erroneous preposition choice ("Food of humans").

### Case F016

* **Axis:** `SYN`
* **Required change and validity criterion:** Restore one harder Original word or phrase with the same meaning as the simple wording.
* **Source:** WikiAutoEN
* **Original:** A guild is an association of artisans or merchants who oversee the practice of their craft/trade in a particular area.
* **Simplified:** A guild is an association of craftspeople or merchants who control the practice of their craft in a town.
* **Degraded:** A guild is an association of craftspeople or merchants who oversee the practice of their craft in a town.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores "oversee" in place of "control".

### Case F017

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** WikiAutoEN
* **Original:** Taunton is a large town in Somerset, England.
* **Simplified:** Taunton is a town in the county of Somerset. Taunton is the county town of Somerset. "Tone town" became Taunton.
* **Degraded:** Taunton are a town in the county of Somerset. Taunton is the county town of Somerset. " Tone town " became Taunton.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Clear subject-verb agreement error ("Taunton are a town").

### Case F018

* **Axis:** `EXPL`
* **Required change and validity criterion:** Remove one explanation or definition that genuinely helped understanding, changing nothing else.
* **Source:** WikiAutoEN
* **Original:** After World War I, Hitler returned to Munich.
* **Simplified:** After World War I, Hitler stayed in the army and returned to Munich.
* **Degraded:** After World War I, Hitler returned to Munich.
* [ ] Valid
* [x] Invalid
* [ ] Unsure
* **Note:** "stayed in the army" is an added biographical historical fact, not an explanatory gloss or definition of a concept.

### Case F019

* **Axis:** `OMIT`
* **Required change and validity criterion:** Restore one detail that was usefully omitted; it must be unnecessary or too hard for the target reader.
* **Source:** WikiAutoEN
* **Original:** Desmond Herbert Carrington (23 May 1926 – 1 February 2017) was a British actor and broadcaster whose career spanned over 70 years.
* **Simplified:** Desmond Herbert Carrington (23 May 1926 – 1 February 2017) was a British actor and broadcaster.
* **Degraded:** Desmond Herbert Carrington (23 May 1926 – 1 February 2017) was a British actor and broadcaster whose career spanned over 70 years.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores the non-essential relative clause detail from the Original.

### Case F020

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** ASSET
* **Original:** The Shaolin Monastery or Shaolin Temple, is a Chán Buddhist temple at Song Shan near Zhengzhou City Henan Province in Dengfeng, China.
* **Simplified:** The Shaolin Monastery is in China. It is a Buddhist temple.
* **Degraded:** The Shaolin Monastery is on China. It is a Buddhist temple.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Preposition error ("on China" instead of "in China").

### Case F021

* **Axis:** `EXPL`
* **Required change and validity criterion:** Remove one explanation or definition that genuinely helped understanding, changing nothing else.
* **Source:** WikiAutoEN
* **Original:** Richard Dominguez was born Eufrancio Ricardo Dominguez to Ricardo and Juanita Dominguez in Dallas, Texas on September 22, 1960.
* **Simplified:** Richard Dominguez was born in Dallas, Texas on September 22, 1960 as the second of seven children.
* **Degraded:** Richard Dominguez was born in Dallas, Texas on September 22, 1960.
* [ ] Valid
* [x] Invalid
* [ ] Unsure
* **Note:** "as the second of seven children" is incidental biographical information, not an explanation or definition.

### Case F022

* **Axis:** `SYN`
* **Required change and validity criterion:** Restore one harder Original word or phrase with the same meaning as the simple wording.
* **Source:** WikiAutoEN
* **Original:** Ringed seals occur throughout the Arctic Ocean.
* **Simplified:** Ringed seals live throughout the Arctic Ocean.
* **Degraded:** Ringed seals occur throughout the Arctic Ocean.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores formal/scientific "occur" in place of simpler "live".

### Case F023

* **Axis:** `SYN`
* **Required change and validity criterion:** Restore one harder Original word or phrase with the same meaning as the simple wording.
* **Source:** ASSET
* **Original:** It has a black bill, crimson eyes, and a call reminiscent of a dog's bark.
* **Simplified:** It has a black bill, dark red eyes, and a call like a dog's bark.
* **Degraded:** It has a black bill, crimson eyes, and a call like a dog's bark.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores lower-frequency color descriptor "crimson" in place of "dark red".

### Case F024

* **Axis:** `EXPL`
* **Required change and validity criterion:** Remove one explanation or definition that genuinely helped understanding, changing nothing else.
* **Source:** WikiAutoEN
* **Original:** The megamouth shark ("Megachasma pelagios") is a species of deepwater shark.
* **Simplified:** The megamouth shark ("Megachasma pelagios") is a large, slow-swimming, timid shark that was only discovered in 1976.
* **Degraded:** The megamouth shark (" Megachasma pelagios ") is a large, slow-swimming, timid shark.
* [ ] Valid
* [x] Invalid
* [ ] Unsure
* **Note:** "that was only discovered in 1976" is historical trivia/fact, not an explanation or definition.

### Case F025

* **Axis:** `SYN`
* **Required change and validity criterion:** Restore one harder Original word or phrase with the same meaning as the simple wording.
* **Source:** WikiAutoEN
* **Original:** It stars Joey Cramer as David Freeman, a 12-year-old boy who is abducted by an alien spaceship and finds himself caught in a world that has changed around him.
* **Simplified:** It is about David Freeman, a 12-year-old boy who is taken by an alien spaceship and finds himself caught in a world that has changed around him.
* **Degraded:** It is about David Freeman, a 12-year-old boy who is abducted by an alien spaceship and finds himself caught in a world that has changed around him.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores harder word "abducted" in place of "taken".

### Case F026

* **Axis:** `OMIT`
* **Required change and validity criterion:** Restore one detail that was usefully omitted; it must be unnecessary or too hard for the target reader.
* **Source:** WikiAutoEN
* **Original:** Diane Carol Baker (born February 25, 1938) is an American actress, producer and educator who has appeared in motion pictures and on television since 1959.
* **Simplified:** Diane Carol Baker (born February 25, 1938) is an American actress, producer and educator.
* **Degraded:** Diane Carol Baker (born February 25, 1938) is an American actress, producer and educator who has appeared in motion pictures and on television since 1959.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores the non-essential relative clause detail from the Original.

### Case F027

* **Axis:** `EXPL`
* **Required change and validity criterion:** Remove one explanation or definition that genuinely helped understanding, changing nothing else.
* **Source:** WikiAutoEN
* **Original:** Osceola County is a county located in the U.S. state of Florida.
* **Simplified:** Osceola County is a county in the U.S. state of Florida, and was formed on May 8, 1917.
* **Degraded:** Osceola County is a county in the U. S. state of Florida.
* [ ] Valid
* [x] Invalid
* [ ] Unsure
* **Note:** Date of formation ("and was formed on May 8, 1917") is historical detail, not an explanation or definition aiding comprehension of what a county is.

### Case F028

* **Axis:** `SYN`
* **Required change and validity criterion:** Restore one harder Original word or phrase with the same meaning as the simple wording.
* **Source:** WikiAutoEN
* **Original:** He made his debut as a professional actor at the age of 79.
* **Simplified:** His career as a professional actor started at the age of 79.
* **Degraded:** His debut as a professional actor started at the age of 79.
* [ ] Valid
* [x] Invalid
* [ ] Unsure
* **Note:** "His debut ... started" is a semantic mismatch / unnatural phrasing, altering the grammar/collocation rather than cleanly restoring a synonym with the same meaning.

### Case F029

* **Axis:** `OMIT`
* **Required change and validity criterion:** Restore one detail that was usefully omitted; it must be unnecessary or too hard for the target reader.
* **Source:** WikiAutoEN
* **Original:** Richard Bakalyan (January 29, 1931 – February 27, 2015) was an Armenian American character actor who started his career playing juvenile delinquents in his first several films.
* **Simplified:** Richard Bakalyan (January 29, 1931 – February 27, 2015) was an American character actor.
* **Degraded:** Richard Bakalyan (January 29, 1931 – February 27, 2015) was an Armenian American character actor.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores specific ethnic heritage detail "Armenian" that had been simplified/omitted.

### Case F030

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** WikiAutoEN
* **Original:** "No Tears Left to Cry" (stylized in all lowercase) is a song by American singer Ariana Grande from her fourth studio album, "Sweetener" (2018).
* **Simplified:** "No Tears Left to Cry" is a song by American singer Ariana Grande from her fourth studio album, "Sweetener".
* **Degraded:** " No Tears Left to Cry " is song by American singer Ariana Grande from her fourth studio album, " Sweetener ".
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Missing indefinite article ("is song").

### Case F031

* **Axis:** `OMIT`
* **Required change and validity criterion:** Restore one detail that was usefully omitted; it must be unnecessary or too hard for the target reader.
* **Source:** WikiAutoEN
* **Original:** On September 19, a westward moving tropical wave became a tropical depression about 900 mi east of the southwestern-most islands of Cape Verde.
* **Simplified:** On September 19, a tropical wave became a tropical depression in the Atlantic Ocean.
* **Degraded:** On September 19, a westward moving tropical wave became a tropical depression in the Atlantic Ocean.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores modifier "westward moving", adding unnecessary directional complexity back in.

### Case F032

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** ASSET
* **Original:** Religion The religion of Teotihuacan is similar to those of other Mesoamerican cultures.
* **Simplified:** Teotihuacan is like other Mesoamerican religions.
* **Degraded:** Teotihuacan are like other Mesoamerican religions.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Subject-verb agreement error ("Teotihuacan are").

### Case F033

* **Axis:** `EXPL`
* **Required change and validity criterion:** Remove one explanation or definition that genuinely helped understanding, changing nothing else.
* **Source:** WikiAutoEN
* **Original:** He is the son of Yoko Ono and John Lennon.
* **Simplified:** He is the son of John Lennon and his second wife Yoko Ono.
* **Degraded:** He is the son of Yoko Ono.
* [ ] Valid
* [x] Invalid
* [ ] Unsure
* **Note:** Omits John Lennon completely, causing severe loss of core factual information rather than removing an explanatory elaboration.

### Case F034

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** WikiAutoEN
* **Original:** John Warnock Hinckley Jr. (born May 29, 1955) is an American man who, on March 30, 1981, attempted to assassinate U.S. President Ronald Reagan in Washington, D.C.
* **Simplified:** John Warnock Hinckley, Jr. (born May 29, 1955) is the man who attempted to assassinate President Ronald Reagan.
* **Degraded:** John Warnock Hinckley, Jr. (born May 29, 1955) is man who attempted to assassinate President Ronald Reagan.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Missing article ("is man who").

### Case F035

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** WikiAutoEN
* **Original:** Norman Eugene "Clint" Walker (May 30, 1927 – May 21, 2018) was an American actor and singer.
* **Simplified:** Clint Walker (born Norman Eugene Walker; May 30, 1927 – May 21, 2018) was an American actor.
* **Degraded:** Clint Walker (born Norman Eugene Walker; May 30, 1927 – May 21, 2018) were an American actor.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Agreement error ("were an American actor").

### Case F036

* **Axis:** `EXPL`
* **Required change and validity criterion:** Remove one explanation or definition that genuinely helped understanding, changing nothing else.
* **Source:** WikiAutoEN
* **Original:** Lauren Michael Holly (born October 28, 1963) is an American actress.
* **Simplified:** Lauren Holly (born October 28, 1963, Bristol, Pennsylvania) is an American television and movie actress.
* **Degraded:** Lauren Holly (born October 28, 1963, Bristol, Pennsylvania) is an American actress.
* [ ] Valid
* [x] Invalid
* [ ] Unsure
* **Note:** "television and movie" specifies medium/scope, not an explanation or definition of the concept of an actress.

### Case F037

* **Axis:** `EXPL`
* **Required change and validity criterion:** Remove one explanation or definition that genuinely helped understanding, changing nothing else.
* **Source:** WikiAutoEN
* **Original:** Seneca was born in Córdoba in Hispania, and raised in Rome, where he was trained in rhetoric and philosophy.
* **Simplified:** He was born about 4 BC in Córdoba in Hispania (which is now in Spain).
* **Degraded:** He was born in Co ́ rdoba in Hispania (which is now in Spain).
* [ ] Valid
* [x] Invalid
* [ ] Unsure
* **Note:** Removes the birth date ("about 4 BC") while leaving the explanatory parenthetical "(which is now in Spain)"; thus it removed factual information instead of the explanation.

### Case F038

* **Axis:** `OMIT`
* **Required change and validity criterion:** Restore one detail that was usefully omitted; it must be unnecessary or too hard for the target reader.
* **Source:** WikiAutoEN
* **Original:** Maggie Blye (October 24, 1942 – March 24, 2016) was an American actress, also sometimes billed as Margaret Blye.
* **Simplified:** Maggie Blye (October 24, 1942 – March 24, 2016) was an American actress.
* **Degraded:** Maggie Blye (October 24, 1942 – March 24, 2016) was an American actress, also sometimes billed as Margaret Blye.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores an unnecessary alternative billing detail.

### Case F039

* **Axis:** `OMIT`
* **Required change and validity criterion:** Restore one detail that was usefully omitted; it must be unnecessary or too hard for the target reader.
* **Source:** WikiAutoEN
* **Original:** Thomas Garrett Cavanagh (March 24, 1982 – January 6, 2011) was an American professional ice hockey center who most recently played with the Springfield Falcons of the American Hockey League.
* **Simplified:** Thomas Garrett Cavanagh (March 24, 1982 – January 6, 2011) was an American professional ice hockey center.
* **Degraded:** Thomas Garrett Cavanagh (March 24, 1982 – January 6, 2011) was an American professional ice hockey center who most recently played with the Springfield Falcons of the American Hockey League.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores long, non-essential minor league detail.

### Case F040

* **Axis:** `EXPL`
* **Required change and validity criterion:** Remove one explanation or definition that genuinely helped understanding, changing nothing else.
* **Source:** WikiAutoEN
* **Original:** Mang died of a heart attack at his gym in Bellenberg, Germany on 12 March 2018.
* **Simplified:** Mang died in Berlin on 12 March 2018 of a heart attack at the age of 67.
* **Degraded:** Mang died of a heart attack at the age of 67.
* [ ] Valid
* [x] Invalid
* [ ] Unsure
* **Note:** Drops date and place of death ("in Berlin on 12 March 2018"), which are core factual details, not an explanation or definition.

### Case F041

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** ASSET
* **Original:** A hunting dog refers to any dog who assists humans in hunting.
* **Simplified:** Any dog who helps humans hunt is considered a hunting dog.
* **Degraded:** Any dog who helps humans hunt is considered hunting dog.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Missing article ("considered hunting dog").

### Case F042

* **Axis:** `SYN`
* **Required change and validity criterion:** Restore one harder Original word or phrase with the same meaning as the simple wording.
* **Source:** ASSET
* **Original:** There are numerous legends about the origins of boxing in Greece.
* **Simplified:** There are many stories about how boxing began in Greece.
* **Degraded:** There are numerous legends about how boxing began in Greece.
* [ ] Valid
* [x] Invalid
* [ ] Unsure
* **Note:** Restores two words ("numerous legends") simultaneously, violating the criterion of restoring *one* harder word or phrase while keeping the rest unchanged.

### Case F043

* **Axis:** `OMIT`
* **Required change and validity criterion:** Restore one detail that was usefully omitted; it must be unnecessary or too hard for the target reader.
* **Source:** WikiAutoEN
* **Original:** Bondevik was born in Sauda, Norway on 20 June 1941.
* **Simplified:** He was born in Sauda, Norway.
* **Degraded:** He was born in Sauda, Norway on 20 June 1941.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores specific birth date detail.

### Case F044

* **Axis:** `OMIT`
* **Required change and validity criterion:** Restore one detail that was usefully omitted; it must be unnecessary or too hard for the target reader.
* **Source:** ASSET
* **Original:** The Temple of Jupiter, Capitolium, or Temple of the Capitoline Triad was a temple in Roman Pompeii, at the north end of its forum.
* **Simplified:** The Temple of Jupiter, Capitolium, or Temple of the Capitoline Triad was a temple in Roman Pompeii.
* **Degraded:** The Temple of Jupiter, Capitolium, or Temple of the Capitoline Triad was a temple in Roman Pompeii, at the north end of its forum.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores the specific geographic location clause within the forum.

### Case F045

* **Axis:** `OMIT`
* **Required change and validity criterion:** Restore one detail that was usefully omitted; it must be unnecessary or too hard for the target reader.
* **Source:** WikiAutoEN
* **Original:** Nitrogenous waste is probably excreted through the body wall, as part of respiration, and the protonephridia are believed to function mainly in osmoregulation.
* **Simplified:** Nitrogenous waste is probably excreted through the body wall, as part of respiration.
* **Degraded:** Nitrogenous waste is probably excreted through the body wall, as part of respiration, and the protonephridia are believed to function mainly in osmoregulation.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores highly technical second clause ("protonephridia... osmoregulation") that was appropriately omitted.

### Case F046

* **Axis:** `SYN`
* **Required change and validity criterion:** Restore one harder Original word or phrase with the same meaning as the simple wording.
* **Source:** ASSET
* **Original:** It is often responsible for adverse weather throughout the world.
* **Simplified:** It is often the reason for bad weather around the world.
* **Degraded:** It is often the reason for adverse weather around the world.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores harder vocabulary word "adverse" in place of "bad".

### Case F047

* **Axis:** `OMIT`
* **Required change and validity criterion:** Restore one detail that was usefully omitted; it must be unnecessary or too hard for the target reader.
* **Source:** WikiAutoEN
* **Original:** Nancy Maryanne Dow (July 22, 1936 – May 25, 2016) was an American actress and model who appeared in a small group of films and television shows.
* **Simplified:** Nancy Maryanne Dow (July 22, 1936 – May 25, 2016) was an American actress and model.
* **Degraded:** Nancy Maryanne Dow (July 22, 1936 – May 25, 2016) was an American actress and model who appeared in a small group of films and television shows.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores non-essential qualifying relative clause.

### Case F048

* **Axis:** `SYN`
* **Required change and validity criterion:** Restore one harder Original word or phrase with the same meaning as the simple wording.
* **Source:** WikiAutoEN
* **Original:** There are several varieties of the diet.
* **Simplified:** There are many types of the diet.
* **Degraded:** There are several varieties of the diet.
* [ ] Valid
* [x] Invalid
* [ ] Unsure
* **Note:** Restores two words ("several" and "varieties") instead of a single word/phrase.

### Case F049

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** ASSET
* **Original:** He was the son of the Reverend Martin Luther King, Sr. and Alberta Williams King.
* **Simplified:** He was the son of the Reverend Martin Luther King, Sr. His mother was Alberta Williams King.
* **Degraded:** He were the son of the Reverend Martin Luther King, Sr. His mother was Alberta Williams King.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Subject-verb agreement error ("He were").

### Case F050

* **Axis:** `OMIT`
* **Required change and validity criterion:** Restore one detail that was usefully omitted; it must be unnecessary or too hard for the target reader.
* **Source:** ASSET
* **Original:** Pontedera is an Italian industrial town in Tuscany, Italy, in the administrative province of Pisa.
* **Simplified:** Pontedera is a town in Tuscany, Italy.
* **Degraded:** Pontedera is a town in Tuscany, Italy, in the administrative province of Pisa.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores unnecessary administrative detail.

### Case F051

* **Axis:** `SYN`
* **Required change and validity criterion:** Restore one harder Original word or phrase with the same meaning as the simple wording.
* **Source:** WikiAutoEN
* **Original:** The Chinchorro mummies are mummified remains of individuals from the South American Chinchorro culture, found in what is now northern Chile.
* **Simplified:** The Chinchorro mummies are mummified remains of people from the South American Chinchorro culture, found in what is now northern Chile and southern Peru.
* **Degraded:** The Chinchorro mummies are mummified remains of individuals from the South American Chinchorro culture, found in what is now northern Chile and southern Peru.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores "individuals" in place of "people".

### Case F052

* **Axis:** `SYN`
* **Required change and validity criterion:** Restore one harder Original word or phrase with the same meaning as the simple wording.
* **Source:** WikiAutoEN
* **Original:** Water droplets in clouds coalesce around the particles.
* **Simplified:** Water droplets in clouds fuse around the pollutants.
* **Degraded:** Water droplets in clouds coalesce around the pollutants.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores low-frequency scientific verb "coalesce" in place of "fuse".

### Case F053

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** ASSET
* **Original:** He traveled over 200,000 miles, an incredible achievement for pre-aviation times.
* **Simplified:** He traveled over 200,000 miles. It was an achievement for those times.
* **Degraded:** He traveled over 200,000 miles. It were an achievement for those times.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Subject-verb agreement error ("It were").

### Case F054

* **Axis:** `OMIT`
* **Required change and validity criterion:** Restore one detail that was usefully omitted; it must be unnecessary or too hard for the target reader.
* **Source:** WikiAutoEN
* **Original:** Brandon Hardesty was born in Baltimore, Maryland, the youngest child in the family.
* **Simplified:** He was born in Baltimore, Maryland.
* **Degraded:** He was born in Baltimore, Maryland, the youngest child in the family.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores non-essential appositive phrase detailing family birth order.

### Case F055

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** ASSET
* **Original:** The National Party, promoting a policy of "change", won 45% of the party vote and 59 of the 122 seats in Parliament (two seat overhang), a substantial margin over the Labour Party which won 43 seats.
* **Simplified:** The National Party won 59 seats in Parliament. The Labour Party only won 43 seats.
* **Degraded:** The National Party won 59 seats on Parliament. The Labour Party only won 43 seats.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Incorrect preposition ("on Parliament").

### Case F056

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** WikiAutoEN
* **Original:** PostScript is a Turing-complete programming language, belonging to the concatenative group.
* **Simplified:** Postscript is a programming language.
* **Degraded:** Postscript is programming language.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Missing singular count noun article ("is programming language").

### Case F057

* **Axis:** `OMIT`
* **Required change and validity criterion:** Restore one detail that was usefully omitted; it must be unnecessary or too hard for the target reader.
* **Source:** WikiAutoEN
* **Original:** Levente Lengyel (13 June 1933 – 18 August 2014) was a Hungarian chess player, who gained the Grandmaster title in 1964.
* **Simplified:** Levente Lengyel (13 June 1933 – 18 August 2014) was a Hungarian chess player.
* **Degraded:** Levente Lengyel (13 June 1933 – 18 August 2014) was a Hungarian chess player, who gained the Grandmaster title in 1964.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores specific non-essential relative clause.

### Case F058

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** WikiAutoEN
* **Original:** The River Thames , known alternatively in parts as the Isis, is a river that flows through southern England including London.
* **Simplified:** The River Thames is a large river in England.
* **Degraded:** The River Thames are a large river in England.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Subject-verb agreement error ("River Thames are").

### Case F059

* **Axis:** `SYN`
* **Required change and validity criterion:** Restore one harder Original word or phrase with the same meaning as the simple wording.
* **Source:** ASSET
* **Original:** The organic matter in soil derives from plants and animals.
* **Simplified:** The natural matter in soil comes from plants and animals.
* **Degraded:** The natural matter in soil derives from plants and animals.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores harder verb "derives" in place of "comes".

### Case F060

* **Axis:** `SYN`
* **Required change and validity criterion:** Restore one harder Original word or phrase with the same meaning as the simple wording.
* **Source:** WikiAutoEN
* **Original:** Throughout his career he worked on the organism "Drosophila melanogaster" with Thomas Hunt Morgan.
* **Simplified:** In his career he worked on the fruit-fly "Drosophila melanogaster" with Thomas Hunt Morgan.
* **Degraded:** In his career he worked on the organism " Drosophila melanogaster " with Thomas Hunt Morgan.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores the broader/more scientific Original noun "organism" in place of the more concrete "fruit-fly".

### Case F061

* **Axis:** `EXPL`
* **Required change and validity criterion:** Remove one explanation or definition that genuinely helped understanding, changing nothing else.
* **Source:** WikiAutoEN
* **Original:** Their long hair gives the breed its ability to overwinter.
* **Simplified:** Their long hair gives them the ability to overwinter in the valleys.
* **Degraded:** Their long hair gives them the ability to overwinter.
* [ ] Valid
* [x] Invalid
* [ ] Unsure
* **Note:** "in the valleys" specifies a location; it is not an explanation or definition of what "overwinter" means.

### Case F062

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** ASSET
* **Original:** Jörg Heinrich (born December 6, 1969 in Rathenow) is a German football defender.
* **Simplified:** Jörg Heinrich is a German football defender.
* **Degraded:** Jörg Heinrich are a German football defender.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Subject-verb agreement error ("are").

### Case F063

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** ASSET
* **Original:** He is released back into the wild, now with more adult feathers, and a tracking device strapped to his back, and leads the humans home to his native colony.
* **Simplified:** He is returned into the wild. He has more adult feathers, and a device on his back that leads humans to his colony.
* **Degraded:** He is returned into wild. He has more adult feathers, and a device on his back that leads humans to his colony.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Missing definite article ("into wild").

### Case F064

* **Axis:** `OMIT`
* **Required change and validity criterion:** Restore one detail that was usefully omitted; it must be unnecessary or too hard for the target reader.
* **Source:** WikiAutoEN
* **Original:** Wolf was born in Prague, Czechoslovakia.
* **Simplified:** He was born in Prague.
* **Degraded:** He was born in Prague, Czechoslovakia.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores country name detail from the Original.

### Case F065

* **Axis:** `EXPL`
* **Required change and validity criterion:** Remove one explanation or definition that genuinely helped understanding, changing nothing else.
* **Source:** WikiAutoEN
* **Original:** Israel Oliver Peña (born December 16, 1987), known as Israel Oliver, is a swimmer from Spain.
* **Simplified:** Israel Oliver Peña (born December 16, 1987 in Madrid) is a swimmer from Spain.
* **Degraded:** Israel Oliver Pen ̃ a (born December 16, 1987) is a swimmer from Spain.
* [ ] Valid
* [x] Invalid
* [ ] Unsure
* **Note:** "in Madrid" is a biographical place of birth, not an explanation or definition.

### Case F066

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** WikiAutoEN
* **Original:** Born and raised on the Upper West Side of Manhattan, New York City in 1977, Apple is the daughter of singer Diane McAfee and actor Brandon Maggart, who met when both were cast in the Broadway musical "Applause".
* **Simplified:** Apple was born in New York City to singer Diane McAfee and actor Brandon Maggart.
* **Degraded:** Apple was born on New York City to singer Diane McAfee and actor Brandon Maggart.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Preposition error ("born on New York City").

### Case F067

* **Axis:** `OMIT`
* **Required change and validity criterion:** Restore one detail that was usefully omitted; it must be unnecessary or too hard for the target reader.
* **Source:** WikiAutoEN
* **Original:** He was born into the noble Orsini family in Rome and served as a cardinal-deacon prior to becoming pope.
* **Simplified:** He was born into the noble Orsini family in Rome.
* **Degraded:** He was born into the noble Orsini family in Rome and served as a cardinal-deacon prior to becoming pope.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores complex ecclesiastical detail ("cardinal-deacon prior to becoming pope") that was omitted.

### Case F068

* **Axis:** `EXPL`
* **Required change and validity criterion:** Remove one explanation or definition that genuinely helped understanding, changing nothing else.
* **Source:** WikiAutoEN
* **Original:** Larry Paul Langford (March 17, 1946 – January 8, 2019) was an American politician who had a one-term tenure as the mayor of the city of Birmingham, Alabama.
* **Simplified:** Larry Paul Langford (March 17, 1946 – January 8, 2019) was an American politician and convicted criminal. He was the mayor of the city of Birmingham, Alabama serving from 2007 to 2009.
* **Degraded:** Larry Paul Langford (March 17, 1946 – January 8, 2019) was an American politician and convicted criminal. He was the mayor of the city of Birmingham, Alabama.
* [ ] Valid
* [x] Invalid
* [ ] Unsure
* **Note:** "serving from 2007 to 2009" is a date span detail, not an explanation or definition.

### Case F069

* **Axis:** `EXPL`
* **Required change and validity criterion:** Remove one explanation or definition that genuinely helped understanding, changing nothing else.
* **Source:** WikiAutoEN
* **Original:** mycorrhizae, mycorrhiza or mycorrhizas) is a symbiotic association between a fungus and a plant.
* **Simplified:** A mycorrhiza (Greek for "fungus roots") is a symbiotic association between a fungus and the roots of a plant.
* **Degraded:** A mycorrhiza (Greek for " fungus roots ") is a symbiotic association between a fungus and a plant.
* [ ] Valid
* [x] Invalid
* [ ] Unsure
* **Note:** "the roots of a plant" is a factual precision/correction rather than an explanation, and the actual explicit gloss `(Greek for "fungus roots")` was kept.

### Case F070

* **Axis:** `SYN`
* **Required change and validity criterion:** Restore one harder Original word or phrase with the same meaning as the simple wording.
* **Source:** WikiAutoEN
* **Original:** Exeter St David's is the principal railway station serving the city of Exeter in Devon, England.
* **Simplified:** Exeter St Davids railway station is the main train station in Exeter, England.
* **Degraded:** Exeter St Davids railway station is the principal railway station in Exeter, England.
* [ ] Valid
* [x] Invalid
* [ ] Unsure
* **Note:** Restores two words/phrases ("principal" for "main" and "railway station" for "train station") instead of one.

### Case F071

* **Axis:** `SYN`
* **Required change and validity criterion:** Restore one harder Original word or phrase with the same meaning as the simple wording.
* **Source:** WikiAutoEN
* **Original:** In cell biology, an organelle is a specialized subunit within a cell that has a specific function.
* **Simplified:** In cell biology, an organelle is a part of a cell that does a specific job.
* **Degraded:** In cell biology, an organelle is a part of a cell that does a specific function.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores "function" in place of "job".

### Case F072

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** ASSET
* **Original:** The Tuvaluan language is spoken by virtually everyone, while a language very similar to Gilbertese is spoken on Nui.
* **Simplified:** Almost everyone speaks Tuvaluan. On Nui, people speak a language similar to Gilbertese.
* **Degraded:** Almost everyone speaks Tuvaluan. On Nui, people speak a language similar at Gilbertese.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Incorrect preposition ("similar at" instead of "similar to").

### Case F073

* **Axis:** `SYN`
* **Required change and validity criterion:** Restore one harder Original word or phrase with the same meaning as the simple wording.
* **Source:** WikiAutoEN
* **Original:** Radar jamming and deception (electronic countermeasures) is the intentional emission of radio frequency signals to interfere with the operation of a radar by saturating its receiver with noise or false information.
* **Simplified:** Radar jamming is the emission of radio frequency signals to interfere with the work of a radar by flooding its receiver with noise or false information.
* **Degraded:** Radar jamming is the emission of radio frequency signals to interfere with the operation of a radar by flooding its receiver with noise or false information.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores "operation" in place of "work".

### Case F074

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** WikiAutoEN
* **Original:** Giuseppe Furino (] ; born 5 July 1946 in Palermo) is a retired Italian footballer who played as a midfielder.
* **Simplified:** Giuseppe Furino (born 5 July, 1946) is a former Italian football player.
* **Degraded:** Giuseppe Furino (born 5 July, 1946) are a former Italian football player.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Subject-verb agreement error ("are").

### Case F075

* **Axis:** `EXPL`
* **Required change and validity criterion:** Remove one explanation or definition that genuinely helped understanding, changing nothing else.
* **Source:** WikiAutoEN
* **Original:** He died on 13 March 2017 at the age of 92.
* **Simplified:** Boroumand died on 13 March 2017 in Tehran at the age of 92.
* **Degraded:** Boroumand died on 13 March 2017 at the age of 92.
* [ ] Valid
* [x] Invalid
* [ ] Unsure
* **Note:** Location of death ("in Tehran") is factual background, not an explanation or definition.

### Case F076

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** ASSET
* **Original:** These flies are clothed in black or pale (white or golden) hairs, and are themselves either black or metallic green or blue.
* **Simplified:** These flies have black or pale (white or golden) hairs. The flies themselves are either black or metallic green or blue.
* **Degraded:** These flies have black or pale (white or golden) hairs. The flies themselves is either black or metallic green or blue.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Subject-verb agreement error ("themselves is").

### Case F077

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** ASSET
* **Original:** Proper saddle care can extend the useful life of a saddle, often for decades.
* **Simplified:** Good saddle care can help the saddle last for many years.
* **Degraded:** Good saddle care can help saddle last for many years.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Missing article ("help saddle last").

### Case F078

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** WikiAutoEN
* **Original:** Skogö died on 28 May 2019, at the age of 70.
* **Simplified:** He died on 28 May 2019, at the age of 70.
* **Degraded:** He died on 28 May 2019, in the age of 70.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Preposition error ("in the age of 70").

### Case F079

* **Axis:** `SYN`
* **Required change and validity criterion:** Restore one harder Original word or phrase with the same meaning as the simple wording.
* **Source:** ASSET
* **Original:** While the weight of matter is entirely dependent upon the strength of gravity, the mass of matter is invariant.
* **Simplified:** While the weight of matter is only based upon the strength of gravity, the mass of matter never changes.
* **Degraded:** While the weight of matter is entirely dependent upon the strength of gravity, the mass of matter never changes.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores the harder phrase "entirely dependent" from the Original.

### Case F080

* **Axis:** `SYN`
* **Required change and validity criterion:** Restore one harder Original word or phrase with the same meaning as the simple wording.
* **Source:** WikiAutoEN
* **Original:** He worked in several positions there, but is arguably best known as a character designer.
* **Simplified:** He did many jobs there, but is probably best known as a character designer.
* **Degraded:** He did many jobs there, but is arguably best known as a character designer.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores harder adverb "arguably" in place of "probably".

### Case F081

* **Axis:** `OMIT`
* **Required change and validity criterion:** Restore one detail that was usefully omitted; it must be unnecessary or too hard for the target reader.
* **Source:** WikiAutoEN
* **Original:** Geoje (] ) is a city located in South Gyeongsang province, just off the coast of the port city of Busan, South Korea.
* **Simplified:** Geoje is a city in South Gyeongsang province, just off the coast of the port city of Busan, South Korea.
* **Degraded:** Geoje is a city located in South Gyeongsang province, just off the coast of the port city of Busan, South Korea.
* [ ] Valid
* [x] Invalid
* [ ] Unsure
* **Note:** "located" is a minor participle insertion (syntactic fluff/wordiness), not an omitted informative detail that was too hard or unnecessary.

### Case F082

* **Axis:** `OMIT`
* **Required change and validity criterion:** Restore one detail that was usefully omitted; it must be unnecessary or too hard for the target reader.
* **Source:** WikiAutoEN
* **Original:** Dionatan do Nascimento Teixeira (24 July 1992 – 5 November 2017) was a Brazilian-born Slovakian professional footballer who played as a centre-back.
* **Simplified:** Dionatan do Nascimento Teixeira (24 July 1992 – 5 November 2017) was a professional footballer.
* **Degraded:** Dionatan do Nascimento Teixeira (24 July 1992 – 5 November 2017) was a professional footballer who played as a centre-back.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores the specific playing position relative clause.

### Case F083

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** ASSET
* **Original:** The Polish people, or Poles (, singular Polak), are a Western Slavic ethnic group of Central Europe, living predominantly in Poland.
* **Simplified:** Polish people mostly live in Poland and come from Central Europe.
* **Degraded:** Polish people mostly live on Poland and come from Central Europe.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Preposition error ("live on Poland").

### Case F084

* **Axis:** `OMIT`
* **Required change and validity criterion:** Restore one detail that was usefully omitted; it must be unnecessary or too hard for the target reader.
* **Source:** WikiAutoEN
* **Original:** Edward Winslow Bryant Jr. (August 27, 1945 – February 10, 2017) was an American science fiction and horror writer sometimes associated with the Dangerous Visions series of anthologies that bolstered The New Wave.
* **Simplified:** Edward Winslow Bryant Jr. (August 27, 1945 – February 10, 2017) was an American science fiction and horror writer.
* **Degraded:** Edward Winslow Bryant Jr. (August 27, 1945 – February 10, 2017) was an American science fiction and horror writer sometimes associated with the Dangerous Visions series of anthologies that bolstered The New Wave.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores niche, complex literary trivia that was appropriately omitted.

### Case F085

* **Axis:** `SYN`
* **Required change and validity criterion:** Restore one harder Original word or phrase with the same meaning as the simple wording.
* **Source:** ASSET
* **Original:** There are numerous legends about the origins of boxing in Greece.
* **Simplified:** There are many legends about the start of boxing in Greece.
* **Degraded:** There are many legends about the origins of boxing in Greece.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores "origins" in place of "start".

### Case F086

* **Axis:** `OMIT`
* **Required change and validity criterion:** Restore one detail that was usefully omitted; it must be unnecessary or too hard for the target reader.
* **Source:** ASSET
* **Original:** Emmen is a municipality and a town in the northeastern Netherlands.
* **Simplified:** Emmen is a town in the Netherlands.
* **Degraded:** Emmen is a municipality and a town in the Netherlands.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores administrative term/detail "a municipality and".

### Case F087

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** WikiAutoEN
* **Original:** Lucey was born in La Crosse, Wisconsin on March 21, 1918, the son of Ella (McNamara) and Gregory Lucey.
* **Simplified:** Lucey was born in La Crosse, Wisconsin.
* **Degraded:** Lucey was born on La Crosse, Wisconsin.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Preposition error ("born on La Crosse").

### Case F088

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** WikiAutoEN
* **Original:** It builds a small stick nest several meters up in a tree and lays two white eggs.
* **Simplified:** When it lays its eggs, it builds a small stick nest several meters up in a tree.
* **Degraded:** When it lays its eggs, it builds a small stick nest several meters up in tree.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Missing article ("in tree").

### Case F089

* **Axis:** `OMIT`
* **Required change and validity criterion:** Restore one detail that was usefully omitted; it must be unnecessary or too hard for the target reader.
* **Source:** WikiAutoEN
* **Original:** John Harold Ostrom (February 18, 1928 – July 16, 2005) was an American paleontologist who revolutionized modern understanding of dinosaurs in the 1960s.
* **Simplified:** John Harold Ostrom (February 18, 1928 – July 16, 2005) was an American paleontologist.
* **Degraded:** John Harold Ostrom (February 18, 1928 – July 16, 2005) was an American paleontologist who revolutionized modern understanding of dinosaurs in the 1960s.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores non-essential complex relative clause.

### Case F090

* **Axis:** `SYN`
* **Required change and validity criterion:** Restore one harder Original word or phrase with the same meaning as the simple wording.
* **Source:** WikiAutoEN
* **Original:** The neck is the part of the body, on many vertebrates, that separates the head from the torso.
* **Simplified:** The neck is the part of the body that connects the head to the trunk.
* **Degraded:** The neck is the part of the body that connects the head to the torso.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores anatomical term "torso" in place of "trunk".

### Case F091

* **Axis:** `EXPL`
* **Required change and validity criterion:** Remove one explanation or definition that genuinely helped understanding, changing nothing else.
* **Source:** WikiAutoEN
* **Original:** She wrote several successful comedies, and was the first Chinese person to produce a complete Chinese version of Miguel de Cervantes' novel "Don Quixote".
* **Simplified:** She wrote several successful comedies. She was the first Chinese person to produce a complete Chinese version of "Don Quixote" from the Spanish original.
* **Degraded:** She wrote several successful comedies. She was the first Chinese person to produce a complete Chinese version of " Don Quixote ".
* [ ] Valid
* [x] Invalid
* [ ] Unsure
* **Note:** "from the Spanish original" is an additional factual detail about her source material, not an explanation or definition aiding understanding.

### Case F092

* **Axis:** `OMIT`
* **Required change and validity criterion:** Restore one detail that was usefully omitted; it must be unnecessary or too hard for the target reader.
* **Source:** ASSET
* **Original:** Health considerations Early-term surgical abortion is a simple procedure which is safer than childbirth when performed before the 16th week.
* **Simplified:** Early-term surgical abortion is a procedure that's safer than childbirth when performed before the 16th week.
* **Degraded:** Health considerations Early-term surgical abortion is a procedure that's safer than childbirth when performed before the 16th week.
* [ ] Valid
* [x] Invalid
* [ ] Unsure
* **Note:** "Health considerations" is an artifact section header from the source text, not an informative detail restored into the sentence.

### Case F093

* **Axis:** `OMIT`
* **Required change and validity criterion:** Restore one detail that was usefully omitted; it must be unnecessary or too hard for the target reader.
* **Source:** ASSET
* **Original:** Emmen is a municipality and a town in the northeastern Netherlands.
* **Simplified:** Emmen is a town in the northeastern Netherlands.
* **Degraded:** Emmen is a municipality and a town in the northeastern Netherlands.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores administrative term/detail "a municipality and".

### Case F094

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** WikiAutoEN
* **Original:** Ardeonaig (Gaelic: "Aird Eòdhanaig") is a hamlet on the southern shore of Loch Tay in the Stirling Council area of Scotland.
* **Simplified:** Ardeonaig is a village in Scotland. It is in the Stirling council area.
* **Degraded:** Ardeonaig is village in Scotland. It is in the Stirling council area.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Missing article ("is village").

### Case F095

* **Axis:** `SYN`
* **Required change and validity criterion:** Restore one harder Original word or phrase with the same meaning as the simple wording.
* **Source:** WikiAutoEN
* **Original:** Historically, Malay has been written using various scripts.
* **Simplified:** Historically, Malay has been written in various types of script.
* **Degraded:** Historically, Malay has been written in various scripts.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores Original concise/technical noun phrase "various scripts" replacing the simplified periphrasis "various types of script".

### Case F096

* **Axis:** `OMIT`
* **Required change and validity criterion:** Restore one detail that was usefully omitted; it must be unnecessary or too hard for the target reader.
* **Source:** WikiAutoEN
* **Original:** The River Lark is a river in England that crosses the border between Suffolk and Cambridgeshire.
* **Simplified:** The River Lark is a river in England.
* **Degraded:** The River Lark is a river in England that crosses the border between Suffolk and Cambridgeshire.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores non-essential geographical boundary detail.

### Case F097

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** WikiAutoEN
* **Original:** Squirrel monkeys live in the tropical forests of Central and South America in the canopy layer.
* **Simplified:** Squirrel monkeys live in Central and South America.
* **Degraded:** Squirrel monkeys live on Central and South America.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Preposition error ("live on Central and South America").

### Case F098

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** WikiAutoEN
* **Original:** Philippe Gilbert (born 5 July 1982) is a Belgian professional road bicycle racer, who currently rides for UCI WorldTeam Deceuninck–Quick-Step .
* **Simplified:** Philippe Gilbert (born 5 July 1982) is a Belgian professional road bicycle racer.
* **Degraded:** Philippe Gilbert (born 5 July 1982) are a Belgian professional road bicycle racer.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Subject-verb agreement error ("are").

### Case F099

* **Axis:** `SYN`
* **Required change and validity criterion:** Restore one harder Original word or phrase with the same meaning as the simple wording.
* **Source:** ASSET
* **Original:** A road number is often assigned to a stretch of public roadway.
* **Simplified:** A road number is often given to a part of roadway.
* **Degraded:** A road number is often assigned to a part of roadway.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores passive verb "assigned" in place of "given".

### Case F100

* **Axis:** `EXPL`
* **Required change and validity criterion:** Remove one explanation or definition that genuinely helped understanding, changing nothing else.
* **Source:** WikiAutoEN
* **Original:** Verdugo died on May 30, 2017 in Los Angeles at the age of 92.
* **Simplified:** Verdugo died on May 30, 2017 in Los Angeles, California from natural causes at the age of 92.
* **Degraded:** Verdugo died on May 30, 2017 in Los Angeles at the age of 92.
* [ ] Valid
* [x] Invalid
* [ ] Unsure
* **Note:** Removes factual cause of death ("from natural causes") and state ("California"), neither of which functions as an explanatory definition.

### Case F101

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** ASSET
* **Original:** He was married to Greek duchess Sofia.
* **Simplified:** He was married to Sofia. Sofia was a Greek duchess.
* **Degraded:** He were married to Sofia. Sofia was a Greek duchess.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Subject-verb agreement error ("He were").

### Case F102

* **Axis:** `SYN`
* **Required change and validity criterion:** Restore one harder Original word or phrase with the same meaning as the simple wording.
* **Source:** WikiAutoEN
* **Original:** Punjabi is the focal language of the people.
* **Simplified:** Punjabi is the main language of the people here.
* **Degraded:** Punjabi is the focal language of the people here.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores harder adjective "focal" in place of "main".

### Case F103

* **Axis:** `EXPL`
* **Required change and validity criterion:** Remove one explanation or definition that genuinely helped understanding, changing nothing else.
* **Source:** ASSET
* **Original:** The RPG-26 Aglen is a disposable anti-tank rocket launcher developed by the Soviet Union.
* **Simplified:** The RPG-26 Aglen is an anti-tank rocket launcher that can be thrown away after use. It was developed by the Soviet Union.
* **Degraded:** The RPG-26 Aglen is an anti-tank rocket launcher developed by the Soviet Union.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Successfully removes the plain-language definition/explanation of "disposable" ("that can be thrown away after use").

### Case F104

* **Axis:** `EXPL`
* **Required change and validity criterion:** Remove one explanation or definition that genuinely helped understanding, changing nothing else.
* **Source:** WikiAutoEN
* **Original:** "Cinnamon Girl" is a song by Neil Young.
* **Simplified:** "Cinnamon Girl" is a song first performed by Neil Young in 1969.
* **Degraded:** " Cinnamon Girl " is a song first performed by Neil Young.
* [ ] Valid
* [x] Invalid
* [ ] Unsure
* **Note:** "in 1969" is a date fact, not an explanation or definition.

### Case F105

* **Axis:** `SYN`
* **Required change and validity criterion:** Restore one harder Original word or phrase with the same meaning as the simple wording.
* **Source:** ASSET
* **Original:** On the outbreak of war in August 1914, the regiment went to France and was engaged in the early fighting.
* **Simplified:** At the start of war in August 1914, the army unit was fighting in France.
* **Degraded:** At the outbreak of war in August 1914, the army unit was fighting in France.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores "outbreak" in place of "start".

### Case F106

* **Axis:** `OMIT`
* **Required change and validity criterion:** Restore one detail that was usefully omitted; it must be unnecessary or too hard for the target reader.
* **Source:** WikiAutoEN
* **Original:** DuPage County is a county in the U.S. state of Illinois, and one of the collar counties of the Chicago metropolitan area.
* **Simplified:** DuPage County is a county in the U.S. state of Illinois.
* **Degraded:** DuPage County is a county in the U. S. state of Illinois, and one of the collar counties of the Chicago metropolitan area.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Restores the difficult/obscure local geographic terminology ("collar counties of the Chicago metropolitan area").

### Case F107

* **Axis:** `OMIT`
* **Required change and validity criterion:** Restore one detail that was usefully omitted; it must be unnecessary or too hard for the target reader.
* **Source:** ASSET
* **Original:** Note that Adrastea is now the name of another satellite of Jupiter.
* **Simplified:** Adrastea is the name of another satellite of Jupiter.
* **Degraded:** Note that Adrastea is the name of another satellite of Jupiter.
* [ ] Valid
* [x] Invalid
* [ ] Unsure
* **Note:** "Note that" is a meta-discourse discourse marker, not an informative detail.

### Case F108

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** ASSET
* **Original:** The electromagnetic spectrum is the range of all possible frequencies of electromagnetic radiation.
* **Simplified:** The electromagnetic spectrum is the range of electromagnetic radiation.
* **Degraded:** The electromagnetic spectrum are the range of electromagnetic radiation.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Subject-verb agreement error ("electromagnetic spectrum are").

### Case F109

* **Axis:** `EXPL`
* **Required change and validity criterion:** Remove one explanation or definition that genuinely helped understanding, changing nothing else.
* **Source:** WikiAutoEN
* **Original:** Marie-Fleur "Fleur" Agema (born 16 September 1976) is a Dutch politician and former spatial designer.
* **Simplified:** Marie-Fleur "Fleur" Agema (born 16 September 1976 in Purmerend) is a Dutch politician of the Party for Freedom (PVV).
* **Degraded:** Marie-Fleur " Fleur " Agema (born 16 September 1976) is a Dutch politician of the Party for Freedom (PVV).
* [ ] Valid
* [x] Invalid
* [ ] Unsure
* **Note:** "in Purmerend" is biographical place of birth, not an explanatory concept/definition.

### Case F110

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** ASSET
* **Original:** This article covers the details of the Preparations for Hurricane Katrina, a major category 5 hurricane that devastated parts of Louisiana, Mississippi, and Alabama.
* **Simplified:** This article is about the Preparations for Hurricane Katrina. Hurricane Katrina devastated parts of Louisiana, Mississippi, and Alabama.
* **Degraded:** This article are about the Preparations for Hurricane Katrina. Hurricane Katrina devastated parts of Louisiana, Mississippi, and Alabama.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Subject-verb agreement error ("article are").

### Case F111

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** WikiAutoEN
* **Original:** In the 1980s, he became famous throughout the Soviet Union for his songs about life as a Russian "émigré" in New York in Brighton Beach.
* **Simplified:** He was known for his 80s music about life as a Russian immigrant in New York.
* **Degraded:** He was known for his 80s music about life as a Russian immigrant on New York.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Preposition error ("on New York").

### Case F112

* **Axis:** `EXPL`
* **Required change and validity criterion:** Remove one explanation or definition that genuinely helped understanding, changing nothing else.
* **Source:** WikiAutoEN
* **Original:** Simon Blair Doull (born 6 August 1969) is a New Zealand radio personality, commentator and former international cricketer.
* **Simplified:** Simon Blair Doull (born 6 August 1969 in Pukekohe, Auckland) is a New Zealand radio personality, commentator and former international cricketer.
* **Degraded:** Simon Blair Doull (born 6 August 1969) is a New Zealand radio personality, commentator and former international cricketer.
* [ ] Valid
* [x] Invalid
* [ ] Unsure
* **Note:** "in Pukekohe, Auckland" is a birth location, not an explanation or definition.

### Case F113

* **Axis:** `EXPL`
* **Required change and validity criterion:** Remove one explanation or definition that genuinely helped understanding, changing nothing else.
* **Source:** WikiAutoEN
* **Original:** Julio Gutierrez Garcia (born in Madrid) is a track and field athlete from Spain.
* **Simplified:** Julio Gutierrez Garcia (born March 26, 1962 in Madrid) is a track and field athlete from Spain.
* **Degraded:** Julio Gutierrez Garcia (born in Madrid) is a track and field athlete from Spain.
* [ ] Valid
* [x] Invalid
* [ ] Unsure
* **Note:** "March 26, 1962" is an exact date of birth, not an explanation or definition.

### Case F114

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** WikiAutoEN
* **Original:** Supertramp is the self-titled debut album by the English rock band Supertramp, released in July 1970.
* **Simplified:** Supertramp is the first album of Supertramp. Supertramp recorded this album in June 1970 in Willesden.
* **Degraded:** Supertramp are the first album of Supertramp. Supertramp recorded this album in June 1970 in Willesden.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Subject-verb agreement error ("Supertramp are the first album").

### Case F115

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** ASSET
* **Original:** Cognition is the scientific term for "the process of thought".
* **Simplified:** Cognition is "the process of thought".
* **Degraded:** Cognition is " the process for thought ".
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Preposition error ("process for thought").

### Case F116

* **Axis:** `FLUENCY`
* **Required change and validity criterion:** Introduce one obvious local grammar error while preserving the meaning and every other quality.
* **Source:** WikiAutoEN
* **Original:** Bradley Whitford (born October 10, 1959) is an American actor and political activist.
* **Simplified:** Bradley Whitford (born October 10, 1959 in Madison, Wisconsin) is an American actor.
* **Degraded:** Bradley Whitford (born October 10, 1959 on Madison, Wisconsin) is an American actor.
* [x] Valid
* [ ] Invalid
* [ ] Unsure
* **Note:** Preposition error ("on Madison, Wisconsin").