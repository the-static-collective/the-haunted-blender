from __future__ import annotations

import argparse
import json

from . import owned_pixel_film


def main(argv=None):
    parser = argparse.ArgumentParser(prog="haunted-blender-owned-pixel-film")
    parser.add_argument("spec_json")
    parser.add_argument("donor_manifest_json")
    parser.add_argument("output_dir")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=360)
    parser.add_argument("--fps", type=int, default=12)
    args = parser.parse_args(argv)

    result = owned_pixel_film.render_spec(
        args.spec_json,
        args.donor_manifest_json,
        args.output_dir,
        width=args.width,
        height=args.height,
        fps=args.fps,
    )
    receipt = result["receipt"]
    print(json.dumps({
        "movie": result["movie"],
        "receipt": result["receiptPath"],
        "renderId": receipt["id"],
        "collectionId": receipt["collectionId"],
        "donorId": receipt["donorId"],
        "donorOriginalDriveSha256": receipt["donorOriginalDriveSha256"],
        "donorDerivativeSha256": receipt["donorDerivativeSha256"],
        "outputSha256": receipt["outputSha256"],
        "ownedPixelFrames": receipt["ownedPixelFrames"],
        "frameCount": receipt["frameCount"],
        "beatCount": receipt["beatCount"],
        "durationSeconds": receipt["durationSeconds"],
        "hasAudio": receipt["hasAudio"],
        "externalGenerations": 0,
        "providerCredits": 0,
        "usdMicros": 0,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
