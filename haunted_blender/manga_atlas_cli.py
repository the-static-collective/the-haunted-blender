from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import manga_atlas


def _read(path: str | Path) -> dict:
    return json.loads(Path(path).expanduser().resolve(strict=True).read_text(encoding="utf-8"))


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"Will not overwrite: {path}")
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def emit(value):
    print(json.dumps(value, indent=2, sort_keys=True))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="haunted-blender-manga-atlas")
    sub = parser.add_subparsers(dest="command", required=True)

    source = sub.add_parser("source")
    source.add_argument("source_image")
    source.add_argument("output_json")
    source.add_argument("--class", dest="source_class", required=True, choices=sorted(manga_atlas.SOURCE_CLASSES))
    source.add_argument("--label", default="")
    source.add_argument("--rights-note", default="")
    source.add_argument("--pixel-reuse", action="store_true")
    source.add_argument("--derivative-reuse", action="store_true")
    source.add_argument("--publication-reuse", action="store_true")
    source.add_argument("--family", action="append", default=[])
    source.add_argument("--page-role", choices=sorted(manga_atlas.PAGE_ROLES))
    source.add_argument("--continuity-group")
    source.add_argument("--motif", action="append", default=[])
    source.add_argument("--sequence-index", type=int)

    analyze = sub.add_parser("analyze")
    analyze.add_argument("source_manifest_json")
    analyze.add_argument("output_json")

    harvest = sub.add_parser("harvest")
    harvest.add_argument("source_manifest_json")
    harvest.add_argument("output_dir")

    drawer = sub.add_parser("drawer")
    drawer.add_argument("page_harvest_json")
    drawer.add_argument("output_json")

    atlas = sub.add_parser("atlas")
    atlas.add_argument("output_json")
    atlas.add_argument("report_json", nargs="+")

    prescribe = sub.add_parser("director")
    prescribe.add_argument("report_json")
    prescribe.add_argument("output_json")

    sequence = sub.add_parser("sequence")
    sequence.add_argument("output_json")
    sequence.add_argument("report_json", nargs="+")

    sequence_director = sub.add_parser("sequence-director")
    sequence_director.add_argument("sequence_json")
    sequence_director.add_argument("output_json")

    args = parser.parse_args(argv)

    if args.command == "source":
        result = manga_atlas.source_manifest(
            args.source_image,
            source_class=args.source_class,
            pixel_reuse=args.pixel_reuse,
            derivative_reuse=args.derivative_reuse,
            publication_reuse=args.publication_reuse,
            grammar_families=args.family,
            rights_note=args.rights_note,
            label=args.label,
            page_role=args.page_role,
            continuity_group=args.continuity_group,
            motifs=args.motif,
            sequence_index=args.sequence_index,
        )
        _write(Path(args.output_json).expanduser().resolve(), result)
    elif args.command == "analyze":
        result = manga_atlas.analyze_page(_read(args.source_manifest_json))
        _write(Path(args.output_json).expanduser().resolve(), result)
    elif args.command == "harvest":
        result = manga_atlas.harvest_page(
            _read(args.source_manifest_json),
            args.output_dir,
        )
    elif args.command == "drawer":
        result = manga_atlas.page_harvest_to_parts_drawer(
            _read(args.page_harvest_json),
            args.output_json,
        )
    elif args.command == "atlas":
        result = manga_atlas.build_atlas([_read(path) for path in args.report_json])
        _write(Path(args.output_json).expanduser().resolve(), result)
    elif args.command == "director":
        result = manga_atlas.director_prescription(_read(args.report_json))
        _write(Path(args.output_json).expanduser().resolve(), result)
    elif args.command == "sequence":
        result = manga_atlas.build_sequence_grammar(
            [_read(path) for path in args.report_json]
        )
        _write(Path(args.output_json).expanduser().resolve(), result)
    else:
        result = manga_atlas.sequence_director_prescription(
            _read(args.sequence_json)
        )
        _write(Path(args.output_json).expanduser().resolve(), result)

    emit(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
