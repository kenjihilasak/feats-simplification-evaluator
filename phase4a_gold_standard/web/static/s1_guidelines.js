// Degradation Validation guidelines: one source for the in-page panel and the guidelines page.
// The seven FEATS axes (v2, 30 Oct 2026). COMP and SYNT are no longer axes; their guide shows only on their old items.
const AXES = ["MEANING", "FLUENCY", "OMIT", "SYN", "EXPL", "MOD", "ILLOC"];

export const GUIDE = {
  en: {
    title: "Degradation Validation guidelines",
    open: "Guidelines", close: "Close", axisGuide: "How to judge", better: "Better", worse: "Worse", howTitle: "How to answer",
    contents: "Contents", backToTask: "Back to the task",
    intro: [
      "Judge only the axis shown on the item. X, Y and Z are neutral labels in random order.",
      "The optional AI suggestion is help, not an answer key. Read the texts first and correct it whenever needed.",
    ],
    how: [
      "Two versions: choose the better one, or <b>Same</b> if they are equally good on the axis.",
      "Three versions: give <b>1 to the best</b>, <b>2 to the middle</b> and <b>3 to the worst</b>. Equal numbers mean a tie.",
      "Report separately any other change (meaning, fluency or something else) and say which version has it.",
      "If you are unsure, tick “I am uncertain” and explain briefly in the note.",
    ],
    axes: {
      MEANING: { name: "Meaning — faithful content", rule: "The simplified text should say what the Original says.", worse: "Content is lost, or a fact now contradicts the Original.",
        examples: [["Coventry is a city in England. It is also a metropolitan borough.", "Coventry is a city in England.", "Content of the Original is lost."],
                   ["The elections are held every 5 years.", "The elections are held every 15 years.", "A fact contradicts the Original."]],
        tip: "Removing a redundant word such as “also” loses nothing: choose Same. A change in certainty (“is” → “might be”) is a Meaning change." },
      FLUENCY: { name: "Fluency — grammar", rule: "The text should be grammatical and read naturally.", worse: "It has more, or more serious, grammar errors; the meaning is the same.",
        examples: [["People already in a band.", "People already on band.", "A wrong preposition and a missing article."],
                   ["A side project is another project.", "A side project are another project.", "Broken agreement."]],
        tip: "A missing article or a wrong preposition is minor; broken agreement or swapped words is major; several errors together are worst." },
      OMIT: { name: "Omission — unnecessary detail", rule: "The simplified text should leave out details the reader does not need.", worse: "An unnecessary detail is back.",
        examples: [["Ada was a mathematician.", "Ada, born on 10 December, was a mathematician.", "The date is not needed."]],
        tip: "With three versions: a focused sentence ranks first, one restored detail second, two restored details third." },
      SYN: { name: "Synonymy — simple words", rule: "The simplified text should use simple, common words.", worse: "A harder word is back, with the same meaning.",
        examples: [["Use a helpful method.", "Utilize a helpful method.", ""], ["Use a helpful method.", "Utilize a beneficial methodology.", "Two harder words: worse still."]],
        tip: "A change of meaning is not a SYN problem: report it as a side effect. Names and titles are not judged as words." },
      EXPL: { name: "Explanation — difficult terms explained", rule: "Difficult terms should be explained for the reader.", worse: "A useful explanation was removed.",
        examples: [["Tachycardia (a fast heartbeat) is common.", "Tachycardia is common.", ""]],
        tip: "Choose Same if both versions explain the term equally well." },
      MOD: { name: "Modulation — order of information", rule: "Information should come in the order that is easiest to follow: the main point first, and each sentence after the one it depends on.", worse: "Secondary information comes first, or a sentence comes before the one it depends on.",
        examples: [["He served as President of the European Parliament from 2017 to 2019.", "From 2017 to 2019 he served as President of the European Parliament.", "The main point comes later."],
                   ["Marie Curie was a scientist. She discovered radium.", "She discovered radium. Marie Curie was a scientist.", "“She” comes before we know who she is."]],
        tip: "With three versions: the clean order first; secondary information moved to the front second; moved to the front and the sentences swapped third. Splitting a sentence is not judged here." },
      COMP: { name: "Compression — compact constructions", rule: "The simplified text should say the same thing with shorter, simpler grammatical constructions.", worse: "A longer or more complex construction is back, with the same meaning.",
        examples: [["Fewer people travelled by plane after COVID.", "Air travel saw a dramatic reduction in passenger numbers after COVID.", ""]],
        tip: "A change of meaning is not a COMP problem: report it as a side effect." },
      SYNT: { name: "Syntactic change — easy sentence structure", rule: "The simplified text should use a sentence structure that is easy to follow.", worse: "A harder structure is back (for example a nominalisation), with the same meaning.",
        examples: [["The project was delayed because the money arrived late.", "The late arrival of the money caused a delay of the project.", ""]],
        tip: "A change of meaning is not a SYNT problem: report it as a side effect." },
      ILLOC: { name: "Illocution — directness of the act", rule: "Keep the purpose of the Original (informing, instructing, asking) and express it directly, so the reader knows at once what is stated, asked or required.", worse: "The same act is expressed indirectly.",
        examples: [["Use soap and warm water.", "Soap and warm water should be used.", "The instruction became impersonal."],
                   ["Where did the name “foxtrot” come from?", "The question is where the name “foxtrot” came from.", "The question became indirect."],
                   ["You can only find it on Christmas Island.", "It is only found on Christmas Island.", "The reader is no longer addressed."]],
        tip: "A reworded version that keeps the act direct is as good: choose Same. Turning a statement into an instruction is not worse on this axis, and a change in certainty belongs to Meaning." },
    },
  },
  es: {
    title: "Guía de validación de degradaciones",
    open: "Guía", close: "Cerrar", axisGuide: "Cómo juzgar", better: "Mejor", worse: "Peor", howTitle: "Cómo responder",
    contents: "Contenido", backToTask: "Volver a la tarea",
    intro: [
      "Juzga solo el eje indicado en el ítem. X, Y y Z son etiquetas neutras en orden aleatorio.",
      "La sugerencia opcional de IA es una ayuda, no la respuesta correcta. Lee primero los textos y corrígela siempre que haga falta.",
    ],
    how: [
      "Dos versiones: elige la mejor, o <b>Igual</b> si son igual de buenas en el eje.",
      "Tres versiones: da <b>1 a la mejor</b>, <b>2 a la intermedia</b> y <b>3 a la peor</b>. Números iguales indican empate.",
      "Indica aparte cualquier otro cambio (significado, fluidez u otra cosa) y en qué versión aparece.",
      "Si dudas, marca “No estoy seguro/a” y explícalo brevemente en la nota.",
    ],
    axes: {
      MEANING: { name: "Significado — contenido fiel", rule: "El texto simplificado debe decir lo mismo que el original.", worse: "Se pierde contenido o un dato contradice ahora el original.",
        examples: [["Coventry es una ciudad de Inglaterra. También es un distrito metropolitano.", "Coventry es una ciudad de Inglaterra.", "Se pierde contenido del original."],
                   ["Las elecciones son cada 5 años.", "Las elecciones son cada 15 años.", "Un dato contradice el original."]],
        tip: "Quitar una palabra redundante como «también» no pierde nada: elige Igual. Un cambio de certeza («es» → «quizás es») es un cambio de significado." },
      FLUENCY: { name: "Fluidez — gramática", rule: "El texto debe ser gramatical y sonar natural.", worse: "Tiene más errores gramaticales, o más graves; el significado es el mismo.",
        examples: [["Para más información consulta la lista.", "Por más información consulta lista.", "Una preposición equivocada y un artículo que falta."],
                   ["Los países más pequeños tienen menos participantes.", "Las países más pequeños tienen menos participantes.", "Concordancia rota."]],
        tip: "Un artículo que falta o una preposición equivocada es leve; una concordancia rota o dos palabras intercambiadas es grave; varios errores juntos es lo peor." },
      OMIT: { name: "Omisión — detalles innecesarios", rule: "El texto simplificado debe dejar fuera los detalles que el lector no necesita.", worse: "Ha vuelto un detalle innecesario.",
        examples: [["La Comisión presentó el informe.", "La Comisión presentó el informe el 12 de marzo en Bruselas.", "La fecha y el lugar no hacen falta."]],
        tip: "Con tres versiones: primero la frase centrada en lo esencial, después la que recupera un detalle y al final la que recupera dos." },
      SYN: { name: "Sinonimia — palabras sencillas", rule: "El texto simplificado debe usar palabras sencillas y frecuentes.", worse: "Ha vuelto una palabra más difícil, con el mismo significado.",
        examples: [["Usar un método útil.", "Utilizar un método útil.", ""], ["Comprar una entrada.", "Adquirir una entrada.", ""]],
        tip: "Un cambio de significado no es un problema de SYN: indícalo como efecto secundario. Los nombres y títulos no se juzgan como palabras." },
      EXPL: { name: "Explicación — términos difíciles explicados", rule: "Los términos difíciles deben explicarse para el lector.", worse: "Se ha quitado una explicación útil.",
        examples: [["La taquicardia (el corazón late muy rápido) es frecuente.", "La taquicardia es frecuente.", ""]],
        tip: "Elige Igual si las dos versiones explican el término igual de bien." },
      MOD: { name: "Modulación — orden de la información", rule: "La información debe aparecer en el orden más fácil de seguir: primero la idea principal, y cada oración después de aquella de la que depende.", worse: "La información secundaria va primero, o una oración aparece antes que aquella de la que depende.",
        examples: [["El Hospital ofrece este programa en el nuevo edificio de Oncología.", "En el nuevo edificio de Oncología el Hospital ofrece este programa.", "La idea principal llega más tarde."],
                   ["Marie Curie fue una científica. Ella descubrió el radio.", "Ella descubrió el radio. Marie Curie fue una científica.", "«Ella» aparece antes de saber quién es."]],
        tip: "Con tres versiones: primero el orden limpio; después la que adelanta información secundaria; al final la que además invierte las oraciones. Partir una oración en dos no se juzga aquí." },
      COMP: { name: "Compresión — construcciones breves", rule: "El texto simplificado debe decir lo mismo con construcciones gramaticales más breves y sencillas.", worse: "Ha vuelto una construcción más larga o compleja, con el mismo significado.",
        examples: [["Menos gente viajó en avión después del COVID.", "El transporte aéreo experimentó una drástica reducción del número de pasajeros tras el COVID.", ""]],
        tip: "Un cambio de significado no es un problema de COMP: indícalo como efecto secundario." },
      SYNT: { name: "Cambio sintáctico — estructura de oración fácil", rule: "El texto simplificado debe usar una estructura de oración fácil de seguir.", worse: "Ha vuelto una estructura más difícil (por ejemplo, una nominalización), con el mismo significado.",
        examples: [["El proyecto se retrasó porque el dinero llegó tarde.", "La llegada tardía del dinero provocó el retraso del proyecto.", ""]],
        tip: "Un cambio de significado no es un problema de SYNT: indícalo como efecto secundario." },
      ILLOC: { name: "Ilocución — acto directo", rule: "Mantén el propósito del original (informar, instruir, preguntar) y exprésalo de forma directa, para que el lector sepa enseguida qué se afirma, se pregunta o se pide.", worse: "El mismo acto se expresa de forma indirecta.",
        examples: [["Consulta la lista completa de recomendaciones.", "Se puede consultar la lista completa de recomendaciones.", "La instrucción pasó a ser impersonal."],
                   ["¿Qué son los paneles europeos de ciudadanos?", "Se pregunta qué son los paneles europeos de ciudadanos.", "La pregunta pasó a ser indirecta."],
                   ["Podéis presentar una queja.", "Se puede presentar una queja.", "Ya no se dirige al lector."]],
        tip: "Una versión reformulada que mantiene el acto directo es igual de buena: elige Igual. Convertir una afirmación en instrucción no es peor en este eje, y un cambio de certeza corresponde a Significado." },
    },
  },
  fr: {
    title: "Consignes de validation des dégradations",
    open: "Consignes", close: "Fermer", axisGuide: "Comment juger", better: "Meilleure", worse: "Moins bonne", howTitle: "Comment répondre",
    contents: "Sommaire", backToTask: "Retour à la tâche",
    intro: [
      "Jugez uniquement l’axe indiqué sur l’élément. X, Y et Z sont des étiquettes neutres dans un ordre aléatoire.",
      "La suggestion facultative d’IA est une aide, pas un corrigé. Lisez d’abord les textes et corrigez-la chaque fois que nécessaire.",
    ],
    how: [
      "Deux versions : choisissez la meilleure, ou <b>Identiques</b> si elles sont aussi bonnes sur l’axe.",
      "Trois versions : attribuez <b>1 à la meilleure</b>, <b>2 à l’intermédiaire</b> et <b>3 à la moins bonne</b>. Des nombres égaux indiquent une égalité.",
      "Signalez séparément tout autre changement (sens, fluidité ou autre) et la version concernée.",
      "En cas de doute, cochez « Je ne suis pas sûr·e » et expliquez brièvement dans la note.",
    ],
    axes: {
      MEANING: { name: "Sens — contenu fidèle", rule: "Le texte simplifié doit dire ce que dit l’original.", worse: "Du contenu est perdu, ou un fait contredit désormais l’original.",
        examples: [["Coventry est une ville d’Angleterre. C’est aussi un district métropolitain.", "Coventry est une ville d’Angleterre.", "Du contenu de l’original est perdu."],
                   ["Les élections ont lieu tous les 5 ans.", "Les élections ont lieu tous les 15 ans.", "Un fait contredit l’original."]],
        tip: "Supprimer un mot redondant comme « aussi » ne fait rien perdre : choisissez Identiques. Un changement de certitude (« est » → « est peut-être ») est un changement de sens." },
      FLUENCY: { name: "Fluidité — grammaire", rule: "Le texte doit être grammatical et se lire naturellement.", worse: "Il contient plus d’erreurs de grammaire, ou plus graves ; le sens est le même.",
        examples: [["Il parle du livre au professeur.", "Il parle livre pour professeur.", "Une préposition erronée et un article manquant."],
                   ["Les problèmes sont importants.", "Le problèmes sont importants.", "Accord rompu."]],
        tip: "Un article manquant ou une préposition erronée est mineur ; un accord rompu ou deux mots inversés est majeur ; plusieurs erreurs ensemble, c’est le pire." },
      OMIT: { name: "Omission — détails inutiles", rule: "Le texte simplifié doit laisser de côté les détails dont le lecteur n’a pas besoin.", worse: "Un détail inutile est revenu.",
        examples: [["Ada était mathématicienne.", "Ada, née le 10 décembre, était mathématicienne.", "La date est inutile."]],
        tip: "Pour trois versions : d’abord la phrase centrée sur l’essentiel, puis celle qui rétablit un détail, puis celle qui en rétablit deux." },
      SYN: { name: "Synonymie — mots simples", rule: "Le texte simplifié doit employer des mots simples et courants.", worse: "Un mot plus difficile est revenu, avec le même sens.",
        examples: [["Utiliser une méthode utile.", "Recourir à une méthode utile.", ""], ["Acheter un billet.", "Acquérir un billet.", ""]],
        tip: "Un changement de sens n’est pas un problème de SYN : signalez-le comme effet secondaire. Les noms et les titres ne sont pas jugés comme des mots." },
      EXPL: { name: "Explication — termes difficiles expliqués", rule: "Les termes difficiles doivent être expliqués au lecteur.", worse: "Une explication utile a été supprimée.",
        examples: [["La tachycardie (le cœur bat très vite) est fréquente.", "La tachycardie est fréquente.", ""]],
        tip: "Choisissez Identiques si les deux versions expliquent le terme aussi bien." },
      MOD: { name: "Modulation — ordre de l’information", rule: "L’information doit venir dans l’ordre le plus facile à suivre : l’idée principale d’abord, et chaque phrase après celle dont elle dépend.", worse: "L’information secondaire vient en premier, ou une phrase précède celle dont elle dépend.",
        examples: [["Il a présidé le Parlement européen de 2017 à 2019.", "De 2017 à 2019 il a présidé le Parlement européen.", "L’idée principale arrive plus tard."],
                   ["Marie Curie était une scientifique. Elle a découvert le radium.", "Elle a découvert le radium. Marie Curie était une scientifique.", "« Elle » apparaît avant qu’on sache de qui il s’agit."]],
        tip: "Pour trois versions : d’abord l’ordre propre ; puis celle qui avance une information secondaire ; enfin celle qui, en plus, inverse les phrases. Couper une phrase en deux n’est pas jugé ici." },
      COMP: { name: "Compression — constructions courtes", rule: "Le texte simplifié doit dire la même chose avec des constructions grammaticales plus courtes et plus simples.", worse: "Une construction plus longue ou plus complexe est revenue, avec le même sens.",
        examples: [["Moins de gens ont pris l’avion après le COVID.", "Le transport aérien a connu une baisse spectaculaire du nombre de passagers après le COVID.", ""]],
        tip: "Un changement de sens n’est pas un problème de COMP : signalez-le comme effet secondaire." },
      SYNT: { name: "Changement syntaxique — structure de phrase facile", rule: "Le texte simplifié doit employer une structure de phrase facile à suivre.", worse: "Une structure plus difficile est revenue (par exemple une nominalisation), avec le même sens.",
        examples: [["Le projet a pris du retard parce que l’argent est arrivé tard.", "L’arrivée tardive de l’argent a provoqué le retard du projet.", ""]],
        tip: "Un changement de sens n’est pas un problème de SYNT : signalez-le comme effet secondaire." },
      ILLOC: { name: "Illocution — acte direct", rule: "Gardez le but de l’original (informer, donner une consigne, poser une question) et exprimez-le directement, pour que le lecteur sache tout de suite ce qui est affirmé, demandé ou exigé.", worse: "Le même acte est exprimé de façon indirecte.",
        examples: [["Veuillez ne pas renommer ces classes.", "Ces classes ne doivent pas être renommées.", "La consigne est devenue impersonnelle."],
                   ["D’où vient le nom « foxtrot » ?", "La question est de savoir d’où vient le nom « foxtrot ».", "La question est devenue indirecte."],
                   ["Vous pouvez le trouver sur l’île Christmas.", "On peut le trouver sur l’île Christmas.", "Le lecteur n’est plus interpellé."]],
        tip: "Une version reformulée qui garde l’acte direct est aussi bonne : choisissez Identiques. Transformer une affirmation en consigne n’est pas moins bon sur cet axe, et un changement de certitude relève du Sens." },
    },
  },
  it: {
    title: "Linee guida per la validazione delle degradazioni",
    open: "Linee guida", close: "Chiudi", axisGuide: "Come giudicare", better: "Migliore", worse: "Peggiore", howTitle: "Come rispondere",
    contents: "Indice", backToTask: "Torna al compito",
    intro: [
      "Giudica solo l’asse indicato nell’elemento. X, Y e Z sono etichette neutre in ordine casuale.",
      "Il suggerimento facoltativo dell’IA è un aiuto, non la risposta corretta. Leggi prima i testi e correggilo ogni volta che serve.",
    ],
    how: [
      "Due versioni: scegli la migliore, oppure <b>Uguali</b> se sono ugualmente buone sull’asse.",
      "Tre versioni: dai <b>1 alla migliore</b>, <b>2 all’intermedia</b> e <b>3 alla peggiore</b>. Numeri uguali indicano un pareggio.",
      "Segnala a parte qualsiasi altro cambiamento (significato, fluidità o altro) e in quale versione compare.",
      "Se hai dubbi, spunta “Non sono sicuro/a” e spiega brevemente nella nota.",
    ],
    axes: {
      MEANING: { name: "Significato — contenuto fedele", rule: "Il testo semplificato deve dire ciò che dice l’originale.", worse: "Si perde contenuto, oppure un fatto ora contraddice l’originale.",
        examples: [["Coventry è una città dell’Inghilterra. È anche un distretto metropolitano.", "Coventry è una città dell’Inghilterra.", "Si perde contenuto dell’originale."],
                   ["Le elezioni europee si tengono ogni 5 anni.", "Le elezioni europee si tengono ogni 15 anni.", "Un fatto contraddice l’originale."]],
        tip: "Togliere una parola ridondante come «anche» non fa perdere nulla: scegli Uguali. Un cambiamento di certezza («è» → «forse è») è un cambiamento di significato." },
      FLUENCY: { name: "Fluidità — grammatica", rule: "Il testo deve essere grammaticale e suonare naturale.", worse: "Ha più errori grammaticali, o più gravi; il significato è lo stesso.",
        examples: [["Visitate il sito web.", "Visitate sito web.", "Manca un articolo."],
                   ["La legge è uguale per tutti.", "Il legge è uguale per tutti.", "Accordo sbagliato."]],
        tip: "Un articolo mancante o una preposizione sbagliata è un errore lieve; un accordo sbagliato o due parole invertite è grave; più errori insieme è il caso peggiore." },
      OMIT: { name: "Omissione — dettagli non necessari", rule: "Il testo semplificato deve tralasciare i dettagli di cui il lettore non ha bisogno.", worse: "È tornato un dettaglio non necessario.",
        examples: [["Il gioco non valeva la candela.", "Il gioco non valeva la candela, almeno fino ad oggi.", "Il dettaglio aggiunto non serve."]],
        tip: "Con tre versioni: prima la frase centrata sull’essenziale, poi quella che recupera un dettaglio, infine quella che ne recupera due." },
      SYN: { name: "Sinonimia — parole semplici", rule: "Il testo semplificato deve usare parole semplici e comuni.", worse: "È tornata una parola più difficile, con lo stesso significato.",
        examples: [["Usare un metodo utile.", "Utilizzare un metodo utile.", ""],
                   ["Comprare un biglietto.", "Acquistare un biglietto.", ""]],
        tip: "Un cambiamento di significato non è un problema di SYN: segnalalo come effetto secondario. I nomi e i titoli non si giudicano come parole." },
      EXPL: { name: "Spiegazione — termini difficili spiegati", rule: "I termini difficili devono essere spiegati al lettore.", worse: "È stata tolta una spiegazione utile.",
        examples: [["La tachicardia (il cuore batte molto veloce) è frequente.", "La tachicardia è frequente.", ""]],
        tip: "Scegli Uguali se le due versioni spiegano il termine ugualmente bene." },
      MOD: { name: "Modulazione — ordine dell’informazione", rule: "L’informazione deve arrivare nell’ordine più facile da seguire: prima l’idea principale, e ogni frase dopo quella da cui dipende.", worse: "L’informazione secondaria viene prima, oppure una frase compare prima di quella da cui dipende.",
        examples: [["Il Senato ha approvato la legge il 1 aprile.", "Il 1 aprile il Senato ha approvato la legge.", "L’idea principale arriva più tardi."],
                   ["Marie Curie era una scienziata. Lei scoprì il radio.", "Lei scoprì il radio. Marie Curie era una scienziata.", "«Lei» compare prima di sapere chi è."]],
        tip: "Con tre versioni: prima l’ordine pulito; poi quella che anticipa un’informazione secondaria; infine quella che, in più, inverte le frasi. Dividere una frase in due non si giudica qui." },
      ILLOC: { name: "Illocuzione — atto diretto", rule: "Mantieni lo scopo dell’originale (informare, dare istruzioni, chiedere) ed esprimilo in modo diretto, così che il lettore capisca subito che cosa si afferma, si chiede o si richiede.", worse: "Lo stesso atto è espresso in modo indiretto.",
        examples: [["Lavare e tritare il prezzemolo.", "Il prezzemolo deve essere lavato e tritato.", "L’istruzione è diventata impersonale."],
                   ["Come funziona il Parlamento europeo?", "Si chiede come funziona il Parlamento europeo.", "La domanda è diventata indiretta."],
                   ["Questo è un tuo problema.", "Questo è un problema.", "Il lettore non è più interpellato."]],
        tip: "Una versione riformulata che mantiene l’atto diretto è ugualmente buona: scegli Uguali. Trasformare un’affermazione in un’istruzione non è peggio su questo asse, e un cambiamento di certezza riguarda il Significato." },
    },
  },
};

