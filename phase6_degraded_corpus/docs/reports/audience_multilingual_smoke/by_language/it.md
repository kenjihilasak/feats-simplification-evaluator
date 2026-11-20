# Italian: simplifications by audience and generator

[← Back to the report](../README.md) · 10 originals · Gemini = gemini-3.5-flash-lite, GPT = gpt-5.4-mini

**Strategies** are confirmed as in the FEATS pipeline: at least 2 of the 4 E2R strategy classifiers (E5, XLM-R, Qwen2.5-7B, Gemma-3-12B, each with its published thresholds) predict the strategy, and Gemma is one of them. The classifiers cover six strategies; Illocution is not detected.

## 1. Terence

> **Original:** Dopo una lunga consultazione, Ernesta e i suoi compagni conclusero che il modo migliore per gli abitanti della via era quello di realizzare un sistema per raffreddare la calda aria estiva.

| Audience | Gemini | GPT |
|---|---|---|
| **B1 adults** | Dopo una lunga riunione, Ernesta e i suoi amici decisero qual era la cosa migliore per le persone della via: creare un sistema per rinfrescare l'aria calda dell'estate.<br><sub>**Strategies:** Modulation, Synonymy</sub> | Dopo una lunga discussione, Ernesta e i suoi compagni decisero che il modo migliore per gli abitanti della strada era costruire un sistema per raffreddare l’aria calda dell’estate.<br><sub>**Strategies:** Synonymy</sub> |
| **Children 8–13** | Dopo una lunga riunione, Ernesta e i suoi amici decisero che il modo migliore per le persone della via era costruire un sistema per rinfrescare la calda aria d'estate.<br><sub>**Strategies:** Synonymy</sub> | Dopo aver parlato a lungo, Ernesta e i suoi compagni decisero che il modo migliore per le persone della via era costruire un sistema per raffreddare l’aria calda dell’estate.<br><sub>**Strategies:** Synonymy</sub> |
| **Intellectual disability** | Ernesta e i suoi amici hanno deciso una cosa importante. Per rinfrescare le case dal caldo dell'estate, volevano fare un impianto per l'aria fresca nella strada.<br><sub>**Strategies:** Modulation, Synonymy, Syntactic change</sub> | Dopo una lunga discussione, Ernesta e i suoi compagni decisero che il modo migliore per le persone della via era costruire un sistema per raffreddare l’aria calda dell’estate.<br><sub>**Strategies:** Synonymy</sub> |

## 2. PaCCSS-IT

> **Original:** Che cosa farà dunque a costoro il padrone della vigna ?

| Audience | Gemini | GPT |
|---|---|---|
| **B1 adults** | Cosa farà il padrone della vigna a queste persone?<br><sub>**Strategies:** Synonymy</sub> | Che cosa farà allora il padrone della vigna a queste persone?<br><sub>**Strategies:** Synonymy</sub> |
| **Children 8–13** | Cosa farà il padrone della vigna a queste persone?<br><sub>**Strategies:** Synonymy</sub> | Che cosa farà allora il padrone della vigna a queste persone?<br><sub>**Strategies:** Synonymy</sub> |
| **Intellectual disability** | Che cosa farà il padrone della vigna?<br><sub>**Strategies:** Compression, Omission</sub> | Che cosa farà allora il padrone della vigna a queste persone?<br><sub>**Strategies:** Synonymy</sub> |

## 3. Wikipedia-Vikidia

> **Original:** San Marino infatti non dispone di una vera e propria Costituzione; le fonti del diritto di rango costituzionale sono rappresentati dalle Antiche Consuetudini, dalle Leges Statutae Sancti Marini, gli antichi statuti del 1600 e dalla legislazione successiva (reformationes), entro cui si inserisce la Dichiarazione dei Diritti.

