#!/usr/bin/env python3
"""Merge v1 predictions for unrepaired rows with text-repair delta predictions."""
from __future__ import annotations
import argparse,csv,hashlib,json,shutil
from pathlib import Path
MODELS=("xlmr_large_focal","multilingual_e5_large_bce","qwen2p5_7b_pairwise_qlora","gemma3_12b_pairwise_qlora")
LANGS=("ar","ca","de","en","es","fr","it","ja","pt-BR","ru","sl","ur")
def sha(path):
 d=hashlib.sha256();
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''): d.update(b)
 return d.hexdigest()
def load(path):
 with path.open(encoding='utf-8') as f: return [json.loads(x) for x in f]
def main():
 p=argparse.ArgumentParser(description=__doc__); p.add_argument('--input-root',type=Path,required=True); p.add_argument('--v1-root',type=Path,required=True); p.add_argument('--delta-root',type=Path,required=True); p.add_argument('--output-root',type=Path,required=True); p.add_argument('--experiment-config',type=Path,required=True); a=p.parse_args()
 if a.output_root.exists(): raise FileExistsError(a.output_root)
 a.output_root.mkdir(parents=True); shutil.copy2(a.experiment_config,a.output_root/'experiment_config.json')
 manifest=[]
 for lang in LANGS:
  inp=a.input_root/lang/'feats_consolidated.jsonl'; metadata=load(inp); repaired={str(x['canonical_pair_id']) for x in metadata if x.get('text_repaired') is True}; ids=[str(x['canonical_pair_id']) for x in metadata]
  manifest.append({'input_file':f'{lang}/feats_consolidated.jsonl','output_file':f'predictions/{lang}/feats_consolidated.jsonl','language':lang,'total_pairs':len(ids),'matching_pairs':len(ids),'selected_pairs':len(ids),'input_sha256':sha(inp)})
  for model in MODELS:
   old=load(a.v1_root/'models'/model/'predictions'/lang/'feats_consolidated.jsonl'); delta={str(x['canonical_pair_id']):x for x in load(a.delta_root/'models'/model/'predictions'/lang/'feats_consolidated.jsonl')}
   if [str(x['canonical_pair_id']) for x in old]!=ids: raise ValueError(f'v1 ID mismatch {model}/{lang}')
   if set(delta)!=repaired: raise ValueError(f'delta ID mismatch {model}/{lang}')
   out=a.output_root/'models'/model/'predictions'/lang/'feats_consolidated.jsonl'; out.parent.mkdir(parents=True,exist_ok=True)
   with out.open('w',encoding='utf-8') as f:
    for row in old:
     pid=str(row['canonical_pair_id']); selected=dict(delta[pid] if pid in repaired else row); selected['prediction_source']='textrepair_delta' if pid in repaired else 'v1'; f.write(json.dumps(selected,ensure_ascii=False,separators=(',',':'))+'\n')
 with (a.output_root/'input_manifest.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(manifest[0])); w.writeheader(); w.writerows(manifest)
 for model in MODELS:
  source=json.loads((a.delta_root/'models'/model/'run_config.json').read_text()); source.update({'schema':'feats-phase3-model-run-v2','status':'complete','experiment_id':a.output_root.name,'shard':None,'processed_pairs':sum(int(x['selected_pairs']) for x in manifest)})
  root=a.output_root/'models'/model; (root/'reports').mkdir(exist_ok=True); (root/'run_config.json').write_text(json.dumps(source,indent=2)+'\n')
 print(a.output_root)
if __name__=='__main__': main()
