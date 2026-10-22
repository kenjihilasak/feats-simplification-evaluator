"""Create blinded S1 suggestions with Gemini or OpenAI; never reads an S1 key."""
from __future__ import annotations
import argparse, json, os, time, urllib.error, urllib.request
from pathlib import Path

DEFINITIONS={"OMIT":"Leave out unnecessary detail; worse means unnecessary detail is back.","SYN":"Use simple words; worse means a harder word is back.","EXPL":"Explain difficult terms; worse means an explanation was removed.","MOD":"Order information clearly; worse means the main point comes late or the order is confusing.","ILLOC":"Keep utterance type and certainty; worse means these changed."}

def read_rows(paths):
    for path in paths:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip(): yield json.loads(line)

def prompt(item):
    labels=list(item["versions"])
    task=("Choose X, Y, or Same for the better version." if item["format"]=="pair" else "Assign ranks 1 (best), 2, or 3 (worst) to X, Y, Z. Equal ranks are ties.")
    language={"en":"English","es":"Spanish","fr":"French"}[item.get("language","en")]
    return f'''You assist a human linguistic annotator. Judge independently and only the named simplification axis. Labels are blinded.\nLanguage of the texts: {language}\nAxis: {item['axis']}\nDefinition: {DEFINITIONS[item['axis']]}\nTask: {task}\nAlso detect whether any version has an unintended difference outside the axis: none, meaning, fluency, or other.\nReturn only one JSON object with keys choice, ranks, side_effect, side_effect_version, note. For a pair, choice is X/Y/Same and ranks is {{}}. For rank3, choice is an empty string and ranks maps X/Y/Z to integers. side_effect_version is an empty string when none. note is one short sentence written in {language}.\nOriginal: {item['original']}\nVersions:\n'''+"\n".join(f"{x}: {item['versions'][x]}" for x in labels)

def validate(item,value):
    if not isinstance(value,dict): raise ValueError("response is not an object")
    side=value.get("side_effect"); side_version=value.get("side_effect_version") or ""
    if side not in {"none","meaning","fluency","other"}: raise ValueError("invalid side_effect")
    if side!="none" and side_version not in item["versions"]: raise ValueError("invalid side_effect_version")
    suggestion={"side_effect":side,"side_effect_version":None if side=="none" else side_version,"note":str(value.get("note", ""))[:500]}
    if item["format"]=="pair":
        if value.get("choice") not in {"X","Y","Same"}: raise ValueError("invalid pair choice")
        suggestion["choice"]=value["choice"]
    else:
        ranks=value.get("ranks")
        if not isinstance(ranks,dict) or set(ranks)!={"X","Y","Z"}: raise ValueError("invalid ranks")
        ranks={x:int(ranks[x]) for x in "XYZ"}
        if any(v not in {1,2,3} for v in ranks.values()): raise ValueError("invalid rank value")
        suggestion["ranks"]=ranks
    return suggestion

def key_from_env(provider="gemini"):
    name=provider.upper()
    key=os.environ.get(f"{name}_API_KEY","").strip()
    key_file=os.environ.get(f"{name}_API_KEY_FILE","").strip()
    if not key and key_file: key=Path(key_file).read_text(encoding="utf-8").strip()
    if not key: raise RuntimeError(f"set {name}_API_KEY or {name}_API_KEY_FILE")
    return key

RANK={"anyOf":[{"type":"integer","enum":[1,2,3]},{"type":"null"}]}
# Strict structured output needs every key; a pair answers with null ranks, a rank3 item with an empty choice.
OPENAI_SCHEMA={"type":"object","additionalProperties":False,"required":["choice","ranks","side_effect","side_effect_version","note"],"properties":{
    "choice":{"type":"string","enum":["X","Y","Same",""]},
    "ranks":{"type":"object","additionalProperties":False,"required":["X","Y","Z"],"properties":{"X":RANK,"Y":RANK,"Z":RANK}},
    "side_effect":{"type":"string","enum":["none","meaning","fluency","other"]},
    "side_effect_version":{"type":"string","enum":["","X","Y","Z"]},"note":{"type":"string"}}}

def from_openai(item,value):
    value=dict(value); ranks=value.get("ranks") or {}
    value["ranks"]={} if item["format"]=="pair" else {k:v for k,v in ranks.items() if v is not None}
    return value

