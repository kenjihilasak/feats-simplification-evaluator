"""Build the 30 blinded S1 controls without changing the frozen 300 items."""
from __future__ import annotations
import argparse, json, random, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
RUN=ROOT/"phase6_degraded_corpus/runs/annotation_v1"
SUPPORTED={"MOD","OMIT","SYN","EXPL","ILLOC"}
def jsonl(path):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip(): yield json.loads(line)
def reviewed(path):
    text=path.read_text(encoding="utf-8")
    for block in re.split(r"(?=^### Case )",text,flags=re.M):
        if "* [x] Valid" not in block: continue
        def field(name):
            match=re.search(rf"^\* \*\*{name}:\*\*\s*(.*)$",block,re.M)
            return match.group(1).strip() if match else None
        case=re.search(r"^### Case (\S+)",block,re.M); axis=field("Axis")
        if axis: axis=axis.split()[0].strip("`")
        if case and axis in SUPPORTED and field("Original") and field("Simplified") and field("Degraded"):
            yield {"source_case":case.group(1),"axis":axis,"original":field("Original"),"clean":field("Simplified"),"degraded":field("Degraded"),"report":str(path.relative_to(ROOT))}
def build(seed=4817):
    rng=random.Random(seed); keys=json.loads((RUN/"s1_key.json").read_text()); used={x["canonical_original_id"] for x in keys}; pools=[]
    for path in sorted((ROOT/"phase6_degraded_corpus/runs/fose_en_v2/pools").glob("*.jsonl")):
        for row in jsonl(path):
            if row.get("canonical_original_id") not in used and row.get("target_axis") in SUPPORTED: pools.append(row)
    pools.sort(key=lambda x:(x["target_axis"],x["canonical_original_id"])); rng.shuffle(pools); controls=[]; control_keys=[]
    for number,row in enumerate(pools[:15],1):
        label=row["clean_simplification"]; case=f"C{number:03d}"; axis=row["target_axis"]
        controls.append({"case_id":case,"axis":axis,"format":"pair","original":row["original"],"versions":{"X":label,"Y":label}})
        control_keys.append({"case_id":case,"control_kind":"identical","expected":"Same","source_id":row["canonical_original_id"]})
    candidates=[]
    for path in [ROOT/"phase6_degraded_corpus/docs/reports/current/fose_v1_review.md",ROOT/"phase6_degraded_corpus/docs/reports/current/mmi_v2_heldout_review.md"]: candidates.extend(reviewed(path))
    unique=[]; seen=set()
    for row in candidates:
        signature=(row["original"],row["clean"],row["degraded"],row["axis"])
        if signature not in seen: seen.add(signature); unique.append(row)
    rng.shuffle(unique)
    if len(unique)<15: raise RuntimeError("fewer than 15 previously validated controls")
    for offset,row in enumerate(unique[:15],16):
        labels=[("X",row["clean"],1.0,"clean"),("Y",row["degraded"],0.0,"known_valid_degradation")]
        if rng.random()<.5: labels.reverse()
        case=f"C{offset:03d}"; controls.append({"case_id":case,"axis":row["axis"],"format":"pair","original":row["original"],"versions":{label:text for label,text,_,_ in labels}})
        control_keys.append({"case_id":case,"control_kind":"known_valid","expected":next(label for label,_,level,_ in labels if level==1.0),"levels":{label:level for label,_,level,_ in labels},"operations":{label:op for label,_,_,op in labels},"source_case":row["source_case"],"source_report":row["report"]})
    return controls,control_keys
def main(argv=None):
    parser=argparse.ArgumentParser(); parser.add_argument("--seed",type=int,default=4817); args=parser.parse_args(argv); controls,key=build(args.seed); RUN.mkdir(parents=True,exist_ok=True)
    (RUN/"s1_controls.jsonl").write_text("".join(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n" for x in controls),encoding="utf-8")
    (RUN/"s1_controls_key.json").write_text(json.dumps(key,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"controls":len(controls),"identical":15,"known_valid":15},sort_keys=True))
if __name__=="__main__": main()
