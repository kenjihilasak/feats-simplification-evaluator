#!/usr/bin/env python3
"""Cross-validated audit of shallow shortcuts in axis pair sets."""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

import numpy as np

from phase6_degraded_corpus.src.common.contracts import read_jsonl, stable_key
from phase6_degraded_corpus.src.planning.plan_mmi_operations import split_sentences

TOKEN = re.compile(r"\w+(?:[-’']\w+)*|[^\w\s]", re.UNICODE)
FEATURE_NAMES = ("delta_tokens", "delta_characters", "delta_sentences", "has_question", "has_exclamation", "delta_commas", "token_overlap", "cola_delta", "nli_entailment")
RULE_AXES = {"OMIT", "SYN", "EXPL"}
RULE_GATE = (2, 3, 4, 5, 7, 8)
DEFINITIONAL = (0, 1, 6)
ALL_FEATURES = tuple(range(len(FEATURE_NAMES)))


def _tokens(text: str) -> list[str]:
    return TOKEN.findall(text or "")


def shallow_features(baseline: str, candidate: str, metadata: dict | None = None) -> list[float]:
    metadata = metadata or {}
    a, b = _tokens(baseline), _tokens(candidate)
    aset, bset = {x.casefold() for x in a}, {x.casefold() for x in b}
    return [len(b)-len(a), len(candidate)-len(baseline), len(split_sentences(candidate))-len(split_sentences(baseline)),
            float("?" in candidate), float("!" in candidate), candidate.count(",")-baseline.count(","),
            len(aset & bset)/max(1, len(aset | bset)), float(metadata.get("cola_delta", 0.0)), float(metadata.get("nli_entailment", 0.0))]


def _selected(row: dict) -> tuple[str | None, dict]:
    direct = row.get("degraded_simplification") or row.get("degraded")
    if direct:
        return direct, row.get("features") or {}
    candidates = row.get("candidates") or []
    index = row.get("selected_index")
    if index is None or not 0 <= index < len(candidates):
        return None, {}
    candidate = candidates[index]
    return candidate.get("degraded"), candidate.get("features") or {}


def _meta(row: dict, features: dict, clean: bool) -> dict:
    clean_accept = float(row.get("clean_acceptability", 0.0))
    baseline_accept = float(row.get("original_acceptability", clean_accept))
    if clean:
        probs = row.get("clean_nli_probabilities") or row.get("clean_nli_original") or {}
        accept = clean_accept
    else:
        probs = features.get("nli_original_degraded") or features.get("nli_clean_degraded") or {}
        accept = float(features.get("acceptability", row.get("degraded_acceptability", clean_accept)))
    return {"cola_delta": accept-baseline_accept, "nli_entailment": float(probs.get("entailment", 0.0))}


def pair_examples(rows: list[dict]) -> tuple[np.ndarray, np.ndarray, list[str], list[str]]:
    x=[]; y=[]; axes=[]; operations=[]
    for row in rows:
        clean = row.get("clean_simplification") or row.get("simplified")
        degraded, features = _selected(row)
        if not clean or not degraded:
            continue
        baseline = row.get("original") or clean
        axis = row.get("target_axis", row.get("axis", "UNKNOWN"))
        operation = row.get("operation") or (row.get("rule_output") or {}).get("expl_pattern") or row.get("error_type") or "unknown"
        for candidate,label,meta in ((clean,1,_meta(row,{},True)),(degraded,0,_meta(row,features,False))):
            x.append(shallow_features(baseline,candidate,meta)); y.append(label); axes.append(axis); operations.append(str(operation))
    return np.asarray(x,float),np.asarray(y,int),axes,operations


def _fit_logistic(x,y):
    mean,scale=x.mean(0),x.std(0); scale[scale==0]=1
    z=np.column_stack([np.ones(len(x)),(x-mean)/scale]); weights=np.zeros(z.shape[1])
    for _ in range(1500):
        prob=1/(1+np.exp(-np.clip(z@weights,-30,30))); grad=z.T@(prob-y)/len(y); grad[1:]+=1e-3*weights[1:]; weights-=.2*grad
    return weights,mean,scale


def _predict(model,x):
    w,m,s=model; z=np.column_stack([np.ones(len(x)),(x-m)/s]); return 1/(1+np.exp(-np.clip(z@w,-30,30)))


def _roc_auc(y,scores):
    order=np.argsort(scores,kind="mergesort"); ranks=np.empty(len(scores),float); i=0
    while i<len(order):
        j=i+1
        while j<len(order) and scores[order[j]]==scores[order[i]]: j+=1
        ranks[order[i:j]]=(i+1+j)/2; i=j
    pos=y==1; neg=y==0
    return float((ranks[pos].sum()-pos.sum()*(pos.sum()+1)/2)/(pos.sum()*neg.sum()))


def cv_auc(x,y,seed=20260930):
    counts=np.bincount(y.astype(int),minlength=2); folds=min(5,int(counts.min()))
    if folds<2 or len(set(y))<2: return None
    rng=np.random.default_rng(seed); fold_ids=np.empty(len(y),int)
    for label in (0,1):
        indices=np.flatnonzero(y==label); rng.shuffle(indices); fold_ids[indices]=np.arange(len(indices))%folds
    pred=np.zeros(len(y))
    for fold in range(folds):
        test=fold_ids==fold; pred[test]=_predict(_fit_logistic(x[~test],y[~test]),x[test])
    return _roc_auc(y,pred)


