from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import motion_organ


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(value, path):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv=None):
    p = argparse.ArgumentParser(prog="haunted-blender-motion-organ")
    sub = p.add_subparsers(dest="command", required=True)

    req = sub.add_parser("request")
    req.add_argument("root")
    req.add_argument("--scene-id", required=True)
    req.add_argument("--scene-sha256", required=True)
    req.add_argument("--window-id", required=True)
    req.add_argument("--start", type=float, required=True)
    req.add_argument("--duration", type=float, required=True)
    req.add_argument("--prompt", required=True)
    req.add_argument("--source-address", required=True)
    req.add_argument("--input-mode", default="image-to-video")
    req.add_argument("--aspect-ratio", default="16:9")
    req.add_argument("--source-assertion", default="operator_asserted_synthetic")
    req.add_argument("--approve-disclosure", action="store_true")

    offers = sub.add_parser("offers")
    offers.add_argument("root")
    offers.add_argument("offers_json")

    route = sub.add_parser("route")
    route.add_argument("root")
    route.add_argument("request")
    route.add_argument("offers")
    route.add_argument("--max-attempts", type=int, default=8)

    organ = sub.add_parser("relatte-spec")
    organ.add_argument("root")
    organ.add_argument("route")
    organ.add_argument("--created-at", required=True)
    organ.add_argument("--source-world", required=True)
    organ.add_argument("--source-particular", required=True)
    organ.add_argument("--return-address")

    admit = sub.add_parser("admit")
    admit.add_argument("root")
    admit.add_argument("route")
    admit.add_argument("offer_id")
    admit.add_argument("video")
    admit.add_argument("--provider-job-id", required=True)

    board = sub.add_parser("board")
    board.add_argument("root")
    board.add_argument("request")

    accept = sub.add_parser("accept")
    accept.add_argument("root")
    accept.add_argument("request")
    accept.add_argument("video")
    accept.add_argument("--keep", action="store_true")

    args = p.parse_args(argv)
    if args.command == "request":
        result = motion_organ.freeze_request(
            args.root,
            scene_id=args.scene_id,
            scene_sha256=args.scene_sha256,
            window_id=args.window_id,
            start_seconds=args.start,
            duration_seconds=args.duration,
            prompt=args.prompt,
            source_address=args.source_address,
            input_mode=args.input_mode,
            aspect_ratio=args.aspect_ratio,
            source_assertion=args.source_assertion,
            remote_disclosure_approved=args.approve_disclosure,
        )
    elif args.command == "offers":
        result = motion_organ.freeze_offers(args.root, read(args.offers_json))
    elif args.command == "route":
        result = motion_organ.route_request(args.root, args.request, args.offers, max_attempts=args.max_attempts)
    elif args.command == "relatte-spec":
        result = motion_organ.to_relatte_organ_spec(
            args.root, args.route, created_at=args.created_at,
            source_world=args.source_world, source_particular=args.source_particular,
            return_address=args.return_address,
        )
    elif args.command == "admit":
        result = motion_organ.admit_candidate(
            args.root, args.route, args.offer_id, args.video,
            provider_job_id=args.provider_job_id,
        )
    elif args.command == "board":
        result = motion_organ.candidate_board(args.root, args.request)
    else:
        result = motion_organ.accept_candidate(
            args.root, args.request, args.video, filmmaker_approval=args.keep
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