def generate_openai(item,key,model,retries=10):
    body=json.dumps({"model":model,"messages":[{"role":"user","content":prompt(item)}],"reasoning_effort":"low","max_completion_tokens":2000,
                     "response_format":{"type":"json_schema","json_schema":{"name":"s1_suggestion","strict":True,"schema":OPENAI_SCHEMA}}}).encode()
    request=urllib.request.Request("https://api.openai.com/v1/chat/completions",data=body,headers={"Content-Type":"application/json","Authorization":f"Bearer {key}"},method="POST")
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request,timeout=120) as response: payload=json.load(response)
            text=payload["choices"][0]["message"]["content"]
            return validate(item,from_openai(item,json.loads(text))),payload.get("usage",{})
        except urllib.error.HTTPError as error:
            detail=error.read().decode("utf-8",errors="replace")[:1000]
            if attempt+1==retries or error.code not in {429,500,502,503,504}:
                raise RuntimeError(f"OpenAI failed for {item['case_id']}: HTTP {error.code}: {detail}") from error
            retry_after=float(error.headers.get("Retry-After","0") or 0)
            time.sleep(max(retry_after,min(60.0,5.0*(attempt+1))))
        except (urllib.error.URLError,KeyError,TypeError,json.JSONDecodeError,ValueError) as error:
            if attempt+1==retries:
                raise RuntimeError(f"OpenAI failed for {item['case_id']}: {error}") from error
            time.sleep(min(60.0,2.0**attempt))

def generate(item,key,model,retries=10):
    url=f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body=json.dumps({"contents":[{"role":"user","parts":[{"text":prompt(item)}]}],"generationConfig":{"temperature":0,"maxOutputTokens":512,"responseMimeType":"application/json","thinkingConfig":{"thinkingBudget":256}}}).encode()
    request=urllib.request.Request(url,data=body,headers={"Content-Type":"application/json","x-goog-api-key":key},method="POST")
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request,timeout=90) as response: payload=json.load(response)
            text="".join(part.get("text","") for part in payload["candidates"][0]["content"]["parts"])
            return validate(item,json.loads(text)),payload.get("usageMetadata",{})
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")[:1000]
            if attempt + 1 == retries or error.code not in {429, 500, 502, 503, 504}:
                raise RuntimeError(f"Gemini failed for {item['case_id']}: HTTP {error.code}: {detail}") from error
            retry_after = float(error.headers.get("Retry-After", "0") or 0)
            time.sleep(max(retry_after, min(60.0, 5.0 * (attempt + 1))))
        except (urllib.error.URLError, KeyError, json.JSONDecodeError, ValueError) as error:
            if attempt + 1 == retries:
                raise RuntimeError(f"Gemini failed for {item['case_id']}: {error}") from error
            time.sleep(min(60.0, 2.0 ** attempt))

def main(argv=None):
    parser=argparse.ArgumentParser(); parser.add_argument("--input",type=Path,action="append",required=True); parser.add_argument("--output",type=Path,required=True); parser.add_argument("--provider",choices=("gemini","openai"),default="gemini"); parser.add_argument("--model"); parser.add_argument("--limit",type=int); parser.add_argument("--delay",type=float,default=15.0); args=parser.parse_args(argv)
    args.model=args.model or {"gemini":"gemini-3.8-flash","openai":"gpt-5.4-mini-2026-03-17"}[args.provider]
    call=generate_openai if args.provider=="openai" else generate
    items=list(read_rows(args.input)); existing={}
    if args.output.exists():
        existing={row["case_id"]:row for row in read_rows([args.output])}
    pending=[x for x in items if x["case_id"] not in existing]
    if args.limit is not None: pending=pending[:args.limit]
    key=key_from_env(args.provider); args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("a",encoding="utf-8") as handle:
        for index,item in enumerate(pending,1):
            suggestion,usage=call(item,key,args.model)
            handle.write(json.dumps({"case_id":item["case_id"],"model":args.model,"suggestion":suggestion,"usage":usage},ensure_ascii=False,sort_keys=True)+"\n"); handle.flush()
            print(f"{index}/{len(pending)} {item['case_id']}",flush=True); time.sleep(args.delay)
    print(json.dumps({"generated":len(pending),"existing":len(existing),"output":str(args.output)},sort_keys=True))
if __name__=="__main__": main()
