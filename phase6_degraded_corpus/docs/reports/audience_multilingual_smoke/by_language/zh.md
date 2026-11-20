# Chinese: simplifications by audience and generator

[← Back to the report](../README.md) · 10 originals · Gemini = gemini-3.5-flash-lite, GPT = gpt-5.4-mini

**Strategies** are confirmed as in the FEATS pipeline: at least 2 of the 4 E2R strategy classifiers (E5, XLM-R, Qwen2.5-7B, Gemma-3-12B, each with its published thresholds) predict the strategy, and Gemma is one of them. The classifiers cover six strategies; Illocution is not detected. Chinese is not among the classifiers' training languages, so these labels are indicative only.

## 1. wikimedia/wikipedia:20231101.zh

> **Original:** 夫武昌揚靈於大江，東趨賓山（江蘇省），四日而極，足以轉輸矣，外鑑諸鄰國，柏林無海，江戶則曰海堧爾；內海雖咸，亦猶大江也……江沔之在上游，其通達等是矣，何必傅海！

| Audience | Gemini | GPT |
|---|---|---|
| **B1 adults** | 武昌的軍隊在長江上很有威望。向東到江蘇的賓山，四天就到了。這條路用來運送物資很足夠了。看看外面的國家：柏林沒有海，江戶也只是靠海邊。內海雖然是鹹水，也跟長江一樣。長江和漢水在上游，交通一樣方便，為什麼一定要走到海邊呢？<br><sub>**Strategies:** Compression, Modulation, Omission, Synonymy</sub> | 武昌在长江上扬名，向东到宾山（江苏省），四天就能到达，已经足够运送货物了。和邻国相比，柏林没有海，江户则靠海；内海虽然是咸水，也还是像大江一样……江沔在上游，交通便利也是一样的，何必一定要靠海呢！<br><sub>**Strategies:** Compression, Modulation, Omission, Synonymy</sub> |
| **Children 8–13** | 武昌的船在大江上展現神威，四天就能抵達江蘇的賓山，運送物資非常足夠。看看外面的鄰國，柏林沒有海，江戶也只是靠著海邊。內海雖然是鹹水，但也像大江一樣。長江和漢水在上游一樣很通暢，為什麼一定要出海呢！<br><sub>**Strategies:** Compression, Modulation, Omission, Synonymy</sub> | 武昌在大江上，向東流到賓山（江蘇省），要四天才到。這已經足夠運送貨物了。看一看鄰國，柏林沒有海，江戶也只是靠海；內海雖然是咸水，也像大江一樣……江沔在上游，通到外面的地方也是一樣，何必一定要靠海呢！<br><sub>**Strategies:** Compression, Modulation, Omission, Synonymy</sub> |
| **Intellectual disability** | 長江水路交通很好。我們不需要靠海。<br><sub>**Strategies:** Compression, Omission</sub> | 武昌在長江邊，向東到賓山（江蘇省），四天就到了，已經足夠運送貨物了。對外看鄰國，柏林沒有海，江戶也只是靠海；對內看，海水雖然是鹹的，也還像大江一樣……長江和沔水在上游，通達的情況也是一樣，何必一定要靠海呢！<br><sub>**Strategies:** Compression, Modulation, Omission, Synonymy</sub> |

## 2. wikimedia/wikipedia:20231101.zh

> **Original:** 古《尚書》說，脾，木也；肺，火也；心，土也；肝，金也；腎，水也。

| Audience | Gemini | GPT |
|---|---|---|
| **B1 adults** | 古老《尚書》記載，脾是木，肺是火，心是土，肝是金，腎是水。<br><sub>**Strategies:** Synonymy</sub> | The old book Shangshu says: the spleen is wood, the lungs are fire, the heart is earth, the liver is metal, and the kidneys are water. ⚠️ *wrong language*<br><sub>**Strategies:** Modulation, Synonymy</sub> |
| **Children 8–13** | 古書《尚書》說：脾臟就像木，肺就像火，心臟就像土，肝臟就像金，腎臟就像水。<br><sub>**Strategies:** Explanation, Synonymy</sub> | 古代的《尚書》說：脾屬木，肺屬火，心屬土，肝屬金，腎屬水。<br><sub>**Strategies:** none</sub> |
| **Intellectual disability** | 古書說：脾是木，肺是火，心是土，肝是金，腎是水。<br><sub>**Strategies:** Compression, Synonymy</sub> | 古《尚書》說，脾屬木，肺屬火，心屬土，肝屬金，腎屬水。<br><sub>**Strategies:** Compression</sub> |

