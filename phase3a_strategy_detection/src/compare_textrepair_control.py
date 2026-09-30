#!/usr/bin/env python3
"""Compare text-repair control predictions with the original v1 run."""
from __future__ import annotations
import argparse, json
from pathlib import Path
MODELS=("xlmr_large_focal","multilingual_e5_large_bce","qwen2p5_7b_pairwise_qlora","gemma3_12b_pairwise_qlora")
LANGS=("ar","ca","de","en","es","fr","it","ja","pt-BR","ru","sl","ur")

def rows(path):
    with path.open(encoding="utf-8") as f:
        for line in f: yield json.loads(line)

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--v1-root',type=Path,required=True); p.add_argument('--control-root',type=Path,required=True); p.add_argument('--output',type=Path,required=True); p.add_argument('--minimum-agreement',type=float,default=.995); a=p.parse_args()
    report={"schema":"feats-phase3a-textrepair-control-comparison-v1","minimum_label_set_agreement":a.minimum_agreement,"models":{}}
    for model in MODELS:
        same=total=0; max_delta=0.; worst=None; by_language={}
        for lang in LANGS:
            old_path=a.v1_root/'models'/model/'predictions'/lang/'feats_consolidated.jsonl'
            new_path=a.control_root/'models'/model/'predictions'/lang/'feats_consolidated.jsonl'
            old={str(x['canonical_pair_id']):x for x in rows(old_path)}
            lsame=ltotal=0
            for new in rows(new_path):
                pid=str(new['canonical_pair_id']); prior=old[pid]; ltotal+=1; total+=1
                equal=prior['predicted_codes']==new['predicted_codes']; lsame+=equal; same+=equal
                for code,value in new['strategy_scores'].items():
                    delta=abs(float(value)-float(prior['strategy_scores'][code]))
                    if delta>max_delta: max_delta=delta; worst={"canonical_pair_id":pid,"strategy":code,"v1":prior['strategy_scores'][code],"control":value}
            by_language[lang]={"pairs":ltotal,"label_set_agreement":lsame/ltotal if ltotal else None}
        agreement=same/total
        report['models'][model]={"pairs":total,"exact_label_set_matches":same,"label_set_agreement":agreement,"maximum_absolute_probability_difference":max_delta,"worst_probability_difference":worst,"by_language":by_language,"passed":agreement>=a.minimum_agreement}
    report['passed']=all(x['passed'] for x in report['models'].values())
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(report,indent=2)+'\n')
    md=['# Text-repair reproducibility control','','| Model | Pairs | Exact label-set agreement | Max |Δ probability| | Pass |','|---|---:|---:|---:|:---:|']
    for m,x in report['models'].items(): md.append(f"| {m} | {x['pairs']:,} | {x['label_set_agreement']:.3%} | {x['maximum_absolute_probability_difference']:.8f} | {'yes' if x['passed'] else 'no'} |")
    md += ['',f"Overall gate: **{'PASS' if report['passed'] else 'FAIL'}** (required ≥ {a.minimum_agreement:.1%} per model)."]
    a.output.with_suffix('.md').write_text('\n'.join(md)+'\n')
    print(json.dumps(report,indent=2))
    if not report['passed']: raise SystemExit(2)
if __name__=='__main__': main()
