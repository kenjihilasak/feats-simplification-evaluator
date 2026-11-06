#!/usr/bin/env python3
"""S1 rank-3 items from iDEM (Catalan, Spanish, Italian): the human simplification against two system outputs.

As the SimpEval-2022 items in English, these give per-axis human judgements on real system outputs, to evaluate the
FEATS scorers outside the synthetic degradations. Three steps:

`select` (CPU): iDEM originals of 6-60 tokens that no item or control of the language's degradation round uses (so no
reviewer sees a sentence twice), one pair per original; three more pairs per language serve as few-shot examples and
are never shown. `--count` caps the items per language (default: enough for about 500 items per reviewer).

`generate` (API): each original is simplified by Gemini (`gemini-3.8-flash`) and GPT (`gpt-6.1-terra`, no
reasoning) with the same generic Easy-to-Read prompt and the same three few-shot pairs, at temperature 0.2. The prompt
is not tied to an axis, so the item measures how the system simplifies, not whether it follows an instruction.
Outputs are cached in `generations.jsonl`; reruns call the APIs only for missing ones.

`build` (CPU): the item axis comes from the strategies a person annotated on the iDEM pair (the six E2R labels,
COMP and SYNT included); among them the axis with fewer items so far, so the axes stay balanced; ties go to the order
OMIT, SYN, MOD, EXPL, COMP, SYNT. Pairs with no annotated strategy go to ILLOC when the human version hosts a direct
act, else to MEANING and FLUENCY alternately. Versions are shuffled as X/Y/Z; systems live only in the key.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import time
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from phase6_degraded_corpus.src.annotation.build_s1_multilingual import displayed
from phase6_degraded_corpus.src.annotation.build_s1_round import item
from phase6_degraded_corpus.src.common.contracts import read_jsonl, stable_key, write_jsonl

SEED = 20261106
SOURCE = "idem"
DATASET = Path("raw/idem_&_saaq_al_bambuu/dataset.csv")
RUN = Path("phase6_degraded_corpus/runs/idem_s1_v1")
ROUNDS = Path("phase6_degraded_corpus/runs")
SECRETS = Path("/scratch/pjbd103/.secrets")
LANGS = {"ca": "Catalan", "es": "Spanish", "it": "Italian"}
TARGET = 500  # items per reviewer, controls included
STRATEGIES = {"Omission": "OMIT", "Synonymy": "SYN", "Modulation": "MOD", "Explanation": "EXPL",
              "Compression": "COMP", "Syntactic Change": "SYNT"}
AXIS_ORDER = ("OMIT", "SYN", "MOD", "EXPL", "COMP", "SYNT")
SYSTEMS = {"gemini": "gemini-3.8-flash", "gpt": "gpt-6.1-terra"}
FEWSHOT = 3
TEMPERATURE = 0.2


def norm(text: str) -> str:
    return re.sub(r"\W+", " ", text).casefold().strip()


def round_originals(lang: str) -> set[str]:
    d = ROUNDS / f"annotation_{lang}_v3"
    rows = read_jsonl(d / "s1_items.jsonl") + read_jsonl(d / "s1_controls.jsonl")
    return {norm(r["original"]) for r in rows}


def select(lang: str, count: int | None) -> dict:
    used = round_originals(lang)
    with DATASET.open(encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["language"] == lang and r["source_corpus"] == "iDEM"]
    seen, pool = set(), []
    for r in rows:
        o, s = r["source_text"].strip(), r["simplified_text"].strip()
        key = norm(o)
        if key in seen or key in used or not 6 <= len(o.split()) <= 60 or norm(s) == key or not s:
            continue
        seen.add(key)
        pool.append({"pair_id": r["pair_id"], "original": o, "human": s,
                     "strategies": sorted(STRATEGIES[k] for k in STRATEGIES if r.get(k) == "1")})
    pool.sort(key=lambda r: stable_key(SEED, f"{lang}:{r['pair_id']}"))
    shots, pool = pool[:FEWSHOT], pool[FEWSHOT:]
    n = len(read_jsonl(ROUNDS / f"annotation_{lang}_v3/s1_items.jsonl")) + len(read_jsonl(ROUNDS / f"annotation_{lang}_v3/s1_controls.jsonl"))
    want = count if count is not None else max(0, TARGET - n)
    return {"language": lang, "few_shot": shots, "items": pool[:want], "free_originals": len(pool) + len(shots),
            "round_items": n, "requested": want}


def prompt(lang: str, shots: list[dict], original: str) -> tuple[str, str]:
    name = LANGS[lang]
    system = (f"You simplify {name} texts into Easy-to-Read {name} for people with reading or intellectual difficulties. "
              f"Keep the information the reader needs, use simple words and short, clear sentences, and write only in {name}. "
              "Answer with the simplified text only, without comments, quotes or labels.")
    examples = "\n\n".join(f"Text: {s['original']}\nEasy-to-Read: {s['human']}" for s in shots)
    return system, f"{examples}\n\nText: {original}\nEasy-to-Read:"


def _post(url: str, body: dict, headers: dict) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", **headers})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < 5:
                time.sleep(2 ** attempt * 3)
                continue
            raise RuntimeError(f"HTTP {e.code}: {e.read()[:300]!r}") from None
        except (urllib.error.URLError, TimeoutError):
            if attempt < 5:
                time.sleep(2 ** attempt * 3)
                continue
            raise


def call(system_name: str, system: str, user: str) -> str:
    if system_name == "gemini":
        key = (SECRETS / "gemini_api_key").read_text().strip()
        out = _post(f"https://generativelanguage.googleapis.com/v1beta/models/{SYSTEMS['gemini']}:generateContent?key={key}",
                    {"systemInstruction": {"parts": [{"text": system}]}, "contents": [{"role": "user", "parts": [{"text": user}]}],
                     "generationConfig": {"temperature": TEMPERATURE, "maxOutputTokens": 1024}}, {})
        return "".join(p.get("text", "") for p in out["candidates"][0]["content"]["parts"]).strip()
    key = (SECRETS / "openai_api_key").read_text().strip()
    out = _post("https://api.openai.com/v1/responses",
                {"model": SYSTEMS["gpt"], "instructions": system, "input": user, "reasoning": {"effort": "none"},
                 "temperature": TEMPERATURE, "max_output_tokens": 1024}, {"Authorization": f"Bearer {key}"})
    return "".join(c.get("text", "") for o in out.get("output", []) if o.get("type") == "message"
                   for c in o.get("content", []) if c.get("type") == "output_text").strip()


def clean_output(text: str) -> str:
    text = re.sub(r"^\s*(Easy-to-Read|Lectura fàcil|Lectura fácil|Lettura facile)\s*:\s*", "", text.strip(), flags=re.I)
    if len(text) > 1 and text[0] in "\"“«" and text[-1] in "\"”»":
        text = text[1:-1].strip()
    return re.sub(r"\s*\n\s*", " ", text).strip()


def generate(selection: dict, cache: Path, systems=tuple(SYSTEMS), workers: int = 4) -> list[dict]:
    done = {(r["pair_id"], r["system"]): r for r in read_jsonl(cache)} if cache.exists() else {}
    jobs = [(r, s) for r in selection["items"] for s in systems if (r["pair_id"], s) not in done]

    def run(job):
        r, s = job
        system, user = prompt(selection["language"], selection["few_shot"], r["original"])
        return {"pair_id": r["pair_id"], "system": s, "model": SYSTEMS[s], "raw": call(s, system, user),
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

    with ThreadPoolExecutor(workers) as pool, cache.open("a", encoding="utf-8") as out:
        for res in pool.map(run, jobs):
            out.write(json.dumps(res, ensure_ascii=False) + "\n")
            out.flush()
            done[(res["pair_id"], res["system"])] = res
    return list(done.values())


def problems(original: str, human: str, text: str) -> list[str]:
    out = []
    if not text:
        out.append("empty")
    elif norm(text) in (norm(original), norm(human)):
        out.append("identical to the original or the human version")
    elif len(text.split()) > 3 * max(len(original.split()), 8):
        out.append("too long")
    if re.search(r"\b(Text|Easy-to-Read|Here is|Aquí tienes|Ecco)\b", text):
        out.append("prompt words in the output")
    return out


def choose_axes(items: list[dict], hosts_act) -> dict[str, tuple[str, str]]:
    assigned, out, fallback = Counter(), {}, []
    for r in items:
        cands = [a for a in r["strategies"] if a in AXIS_ORDER]
        if cands:
            axis = min(cands, key=lambda a: (assigned[a], AXIS_ORDER.index(a)))
            out[r["pair_id"]] = (axis, f"annotated on the iDEM pair: {','.join(r['strategies'])}")
            assigned[axis] += 1
        elif hosts_act(r["human"]):
            out[r["pair_id"]] = ("ILLOC", "no annotated strategy; the human version hosts a direct act")
        else:
            fallback.append(r["pair_id"])
    for i, pid in enumerate(sorted(fallback, key=lambda p: stable_key(SEED, f"fallback:{p}"))):
        out[pid] = (("MEANING", "FLUENCY")[i % 2], "no annotated strategy and no direct act; MEANING/FLUENCY alternate")
    return out


def build(selection: dict, generations: list[dict], hosts_act) -> tuple[list[dict], list[dict], dict, list[dict]]:
    lang = selection["language"]
    gen = {(g["pair_id"], g["system"]): clean_output(g["raw"]) for g in generations}
    usable, dropped = [], []
    for r in selection["items"]:
        texts = {s: gen.get((r["pair_id"], s), "") for s in SYSTEMS}
        issues = {s: problems(r["original"], r["human"], t) for s, t in texts.items()}
        if any(issues.values()) or len(set(map(norm, texts.values()))) < 2:
            dropped.append({"pair_id": r["pair_id"], "issues": {s: i for s, i in issues.items() if i} or {"both": ["same output"]}})
            continue
        usable.append({**r, "outputs": texts})
    axes = choose_axes(usable, hosts_act)
    built = []
    for n, r in enumerate(usable, 1):
        case_id = f"{lang.upper()}-ID{n:03d}"
        axis, reason = axes[r["pair_id"]]
        row = {"clean_simplification": r["human"], "original": r["original"], "canonical_pair_id": f"idem:{lang}:{r['pair_id']}",
               "canonical_original_id": f"idem:{lang}:{r['pair_id']}", "corpus": "iDEM"}
        vs = [(2.0, "human", r["human"]), (0.5, SYSTEMS["gemini"], r["outputs"]["gemini"]), (0.5, SYSTEMS["gpt"], r["outputs"]["gpt"])]
        public, key = displayed(item(axis, row, vs, "rank3"))
        labels = key["operations"]
        key = {**key, "case_id": case_id, "language": lang, "source": SOURCE, "idem_pair_id": r["pair_id"], "systems": labels,
               "human_label": next(k for k, s in labels.items() if s == "human"), "annotated_strategies": r["strategies"],
               "axis_reason": reason}
        built.append(({"case_id": case_id, "language": lang, **public}, key))
    built.sort(key=lambda pk: stable_key(SEED, f"shuffle:{pk[1]['case_id']}"))
    public, key = [p for p, _ in built], [k for _, k in built]
    meta = [{"case_id": k["case_id"], "dataset": "iDEM", "human_versions": [k["human_label"]]} for k in key]
    report = {"language": lang, "items": len(public), "dropped": len(dropped), "by_axis": dict(sorted(Counter(k["axis"] for k in key).items())),
              "free_originals": selection["free_originals"], "round_items": selection["round_items"], "models": SYSTEMS,
              "temperature": TEMPERATURE, "few_shot_pairs": [s["pair_id"] for s in selection["few_shot"]], "dropped_pairs": dropped}
    return public, key, report, meta


def illoc_checker(lang: str):
    from phase6_degraded_corpus.src.common.languages import load_nlp
    from phase6_degraded_corpus.src.selection.select_multilingual_pools import illoc_host
    nlp = load_nlp(lang, disable=("ner",))
    return lambda text: illoc_host(text, lang, nlp) is not None


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("step", choices=("select", "generate", "build"))
    p.add_argument("--language", choices=sorted(LANGS), required=True)
    p.add_argument("--count", type=int)
    p.add_argument("--systems", nargs="+", choices=sorted(SYSTEMS), default=sorted(SYSTEMS), help="generate: which systems to call")
    args = p.parse_args()
    out = RUN / args.language
    out.mkdir(parents=True, exist_ok=True)
    if args.step == "select":
        sel = select(args.language, args.count)
        (out / "selection.json").write_text(json.dumps(sel, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({k: (len(v) if isinstance(v, list) else v) for k, v in sel.items()}, indent=2))
        return
    sel = json.loads((out / "selection.json").read_text(encoding="utf-8"))
    if args.step == "generate":
        gens = generate(sel, out / "generations.jsonl", tuple(args.systems))
        print(json.dumps({"generations": len(gens), "by_system": dict(Counter(g["system"] for g in gens))}))
        return
    public, key, report, meta = build(sel, read_jsonl(out / "generations.jsonl"), illoc_checker(args.language))
    write_jsonl(out / "items.jsonl", public)
    write_jsonl(out / "meta.jsonl", meta)
    (out / "key.json").write_text(json.dumps(key, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    (out / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "dropped_pairs"}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
