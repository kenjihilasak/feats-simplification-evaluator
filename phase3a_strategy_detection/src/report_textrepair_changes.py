#!/usr/bin/env python3
"""Report strategy and strict-candidate changes caused by text repair."""
from __future__ import annotations
import argparse,json
from collections import Counter,defaultdict
from pathlib import Path
MODELS=("xlmr_large_focal","multilingual_e5_large_bce","qwen2p5_7b_pairwise_qlora","gemma3_12b_pairwise_qlora")
LANGS=("ar","ca","de","en","es","fr","it","ja","pt-BR","ru","sl","ur")
def stream(path):
 with path.open(encoding='utf-8') as f:
  for line in f: yield json.loads(line)
def label(row): return '+'.join(row['predicted_codes']) or 'NONE'
def candidates(root):
 out={}
 for p in (root/'data').glob('*/*.jsonl'):
  for x in stream(p): out[str(x['canonical_pair_id'])]=x
 return out
def main():
 p=argparse.ArgumentParser(); p.add_argument('--input-root',type=Path,required=True); p.add_argument('--v1-root',type=Path,required=True); p.add_argument('--delta-root',type=Path,required=True); p.add_argument('--old-candidates',type=Path,required=True); p.add_argument('--new-candidates',type=Path,required=True); p.add_argument('--output',type=Path,required=True); a=p.parse_args()
 meta={}; bylang={}
 for lang in LANGS:
  rows={str(x['canonical_pair_id']):x for x in stream(a.input_root/lang/'feats_consolidated.jsonl') if x.get('text_repaired') is True}; meta.update(rows); bylang[lang]=set(rows)
 lines=['# Text-repair strategy-label change report','',f'Repaired pairs evaluated: **{len(meta):,}**.','']
 for model in MODELS:
  total=Counter(); changed=Counter(); transitions=defaultdict(Counter)
  for lang in LANGS:
   old={str(x['canonical_pair_id']):x for x in stream(a.v1_root/'models'/model/'predictions'/lang/'feats_consolidated.jsonl') if str(x['canonical_pair_id']) in bylang[lang]}
   new={str(x['canonical_pair_id']):x for x in stream(a.delta_root/'models'/model/'predictions'/lang/'feats_consolidated.jsonl')}
   if set(old)!=set(new): raise ValueError(f'ID mismatch {model}/{lang}')
   for pid,n in new.items():
    o=old[pid]; corpora=sorted({str(c.get('corpus','unknown')) for c in meta[pid].get('corpora',[])}) or ['unknown']; keys=[('all','all'),(lang,'all'),*((lang,c) for c in corpora)]
    pair=(label(o),label(n)); is_changed=pair[0]!=pair[1]
    for key in keys: total[key]+=1; changed[key]+=is_changed; transitions[key][pair]+=1
  lines += [f'## {model}','','| Language | Corpus | Repaired | Changed | Share |','|---|---|---:|---:|---:|']
  for key in sorted(total): lines.append(f'| {key[0]} | {key[1]} | {total[key]:,} | {changed[key]:,} | {changed[key]/total[key]:.2%} |')
  lines += ['','### Label-set transitions','','| Language | Corpus | v1 → repaired | Rows |','|---|---|---|---:|']
  for key in sorted(transitions):
   for (before,after),count in sorted(transitions[key].items(),key=lambda x:(-x[1],x[0])):
    if before!=after: lines.append(f'| {key[0]} | {key[1]} | `{before}` → `{after}` | {count:,} |')
  lines.append('')
 old=candidates(a.old_candidates); new=candidates(a.new_candidates); old_ids=set(old); new_ids=set(new); entered=new_ids-old_ids; left=old_ids-new_ids; common=old_ids&new_ids; changed_strategy={x for x in common if old[x]['candidate_strategy_code']!=new[x]['candidate_strategy_code']}
 lines += ['## Strict candidate set','',f'- Entered: **{len(entered):,}**',f'- Left: **{len(left):,}**',f'- Changed single strategy: **{len(changed_strategy):,}**','', '### English strategies before and after','','| Strategy | Before | After |','|---|---:|---:|']
 for code in ('SYN','MOD','COMP','EXPL','SYNT','OMIT'):
  before=sum(x.get('language')=='en' and x['candidate_strategy_code']==code for x in old.values()); after=sum(x.get('language')=='en' and x['candidate_strategy_code']==code for x in new.values()); lines.append(f'| {code} | {before:,} | {after:,} |')
 examples=sorted((entered|left|changed_strategy)&bylang['en'])[:20]; lines += ['','### Changed English examples','','| ID | Change | Original (repaired) | Simple (repaired) |','|---|---|---|---|']
 def esc(x): return str(x).replace('|','\\|').replace('\n',' ')[:240]
 for pid in examples:
  b=old.get(pid,{}).get('candidate_strategy_code','—'); n=new.get(pid,{}).get('candidate_strategy_code','—'); m=meta[pid]; lines.append(f'| `{pid}` | {b} → {n} | {esc(m["original"])} | {esc(m["simple"])} |')
 a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text('\n'.join(lines)+'\n',encoding='utf-8'); print(a.output)
if __name__=='__main__': main()
