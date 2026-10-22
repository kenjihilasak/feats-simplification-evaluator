// Degradation Validation guidelines: one source for the in-page panel and the guidelines page.
const AXES = ["OMIT", "SYN", "EXPL", "MOD", "ILLOC"];

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
      OMIT: { name: "Omission — unnecessary detail", rule: "The simplified text should leave out details the reader does not need.", worse: "An unnecessary detail is back.",
        examples: [["Ada was a mathematician.", "Ada, born on 10 December, was a mathematician.", "The date is not needed."]],
        tip: "With three versions: a focused sentence ranks first, one restored detail second, two restored details third." },
      SYN: { name: "Synonymy — simple words", rule: "The simplified text should use simple, common words.", worse: "A harder word is back, with the same meaning.",
        examples: [["Use a helpful method.", "Utilize a helpful method.", ""], ["Use a helpful method.", "Utilize a beneficial methodology.", "Two harder words: worse still."]],
        tip: "Change of meaning is not a SYN problem: report it as a side effect." },
      EXPL: { name: "Explanation — difficult terms explained", rule: "Difficult terms should be explained for the reader.", worse: "A useful explanation was removed.",
        examples: [["Tachycardia (a fast heartbeat) is common.", "Tachycardia is common.", ""]],
        tip: "Choose Same if both versions explain the term equally well." },
      MOD: { name: "Modulation — order of information", rule: "Information should come in an order that is easy to follow.", worse: "The main point comes late, or sentences are in a confusing order.",
        examples: [["Marie Curie was a scientist. She discovered radium.", "She discovered radium. Marie Curie was a scientist.", "“She” comes before we know who she is."],
                   ["The museum opened a gallery after years of planning.", "After many long years of careful planning, the museum opened a gallery.", "The reader waits for the main point."]],
        tip: "With three versions: clear order first, one confusing change second, both changes third." },
      ILLOC: { name: "Illocution — type of statement and certainty", rule: "Keep the kind of utterance (statement, instruction, question) and how certain it is.", worse: "A statement became an instruction, or was made uncertain.",
        examples: [["Water boils at 100 °C.", "Water might boil at 100 °C.", "The source is certain."], ["The museum opens at nine.", "Remember that the museum opens at nine.", "A plain statement became an instruction."]],
        tip: "Choose Same if the type of statement and the certainty are equivalent." },
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
      OMIT: { name: "Omisión — detalles innecesarios", rule: "El texto simplificado debe dejar fuera los detalles que el lector no necesita.", worse: "Ha vuelto un detalle innecesario.",
        examples: [["La Comisión presentó el informe.", "La Comisión presentó el informe el 12 de marzo en Bruselas.", "La fecha y el lugar no hacen falta."]],
        tip: "Con tres versiones: primero la frase centrada en lo esencial, después la que recupera un detalle y al final la que recupera dos." },
      SYN: { name: "Sinonimia — palabras sencillas", rule: "El texto simplificado debe usar palabras sencillas y frecuentes.", worse: "Ha vuelto una palabra más difícil, con el mismo significado.",
        examples: [["Usar un método útil.", "Utilizar un método útil.", ""], ["Comprar una entrada.", "Adquirir una entrada.", ""]],
        tip: "Un cambio de significado no es un problema de SYN: indícalo como efecto secundario." },
      EXPL: { name: "Explicación — términos difíciles explicados", rule: "Los términos difíciles deben explicarse para el lector.", worse: "Se ha quitado una explicación útil.",
        examples: [["La taquicardia (el corazón late muy rápido) es frecuente.", "La taquicardia es frecuente.", ""]],
        tip: "Elige Igual si las dos versiones explican el término igual de bien." },
      MOD: { name: "Modulación — orden de la información", rule: "La información debe aparecer en un orden fácil de seguir.", worse: "La idea principal llega tarde o las oraciones están en un orden confuso.",
        examples: [["Marie Curie fue una científica. Ella descubrió el radio.", "Ella descubrió el radio. Marie Curie fue una científica.", "«Ella» aparece antes de saber quién es."],
                   ["El museo abrió una sala tras años de trabajo.", "Tras muchos y largos años de trabajo cuidadoso, el museo abrió una sala.", "El lector espera demasiado a la idea principal."]],
        tip: "Con tres versiones: primero el orden claro, después un cambio confuso y al final los dos cambios." },
      ILLOC: { name: "Ilocución — tipo de enunciado y certeza", rule: "Mantén el tipo de enunciado (afirmación, instrucción, pregunta) y su grado de certeza.", worse: "Una afirmación se ha convertido en instrucción o se ha vuelto incierta.",
        examples: [["El agua hierve a 100 °C.", "El agua quizás hierve a 100 °C.", "El original es seguro."], ["El museo abre a las nueve.", "Recuerde que el museo abre a las nueve.", "Una afirmación pasó a ser una instrucción."]],
        tip: "Elige Igual si el tipo de enunciado y la certeza son equivalentes." },
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
      OMIT: { name: "Omission — détails inutiles", rule: "Le texte simplifié doit laisser de côté les détails dont le lecteur n’a pas besoin.", worse: "Un détail inutile est revenu.",
        examples: [["Ada était mathématicienne.", "Ada, née le 10 décembre, était mathématicienne.", "La date est inutile."]],
        tip: "Pour trois versions : d’abord la phrase centrée sur l’essentiel, puis celle qui rétablit un détail, puis celle qui en rétablit deux." },
      SYN: { name: "Synonymie — mots simples", rule: "Le texte simplifié doit employer des mots simples et courants.", worse: "Un mot plus difficile est revenu, avec le même sens.",
        examples: [["Utiliser une méthode utile.", "Recourir à une méthode utile.", ""], ["Acheter un billet.", "Acquérir un billet.", ""]],
        tip: "Un changement de sens n’est pas un problème de SYN : signalez-le comme effet secondaire." },
      EXPL: { name: "Explication — termes difficiles expliqués", rule: "Les termes difficiles doivent être expliqués au lecteur.", worse: "Une explication utile a été supprimée.",
        examples: [["La tachycardie (le cœur bat très vite) est fréquente.", "La tachycardie est fréquente.", ""]],
        tip: "Choisissez Identiques si les deux versions expliquent le terme aussi bien." },
      MOD: { name: "Modulation — ordre de l’information", rule: "L’information doit venir dans un ordre facile à suivre.", worse: "L’idée principale arrive tard ou les phrases sont dans un ordre confus.",
        examples: [["Marie Curie était une scientifique. Elle a découvert le radium.", "Elle a découvert le radium. Marie Curie était une scientifique.", "« Elle » apparaît avant qu’on sache de qui il s’agit."],
                   ["Le musée a ouvert une galerie après des années de préparation.", "Après de longues années de préparation minutieuse, le musée a ouvert une galerie.", "Le lecteur attend trop l’idée principale."]],
        tip: "Pour trois versions : d’abord l’ordre clair, puis un changement confus, puis les deux changements." },
      ILLOC: { name: "Illocution — type d’énoncé et certitude", rule: "Gardez le type d’énoncé (affirmation, consigne, question) et son degré de certitude.", worse: "Une affirmation est devenue une consigne ou a été rendue incertaine.",
        examples: [["L’eau bout à 100 °C.", "L’eau bout peut-être à 100 °C.", "La source est certaine."], ["Le musée ouvre à neuf heures.", "Retenez que le musée ouvre à neuf heures.", "Une simple affirmation est devenue une consigne."]],
        tip: "Choisissez Identiques si le type d’énoncé et la certitude sont équivalents." },
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
  const order = current ? [current, ...AXES.filter((x) => x !== current)] : AXES;
  const nav = AXES.map((x) => `<a href="#axis-${x}" class="g-chip${x === current ? " is-current" : ""}">${x}</a>`).join("");
  return `<div class="g-intro">${g.intro.map((p) => `<p>${esc(p)}</p>`).join("")}</div>
    <div class="g-how"><h2>${g.howTitle}</h2><ul>${g.how.map((x) => `<li>${x}</li>`).join("")}</ul></div>
    <nav class="g-nav" aria-label="${g.contents}">${nav}</nav>
    ${order.map((x) => axisHtml(lang, x)).join("")}`;
}