export const guide = (lang) => GUIDE[lang] || GUIDE.en;

function esc(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

/** One axis: rule, what "worse" means, better/worse examples and a tip. */
export function axisHtml(lang, axis, heading = true) {
  const g = guide(lang), a = g.axes[axis];
  if (!a) return "";
  const examples = a.examples.map(([better, worse, why]) => `
    <div class="g-example">
      <div class="g-better"><span>${g.better}</span>${esc(better)}</div>
      <div class="g-worse"><span>${g.worse}</span>${esc(worse)}</div>
      ${why ? `<p class="g-why">${esc(why)}</p>` : ""}
    </div>`).join("");
  return `<section class="g-axis" id="axis-${axis}" data-axis="${axis}">
    ${heading ? `<h2><span class="g-code">${axis}</span> ${esc(a.name)}</h2>` : ""}
    <p class="g-rule">${esc(a.rule)}</p>
    <p class="g-worse-means"><b>${g.worse}:</b> ${esc(a.worse)}</p>
    ${examples}
    <p class="g-tip">${esc(a.tip)}</p>
  </section>`;
}

/** The whole guide: intro, how to answer, then every axis (the current one first when given). */
export function fullHtml(lang, current = null) {
  const g = guide(lang);
  const shown = current && !AXES.includes(current) ? [current, ...AXES] : AXES;
  const order = current ? [current, ...shown.filter((x) => x !== current)] : shown;
  const nav = shown.map((x) => `<a href="#axis-${x}" class="g-chip${x === current ? " is-current" : ""}">${x}</a>`).join("");
  return `<div class="g-intro">${g.intro.map((p) => `<p>${esc(p)}</p>`).join("")}</div>
    <div class="g-how"><h2>${g.howTitle}</h2><ul>${g.how.map((x) => `<li>${x}</li>`).join("")}</ul></div>
    <nav class="g-nav" aria-label="${g.contents}">${nav}</nav>
    ${order.map((x) => axisHtml(lang, x)).join("")}`;
}
