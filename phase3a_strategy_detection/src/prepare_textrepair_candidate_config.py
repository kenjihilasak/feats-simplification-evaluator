#!/usr/bin/env python3
"""Count the unchanged Gemma-anchored rule and write its candidate config."""
import argparse,json
from itertools import zip_longest
from pathlib import Path
MODELS=("gemma3_12b_pairwise_qlora","multilingual_e5_large_bce","qwen2p5_7b_pairwise_qlora","xlmr_large_focal")
LANGS=("ar","ca","de","en","es","fr","it","ja","pt-BR","ru","sl","ur")
def stream(p):
 with p.open(encoding='utf-8') as f:
  for x in f: yield json.loads(x)
def main():
 p=argparse.ArgumentParser(); p.add_argument('--effective-root',type=Path,required=True); p.add_argument('--output',type=Path,required=True); a=p.parse_args(); count=0
 for lang in LANGS:
  paths=[a.effective_root/'models'/m/'predictions'/lang/'feats_consolidated.jsonl' for m in MODELS]
  for rows in zip_longest(*(stream(x) for x in paths)):
   if any(x is None for x in rows): raise ValueError(f'length mismatch {lang}')
   codes=[x['predicted_codes'] for x in rows]
   if len(codes[0])==1 and any(x==codes[0] for x in codes[1:]): count+=1
 cfg={"schema":"feats-phase3a-gemma-anchored-candidate-config-v1","candidate_id":"2026-09-30_single_strategy_gemma_anchored_strict_textrepair_v1","source_experiment_config":"phase3a_strategy_detection/configs/experiments/four_models_textrepair_effective_v1.json","anchor_model":MODELS[0],"confirmation_models":list(MODELS[1:]),"selection":{"anchor_strategy_count":1,"confirmation_mode":"exact_singleton","minimum_confirmation_models":1},"expected_candidates":count,"output_root":"phase3a_strategy_detection/gold_candidates"}
 a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(cfg,indent=2)+'\n'); print(count)
if __name__=='__main__': main()
