# Phase 3 pilot qualitative examples

The source corpus is always shown in the final column. These examples are
diagnostic only; the pilot deliberately oversamples long pairs.

## Largest disagreements on already labelled pairs

| Original | Simplification | Predicted | Human | Scores | Source |
|---|---|---|---|---|---|
| Secondo Alleanza Verdi-Sinistra, il limite di 45 giorni è troppo breve per condurre pienamente le intercettazioni, che richiederebbero più tempo per essere svolte in modo ottimale. | Il partito Alleanza Verdi-Sinistra dice: 45 giorni non bastano per fare bene le intercettazioni. Serve più tempo. | SYN, MOD, COMP, SYNT, OMIT | SYN, MOD, EXPL, OMIT | SYN=0.993, MOD=0.988, COMP=0.867, EXPL=0.016, SYNT=0.378, OMIT=0.531 | iDEM / iDEM / it |
| La scorsa settimana il presidente Eugenio Giani ha promesso ulteriori 500mila euro che vanno aggiunti agli 1,2 milioni messi a disposizione ogni anno. | Ogni anno, la Regione Toscana dà 1,2 milioni di euro per la laguna. Eugenio Giani è il presidente della Regione Toscana. La settimana scorsa, ha promesso: quest'anno diamo 500.000 euro di più. | SYN, MOD, COMP, SYNT, OMIT | SYN, MOD | SYN=0.984, MOD=0.996, COMP=0.593, EXPL=0.067, SYNT=0.320, OMIT=0.320 | iDEM / iDEM / it |
| Se trata de un plan con acciones e iniciáticas concretas para reducir las emisiones de CO2 que pasa por acciones de eficiencia energética, cuidado del medio ambiente, mejora y eficiencia de infraestructuras y servicios de la ciudad y fomento de la movilidad sostenible. | Un plan con acciones e iniciáticas concretas para reducir la emisiones contaminantes de CO2 como: • acciones para malgastar menos energia, • cuidado del medio ambiete, • mejora de los edificios de la ciudad y sus servicios • y fomento de la movilidad sostenible. | SYN, MOD, COMP, EXPL, SYNT | SYN, MOD, EXPL, OMIT | SYN=0.946, MOD=0.990, COMP=0.164, EXPL=0.988, SYNT=0.270, OMIT=0.223 | iDEM / iDEM / es |
| En los informes aparecen acusaciones ya conocidas, como el ingreso de 7,1 millones de euros por la Fundación Ceps –por la que pasaron los fundadores de Podemos como politólogos– seis años antes de que existiera la formación. | En los informes aparecen acusaciones que son conocidas. Por ejemplo, el dinero que recibió la Fundación Ceps. En esta fundación trabajaron los creadores de Podemos 6 años antes de crear el partido político. | SYN, MOD, EXPL, SYNT | SYN, MOD, COMP | SYN=0.894, MOD=0.990, COMP=0.085, EXPL=0.500, SYNT=0.245, OMIT=0.037 | iDEM / iDEM / es |
| Según el informe número 4 redactado por Aliste, el abogado también estuvo implicado en el viaje de uno de los mandos de la brigada política a Nueva York para recabar un testimonio contra Podemos de Rafael Isea, exministro de Finanzas venezolano. | Según el informe número 4, José Aliste participó en el viaje de uno de los jefes de la polícia a Nueva York. El objetivo del viaje era conseguir información, del antiguo ministro de finanzas de Venezuela, contra Podemos. | SYN, MOD, COMP, EXPL, SYNT | SYN, MOD | SYN=0.977, MOD=0.986, COMP=0.148, EXPL=0.407, SYNT=0.320, OMIT=0.020 | iDEM / iDEM / es |
| The european experience sobre turisme urbà i cultura, elaborat el 2005 per la Comissió Europea de Viatges / OMT, indicava un creixement significatiu d’aquest tipus de turisme, amb un augment del 38% en les pernoctacions a ciutats europees entre el 1993 i el 2000. | Un estudi fet l’any 2005 per la Comissió Europea de Viatges deia que el turisme urbà i cultural va créixer molt Entre el 1993 i el 2000, les nits passades en hotels de ciutats europees van crèixer gairebé 4 de cada 10 nits més que abans. | SYN, COMP, SYNT | COMP, OMIT | SYN=0.967, MOD=0.148, COMP=0.320, EXPL=0.067, SYNT=0.469, OMIT=0.029 | iDEM / iDEM / ca |
| Aquesta xifra va augmentar al 70% el 2014, a mesura que creixia el nombre de turistes. | L' any 2014, encara més gent no estava contenta amb el turisme perquè venien més turistes a la ciutat. | SYNT | SYN, COMP | SYN=0.500, MOD=0.060, COMP=0.033, EXPL=0.060, SYNT=0.270, OMIT=0.009 | iDEM / iDEM / ca |
| És crucial tenir en compte que hi ha certs requisits i excepcions pel que fa a les condicions que motivin el desplaçament a Espanya; per tant, és important revisar la teva situació particular amb un advocat o advocada especialista. | Hi ha condicions i casos especials segons el motiu pel qual veniu a treballar a Espanya. Per això, és recomanable que parleu amb un advocat o advocada que conegui aquest tema. | SYN, SYNT | COMP | SYN=0.980, MOD=0.067, COMP=0.085, EXPL=0.037, SYNT=0.294, OMIT=0.054 | iDEM / iDEM / ca |
| خرجت إلى الفناء الداخلي أحمل أواني نورية: في حين كان بابو ولاكشمي ولوزفيميندا ينظرون إليّ من وراء زجاج نافذة المطبخ بنظرات أسى طأطأت مبتلعا بكائي. | خرجت إلى الفناء أحمل أغراض نورية، في حين كان الخدم ينظرون إليّ من وراء زجاج نافذة المطبخ بنظرات حزن، كنت أبكي. | SYN, COMP, OMIT | SYN, MOD, COMP, EXPL | SYN=0.984, MOD=0.014, COMP=0.958, EXPL=0.029, SYNT=0.014, OMIT=0.531 | Saaq al-Bambuu / Saaq al-Bambuu / ar |
| L'inclusione sociale delle persone con disabilità implica l'esercizio, su base di parità con gli altri, del diritto all'attiva partecipazione in tutti gli aspetti della vita, compresa la vita civile, sociale, economica, culturale e politica della comunità; | L'inclusione sociale delle persone con disabilità vuol dire che le persone con disabilità hanno il diritto di partecipare attivamente alla vita della comunità e in tutti i suoi ambiti: culturale, politico, sociale, ecc. | SYN, MOD, COMP, EXPL, SYNT, OMIT | SYN, MOD, COMP, SYNT | SYN=0.984, MOD=0.730, COMP=0.593, EXPL=0.977, SYNT=0.817, OMIT=0.437 | iDEM / iDEM / it |
| «Questa legge rappresenta un passo ulteriore verso un Paese più rispettoso delle libertà dei propri cittadini», ha detto per esempio il deputato di Forza Italia Pietro Pittalis. | Pietro Pittalis è un membro di Forza Italia. Ha detto: questa legge aiuta l'Italia a rispettare meglio la libertà delle persone. | SYN, MOD, SYNT | SYN, MOD, COMP | SYN=0.991, MOD=0.988, COMP=0.033, EXPL=0.018, SYNT=0.223, OMIT=0.060 | iDEM / iDEM / it |
| Con un emendamento sono stati tolti dalla lista degli atti da abrogare alcuni regi decreti che hanno stabilito dei confini tra comuni ancora oggi esistenti. | Nella proposta di legge, c'è una lista con le regole da cancellare. Una modifica ha tolto alcune vecchie regole dalla lista. Fissano i confini tra comuni che esistono ancora oggi. | SYN, MOD, COMP, SYNT | SYN, MOD, SYNT, OMIT | SYN=0.988, MOD=0.997, COMP=0.183, EXPL=0.060, SYNT=0.378, OMIT=0.148 | iDEM / iDEM / it |

