# Qualitative audit: iDEM and Saaq al-Bambuu

This is a small manual inspection of the 1,406 newly integrated pairs. It is
diagnostic rather than a formal annotation study.

## LaBSE below 0.62

For Saaq al-Bambuu, the inspected extreme cases are clearly unrelated sentence
pairs, so the lower threshold is useful for detecting alignment errors.

| Original | Simplification | LaBSE | Corpus source |
|---|---|---:|---|
| لابد أن ذنبه العظيم وانكشاف أمره دفعاه للهرب من المواجهة والدفاع عن نفسه. | هل كنت مخدوعا بغسان؟ تقول خولة أن هذا ما تؤمن به ماما غنيمة، وهو ما ترفضه عمتي هند. | 0.048097 | Saaq al-Bambuu |
| شعر بالإهمال فانتفض. | كنت وحيدا. | 0.190301 | Saaq al-Bambuu |

The iDEM cases are mixed. The filter catches malformed or weakly aligned pairs,
but it also removes valid Easy-to-Read rewrites that expand an expression with
an explanation. This suggests calibrating the lower threshold separately for
iDEM rather than accepting `0.62` as final.

| Original | Simplification | LaBSE | Corpus source |
|---|---|---:|---|
| ES_017_025 | El juez, en su auto, resta importancia al papel que Rodríguez jugó en las filtraciones y en cómo desencadenó los movimientos de la Fiscalía, al entender que la causa gira en torno a la filtración de otro correo: el de febrero en el que el abogado de González Amador reconocía su fraude fiscal de 350.000 euros. aseguras tu derecho a participar en las decisiones sobre el futuro de la Unión Europea. También apoyas que los diputados que forman parte del Parlamento europeo cumplan sus funciones de acuerdo a la ley. | 0.198598 | iDEM / Spanish |
| Si també cal reduir la fiança, es concretarà en aquesta trucada. | Si heu de deixar menys diners de la fiança, us ho diran durant la trucada. Una fiança és una quantitat de diners que una persona deixa com a garantia. En el cas del BdM serveix per assegurar que la persona tornarà el producte que li han deixat. Quan es retorna el producte es retornen els diners. | 0.502366 | iDEM / Catalan |
| 17 marzo 2020 n. 18 e del Decreto del Presidente del Consiglio dei Ministri di data 18 ottobre 2020, con modalità di comunicazione e partecipazione telematiche attraverso la piattaforma “Zoom Meeting”. | Abbiamo fatto tutto secondo le regole della legge. Tutte le informazioni e l'incontro erano online. Abbiamo usato la piattaforma Zoom. | 0.444313 | iDEM / Italian |

## LaBSE above 0.95

The inspected Saaq cases contain only a preposition, pronoun, or lexical
substitution. In iDEM, several cases are identical headings, dates, or numbers;
others contain limited paraphrasing or sentence splitting. The filter is useful
for removing near copies, although sentence-splitting cases should be reviewed
when the threshold is tuned.

| Original | Simplification | LaBSE | Corpus source |
|---|---|---:|---|
| يعمل حاليا بوظيفة مترجم في سفارة جمهورية الفلبين لدى الكويت. | يعمل حاليا بوظيفة مترجم في سفارة جمهورية الفلبين في الكويت. | 0.999499 | Saaq al-Bambuu |
| Madrid, 15 de noviembre de 2021. | Madrid, 15 de noviembre de 2021. | 1.000000 | iDEM / Spanish |
| El Banc del Moviment és un servei municipal de la Xarxa Solidària de Productes de Suport de Barcelona. | El Banc del Moviment és un servei de l'Ajuntament de Barcelona. Forma part de la Xarxa Solidària de Productes de Suport de Barcelona. | 0.962563 | iDEM / Catalan |
| Le ultime elezioni si sono svolte a giugno 2024: ecco i risultati. | Le ultime elezioni c'erano a giugno 2024. Ecco i risultati. | 0.981520 | iDEM / Italian |

## Complexity inversions

The classifier rejected five iDEM pairs and no Saaq pair as confident
complexity inversions. The Catalan example below is a plausible Easy-to-Read
rewrite with splitting and explanation, so its rejection is a classifier false
positive. Two Spanish inversions involve isolated section numbers and are poor
input pairs independently of the complexity prediction.

| Original | Simplification | LaBSE | Corpus source |
|---|---|---:|---|
| [2] L’èxit d’aquestes accions va animar la capital catalana a organitzar, el 2004, el Fòrum Universal de les Cultures, una trobada sobre el diàleg cultural promoguda per la UNESCO. | L’èxit de les celebracions com els Jocs Olímpics va animar Barcelona a organitzar el Fòrum Universal de les Cultures a l'any 2004. Era una trobada per parlar sobre el diàleg entre cultures. Aquest acte va ser promogut per la UNESCO. La Unesco és l'Organització de les Nacions Unides per l'Educació, la Ciència i la Cultura. | 0.826816 | iDEM / Catalan |
| 2. | Sesión 2. Revisión y mejora | 0.392324 | iDEM / Spanish |