## 3. wikimedia/wikipedia:20231101.zh

> **Original:** 戰國初年，各國開始變法運動，其中，以李悝變法的魏國，在魏文侯時首先興起，北伐韓、趙、中山，東伐齊、宋，南伐楚，西伐秦，成為強國。

| Audience | Gemini | GPT |
|---|---|---|
| **B1 adults** | 戰國初年，各國開始改革。魏國在李悝變法和魏文侯的帶領下，變得非常強大。魏國向北、向東、向南、向西攻打其他國家，成為當時的強國。<br><sub>**Strategies:** Compression, Modulation, Synonymy</sub> | 戰國初年，各國開始改革。其中，魏國在魏文侯時先開始李悝變法。魏國向北攻打韓、趙、中山，向東攻打齊、宋，向南攻打楚，向西攻打秦，最後成為強國。<br><sub>**Strategies:** Compression, Modulation, Synonymy</sub> |
| **Children 8–13** | 戰國剛開始的時候，各國紛紛改變舊辦法來讓國家變強。其中，魏國因為用了李悝（ㄎㄨㄟ）的辦法，在魏文侯的帶領下最早強大起來。魏國到處攻打其他國家，成為一個很厲害的強國。<br><sub>**Strategies:** Compression, Synonymy</sub> | 戰國初年，各國開始改革。其中，魏國在魏文侯時先開始改革。李悝幫助魏國變法，讓魏國變強。魏國還向北攻打韓、趙、中山，向東攻打齊、宋，向南攻打楚，向西攻打秦，成為強國。<br><sub>**Strategies:** Compression, Modulation, Synonymy, Syntactic change</sub> |
| **Intellectual disability** | 戰國初年，各國開始改革。魏國在李悝和魏文侯的帶領下最早變強，四處攻打其他國家，成為一個強大的國家。<br><sub>**Strategies:** Compression, Synonymy</sub> | 戰國初年，各國開始改革。魏國在魏文侯時，先開始李悝的改革。魏國向北攻打韓、趙、中山，向東攻打齊、宋，向南攻打楚，向西攻打秦，最後成為強國。<br><sub>**Strategies:** Compression, Modulation, Synonymy</sub> |

## 4. wikimedia/wikipedia:20231101.zh

> **Original:** 生命的最小單位是生物，生物是由一個或多個細胞組成，能够新陳代謝，維持恆定性，可以成長，回应刺激，可以繁殖甚至演化，以適應外界環境，繼續繁殖并產生後代。

| Audience | Gemini | GPT |
|---|---|---|
| **B1 adults** | 生命的最小單位是細胞。細胞可以維持生命、長大、生出後代，還能適應環境。<br><sub>**Strategies:** Compression, Omission, Synonymy</sub> | 生物是生命的最小單位。生物由一個或多個細胞組成。它們可以新陳代謝，維持身體穩定，可以成長，對刺激作出反應，可以繁殖，也可以演化，以適應外界環境，繼續繁殖並產生後代。<br><sub>**Strategies:** Compression, Modulation, Synonymy</sub> |
| **Children 8–13** | 所有生物都是由細胞組成的。細胞是生命的最小單位。生物會長大、生小孩，還能適應環境。<br><sub>**Strategies:** Compression, Modulation, Omission, Synonymy, Syntactic change</sub> | 生物是生命的最小單位。生物由一個或多個細胞組成，可以新陳代謝，維持身體穩定，可以成長，對刺激做出反應，也可以繁殖，甚至演化，來適應外界環境，繼續繁殖並產生後代。<br><sub>**Strategies:** Compression, Synonymy</sub> |
| **Intellectual disability** | 細胞是生命的基本單位。細胞會長大，會生出下一代，還能適應環境。<br><sub>**Strategies:** Compression, Omission, Synonymy</sub> | 生物是生命的最小單位。生物由一個或多個細胞組成。它們可以新陳代謝，維持身體穩定，可以成長，對刺激作出反應，可以繁殖，也可以演化，適應外界環境，繼續繁殖並產生後代。<br><sub>**Strategies:** Compression, Modulation, Synonymy</sub> |

## 5. wikimedia/wikipedia:20231101.zh

> **Original:** 前781年，周幽王继位，任用好利的虢石父执政，朝政腐败，国人怨声四起；幽王三年（前779年），伐六济之戎失败；同时天灾频仍，周朝统治内外交困。