## Predictions nearest to each decision threshold

### SYN (threshold 0.63)

| Original | Simplification | Predicted | Human | Scores | Source |
|---|---|---|---|---|---|
| La fidejussione bancaria o assicurativa dovrà prevedere espressamente la rinuncia al beneficio della preventiva escussione del debitore principale e la sua operatività entro 15 giorni a semplice richiesta scritta della stazione appaltante . | La fidejussione bancaria deve prevedere la rinuncia al beneficio della preventiva escussione del debitore principale e la sua operatività entro 15 giorni a semplice richiesta della stazione appaltante . | COMP | not annotated | SYN=0.622, MOD=0.294, COMP=0.320, EXPL=0.006, SYNT=0.060, OMIT=0.183 | MultiSim / PaCCSS-IT / it |
| Una proposizione subordinata è una proposizione che dipende dalla proposizione principale. | Una proposizione subordinata (o secondaria) è una proposizione che dipende dalla proposizione principale. | COMP | not annotated | SYN=0.622, MOD=0.011, COMP=0.202, EXPL=0.054, SYNT=0.029, OMIT=0.047 | MultiSim / SimpitikiWiki / it |

### MOD (threshold 0.54)

| Original | Simplification | Predicted | Human | Scores | Source |
|---|---|---|---|---|---|
| Вышла тут к нему Василиса Премудрая и говорит: | Вышла из дворца Василиса Премудрая. | COMP, OMIT | not annotated | SYN=0.148, MOD=0.531, COMP=0.223, EXPL=0.023, SYNT=0.042, OMIT=0.320 | MultiSim / RuAdaptFairytales / ru |
| Nel Caos c’era solo un grande, immenso uovo e dentro di esso cresceva Pangu, il creatore. | C’è solo un grande uovo che contiene il Caos e dentro l’uovo cresce Pangu, il creatore. | COMP | not annotated | SYN=0.270, MOD=0.531, COMP=0.133, EXPL=0.037, SYNT=0.133, OMIT=0.119 | MultiSim / Teacher / it |

