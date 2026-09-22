"""N2 optional geometry cartridge: artist-authored point correspondences, never inferred identities.

Builds on a frozen N1 alchemy snapshot. Neither N0 film schema nor N1 recipe/renderer is changed.
Pillow is needed only when planning/rendering this explicit cartridge.
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

from . import alchemy, catalog
from .project import stable_bytes

SCHEMA = "haunted-blender/correspondence-recipe/v1"
SNAPSHOT_SCHEMA = "haunted-blender/correspondence-snapshot/v1"
WIDTH, HEIGHT, FPS, FRAMES = 320, 180, 24, 49
IDENT = re.compile(r"correspondence-[0-9a-f]{16}")
LANDMARK = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}")
MIN_SEPARATION_PX = 8.0


def _pillow():
    try:
        from PIL import Image, ImageOps
    except ImportError as exc:
        raise RuntimeError("Correspondence cartridge requires optional Pillow: python -m pip install Pillow") from exc
    return Image, ImageOps


def _vault(root: Path) -> Path:
    return alchemy._vault(root)


def _recipe_path(root: Path, recipe_id: str) -> Path:
    if not isinstance(recipe_id, str) or IDENT.fullmatch(recipe_id) is None:
        raise ValueError("Invalid correspondence recipe ID")
    return _vault(root) / "projects" / "correspondence" / (recipe_id + ".json")


def validate(recipe: dict) -> None:
    if not isinstance(recipe, dict) or recipe.get("schema") != SCHEMA:
        raise ValueError("Unknown correspondence recipe schema")
    if not isinstance(recipe.get("id"), str) or IDENT.fullmatch(recipe["id"]) is None:
        raise ValueError("Invalid correspondence recipe ID")
    if not isinstance(recipe.get("parent_snapshot"), str):
        raise ValueError("Missing frozen alchemy parent")
    if not isinstance(recipe.get("parent_sha256"), str) or re.fullmatch(r"[0-9a-f]{64}", recipe["parent_sha256"]) is None:
        raise ValueError("Invalid parent snapshot digest")
    if recipe.get("from_role") == recipe.get("to_role") or not all(
        isinstance(recipe.get(k), str) for k in ("from_role", "to_role")
    ):
        raise ValueError("Two different ordered participant roles are required")
    if not isinstance(recipe.get("max_error_px"), (int, float)) or isinstance(recipe["max_error_px"], bool) or not math.isfinite(recipe["max_error_px"]) or not 0 < recipe["max_error_px"] <= 32:
        raise ValueError("Invalid maximum geometric reprojection error")
    points = recipe.get("points")
    if not isinstance(points, list) or not 2 <= len(points) <= 16:
        raise ValueError("Provide 2–16 explicit point correspondences")
    labels = set()
    for point in points:
        if not isinstance(point, dict) or set(point) != {"id", "from", "to"}:
            raise ValueError("Each correspondence needs id, from, and to")
        label = point["id"]
        if not isinstance(label, str) or LANDMARK.fullmatch(label) is None or label in labels:
            raise ValueError("Invalid or duplicate correspondence label")
        labels.add(label)
        for role in ("from", "to"):
            xy = point[role]
            if not isinstance(xy, list) or len(xy) != 2 or any(
                isinstance(v, bool) or not isinstance(v, (float, int)) or not math.isfinite(v) or not 0 <= v <= 1
                for v in xy
            ):
                raise ValueError("Point positions must be finite normalized [x,y] coordinates in [0,1]")
    for role in ("from", "to"):
        a, b = points[0][role], points[1][role]
        if math.hypot(a[0] - b[0], a[1] - b[1]) < 0.025:
            raise ValueError("First two landmarks must be distinct and well-separated")
    if recipe.get("renderer") != "pillow-similarity-ffmpeg/v1":
        raise ValueError("Unsupported correspondence rendering contract")
    revises = recipe.get("revises")
    if revises is not None and (not isinstance(revises, str) or IDENT.fullmatch(revises) is None or revises == recipe["id"]):
        raise ValueError("Invalid revision ancestry")


def _parent(root: Path, recipe: dict) -> tuple[dict, dict]:
    parent_path = Path(recipe["parent_snapshot"])
    bundle, sha = alchemy._load_snapshot(root, parent_path)
    if sha != recipe["parent_sha256"]:
        raise ValueError("Frozen alchemy parent identity changed")
    ordered = bundle["recipe"]["order"]
    try:
        i = ordered.index(recipe["from_role"])
    except ValueError as exc:
        raise ValueError("From-role is absent from parent") from exc
    if i + 1 >= len(ordered) or ordered[i + 1] != recipe["to_role"]:
        raise ValueError("Only two consecutive roles in the declared alchemy order can be transformed")
    return bundle, alchemy.plan(root, parent_path)


def create(root: Path, parent_snapshot: Path, points: list[dict], *, from_role: str | None = None,
           to_role: str | None = None, max_error_px: float = 2.0, revises: str | None = None) -> dict:
    root = _vault(root)
    parent = parent_snapshot.expanduser().resolve(strict=True)
    bundle, parent_sha = alchemy._load_snapshot(root, parent)
    alchemy.plan(root, parent)
    order = bundle["recipe"]["order"]
    if len(order) < 2:
        raise ValueError("A transformation requires two participants")
    from_role = from_role or order[0]
    to_role = to_role or order[1]
    if revises is not None:
        earlier = json.loads(_recipe_path(root, revises).read_text(encoding="utf-8"))
        validate(earlier)
        if earlier["parent_sha256"] != parent_sha or earlier["parent_snapshot"] != str(parent):
            raise ValueError("Revisions must keep the same frozen alchemy parent")
    recipe = {
        "schema": SCHEMA, "id": "correspondence-" + uuid.uuid4().hex[:16],
        "parent_snapshot": str(parent), "parent_sha256": parent_sha,
        "from_role": from_role, "to_role": to_role,
        "points": points, "max_error_px": max_error_px,
        "renderer": "pillow-similarity-ffmpeg/v1", "revises": revises,
        "evidence_class": "artist_proposed", "coordinate_system": "normalized-oriented-source-image/v1",
    }
    validate(recipe)
    _parent(root, recipe)
    path = _recipe_path(root, recipe["id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(recipe, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    return recipe


def freeze(root: Path, recipe_id: str) -> Path:
    recipe = json.loads(_recipe_path(root, recipe_id).read_text(encoding="utf-8"))
    validate(recipe)
    if recipe["id"] != recipe_id:
        raise ValueError("Recipe identity mismatch")
    _parent(root, recipe)
    bundle = {
        "schema": SNAPSHOT_SCHEMA, "recipe": recipe,
        "nonclaims": [
            "Landmarks are artist-selected proposed correspondences, not detected identities",
            "Geometric reprojection bounds apply to declared landmark coordinates, not tracked image pixels",
            "Pixel colors, semantic meaning, true 3D shape and physical material continuity are not proven",
        ],
    }
    payload = stable_bytes(bundle)
    digest = hashlib.sha256(payload).hexdigest()
    folder = _vault(root) / "snapshots" / "correspondence" / recipe_id
    folder.mkdir(parents=True, exist_ok=True)
    destination = folder / (digest + ".json")
    try:
        with destination.open("xb") as handle:
            handle.write(payload + b"\n")
    except FileExistsError:
        if destination.read_bytes() != payload + b"\n":
            raise ValueError("Frozen correspondence snapshot was modified")
    return destination


def _load(root: Path, snapshot: Path) -> tuple[dict, str]:
    root = _vault(root)
    path = snapshot.expanduser().resolve(strict=True)
    base = root / "snapshots" / "correspondence"
    if base not in path.parents:
        raise ValueError("Snapshot must be in correspondence vault")
    bundle = json.loads(path.read_text(encoding="utf-8"))
    if bundle.get("schema") != SNAPSHOT_SCHEMA:
        raise ValueError("Unknown correspondence snapshot schema")
    recipe = bundle["recipe"]
    validate(recipe)
    sha = hashlib.sha256(stable_bytes(bundle)).hexdigest()
    if path.name != sha + ".json" or path.parent.name != recipe["id"] or path.parent.parent != base:
        raise ValueError("Correspondence snapshot hash or identity mismatch")
    return bundle, sha


def _image_with_points(path: str, points: list[dict], role: str):
    """Return letterboxed oriented RGB image and landmark positions on the 320x180 canvas."""
    Image, ImageOps = _pillow()
    with Image.open(path) as opened:
        oriented = ImageOps.exif_transpose(opened)
        oriented.load()
        original_w, original_h = oriented.size
        oriented.thumbnail((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
        left = (WIDTH - oriented.width) // 2
        top = (HEIGHT - oriented.height) // 2
        canvas.paste(oriented.convert("RGB"), (left, top))
        anchors = [(left + pt[role][0] * (oriented.width - 1),
                    top + pt[role][1] * (oriented.height - 1))
                   for pt in points]
        return canvas, anchors, [original_w, original_h]


def _similarity(source: list[tuple[float, float]], desired: list[tuple[float, float]]):
    """Return forward similarity and Pillow inverse affine coefficients."""
    (sx0, sy0), (sx1, sy1) = source[:2]
    (dx0, dy0), (dx1, dy1) = desired[:2]
    vx, vy = sx1 - sx0, sy1 - sy0
    wx, wy = dx1 - dx0, dy1 - dy0
    denom = vx * vx + vy * vy
    if denom < MIN_SEPARATION_PX ** 2 or wx * wx + wy * wy < MIN_SEPARATION_PX ** 2:
        raise ValueError("First two landmarks collapse during transformation")
    a = (wx * vx + wy * vy) / denom
    b = (wy * vx - wx * vy) / denom
    tx = dx0 - (a * sx0 - b * sy0)
    ty = dy0 - (b * sx0 + a * sy0)
    inv = 1.0 / (a * a + b * b)
    matrix = (
        a * inv, b * inv, -(a * tx + b * ty) * inv,
        -b * inv, a * inv, (b * tx - a * ty) * inv,
    )
    return (a, b, tx, ty), matrix


def _project(transform, p):
    a, b, tx, ty = transform
    return (a * p[0] - b * p[1] + tx, b * p[0] + a * p[1] + ty)


def _geometry(source, target, t):
    intermediate = [((1 - t) * s[0] + t * d[0], (1 - t) * s[1] + t * d[1])
                    for s, d in zip(source, target)]
    forward_source, inverse_source = _similarity(source, intermediate)
    forward_target, inverse_target = _similarity(target, intermediate)
    errors = [max(math.dist(_project(forward_source, s), q),
                  math.dist(_project(forward_target, d), q))
              for s, d, q in zip(source, target, intermediate)]
    return intermediate, inverse_source, inverse_target, max(errors)


def plan(root: Path, snapshot: Path) -> dict:
    bundle, sha = _load(root, snapshot)
    recipe = bundle["recipe"]
    parent_bundle, parent_plan = _parent(root, recipe)
    source = parent_bundle["sources"][recipe["from_role"]]["frame"]
    target = parent_bundle["sources"][recipe["to_role"]]["frame"]
    image_from, source_anchors, source_size = _image_with_points(source["path"], recipe["points"], "from")
    image_to, target_anchors, target_size = _image_with_points(target["path"], recipe["points"], "to")
    image_from.close()
    image_to.close()
    max_error = 0.0
    for frame in range(FRAMES):
        _, _, _, error = _geometry(source_anchors, target_anchors, frame / (FRAMES - 1))
        max_error = max(max_error, error)
    if max_error > recipe["max_error_px"]:
        raise ValueError("Declared correspondence reprojection exceeds tolerance: "
                         + str(round(max_error, 4)) + " px")
    return {
        "schema": "haunted-blender/correspondence-plan/v1",
        "snapshot_sha256": sha, "parent_snapshot_sha256": recipe["parent_sha256"],
        "relation": parent_bundle["recipe"]["relation"], "evidence_class": recipe["evidence_class"],
        "renderer": recipe["renderer"], "from_role": recipe["from_role"],
        "to_role": recipe["to_role"], "point_count": len(recipe["points"]),
        "points": recipe["points"], "max_error_px": recipe["max_error_px"],
        "max_geometric_reprojection_error_px": round(max_error, 9),
        "frames": FRAMES, "width": WIDTH, "height": HEIGHT, "fps": FPS,
        "source": {"asset_id": source["id"], "sha256": source["sha256"],
                   "path": source["path"], "size": source_size},
        "target": {"asset_id": target["id"], "sha256": target["sha256"],
                   "path": target["path"], "size": target_size},
        "constraints": {"landmark_reprojection": "validated",
                        "actual_pixel_tracking": "not_assessed",
                        "semantic_relation": "artist_proposed",
                        "materials_and_depth": "not_assessed"},
        "nonclaims": bundle["nonclaims"],
    }


def render(root: Path, snapshot: Path, out: Path) -> dict:
    spec = plan(root, snapshot)
    Image, _ = _pillow()
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFmpeg is required for the correspondence video render")
    out = out.expanduser().resolve()
    receipt_path = out.with_suffix(out.suffix + ".receipt.json")
    if out.exists() or receipt_path.exists():
        raise FileExistsError("Will not overwrite existing video or receipt")
    from_image, source_anchors, _ = _image_with_points(spec["source"]["path"], spec["points"], "from")
    to_image, target_anchors, _ = _image_with_points(spec["target"]["path"], spec["points"], "to")
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="blender-correspondence-") as folder:
        staged = Path(folder) / "take.mp4"
        cmd = [ffmpeg, "-nostdin", "-v", "error", "-y",
               "-f", "rawvideo", "-pixel_format", "rgb24",
               "-video_size", str(WIDTH) + "x" + str(HEIGHT), "-framerate", str(FPS),
               "-i", "pipe:0", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
               "-movflags", "+faststart", str(staged)]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        try:
            assert proc.stdin is not None
            for index in range(FRAMES):
                t = index / (FRAMES - 1)
                _, inv_from, inv_to, _ = _geometry(source_anchors, target_anchors, t)
                warped_from = from_image.transform(
                    (WIDTH, HEIGHT), Image.Transform.AFFINE, inv_from,
                    resample=Image.Resampling.BICUBIC, fillcolor=(0, 0, 0))
                warped_to = to_image.transform(
                    (WIDTH, HEIGHT), Image.Transform.AFFINE, inv_to,
                    resample=Image.Resampling.BICUBIC, fillcolor=(0, 0, 0))
                frame = Image.blend(warped_from, warped_to, t)
                proc.stdin.write(frame.tobytes())
            proc.stdin.close()
            error_text = proc.stderr.read() if proc.stderr is not None else b""
            if proc.wait() != 0:
                raise RuntimeError("FFmpeg correspondence render failed: " + error_text.decode("utf-8", errors="replace")[-1500:])
        except BaseException:
            proc.kill()
            proc.wait()
            raise
        finally:
            if proc.stdin is not None and not proc.stdin.closed:
                proc.stdin.close()
            if proc.stderr is not None:
                proc.stderr.close()
            from_image.close()
            to_image.close()
        # Parent snapshot and all original/derivative hashes are rechecked before publishing.
        plan(root, snapshot)
        shutil.copyfile(staged, out)
    receipt = {
        "schema": "haunted-blender/correspondence-receipt/v1",
        "status": "scoped_complete", "claim": "Geometric landmark-guided 2D morph preview, not semantic metamorphosis",
        "snapshot_sha256": spec["snapshot_sha256"], "parent_snapshot_sha256": spec["parent_snapshot_sha256"],
        "renderer": spec["renderer"], "source_asset_id": spec["source"]["asset_id"],
        "target_asset_id": spec["target"]["asset_id"], "point_count": spec["point_count"],
        "max_geometric_reprojection_error_px": spec["max_geometric_reprojection_error_px"],
        "constraints": spec["constraints"], "frames": spec["frames"],
        "output_path": str(out), "output_sha256": catalog.digest_file(out),
        "nonclaims": spec["nonclaims"],
    }
    temp = receipt_path.with_suffix(receipt_path.suffix + ".tmp")
    try:
        with temp.open("x", encoding="utf-8") as handle:
            handle.write(stable_bytes(receipt).decode("utf-8") + "\n")
        os.replace(temp, receipt_path)
    except Exception:
        out.unlink(missing_ok=True)
        temp.unlink(missing_ok=True)
        raise
    return receipt