| Audience | Gemini | GPT |
|---|---|---|
| **B1 adults** | San Marino non ha una vera Costituzione. Le sue leggi più importanti sono antiche regole del 1600 e altre leggi fatte nel tempo, che includono anche la Dichiarazione dei Diritti.<br><sub>**Strategies:** Compression, Modulation, Omission, Synonymy</sub> | San Marino non ha una vera Costituzione. Le sue leggi più importanti sono le Antiche Consuetudini, le Leges Statutae Sancti Marini, gli antichi statuti del 1600 e le leggi successive, chiamate reformationes. In questo insieme c’è anche la Dichiarazione dei Diritti.<br><sub>**Strategies:** Compression, Modulation, Omission, Synonymy</sub> |
| **Children 8–13** | San Marino non ha una vera Costituzione. Le sue leggi più importanti si trovano in antichi statuti e in regole scritte nel corso del tempo, come la Dichiarazione dei Diritti.<br><sub>**Strategies:** Compression, Modulation, Omission, Synonymy</sub> | San Marino non ha una vera Costituzione. Le regole più importanti sono le Antiche Consuetudini, le Leges Statutae Sancti Marini, gli antichi statuti del 1600 e le leggi venute dopo. In queste regole c’è anche la Dichiarazione dei Diritti.<br><sub>**Strategies:** Compression, Modulation, Omission, Synonymy, Syntactic change</sub> |
| **Intellectual disability** | San Marino non ha una Costituzione vera e propria. Le leggi più importanti si basano su vecchie tradizioni e antiche regole del 1600.<br><sub>**Strategies:** Compression, Modulation, Omission, Synonymy</sub> | San Marino non ha una vera Costituzione. Le regole più importanti sono le Antiche Consuetudini, le Leges Statutae Sancti Marini, gli antichi statuti del 1600 e le leggi successive, chiamate reformationes. In queste regole si trova anche la Dichiarazione dei Diritti.<br><sub>**Strategies:** Compression, Modulation, Omission, Synonymy, Syntactic change</sub> |

## 4. Teacher

> **Original:** Nel deserto vivono invece alcuni esemplari caratteristici di fauna e flora.

| Audience | Gemini | GPT |
|---|---|---|
| **B1 adults** | Nel deserto vivono anche alcune piante e animali particolari.<br><sub>**Strategies:** Synonymy</sub> | Nel deserto vivono alcuni animali e piante tipici.<br><sub>**Strategies:** Compression, Synonymy</sub> |
| **Children 8–13** | Nel deserto vivono anche piante e animali speciali.<br><sub>**Strategies:** Synonymy</sub> | Nel deserto vivono alcuni animali e piante tipici.<br><sub>**Strategies:** Compression, Synonymy</sub> |
| **Intellectual disability** | Nel deserto vivono anche piante e animali.<br><sub>**Strategies:** Compression, Synonymy</sub> | Nel deserto vivono alcuni animali e piante tipici.<br><sub>**Strategies:** Compression, Synonymy</sub> |

## 5. iDEM

> **Original:** Benefici in favore dei lavoratori sordomuti e invalidi Utilizza il servizio Il servizio permette di inviare la domanda di riconoscimento del beneficio di due mesi di contribuzione figurativa a fini pensionistici e contributivi per lavoratori sordomuti e invalidi con un'invalidità superiore al 74%.