### COMP (threshold 0.09)

| Original | Simplification | Predicted | Human | Scores | Source |
|---|---|---|---|---|---|
| これまでのところは旨くいっている。 | これまでのところはうまくいっている。 | SYN | not annotated | SYN=0.980, MOD=0.011, COMP=0.085, EXPL=0.007, SYNT=0.011, OMIT=0.005 | MultiSim / EasyJapaneseExtended / ja |
| 1891 turned out to be Wilde's annus mirabilis; apart from his three collections he also produced his only novel. The Picture of Dorian Gray The first version of The Picture of Dorian Gray was published as the lead story in the July 1890 edition of Lippincott's Monthly Magazine, along with five others. The story begins with a man painting a picture of Gray. | In 1891, The picture of Dorian Gray was published. | OMIT | not annotated | SYN=0.029, MOD=0.037, COMP=0.085, EXPL=0.016, SYNT=0.183, OMIT=0.500 | Align-and-Shine / Wikipedia-Vikidia / en |

### EXPL (threshold 0.40)

| Original | Simplification | Predicted | Human | Scores | Source |
|---|---|---|---|---|---|
| Os investidores poderão optar por comprar a companhia em leilão com as rotas nacionais e internacionais, batizada de Varig Operacional, ao preço mínimo de US$ 860 milhões, ou adquirir só a parte doméstica, a Varig Doméstica, ao valor-base de US$ 700 milhões (veja quadro na página ao lado). | Minutos antes do início da reunião, fechou-se o acordo que unificou a proposta do movimento Trabalhadores do Grupo Varig com a proposta da consultoria Alvarez&Marsal, contratada para conduzir o processo de recuperação judicial.Os investidores poderão optar por comprar a companhia em leilão com as rotas nacionais e internacionais ao preço mínimo de US$ 860 milhões. A companhia com as rotas nacionais e internacionais chama-se Varig Operacional. Os investidores poderão adquirir só a parte doméstic… | SYN, MOD, COMP, EXPL, SYNT, OMIT | not annotated | SYN=0.836, MOD=0.990, COMP=0.593, EXPL=0.406, SYNT=0.348, OMIT=0.562 | MultiSim / PorSimples / pt-BR |
| Воротился старик ко старухе, У старухи новое корыто. | Рассердилась старуха на старика, начала ругать его, что не попросил он у золотой рыбки даже новое корыто. Старик поклонился рыбке и ответил, что его старуха хочет новое корыто. Вернулся старик домой и увидел, что у старухи новое корыто. Поклонился старик рыбке и сказал, что мало старухе нового корыта, просит теперь она новую избу. | MOD, COMP, EXPL | not annotated | SYN=0.469, MOD=0.593, COMP=0.119, EXPL=0.407, SYNT=0.164, OMIT=0.202 | MultiSim / RuAdaptFairytales / ru |

