#!/usr/bin/env python3
"""Build the blinded, operation-stratified MMI v3 review JSONL and key."""
from __future__ import annotations
import argparse
import json
from collections import defaultdict
from pathlib import Path
from phase6_degraded_corpus.src.common.contracts import read_jsonl, stable_key, write_jsonl


def selected_text(row: dict) -> str | None:
    index=row.get("selected_index"); candidates=row.get("candidates") or []
    return candidates[index].get("degraded") if index is not None and 0 <= index < len(candidates) and candidates[index].get("valid") else None


def stratified(rows: list[dict], axis: str, count: int, seed: int) -> list[dict]:
    groups=defaultdict(list)
    for row in rows:
        if row.get("target_axis")==axis and selected_text(row): groups[row["operation"]].append(row)
    for op in groups: groups[op].sort(key=lambda r:stable_key(seed,f"review:{axis}:{op}:{r['canonical_pair_id']}"))
    output=[]; labels=sorted(groups); position=0
    while len(output)<count and labels:
        op=labels[position%len(labels)]; output.append(groups[op].pop(0))
        if not groups[op]: labels.remove(op); position=0
        else: position+=1
    if len(output)<count: raise RuntimeError(f"{axis}: only {len(output)} checker-valid rows, need {count}")
    return output


def build(rows: list[dict], count: int=60, seed: int=20261002):
    selected=[]
    for axis in ("MOD","ILLOC"): selected += stratified(rows,axis,count,seed)
    selected.sort(key=lambda r:stable_key(seed,f"shuffle:{r['canonical_pair_id']}:{r['target_axis']}"))
    review=[]; key=[]
    for i,row in enumerate(selected,1):
        case=f"A{i:03d}"; degraded=selected_text(row)
        review.append({"case_id":case,"axis":row["target_axis"],"original":row["original"],"simplified":row["clean_simplification"],"degraded":degraded})
        key.append({"case_id":case,"canonical_pair_id":row["canonical_pair_id"],"canonical_original_id":row["canonical_original_id"],"axis":row["target_axis"],"operation":row["operation"],"corpus":row["corpus"]})
    return review,key


def main():
    p=argparse.ArgumentParser(); p.add_argument('--scored',type=Path,action='append',required=True); p.add_argument('--output-dir',type=Path,required=True); p.add_argument('--count',type=int,default=60); p.add_argument('--seed',type=int,default=20261002); args=p.parse_args()
    review,key=build([r for path in args.scored for r in read_jsonl(path)],args.count,args.seed); args.output_dir.mkdir(parents=True,exist_ok=True)
    write_jsonl(args.output_dir/'review_sample.jsonl',review); (args.output_dir/'review_key.json').write_text(json.dumps(key,indent=2,sort_keys=True)+'\n')
    print(json.dumps({a:sum(r['axis']==a for r in review) for a in ('MOD','ILLOC')},indent=2))
if __name__=='__main__': main()