| Audience | Gemini | GPT |
|---|---|---|
| **B1 adults** | Questo servizio permette ai lavoratori sordi e invalidi (con un'invalidità superiore al 74%) di fare domanda per ricevere due mesi di contributi in più per la pensione.<br><sub>**Strategies:** Compression, Modulation, Synonymy, Syntactic change</sub> | Benefits for deaf-mute and disabled workers  Use the service. The service lets you send the request to get the benefit of two months of credited contributions for pension and social security purposes for deaf-mute and disabled workers with a disability of more than 74%. ⚠️ *wrong language*<br><sub>**Strategies:** Compression, Modulation, Synonymy, Syntactic change</sub> |
| **Children 8–13** | Questo servizio ti permette di chiedere un aiuto speciale per la pensione. È dedicato ai lavoratori sordi e alle persone con una disabilità superiore al 74 per cento. Con questo servizio puoi fare la domanda per ricevere due mesi di contributi in più per la pensione.<br><sub>**Strategies:** Compression, Modulation, Omission, Synonymy, Syntactic change</sub> | Vantaggi per i lavoratori sordi e con disabilità  Usa questo servizio. Il servizio permette di inviare la domanda per ottenere 2 mesi di contributi figurativi per la pensione e per i contributi, per i lavoratori sordi e con una disabilità superiore al 74%.<br><sub>**Strategies:** Compression, Modulation, Synonymy</sub> |
| **Intellectual disability** | Con questo servizio puoi chiedere due mesi di contributi in più ogni anno se sei un lavoratore sordo o con una disabilità superiore al 74%.<br><sub>**Strategies:** Compression, Synonymy, Syntactic change</sub> | Benefici per i lavoratori sordi e con disabilità  Usa questo servizio. Il servizio permette di inviare la domanda per ottenere il riconoscimento di un beneficio di due mesi di contributi figurativi per la pensione e per i contributi. Questo beneficio è per i lavoratori sordi e con disabilità con un’invalidità superiore al 74%.<br><sub>**Strategies:** Compression, Modulation, Omission, Synonymy</sub> |

## 6. SimpitikiWiki

> **Original:** Il lapislazzuli è anche stato, e tuttora è, usato in gioielleria e nell'intaglio e nella scultura.

| Audience | Gemini | GPT |
|---|---|---|
| **B1 adults** | Il lapislazzuli è usato per fare gioielli e oggetti intagliati o scolpiti.<br><sub>**Strategies:** Omission, Synonymy, Syntactic change</sub> | Il lapislazzuli è stato, e ancora oggi è, usato per fare gioielli, intagli e sculture.<br><sub>**Strategies:** Synonymy, Syntactic change</sub> |
| **Children 8–13** | Oggi e in passato, il lapislazzuli viene usato per fare gioielli e statue.<br><sub>**Strategies:** Compression, Omission, Synonymy, Syntactic change</sub> | Il lapislazzuli è stato, e ancora oggi è, usato per fare gioielli, intagli e sculture.<br><sub>**Strategies:** Synonymy, Syntactic change</sub> |
| **Intellectual disability** | Il lapislazzuli è una pietra usata per fare gioielli e oggetti d'arte.<br><sub>**Strategies:** Explanation, Omission, Synonymy, Syntactic change</sub> | Il lapislazzuli è stato, e ancora oggi è, usato per fare gioielli, intagli e sculture.<br><sub>**Strategies:** Synonymy, Syntactic change</sub> |

## 7. AdminIt

> **Original:** Per ulteriori informazioni, si invita a presentarsi agli sportelli di questo Ufficio, in Prato della Valle n. 00/00 o a telefonare allo 000/1112223-3.

| Audience | Gemini | GPT |
|---|---|---|
| **B1 adults** | Per avere altre informazioni, potete andare agli sportelli di questo Ufficio in Prato della Valle 00/00. Oppure potete telefonare al numero 000/1112223-3.<br><sub>**Strategies:** Compression, Modulation, Synonymy</sub> | Per avere altre informazioni, si prega di andare agli sportelli di questo Ufficio, in Prato della Valle n. 00/00, oppure di telefonare allo 000/1112223-3.<br><sub>**Strategies:** Synonymy</sub> |
| **Children 8–13** | Per avere più informazioni, vieni al nostro ufficio in Prato della Valle 00/00 o chiama il numero 000/1112223-3.<br><sub>**Strategies:** Compression, Synonymy</sub> | Per avere più informazioni, vai agli sportelli di questo Ufficio, in Prato della Valle n. 00/00, oppure chiama lo 000/1112223-3.<br><sub>**Strategies:** Compression, Synonymy, Syntactic change</sub> |
| **Intellectual disability** | Vuoi saperne di più? Vieni nel nostro ufficio in Prato della Valle 00/00. Oppure chiama il numero 000/1112223-3.<br><sub>**Strategies:** Compression, Modulation, Omission, Synonymy, Syntactic change</sub> | Per avere altre informazioni, si prega di andare agli sportelli di questo Ufficio, in Prato della Valle n. 00/00, oppure di telefonare allo 000/1112223-3.<br><sub>**Strategies:** Synonymy</sub> |

## 8. Terence

> **Original:** E la cosa davvero speciale riguardo ad Alberto era che non si trattava esattamente di un cane comune - non era un Labrador e neanche uno Spaniel come quelli che avevano gli amici di Emanuele.

| Audience | Gemini | GPT |
|---|---|---|
| **B1 adults** | Alberto non era un cane comune. Non era un Labrador o uno Spaniel come quelli degli amici di Emanuele. Era un cane davvero speciale.<br><sub>**Strategies:** Compression, Modulation, Omission</sub> | La cosa davvero speciale di Alberto era che non era un cane comune. Non era un Labrador né uno Spaniel, come quelli degli amici di Emanuele.<br><sub>**Strategies:** Compression, Modulation, Omission</sub> |
| **Children 8–13** | La cosa speciale di Alberto era che non era un cane normale: non era un Labrador e neanche uno Spaniel come quelli degli amici di Emanuele.<br><sub>**Strategies:** Compression, Omission, Synonymy</sub> | La cosa davvero speciale di Alberto era che non era un cane normale. Non era un Labrador e nemmeno uno Spaniel, come quelli che avevano gli amici di Emanuele.<br><sub>**Strategies:** Compression, Omission, Synonymy</sub> |
| **Intellectual disability** | Alberto non era un cane comune. Non era come i cani degli amici di Emanuele.<br><sub>**Strategies:** Compression, Modulation, Omission</sub> | La cosa davvero speciale di Alberto era che non era un cane normale. Non era un Labrador e nemmeno uno Spaniel, come quelli che avevano gli amici di Emanuele.<br><sub>**Strategies:** Compression, Omission, Synonymy</sub> |

## 9. PaCCSS-IT

> **Original:** Che in tutto ciò ci sia una fondo di verità ?

| Audience | Gemini | GPT |
|---|---|---|
| **B1 adults** | C'è un fondo di verità in tutto questo?<br><sub>**Strategies:** Synonymy</sub> | C’è un fondo di verità in tutto questo?<br><sub>**Strategies:** Synonymy</sub> |
| **Children 8–13** | C'è un po' di verità in tutto questo?<br><sub>**Strategies:** Synonymy</sub> | C’è un po’ di verità in tutto questo?<br><sub>**Strategies:** Synonymy</sub> |
| **Intellectual disability** | È vero?<br><sub>**Strategies:** Omission</sub> | C’è un fondo di verità in tutto questo?<br><sub>**Strategies:** Synonymy</sub> |

## 10. Wikipedia-Vikidia

> **Original:** Nella Historia Ecclesiastica di Orderico Vitale si fa accenno a una coltissima matrona, poi identificata in Trotula de Ruggiero, che nel 1059 a Salerno dialogò di medicina con Rodolfo Malacorona, unica donna che possedesse una cultura tale da poter discutere con il famoso medico normanno.

| Audience | Gemini | GPT |
|---|---|---|
| **B1 adults** | Nel 1059 a Salerno, una donna colta di nome Trotula de Ruggiero parlò di medicina con il famoso medico Rodolfo Malacorona. Lo racconta lo scrittore Orderico Vitale nella sua opera Historia Ecclesiastica. Trotula era l'unica donna capace di discutere di medicina con lui.<br><sub>**Strategies:** Compression, Explanation, Modulation, Omission, Synonymy, Syntactic change</sub> | Nella Historia Ecclesiastica di Orderico Vitale si parla di una donna molto colta, poi identificata come Trotula de Ruggiero. Nel 1059, a Salerno, parlò di medicina con Rodolfo Malacorona. Era l’unica donna con una cultura così grande da poter discutere con il famoso medico normanno.<br><sub>**Strategies:** Compression, Modulation, Omission, Synonymy, Syntactic change</sub> |
| **Children 8–13** | Nel libro di storia del monaco Orderico Vitale si parla di una donna molto colta. Nel 1059, a Salerno, questa donna parlò di medicina con il famoso medico Rodolfo Malacorona. Era l'unica donna a sapere così tanta medicina da poter discutere con lui. Più tardi fu riconosciuta come Trotula de Ruggiero.<br><sub>**Strategies:** Compression, Explanation, Modulation, Omission, Synonymy, Syntactic change</sub> | Nella Historia Ecclesiastica di Orderico Vitale si parla di una donna molto colta, poi identificata come Trotula de Ruggiero. Nel 1059, a Salerno, parlò di medicina con Rodolfo Malacorona. Era l’unica donna con una cultura così grande da poter discutere con il famoso medico normanno.<br><sub>**Strategies:** Compression, Modulation, Omission, Synonymy, Syntactic change</sub> |
| **Intellectual disability** | Nel 1059 a Salerno, una donna di nome Trotula parlò di medicina con un famoso medico di nome Rodolfo. Lei era l'unica donna a sapere così tante cose sulla medicina a quel tempo.<br><sub>**Strategies:** Compression, Modulation, Omission, Synonymy, Syntactic change</sub> | Nella Historia Ecclesiastica di Orderico Vitale si parla di una donna molto colta, poi identificata come Trotula de Ruggiero. Nel 1059, a Salerno, parlò di medicina con Rodolfo Malacorona. Era l’unica donna con una cultura così grande da poter discutere con il famoso medico normanno.<br><sub>**Strategies:** Compression, Modulation, Omission, Synonymy, Syntactic change</sub> |