### SYNT (threshold 0.20)

| Original | Simplification | Predicted | Human | Scores | Source |
|---|---|---|---|---|---|
| 初めて催眠に入る人の場合、とても浅い催眠状態から、覚醒してもらって、催眠状態と普通に覚醒した状態とを比べてもらうことがよくあります。 | 初めて自分で寝る状態に入る人の場合、とても浅く寝る状態から、目を開けてもらって、自分で寝る状態と普通に目を開けた状態とを比べてもらうことがよくあります。 | SYN, SYNT | not annotated | SYN=0.924, MOD=0.348, COMP=0.076, EXPL=0.047, SYNT=0.202, OMIT=0.003 | MultiSim / EasyJapaneseExtended / ja |
| In "Tantantadruj!" je bila tudi prva beseda, ki jo je izgovoril. | Tantadruj je bila prva beseda, ki jo je povedal. | SYN, COMP, SYNT, OMIT | not annotated | SYN=0.977, MOD=0.085, COMP=0.562, EXPL=0.010, SYNT=0.202, OMIT=0.406 | MultiSim / TSSlovene / sl |

### OMIT (threshold 0.32)

| Original | Simplification | Predicted | Human | Scores | Source |
|---|---|---|---|---|---|
| Вышла тут к нему Василиса Премудрая и говорит: | Вышла из дворца Василиса Премудрая. | COMP, OMIT | not annotated | SYN=0.148, MOD=0.531, COMP=0.223, EXPL=0.023, SYNT=0.042, OMIT=0.320 | MultiSim / RuAdaptFairytales / ru |
| One-third of the country is within the Andean mountain range. With of area, Bolivia is the fifth largest country in South America, after Brazil, Argentina, Peru and Colombia (and alongside Paraguay, one of the only two landlocked countries in the Americas), the 27th largest in the world, the largest landlocked country in the Southern Hemisphere and the world's seventh largest landlocked country, after Kazakhstan, Mongolia, Chad, Niger, Mali and Ethiopia. The country's population, estimated at 1… | Bolivia (also Bolivië; Aymara: Wuliwya, Quechua: Bulibiya, Guaraní: Volívia), complete the plurinational State of Bolivia (Spanish: Estado Plurinacional de Bolivia, Aymara: Wuliwya Suyu, Quechua, Guaraní: Tetã Volívia Mamallaqta: Bulibya) is a country in South America which borders Peru, Brazil, Paraguay, Argentina and Chile. | COMP, OMIT | not annotated | SYN=0.202, MOD=0.054, COMP=0.119, EXPL=0.095, SYNT=0.148, OMIT=0.320 | Align-and-Shine / Wikipedia-Vikidia / en |