| Audience | Gemini | GPT |
|---|---|---|
| **B1 adults** | 公元前781年，周幽王当了国王。他让贪财的虢石父掌管国家，政治变得很腐败，百姓非常不满。公元前779年，周幽王打仗失败。这时候又发生很多天灾，周朝陷入了严重的困境。<br><sub>**Strategies:** Modulation, Synonymy</sub> | 前781年，周幽王继位。他任用贪财的虢石父管理朝政，国家政治腐败，百姓怨声四起。幽王三年，也就是前779年，讨伐六济之戎失败。同时，天灾不断，周朝内外交困。<br><sub>**Strategies:** Compression, Modulation, Synonymy</sub> |
| **Children 8–13** | 前781年，周幽王当了国王。他重用贪财的虢石父，把国家治理得很糟，百姓非常不满。三年后，周幽王打仗失败。再加上天灾不断，周朝陷入了内外困境。<br><sub>**Strategies:** Modulation, Synonymy</sub> | 前781年，周幽王继位。他任用贪财的虢石父管理国家，朝廷很腐败，百姓怨声不断。幽王三年，也就是前779年，攻打六济之戎失败。那时，天灾也很多，周朝内外都很困难。<br><sub>**Strategies:** Compression, Modulation, Omission, Synonymy</sub> |
| **Intellectual disability** | 公元前781年，周幽王当了国王。他重用贪财的虢石父，把国家治理得很糟，百姓非常不满。公元前779年，周幽王打仗失败。这时候又接连发生天灾，周朝遇到了很大的困难。<br><sub>**Strategies:** Compression, Modulation, Synonymy</sub> | 前781年，周幽王继位。他任用贪财的虢石父管理朝政，国家政治腐败，百姓怨声不断。幽王三年，也就是前779年，讨伐六济之戎失败。那时，天灾也很多。周朝内外都很困难。<br><sub>**Strategies:** Compression, Modulation, Omission, Synonymy</sub> |

## 6. wikimedia/wikipedia:20231101.zh

> **Original:** 五年后，王莽毒死仅14岁的平帝，并迎立太子刘婴即位，号“孺子”，自己担任“假皇帝”，9年1月，王莽逼迫孺子婴退位，篡漢自立新朝，西汉结束。

| Audience | Gemini | GPT |
|---|---|---|
| **B1 adults** | 五年后，王莽毒死了十四岁的平帝。 王莽让年幼的刘婴当皇帝。 九年一月，王莽逼刘婴退位。 王莽自己当皇帝，建立了新朝。 西汉灭亡了。<br><sub>**Strategies:** Compression, Modulation, Omission, Synonymy</sub> | 五年后，王莽毒死了只有14岁的平帝，又立太子刘婴做皇帝，称他为“孺子”。王莽自己做“假皇帝”。公元9年1月，王莽逼孺子婴退位，夺取汉朝政权，建立新朝，西汉结束。<br><sub>**Strategies:** Compression, Modulation, Synonymy</sub> |
| **Children 8–13** | 五年后，王莽毒死了十四岁的汉平帝。他又让两岁的刘婴当皇帝，自己当假皇帝。公元9年，王莽逼刘婴退位，自己当了皇帝，建立了新朝，西汉就这样结束了。<br><sub>**Strategies:** Compression, Modulation, Synonymy</sub> | 五年后，王莽毒死了只有14岁的平帝，又扶立太子刘婴做皇帝，称他为“孺子”。王莽自己做“假皇帝”。公元9年1月，王莽逼孺子婴退位，夺取汉朝皇位，建立新朝。西汉结束了。<br><sub>**Strategies:** Compression, Modulation, Synonymy</sub> |
| **Intellectual disability** | 王莽害死了十四岁的皇帝。 后来，王莽自己当了皇帝。 西汉灭亡了。<br><sub>**Strategies:** Compression, Modulation, Omission, Synonymy</sub> | 五年后，王莽毒死了只有14岁的平帝，又让太子刘婴继位，称为“孺子”。王莽自己做“假皇帝”。9年1月，王莽逼孺子婴退位，夺取汉朝政权，建立新朝。西汉结束。<br><sub>**Strategies:** Compression, Modulation, Synonymy</sub> |

## 7. wikimedia/wikipedia:20231101.zh

> **Original:** 1842年，英軍進入長江，切斷江南對北京的物資供應，於是清廷求和，《南京條約》簽署，除在東南沿海開放上海等5個通商口岸之外，還割讓香港島，中國的主權受到破壞。

