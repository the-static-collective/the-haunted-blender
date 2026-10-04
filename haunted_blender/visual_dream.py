"""A bounded dream walk over an explicitly authored, frozen fictional world."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from . import catalog, project, scene_weave, take_cut

SCORE = "haunted-blender/visual-dream-score/v0"
PLAN = "haunted-blender/visual-dream-plan/v0"
RECEIPT = "haunted-blender/visual-dream-receipt/v0"
RELATIONS = ("association", "contradiction", "residue")
CAMERAS = ("front", "threshold", "behind")
MAX_STEPS = 12
FPS, WIDTH, HEIGHT = 12, 480, 270


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def digest(data):
    return hashlib.sha256(project.stable_bytes(data)).hexdigest()


def _read_score(root, score_path):
    path = Path(score_path).expanduser().resolve(strict=True)
    vault = Path(root).expanduser().resolve() / "snapshots" / "visual-dream"
    require(path.parent == vault, "Dream score must be frozen inside the private vault")
    score = json.loads(path.read_text(encoding="utf-8"))
    require(path.name == digest(score) + ".json", "Dream score digest mismatch")
    return score


def freeze(root, score):
    """Freeze an authored score after validating its world and bounded walk."""
    result = compile_plan(root, score)
    vault = Path(root).expanduser().resolve() / "snapshots" / "visual-dream"
    vault.mkdir(parents=True, exist_ok=True)
    path = vault / (result["score_sha256"] + ".json")
    expected = project.stable_bytes(score) + b"\n"
    try:
        with path.open("xb") as stream:
            stream.write(expected)
    except FileExistsError:
        require(path.read_bytes() == expected, "Frozen dream score changed")
    return path


def compile_plan(root, score):
    """Return deterministic observation proposals; do not change world knowledge."""
    require(isinstance(score, dict) and set(score) == {
        "schema", "world_snapshot", "world_sha256", "beat", "start", "nodes",
        "edges", "camera_score", "max_steps"}, "Invalid dream score fields")
    require(score["schema"] == SCORE, "Unknown dream score schema")
    world = scene_weave.load_snapshot(root, score["world_snapshot"])
    require(scene_weave.sha(world) == score["world_sha256"], "World snapshot changed")
    beat = score["beat"]
    require(type(beat) is int and 0 <= beat < len(world["beats"]), "Invalid dream beat")
    steps = score["max_steps"]
    require(type(steps) is int and 1 <= steps <= MAX_STEPS, "Dream exceeds 12 steps")
    facts = {f["id"]: f for f in world["facts"] if f["since_beat"] <= beat}
    known = {k["fact_id"] for k in world["knowledge"]
             if k["observer"] == "audience" and k["since_beat"] <= beat}
    nodes = score["nodes"]
    require(isinstance(nodes, list) and 1 <= len(nodes) <= MAX_STEPS, "Invalid node count")
    require(all(isinstance(n, dict) and set(n) == {"id", "fact_id", "motif"}
                and isinstance(n["id"], str) and re.fullmatch(r"[a-z0-9_-]{1,40}", n["id"])
                and n["fact_id"] in facts and isinstance(n["motif"], str)
                and 1 <= len(n["motif"]) <= 40 for n in nodes), "Invalid dream node")
    by_id = {n["id"]: n for n in nodes}
    require(len(by_id) == len(nodes) and score["start"] in by_id, "Duplicate or unknown start node")
    edges = score["edges"]
    require(isinstance(edges, list) and len(edges) <= 36, "Too many dream edges")
    require(all(isinstance(e, dict) and set(e) == {"from", "to", "relation"}
                and e["from"] in by_id and e["to"] in by_id
                and e["from"] != e["to"] and e["relation"] in RELATIONS
                for e in edges), "Invalid authored edge")
    require(len({(e["from"], e["to"], e["relation"]) for e in edges}) == len(edges),
            "Duplicate dream edge")
    camera_score = score["camera_score"]
    require(isinstance(camera_score, list) and len(camera_score) == steps,
            "One camera position and door angle required per step")
    require(all(isinstance(c, dict) and set(c) == {"camera", "door_degrees"}
                and c["camera"] in CAMERAS and type(c["door_degrees"]) is int
                and 0 <= c["door_degrees"] <= 90 for c in camera_score),
            "Invalid camera or door angle")

    walk = []
    visited = set()
    current = score["start"]
    incoming = None
    for index in range(steps):
        node = by_id[current]
        camera = camera_score[index]
        # This gate applies to what can be depicted from the camera, not to
        # the established facts or the audience's durable knowledge record.
        threshold = {"front": 90, "threshold": 17, "behind": 43}[camera["camera"]]
        optically_available = camera["door_degrees"] >= threshold
        disclosed = node["fact_id"] in known and optically_available
        walk.append({"step": index, "node_id": current, "fact_id": node["fact_id"],
                     "motif": node["motif"], "incoming_relation": incoming,
                     "camera": camera["camera"], "door_degrees": camera["door_degrees"],
                     "optically_available": optically_available,
                     "audience_known_at_beat": node["fact_id"] in known,
                     "depict_fact": disclosed,
                     "gate": "visible" if disclosed else (
                         "knowledge_held" if node["fact_id"] not in known else "door_or_camera_held")})
        visited.add(current)
        choices = sorted((e for e in edges if e["from"] == current and e["to"] not in visited),
                         key=lambda e: (RELATIONS.index(e["relation"]), e["to"]))
        if not choices:
            break
        selected = choices[0]
        current, incoming = selected["to"], selected["relation"]
    motifs = sorted({row["motif"] for row in walk
                     if sum(x["motif"] == row["motif"] for x in walk) > 1})
    return {"schema": PLAN, "score_sha256": digest(score),
            "world_sha256": scene_weave.sha(world), "beat": beat,
            "walk": walk, "authored_motif_recurrences": motifs,
            "status": "proposal_only", "distribution_authorized": False,
            "nonclaims": ["The graph edges and motifs are authored, not inferred from media",
                          "A camera gate is a fictional depiction rule, not evidence of real events",
                          "Traversal does not establish new audience knowledge or interpret recurrence",
                          "No MEMENTO, Dogram or 3rdi service was queried or modified"]}


def plan(root, score_path):
    score = _read_score(root, score_path)
    return compile_plan(root, score)


def render(root, score_path, out):
    """Make a silent, local procedural MP4 with a frame receipt per graph step."""
    from PIL import Image, ImageDraw, ImageFont

    root = Path(root).expanduser().resolve()
    out = Path(out).expanduser().resolve()
    require(out.parent == root / "renders" / "visual-dream" and out.suffix.lower() == ".mp4",
            "Output must be an MP4 in the private visual-dream vault")
    receipt_path = out.with_suffix(".mp4.receipt.json")
    require(not out.exists() and not receipt_path.exists(), "Refusing to overwrite dream output")
    ffmpeg = shutil.which("ffmpeg")
    require(ffmpeg is not None, "FFmpeg is required")
    snapshot = plan(root, score_path)
    frames = []
    frame_map = []
    font = ImageFont.load_default()
    for item in snapshot["walk"]:
        previous = snapshot["walk"][item["step"] - 1]["door_degrees"] if item["step"] else 0
        threshold = {"front": 90, "threshold": 17, "behind": 43}[item["camera"]]
        for subframe in range(FPS):
            angle = previous + (item["door_degrees"] - previous) * (subframe + 1) / FPS
            disclosed = item["audience_known_at_beat"] and angle >= threshold
            frame = Image.new("RGB", (WIDTH, HEIGHT), "#131927")
            draw = ImageDraw.Draw(frame)
            aperture = round(220 * angle / 90)
            # Each frame's aperture and visibility use the same interpolated angle.
            draw.rectangle((130, 30, 375, 235), fill="#0b0d17", outline="#ad8155", width=5)
            draw.rectangle((132, 32, 132 + aperture, 233),
                           fill=("#395766" if disclosed else "#202b39"))
            draw.polygon(((133 + aperture, 33), (374, 33), (374, 233), (133 + aperture, 233)),
                         fill="#654633")
            draw.text((16, 13), f"DREAM {item['step'] + 1:02}  /  {item['incoming_relation'] or 'entry'}",
                      fill="#f1d7ac", font=font)
            draw.text((16, 244), f"CAMERA {item['camera']}  /  DOOR {angle:04.1f} deg",
                      fill="#f1d7ac", font=font)
            if disclosed:
                draw.text((144, 96), item["fact_id"][:27], fill="#ffffff", font=font)
                draw.text((144, 111), item["motif"][:30], fill="#f1d7ac", font=font)
            else:
                draw.text((144, 108), "[held]", fill="#b9bdc6", font=font)
            frame_map.append({"frame": len(frame_map), "step": item["step"],
                              "angle_tenths": round(angle * 10), "fact_depicted": bool(disclosed)})
            frames.append(frame.tobytes())
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="visual-dream-", dir=out.parent) as folder:
        staged = Path(folder) / "dream.mp4"
        subprocess.run([ffmpeg, "-nostdin", "-v", "error", "-f", "rawvideo",
                        "-pixel_format", "rgb24", "-video_size", f"{WIDTH}x{HEIGHT}",
                        "-framerate", str(FPS), "-i", "pipe:0", "-an",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
                        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(staged)],
                       input=b"".join(frames), capture_output=True, check=True, timeout=60)
        take_cut._probe(staged, max_seconds=MAX_STEPS + 1)
        require(plan(root, score_path) == snapshot, "Frozen dream changed during rendering")
        output_sha = catalog.digest_file(staged)
        receipt = {"schema": RECEIPT, "adapter": "procedural-door-card/v0",
                   "status": "scoped_complete", "plan": snapshot,
                   "source_score_sha256": snapshot["score_sha256"],
                   "output_sha256": output_sha, "fps": FPS,
                   "seconds_per_step": 1, "output_frame_count": len(frames),
                   "frame_map": frame_map,
                   "sound": "omitted", "distribution_authorized": False,
                   "nonclaims": snapshot["nonclaims"] + [
                       "This schematic door is not footage and does not depict a photographed person",
                       "A rendered proposal does not inherit publication or scene placement approval"]}
        created = False
        try:
            with out.open("xb") as destination, staged.open("rb") as source:
                created = True
                shutil.copyfileobj(source, destination)
            require(catalog.digest_file(out) == output_sha, "Dream output digest changed")
            with receipt_path.open("xb") as destination:
                destination.write(project.stable_bytes(receipt) + b"\n")
        except Exception:
            if created:
                out.unlink(missing_ok=True)
            raise
    return {"video": str(out), "receipt": str(receipt_path),
            "output_sha256": output_sha, "steps": len(snapshot["walk"])}
