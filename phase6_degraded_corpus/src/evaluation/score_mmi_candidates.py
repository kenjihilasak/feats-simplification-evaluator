#!/usr/bin/env python3
"""Apply the v2 axis checks (plan §3) to every candidate of every config, identically.

C0 raw outputs (frozen v1 scripts) are first converted to the v2 record shape with one
candidate. Each candidate gets its check vector; a row's selected candidate is the first
one (in sample order) that passes every check of its axis/operation.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import read_jsonl, write_jsonl
from phase6_degraded_corpus.src.common.languages import get as language, is_imperative_root, is_second_person, is_subject, load_nlp
from phase6_degraded_corpus.src.planning.plan_mmi_operations import split_sentences

WORD = re.compile(r"\d+(?:[.,]\d+)*|\w+(?:[-’']\w+)*|[^\w\s]")
NUMBER = re.compile(r"\d+(?:[.,]\d+)*")
NEGATION = re.compile(r"\b(?:not|never|no|n't|none|nobody|nothing)\b", re.I)
CONNECTIVES = {
    "and", "but", "or", "so", "because", "while", "whereas", "although", "though", "which", "who",
    "whom", "whose", "where", "when", "that", "this", "these", "those", "it", "he", "she", "they",
    "him", "her", "them", "its", "his", "their", "there", "also", "then", "be", "have", "do",
    "including", "include", "call", "called", "known",
}
QUESTION_START = {
    "is", "are", "was", "were", "do", "does", "did", "has", "have", "had", "can", "could", "will",
    "would", "should", "may", "might", "must", "shall", "who", "what", "when", "where", "which", "why", "how",
}
DIRECTIVE_LEXICON = {
    "note", "that", "remember", "keep", "in", "mind", "consider", "please", "know", "bear", "be",
    "aware", "you", "should", "must", "learn", "understand", "notice", "recall", "take", ",", ":",
}
HEDGE_LEXICON = {
    "might", "may", "could", "possibly", "perhaps", "probably", "likely", "maybe", "it", "is", "was",
    "believed", "thought", "said", "that", "seems", "seem", "seemed", "appears", "appear", "appeared",
    "to", "have", "has", "had", "be", "been", "reportedly", "some", "people", "say", "according",
    "apparently", "presumably", "supposedly", "would", "can", ",",
}
MODAL_HEDGES = {"may", "might", "could", "probably", "possibly", "perhaps", "likely", "maybe"}
APPROXIMATORS = {"about", "around", "approximately", "roughly", "nearly", "almost", "some"}
AUXILIARIES = {"is", "are", "was", "were", "be", "been", "has", "have", "had", "do", "does", "did", "will", "can"}


def tokens(text: str) -> list[str]:
    return [t.casefold() for t in WORD.findall(text or "")]


def signature(text: str) -> list[str]:
    return re.findall(r"\w+", (text or "").casefold())


def diff_blocks(a: list[str], b: list[str]) -> list[tuple[str, list[str], list[str]]]:
    ops = difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes()
    return [(op, a[i1:i2], b[j1:j2]) for op, i1, i2, j1, j2 in ops if op != "equal"]


def overlap(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, tokens(a), tokens(b), autojunk=False).ratio()


class Checkers:
    """NLI, acceptability and spaCy, loaded once.

    Acceptability is the CoLA acceptable-class probability in English (`acceptability_kind: classifier`). No
    Spanish or French CoLA classifier exists, so those languages use SLOR (`acceptability_kind: slor`): the
    causal-LM log-probability minus the unigram log-probability, per word (Lau et al., 2017). Both are used only
    relative to the clean text and to thresholds calibrated on the same scale.
    """

    def __init__(self, pools_config: dict, device: str):
        import torch
        from transformers import AutoModelForCausalLM, AutoModelForSequenceClassification, AutoTokenizer

        self.torch = torch
        self.device = torch.device(device)
        self.lang = pools_config.get("language", "en")
        self.res = language(self.lang)
        self.kind = pools_config.get("acceptability_kind", "classifier")
        cache = Path(pools_config["cache_dir"]) / "hub"

        def load(model_id: str, revision: str, causal: bool = False, path: str | None = None):
            path = Path(path) if path else cache / f"models--{model_id.replace('/', '--')}" / "snapshots" / revision
            tok = AutoTokenizer.from_pretrained(path, local_files_only=True)
            if causal:
                model = AutoModelForCausalLM.from_pretrained(path, local_files_only=True, torch_dtype=torch.bfloat16)
            else:
                model = AutoModelForSequenceClassification.from_pretrained(path, local_files_only=True)
            return tok, model.to(self.device).eval()

        self.nli_tok, self.nli = load(pools_config["nli_model"], pools_config["nli_revision"])
        self.nli_ids = {k: int(self.nli.config.label2id[k]) for k in ("entailment", "neutral", "contradiction")}
        self.cola_tok, self.cola = load(pools_config["acceptability_model"], pools_config["acceptability_revision"],
                                        causal=self.kind == "slor", path=pools_config.get("acceptability_path"))
        self.nlp = load_nlp(self.lang)
        self.batch = pools_config.get("checker_batch_size", 64)

    def nli_probs(self, premises: list[str], hypotheses: list[str]) -> list[dict]:
        out = []
        with self.torch.inference_mode():
            for i in range(0, len(premises), self.batch):
                enc = self.nli_tok(premises[i:i + self.batch], hypotheses[i:i + self.batch], padding=True,
                                   truncation=True, max_length=512, return_tensors="pt").to(self.device)
                probs = self.nli(**enc).logits.softmax(-1).float().cpu()
                out += [{k: float(p[idx]) for k, idx in self.nli_ids.items()} for p in probs]
        return out

    def acceptability(self, texts: list[str]) -> list[float]:
        if self.kind == "slor":
            return self.slor(texts)
        out = []
        with self.torch.inference_mode():
            for i in range(0, len(texts), self.batch):
                enc = self.cola_tok(texts[i:i + self.batch], padding=True, truncation=True,
                                    max_length=512, return_tensors="pt").to(self.device)
                out += self.cola(**enc).logits.softmax(-1)[:, 0].float().cpu().tolist()
        return out

    def slor(self, texts: list[str]) -> list[float]:
        from wordfreq import word_frequency
        import math

        tok, lm = self.cola_tok, self.cola
        start = tok.eos_token_id if tok.bos_token_id is None else tok.bos_token_id
        out = []
        with self.torch.inference_mode():
            for i in range(0, len(texts), self.batch):
                chunk = texts[i:i + self.batch]
                ids = [[start] + tok(t, add_special_tokens=False)["input_ids"][:510] for t in chunk]
                width = max(map(len, ids))
                pad = tok.pad_token_id if tok.pad_token_id is not None else start
                batch = self.torch.tensor([x + [pad] * (width - len(x)) for x in ids], device=self.device)
                mask = self.torch.tensor([[1] * len(x) + [0] * (width - len(x)) for x in ids], device=self.device)
                logp = lm(input_ids=batch, attention_mask=mask).logits[:, :-1].float().log_softmax(-1)
                target = logp.gather(-1, batch[:, 1:].unsqueeze(-1)).squeeze(-1) * mask[:, 1:]
                for text, total in zip(chunk, target.sum(-1).cpu().tolist()):
                    words = [w.casefold() for w in re.findall(r"[^\W\d_]+(?:[-’'][^\W\d_]+)*", text)] or [text]
                    unigram = sum(math.log(max(word_frequency(w, self.lang), 1e-8)) for w in words)
                    out.append((total - unigram) / len(words))
        return out

    def content_lemmas(self, text: str) -> set[str]:
        connectives = CONNECTIVES if self.lang == "en" else self.res.connectives
        return {
            t.lemma_.casefold() for t in self.nlp(text)
            if t.is_alpha and not t.is_stop and t.lemma_.casefold() not in connectives and t.pos_ != "PRON"
        }

    def proper_nouns(self, text: str) -> set[str]:
        return {t.text.casefold() for t in self.nlp(text) if t.pos_ == "PROPN"}


def check_meaning(row, cand, feats, cfg) -> dict:
    blocks = diff_blocks(tokens(row["clean_simplification"]), tokens(cand))
    inserted = [t for _, _, new in blocks for t in new if re.match(r"\w", t)]
    original_tokens = set(tokens(row["original"]))
    checks = {
        "one_edit_block": len(blocks) == 1,
        "contradicts_original": feats["nli_original_degraded"]["contradiction"] >= 0.5,
        "fluency_kept": feats["acceptability"] >= row["clean_acceptability"] - cfg["delta"],
    }
    if row.get("meaning_type") in {"entity", "property"}:
        checks["replacement_not_in_original"] = not inserted or not set(inserted) <= original_tokens
    return checks


def check_mod(row, cand, feats, cfg, ck: Checkers) -> dict:
    clean = row["clean_simplification"]
    lem_c, lem_d = ck.content_lemmas(clean), ck.content_lemmas(cand)
    original_only = ck.content_lemmas(row["original"]) - lem_c
    same_count = row.get("operation", "").startswith("mod_")
    n_cand, n_clean = len(split_sentences(cand, ck.lang)), len(split_sentences(clean, ck.lang))
    negation = NEGATION if ck.lang == "en" else ck.res.negation
    return {
        "sentence_count_expected": n_cand == n_clean if same_count else n_cand == n_clean - 1,
        "content_lemmas_within_2": len(lem_c ^ lem_d) <= 2,
        "numbers_identical": sorted(NUMBER.findall(cand)) == sorted(NUMBER.findall(clean)),
        "negation_identical": len(negation.findall(cand)) == len(negation.findall(clean)),
        "proper_nouns_kept": all(p in cand.casefold() for p in ck.proper_nouns(clean)) and all(p in clean.casefold() for p in ck.proper_nouns(cand)),
        "no_original_leak": not (lem_d - lem_c) & original_only,
        "entails_both_ways": min(feats["nli_clean_degraded"]["entailment"], feats["nli_degraded_clean"]["entailment"]) >= 0.5,
        "acceptable": acceptable_enough(row, feats, cfg),
        **mod_movement(row.get("operation", ""), clean, cand, ck),
    }


def mod_movement(op: str, clean: str, cand: str, ck) -> dict:
    """The requested reordering must actually happen, not a trivial shift of one or two words."""
    if op == "mod_front_heavy":
        for before, after in zip(split_sentences(clean, ck.lang), split_sentences(cand, ck.lang)):
            if before != after:
                subject = [t for t in ck.nlp(before) if is_subject(t.dep_)]
                first = subject[0].text.casefold() if subject else tokens(before)[0].casefold()
                moved = [t.casefold() for t in tokens(after)]
                words = [t for t in ck.nlp(after) if not t.is_punct]
                # "..., it was." / "..., he is best known.": fronting the complement strands the verb.
                stranded = bool(words) and words[-1].pos_ in {"AUX", "VERB"}
                return {"fronted_phrase_ge_4_tokens": first in moved and moved.index(first) >= 4, "verb_not_stranded": not stranded}
        return {"fronted_phrase_ge_4_tokens": False}
    if op == "mod_bury_topic":
        for before, after in zip(split_sentences(clean, ck.lang), split_sentences(cand, ck.lang)):
            if before != after:
                subject = [t for t in ck.nlp(before) if is_subject(t.dep_)]
                if not subject:
                    return {"topic_moved_to_end": False}
                head = subject[0].text.casefold()
                doc = ck.nlp(after)
                root = next((t.i for t in doc if t.dep_ == "ROOT"), None)
                where = next((t.i for t in doc if t.text.casefold() == head), None)
                return {"topic_moved_to_end": root is not None and where is not None and where > root}
        return {"topic_moved_to_end": False}
    return {}


def acceptable_enough(row: dict, feats: dict, cfg: dict) -> bool:
    """Absolute τ, or no worse than the clean text by more than δ (merges and questions score lower on CoLA)."""
    return feats["acceptability"] >= min(cfg["tau_accept"], row["clean_acceptability"] - cfg["delta"])


ILLOC_V4 = {"illoc_directive_to_impersonal", "illoc_question_to_indirect", "illoc_address_to_impersonal"}
# An indirect question must embed the question under a verb of asking or "the question is", then if/whether or a
# wh-word. Without that, the model has answered the question ("Does any subset sum to zero?" -> "A subset sums to
# zero.") or used it as a subject ("Si può trovare una soluzione è una questione.").
_WH = {
    "en": r"whether|if|what|how|why|where|when|who|which",
    "es": r"si|qué|cómo|por qué|dónde|cuándo|quién|quiénes|cuál|cuáles|cuánto|cuántos|cuántas",
    "fr": r"si|s['’]|ce que|ce qui|comment|pourquoi|où|quand|qui|quel|quelle|quels|quelles|combien",
    "it": r"se|come|quale|quali|qual|cosa|che cosa|perché|dove|quando|chi|quanto|quanti|quante",
    "ca": r"si|què|com|per què|on|quan|qui|quin|quina|quins|quines|quant|quants",
    "ru": r"ли|что|как|почему|где|когда|кто|какой|какая|какое|какие|сколько|зачем",
    "ar": r"إذا|هل|ماذا|كيف|لماذا|أين|متى|من|ما",
}
_ASK = {
    "en": r"asks?|asked|asking|wonders?|question (?:is|of|as to)|to know",
    "es": r"se pregunta|se preguntará|se preguntaba|se consulta|pregunta es|cuestión es|se desea saber|saber",
    "fr": r"demande|demandé|demandée|question est|question de|savoir",
    "it": r"chiede|chiesto|domanda|domanda è|questione è|sapere",
    "ca": r"demana|pregunta|preguntava|qüestió és|saber",
    "ru": r"спрашива\w*|вопрос в том|вопрос о том|узнать|интересует",
    "ar": r"يسأل|يُسأل|يتساءل|السؤال|معرفة",
}
INDIRECT_MARKERS = {lang: rf"(?:^|\W)(?:{_ASK[lang]})(?:\W.*?)?(?:^|\W)(?:{_WH[lang]})(?=\W|$)" for lang in _WH}
QUOTE_CHARS = "\"'“”«»„‘’"


CATALAN_ELISION = re.compile(r"\b(?:es|se)\s+(?=h?[aeiouàèéíòóú])", re.I)  # "es utilitzen" -> "s'utilitzen"


def known_words(cand: str, sources: str, lang: str) -> bool:
    """Every word the model added exists in the language (wordfreq) or in the source texts; Catalan also elides."""
    from wordfreq import zipf_frequency

    seen = {w.casefold() for w in re.findall(r"\w+", sources)}
    new = {w.casefold() for w in re.findall(r"\w+", cand)} - seen
    if lang == "ca" and len(CATALAN_ELISION.findall(cand)) > len(CATALAN_ELISION.findall(sources)):
        return False
    return all(w.isdigit() or zipf_frequency(w, lang) > 0 for w in new)


def unaccent(word: str) -> str:
    import unicodedata
    return "".join(ch for ch in unicodedata.normalize("NFD", word) if not unicodedata.combining(ch))


def check_illoc_v4(op: str, row, cand, feats, cfg, ck: Checkers) -> dict:
    """The same act, made less direct: the edited sentence no longer addresses the reader, gives no instruction and
    asks no question; facts, numbers, negation and certainty stay; no other sentence changes."""
    clean = row["clean_simplification"]
    before, after = split_sentences(clean, ck.lang), split_sentences(cand, ck.lang)
    changed = [(b, a) for b, a in zip(before, after) if b != a]
    edited = changed[0][1] if len(before) == len(after) and len(changed) == 1 else cand
    parsed = ck.nlp(edited if ck.lang in {"en", "ru", "ar"} else edited[:1].lower() + edited[1:])
    lem_c, lem_d = ck.content_lemmas(clean), ck.content_lemmas(cand)
    hedges = MODAL_HEDGES if ck.lang == "en" else ck.res.modal_hedges
    negation = NEGATION if ck.lang == "en" else ck.res.negation
    inserted = {t.casefold() for _, _, new in diff_blocks(tokens(clean), tokens(cand)) for t in new}
    contradiction = max(feats["nli_clean_degraded"]["contradiction"], feats["nli_degraded_clean"]["contradiction"])
    host = changed[0][0] if changed else clean
    host_doc = ck.nlp(host if ck.lang in {"en", "ru", "ar"} else host[:1].lower() + host[1:])
    act = {"illoc_question_to_indirect": host.rstrip().endswith(tuple(ck.res.question_marks)),
           "illoc_directive_to_impersonal": is_imperative_root(host_doc, ck.lang),
           "illoc_address_to_impersonal": is_second_person(host_doc, host, ck.lang)}[op]
    return {
        # The checkers' own parse must find the act the operation removes, or the "degradation" is another edit.
        "act_in_clean": act,
        "one_sentence_changed": len(before) == len(after) and len(changed) == 1,
        "not_question": not any(q in edited for q in ck.res.question_marks),
        "not_imperative": not is_imperative_root(parsed, ck.lang),
        "no_reader_address": not is_second_person(parsed, edited, ck.lang),
        "no_exclamation": "!" not in edited and "¡" not in edited,
        "no_hedge_added": not inserted & hedges,
        "numbers_identical": sorted(NUMBER.findall(cand)) == sorted(NUMBER.findall(clean)),
        "proper_nouns_kept": all(n in cand.casefold() for n in ck.proper_nouns(clean)),
        "negation_kept": bool(negation.search(cand)) == bool(negation.search(clean)),
        "content_added_le_2": len(lem_d - lem_c) <= 2,
        "content_removed_le_2": len(lem_c - lem_d) <= 2,
        # Length is a shortcut a scorer could learn; an impersonal rewrite needs a few words, not a paraphrase.
        "token_delta_le_5": abs(len(tokens(cand)) - len(tokens(clean))) <= 5,
        "no_contradiction": contradiction < 0.5,
        "acceptable": acceptable_enough(row, feats, cfg),
        # SLOR misses broken words from a weak model ("es demdement", "heuen" in Catalan).
        "known_words": known_words(cand, clean + " " + row["original"], ck.lang),
        # The model sometimes corrects the clean text ("esta" -> "está"); the degraded version must not be a repair.
        "no_spelling_fix": not any(len(o) == len(n) and any(unaccent(a) == unaccent(b) and a != b for a, b in zip(o, n))
                                   for _, o, n in diff_blocks(tokens(clean), tokens(cand))),
        # The model sometimes rewrites every " as '; a typographic change across the text is a cue, not an edit.
        "quotes_kept": all(cand.count(q) == clean.count(q) for q in QUOTE_CHARS),
        **({"indirect_marker": bool(re.search(INDIRECT_MARKERS[ck.lang], edited, re.I))}
           if op == "illoc_question_to_indirect" else {}),
    }


def check_illoc(op: str, row, cand, feats, cfg, ck: Checkers) -> dict:
    clean = row["clean_simplification"]
    blocks = diff_blocks(tokens(clean), tokens(cand))
    token_delta = abs(len(tokens(cand)) - len(tokens(clean)))
    if op in ILLOC_V4:
        return check_illoc_v4(op, row, cand, feats, cfg, ck)
    if op.startswith("illoc_"):
        lem_c, lem_d = ck.content_lemmas(clean), ck.content_lemmas(cand)
        if op == "illoc_imperative_swap":
            # An instruction drops the subject and its modal; it may lose up to two content words but add none.
            lexical = {"token_delta_le_4": token_delta <= 4, "no_new_content": len(lem_d - lem_c) <= 1, "content_removed_le_2": len(lem_c - lem_d) <= 2}
        else:
            lexical = {"token_delta_le_2": token_delta <= 2, "content_lemmas_within_1": len(lem_c ^ lem_d) <= 1}
        checks = {
            "edit_present": bool(blocks),
            **lexical,
            "acceptable": acceptable_enough(row, feats, cfg),
        }
        question = any(q in cand for q in ck.res.question_marks)
        if op == "illoc_question_to_statement":
            checks.update({"clean_is_question": clean.rstrip().endswith("?"), "degraded_not_question": not question})
        else:
            checks["no_question_mark"] = not question
        checks["no_exclamation"] = "!" not in cand and "¡" not in cand
        inserted = {t.casefold() for _, _, new in blocks for t in new}
        hedges, approximators = (MODAL_HEDGES, APPROXIMATORS) if ck.lang == "en" else (ck.res.modal_hedges, ck.res.approximators)
        if op == "illoc_hedge_swap":
            checks["inserted_modal_hedge"] = bool(inserted & hedges)
            checks["no_approximator"] = not inserted & approximators
            checks["numbers_identical"] = sorted(NUMBER.findall(cand)) == sorted(NUMBER.findall(clean))
        if op == "illoc_imperative_swap":
            parsed = ck.nlp(cand if ck.lang == "en" else cand[:1].lower() + cand[1:])
            checks["imperative_root"] = is_imperative_root(parsed, ck.lang)
            if ck.lang != "en":
                checks["modal_removed"] = not ck.res.imperative_cue.search(cand)
        return checks
    inserted = [t for _, _, new in blocks for t in new]
    deleted = [t for _, old, _ in blocks for t in old]
    acceptable = acceptable_enough(row, feats, cfg)
    if op == "assertion_to_question":
        first = tokens(cand)[:1]
        return {"ends_with_question_mark": cand.rstrip().rstrip('"”').endswith("?"), "question_opening": bool(first) and first[0] in QUESTION_START,
                "content_lemmas_within_1": len(ck.content_lemmas(clean) ^ ck.content_lemmas(cand)) <= 1, "acceptable": acceptable}
    lexicon = DIRECTIVE_LEXICON if op == "assertion_to_directive" else HEDGE_LEXICON
    return {"edit_blocks_le_2": 1 <= len(blocks) <= 2, "inserted_in_lexicon": bool(inserted) and set(inserted) <= lexicon,
            "deleted_only_auxiliaries_or_final_punct": set(deleted) <= AUXILIARIES | {".", ","}, "not_question": not cand.rstrip().endswith("?"), "acceptable": acceptable}


def c0_records(path_meaning: Path, path_other: Path, plan: dict[str, dict]) -> list[dict]:
    records = []
    for path, key in ((path_meaning, "distorted_simplification"), (path_other, "degraded_simplification")):
        if not path.exists():
            continue
        for raw in read_jsonl(path):
            row = plan[raw["canonical_pair_id"]]
            degraded = (raw.get("generation") or {}).get(key)
            records.append({
                **{k: row.get(k) for k in ("canonical_pair_id", "canonical_original_id", "corpus", "target_axis", "operation",
                                         "original", "clean_simplification", "clean_acceptability", "meaning_type",
                                         "generator_kind", "target_span", "split")},
                "config_id": "C0", "model": "Qwen/Qwen2.5-7B-Instruct (4-bit NF4, v1 pipeline)",
                "candidates": [{"raw": raw.get("raw_response"), "parsed": raw.get("generation"),
                                "degraded": degraded.strip() if isinstance(degraded, str) else None, "generator": "llm"}],
                "c0_v1_operation": raw.get("assigned_operation") or raw.get("assigned_corruption"),
            })
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generations", type=Path, help="v2 generation file")
    parser.add_argument("--c0-dir", type=Path, help="C0_raw directory (meaning.jsonl, mod_illoc.jsonl)")
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--pools-config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()
    cfg = json.loads(args.pools_config.read_text(encoding="utf-8"))
    plan = {row["canonical_pair_id"]: row for row in read_jsonl(args.plan)}
    if args.c0_dir:
        records = c0_records(args.c0_dir / "meaning.jsonl", args.c0_dir / "mod_illoc.jsonl", plan)
    else:
        records = read_jsonl(args.generations)
    ck = Checkers(cfg, args.device)

    flat = [(ri, ci, c["degraded"]) for ri, r in enumerate(records) for ci, c in enumerate(r["candidates"]) if c["degraded"]]
    texts = [d for _, _, d in flat]
    acc = ck.acceptability(texts)
    originals = [records[ri]["original"] for ri, _, _ in flat]
    cleans = [records[ri]["clean_simplification"] for ri, _, _ in flat]
    nli_od = ck.nli_probs(originals, texts)
    nli_cd = ck.nli_probs(cleans, texts)
    nli_dc = ck.nli_probs(texts, cleans)
    feats_by = {(ri, ci): {"acceptability": acc[k], "nli_original_degraded": nli_od[k],
                           "nli_clean_degraded": nli_cd[k], "nli_degraded_clean": nli_dc[k]}
                for k, (ri, ci, _) in enumerate(flat)}

    for ri, row in enumerate(records):
        clean, original = row["clean_simplification"], row["original"]
        for ci, cand in enumerate(row["candidates"]):
            degraded = cand["degraded"]
            if not degraded:
                cand.update({"features": None, "checks": {"parsed": False}, "valid": False})
                continue
            feats = feats_by[(ri, ci)]
            axis = row["target_axis"]
            base = {"parsed": True, "not_noop": signature(degraded) != signature(clean)}
            if axis != "MOD":
                # For MOD, moving toward the Original is the intended effect; no_original_leak covers leaks.
                base["not_copy_original"] = not (signature(degraded) == signature(original)
                                                 or overlap(degraded, original) > overlap(degraded, clean) + 0.1)
            if axis == "MEANING":
                specific = check_meaning(row, degraded, feats, cfg)
            elif axis == "MOD":
                specific = check_mod(row, degraded, feats, cfg, ck)
            else:
                ops = ([row["operation"]] if row.get("config_id") != "C0"
                       else ["assertion_to_question", "assertion_to_directive", "assertion_to_hedged"])
                results = {op: check_illoc(op, row, degraded, feats, cfg, ck) for op in ops}
                # C0 used v1 operations: credit it with the v2 operation it satisfies best.
                best = max(results, key=lambda op: (all(results[op].values()), sum(results[op].values())))
                specific = results[best]
                cand["matched_operation"] = best
            cand["features"] = feats
            cand["checks"] = {**base, **specific}
            cand["valid"] = all(cand["checks"].values())
        valid = [c.get("valid", False) for c in row["candidates"]]
        row["selected_index"] = valid.index(True) if any(valid) else None
        row["check_pass_at_1"] = bool(valid) and valid[0]
        row["yield"] = any(valid)
        row["single_edit"] = _single_edit(row)
    write_jsonl(args.output, records)
    print(json.dumps({"rows": len(records), "yield": sum(r["yield"] for r in records)}, indent=2))


def _single_edit(row: dict) -> bool | None:
    idx = row["selected_index"] if row["selected_index"] is not None else 0
    cand = row["candidates"][idx] if row["candidates"] else None
    if not cand or not cand["degraded"]:
        return None
    if row["target_axis"] == "MOD":
        return cand["checks"].get("sentence_count_expected")
    return len(diff_blocks(tokens(row["clean_simplification"]), tokens(cand["degraded"]))) == 1


if __name__ == "__main__":
    main()
