"""N3 Living Mesh: bounded, deterministic piecewise-affine image deformation.

Pure geometry calculations follow Dogram's delta/orientation/receipt discipline,
without importing Dogram or attributing artistic, historical or causal authority to it.
N0/N1/N2 modules and frozen contracts remain untouched.
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

from . import alchemy, catalog, correspondence
from .project import stable_bytes

SCHEMA = "haunted-blender/living-mesh-recipe/v1"
FROZEN_SCHEMA = "haunted-blender/living-mesh-snapshot/v1"
GRID = 5
VERTICES = GRID * GRID
WIDTH, HEIGHT, FPS, FRAMES = correspondence.WIDTH, correspondence.HEIGHT, correspondence.FPS, correspondence.FRAMES
IDENT = re.compile(r"mesh-[0-9a-f]{16}")
MIN_AREA_PX2 = 6.0


def grid() -> list[list[float]]:
    """Canonical normalized 5x5 row-major mesh; boundary nodes remain fixed."""
    return [[col / (GRID - 1), row / (GRID - 1)]
            for row in range(GRID) for col in range(GRID)]


def triangles() -> list[tuple[int, int, int]]:
    """Fixed oriented connectivity: 32 non-overlapping triangles covering the frame."""
    result = []
    for row in range(GRID - 1):
        for col in range(GRID - 1):
            a = row * GRID + col
            result.extend([(a, a + 1, a + GRID + 1), (a, a + GRID + 1, a + GRID)])
    return result


def _path(root: Path, recipe_id: str) -> Path:
    if not isinstance(recipe_id, str) or IDENT.fullmatch(recipe_id) is None:
        raise ValueError("Invalid living-mesh recipe ID")
    return alchemy._vault(root) / "projects" / "living-mesh" / (recipe_id + ".json")


def _valid_vertices(value) -> None:
    if not isinstance(value, list) or len(value) != VERTICES:
        raise ValueError("Mesh must have exactly 25 ordered vertices")
    for point in value:
        if not isinstance(point, list) or len(point) != 2 or any(
            isinstance(x, bool) or not isinstance(x, (int, float)) or
            not math.isfinite(x) or x < 0 or x > 1 for x in point
        ):
            raise ValueError("Mesh coordinates must be finite normalized pairs in [0,1]")
    canonical = grid()
    for index, (point, reference) in enumerate(zip(value, canonical)):
        row, col = divmod(index, GRID)
        if row in (0, GRID - 1) or col in (0, GRID - 1):
            if any(abs(point[axis] - reference[axis]) > 1e-9 for axis in (0, 1)):
                raise ValueError("Boundary vertices must remain fixed in N3")


def validate(recipe: dict) -> None:
    if not isinstance(recipe, dict) or recipe.get("schema") != SCHEMA or not isinstance(recipe.get("id"), str) or IDENT.fullmatch(recipe["id"]) is None:
        raise ValueError("Invalid living-mesh recipe schema or ID")
    if recipe.get("renderer") != "pillow-triangle-mesh-ffmpeg/v1" or recipe.get("evidence_class") != "artist_proposed":
        raise ValueError("Unknown renderer or evidence class")
    if not isinstance(recipe.get("parent_snapshot"), str) or not isinstance(recipe.get("parent_sha256"), str) or re.fullmatch(r"[0-9a-f]{64}", recipe["parent_sha256"]) is None:
        raise ValueError("Invalid frozen N2 parent reference")
    for key in ("source_vertices", "target_vertices"):
        _valid_vertices(recipe.get(key))
    if not isinstance(recipe.get("max_landmark_error_px"), (float, int)) or isinstance(recipe["max_landmark_error_px"], bool) or not math.isfinite(recipe["max_landmark_error_px"]) or not 0 < recipe["max_landmark_error_px"] <= 32:
        raise ValueError("Invalid declared landmark tolerance")
    revision = recipe.get("revises")
    if revision is not None and (not isinstance(revision, str) or IDENT.fullmatch(revision) is None or revision == recipe["id"]):
        raise ValueError("Invalid revision link")


def _parent(root: Path, recipe: dict):
    parent_path = Path(recipe["parent_snapshot"])
    parent, sha = correspondence._load(root, parent_path)
    if sha != recipe["parent_sha256"]:
        raise ValueError("N2 frozen parent digest differs from recipe")
    return parent, correspondence.plan(root, parent_path)


def create(root: Path, parent_snapshot: Path, target_vertices: list[list[float]], *,
           source_vertices: list[list[float]] | None = None, max_landmark_error_px: float = 3.0,
           revises: str | None = None) -> dict:
    root = alchemy._vault(root)
    parent_path = parent_snapshot.expanduser().resolve(strict=True)
    parent, parent_sha = correspondence._load(root, parent_path)
    correspondence.plan(root, parent_path)
    if revises is not None:
        earlier = json.loads(_path(root, revises).read_text(encoding="utf-8"))
        validate(earlier)
        if earlier["parent_snapshot"] != str(parent_path) or earlier["parent_sha256"] != parent_sha:
            raise ValueError("Revision must retain its exact frozen parent")
    recipe = {
        "schema": SCHEMA, "id": "mesh-" + uuid.uuid4().hex[:16],
        "parent_snapshot": str(parent_path), "parent_sha256": parent_sha,
        "source_vertices": grid() if source_vertices is None else source_vertices,
        "target_vertices": target_vertices, "max_landmark_error_px": max_landmark_error_px,
        "renderer": "pillow-triangle-mesh-ffmpeg/v1",
        "evidence_class": "artist_proposed", "revises": revises,
    }
    validate(recipe)
    _parent(root, recipe)
    file = _path(root, recipe["id"])
    file.parent.mkdir(parents=True, exist_ok=True)
    with file.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(recipe, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    return recipe


def freeze(root: Path, recipe_id: str) -> Path:
    recipe = json.loads(_path(root, recipe_id).read_text(encoding="utf-8"))
    validate(recipe)
    if recipe["id"] != recipe_id:
        raise ValueError("Recipe ID differs from path")
    _parent(root, recipe)
    content = {
        "schema": FROZEN_SCHEMA, "recipe": recipe,
        "nonclaims": [
            "Local geometric orientation and declared-landmark error do not certify pixel identity",
            "A positive signed face area does not establish physical material, 3D depth or semantic continuity",
            "N3 fixes mesh connectivity; topology birth, tearing, occlusion and inpainting are not implemented",
        ],
    }
    payload = stable_bytes(content)
    digest = hashlib.sha256(payload).hexdigest()
    folder = alchemy._vault(root) / "snapshots" / "living-mesh" / recipe_id
    folder.mkdir(parents=True, exist_ok=True)
    destination = folder / (digest + ".json")
    try:
        with destination.open("xb") as handle:
            handle.write(payload + b"\n")
    except FileExistsError:
        if destination.read_bytes() != payload + b"\n":
            raise ValueError("Existing living-mesh snapshot was modified")
    return destination


def _load(root: Path, snapshot: Path):
    root = alchemy._vault(root)
    path = snapshot.expanduser().resolve(strict=True)
    base = root / "snapshots" / "living-mesh"
    if base not in path.parents:
        raise ValueError("Mesh snapshot must live inside its own vault")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != FROZEN_SCHEMA:
        raise ValueError("Invalid living-mesh snapshot schema")
    validate(payload["recipe"])
    sha = hashlib.sha256(stable_bytes(payload)).hexdigest()
    if path.name != sha + ".json" or path.parent.name != payload["recipe"]["id"] or path.parent.parent != base:
        raise ValueError("Living-mesh snapshot hash or identity mismatch")
    return payload, sha


def pixels(vertices: list[list[float]]) -> list[tuple[float, float]]:
    return [(v[0] * (WIDTH - 1), v[1] * (HEIGHT - 1)) for v in vertices]


def signed_twice_area(a, b, c) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _cross(a, b) -> float:
    return a[0] * b[1] - a[1] * b[0]


def orientation_envelope(before, after, face) -> dict:
    """Analytical minimum of signed *double* area over t in [0,1]."""
    p = [before[i] for i in face]
    q = [after[i] for i in face]
    u = (p[1][0] - p[0][0], p[1][1] - p[0][1])
    v = (p[2][0] - p[0][0], p[2][1] - p[0][1])
    du = ((q[1][0] - q[0][0]) - u[0], (q[1][1] - q[0][1]) - u[1])
    dv = ((q[2][0] - q[0][0]) - v[0], (q[2][1] - q[0][1]) - v[1])
    a0 = _cross(u, v)
    linear = _cross(du, v) + _cross(u, dv)
    quadratic = _cross(du, dv)
    candidates = [(0.0, a0), (1.0, a0 + linear + quadratic)]
    if abs(quadratic) > 1e-12:
        t = -linear / (2 * quadratic)
        if 0 < t < 1:
            candidates.append((t, a0 + linear * t + quadratic * t * t))
    min_t, min_double_area = min(candidates, key=lambda p: p[1])
    return {"source_twice_area_px2": round(a0, 9),
            "target_twice_area_px2": round(a0 + linear + quadratic, 9),
            "delta_twice_area_px2": round(linear + quadratic, 9),
            "min_twice_area_px2": round(min_double_area, 9),
            "min_at_t": round(min_t, 9)}


def _barycentric(point, face_pts):
    a, b, c = face_pts
    denominator = signed_twice_area(a, b, c)
    if abs(denominator) < 1e-12:
        return None
    b_weight = _cross((point[0] - a[0], point[1] - a[1]),
                      (c[0] - a[0], c[1] - a[1])) / denominator
    c_weight = _cross((b[0] - a[0], b[1] - a[1]),
                      (point[0] - a[0], point[1] - a[1])) / denominator
    a_weight = 1 - b_weight - c_weight
    weights = (a_weight, b_weight, c_weight)
    return weights if min(weights) >= -1e-7 else None


def _embed(point, vertex_positions, faces):
    for face_id, face in enumerate(faces):
        weights = _barycentric(point, [vertex_positions[i] for i in face])
        if weights is not None:
            return face_id, weights
    raise ValueError("Declared landmark falls outside supported oriented mesh")


def _weighted(weights, pts):
    return (sum(w * p[0] for w, p in zip(weights, pts)),
            sum(w * p[1] for w, p in zip(weights, pts)))


def _landmark_receipt(source_pts, target_pts, parent_points, faces):
    """Track inherited N2 declared landmarks through the N3 piecewise affine mesh."""
    source_image_points = [
        (point["from"][0] * (WIDTH - 1), point["from"][1] * (HEIGHT - 1))
        for point in parent_points
    ]
    target_image_points = [
        (point["to"][0] * (WIDTH - 1), point["to"][1] * (HEIGHT - 1))
        for point in parent_points
    ]
    # N2 positions are *oriented source-image fractions*, not whole-canvas fractions.
    # Caller converts them via N2's audited letterboxing map before invoking this helper.
    items = []
    worst = 0.0
    for landmark, source, target in zip(parent_points, source_image_points, target_image_points):
        source_face, weights = _embed(source, source_pts, faces)
        target_face, target_weights = _embed(target, target_pts, faces)
        if source_face != target_face:
            raise ValueError("N2 landmark crosses mesh faces: " + landmark["id"])
        face = faces[source_face]
        end = _weighted(weights, [target_pts[i] for i in face])
        start = _weighted(target_weights, [source_pts[i] for i in face])
        error = max(math.dist(end, target), math.dist(start, source))
        worst = max(worst, error)
        items.append({"id": landmark["id"], "face": source_face,
                      "source_to_target_error_px": round(math.dist(end, target), 9),
                      "target_to_source_error_px": round(math.dist(start, source), 9)})
    return worst, items


def _anchors_for_frame(path: str, parent_points: list[dict], role: str):
    canvas, anchor_list, dimensions = correspondence._image_with_points(path, parent_points, role)
    return canvas, anchor_list, dimensions


def _checks(root: Path, bundle: dict) -> dict:
    recipe = bundle["recipe"]
    parent, parent_plan = _parent(root, recipe)
    source = parent_plan["source"]
    target = parent_plan["target"]
    source_image, source_anchors, source_size = _anchors_for_frame(source["path"], parent["recipe"]["points"], "from")
    target_image, target_anchors, target_size = _anchors_for_frame(target["path"], parent["recipe"]["points"], "to")
    source_image.close()
    target_image.close()
    source_pts = pixels(recipe["source_vertices"])
    target_pts = pixels(recipe["target_vertices"])
    faces = triangles()
    face_receipts = []
    for i, face in enumerate(faces):
        record = orientation_envelope(source_pts, target_pts, face)
        if record["min_twice_area_px2"] <= 2 * MIN_AREA_PX2:
            raise ValueError("Triangle collapse or orientation flip along continuous path: face " + str(i))
        face_receipts.append({"face": i, "vertices": list(face), **record})
    # Evaluate N2 anchor positions in the actual oriented-and-letterboxed image,
    # rather than interpreting them as normalized full-canvas coordinates.
    max_error, landmark_receipts = _actual_landmarks(
        source_anchors, target_anchors, parent["recipe"]["points"],
        source_pts, target_pts, faces
    )
    if max_error > recipe["max_landmark_error_px"] + 1e-7:
        raise ValueError("Inherited N2 landmark error exceeds declared tolerance: "
                         + str(round(max_error, 6)) + " px")
    return {"source": source, "target": target, "source_size": source_size,
            "target_size": target_size, "source_pts": source_pts,
            "target_pts": target_pts, "faces": faces,
            "face_receipts": face_receipts, "landmark_receipts": landmark_receipts,
            "max_landmark_error_px": round(max_error, 9)}


def _actual_landmarks(source_anchors, target_anchors, parent_points, source_pts, target_pts, faces):
    entries = []
    worst = 0.0
    for original, s, d in zip(parent_points, source_anchors, target_anchors):
        s_face, s_weights = _embed(s, source_pts, faces)
        d_face, d_weights = _embed(d, target_pts, faces)
        if s_face != d_face:
            raise ValueError("Inherited N2 landmark crosses mesh faces: " + original["id"])
        face = faces[s_face]
        predicted_target = _weighted(s_weights, [target_pts[i] for i in face])
        predicted_source = _weighted(d_weights, [source_pts[i] for i in face])
        forward = math.dist(predicted_target, d)
        reverse = math.dist(predicted_source, s)
        worst = max(worst, forward, reverse)
        entries.append({"id": original["id"], "face": s_face,
                        "source_to_target_error_px": round(forward, 9),
                        "target_to_source_error_px": round(reverse, 9)})
    return worst, entries


def plan(root: Path, snapshot: Path) -> dict:
    bundle, sha = _load(root, snapshot)
    c = _checks(root, bundle)
    recipe = bundle["recipe"]
    return {
        "schema": "haunted-blender/living-mesh-plan/v1",
        "snapshot_sha256": sha, "parent_snapshot_sha256": recipe["parent_sha256"],
        "renderer": recipe["renderer"], "evidence_class": recipe["evidence_class"],
        "source": c["source"], "target": c["target"], "source_size": c["source_size"],
        "target_size": c["target_size"], "grid": GRID, "face_count": len(c["faces"]),
        "vertices": {"source": recipe["source_vertices"], "target": recipe["target_vertices"]},
        "face_receipts": c["face_receipts"], "landmark_receipts": c["landmark_receipts"],
        "max_inherited_landmark_error_px": c["max_landmark_error_px"],
        "allowed_landmark_error_px": recipe["max_landmark_error_px"],
        "constraints": {"triangle_orientation_all_continuous_t": "validated_analytically",
                        "inherited_n2_landmarks": "validated_geometrically",
                        "visible_pixel_identity": "not_assessed",
                        "topology_changes": "not_supported",
                        "semantic_continuity": "not_assessed"},
        "width": WIDTH, "height": HEIGHT, "fps": FPS, "frames": FRAMES,
        "nonclaims": bundle["nonclaims"],
    }


def _inverse_affine(source_tri, dest_tri):
    a, b, c = dest_tri
    det = signed_twice_area(a, b, c)
    if det <= 2 * MIN_AREA_PX2:
        raise ValueError("Degenerate or reversed destination triangle")
    sa, sb, sc = source_tri
    sx1, sx2 = sb[0] - sa[0], sc[0] - sa[0]
    sy1, sy2 = sb[1] - sa[1], sc[1] - sa[1]
    dx1, dx2 = b[0] - a[0], c[0] - a[0]
    dy1, dy2 = b[1] - a[1], c[1] - a[1]
    aa = (sx1 * dy2 - sx2 * dy1) / det
    bb = (sx2 * dx1 - sx1 * dx2) / det
    dd = (sy1 * dy2 - sy2 * dy1) / det
    ee = (sy2 * dx1 - sy1 * dx2) / det
    return (aa, bb, sa[0] - aa * a[0] - bb * a[1],
            dd, ee, sa[1] - dd * a[0] - ee * a[1])


def _warp(image, start, dest, faces):
    Image, _ = correspondence._pillow()
    from PIL import ImageDraw
    canvas = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    for face in faces:
        dest_tri = [dest[i] for i in face]
        source_tri = [start[i] for i in face]
        bounds = (max(0, int(math.floor(min(p[0] for p in dest_tri))) - 1),
                  max(0, int(math.floor(min(p[1] for p in dest_tri))) - 1),
                  min(WIDTH, int(math.ceil(max(p[0] for p in dest_tri))) + 2),
                  min(HEIGHT, int(math.ceil(max(p[1] for p in dest_tri))) + 2))
        left, top, right, bottom = bounds
        if right <= left or bottom <= top:
            continue
        aa, bb, cc, dd, ee, ff = _inverse_affine(source_tri, dest_tri)
        clipped = image.transform(
            (right - left, bottom - top), Image.Transform.AFFINE,
            (aa, bb, aa * left + bb * top + cc, dd, ee, dd * left + ee * top + ff),
            resample=Image.Resampling.BILINEAR, fillcolor=(0, 0, 0))
        mask = Image.new("L", clipped.size, 0)
        ImageDraw.Draw(mask).polygon([(p[0] - left, p[1] - top) for p in dest_tri], fill=255)
        canvas.paste(clipped, (left, top), mask)
        clipped.close()
        mask.close()
    return canvas


def render(root: Path, snapshot: Path, out: Path) -> dict:
    spec = plan(root, snapshot)
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFmpeg is required for local mesh rendering")
    Image, _ = correspondence._pillow()
    out = out.expanduser().resolve()
    receipt_file = out.with_suffix(out.suffix + ".receipt.json")
    if out.exists() or receipt_file.exists():
        raise FileExistsError("Existing video or receipt will not be overwritten")
    source_image, _, _ = _anchors_for_frame(spec["source"]["path"], [], "from")
    target_image, _, _ = _anchors_for_frame(spec["target"]["path"], [], "to")
    before = pixels(spec["vertices"]["source"])
    after = pixels(spec["vertices"]["target"])
    faces = triangles()
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="blender-living-mesh-") as folder:
        staged = Path(folder) / "mesh.mp4"
        cmd = [ffmpeg, "-nostdin", "-v", "error", "-y",
               "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size",
               str(WIDTH) + "x" + str(HEIGHT), "-framerate", str(FPS),
               "-i", "pipe:0", "-an", "-c:v", "libx264",
               "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(staged)]
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        try:
            for index in range(FRAMES):
                t = index / (FRAMES - 1)
                if index == 0:
                    frame = source_image.copy()
                elif index == FRAMES - 1:
                    frame = target_image.copy()
                else:
                    intermediate = [((1 - t) * a[0] + t * b[0],
                                     (1 - t) * a[1] + t * b[1])
                                    for a, b in zip(before, after)]
                    warped_source = _warp(source_image, before, intermediate, faces)
                    warped_target = _warp(target_image, after, intermediate, faces)
                    frame = Image.blend(warped_source, warped_target, t)
                    warped_source.close()
                    warped_target.close()
                process.stdin.write(frame.tobytes())
                frame.close()
            process.stdin.close()
            error_bytes = process.stderr.read()
            if process.wait() != 0:
                raise RuntimeError("FFmpeg mesh render failed: " + error_bytes.decode("utf-8", "replace")[-1500:])
        except BaseException:
            process.kill()
            process.wait()
            raise
        finally:
            if process.stdin is not None and not process.stdin.closed:
                process.stdin.close()
            if process.stderr is not None:
                process.stderr.close()
            source_image.close()
            target_image.close()
        plan(root, snapshot)  # Reverify N2, N1 and N0 binding before output and receipt.
        shutil.copyfile(staged, out)
    receipt = {
        "schema": "haunted-blender/living-mesh-receipt/v1", "status": "scoped_complete",
        "claim": "2D locally deformable triangle-mesh preview; not verified semantic or material metamorphosis",
        "snapshot_sha256": spec["snapshot_sha256"],
        "parent_snapshot_sha256": spec["parent_snapshot_sha256"],
        "renderer": spec["renderer"],
        "source_asset_id": spec["source"]["asset_id"],
        "target_asset_id": spec["target"]["asset_id"],
        "face_receipts": spec["face_receipts"],
        "landmark_receipts": spec["landmark_receipts"],
        "max_inherited_landmark_error_px": spec["max_inherited_landmark_error_px"],
        "constraints": spec["constraints"], "frames": FRAMES,
        "output_path": str(out), "output_sha256": catalog.digest_file(out),
        "nonclaims": spec["nonclaims"],
    }
    temp = receipt_file.with_suffix(receipt_file.suffix + ".tmp")
    try:
        with temp.open("x", encoding="utf-8") as handle:
            handle.write(stable_bytes(receipt).decode("utf-8") + "\n")
        os.replace(temp, receipt_file)
    except Exception:
        out.unlink(missing_ok=True)
        temp.unlink(missing_ok=True)
        raise
    return receipt
