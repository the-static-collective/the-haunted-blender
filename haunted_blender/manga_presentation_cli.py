"""005 prepare/execute/verify doors. No automatic ground or admission."""
import argparse
from pathlib import Path

from . import mangalize as m, manga_presentation as presentation


def main(argv=None):
    parser = argparse.ArgumentParser(prog='haunted-blender-presentation')
    sub = parser.add_subparsers(dest='command', required=True)
    for command in ('prepare', 'execute', 'verify'):
        p = sub.add_parser(command)
        for name in ('source_root', 'ancestor_event', 'released_event', 'performed_event', 'pixel_event', 'output'):
            p.add_argument(name, type=Path)
        p.add_argument('--use', action='append', type=Path, required=True)
        if command == 'prepare':
            p.add_argument('--rgba8', action='append', nargs=4, type=int, required=True)
            p.add_argument('--intent', required=True)
            p.add_argument('--authority-ref', required=True)
        else:
            for name in ('ground', 'proposal', 'admission'):
                p.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        bundles = [{k: m.read(path / (k + '.json')) for k in ('role', 'placement', 'admission')} for path in args.use]
        roots = [args.source_root, args.ancestor_event, args.released_event]
        presentation.protect_output(args.output, [*roots, args.performed_event, args.pixel_event])
        if args.command == 'prepare':
            parent = presentation.verified_parent(*roots, bundles, args.performed_event, args.pixel_event)
            candidates = []
            for rgba8 in args.rgba8:
                value = presentation.ground(parent, rgba8, intent=args.intent)
                proposal = presentation.propose(parent, value, authority_ref=args.authority_ref)
                candidates.append({'ground': value, 'proposal': proposal})
            # Observe and validate the entire set before persisting any candidate.
            comparison = presentation.compare(parent, args.pixel_event, candidates)
            for candidate in candidates:
                directory = args.output / candidate['ground']['groundHash']
                for kind, value in candidate.items():
                    m.persist(directory / (kind + '.json'), value)
            m.persist(args.output / 'comparison.json', comparison)
            print('PRESENTATION GROUND READY — SELECTION / ADMISSION REQUIRED')
            print('comparisonHash:', comparison['comparisonHash'])
        else:
            records = [m.read(getattr(args, kind)) for kind in ('ground', 'proposal', 'admission')]
            result = (presentation.verify if args.command == 'verify' else presentation.execute)(
                *roots, bundles, args.performed_event, args.pixel_event, *records, args.output)
            print(result if isinstance(result, str) else result['projectionHash'])
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print('MANGALIZE-005: REFUSE: ' + str(exc))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
