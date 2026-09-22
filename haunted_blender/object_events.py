"""N6 explicit event graph over a frozen N5 Living Object.

Only declared visibility and lineage change. Never interpret alpha overlap as a
physical split, join, aperture, shadow, or topology operation.
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

from . import alchemy, catalog, contour_material as n4, correspondence, living_object as n5
from .project import stable_bytes

SCHEMA = "haunted-blender/object-events-recipe/v1"
FROZEN = "haunted-blender/object-events-snapshot/v1"
RENDERER = "pillow-object-events-ffmpeg/v1"
IDENT = re.compile(r"events-[0-9a-f]{16}")
LABEL = n5.NAME
DIGEST = n5.SHA
SUPPORTED_EVENT_TYPES = frozenset({"birth", "death", "split", "join"})
RESERVED_EVENT_TYPES = frozenset({
    "reveal", "conceal", "open", "close", "detach", "attach",
    "split_many", "join_many", "part_birth", "part_death",
})
PART_ROLES = frozenset({
    "primary-mass", "rim", "interior", "handle", "shadow", "reflection",
    "split-child", "joined-part", "other",
})
WIDTH, HEIGHT, FPS, FRAMES = n5.WIDTH, n5.HEIGHT, n5.FPS, n5.FRAMES


def _path(root: Path, ident: str) -> Path:
    if not isinstance(ident, str) or IDENT.fullmatch(ident) is None:
        raise ValueError("Invalid N6 recipe ID")
    return alchemy._vault(root) / "projects" / "object-events" / (ident + ".json")


def validate(recipe: dict) -> None:
    if not isinstance(recipe, dict) or recipe.get("schema") != SCHEMA:
        raise ValueError("Unknown object-events recipe schema")
    if not isinstance(recipe.get("id"), str) or IDENT.fullmatch(recipe["id"]) is None:
        raise ValueError("Invalid N6 recipe identity")
    if recipe.get("renderer") != RENDERER or recipe.get("evidence_class") != "artist_proposed":
        raise ValueError("Unknown renderer or evidence class")
    if not isinstance(recipe.get("parent_snapshot"), str) or not isinstance(recipe.get("parent_sha256"), str) or DIGEST.fullmatch(recipe["parent_sha256"]) is None:
        raise ValueError("Missing frozen N5 parent and digest")
    revises = recipe.get("revises")
    if revises is not None and (not isinstance(revises, str) or IDENT.fullmatch(revises) is None or revises == recipe["id"]):
        raise ValueError("Invalid N6 revision ancestry")
    parts = recipe.get("parts")
    events = recipe.get("events")
    if not isinstance(parts, list) or not 2 <= len(parts) <= 8:
        raise ValueError("Declare 2-8 event-level part identities")
    if not isinstance(events, list) or not 1 <= len(events) <= 12:
        raise ValueError("Declare 1-12 explicit events")
    seen_parts = set()
    for part in parts:
        if not isinstance(part, dict) or set(part) != {"id", "source_layer_name", "role", "initial"}:
            raise ValueError("Part requires id, source_layer_name, role and initial")
        ident = part["id"]
        if not isinstance(ident, str) or LABEL.fullmatch(ident) is None or ident in seen_parts:
            raise ValueError("Invalid or duplicated part identity")
        if not isinstance(part["source_layer_name"], str) or LABEL.fullmatch(part["source_layer_name"]) is None:
            raise ValueError("Invalid N5 source layer name")
        if part["role"] not in PART_ROLES or type(part["initial"]) is not bool:
            raise ValueError("Part must have supported descriptive role and explicit initial boolean")
        seen_parts.add(ident)
    seen_events = set()
    for event in events:
        if not isinstance(event, dict) or set(event) != {"id", "type", "from", "to", "start_frame", "end_frame"}:
            raise ValueError("Event requires id, type, from, to, start_frame and end_frame")
        ident, typ = event["id"], event["type"]
        if not isinstance(ident, str) or LABEL.fullmatch(ident) is None or ident in seen_events:
            raise ValueError("Invalid or duplicate event ID")
        seen_events.add(ident)
        if typ not in SUPPORTED_EVENT_TYPES:
            if typ in RESERVED_EVENT_TYPES:
                raise ValueError("Reserved future event is not implemented in N6: " + typ)
            raise ValueError("Unknown event type")
        for key in ("start_frame", "end_frame"):
            if type(event[key]) is not int or not 0 <= event[key] < FRAMES:
                raise ValueError("Event frame must be a valid integer in 0..48")
        if event["start_frame"] >= event["end_frame"]:
            raise ValueError("Event window must span at least one frame")
        source, target = event["from"], event["to"]
        if not isinstance(source, list) or not isinstance(target, list):
            raise ValueError("Event participants must be lists")
        shapes = {"birth": (0, 1), "death": (1, 0), "split": (1, 2), "join": (2, 1)}
        if (len(source), len(target)) != shapes[typ]:
            raise ValueError("Event participant cardinality is invalid for " + typ)
        members = source + target
        if any(not isinstance(p, str) or p not in seen_parts for p in members) or len(set(members)) != len(members):
            raise ValueError("Event references unknown or repeated part")
    # Every noninitial part must have a unique producer. An existing identity
    # cannot be born again, including a recycled split parent after a join.
    producer, consumer = {}, {}
    for event in events:
        for name in event["to"]:
            if name in producer or name in consumer:
                raise ValueError("Part has duplicate or contradictory lifecycle: " + name)
            producer[name] = event
        for name in event["from"]:
            if name in consumer:
                raise ValueError("Part is consumed twice: " + name)
            consumer[name] = event
    by_id = {p["id"]: p for p in parts}
    for ident, part in by_id.items():
        born = producer.get(ident)
        died = consumer.get(ident)
        if part["initial"] and born is not None:
            raise ValueError("An initially active part cannot be born or produced twice: " + ident)
        if not part["initial"] and born is None:
            raise ValueError("Noninitial part has no producing event: " + ident)
        if born is not None and died is not None and born["end_frame"] >= died["start_frame"]:
            raise ValueError("Part cannot be consumed before its birth completes: " + ident)
    # All incoming/outgoing windows on the same part are disjoint by the
    # birth-before-consumption check, and each has at most one endpoint.
    # A directed cycle would require a part ID to be produced twice or
    # consumed before birth; nevertheless explicitly defend against it.
    edges = {p: set() for p in seen_parts}
    for event in events:
        for a in event["from"]:
            edges[a].update(event["to"])
    visiting, visited = set(), set()
    def visit(node):
        if node in visiting:
            raise ValueError("Cyclic event lineage is unsupported")
        if node in visited:
            return
        visiting.add(node)
        for child in edges[node]:
            visit(child)
        visiting.remove(node)
        visited.add(node)
    for name in sorted(edges):
        visit(name)
    for event in events:
        for name in event["from"]:
            birth = producer.get(name)
            if birth is not None and birth["end_frame"] >= event["start_frame"]:
                raise ValueError("Input does not exist before event begins: " + name)


def _parent(root: Path, recipe: dict) -> tuple[dict, dict]:
    path = Path(recipe["parent_snapshot"])
    packet, digest = n5._load(root, path)
    if digest != recipe["parent_sha256"]:
        raise ValueError("Frozen N5 parent digest has changed")
    proof = n5.plan(root, path)  # Recheck all N0-N5 sources, plates, geometry.
    names = {layer["name"] for layer in packet["recipe"]["layers"]}
    if any(part["source_layer_name"] not in names for part in recipe["parts"]):
        raise ValueError("Part references a layer absent from frozen N5")
    return packet, proof


def create(root: Path, parent_snapshot: Path, parts: list[dict],
           events: list[dict], *, revises: str | None = None) -> dict:
    root = alchemy._vault(root)
    parent = parent_snapshot.expanduser().resolve(strict=True)
    _, digest = n5._load(root, parent)
    recipe = {
        "schema": SCHEMA, "id": "events-" + uuid.uuid4().hex[:16],
        "renderer": RENDERER, "evidence_class": "artist_proposed",
        "parent_snapshot": str(parent), "parent_sha256": digest,
        "parts": parts, "events": events, "revises": revises,
    }
    validate(recipe)
    _parent(root, recipe)
    if revises is not None:
        previous = json.loads(_path(root, revises).read_text(encoding="utf-8"))
        validate(previous)
        if previous["parent_snapshot"] != str(parent) or previous["parent_sha256"] != digest:
            raise ValueError("Revision must preserve its exact frozen N5 parent")
    dest = _path(root, recipe["id"])
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(recipe, sort_keys=True, indent=2, ensure_ascii=False) + "\n")
    return recipe


def freeze(root: Path, ident: str) -> Path:
    recipe = json.loads(_path(root, ident).read_text(encoding="utf-8"))
    validate(recipe)
    if recipe["id"] != ident:
        raise ValueError("N6 recipe ID differs from path")
    _parent(root, recipe)
    bundle = {
        "schema": FROZEN, "recipe": recipe,
        "nonclaims": [
            "Part identity and lineage are artist-declared; a split does not automatically cut a contour",
            "Joined alpha masks are not proof of fusion, causal identity or material conservation",
            "Birth/death are changes of rendered visibility, not historical events or physical creation/destruction",
            "An event child may reuse a frozen N5 texture and geometry; no new media is synthesized",
            "Holes, apertures, shadows, true topology, depth and hidden-background reconstruction are not implemented",
        ],
    }
    payload = stable_bytes(bundle)
    digest = hashlib.sha256(payload).hexdigest()
    folder = alchemy._vault(root) / "snapshots" / "object-events" / ident
    folder.mkdir(parents=True, exist_ok=True)
    destination = folder / (digest + ".json")
    try:
        with destination.open("xb") as handle:
            handle.write(payload + b"\n")
    except FileExistsError:
        if destination.read_bytes() != payload + b"\n":
            raise ValueError("Existing frozen N6 snapshot differs")
    return destination


def _load(root: Path, snapshot: Path) -> tuple[dict, str]:
    path = snapshot.expanduser().resolve(strict=True)
    base = alchemy._vault(root) / "snapshots" / "object-events"
    if base not in path.parents:
        raise ValueError("Frozen N6 snapshot must remain in its own vault")
    bundle = json.loads(path.read_text(encoding="utf-8"))
    if bundle.get("schema") != FROZEN:
        raise ValueError("Unknown N6 snapshot schema")
    validate(bundle["recipe"])
    sha = hashlib.sha256(stable_bytes(bundle)).hexdigest()
    if path.parent.parent != base or path.parent.name != bundle["recipe"]["id"] or path.name != sha + ".json":
        raise ValueError("N6 snapshot hash or identity mismatch")
    return bundle, sha


def _progress(event: dict, frame: int) -> float:
    return max(0., min(1., (frame - event["start_frame"]) /
                        (event["end_frame"] - event["start_frame"])))


def frame_state(recipe: dict, frame: int) -> dict:
    if type(frame) is not int or not 0 <= frame < FRAMES:
        raise ValueError("Frame must be integer 0..48")
    # Recipe passed here must have been validated by create / plan / _load.
    values = {p["id"]: (1. if p["initial"] else 0.) for p in recipe["parts"]}
    progress = {}
    for event in sorted(recipe["events"], key=lambda e: (e["start_frame"], e["id"])):
        t = _progress(event, frame)
        if frame < event["start_frame"]:
            continue
        progress[event["id"]] = round(t, 9)
        for name in event["from"]:
            values[name] *= (1. - t)
        for name in event["to"]:
            # Noninitial identities start at 0; once produced, retain
            # their event-defined visibility until a later consuming event.
            if frame >= event["start_frame"]:
                values[name] = t
    # Important: subsequent events consume a previously born part only
    # after that part reached 1. Never re-enable consumed parts.
    return {
        "frame": frame,
        "active_parts": [p["id"] for p in recipe["parts"] if values[p["id"]] > 0],
        "effective_visibility": {k: round(v, 9) for k, v in values.items()},
        "event_progress": progress,
    }


def plan(root: Path, snapshot: Path) -> dict:
    bundle, digest = _load(root, snapshot)
    parent, proof = _parent(root, bundle["recipe"])
    recipe = bundle["recipe"]
    incoming = {p["id"]: [] for p in recipe["parts"]}
    outgoing = {p["id"]: [] for p in recipe["parts"]}
    for event in recipe["events"]:
        for source in event["from"]:
            outgoing[source].append(event["id"])
        for target in event["to"]:
            incoming[target].append(event["id"])
    return {
        "schema": "haunted-blender/object-events-plan/v1",
        "snapshot_sha256": digest,
        "parent_snapshot_sha256": recipe["parent_sha256"],
        "parent_n3_sha256": proof["parent_n3_sha256"],
        "renderer": RENDERER,
        "background_mode": proof["background_mode"],
        "ordered_layers": proof["ordered_layers"],
        "parts": recipe["parts"],
        "events": recipe["events"],
        "lineage": {key: {"produced_by": incoming[key], "consumed_by": outgoing[key]}
                    for key in incoming},
        "frame_states": [frame_state(recipe, frame) for frame in range(FRAMES)],
        "frames": FRAMES, "width": WIDTH, "height": HEIGHT, "fps": FPS,
        "checks": {
            "declared_lifecycle": "validated",
            "source_and_scene_lineage": "verified_via_N5",
            "alpha_coverage_and_overlap": "measured_during_render",
            "geometric_split_or_fusion": "not_implemented",
        },
        "nonclaims": bundle["nonclaims"],
    }


def _foreground_at(prepared: dict, parts: list[dict], state: dict, frame: int):
    Image, _ = correspondence._pillow()
    from PIL import ImageChops
    scene = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    occupied = Image.new("L", (WIDTH, HEIGHT), 0)
    records, overlap = [], 0
    for part in sorted(parts, key=lambda p: (prepared[p["source_layer_name"]]["config"]["z"], p["id"])):
        name = part["id"]
        item = prepared[part["source_layer_name"]]
        conf = item["config"]
        visibility = state["effective_visibility"][name]
        local_t = max(0., min(1., (frame - conf["delay_frames"]) /
                             (FRAMES - 1 - conf["delay_frames"])))
        a, b = item["source_points"], item["target_points"]
        intermediate = [((1-local_t)*p[0] + local_t*q[0],
                         (1-local_t)*p[1] + local_t*q[1])
                        for p, q in zip(a, b)]
        first = n4._warp_object(item["source"], n4._fan_at(a),
                                n4._fan_at(intermediate), n4._fan_faces(len(a)))
        if item["mode"] == "source-only":
            subject = first
        else:
            second = n4._warp_object(item["target"], n4._fan_at(b),
                                     n4._fan_at(intermediate), n4._fan_faces(len(b)))
            subject = Image.blend(first, second, local_t)
            first.close()
            second.close()
        alpha = subject.getchannel("A")
        effective_opacity = conf["opacity"] * visibility
        if effective_opacity != 1.:
            adjusted = alpha.point(lambda v: round(v * effective_opacity))
            subject.putalpha(adjusted)
            alpha.close()
            alpha = adjusted
        mask = alpha.point(lambda v: 255 if v else 0)
        intersection = ImageChops.multiply(occupied, mask)
        overlap += intersection.histogram()[255]
        combined = ImageChops.lighter(occupied, mask)
        occupied.close()
        occupied = combined
        coverage = mask.histogram()[255]
        records.append({
            "part_id": name, "source_layer_name": part["source_layer_name"],
            "z": conf["z"], "local_t": round(local_t, 9),
            "visibility": visibility,
            "effective_opacity": round(effective_opacity, 9),
            "nonzero_alpha_px": coverage,
        })
        scene.alpha_composite(subject)
        intersection.close()
        mask.close()
        alpha.close()
        subject.close()
    occupied.close()
    return scene, {"frame": frame, "parts": records, "overlap_px": overlap}


def render(root: Path, snapshot: Path, out: Path, *, alpha_preview_out: Path | None = None) -> dict:
    spec = plan(root, snapshot)
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("Local FFmpeg is required for N6 output")
    out = out.expanduser().resolve()
    preview = alpha_preview_out.expanduser().resolve() if alpha_preview_out is not None else None
    receipt_path = out.with_suffix(out.suffix + ".receipt.json")
    destinations = [out, receipt_path] + ([preview] if preview is not None else [])
    if len(set(destinations)) != len(destinations):
        raise ValueError("Output, receipt and alpha preview must be distinct")
    if any(p.exists() for p in destinations):
        raise FileExistsError("N6 refuses to overwrite an existing output or receipt")
    if preview is not None and preview.suffix.lower() != ".png":
        raise ValueError("Transparent preview must be a PNG file")
    bundle, _ = _load(root, snapshot)
    parent_packet, _ = n5._load(root, Path(bundle["recipe"]["parent_snapshot"]))
    members = n5._parents(root, parent_packet["recipe"])
    prepared = {}
    background = None
    try:
        for member in members:
            item = n5._prepare_layer(member)
            prepared[item["config"]["name"]] = item
        background = n4._base_image(members[0][1], members[0][2])
        out.parent.mkdir(parents=True, exist_ok=True)
        if preview is not None:
            preview.parent.mkdir(parents=True, exist_ok=True)
        measures = []
        with tempfile.TemporaryDirectory(prefix="blender-events-") as folder:
            video = Path(folder) / "object-events.mp4"
            preview_staged = Path(folder) / "event-midpoint.png"
            cmd = [ffmpeg, "-nostdin", "-v", "error", "-y", "-f", "rawvideo",
                   "-pixel_format", "rgb24", "-video_size", str(WIDTH)+"x"+str(HEIGHT),
                   "-framerate", str(FPS), "-i", "pipe:0", "-an", "-c:v", "libx264",
                   "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(video)]
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            try:
                for frame in range(FRAMES):
                    state = spec["frame_states"][frame]
                    foreground, measure = _foreground_at(prepared, spec["parts"], state, frame)
                    measures.append({**state, **measure})
                    if preview is not None and frame == FRAMES // 2:
                        foreground.save(preview_staged, format="PNG")
                    composed = background.copy().convert("RGBA")
                    composed.alpha_composite(foreground)
                    rgb = composed.convert("RGB")
                    process.stdin.write(rgb.tobytes())
                    rgb.close()
                    composed.close()
                    foreground.close()
                process.stdin.close()
                errors = process.stderr.read()
                if process.wait() != 0:
                    raise RuntimeError("FFmpeg N6 render failed: " +
                                       errors.decode("utf-8", "replace")[-1500:])
            except BaseException:
                process.kill()
                process.wait()
                raise
            finally:
                if process.stdin is not None and not process.stdin.closed:
                    process.stdin.close()
                if process.stderr is not None:
                    process.stderr.close()
            plan(root, snapshot)  # Revalidate all frozen ancestors and media before publication.
            shutil.copyfile(video, out)
            if preview is not None:
                shutil.copyfile(preview_staged, preview)
        receipt = {
            "schema": "haunted-blender/object-events-receipt/v1",
            "status": "scoped_complete",
            "claim": "Declared part-lineage and alpha visibility transitions, not geometric split or fusion",
            "snapshot_sha256": spec["snapshot_sha256"],
            "parent_snapshot_sha256": spec["parent_snapshot_sha256"],
            "renderer": RENDERER, "events": spec["events"],
            "lineage": spec["lineage"], "frame_receipts": measures,
            "frame_count": FRAMES, "background_mode": spec["background_mode"],
            "output_path": str(out), "output_sha256": catalog.digest_file(out),
            "alpha_preview_path": str(preview) if preview is not None else None,
            "alpha_preview_sha256": catalog.digest_file(preview) if preview is not None else None,
            "nonclaims": spec["nonclaims"],
        }
        temp_receipt = receipt_path.with_suffix(receipt_path.suffix + ".tmp")
        try:
            with temp_receipt.open("x", encoding="utf-8") as handle:
                handle.write(stable_bytes(receipt).decode("utf-8") + "\n")
            os.replace(temp_receipt, receipt_path)
        except Exception:
            out.unlink(missing_ok=True)
            if preview is not None:
                preview.unlink(missing_ok=True)
            temp_receipt.unlink(missing_ok=True)
            raise
        return receipt
    finally:
        for item in prepared.values():
            item["source"].close()
            item["target"].close()
        if background is not None:
            background.close()
