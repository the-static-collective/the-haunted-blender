"""N5 Living Object: multiple frozen N4 foregrounds composed as one 2D cinematic entity.

Local and opt-in. N0-N4 files, accepted snapshots, and renderers are untouched.
Every component retains its own snapshot, material mode, z-order, opacity, and clock.
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

from . import alchemy, catalog, contour_material as n4, correspondence
from .project import stable_bytes

SCHEMA = "haunted-blender/living-object-recipe/v1"
FROZEN = "haunted-blender/living-object-snapshot/v1"
IDENT = re.compile(r"object-[0-9a-f]{16}")
NAME = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{0,39}")
SHA = re.compile(r"[0-9a-f]{64}")
WIDTH, HEIGHT, FPS, FRAMES = n4.WIDTH, n4.HEIGHT, n4.FPS, n4.FRAMES
RENDERER = "pillow-layered-object-ffmpeg/v1"


def _path(root: Path, ident: str) -> Path:
    if not isinstance(ident, str) or IDENT.fullmatch(ident) is None:
        raise ValueError("Invalid living-object ID")
    return alchemy._vault(root) / "projects" / "living-object" / (ident + ".json")


def validate(recipe: dict) -> None:
    if not isinstance(recipe, dict) or recipe.get("schema") != SCHEMA:
        raise ValueError("Unknown N5 recipe schema")
    if not isinstance(recipe.get("id"), str) or IDENT.fullmatch(recipe["id"]) is None:
        raise ValueError("Invalid living-object ID")
    if recipe.get("renderer") != RENDERER or recipe.get("evidence_class") != "artist_proposed":
        raise ValueError("Unknown N5 renderer or evidence class")
    layers = recipe.get("layers")
    if not isinstance(layers, list) or not 2 <= len(layers) <= 4:
        raise ValueError("Living object requires 2-4 independent foreground layers")
    names, zs, paths = set(), set(), set()
    for layer in layers:
        if not isinstance(layer, dict) or set(layer) != {
            "name", "snapshot", "snapshot_sha256", "z", "delay_frames", "opacity"
        }:
            raise ValueError("Layer requires name, N4 snapshot, digest, z, delay and opacity")
        if not isinstance(layer["name"], str) or NAME.fullmatch(layer["name"]) is None or layer["name"] in names:
            raise ValueError("Invalid or repeated layer name")
        if not isinstance(layer["snapshot"], str) or not layer["snapshot"]:
            raise ValueError("Missing frozen N4 layer path")
        if not isinstance(layer["snapshot_sha256"], str) or SHA.fullmatch(layer["snapshot_sha256"]) is None:
            raise ValueError("Invalid frozen N4 layer digest")
        if layer["snapshot"] in paths:
            raise ValueError("A single frozen N4 take cannot masquerade as two independent layers")
        if isinstance(layer["z"], bool) or not isinstance(layer["z"], int) or not -16 <= layer["z"] <= 16 or layer["z"] in zs:
            raise ValueError("Layer z-order must be a unique integer from -16 to 16")
        if isinstance(layer["delay_frames"], bool) or not isinstance(layer["delay_frames"], int) or not 0 <= layer["delay_frames"] <= 24:
            raise ValueError("Layer delay_frames must be an integer from 0 to 24")
        if isinstance(layer["opacity"], bool) or not isinstance(layer["opacity"], (int, float)) or not math.isfinite(layer["opacity"]) or not 0 < layer["opacity"] <= 1:
            raise ValueError("Layer opacity must be finite and between 0 (exclusive) and 1")
        names.add(layer["name"])
        zs.add(layer["z"])
        paths.add(layer["snapshot"])
    revises = recipe.get("revises")
    if revises is not None and (not isinstance(revises, str) or IDENT.fullmatch(revises) is None or revises == recipe["id"]):
        raise ValueError("Invalid N5 revision ancestry")


def _parents(root: Path, recipe: dict):
    """Verify all lineage and one genuinely common scene/background across layers."""
    members = []
    shared = None
    for layer in recipe["layers"]:
        path = Path(layer["snapshot"])
        packet, digest = n4._load(root, path)
        if digest != layer["snapshot_sha256"]:
            raise ValueError("N4 layer digest changed: " + layer["name"])
        proof = n4.plan(root, path)  # Rechecks N0/N1/N2/N3, geometry, and plate.
        source = proof["source"]
        target = proof["target"]
        plate = proof["clean_plate"]
        scene = (
            packet["recipe"]["parent_sha256"],
            source["sha256"], target["sha256"],
            proof["background_mode"],
            plate["requested"]["sha256"] if plate else None,
            plate["frame"]["sha256"] if plate else None,
        )
        if shared is None:
            shared = scene
        elif scene != shared:
            raise ValueError("All N5 layers must share one exact frozen scene and background")
        members.append((layer, packet, proof))
    return members


def create(root: Path, layers: list[dict], *, revises: str | None = None) -> dict:
    """Each layer input uses a frozen N4 snapshot path; SHA bindings are resolved here."""
    root = alchemy._vault(root)
    if not isinstance(layers, list):
        raise ValueError("Layers must be a JSON array")
    bound = []
    for item in layers:
        if not isinstance(item, dict) or set(item) != {"name", "snapshot", "z", "delay_frames", "opacity"}:
            raise ValueError("Each new layer needs name, snapshot, z, delay_frames and opacity")
        path = Path(item["snapshot"]).expanduser().resolve(strict=True)
        _, sha = n4._load(root, path)
        bound.append({**item, "snapshot": str(path), "snapshot_sha256": sha})
    recipe = {"schema": SCHEMA, "id": "object-" + uuid.uuid4().hex[:16],
              "renderer": RENDERER, "evidence_class": "artist_proposed",
              "layers": bound, "revises": revises}
    validate(recipe)
    _parents(root, recipe)
    if revises is not None:
        before = json.loads(_path(root, revises).read_text(encoding="utf-8"))
        validate(before)
        # Reordering and clocks may change in a revision, not the parent scene.
        if _parents(root, before)[0][2]["parent_snapshot_sha256"] != _parents(root, recipe)[0][2]["parent_snapshot_sha256"]:
            raise ValueError("N5 revision must retain the same N3 scene")
    destination = _path(root, recipe["id"])
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(recipe, sort_keys=True, indent=2, ensure_ascii=False) + "\n")
    return recipe


def freeze(root: Path, ident: str) -> Path:
    recipe = json.loads(_path(root, ident).read_text(encoding="utf-8"))
    validate(recipe)
    if recipe["id"] != ident:
        raise ValueError("N5 recipe ID differs from path")
    _parents(root, recipe)
    bundle = {
        "schema": FROZEN, "recipe": recipe,
        "nonclaims": [
            "A compositing layer is not a separately witnessed physical object",
            "An artist-assigned shared object name is not evidence that masks have common physical identity",
            "Independent component clocks do not create or prove event chronology",
            "Alpha overlap is a rendered pixel property, not physical occlusion or reconstructed depth",
            "N5 supports no splitting, fusion, holes, inferred shadow, or hidden-background reconstruction",
        ],
    }
    payload = stable_bytes(bundle)
    sha = hashlib.sha256(payload).hexdigest()
    folder = alchemy._vault(root) / "snapshots" / "living-object" / ident
    folder.mkdir(parents=True, exist_ok=True)
    result = folder / (sha + ".json")
    try:
        with result.open("xb") as handle:
            handle.write(payload + b"\n")
    except FileExistsError:
        if result.read_bytes() != payload + b"\n":
            raise ValueError("Frozen N5 snapshot was modified")
    return result


def _load(root: Path, snapshot: Path):
    root = alchemy._vault(root)
    path = snapshot.expanduser().resolve(strict=True)
    base = root / "snapshots" / "living-object"
    if base not in path.parents:
        raise ValueError("N5 snapshot must reside inside the living-object vault")
    packet = json.loads(path.read_text(encoding="utf-8"))
    if packet.get("schema") != FROZEN:
        raise ValueError("Unknown N5 snapshot schema")
    validate(packet["recipe"])
    sha = hashlib.sha256(stable_bytes(packet)).hexdigest()
    if path.name != sha + ".json" or path.parent.parent != base or path.parent.name != packet["recipe"]["id"]:
        raise ValueError("Living-object snapshot hash or identity mismatch")
    return packet, sha


def plan(root: Path, snapshot: Path) -> dict:
    packet, sha = _load(root, snapshot)
    members = _parents(root, packet["recipe"])
    layers = []
    for config, _, proof in sorted(members, key=lambda entry: entry[0]["z"]):
        layers.append({
            "name": config["name"], "z": config["z"],
            "snapshot_sha256": config["snapshot_sha256"],
            "delay_frames": config["delay_frames"], "opacity": config["opacity"],
            "material_mode": proof["material_mode"], "vertex_count": proof["vertex_count"],
            "source_sha256": proof["source"]["sha256"], "target_sha256": proof["target"]["sha256"],
            "face_receipts": proof["face_receipts"],
        })
    first = members[0][2]
    return {
        "schema": "haunted-blender/living-object-plan/v1",
        "snapshot_sha256": sha, "renderer": RENDERER,
        "parent_n3_sha256": first["parent_snapshot_sha256"],
        "background_mode": first["background_mode"],
        "clean_plate_sha256": first["clean_plate"]["frame"]["sha256"] if first["clean_plate"] else None,
        "width": WIDTH, "height": HEIGHT, "fps": FPS, "frames": FRAMES,
        "ordered_layers": layers,
        "checks": {
            "source_and_snapshot_lineage": "verified",
            "scene_and_background_compatibility": "verified",
            "mask_geometry": "verified_per_N4",
            "alpha_overlap": "measured_during_render",
            "semantic_identity": "not_assessed",
        },
        "nonclaims": packet["nonclaims"],
    }


def _prepare_layer(entry):
    """Cut out each texture before any scene compositing; source background never leaks."""
    config, packet, proof = entry
    recipe = packet["recipe"]
    s_image, source_points, _ = n4._image_and_contour(proof["source"]["path"], recipe["source_contour"])
    d_image, target_points, _ = n4._image_and_contour(proof["target"]["path"], recipe["target_contour"])
    try:
        source_cutout = n4._cutout(s_image, source_points)
        target_cutout = n4._cutout(d_image, target_points)
    finally:
        s_image.close()
        d_image.close()
    return {"config": config, "source_points": source_points, "target_points": target_points,
            "source": source_cutout, "target": target_cutout, "mode": proof["material_mode"]}


def _foreground_at(layers, frame_index: int):
    """Return transparent RGBA subject composite and independently recorded overlap statistics."""
    Image, _ = correspondence._pillow()
    from PIL import ImageChops
    scene = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    occupied = Image.new("L", (WIDTH, HEIGHT), 0)
    per_layer = []
    overlaps = 0
    for item in sorted(layers, key=lambda layer: layer["config"]["z"]):
        config = item["config"]
        delay = config["delay_frames"]
        t = max(0., min(1., (frame_index - delay) / (FRAMES - 1 - delay)))
        a, b = item["source_points"], item["target_points"]
        mid = [((1-t)*p[0]+t*q[0], (1-t)*p[1]+t*q[1]) for p,q in zip(a,b)]
        first = n4._warp_object(item["source"], n4._fan_at(a), n4._fan_at(mid), n4._fan_faces(len(a)))
        if item["mode"] == "source-only":
            subject = first
        else:
            second = n4._warp_object(item["target"], n4._fan_at(b), n4._fan_at(mid), n4._fan_faces(len(b)))
            subject = Image.blend(first, second, t)
            first.close()
            second.close()
        alpha = subject.getchannel("A")
        if config["opacity"] < 1:
            adjusted = alpha.point(lambda v: round(v * config["opacity"]))
            subject.putalpha(adjusted)
            alpha.close()
            alpha = adjusted
        binary = alpha.point(lambda v: 255 if v else 0)
        intersection = ImageChops.multiply(occupied, binary)
        overlaps += intersection.histogram()[255]
        combined = ImageChops.lighter(occupied, binary)
        occupied.close()
        occupied = combined
        pixels = binary.histogram()[255]
        per_layer.append({"name": config["name"], "z": config["z"], "local_t": round(t, 9),
                          "nonzero_alpha_px": pixels})
        scene.alpha_composite(subject)
        intersection.close()
        binary.close()
        alpha.close()
        subject.close()
    occupied.close()
    return scene, {"frame": frame_index, "layers": per_layer, "overlap_px": overlaps}


def render(root: Path, snapshot: Path, out: Path, *, alpha_preview_out: Path | None = None) -> dict:
    spec = plan(root, snapshot)
    if not shutil.which("ffmpeg"):
        raise RuntimeError("Local FFmpeg is required for N5 MP4 preview")
    out = out.expanduser().resolve()
    preview = alpha_preview_out.expanduser().resolve() if alpha_preview_out is not None else None
    receipt_path = out.with_suffix(out.suffix + ".receipt.json")
    paths = [out, receipt_path] + ([preview] if preview is not None else [])
    if len(set(paths)) != len(paths):
        raise ValueError("Output, transparent preview and receipt paths must be distinct")
    if any(path.exists() for path in paths):
        raise FileExistsError("Will not overwrite N5 output, alpha preview or receipt")
    packet, _ = _load(root, snapshot)
    members = _parents(root, packet["recipe"])
    prepared = []
    try:
        for entry in members:
            prepared.append(_prepare_layer(entry))
        background = n4._base_image(members[0][1], members[0][2])
        out.parent.mkdir(parents=True, exist_ok=True)
        if preview is not None:
            if preview.suffix.lower() != ".png":
                raise ValueError("Transparent preview must have a .png extension")
            preview.parent.mkdir(parents=True, exist_ok=True)
        measured = []
        with tempfile.TemporaryDirectory(prefix="blender-living-object-") as work:
            staged = Path(work) / "preview.mp4"
            staged_alpha = Path(work) / "midpoint.png"
            cmd = ["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo",
                   "-pixel_format", "rgb24", "-video_size", str(WIDTH)+"x"+str(HEIGHT),
                   "-framerate", str(FPS), "-i", "pipe:0", "-an", "-c:v", "libx264",
                   "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(staged)]
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            try:
                for index in range(FRAMES):
                    foreground, record = _foreground_at(prepared, index)
                    measured.append(record)
                    if preview is not None and index == FRAMES // 2:
                        foreground.save(staged_alpha, format="PNG")
                    assembled = background.copy().convert("RGBA")
                    assembled.alpha_composite(foreground)
                    rgb = assembled.convert("RGB")
                    process.stdin.write(rgb.tobytes())
                    rgb.close()
                    assembled.close()
                    foreground.close()
                process.stdin.close()
                stderr = process.stderr.read()
                if process.wait() != 0:
                    raise RuntimeError("FFmpeg living-object render failed: "
                                       + stderr.decode("utf-8", "replace")[-1600:])
            except BaseException:
                process.kill()
                process.wait()
                raise
            finally:
                if process.stdin is not None and not process.stdin.closed:
                    process.stdin.close()
                if process.stderr is not None:
                    process.stderr.close()
            # Revalidate all frozen ancestor paths, source hashes and plate before publishing.
            plan(root, snapshot)
            shutil.copyfile(staged, out)
            if preview is not None:
                shutil.copyfile(staged_alpha, preview)
        receipt = {
            "schema": "haunted-blender/living-object-receipt/v1",
            "status": "scoped_complete",
            "claim": "Bounded composited 2D foreground preview, not physical object or depth reconstruction",
            "snapshot_sha256": spec["snapshot_sha256"], "parent_n3_sha256": spec["parent_n3_sha256"],
            "renderer": RENDERER, "background_mode": spec["background_mode"],
            "clean_plate_sha256": spec["clean_plate_sha256"],
            "ordered_layers": spec["ordered_layers"],
            "frame_receipts": measured, "frame_count": FRAMES,
            "output_path": str(out), "output_sha256": catalog.digest_file(out),
            "alpha_preview_path": str(preview) if preview is not None else None,
            "alpha_preview_sha256": catalog.digest_file(preview) if preview is not None else None,
            "nonclaims": spec["nonclaims"],
        }
        temporary_receipt = receipt_path.with_suffix(receipt_path.suffix + ".tmp")
        try:
            with temporary_receipt.open("x", encoding="utf-8") as handle:
                handle.write(stable_bytes(receipt).decode("utf-8") + "\n")
            os.replace(temporary_receipt, receipt_path)
        except Exception:
            out.unlink(missing_ok=True)
            if preview is not None:
                preview.unlink(missing_ok=True)
            temporary_receipt.unlink(missing_ok=True)
            raise
        return receipt
    finally:
        for item in prepared:
            item["source"].close()
            item["target"].close()
        if "background" in locals():
            background.close()
