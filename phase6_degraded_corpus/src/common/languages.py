"""Per-language resources for the Phase 6 rules and checkers.

English values are the ones the EN pipeline has always used, so passing `lang="en"` (the default everywhere)
leaves English output unchanged. Spanish and French values mirror them word class by word class.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Language:
    code: str
    spacy_model: str
    # EXPL: explanatory insertions.
    articles: frozenset[str]
    relative_pronouns: frozenset[str]
    definitional_verbs: frozenset[str]
    gloss_markers: tuple[str, ...]
    # MOD: an adjacent sentence that depends on the previous one.
    anaphors: frozenset[str]
    definite_articles: frozenset[str]
    # Sentence splitting.
    abbreviations: tuple[str, ...]
    # ILLOC.
    imperative_cue: re.Pattern
    modal_hedges: frozenset[str]
    approximators: frozenset[str]
    question_marks: str
    # Shared checks.
    negation: re.Pattern
    connectives: frozenset[str] = field(default_factory=frozenset)
    entity_types_factual: frozenset[str] = field(default_factory=frozenset)


EN = Language(
    code="en",
    spacy_model="en_core_web_sm",
    articles=frozenset({"a", "an", "the"}),
    relative_pronouns=frozenset({"which", "who"}),
    definitional_verbs=frozenset({"is", "are", "means"}),
    gloss_markers=("known as", "also called", "called", "meaning", "that is", "i . e .", "such as"),
    anaphors=frozenset({"he", "she", "it", "they", "him", "her", "them", "this", "that", "these", "those"}),
    definite_articles=frozenset({"the"}),
    abbreviations=("Mr.", "Mrs.", "Dr.", "St.", "Jr.", "Sr."),
    imperative_cue=re.compile(r"\b(?:should|must|need to|needs to|have to|has to|had better)\b", re.I),
    modal_hedges=frozenset({"may", "might", "could", "probably", "possibly", "perhaps", "likely", "maybe"}),
    approximators=frozenset({"about", "around", "approximately", "roughly", "nearly", "almost", "some"}),
    question_marks="?",
    negation=re.compile(r"\b(?:not|never|no|n't|none|nobody|nothing)\b", re.I),
    connectives=frozenset({
        "and", "but", "or", "so", "because", "while", "whereas", "although", "though", "which", "who",
        "whom", "whose", "where", "when", "that", "this", "these", "those", "it", "he", "she", "they",
        "him", "her", "them", "its", "his", "their", "there", "also", "then", "be", "have", "do",
        "including", "include", "call", "called", "known",
    }),
    entity_types_factual=frozenset({"DATE", "TIME", "MONEY", "PERCENT", "QUANTITY", "CARDINAL", "ORDINAL"}),
)

ES = Language(
    code="es",
    spacy_model="es_core_news_sm",
    articles=frozenset({"el", "la", "los", "las", "un", "una", "unos", "unas", "lo"}),
    relative_pronouns=frozenset({"que", "quien", "quienes", "cual", "cuales"}),
    definitional_verbs=frozenset({"es", "son", "significa", "significan", "quiere"}),
    gloss_markers=("conocido como", "conocida como", "conocidos como", "conocidas como", "también llamado",
                   "también llamada", "llamado", "llamada", "llamados", "llamadas", "es decir", "o sea",
                   "que significa", "que quiere decir", "como por ejemplo", "por ejemplo"),
    anaphors=frozenset({"él", "ella", "ellos", "ellas", "esto", "este", "esta", "estos", "estas", "eso", "ese",
                        "esa", "esos", "esas", "aquel", "aquella", "su", "sus", "lo", "la", "le", "les"}),
    definite_articles=frozenset({"el", "la", "los", "las"}),
    abbreviations=("Sr.", "Sra.", "Srta.", "Dr.", "Dra.", "Ud.", "Uds.", "D.", "Dña.", "etc.", "p. ej."),
    imperative_cue=re.compile(
        r"\b(?:debe|deben|debes|debemos|deberá|deberán|tiene que|tienen que|tienes que|hay que|"
        r"es necesario|es obligatorio|necesita|necesitan|puede|pueden)\b", re.I),
    modal_hedges=frozenset({"quizás", "quizá", "tal", "vez", "probablemente", "posiblemente", "podría", "podrían",
                            "puede", "pueden", "parece", "parecen", "seguramente", "acaso"}),
    approximators=frozenset({"aproximadamente", "alrededor", "unos", "unas", "casi", "cerca", "más", "menos",
                             "aprox"}),
    question_marks="?¿",
    negation=re.compile(r"\b(?:no|nunca|jamás|ningún|ninguno|ninguna|nadie|nada|tampoco|ni)\b", re.I),
    connectives=frozenset({
        "y", "e", "pero", "o", "u", "así", "porque", "mientras", "aunque", "que", "quien", "cual", "donde",
        "cuando", "esto", "este", "esta", "estos", "estas", "eso", "él", "ella", "ellos", "ellas", "su", "sus",
        "también", "luego", "ser", "estar", "haber", "tener", "hacer", "incluir", "llamar", "llamado", "conocido",
    }),
)

FR = Language(
    code="fr",
    spacy_model="fr_core_news_sm",
    articles=frozenset({"le", "la", "les", "l'", "l’", "un", "une", "des"}),
    relative_pronouns=frozenset({"qui", "que", "lequel", "laquelle", "lesquels", "lesquelles", "dont"}),
    definitional_verbs=frozenset({"est", "sont", "signifie", "signifient", "veut"}),
    gloss_markers=("connu sous le nom de", "connue sous le nom de", "aussi appelé", "aussi appelée",
                   "également appelé", "également appelée", "appelé", "appelée", "appelés", "appelées",
                   "c'est-à-dire", "c’est-à-dire",
                   "qui signifie", "qui veut dire", "comme par exemple", "par exemple"),
    anaphors=frozenset({"il", "elle", "ils", "elles", "ce", "cela", "ceci", "ça", "celui", "celle", "ceux",
                        "celles", "ces", "cet", "cette", "son", "sa", "ses", "leur", "leurs"}),
    definite_articles=frozenset({"le", "la", "les"}),
    abbreviations=("M.", "Mme.", "Mlle.", "Dr.", "St.", "Ste.", "etc.", "av.", "apr.", "J.-C."),
    imperative_cue=re.compile(
        r"\b(?:doit|doivent|devez|devons|dois|devra|devront|il faut|faut|il est nécessaire|"
        r"il est obligatoire|peut|peuvent|pouvez)\b", re.I),
    modal_hedges=frozenset({"peut-être", "peut", "probablement", "possiblement", "pourrait", "pourraient",
                            "semble", "semblent", "sans", "doute", "sûrement", "vraisemblablement", "aurait",
                            "auraient", "serait", "seraient"}),
    approximators=frozenset({"environ", "près", "presque", "quelque", "quelques", "autour", "approximativement",
                             "plus", "moins"}),
    question_marks="?",
    negation=re.compile(r"\b(?:ne|n'|n’|pas|jamais|aucun|aucune|personne|rien|ni|nul|nulle)\b", re.I),
    connectives=frozenset({
        "et", "mais", "ou", "donc", "car", "parce", "pendant", "tandis", "bien", "quoique", "qui", "que",
        "dont", "où", "quand", "ce", "cela", "ces", "cet", "cette", "il", "elle", "ils", "elles", "son", "sa",
        "ses", "leur", "leurs", "aussi", "puis", "être", "avoir", "faire", "inclure", "appeler", "appelé", "connu",
    }),
)

LANGUAGES = {lang.code: lang for lang in (EN, ES, FR)}


def get(code: str | None) -> Language:
    try:
        return LANGUAGES[code or "en"]
    except KeyError as error:
        raise ValueError(f"unsupported Phase 6 language: {code}") from error


def stop_words(code: str) -> frozenset[str]:
    if code == "en":
        from spacy.lang.en.stop_words import STOP_WORDS
    elif code == "es":
        from spacy.lang.es.stop_words import STOP_WORDS
    elif code == "fr":
        from spacy.lang.fr.stop_words import STOP_WORDS
    else:
        raise ValueError(code)
    return frozenset(STOP_WORDS)


def is_subject(dep: str) -> bool:
    """English spaCy uses nsubj/nsubjpass; the UD-based Spanish and French models use nsubj and nsubj:pass."""
    return dep in {"nsubj", "nsubjpass"} or dep.startswith("nsubj:")


def is_imperative_root(doc, code: str) -> bool:
    """A root verb in the imperative without its own subject.

    The small Spanish and French spaCy models tag sentence-initial imperatives badly (PROPN, ADV, infinitive), so
    outside English the caller parses the text with a lowercased first letter and this checks structure: the
    sentence opens with its root, tagged as a verb-like word, and in French with an imperative ending.
    """
    roots = [t for t in doc if t.dep_ == "ROOT"]
    if not roots:
        return False
    root = roots[0]
    if code == "en":
        return root.tag_ == "VB" and not any(is_subject(t.dep_) and t.head == root for t in doc)
    first = next((t for t in doc if not t.is_punct), None)
    if first is None or first.i != root.i:
        return False
    imperative_mood = "Imp" in first.morph.get("Mood")
    verb_like = imperative_mood or first.pos_ in {"VERB", "AUX", "ADJ", "ADV"}
    if code == "fr":
        return verb_like and (imperative_mood or first.lower_.endswith(("ez", "ons")))
    return verb_like
