"""Join a downloaded S1 export with local hidden keys and report validity."""
from __future__ import annotations
import argparse, json, math
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
RUN=ROOT/"phase6_degraded_corpus/runs/annotation_v1"

def read_jsonl(path):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip(): yield json.loads(line)
def rate(values): return sum(values)/len(values) if values else None
def tau_b(planned,human):
    labels=list(planned); concord=discord=tie_p=tie_h=0
    for i,a in enumerate(labels):
        for b in labels[i+1:]:
            p=(planned[a]>planned[b])-(planned[a]<planned[b]); h=(human[a]<human[b])-(human[a]>human[b])
            if p==0: tie_p+=1
            elif h==0: tie_h+=1
            elif p==h: concord+=1
            else: discord+=1
    denominator=math.sqrt((concord+discord+tie_p)*(concord+discord+tie_h))
    return (concord-discord)/denominator if denominator else None

def in_round(case,language):
    """English case ids predate prefixes (S001, C001); Spanish and French ones start with ES- / FR-."""
    return "-" not in case if language=="en" else case.startswith(f"{language.upper()}-")
def analyze(export,key_path=RUN/"s1_key.json",controls_path=RUN/"s1_controls_key.json",language="en"):
    key={x["case_id"]:x for x in json.loads(key_path.read_text())}; controls={x["case_id"]:x for x in json.loads(controls_path.read_text())}
    groups=defaultdict(list); operation_groups=defaultdict(list); rank_parts=defaultdict(lambda: {"clean_over_half": [], "half_over_zero": []}); taus=defaultdict(list); changes=defaultdict(list); adjudication=[]; control_scores=[]; records=[]
    for row in read_jsonl(export):
        if row.get("state")!="submitted" or not in_round(row["case_id"],language): continue
        answer=row.get("human_final") or {}; case=row["case_id"]
        if case in controls:
            expected=controls[case]["expected"]; correct=answer.get("choice")==expected and answer.get("side_effect")=="none"; control_scores.append(correct); records.append({"case_id":case,"control":True,"valid":correct}); continue
        hidden=key.get(case)
        if not hidden: raise ValueError(f"unknown case_id {case}")
        levels=hidden["levels"]; no_side=answer.get("side_effect")=="none"; valid=False; binary=None; level_check=None; tau=None
        if hidden["format"]=="pair":
            clean=max(levels,key=levels.get); valid=answer.get("choice")==clean and no_side
        else:
            ranks=answer.get("ranks",{}); ordered=sorted(levels,key=levels.get,reverse=True)
            valid=set(ranks)==set(levels) and all(ranks[ordered[i]]<ranks[ordered[i+1]] for i in range(len(ordered)-1)) and no_side
            binary=set(ranks)==set(levels) and ranks[ordered[0]]<ranks[ordered[1]]
            level_check=set(ranks)==set(levels) and ranks[ordered[1]]<ranks[ordered[2]]
            rank_parts[hidden["axis"]]["clean_over_half"].append(binary)
            rank_parts[hidden["axis"]]["half_over_zero"].append(level_check)
            tau=tau_b(levels,ranks) if set(ranks)==set(levels) else None
            if tau is not None: taus[(hidden["axis"],hidden["format"])].append(tau)
        groups[(hidden["axis"],hidden["format"])].append(valid)
        for operation in sorted(set(hidden.get("operations",{}).values())-{"clean"}): operation_groups[(hidden["axis"],operation)].append(valid)
        if row.get("llm_suggestion") is not None: changes[hidden["axis"]].append(bool(row.get("changed")))
        concern=bool(answer.get("uncertain") or answer.get("side_effect") not in {None,"none"} or str(answer.get("note","")).strip())
        record={"case_id":case,"axis":hidden["axis"],"format":hidden["format"],"valid":valid,"binary_clean_over_half":binary,"level_half_over_zero":level_check,"kendall_tau":tau,"changed":row.get("changed")}
        records.append(record)
        if concern: adjudication.append(record|{"human_final":answer})
    result={"schema":"feats-s1-results-v1","submitted_noncontrol":sum(not x.get("control",False) for x in records),"validity_by_axis_format":{f"{a}/{f}":{"valid":sum(v),"total":len(v),"rate":rate(v),"pass_85pct":rate(v)>=.85} for (a,f),v in sorted(groups.items())},"validity_by_operation":{f"{a}/{o}":{"valid":sum(v),"total":len(v),"rate":rate(v)} for (a,o),v in sorted(operation_groups.items())},"rank3_checks":{axis:{name:{"passed":sum(values),"total":len(values),"rate":rate(values)} for name,values in checks.items()} for axis,checks in sorted(rank_parts.items())},"kendall_tau":{f"{a}/{f}":rate(v) for (a,f),v in sorted(taus.items())},"control_accuracy":{"correct":sum(control_scores),"total":len(control_scores),"rate":rate(control_scores),"flagged":bool(control_scores and rate(control_scores)<.70)},"llm_change_rate_by_axis":{a:{"changed":sum(v),"total":len(v),"rate":rate(v)} for a,v in sorted(changes.items())},"adjudication_count":len(adjudication)}
    return result,adjudication
def markdown(result):
    lines=["# S1 results","","Human annotation (LLM-assisted). Each item has one responsible annotator; no inter-annotator agreement or majority label is reported.","","## Validity", "","| Axis / format | Valid | Total | Rate | ≥85% |","|---|---:|---:|---:|:---:|"]
    for name,x in result["validity_by_axis_format"].items(): lines.append(f"| {name} | {x['valid']} | {x['total']} | {x['rate']:.1%} | {'yes' if x['pass_85pct'] else 'no'} |")
    control=result["control_accuracy"]; lines += ["","## Controls","",f"Accuracy: {control['correct']}/{control['total']} ({control['rate']:.1%})" if control['rate'] is not None else "No submitted controls.","",f"Adjudication queue: {result['adjudication_count']} cases.",""]
    return "\n".join(lines)
def main(argv=None):
    parser=argparse.ArgumentParser(); parser.add_argument("export",type=Path); parser.add_argument("--language",choices=("en","es","fr"),default="en"); parser.add_argument("--reports-dir",type=Path); args=parser.parse_args(argv)
    # English keeps its original paths; Spanish and French rounds live in annotation_<lang>_v1.
    run=RUN if args.language=="en" else ROOT/f"phase6_degraded_corpus/runs/annotation_{args.language}_v1"; suffix="" if args.language=="en" else f"_{args.language}"
    reports=args.reports_dir or run/"reports"
    # The export holds every language; analyze keeps this round's cases only.
    result,adjudication=analyze(args.export,run/"s1_key.json",run/"s1_controls_key.json",args.language); reports.mkdir(parents=True,exist_ok=True)
    (reports/"s1_results.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n"); (reports/"adjudication.jsonl").write_text("".join(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n" for x in adjudication)); current=ROOT/f"phase6_degraded_corpus/docs/reports/current/s1_results{suffix}.md"; current.write_text(markdown(result),encoding="utf-8"); print(json.dumps(result,sort_keys=True))
if __name__=="__main__": main()
