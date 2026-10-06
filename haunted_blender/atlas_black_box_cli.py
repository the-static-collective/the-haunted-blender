from __future__ import annotations
import argparse,json
from . import atlas_black_box

def main(argv=None):
    p=argparse.ArgumentParser(prog="haunted-blender-atlas-black-box")
    s=p.add_subparsers(dest="cmd",required=True)
    v=s.add_parser("verify")
    v.add_argument("root")
    v.add_argument("lane",choices=sorted(atlas_black_box.LANES))
    m=s.add_parser("summary")
    m.add_argument("root")
    args=p.parse_args(argv)
    result=atlas_black_box.verify_lane(args.root,args.lane) if args.cmd=="verify" else atlas_black_box.summarize(args.root)
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
