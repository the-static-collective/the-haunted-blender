from __future__ import annotations
import argparse
import json
from . import cockpit

def emit(value):
    print(json.dumps(value, indent=2, sort_keys=True))

def main(argv=None):
    parser=argparse.ArgumentParser(prog="haunted-blender-cockpit")
    sub=parser.add_subparsers(dest="command", required=True)

    create=sub.add_parser("create")
    create.add_argument("root")
    create.add_argument("--project-id", required=True)
    create.add_argument("--title", required=True)
    create.add_argument("--track-id")
    create.add_argument("--remote", action="store_true")

    add=sub.add_parser("add-section")
    add.add_argument("root"); add.add_argument("section_id"); add.add_argument("kind")
    add.add_argument("start", type=float); add.add_argument("end", type=float); add.add_argument("--label")

    grow=sub.add_parser("grow"); grow.add_argument("root"); grow.add_argument("section_id"); grow.add_argument("ecology_id")
    keep=sub.add_parser("keep"); keep.add_argument("root"); keep.add_argument("section_id"); keep.add_argument("proposal_id"); keep.add_argument("--scene-id")
    moving=sub.add_parser("moving"); moving.add_argument("root"); moving.add_argument("section_id"); moving.add_argument("scene_id")
    awaken=sub.add_parser("awaken"); awaken.add_argument("root"); awaken.add_argument("section_id"); awaken.add_argument("window_id")
    witness=sub.add_parser("witness"); witness.add_argument("root"); witness.add_argument("section_id"); witness.add_argument("video_address")
    alive=sub.add_parser("alive"); alive.add_argument("root"); alive.add_argument("section_id")
    haunt=sub.add_parser("haunt"); haunt.add_argument("root"); haunt.add_argument("section_id"); haunt.add_argument("haunt_id")
    local=sub.add_parser("local-only"); local.add_argument("root"); local.add_argument("state", choices=["on","off"])
    view=sub.add_parser("view"); view.add_argument("root")
    resume=sub.add_parser("resume"); resume.add_argument("root")

    args=parser.parse_args(argv)
    if args.command=="create":
        result=cockpit.create_project(args.root,project_id=args.project_id,title=args.title,track_id=args.track_id,local_only=not args.remote)
    elif args.command=="add-section":
        result=cockpit.add_section(args.root,section_id=args.section_id,kind=args.kind,start=args.start,end=args.end,label=args.label)
    elif args.command=="grow":
        result=cockpit.action_grow(args.root,args.section_id,ecology_id=args.ecology_id)
    elif args.command=="keep":
        result=cockpit.action_keep(args.root,args.section_id,proposal_id=args.proposal_id,scene_id=args.scene_id)
    elif args.command=="moving":
        result=cockpit.action_scene_rendered(args.root,args.section_id,scene_id=args.scene_id)
    elif args.command=="awaken":
        result=cockpit.action_awaken(args.root,args.section_id,window_id=args.window_id)
    elif args.command=="witness":
        result=cockpit.action_witness(args.root,args.section_id,video_address=args.video_address)
    elif args.command=="alive":
        result=cockpit.action_alive(args.root,args.section_id)
    elif args.command=="haunt":
        result=cockpit.action_haunt(args.root,args.section_id,haunt_id=args.haunt_id)
    elif args.command=="local-only":
        result=cockpit.set_local_only(args.root,args.state=="on")
    elif args.command=="view":
        result=cockpit.cockpit_view(args.root)
    else:
        result=cockpit.resume_summary(args.root)
    emit(result)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
