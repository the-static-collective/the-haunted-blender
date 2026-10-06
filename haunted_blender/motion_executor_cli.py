from __future__ import annotations
import argparse,json
from pathlib import Path
from . import motion_executor
def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def emit(v): print(json.dumps(v,indent=2,sort_keys=True))
def main(argv=None):
    p=argparse.ArgumentParser(prog="haunted-blender-motion-executor");s=p.add_subparsers(dest="cmd",required=True)
    b=s.add_parser("build");b.add_argument("root");b.add_argument("route");b.add_argument("--occurrence-budget-micros",type=int,required=True);b.add_argument("--per-job-budget-micros",type=int,required=True)
    n=s.add_parser("next");n.add_argument("root");n.add_argument("plan");n.add_argument("state")
    for name in ["capabilities","quote","submit","status","fetch"]:
        q=s.add_parser(name);q.add_argument("root");q.add_argument("plan");q.add_argument("state");q.add_argument("receipt")
    a=s.add_parser("advance");a.add_argument("root");a.add_argument("plan");a.add_argument("state")
    args=p.parse_args(argv)
    if args.cmd=="build": r=motion_executor.build_plan(args.root,args.route,occurrence_budget_usd_micros=args.occurrence_budget_micros,per_job_budget_usd_micros=args.per_job_budget_micros)
    elif args.cmd=="next": r=motion_executor.next_action(args.root,args.plan,args.state)
    elif args.cmd=="advance": r=motion_executor.advance(args.root,args.plan,args.state)
    else: r=getattr(motion_executor,"record_"+args.cmd)(args.root,args.plan,args.state,read(args.receipt))
    emit(r);return 0
if __name__=="__main__": raise SystemExit(main())
