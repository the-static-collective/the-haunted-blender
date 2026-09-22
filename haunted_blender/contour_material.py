"""N4 Contour & Material: explicit closed-object masks with separate shape and material.

Only inherited N3 frozen source/target images are read. The full-frame N3 renderer,
N2 correspondence engine, N1 alchemy and N0 film/catalog are never modified.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

from . import alchemy, catalog, correspondence, living_mesh
from .project import stable_bytes

SCHEMA = "haunted-blender/contour-recipe/v1"
FROZEN_SCHEMA = "haunted-blender/contour-snapshot/v1"
IDENT = re.compile(r"contour-[0-9a-f]{16}")
DIGEST = re.compile(r"[0-9a-f]{64}")
WIDTH, HEIGHT, FPS, FRAMES = living_mesh.WIDTH, living_mesh.HEIGHT, living_mesh.FPS, living_mesh.FRAMES
MIN_DOUBLE_AREA = 12.0
MATERIAL_MODES = ("source-only", "crossfade")
BACKGROUND_MODES = ("diagnostic-matte", "clean-plate")
DIAGNOSTIC_COLOR = (13, 21, 37)


def _path(root: Path, ident: str) -> Path:
    if not isinstance(ident, str) or IDENT.fullmatch(ident) is None:
        raise ValueError("Invalid N4 contour ID")
    return alchemy._vault(root) / "projects" / "contour" / (ident + ".json")


def _valid_contour(contour) -> None:
    if not isinstance(contour, list) or not 3 <= len(contour) <= 12:
        raise ValueError("Contour must have 3-12 ordered vertices")
    for xy in contour:
        if not isinstance(xy, list) or len(xy) != 2 or any(
            isinstance(x, bool) or not isinstance(x, (int, float)) or
            not math.isfinite(x) or not 0 <= x <= 1 for x in xy
        ):
            raise ValueError("Contour coordinates must be finite normalized [x,y] pairs")


def validate(recipe: dict) -> None:
    if not isinstance(recipe, dict) or recipe.get("schema") != SCHEMA:
        raise ValueError("Unknown N4 recipe schema")
    if not isinstance(recipe.get("id"), str) or IDENT.fullmatch(recipe["id"]) is None:
        raise ValueError("Invalid contour recipe ID")
    if not isinstance(recipe.get("parent_snapshot"), str) or not isinstance(recipe.get("parent_sha256"), str) or DIGEST.fullmatch(recipe["parent_sha256"]) is None:
        raise ValueError("Missing frozen N3 parent and digest")
    for key in ("source_contour", "target_contour"):
        _valid_contour(recipe.get(key))
    if len(recipe["source_contour"]) != len(recipe["target_contour"]):
        raise ValueError("Source and target contours must have the same ordered vertex count")
    if recipe.get("material_mode") not in MATERIAL_MODES:
        raise ValueError("Unknown or unsupported material mode")
    if recipe.get("background_mode") not in BACKGROUND_MODES:
        raise ValueError("Unknown background mode")
    plate = recipe.get("clean_plate_asset_id")
    if recipe["background_mode"] == "diagnostic-matte" and plate is not None:
        raise ValueError("Diagnostic matte cannot claim a clean plate")
    if recipe["background_mode"] == "clean-plate" and (not isinstance(plate, str) or re.fullmatch(r"asset-[0-9a-f]{24}", plate) is None):
        raise ValueError("Clean-plate mode requires an explicitly cataloged image asset")
    if recipe.get("evidence_class") != "artist_proposed" or recipe.get("renderer") != "pillow-contour-fan-ffmpeg/v1":
        raise ValueError("Unknown evidence or renderer contract")
    previous = recipe.get("revises")
    if previous is not None and (not isinstance(previous, str) or IDENT.fullmatch(previous) is None or previous == recipe["id"]):
        raise ValueError("Invalid revision reference")


def _parent(root: Path, recipe: dict) -> dict:
    parent_path = Path(recipe["parent_snapshot"])
    _, sha = living_mesh._load(root, parent_path)
    if sha != recipe["parent_sha256"]:
        raise ValueError("Frozen N3 parent digest mismatch")
    return living_mesh.plan(root, parent_path)


def _source_record(row) -> dict:
    path = Path(row["path"])
    if not path.is_file() or catalog.digest_file(path) != row["sha256"]:
        raise ValueError("Clean plate changed since cataloging: " + str(path))
    return {"id": row["id"], "path": str(path), "sha256": row["sha256"],
            "kind": row["kind"], "rights": row["rights"]}


def _resolve_plate(root: Path, asset_id: str) -> dict:
    con = catalog.connect(alchemy._vault(root))
    try:
        row = con.execute("SELECT * FROM assets WHERE id=?", (asset_id,)).fetchone()
        if row is None:
            raise ValueError("Unknown clean-plate asset")
        frame = catalog.source_for_render(con, asset_id)
        return {"requested": _source_record(row), "frame": _source_record(frame)}
    finally:
        con.close()


def create(root: Path, parent_snapshot: Path, source_contour: list[list[float]],
           target_contour: list[list[float]], *,
           material_mode: str = "source-only",
           background_mode: str = "diagnostic-matte",
           clean_plate_asset_id: str | None = None, revises: str | None = None) -> dict:
    root = alchemy._vault(root)
    path = parent_snapshot.expanduser().resolve(strict=True)
    _, sha = living_mesh._load(root, path)
    if revises is not None:
        former = json.loads(_path(root, revises).read_text(encoding="utf-8"))
        validate(former)
        if former["parent_snapshot"] != str(path) or former["parent_sha256"] != sha:
            raise ValueError("Revision must preserve exact frozen N3 parent")
    recipe = {
        "schema": SCHEMA, "id": "contour-" + uuid.uuid4().hex[:16],
        "parent_snapshot": str(path), "parent_sha256": sha,
        "source_contour": source_contour, "target_contour": target_contour,
        "material_mode": material_mode, "background_mode": background_mode,
        "clean_plate_asset_id": clean_plate_asset_id,
        "renderer": "pillow-contour-fan-ffmpeg/v1",
        "evidence_class": "artist_proposed", "revises": revises,
    }
    validate(recipe)
    _parent(root, recipe)
    if clean_plate_asset_id is not None:
        _resolve_plate(root, clean_plate_asset_id)
    target = _path(root, recipe["id"])
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8") as file:
        file.write(json.dumps(recipe, sort_keys=True, indent=2, ensure_ascii=False) + "\n")
    return recipe


def freeze(root: Path, recipe_id: str) -> Path:
    recipe = json.loads(_path(root, recipe_id).read_text(encoding="utf-8"))
    validate(recipe)
    if recipe["id"] != recipe_id:
        raise ValueError("N4 recipe ID mismatch")
    _parent(root, recipe)
    plate = _resolve_plate(root, recipe["clean_plate_asset_id"]) if recipe["clean_plate_asset_id"] else None
    bundle = {
        "schema": FROZEN_SCHEMA, "recipe": recipe, "clean_plate": plate,
        "nonclaims": [
            "Polygon and vertex correspondences are artist-authored, not detected object identities",
            "N4 renders its own isolated object; N3 whole-frame pixels are not implicitly used as background",
            "Diagnostic matte is not the source scene; a separate clean plate is only user-declared",
            "No uncovered background is reconstructed, and visual material continuity is not physical conservation",
            "Convex polygon and positive fan orientation do not prove semantic identity or three-dimensional topology",
        ],
    }
    payload = stable_bytes(bundle)
    sha = hashlib.sha256(payload).hexdigest()
    folder = alchemy._vault(root) / "snapshots" / "contour" / recipe_id
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / (sha + ".json")
    try:
        with dest.open("xb") as f:
            f.write(payload + b"\n")
    except FileExistsError:
        if dest.read_bytes() != payload + b"\n":
            raise ValueError("Existing N4 snapshot differs")
    return dest


def _load(root: Path, snapshot: Path):
    path = snapshot.expanduser().resolve(strict=True)
    base = alchemy._vault(root) / "snapshots" / "contour"
    if base not in path.parents:
        raise ValueError("N4 snapshot must remain in its own vault")
    bundle = json.loads(path.read_text(encoding="utf-8"))
    if bundle.get("schema") != FROZEN_SCHEMA:
        raise ValueError("Unknown N4 snapshot schema")
    validate(bundle["recipe"])
    sha = hashlib.sha256(stable_bytes(bundle)).hexdigest()
    if path.name != sha + ".json" or path.parent.parent != base or path.parent.name != bundle["recipe"]["id"]:
        raise ValueError("N4 snapshot hash or identity mismatch")
    if (bundle["clean_plate"] is None) != (bundle["recipe"]["background_mode"] == "diagnostic-matte"):
        raise ValueError("N4 clean-plate binding mismatch")
    if bundle["clean_plate"] is not None:
        if bundle["clean_plate"]["requested"]["id"] != bundle["recipe"]["clean_plate_asset_id"]:
            raise ValueError("N4 clean-plate asset ID mismatch")
        for record in (bundle["clean_plate"]["requested"], bundle["clean_plate"]["frame"]):
            if not Path(record["path"]).is_file() or catalog.digest_file(Path(record["path"])) != record["sha256"]:
                raise ValueError("Frozen clean plate missing or changed")
    return bundle, sha


def _image_and_contour(path: str, coords: list[list[float]]):
    # Reuse N2's EXIF-aware, aspect-preserving source-image coordinate transform.
    data = [{"from": point, "to": point} for point in coords]
    image, positions, dimensions = correspondence._image_with_points(path, data, "from")
    return image, positions, dimensions


def _centroid(polygon):
    return (sum(point[0] for point in polygon) / len(polygon),
            sum(point[1] for point in polygon) / len(polygon))


def _fan_at(polygon):
    return [_centroid(polygon)] + polygon


def _fan_faces(count: int):
    return [(0, i + 1, ((i + 1) % count) + 1) for i in range(count)]


def _area(polygon):
    return .5 * sum(living_mesh._cross(a, b) for a, b in
                    zip(polygon, polygon[1:] + polygon[:1]))


def _geometry(source, target):
    """Check full continuous 2D orientation of a convex contour and its fan."""
    n = len(source)
    if n != len(target):
        raise ValueError("Contour count changed")
    src_fan, dst_fan = _fan_at(source), _fan_at(target)
    face_receipts = []
    for face_id, face in enumerate(_fan_faces(n)):
        proof = living_mesh.orientation_envelope(src_fan, dst_fan, face)
        if proof["min_twice_area_px2"] <= MIN_DOUBLE_AREA:
            raise ValueError("Contour fan collapse or orientation reversal: face " + str(face_id))
        face_receipts.append({"face": face_id, **proof})
    # Convexity of the boundary is a separate constraint; a positive fan is not by
    # itself a proof that the polygon has no concave corner.
    for i in range(n):
        face = ((i - 1) % n + 1, i + 1, (i + 1) % n + 1)
        if living_mesh.orientation_envelope(src_fan, dst_fan, face)["min_twice_area_px2"] <= MIN_DOUBLE_AREA:
            raise ValueError("Contour is nonconvex, folded or degenerate during transition")
    return face_receipts


def _base_image(bundle, source_plan):
    Image, _ = correspondence._pillow()
    plate = bundle["clean_plate"]
    if plate is None:
        return Image.new("RGB", (WIDTH, HEIGHT), DIAGNOSTIC_COLOR)
    canvas, _, _ = _image_and_contour(plate["frame"]["path"], [])
    return canvas


def plan(root: Path, snapshot: Path) -> dict:
    bundle, sha = _load(root, snapshot)
    recipe = bundle["recipe"]
    parent = _parent(root, recipe)
    source_img, s, s_size = _image_and_contour(parent["source"]["path"], recipe["source_contour"])
    target_img, d, d_size = _image_and_contour(parent["target"]["path"], recipe["target_contour"])
    source_img.close()
    target_img.close()
    receipts = _geometry(s, d)
    src_area, dst_area = _area(s), _area(d)
    plate = bundle["clean_plate"]
    return {
        "schema": "haunted-blender/contour-plan/v1",
        "snapshot_sha256": sha, "parent_snapshot_sha256": recipe["parent_sha256"],
        "renderer": recipe["renderer"], "material_mode": recipe["material_mode"],
        "background_mode": recipe["background_mode"], "clean_plate": plate,
        "source": parent["source"], "target": parent["target"], "source_size": s_size,
        "target_size": d_size, "source_contour_px": s, "target_contour_px": d,
        "vertex_count": len(s), "face_receipts": receipts,
        "source_area_px2": round(src_area, 6), "target_area_px2": round(dst_area, 6),
        "area_delta_px2": round(dst_area - src_area, 6),
        "frame_count": FRAMES, "fps": FPS, "width": WIDTH, "height": HEIGHT,
        "constraints": {"convex_contour_all_t": "validated_analytically",
                        "fan_orientation_all_t": "validated_analytically",
                        "material_identity": "artist_declared",
                        "background_hole_filling": "not_performed",
                        "n3_geometry_pixels_as_background": "not_used"},
        "nonclaims": bundle["nonclaims"],
    }


def _cutout(image, polygon):
    Image, _ = correspondence._pillow()
    from PIL import ImageDraw
    mask = Image.new("L", (WIDTH, HEIGHT), 0)
    ImageDraw.Draw(mask).polygon(polygon, fill=255)
    rgba = image.convert("RGBA")
    rgba.putalpha(mask)
    mask.close()
    return rgba


def _warp_object(image, before, after, faces):
    """Warp RGBA texture separately inside each contour fan face."""
    Image, _ = correspondence._pillow()
    from PIL import ImageDraw, ImageChops
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    for face in faces:
        dst = [after[i] for i in face]
        src = [before[i] for i in face]
        l = max(0, int(math.floor(min(p[0] for p in dst))) - 1)
        t = max(0, int(math.floor(min(p[1] for p in dst))) - 1)
        r = min(WIDTH, int(math.ceil(max(p[0] for p in dst))) + 2)
        b = min(HEIGHT, int(math.ceil(max(p[1] for p in dst))) + 2)
        if r <= l or b <= t:
            continue
        a, bb, c, d, e, f = living_mesh._inverse_affine(src, dst)
        tile = image.transform((r-l, b-t), Image.Transform.AFFINE,
                               (a, bb, a*l + bb*t + c, d, e, d*l + e*t + f),
                               resample=Image.Resampling.BILINEAR, fillcolor=(0, 0, 0, 0))
        triangle = Image.new("L", (r-l, b-t), 0)
        ImageDraw.Draw(triangle).polygon([(p[0]-l, p[1]-t) for p in dst], fill=255)
        original_alpha = tile.getchannel("A")
        clipped_alpha = ImageChops.multiply(original_alpha, triangle)
        tile.putalpha(clipped_alpha)
        canvas.alpha_composite(tile, (l, t))
        original_alpha.close()
        clipped_alpha.close()
        triangle.close()
        tile.close()
    return canvas


def _compose_frame(source_cutout, target_cutout, base, source, target, t, material_mode):
    Image, _ = correspondence._pillow()
    intermediate = [((1-t)*a[0] + t*b[0], (1-t)*a[1] + t*b[1])
                    for a, b in zip(source, target)]
    source_warp = _warp_object(source_cutout, _fan_at(source), _fan_at(intermediate), _fan_faces(len(source)))
    if material_mode == "source-only":
        subject = source_warp
    else:
        target_warp = _warp_object(target_cutout, _fan_at(target), _fan_at(intermediate), _fan_faces(len(target)))
        subject = Image.blend(source_warp, target_warp, t)
        source_warp.close()
        target_warp.close()
    alpha = subject.getchannel("A")
    coverage = sum(alpha.histogram()[1:])
    frame = base.copy().convert("RGBA")
    frame.alpha_composite(subject)
    rgb = frame.convert("RGB")
    frame.close()
    alpha.close()
    subject.close()
    return rgb, coverage


def render(root: Path, snapshot: Path, out: Path) -> dict:
    spec = plan(root, snapshot)
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("FFmpeg required for N4 video preview")
    out = out.expanduser().resolve()
    receipt_path = out.with_suffix(out.suffix + ".receipt.json")
    if out.exists() or receipt_path.exists():
        raise FileExistsError("N4 will not overwrite an existing video or receipt")
    source_image, source_coords, _ = _image_and_contour(spec["source"]["path"],
                                                        _load(root, snapshot)[0]["recipe"]["source_contour"])
    target_image, target_coords, _ = _image_and_contour(spec["target"]["path"], _load(root, snapshot)[0]["recipe"]["target_contour"])
    source_cutout = _cutout(source_image, source_coords)
    target_cutout = _cutout(target_image, target_coords)
    source_image.close()
    target_image.close()
    bundle, _ = _load(root, snapshot)
    base = _base_image(bundle, spec)
    out.parent.mkdir(parents=True, exist_ok=True)
    coverage = []
    with tempfile.TemporaryDirectory(prefix="blender-contour-") as folder:
        staged = Path(folder) / "contour.mp4"
        cmd = [ffmpeg, "-nostdin", "-v", "error", "-y", "-f", "rawvideo",
               "-pixel_format", "rgb24", "-video_size", str(WIDTH)+"x"+str(HEIGHT),
               "-framerate", str(FPS), "-i", "pipe:0", "-an", "-c:v",
               "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(staged)]
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        try:
            for index in range(FRAMES):
                image, count = _compose_frame(source_cutout, target_cutout, base,
                                              source_coords, target_coords,
                                              index/(FRAMES-1), spec["material_mode"])
                coverage.append(count)
                process.stdin.write(image.tobytes())
                image.close()
            process.stdin.close()
            stderr = process.stderr.read()
            if process.wait() != 0:
                raise RuntimeError("FFmpeg contour render failed: " + stderr.decode("utf-8", "replace")[-1500:])
        except BaseException:
            process.kill()
            process.wait()
            raise
        finally:
            if process.stdin is not None and not process.stdin.closed:
                process.stdin.close()
            if process.stderr is not None:
                process.stderr.close()
            source_cutout.close()
            target_cutout.close()
            base.close()
        plan(root, snapshot)  # Full inherited source and frozen clean-plate recheck.
        shutil.copyfile(staged, out)
    receipt = {
        "schema": "haunted-blender/contour-receipt/v1", "status": "scoped_complete",
        "claim": "Artist-masked 2D polygon material/shape preview, not background reconstruction or semantic metamorphosis",
        "snapshot_sha256": spec["snapshot_sha256"],
        "parent_snapshot_sha256": spec["parent_snapshot_sha256"],
        "renderer": spec["renderer"], "material_mode": spec["material_mode"],
        "background_mode": spec["background_mode"], "face_receipts": spec["face_receipts"],
        "area_delta_px2": spec["area_delta_px2"], "alpha_coverage_px": coverage,
        "source_sha256": spec["source"]["sha256"], "target_sha256": spec["target"]["sha256"],
        "clean_plate_sha256": spec["clean_plate"]["frame"]["sha256"] if spec["clean_plate"] else None,
        "frame_count": FRAMES, "constraints": spec["constraints"],
        "output_path": str(out), "output_sha256": catalog.digest_file(out),
        "nonclaims": spec["nonclaims"],
    }
    temp = receipt_path.with_suffix(receipt_path.suffix + ".tmp")
    try:
        with temp.open("x", encoding="utf-8") as f:
            f.write(stable_bytes(receipt).decode("utf-8") + "\n")
        os.replace(temp, receipt_path)
    except Exception:
        out.unlink(missing_ok=True)
        temp.unlink(missing_ok=True)
        raise
    return receipt