| Audience | Gemini | GPT |
|---|---|---|
| **B1 adults** | 1842年，英國軍隊打到長江，切斷了北京的物資。清朝政府只好求和，簽署了《南京條約》。條約規定：中國開放上海等5個港口做生意，還要割讓香港島，這破壞了中國的主權。<br><sub>**Strategies:** Compression, Explanation, Modulation, Synonymy</sub> | 1842年，英軍進入長江，切斷江南對北京的物資供應。清廷於是求和，簽署了《南京條約》。除了在東南沿海開放上海等5個通商口岸，還割讓了香港島。中國的主權也因此受到破壞。<br><sub>**Strategies:** Compression, Modulation</sub> |
| **Children 8–13** | 1842年，英國軍隊打到長江，切斷了運往北京的物資，清朝只好求和。雙方簽署了《南京條約》，中國不僅被迫開放上海等5個港口做生意，還把香港島割讓給英國，國家主權受到了破壞。<br><sub>**Strategies:** Compression, Synonymy</sub> | 1842年，英軍進入長江，切斷了江南送往北京的物資。後來，清朝政府求和，簽下了《南京條約》。除了在東南沿海開放上海等5個通商口岸，還把香港島割讓出去。中國的主權也因此受到破壞。<br><sub>**Strategies:** Compression, Modulation, Synonymy</sub> |
| **Intellectual disability** | 1842年，英國軍隊打到長江。清朝政府沒有辦法，只好求和。雙方簽了《南京條約》。中國被迫讓出香港島，還要開放五個港口做生意。<br><sub>**Strategies:** Compression, Modulation, Omission, Synonymy</sub> | 1842年，英軍進入長江，切斷了江南送往北京的物資。清朝政府只好求和，簽下《南京條約》。  除了在東南沿海開放上海等5個通商口岸，還把香港島割讓出去。中國的主權也受到破壞。<br><sub>**Strategies:** Compression, Modulation, Omission, Synonymy</sub> |

## 8. wikimedia/wikipedia:20231101.zh

> **Original:** 936年，軍閥石敬瑭與後唐皇帝鬧翻，聯合契丹人攻打洛陽，後唐滅亡，石敬塘建後晉，石敬塘為了獲契丹的支持，把燕雲十六州割讓給契丹，使之後中原的邊防受到嚴重威脅。

| Audience | Gemini | GPT |
|---|---|---|
| **B1 adults** | 936年，軍閥石敬瑭與後唐皇帝鬧翻。石敬瑭聯合契丹人攻打洛陽，滅了後唐，建立了後晉。為了得到契丹的支持，石敬塘把燕雲十六州送給了契丹。這讓後來中原的邊防受到嚴重的威脅。<br><sub>**Strategies:** Compression, Modulation, Synonymy</sub> | 936年，軍閥石敬瑭和後唐皇帝鬧翻，聯合契丹人攻打洛陽。後唐滅亡後，石敬瑭建立後晉。為了得到契丹的支持，他把燕雲十六州割讓給契丹，讓中原後來的邊防受到嚴重威脅。<br><sub>**Strategies:** Compression, Modulation, Synonymy</sub> |
| **Children 8–13** | 936年，軍閥石敬瑭和後唐皇帝吵翻了。石敬瑭 找契丹人幫忙攻打洛陽，後唐就滅亡了。石敬瑭建立了後晉，為了感謝契丹，他把重要的土地「燕雲十六州」送給了契丹。這讓中原地區的防守變得很危險。<br><sub>**Strategies:** Compression, Modulation, Synonymy</sub> | 936年，軍閥石敬瑭和後唐皇帝鬧翻了。他聯合契丹人攻打洛陽，後唐滅亡。石敬瑭建立了後晉。為了得到契丹的支持，他把燕雲十六州割讓給契丹，讓中原後來的邊防受到很大威脅。<br><sub>**Strategies:** Compression, Modulation, Synonymy</sub> |
| **Intellectual disability** | 936年，石敬瑭帶兵攻打洛陽，建立了後晉。他把土地送給契丹人，換取契丹的支持。這讓以後中國北方的安全受到很大的威脅。<br><sub>**Strategies:** Compression, Modulation, Omission, Synonymy</sub> | 936年，軍閥石敬瑭和後唐皇帝鬧翻，聯合契丹人攻打洛陽。後唐滅亡後，石敬瑭建立後晉。為了得到契丹的支持，他把燕雲十六州割讓給契丹，讓中原後來的邊防受到嚴重威脅。<br><sub>**Strategies:** Compression, Modulation, Synonymy</sub> |

## 9. wikimedia/wikipedia:20231101.zh

> **Original:** 6月，黃埔軍校正式開學，第一期有學員600多人，孫兼任軍校總理，任命蔣為校長，廖仲愷為黨代表；蘇聯派出多名軍官作顧問，並安排中國共產黨黨員入軍校就讀或任教。

