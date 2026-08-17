# Qualitative audit: English and Spanish

This is a small manual inspection of rejected pairs near the LaBSE thresholds
and of Spanish complexity inversions. It is diagnostic rather than a formal
annotation study.

## English: LaBSE above 0.95

These examples are near copies or introduce only limited lexical, omission, or
sentence-boundary changes. Their removal is consistent with the aim of excluding
pairs with too little simplification.

| Original | Simplification | LaBSE | Corpus source |
|---|---|---:|---|
| Cinco de Mayo (in Latin America, Spanish for "Fifth of May") is an annual celebration held on May 5. | Cinco de Mayo (Spanish for "Fifth of May") is a celebration held on the May 5. | 0.952649 | Align-and-Shine / Wikipedia-Vikidia |
| The Republican Party is one of the two major contemporary political parties in the United States, along with the Democratic Party. | The Republican Party is one of the two main political parties in the United States, along with the Democratic Party. | 0.950028 | MultiSim / ASSET |
| Saxon Switzerland is a mountainous climbing area and national park near Dresden in Saxony, Germany. | Saxon Switzerland is a mountainous area and national park near Dresden. | 0.950035 | MultiSim / ASSET |
| Phyllis Lapin is a sales representative at fictitious paper distributor Dunder Mifflin. | Lapin is a sales representative at fictitious paper distributor Dunder Mifflin. | 0.950001 | MultiSim / WikiAutoEN |

The inspected cases support the high threshold locally. Nevertheless, its
corpus-level effect is aggressive: it removes 36.17% of ASSET and 30.15% of
WikiAutoEN, so a larger sample is needed before treating 0.95 as final.

## English: LaBSE below 0.62

The low threshold identifies clear information loss or semantic drift, but it
also removes some plausible paraphrases and compressions.

| Original | Simplification | LaBSE | Corpus source |
|---|---|---:|---|
| He was found by Courson in a bathtub at his apartment. | He was found in a Paris apartment bathtub. | 0.619956 | Align-and-Shine / Wikipedia-Vikidia |
| Autumnal (autumn): Generally begins mid to late September. Tree leaves in full color then turn brown and fall to the ground. | Autumn - this is when leaves fall from the trees and the nights start to get colder. | 0.619930 | Align-and-Shine / Wikipedia-Vikidia |
| Bruises often induce pain but are not normally dangerous. | Painful bruises are normally safe. | 0.619441 | MultiSim / ASSET |
| Also, it hybridizes with some other wattles, notably the rare and endangered Sydney Basin species Acacia pubescens. | It combines with some other wattles including a rare species. | 0.619058 | MultiSim / ASSET |
| The film was released in the United States on May 23, 1980, and in the United Kingdom on October 2, 1980, by Warner Bros. | It was released on May 23, 1980. | 0.619994 | MultiSim / WikiAutoEN |
| On May 3, 1980, he married psychotherapist Carla Green, who then also began serving as his manager; she later became a personal trainer. | In 1980, he married Carla Ferrigno. | 0.619990 | MultiSim / WikiAutoEN |

The last WikiAutoEN example contains a changed name and is a useful rejection.
The first two Align-and-Shine examples remain plausible simplifications despite
falling just below the threshold. This supports calibrating the lower boundary
per source instead of assuming that 0.62 transfers uniformly.

## Spanish: complexity inversions

No Spanish pair was rejected by either LaBSE threshold; all 143 Spanish
rejections came from the complexity-inversion filter. These examples include
valid simplifications, showing false positives from the classifier.

| Original | Simplification | LaBSE | Corpus source |
|---|---|---:|---|
| Ollanta Moisés Humala Tasso (Lima, 27 de junio de 1962) es un militar retirado y político peruano. | Ollanta Moisés Humala Tasso (*Lima, 1962) es un político peruano. | 0.916116 | Align-and-Shine / Wikipedia-Vikidia |
| El jabalí se adapta a todo tipo de hábitats siempre que disponga de una mínima cobertura y alimento (acuden mucho a los chaparros por la bellota), aunque prefiere los lugares con una vegetación alta donde poder camuflarse (carrasca, aulagas, junqueras, espinos...), y donde abunde el agua (para beber, revolcarse en el lodo o el barro y regular su temperatura). | Estos animales se adaptan a zonas muy variadas, aunque suele encontrárselos en áreas con vegetación tupida y cercana a fuentes de agua. | 0.687768 | Align-and-Shine / Wikipedia-Vikidia |
| Por último, Reding dirigiría al ejército de Granada (10 000 hombres) por Mengíbar. | Los 10 000 hombres del ejercito de Granada al mando de Reding se dirigirían a Andujar a través de Mengibar. | 0.821833 | Align-and-Shine / Wikipedia-Vikidia |

For the Ollanta pair, the filter predicted the original as simple (0.9949) and
the simplification as complex (0.9998). The texts indicate the opposite
direction, so this is a clear classifier error rather than a LaBSE rejection.
