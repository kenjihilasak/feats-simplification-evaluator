"""Administrative CLI for the isolated S1 database."""
from __future__ import annotations
import argparse, json, random
from pathlib import Path
from .s1_service import S1Service, S1Settings

def rows(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip(): yield json.loads(line)

def main(argv=None) -> int:
    parser=argparse.ArgumentParser(prog="phase4a-s1")
    parser.add_argument("--database",type=Path)
    sub=parser.add_subparsers(dest="command",required=True)
    load=sub.add_parser("load"); load.add_argument("items",type=Path); load.add_argument("controls",type=Path); load.add_argument("--reviewer",required=True); load.add_argument("--seed",type=int,default=4107); load.add_argument("--identical-controls",type=int,default=15,help="leading controls that are identical pairs (all of them outside English)")
    sug=sub.add_parser("load-suggestions"); sug.add_argument("input",type=Path)
    pri=sub.add_parser("prioritize",help="show these case ids first, in this order"); pri.add_argument("--reviewer",required=True); pri.add_argument("case_ids",nargs="+")
    meta=sub.add_parser("load-meta",help="dataset and human version per item (shown after submission)"); meta.add_argument("input",type=Path)
    exp=sub.add_parser("export"); exp.add_argument("--output",type=Path,required=True)
    back=sub.add_parser("backup"); back.add_argument("--output",type=Path,required=True)
    sub.add_parser("progress"); sub.add_parser("init")
    args=parser.parse_args(argv); service=S1Service(S1Settings(args.database) if args.database else None)
    if args.command=="load":
        values=list(rows(args.items)); controls=list(rows(args.controls))
        for index,item in enumerate(controls): item["_is_control"]=True; item["_control_kind"]="identical" if index<args.identical_controls else "known_valid"
        values.extend(controls); random.Random(args.seed).shuffle(values)
        for index,item in enumerate(values): item["_queue_rank"]=index
        print(json.dumps(service.import_items(values,args.reviewer),sort_keys=True))
    elif args.command=="load-suggestions": print(json.dumps(service.database.import_suggestions(rows(args.input)),sort_keys=True))
    elif args.command=="prioritize": print(json.dumps(service.database.prioritize(args.reviewer,args.case_ids),sort_keys=True))
    elif args.command=="load-meta": print(json.dumps(service.database.import_meta(rows(args.input)),sort_keys=True))
    elif args.command=="export":
        args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text("".join(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n" for x in service.database.export_rows()),encoding="utf-8"); print(args.output)
    elif args.command=="backup": print(json.dumps(service.database.backup(args.output),sort_keys=True))
    elif args.command=="progress": print(json.dumps(service.database.progress(),sort_keys=True))
    else: print(service.database.path)
    return 0
if __name__=="__main__": raise SystemExit(main())
