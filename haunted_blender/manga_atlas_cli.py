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

    collection = sub.add_parser("collection")
    collection.add_argument("output_json")
    collection.add_argument("--label", required=True)
    collection.add_argument("--collection-id", required=True)
    collection.add_argument("--collection-url", default="")
    collection.add_argument("--class", dest="source_class", required=True, choices=sorted(manga_atlas.SOURCE_CLASSES))
    collection.add_argument("--rights-note", required=True)
    collection.add_argument("--pixel-reuse", action="store_true")
    collection.add_argument("--derivative-reuse", action="store_true")
    collection.add_argument("--publication-reuse", action="store_true")
    collection.add_argument("--future-members-inherit", action="store_true")
    collection.add_argument("--member", action="append", default=[])

    source_from_collection = sub.add_parser("source-from-collection")
    source_from_collection.add_argument("source_image")
    source_from_collection.add_argument("collection_json")
    source_from_collection.add_argument("external_id")
    source_from_collection.add_argument("output_json")
    source_from_collection.add_argument("--label", default="")
    source_from_collection.add_argument("--family", action="append", default=[])
    source_from_collection.add_argument("--page-role", choices=sorted(manga_atlas.PAGE_ROLES))
    source_from_collection.add_argument("--continuity-group")
    source_from_collection.add_argument("--motif", action="append", default=[])
    source_from_collection.add_argument("--sequence-index", type=int)
    source_from_collection.add_argument("--observed-membership", action="store_true")
    source_from_collection.add_argument("--observed-membership", action="store_true")

    batch_run = sub.add_parser("batch-run")
    batch_run.add_argument("batch_manifest_json")
    batch_run.add_argument("source_dir")
    batch_run.add_argument("output_dir")

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

    if args.command == "collection":
        members = []
        for raw in args.member:
            if "=" in raw:
                external_id, title = raw.split("=", 1)
            else:
                external_id, title = raw, raw
            members.append({"externalId": external_id, "title": title})
        result = manga_atlas.collection_manifest(
            label=args.label,
            collection_id=args.collection_id,
            collection_url=args.collection_url,
            source_class=args.source_class,
            pixel_reuse=args.pixel_reuse,
            derivative_reuse=args.derivative_reuse,
            publication_reuse=args.publication_reuse,
            rights_note=args.rights_note,
            member_snapshot=members,
            future_members_inherit=args.future_members_inherit,
        )
        _write(Path(args.output_json).expanduser().resolve(), result)
    elif args.command == "source-from-collection":
        result = manga_atlas.source_from_collection(
            args.source_image,
            _read(args.collection_json),
            external_id=args.external_id,
            label=args.label,
            grammar_families=args.family,
            page_role=args.page_role,
            continuity_group=args.continuity_group,
            motifs=args.motif,
            sequence_index=args.sequence_index,
            observed_membership=args.observed_membership,
        )
        _write(Path(args.output_json).expanduser().resolve(), result)
    elif args.command == "batch-run":
        result = manga_atlas.run_owned_batch(
            _read(args.batch_manifest_json),
            args.source_dir,
            args.output_dir,
        )
    elif args.command == "source":
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
            observed_membership=args.observed_membership,
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
