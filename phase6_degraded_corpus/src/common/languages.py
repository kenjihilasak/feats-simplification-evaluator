"""Per-language resources for the Phase 6 rules and checkers.

English values are the ones the EN pipeline has always used, so passing `lang="en"` (the default everywhere)
leaves English output unchanged. The other languages mirror them word class by word class. Arabic has no spaCy
pipeline, so `load_nlp` wraps Stanza in the few spaCy attributes the rules and checks read.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


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
    # ILLOC v4: words that address the reader (pronouns, possessives, frequent second-person verb forms).
    second_person: re.Pattern = re.compile(r"(?!x)x")
    name: str = ""


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
    second_person=re.compile(r"\b(?:you|your|yours|yourself|yourselves)\b", re.I),
    name="English",
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
    second_person=re.compile(r"\b(?:tú|usted|ustedes|vosotros|vosotras|te|ti|contigo|tu|tus|vuestro|vuestra|"
                             r"vuestros|vuestras|os)\b", re.I),
    name="Spanish",
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
    second_person=re.compile(r"(?:\b(?:vous|tu|toi|ton|ta|tes|votre|vos|te)\b|\bt['’])", re.I),
    name="French",
)

IT = Language(
    code="it",
    spacy_model="it_core_news_sm",
    articles=frozenset({"il", "lo", "la", "i", "gli", "le", "l'", "l’", "un", "uno", "una", "un'"}),
    relative_pronouns=frozenset({"che", "cui", "quale", "quali"}),
    definitional_verbs=frozenset({"è", "sono", "significa", "significano", "vuol"}),
    gloss_markers=("conosciuto come", "conosciuta come", "noto come", "nota come", "detto anche", "detta anche",
                   "chiamato", "chiamata", "chiamati", "chiamate", "cioè", "ossia", "ovvero", "vale a dire",
                   "che significa", "che vuol dire", "per esempio", "ad esempio"),
    anaphors=frozenset({"lui", "lei", "loro", "esso", "essa", "essi", "esse", "questo", "questa", "questi",
                        "queste", "quello", "quella", "quelli", "quelle", "ciò", "suo", "sua", "suoi", "sue"}),
    definite_articles=frozenset({"il", "lo", "la", "i", "gli", "le"}),
    abbreviations=("Sig.", "Dott.", "Prof.", "ecc.", "es.", "pag."),
    imperative_cue=re.compile(
        r"\b(?:deve|devono|devi|dovete|dovrà|dovranno|bisogna|occorre|è necessario|è obbligatorio|"
        r"può|possono|puoi|potete)\b", re.I),
    modal_hedges=frozenset({"forse", "probabilmente", "possibilmente", "potrebbe", "potrebbero", "sembra",
                            "sembrano", "magari"}),
    approximators=frozenset({"circa", "quasi", "intorno", "approssimativamente", "più", "meno"}),
    question_marks="?",
    negation=re.compile(r"\b(?:non|mai|nessun|nessuno|nessuna|niente|nulla|né|neanche|nemmeno)\b", re.I),
    connectives=frozenset({
        "e", "ed", "ma", "o", "oppure", "quindi", "perché", "mentre", "anche", "se", "che", "cui", "dove",
        "quando", "questo", "questa", "questi", "queste", "lui", "lei", "loro", "suo", "sua", "suoi", "sue",
        "poi", "essere", "avere", "fare", "includere", "chiamare", "chiamato", "conosciuto",
    }),
    second_person=re.compile(r"\b(?:tu|te|ti|tuo|tua|tuoi|tue|voi|vostro|vostra|vostri|vostre)\b", re.I),
    name="Italian",
)

CA = Language(
    code="ca",
    spacy_model="ca_core_news_sm",
    articles=frozenset({"el", "la", "els", "les", "l'", "l’", "un", "una", "uns", "unes", "en", "na"}),
    relative_pronouns=frozenset({"que", "qui", "qual", "quals", "on"}),
    definitional_verbs=frozenset({"és", "són", "significa", "signifiquen", "vol"}),
    gloss_markers=("conegut com", "coneguda com", "coneguts com", "conegudes com", "també anomenat",
                   "també anomenada", "anomenat", "anomenada", "anomenats", "anomenades", "és a dir", "o sigui",
                   "que significa", "que vol dir", "per exemple"),
    anaphors=frozenset({"ell", "ella", "ells", "elles", "això", "aquest", "aquesta", "aquests", "aquestes",
                        "aquell", "aquella", "aquells", "aquelles", "seu", "seva", "seus", "seves"}),
    definite_articles=frozenset({"el", "la", "els", "les"}),
    abbreviations=("Sr.", "Sra.", "Dr.", "Dra.", "etc.", "p. ex.", "núm.", "pàg."),
    imperative_cue=re.compile(
        r"\b(?:ha de|han de|has de|heu de|hem de|haurà de|cal|és necessari|és obligatori|"
        r"pot|poden|pots|podeu)\b", re.I),
    modal_hedges=frozenset({"potser", "probablement", "possiblement", "podria", "podrien", "sembla", "semblen"}),
    approximators=frozenset({"aproximadament", "gairebé", "prop", "uns", "unes", "més", "menys"}),
    question_marks="?¿",
    negation=re.compile(r"\b(?:no|mai|cap|ningú|res|ni|tampoc)\b", re.I),
    connectives=frozenset({
        "i", "però", "o", "doncs", "perquè", "mentre", "encara", "que", "qui", "on", "quan", "això", "aquest",
        "aquesta", "ell", "ella", "ells", "elles", "seu", "seva", "també", "després", "ser", "estar", "haver",
        "tenir", "fer", "incloure", "anomenar", "anomenat", "conegut",
    }),
    # Catalan public texts address the reader in the second-person plural; the parser's Person=2 covers the
    # verb forms not listed here.
    second_person=re.compile(r"(?:\b(?:tu|vostè|vostès|vosaltres|teu|teva|teus|teves|vostre|vostra|vostres|us|et|"
                             r"podeu|heu|feu|teniu|sou|aneu|trobeu|consulteu|envieu|presenteu|demaneu)\b|\bt['’])", re.I),
    name="Catalan",
)

RU = Language(
    code="ru",
    spacy_model="ru_core_news_sm",
    articles=frozenset(),
    relative_pronouns=frozenset({"который", "которая", "которое", "которые", "которого", "которой", "которых"}),
    definitional_verbs=frozenset({"это", "является", "являются", "означает", "означают"}),
    gloss_markers=("известный как", "известная как", "известное как", "известные как", "также называемый",
                   "называемый", "называемая", "то есть", "т. е.", "что означает", "например"),
    anaphors=frozenset({"он", "она", "оно", "они", "его", "её", "ее", "их", "это", "этот", "эта", "эти",
                        "тот", "та", "те", "ему", "ей", "им"}),
    definite_articles=frozenset(),
    abbreviations=("г.", "гг.", "т. д.", "т. п.", "др.", "им.", "св.", "ул."),
    imperative_cue=re.compile(
        r"\b(?:должен|должна|должно|должны|нужно|надо|необходимо|следует|обязательно|"
        r"можно|может|могут|можете)\b", re.I),
    modal_hedges=frozenset({"возможно", "вероятно", "наверное", "может", "кажется", "видимо", "пожалуй"}),
    approximators=frozenset({"около", "примерно", "почти", "приблизительно", "более", "менее", "порядка"}),
    question_marks="?",
    negation=re.compile(r"\b(?:не|нет|никогда|ни|никто|ничто|ничего|никакой)\b", re.I),
    connectives=frozenset({
        "и", "а", "но", "или", "поэтому", "потому", "так", "что", "который", "где", "когда", "это", "этот",
        "он", "она", "они", "его", "её", "их", "также", "тоже", "затем", "быть", "иметь", "называть",
        "называемый", "известный",
    }),
    second_person=re.compile(r"\b(?:вы|вас|вам|вами|ваш|ваша|ваше|ваши|вашего|вашей|ваших|ты|тебя|тебе|тобой|"
                             r"твой|твоя|твоё|твои)\b", re.I),
    name="Russian",
)

AR = Language(
    code="ar",
    spacy_model="stanza:ar",
    articles=frozenset(),
    relative_pronouns=frozenset({"الذي", "التي", "الذين", "اللذان", "اللتان", "اللواتي", "اللاتي"}),
    definitional_verbs=frozenset({"هو", "هي", "يعني", "تعني"}),
    gloss_markers=("المعروف باسم", "المعروفة باسم", "يسمى", "تسمى", "أي", "يعني", "على سبيل المثال"),
    anaphors=frozenset({"هو", "هي", "هم", "هن", "هذا", "هذه", "ذلك", "تلك", "هؤلاء", "أولئك"}),
    definite_articles=frozenset(),
    abbreviations=("د.", "م.", "هـ.", "ص."),
    imperative_cue=re.compile(r"(?:يجب|ينبغي|لا بد|من الضروري|يمكن|يستطيع)"),
    modal_hedges=frozenset({"ربما", "قد", "لعل", "يبدو", "محتمل", "غالبا"}),
    approximators=frozenset({"حوالي", "تقريبا", "نحو", "قرابة", "أكثر", "أقل"}),
    question_marks="?؟",
    negation=re.compile(r"(?:^|\s)(?:لا|لم|لن|ليس|ليست|ما|غير)(?=\s|$)"),
    connectives=frozenset({"و", "ف", "ثم", "لكن", "أو", "لأن", "بينما", "الذي", "التي", "هذا", "هذه", "هو", "هي",
                           "هم", "أيضا", "كان", "يكون"}),
    # Independent pronouns and frequent addressee forms; the parser's Person=2 covers attached pronouns.
    second_person=re.compile(r"(?:^|\s)(?:أنت|أنتِ|أنتم|أنتن|أنتما|لك|لكم|عليك|عليكم|يمكنك|يمكنكم|إليك|إليكم)(?=[\s.,،؟?!]|$)"),
    name="Arabic",
)

LANGUAGES = {lang.code: lang for lang in (EN, ES, FR, IT, CA, RU, AR)}


def get(code: str | None) -> Language:
    try:
        return LANGUAGES[code or "en"]
    except KeyError as error:
        raise ValueError(f"unsupported Phase 6 language: {code}") from error


def stop_words(code: str) -> frozenset[str]:
    import importlib

    get(code)
    return frozenset(importlib.import_module(f"spacy.lang.{code}.stop_words").STOP_WORDS)


def load_nlp(code: str, disable: tuple[str, ...] = ()):
    """spaCy for every language except Arabic, which gets Stanza behind a spaCy-like token interface."""
    model = get(code).spacy_model
    if not model.startswith("stanza:"):
        import spacy

        return spacy.load(model, disable=list(disable))
    return StanzaNLP(model.split(":", 1)[1])


class _Morph:
    def __init__(self, feats: str | None):
        self.values = dict(x.split("=", 1) for x in (feats or "").split("|") if "=" in x)

    def get(self, key: str) -> list[str]:
        return [self.values[key]] if key in self.values else []

    def __str__(self) -> str:
        return "|".join(f"{k}={v}" for k, v in self.values.items())


class _Token:
    """The spaCy token attributes the Phase 6 rules and checks read."""

    def __init__(self, doc, i: int, word, start: int, stops: frozenset[str]):
        self.doc, self.i, self.text, self.idx = doc, i, word.text, start
        self.lemma_ = word.lemma or word.text
        self.pos_ = word.upos or "X"
        self.tag_ = word.xpos or self.pos_
        self.dep_ = "ROOT" if word.deprel == "root" else (word.deprel or "dep")
        self.morph = _Morph(word.feats)
        self.lower_ = word.text.lower()
        self.is_alpha = word.text.isalpha()
        self.is_punct = self.pos_ == "PUNCT"
        self.is_stop = word.text in stops or self.lemma_ in stops
        self.like_num = self.pos_ == "NUM" or any(ch.isdigit() for ch in word.text)
        self.ent_type_ = ""
        self.whitespace_ = " "
        self.whole = word.parent is None or len(word.parent.words) == 1  # not one of several clitic words
        self._head = word.head - 1  # Stanza heads are 1-based within the sentence; 0 is the root

    @property
    def head(self):
        return self if self._head < 0 else self.doc[self._head]

    @property
    def children(self):
        return [t for t in self.doc if t._head == self.i and t is not self]


class _Doc(list):
    pass


class StanzaNLP:
    def __init__(self, code: str):
        import stanza

        root = Path(__file__).resolve().parents[3] / "cache/stanza"
        self.code, self.stops = code, stop_words(code)
        self.pipeline = stanza.Pipeline(code, dir=str(root), processors="tokenize,mwt,pos,lemma,depparse",
                                        download_method=None, verbose=False)

    def __call__(self, text: str) -> _Doc:
        doc = _Doc()
        for sentence in self.pipeline(text).sentences:
            offset = len(doc)
            for word in sentence.words:
                start = word.parent.start_char if word.parent is not None and word.parent.start_char is not None else 0
                token = _Token(doc, len(doc), word, start, self.stops)
                token._head = -1 if word.head == 0 else offset + word.head - 1
                doc.append(token)
        return doc


def is_subject(dep: str) -> bool:
    """English spaCy uses nsubj/nsubjpass; the UD-based Spanish and French models use nsubj and nsubj:pass."""
    return dep in {"nsubj", "nsubjpass"} or dep.startswith("nsubj:")


INFINITIVE_ENDINGS = {"es": ("ar", "er", "ir", "ír"), "fr": ("er", "ir", "re", "oir"), "it": ("are", "ere", "ire", "rre"),
                      "ca": ("ar", "er", "ir", "re")}


def is_imperative_root(doc, code: str, addresses_reader: bool = True) -> bool:
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
        # A bare VB root is not enough: "There can also be…" and "z should be…" have one. An imperative has no
        # subject, expletive or modal of its own ("do" only in "Do not…"), and only adverbials precede it
        # ("If you need a size, use…", "Please call…").
        children = [t for t in doc if t.head.i == root.i and t.i != root.i]
        if root.tag_ != "VB" or root.text[1:] != root.text[1:].lower():  # "VfR Mannheim a German team."
            return False
        if any(is_subject(t.dep_) or t.dep_ == "expl" for t in children):
            return False
        if any(t.dep_ == "aux" and t.lemma_.casefold() != "do" for t in children):
            return False
        allowed = {"advcl", "advmod", "punct", "intj", "discourse", "aux", "neg", "prep", "npadvmod", "mark", "cc"}
        for t in doc[:root.i]:
            while t.head.i != root.i and t.head.i != t.i:
                t = t.head
            if t.head.i != root.i or t.dep_ not in allowed:
                return False
        return True
    if code in {"ru", "ar"}:
        # These parsers tag the imperative mood reliably, wherever the root stands ("Пожалуйста, принесите…").
        return "Imp" in root.morph.get("Mood") and not any(is_subject(t.dep_) and t.head == root for t in doc)
    first = next((t for t in doc if not t.is_punct), None)
    if first is None or first.i != root.i:
        return False
    if any(is_subject(t.dep_) and t.head.i == root.i for t in doc):
        return False  # "Existe un equipo…": a tú-imperative form, but with its own (postverbal) subject
    # Lowercased brand and title names ("duracell", "xena") can be tagged imperative. A verb either gets an
    # infinitive lemma or, when the small model fails to lemmatise it, is a common word (names are rare: Zipf < 2.5).
    if not first.lemma_.casefold().endswith(INFINITIVE_ENDINGS.get(code, ("",))):
        from wordfreq import zipf_frequency
        if zipf_frequency(first.lower_, code) < 3.0:
            return False
    imperative_mood = "Imp" in first.morph.get("Mood")
    verb_like = imperative_mood or first.pos_ in {"VERB", "AUX"}
    if code == "fr":
        # The small French model tags some sentence-initial imperatives as ADJ or ADV; the ending decides.
        verb_like = verb_like or first.pos_ in {"ADJ", "ADV"}
        # "-ons" also ends names ("Simmons meurt…", tagged as a verb once lowercased); a real first-person plural
        # imperative has a second-person plural form ("allons" -> "allez").
        if first.lower_.endswith("ons") and not imperative_mood:
            from wordfreq import zipf_frequency
            if zipf_frequency(first.lower_[:-3] + "ez", "fr") == 0:
                return False
        return verb_like and (imperative_mood or first.lower_.endswith(("ez", "ons")))
    if code in {"es", "it"}:
        # Pro-drop: "Declarará este miércoles…", "Terminan el domingo…" have no subject token either. Tensed forms
        # other than the present are never imperatives, nor is a plural indicative. The tú form ("participa",
        # "porta") is also a third-person statement, so it counts only when the text addresses the reader
        # elsewhere; the usted form (subjunctive: "envíe", "consulte") always counts.
        morph = first.morph
        if set(morph.get("Tense")) & {"Fut", "Past", "Imp"} or "Cnd" in morph.get("Mood"):
            return False
        if "Ind" in morph.get("Mood") and ("Plur" in morph.get("Number") or not addresses_reader):
            return False
    if code == "ca":
        # The Catalan model tags "Porteu" as PROPN; second-person plural imperatives end in -eu or -iu, futures
        # ("Tindreu", "Podreu") in -reu.
        return imperative_mood or (first.pos_ in {"VERB", "AUX", "PROPN"} and first.lower_.endswith(("eu", "iu"))
                                   and not first.lower_.endswith("reu"))
    return verb_like


def is_second_person(doc, text: str, code: str) -> bool:
    """The text addresses the reader: a listed pronoun or verb form or, in Catalan and Arabic (second-person verb
    endings and attached pronouns), a parsed Person=2 word. Elsewhere the small models tag Person=2 on ordinary
    third-person verbs ("il dessert")."""
    if get(code).second_person.search(text):
        return True
    return code in {"ca", "ar"} and any("2" in t.morph.get("Person") for t in doc)
