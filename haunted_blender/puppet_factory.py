"""FRANKEN BLENDER 008g — Cutout Puppet Factory.

One authored puppet + one room + lyric timing can produce long deterministic
limited-animation footage at zero provider cost.

The aesthetic is intentionally visible machinery: flat parts, hinge rotation,
mouth swaps, hold poses, abrupt reactions, and lyrics used as scenery.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from pathlib import Path

from .cutout_stage import SCHEMA as CUTOUT_SCHEMA, render_cutout
from .scene_growth import TIMING_SCHEMA

SPEC_SCHEMA = "haunted-blender/puppet-spec/v1"
RIG_SCHEMA = "haunted-blender/cutout-puppet-rig/v1"
PERFORMANCE_SCHEMA = "haunted-blender/puppet-performance/v1"

MOUTH_SHAPES = ("closed", "open", "wide", "round", "teeth", "shout")

POSE_GRAMMAR = {
    "idle": {},
    "talk": {
        "head": {"rotation": -2},
        "arm-right": {"rotation": -8},
    },
    "yell": {
        "head": {"rotation": -7, "y": -3},
        "arm-left": {"rotation": -25},
        "arm-right": {"rotation": 28},
        "body": {"rotation": 2},
    },
    "point": {
        "arm-right": {"rotation": -48, "x": 7},
        "head": {"rotation": -3},
    },
    "shrug": {
        "arm-left": {"rotation": -30, "y": -4},
        "arm-right": {"rotation": 30, "y": -4},
        "head": {"y": -2},
    },
    "side-eye": {
        "head": {"rotation": 4, "x": 3},
    },
    "look-left": {
        "head": {"rotation": -5, "x": -4},
    },
    "look-right": {
        "head": {"rotation": 5, "x": 4},
    },
    "pray": {
        "arm-left": {"rotation": 36, "x": 7},
        "arm-right": {"rotation": -36, "x": -7},
        "head": {"rotation": 3},
    },
    "walk": {
        "body": {"x": 8, "rotation": 2},
        "head": {"x": 8},
        "arm-left": {"x": 8, "rotation": 18},
        "arm-right": {"x": 8, "rotation": -18},
        "leg-left": {"x": 8, "rotation": -12},
        "leg-right": {"x": 8, "rotation": 12},
    },
    "fall": {
        "body": {"rotation": 76, "x": 16, "y": 18},
        "head": {"rotation": 68, "x": 20, "y": 12},
        "arm-left": {"rotation": 90, "x": 18, "y": 16},
        "arm-right": {"rotation": 70, "x": 16, "y": 18},
        "leg-left": {"rotation": 70, "x": 12, "y": 18},
        "leg-right": {"rotation": 80, "x": 14, "y": 18},
    },
}

_ROLE_Z = {
    "background": 0,
    "leg-left": 20,
    "leg-right": 21,
    "body": 30,
    "arm-left": 40,
    "arm-right": 41,
    "head": 50,
    "prop": 60,
    "foreground": 80,
}


def _stable(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _hash(value: object) -> str:
    return hashlib.sha256(_stable(value)).hexdigest()


def _file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _font(size: int):
    from PIL import ImageFont
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _safe_name(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value)).strip("-")
    return value or "asset"


def create_room(
    output_path: str | Path,
    *,
    width: int,
    height: int,
    label: str = "room",
) -> dict:
    from PIL import Image, ImageDraw

    out = Path(output_path).expanduser().resolve()
    if out.exists():
        raise FileExistsError("Room generator never overwrites")
    out.parent.mkdir(parents=True, exist_ok=True)

    image = Image.new("RGBA", (width, height), (41, 44, 48, 255))
    draw = ImageDraw.Draw(image)
    # Construction-paper blocks: intentionally flat and obvious.
    floor_y = round(height * 0.69)
    draw.rectangle((0, floor_y, width, height), fill=(71, 57, 47, 255))
    draw.rectangle(
        (round(width * 0.08), round(height * 0.10), round(width * 0.32), round(height * 0.44)),
        fill=(22, 25, 30, 255),
        outline=(226, 226, 218, 255),
        width=max(2, width // 240),
    )
    draw.rectangle(
        (round(width * 0.70), round(height * 0.18), round(width * 0.91), floor_y),
        fill=(54, 45, 38, 255),
        outline=(12, 12, 12, 255),
        width=max(2, width // 240),
    )
    # A visibly crooked baseboard is part of the language.
    draw.line(
        (0, floor_y - 3, width, floor_y + 2),
        fill=(226, 226, 218, 255),
        width=max(2, width // 300),
    )
    draw.text((12, 8), str(label), font=_font(max(12, width // 48)), fill=(190, 190, 184, 180))
    image.save(out)
    return {"path": str(out), "sha256": _file_sha(out)}


def create_mouth_atlas(output_dir: str | Path, *, width: int = 56, height: int = 30) -> dict:
    from PIL import Image, ImageDraw

    root = Path(output_dir).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    result = {}
    for shape in MOUTH_SHAPES:
        out = root / f"mouth-{shape}.png"
        if out.exists():
            raise FileExistsError("Mouth atlas never overwrites")
        image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        cx, cy = width // 2, height // 2
        ink = (18, 18, 18, 255)
        paper = (244, 237, 218, 255)
        if shape == "closed":
            draw.line((8, cy, width - 8, cy), fill=ink, width=3)
        elif shape == "open":
            draw.ellipse((12, 7, width - 12, height - 6), fill=ink)
            draw.ellipse((18, 11, width - 18, height - 10), fill=(165, 82, 78, 255))
        elif shape == "wide":
            draw.ellipse((6, 9, width - 6, height - 8), fill=ink)
            draw.rectangle((14, 12, width - 14, height - 12), fill=(177, 79, 73, 255))
        elif shape == "round":
            r = min(width, height) // 3
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=ink)
            draw.ellipse((cx - r // 2, cy - r // 2, cx + r // 2, cy + r // 2), fill=(165, 82, 78, 255))
        elif shape == "teeth":
            draw.rectangle((9, 8, width - 9, height - 7), fill=ink)
            draw.rectangle((13, 11, width - 13, height - 12), fill=paper)
            draw.line((cx, 11, cx, height - 12), fill=(120, 120, 115, 255), width=1)
        elif shape == "shout":
            draw.ellipse((8, 3, width - 8, height - 3), fill=ink)
            draw.ellipse((17, 9, width - 17, height - 8), fill=(151, 62, 64, 255))
        image.save(out)
        result[shape] = {"path": str(out), "sha256": _file_sha(out)}
    return result


def build_rig(spec: dict, output_dir: str | Path) -> dict:
    if not isinstance(spec, dict) or spec.get("schema") != SPEC_SCHEMA:
        raise ValueError("Expected haunted-blender/puppet-spec/v1")
    canvas = spec.get("canvas") or {}
    width = int(canvas.get("width", 0))
    height = int(canvas.get("height", 0))
    fps = int(canvas.get("fps", 0))
    if width < 64 or height < 64 or fps < 1:
        raise ValueError("Puppet canvas is invalid")

    raw_parts = spec.get("parts")
    if not isinstance(raw_parts, list) or not raw_parts:
        raise ValueError("Puppet requires part images")

    parts = []
    roles = set()
    ids = set()
    for index, raw in enumerate(raw_parts):
        role = str(raw.get("role") or "").strip()
        part_id = str(raw.get("id") or role or f"part-{index:02d}")
        source = Path(str(raw.get("source") or "")).expanduser().resolve(strict=True)
        if role not in _ROLE_Z or role in {"background", "foreground"}:
            raise ValueError(f"Unsupported puppet role: {role}")
        if part_id in ids:
            raise ValueError("Puppet part ids must be unique")
        ids.add(part_id)
        roles.add(role)
        parts.append({
            "id": part_id,
            "role": role,
            "source": str(source),
            "sourceSha256": _file_sha(source),
            "x": float(raw.get("x", 0)),
            "y": float(raw.get("y", 0)),
            "scale": float(raw.get("scale", 1)),
            "rotation": float(raw.get("rotation", 0)),
            "opacity": float(raw.get("opacity", 1)),
            "z": int(raw.get("z", _ROLE_Z[role])),
        })
    if "body" not in roles or "head" not in roles:
        raise ValueError("Puppet requires at least body and head")

    root = Path(output_dir).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)

    room_source = spec.get("roomSource")
    if room_source:
        room = Path(str(room_source)).expanduser().resolve(strict=True)
        room_witness = {"path": str(room), "sha256": _file_sha(room)}
    else:
        room_witness = create_room(
            root / "room.png",
            width=width,
            height=height,
            label=str(spec.get("roomLabel") or "ROOM"),
        )

    mouths = create_mouth_atlas(root / "mouth-atlas")
    anchor = spec.get("mouthAnchor") or {}
    mouth = {
        "x": float(anchor.get("x", width * 0.48)),
        "y": float(anchor.get("y", height * 0.36)),
        "scale": float(anchor.get("scale", 1)),
        "z": int(anchor.get("z", 55)),
        "atlas": mouths,
    }

    body = {
        "schema": RIG_SCHEMA,
        "label": str(spec.get("label") or "puppet"),
        "canvas": {"width": width, "height": height, "fps": fps},
        "room": room_witness,
        "parts": parts,
        "mouth": mouth,
        "poseGrammar": sorted(POSE_GRAMMAR),
        "laws": [
            "RIG != PERFORMANCE",
            "PART IMAGE != JOINT AUTHORITY",
            "MOUTH SHAPE != PHONETIC CLAIM",
            "CRUDE MOTION IS AN INTENTIONAL STYLE SURFACE",
        ],
    }
    rig = {**body, "id": "cutout-puppet-rig:" + _hash(body)[:24]}
    path = root / "puppet-rig.json"
    if path.exists():
        raise FileExistsError("Puppet rig never overwrites")
    path.write_text(json.dumps(rig, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rig


def _shape_for_word(word: str) -> str:
    token = re.sub(r"[^A-Za-z]+", "", word).lower()
    if not token:
        return "closed"
    if any(v in token for v in ("ow", "oo", "ou")) or token[0] in "ou":
        return "round"
    if token[0] in "ae":
        return "wide"
    if token[0] in "iy":
        return "teeth"
    if len(token) >= 8:
        return "shout"
    return "open"


def mouth_events(timing: dict) -> list[dict]:
    if timing.get("schema") != TIMING_SCHEMA:
        raise ValueError("Expected normalized track timing")
    events = []
    for cue in timing.get("lyricsCues") or []:
        words = [w for w in cue["text"].split() if w]
        if not words:
            continue
        start = float(cue["start"])
        end = max(start + 0.08, float(cue["end"]))
        span = max(0.08, end - start)
        each = span / len(words)
        for index, word in enumerate(words):
            ws = start + index * each
            we = min(end, ws + each * 0.86)
            events.append({
                "start": round(ws, 6),
                "end": round(we, 6),
                "shape": _shape_for_word(word),
                "word": word,
                "cueIndex": cue["index"],
            })
    return events


def pose_events(timing: dict) -> list[dict]:
    if timing.get("schema") != TIMING_SCHEMA:
        raise ValueError("Expected normalized track timing")
    cycle = ("talk", "point", "shrug", "side-eye", "look-left", "look-right", "pray", "walk")
    events = []
    for n, cue in enumerate(timing.get("lyricsCues") or []):
        text = cue["text"]
        pose = "yell" if "!" in text else ("shrug" if "?" in text else cycle[n % len(cycle)])
        events.append({
            "start": float(cue["start"]),
            "end": max(float(cue["start"]) + 0.12, float(cue["end"])),
            "pose": pose,
            "cueIndex": cue["index"],
        })
    return events


def _base_state(part: dict) -> dict:
    return {
        "x": float(part["x"]),
        "y": float(part["y"]),
        "scale": float(part.get("scale", 1)),
        "rotation": float(part.get("rotation", 0)),
        "opacity": float(part.get("opacity", 1)),
    }


def _pose_state(part: dict, pose: str) -> dict:
    base = _base_state(part)
    delta = POSE_GRAMMAR.get(pose, {}).get(part["role"], {})
    for key, value in delta.items():
        if key in {"x", "y", "rotation"}:
            base[key] += float(value)
        elif key == "scale":
            base[key] *= float(value)
        elif key == "opacity":
            base[key] = min(1.0, max(0.0, base[key] * float(value)))
    return base


def _hold_keyframes(part: dict, events: list[dict], *, duration: float, fps: int) -> list[dict]:
    base = _base_state(part)
    epsilon = min(0.04, 0.45 / fps)
    frames = [{"time": 0.0, **base}]
    for event in events:
        start = max(0.0, min(duration, float(event["start"])))
        end = max(start, min(duration, float(event["end"])))
        posed = _pose_state(part, event["pose"])
        if start > 0:
            frames.append({"time": round(max(0.0, start - epsilon), 6), **base})
        frames.append({"time": round(start, 6), **posed})
        if end > start:
            frames.append({"time": round(max(start, end - epsilon), 6), **posed})
            frames.append({"time": round(end, 6), **base})
    frames.append({"time": duration, **base})
    # Same-time keyframes can arise from touching lyric cues; keep the later one.
    unique = {}
    for frame in frames:
        unique[round(float(frame["time"]), 6)] = frame
    return [unique[key] for key in sorted(unique)]


def _opacity_keyframes(
    shape: str,
    events: list[dict],
    *,
    duration: float,
    fps: int,
) -> list[dict]:
    epsilon = min(0.025, 0.35 / fps)
    frames = [{"time": 0.0, "opacity": 0.0}]
    for event in events:
        if event["shape"] != shape:
            continue
        start = max(0.0, min(duration, float(event["start"])))
        end = max(start, min(duration, float(event["end"])))
        if start > 0:
            frames.append({"time": round(max(0.0, start - epsilon), 6), "opacity": 0.0})
        frames.append({"time": round(start, 6), "opacity": 1.0})
        frames.append({"time": round(max(start, end - epsilon), 6), "opacity": 1.0})
        frames.append({"time": round(end, 6), "opacity": 0.0})
    frames.append({"time": duration, "opacity": 0.0})
    unique = {}
    for frame in frames:
        unique[round(float(frame["time"]), 6)] = frame
    return [unique[key] for key in sorted(unique)]


def _lyric_geography_asset(
    cue: dict,
    output_path: Path,
    *,
    width: int,
    height: int,
    variant: int,
) -> dict:
    from PIL import Image, ImageDraw

    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    words = cue["text"].split()
    if not words:
        words = ["..."]
    font = _font(max(16, width // 38))
    base_y = round(height * (0.56 + (variant % 3) * 0.045))
    step_w = max(46, round(width * 0.11))
    x = 12
    for index, word in enumerate(words[:8]):
        y = base_y - (index % 4) * round(height * 0.055)
        box_w = min(step_w + len(word) * 4, max(52, width - x - 8))
        draw.rectangle(
            (x, y, min(width - 6, x + box_w), min(height - 6, y + round(height * 0.105))),
            fill=(232, 224, 204, 238),
            outline=(22, 22, 22, 255),
            width=max(2, width // 320),
        )
        draw.text((x + 5, y + 5), word, font=font, fill=(18, 18, 18, 255))
        x += max(26, box_w - 7)
        if x > width - 80:
            x = 12 + (variant % 2) * 24
            base_y = min(height - 60, base_y + round(height * 0.115))
    image.save(output_path)
    return {"path": str(output_path), "sha256": _file_sha(output_path)}


def _cue_layer(
    cue: dict,
    asset: dict,
    *,
    duration: float,
    z: int,
) -> dict:
    start = max(0.0, float(cue["start"]) - 0.08)
    end = min(duration, max(float(cue["end"]), float(cue["start"]) + 0.3) + 0.10)
    return {
        "id": f"lyric-geography-{cue['index']:04d}",
        "source": asset["path"],
        "z": z,
        "x": 0,
        "y": 0,
        "opacity": 0.0,
        "keyframes": [
            {"time": 0.0, "opacity": 0.0},
            {"time": round(start, 6), "opacity": 0.0},
            {"time": round(min(duration, start + 0.04), 6), "opacity": 1.0},
            {"time": round(max(start, end - 0.04), 6), "opacity": 1.0},
            {"time": round(end, 6), "opacity": 0.0},
            {"time": duration, "opacity": 0.0},
        ],
    }


def compile_performance(
    rig: dict,
    timing: dict,
    output_dir: str | Path,
    *,
    cutaway_plan: dict | None = None,
) -> dict:
    if rig.get("schema") != RIG_SCHEMA:
        raise ValueError("Expected cutout puppet rig")
    if timing.get("schema") != TIMING_SCHEMA:
        raise ValueError("Expected normalized track timing")
    duration = float(timing["duration"])
    if duration <= 0:
        raise ValueError("Performance duration must be positive")

    root = Path(output_dir).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    geography_dir = root / "lyric-geography"
    geography_dir.mkdir(parents=True, exist_ok=True)

    canvas = rig["canvas"]
    width, height, fps = int(canvas["width"]), int(canvas["height"]), int(canvas["fps"])
    poses = pose_events(timing)
    mouths = mouth_events(timing)

    layers = [{
        "id": "room",
        "source": rig["room"]["path"],
        "z": 0,
        "x": 0,
        "y": 0,
    }]

    geography = []
    for n, cue in enumerate(timing.get("lyricsCues") or []):
        out = geography_dir / f"cue-{cue['index']:04d}.png"
        asset = _lyric_geography_asset(cue, out, width=width, height=height, variant=n)
        geography.append({"cueIndex": cue["index"], **asset})
        layers.append(_cue_layer(cue, asset, duration=duration, z=8))

    for part in rig["parts"]:
        layers.append({
            "id": part["id"],
            "source": part["source"],
            "z": part["z"],
            "x": part["x"],
            "y": part["y"],
            "scale": part["scale"],
            "rotation": part["rotation"],
            "opacity": part["opacity"],
            "keyframes": _hold_keyframes(part, poses, duration=duration, fps=fps),
        })

    mouth_anchor = rig["mouth"]
    for shape in MOUTH_SHAPES:
        layers.append({
            "id": f"mouth-{shape}",
            "source": mouth_anchor["atlas"][shape]["path"],
            "z": mouth_anchor["z"],
            "x": mouth_anchor["x"],
            "y": mouth_anchor["y"],
            "scale": mouth_anchor["scale"],
            "opacity": 0.0,
            "keyframes": _opacity_keyframes(shape, mouths, duration=duration, fps=fps),
        })

    cutaway_layers = []
    if cutaway_plan is not None:
        from . import cutaway_machine
        if cutaway_plan.get("schema") != cutaway_machine.SCHEMA:
            raise ValueError("Unsupported cutaway plan")
        card_dir = root / "cutaways"
        card_dir.mkdir(parents=True, exist_ok=True)
        for index, entry in enumerate(cutaway_plan.get("entries") or []):
            card = cutaway_machine.render_card(
                entry,
                card_dir / f"cutaway-{index + 1:03d}.png",
                width=width,
                height=height,
            )
            layer = cutaway_machine.card_layer(
                entry, card, duration=duration, z=1000 + index
            )
            layers.append(layer)
            cutaway_layers.append({
                "entryId": entry["id"],
                "kind": entry["kind"],
                "card": card,
            })

    plan = {
        "schema": CUTOUT_SCHEMA,
        "canvas": {
            "width": width,
            "height": height,
            "fps": fps,
            "duration": duration,
        },
        "layers": layers,
    }
    body = {
        "schema": PERFORMANCE_SCHEMA,
        "rigId": rig["id"],
        "timingId": timing["id"],
        "duration": duration,
        "poseEvents": poses,
        "mouthEvents": mouths,
        "lyricGeography": geography,
        "cutaways": cutaway_layers,
        "cutoutPlan": plan,
        "cost": {"externalGenerations": 0, "providerCredits": 0, "usdMicros": 0},
        "laws": [
            "WORDS MAY BECOME SCENERY",
            "MOUTH FLIP != SPEECH RECOGNITION",
            "POSE GRAMMAR != FULL-BODY GENERATION",
            "HOLD FRAMES ARE A FEATURE",
            "ONE RIG MAY PRODUCE UNBOUNDED PROVIDER-FREE DURATION",
        ],
    }
    return {**body, "id": "puppet-performance:" + _hash(body)[:24]}


def render_performance(performance: dict, output_path: str | Path) -> dict:
    if performance.get("schema") != PERFORMANCE_SCHEMA:
        raise ValueError("Expected puppet performance")
    output = Path(output_path).expanduser().resolve()
    receipt = render_cutout(performance["cutoutPlan"], output)
    result = {
        "schema": "haunted-blender/puppet-performance-receipt/v1",
        "performanceId": performance["id"],
        "output": str(output),
        "outputSha256": receipt["outputSha256"],
        "durationSeconds": receipt["durationSeconds"],
        "frameCount": receipt["frameCount"],
        "poseEventCount": len(performance["poseEvents"]),
        "mouthEventCount": len(performance["mouthEvents"]),
        "lyricGeographyCount": len(performance["lyricGeography"]),
        "cutawayCount": len(performance["cutaways"]),
        "externalGenerations": 0,
        "providerCredits": 0,
        "usdMicros": 0,
        "laws": [
            "PUPPET RENDER != FINAL CUT",
            "LOCAL LIMITED ANIMATION != PROVIDER GENERATION",
        ],
    }
    receipt_path = output.with_suffix(output.suffix + ".puppet.json")
    if receipt_path.exists():
        raise FileExistsError("Puppet performance receipt never overwrites")
    receipt_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
