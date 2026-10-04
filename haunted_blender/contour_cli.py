"""N4 command door: explicit object contours on an inherited frozen N3 scene."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import contour_material


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="haunted-contour",
        description="Local masked-object material and shape cartridge; N0-N3 remain unchanged",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create")
    create.add_argument("root", type=Path)
    create.add_argument("living_mesh_snapshot", type=Path)
    create.add_argument("contours_json", type=Path,
                        help="Private JSON object with source and target ordered normalized polygon points")
    create.add_argument("--material", choices=contour_material.MATERIAL_MODES,
                        default="source-only")
    create.add_argument("--background", choices=contour_material.BACKGROUND_MODES,
                        default="diagnostic-matte")
    create.add_argument("--clean-plate-asset-id", default=None)
    create.add_argument("--revises", help="Existing N4 recipe ID; creates a new independent revision")
    for name in ("freeze", "plan", "render"):
        command = sub.add_parser(name)
        command.add_argument("root", type=Path)
        command.add_argument("recipe_id" if name == "freeze" else "snapshot")
        if name == "render":
            command.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "create":
        contours = json.loads(args.contours_json.expanduser().resolve(strict=True).read_text(encoding="utf-8"))
        if not isinstance(contours, dict) or set(contours) != {"source", "target"}:
            raise ValueError("Contour JSON requires exactly source and target")
        result = contour_material.create(
            args.root, args.living_mesh_snapshot,
            source_contour=contours["source"], target_contour=contours["target"],
            material_mode=args.material, background_mode=args.background,
            clean_plate_asset_id=args.clean_plate_asset_id, revises=args.revises,
        )
    elif args.command == "freeze":
        result = {"snapshot": str(contour_material.freeze(args.root, args.recipe_id))}
    elif args.command == "plan":
        result = contour_material.plan(args.root, Path(args.snapshot))
    else:
        result = contour_material.render(args.root, Path(args.snapshot), args.out)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