def _feature_result(x,y,indices,seed):
    if not indices: return None
    subset=x[:,indices]; auc=cv_auc(subset,y,seed)
    weights=_fit_logistic(subset,y)[0][1:] if len(y) and len(set(y))==2 else np.zeros(len(indices))
    largest=int(np.argmax(np.abs(weights)))
    return {"roc_auc":auc,"largest_weight_feature":FEATURE_NAMES[indices[largest]],"largest_weight":float(weights[largest])}


def _cell(x,y,axis,seed):
    gate=RULE_GATE if axis in RULE_AXES else ALL_FEATURES
    result={"examples":len(y),"gate":_feature_result(x,y,gate,seed)}
    result["passed"]=result["gate"]["roc_auc"] is not None and result["gate"]["roc_auc"]<=.70
    if axis in RULE_AXES: result["definitional"]=_feature_result(x,y,DEFINITIONAL,seed)
    return result


def audit(rows: list[dict],seed: int=20260930) -> dict:
    x,y,axes,operations=pair_examples(rows); result={"schema":"feats-shortcut-audit-v2","gate_auc":.70,"axes":{}}
    for axis in sorted(set(axes)):
        idx=np.asarray([a==axis for a in axes]); cell=_cell(x[idx],y[idx],axis,seed); cell["operations"]={}
        for op in sorted({operations[i] for i in np.flatnonzero(idx)}):
            oi=np.asarray([idx[i] and operations[i]==op for i in range(len(idx))]); cell["operations"][op]=_cell(x[oi],y[oi],axis,seed)
        cell["mix"]=dict(sorted(Counter(operations[i] for i in np.flatnonzero(idx)[::2]).items())); result["axes"][axis]=cell
    result["passed"]=bool(result["axes"]) and all(v["passed"] for v in result["axes"].values()); return result


def rebalance_mmi(rows: list[dict], seed: int = 20260930) -> tuple[list[dict], dict]:
    """Keep every v3 operation and retain the largest deterministic fraction of old MOD/ILLOC rows that passes."""
    selected = [r for r in rows if (r.get("target_axis") or r.get("axis")) not in {"MOD", "ILLOC"}]
    decisions = {}
    for axis in ("MOD", "ILLOC"):
        axis_rows = [r for r in rows if (r.get("target_axis") or r.get("axis")) == axis]
        prefix = axis.casefold() + "_"
        new = [r for r in axis_rows if str(r.get("operation", "")).startswith(prefix)]
        old = [r for r in axis_rows if r not in new]
        old.sort(key=lambda r: stable_key(seed, f"rebalance:{axis}:{r.get('canonical_pair_id','')}"))
        best, best_auc = list(new), None
        # Search largest retained old fraction first. The zero-old case is always evaluated.
        for fraction in [i / 20 for i in range(20, -1, -1)]:
            candidate = new + old[:round(len(old) * fraction)]
            if not candidate:
                continue
            value = audit(candidate, seed)["axes"][axis]
            if value["passed"]:
                best, best_auc = candidate, value["gate"]["roc_auc"]
                break
        selected.extend(best)
        decisions[axis] = {"new_kept": len(new), "old_available": len(old), "old_kept": len(best)-len(new),
                           "gate_auc": best_auc, "passed": best_auc is not None and best_auc <= .70}
    return selected, decisions


def write_report(report: dict,output_dir: Path) -> None:
    output_dir.mkdir(parents=True,exist_ok=True); (output_dir/'shortcut_audit.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    lines=['# Shortcut audit','','Gate: ROC-AUC ≤ 0.70.','','| Axis | Examples | Gate AUC | Largest gate feature | Definitional AUC | Pass |','|---|---:|---:|---|---:|:---:|']
    for axis,value in report['axes'].items():
        gate=value['gate']; defin=value.get('definitional'); fmt=lambda v:'n/a' if v is None else f'{v:.3f}'
        lines.append(f"| {axis} | {value['examples']} | {fmt(gate['roc_auc'])} | {gate['largest_weight_feature']} | {fmt(defin['roc_auc'] if defin else None)} | {'yes' if value['passed'] else 'no'} |")
        for op,opv in value['operations'].items():
            lines.append(f"| ↳ {op} | {opv['examples']} | {fmt(opv['gate']['roc_auc'])} | {opv['gate']['largest_weight_feature']} | {fmt(opv.get('definitional',{}).get('roc_auc'))} | {'yes' if opv['passed'] else 'no'} |")
    (output_dir/'shortcut_audit.md').write_text('\n'.join(lines)+'\n')


def main():
    p=argparse.ArgumentParser(); p.add_argument('--input',type=Path,action='append',required=True); p.add_argument('--output-dir',type=Path,required=True); p.add_argument('--seed',type=int,default=20260930); args=p.parse_args()
    report=audit([r for path in args.input for r in read_jsonl(path)],args.seed); write_report(report,args.output_dir); print(json.dumps({"passed":report['passed'],"axes":{k:v['gate']['roc_auc'] for k,v in report['axes'].items()}},indent=2))
if __name__=='__main__': main()
