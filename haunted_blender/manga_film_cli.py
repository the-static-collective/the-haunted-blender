from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import manga_film, narrative_performance


def main(argv=None):
    parser=argparse.ArgumentParser(prog="haunted-blender-manga-film")
    parser.add_argument("spec_json")
    parser.add_argument("output_dir")
    parser.add_argument("--width",type=int,default=640)
    parser.add_argument("--height",type=int,default=360)
    parser.add_argument("--fps",type=int,default=12)
    args=parser.parse_args(argv)

    spec=narrative_performance.read_spec(args.spec_json)
    result=manga_film.render_spec(
        spec,args.output_dir,width=args.width,height=args.height,fps=args.fps
    )
    receipt=result["receipt"]
    print(json.dumps({
        "movie":result["movie"],
        "receipt":result["receiptPath"],
        "renderId":receipt["id"],
        "outputSha256":receipt["outputSha256"],
        "frameCount":receipt["frameCount"],
        "beatCount":receipt["beatCount"],
        "durationSeconds":receipt["durationSeconds"],
        "hasAudio":receipt["hasAudio"],
        "externalGenerations":0,
        "providerCredits":0,
        "usdMicros":0,
    },indent=2,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
