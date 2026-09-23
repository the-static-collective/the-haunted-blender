"""Explicit Creative Claw request, local admission, and filmmaker acceptance doors."""
import argparse
import json
from pathlib import Path

from . import creative_take


def main():
    parser = argparse.ArgumentParser(prog="haunted-creative-take")
    commands = parser.add_subparsers(dest="command", required=True)
    make = commands.add_parser("request")
    make.add_argument("root", type=Path)
    make.add_argument("artifact_snapshot", type=Path)
    make.add_argument("beat", type=int)
    make.add_argument("prompt")
    make.add_argument("--duration", type=int, default=3)
    make.add_argument("--assert-synthetic", action="store_true")
    make.add_argument("--approve-disclosure", action="store_true")
    incoming = commands.add_parser("admit")
    incoming.add_argument("root", type=Path)
    incoming.add_argument("request_snapshot", type=Path)
    incoming.add_argument("video", type=Path)
    incoming.add_argument("--provider-job-id", required=True)
    choose = commands.add_parser("accept")
    choose.add_argument("root", type=Path)
    choose.add_argument("request_snapshot", type=Path)
    choose.add_argument("admitted_video", type=Path)
    choose.add_argument("--approve", action="store_true")
    args = parser.parse_args()
    if args.command == "request":
        result = creative_take.request(args.root, args.artifact_snapshot, args.beat,
                                       args.prompt, duration=args.duration,
                                       synthetic_source=args.assert_synthetic,
                                       disclose_to_provider=args.approve_disclosure)
    elif args.command == "admit":
        result = creative_take.admit(args.root, args.request_snapshot, args.video,
                                     provider_job_id=args.provider_job_id)
    else:
        result = creative_take.accept(args.root, args.request_snapshot, args.admitted_video,
                                      filmmaker_approval=args.approve)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
