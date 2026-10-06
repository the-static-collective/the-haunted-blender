"""Pixel plan/proposal/execute/verify doors. No command issues an admission."""
import argparse
from pathlib import Path
from . import mangalize as m, manga_pixel_execution as pixels


def main(argv=None):
    parser = argparse.ArgumentParser(prog='haunted-blender-pixels')
    sub = parser.add_subparsers(dest='command', required=True)
    for command in ('prepare', 'execute', 'verify'):
        p = sub.add_parser(command)
        for name in ('source_root', 'ancestor_event', 'released_event', 'performed_event', 'output'):
            p.add_argument(name, type=Path)
        p.add_argument('--use', action='append', type=Path, required=True)
        if command == 'prepare':
            p.add_argument('--authority-ref', required=True)
            p.add_argument('--sampler', choices=('LANCZOS', 'NEAREST'), default='LANCZOS')
        else:
            for name in ('plan', 'proposal', 'admission'):
                p.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        bundles = [{k: m.read(p / (k + '.json')) for k in ('role','placement','admission')} for p in args.use]
        if args.command == 'prepare':
            layout = pixels.verified_composition(args.source_root,args.ancestor_event,args.released_event,bundles,args.performed_event)
            plan = pixels.compile_plan(layout,args.ancestor_event,sampler=args.sampler)
            proposal = pixels.propose(layout,args.ancestor_event,plan,authority_ref=args.authority_ref)
            for protected in (args.source_root,args.ancestor_event,args.released_event,args.performed_event):
                m.require(not args.output.resolve().is_relative_to(protected.resolve()),'proposal output cannot mutate ancestor evidence')
            m.persist(args.output / 'plan.json',plan)
            m.persist(args.output / 'proposal.json',proposal)
            m.persist(args.output / 'TRACE.md',pixels.trace(plan,proposal).encode())
            print(plan['planHash']); print(proposal['proposalHash'])
            print('PIXEL EXECUTION READY — ADMISSION REQUIRED')
        else:
            records = [m.read(getattr(args,k)) for k in ('plan','proposal','admission')]
            result = (pixels.verify if args.command == 'verify' else pixels.execute)(
                args.source_root,args.ancestor_event,args.released_event,bundles,args.performed_event,*records,args.output)
            print(result if isinstance(result,str) else result['executionHash'])
        return 0
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print('MANGALIZE-004: REFUSE: '+str(exc)); return 1


if __name__ == '__main__':
    raise SystemExit(main())