| Audience | Gemini | GPT |
|---|---|---|
| **B1 adults** | 6月，黃埔軍校正式開學，有六百多名學生。孫中山擔任軍校總理，蔣介石是校長，廖仲愷是黨代表。蘇聯派軍官來當顧問，也安排中國共產黨黨員去軍校讀書或教書。<br><sub>**Strategies:** Compression, Modulation, Synonymy, Syntactic change</sub> | 6月，黃埔軍校正式開學。第一期有600多名學員。孫兼任軍校總理，任命蔣為校長，廖仲愷為黨代表。蘇聯派出多名軍官作顧問，並安排中國共產黨黨員到軍校讀書或教書。<br><sub>**Strategies:** Compression, Modulation, Synonymy, Syntactic change</sub> |
| **Children 8–13** | 6月，黃埔軍校正式開學，有六百多名學生。孫中山擔任總理，蔣介石當校長，廖仲愷當黨代表。蘇聯派軍官來當顧問，也有共產黨員來讀書或當老師。<br><sub>**Strategies:** Compression, Modulation, Synonymy, Syntactic change</sub> | 6月，黃埔軍校正式開學。第一期有600多名學員。孫兼任軍校總理，任命蔣為校長，廖仲愷為黨代表。蘇聯派出多名軍官當顧問，還安排中國共產黨黨員到軍校讀書或教書。<br><sub>**Strategies:** Compression, Modulation, Synonymy, Syntactic change</sub> |
| **Intellectual disability** | 6月，黃埔軍校開學。 第一期有600多個學生。 孫中山是總理，蔣中正做校長，廖仲愷做黨代表。 蘇聯派人來當顧問。 中國共產黨員也可以去讀書或教書。<br><sub>**Strategies:** Compression, Modulation, Omission, Synonymy</sub> | 6月，黃埔軍校正式開學。第一期有600多名學員。孫兼任軍校總理，任命蔣為校長，廖仲愷為黨代表。蘇聯派出多名軍官當顧問，也安排中國共產黨黨員到軍校讀書或教書。<br><sub>**Strategies:** Compression, Modulation, Synonymy, Syntactic change</sub> |

## 10. wikimedia/wikipedia:20231101.zh

> **Original:** 此时，由于秦末以来动乱多年，国力虚弱，导致汉高祖刘邦在收复秦末被匈奴占据的河套地区时，遭匈奴冒顿单于围困于白登，即白登之围，从此以后，汉朝采用和亲政策。

| Audience | Gemini | GPT |
|---|---|---|
| **B1 adults** | 当时，中国多年打仗，国家很弱。汉高祖刘邦想收回被匈奴占领的土地，却被匈奴包围了。从那以后，汉朝开始和匈奴和亲。<br><sub>**Strategies:** Compression, Modulation, Omission, Synonymy</sub> | 当时，因为秦朝末年以后多年战乱，国家力量很弱，所以汉高祖刘邦在收复秦朝末年被匈奴占领的河套地区时，被匈奴首领冒顿单于围困在白登，这就是白登之围。从那以后，汉朝开始实行和亲政策。<br><sub>**Strategies:** Compression, Modulation, Synonymy</sub> |
| **Children 8–13** | 当时，中国刚刚经历多年战争，国家很虚弱。汉高祖刘邦想夺回被匈奴占领的土地，却被匈奴单于围困在白登山。这就是著名的白登之围。从那以后，汉朝开始对匈奴实行和亲政策。<br><sub>**Strategies:** Compression, Modulation, Synonymy</sub> | 这时，因为秦朝末年以后多年战乱，国家力量很弱，汉高祖刘邦在收回被匈奴占领的河套地区时，被匈奴首领冒顿单于围困在白登，这就是白登之围。从那以后，汉朝开始采用和亲政策。<br><sub>**Strategies:** Compression, Modulation, Synonymy</sub> |
| **Intellectual disability** | 当时，中国打仗很多年，国家很弱。 汉高祖刘邦去打匈奴时，被匈奴军队围困在白登山。 从那时候起，汉朝开始和匈奴和亲。<br><sub>**Strategies:** Compression, Modulation, Omission, Synonymy</sub> | 这时，因为秦朝末年以后多年战乱，国家力量很弱，汉高祖刘邦在收复秦朝末年被匈奴占领的河套地区时，被匈奴首领冒顿单于围困在白登，这就是白登之围。从此以后，汉朝采取了和亲政策。<br><sub>**Strategies:** Compression, Modulation, Synonymy</sub> |
