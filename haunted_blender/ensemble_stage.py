"""FRANKEN BLENDER 008k — Ensemble Stage / Dialogue Grammar.

Composes multiple existing 008g puppet rigs into one ordinary puppet performance.
Each rig keeps its own source authority. The ensemble layer owns only stage
placement, entrance/exit timing, dialogue turns, listener reactions, and eyelines.

The result deliberately uses the existing puppet-performance schema so 008h
stage compost, 008i moving inserts, and 008j Paper Director can consume it.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from . import material_surface, puppet_factory
from .scene_growth import TIMING_SCHEMA

SPEC_SCHEMA = "haunted-blender/ensemble-spec/v1"
ENSEMBLE_SCHEMA = "haunted-blender/ensemble-metadata/v1"

_SLOT_FRACTIONS = {
    2: (0.28, 0.72),
    3: (0.18, 0.50, 0.82),
    4: (0.12, 0.38, 0.64, 0.88),
}


def _stable(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _hash(value: object) -> str:
    return hashlib.sha256(_stable(value)).hexdigest()


def _read(path: str | Path) -> dict:
    return json.loads(Path(path).expanduser().resolve(strict=True).read_text(encoding="utf-8"))


def _image_size(path: str | Path) -> tuple[int, int]:
    from PIL import Image
    with Image.open(Path(path).expanduser().resolve(strict=True)) as image:
        return image.size


def _rig_bounds(rig: dict) -> tuple[float, float, float, float]:
    boxes = []
    for part in rig["parts"]:
        iw, ih = _image_size(part.get("renderSource") or part["source"])
        scale = float(part.get("scale", 1))
        x = float(part.get("x", 0))
        y = float(part.get("y", 0))
        boxes.append((x, y, x + iw * scale, y + ih * scale))
    if not boxes:
        raise ValueError("Rig has no visible parts")
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


def _layout(cast: list[dict], width: int, height: int) -> dict[str, dict]:
    count = len(cast)
    if count < 2 or count > 4:
        raise ValueError("008k ensemble supports 2–4 cast members")
    centers = _SLOT_FRACTIONS[count]
    result = {}
    target_height = height * (0.62 if count <= 2 else 0.55)

    for index, member in enumerate(cast):
        rig = member["rig"]
        x1, y1, x2, y2 = _rig_bounds(rig)
        rig_h = max(1.0, y2 - y1)
        scale = float(member.get("scale") or (target_height / rig_h))
        center_x = width * float(member.get("centerX", centers[index]))
        floor_y = height * float(member.get("floorY", 0.91))
        transformed_w = (x2 - x1) * scale
        transformed_h = (y2 - y1) * scale
        origin_x = center_x - transformed_w / 2 - x1 * scale
        origin_y = floor_y - transformed_h - y1 * scale
        result[member["id"]] = {
            "scale": scale,
            "originX": origin_x,
            "originY": origin_y,
            "box": {
                "x": round(center_x - transformed_w / 2, 6),
                "y": round(floor_y - transformed_h, 6),
                "width": round(transformed_w, 6),
                "height": round(transformed_h, 6),
            },
            "side": "left" if center_x < width / 2 else "right",
        }
    return result


def _transformed_part(part: dict, placement: dict, member_index: int) -> dict:
    scale = float(placement["scale"])
    return {
        **part,
        "id": part["id"],
        "x": float(placement["originX"]) + float(part["x"]) * scale,
        "y": float(placement["originY"]) + float(part["y"]) * scale,
        "scale": float(part.get("scale", 1)) * scale,
        "rotation": float(part.get("rotation", 0)),
        "opacity": float(part.get("opacity", 1)),
        "z": 100 + member_index * 100 + int(part.get("z", 0)),
    }


def _transform_anchor(anchor: dict, placement: dict, member_index: int) -> dict:
    scale = float(placement["scale"])
    return {
        "x": float(placement["originX"]) + float(anchor["x"]) * scale,
        "y": float(placement["originY"]) + float(anchor["y"]) * scale,
        "scale": float(anchor.get("scale", 1)) * scale,
        "z": 100 + member_index * 100 + int(anchor.get("z", 55)),
    }


def _dialogue_turns(spec: dict, timing: dict, cast_ids: list[str]) -> list[dict]:
    raw = spec.get("dialogue") or []
    explicit = {}
    for row in raw:
        cue = int(row["cueIndex"])
        speaker = str(row["speakerId"])
        if speaker not in cast_ids:
            raise ValueError(f"Unknown dialogue speaker: {speaker}")
        listeners = [str(x) for x in (row.get("listenerIds") or [])]
        if not listeners:
            listeners = [x for x in cast_ids if x != speaker]
        if any(x not in cast_ids or x == speaker for x in listeners):
            raise ValueError("Dialogue listeners must be other cast members")
        explicit[cue] = (speaker, listeners)

    turns = []
    for ordinal, cue in enumerate(timing.get("lyricsCues") or []):
        speaker, listeners = explicit.get(
            int(cue["index"]),
            (cast_ids[ordinal % len(cast_ids)], []),
        )
        if not listeners:
            listeners = [x for x in cast_ids if x != speaker]
        primary = listeners[0] if listeners else None
        turns.append({
            "cueIndex": int(cue["index"]),
            "start": float(cue["start"]),
            "end": max(float(cue["start"]) + 0.12, float(cue["end"])),
            "text": cue["text"],
            "speakerId": speaker,
            "listenerIds": listeners,
            "primaryListenerId": primary,
            "assignmentAuthority": (
                "explicit" if int(cue["index"]) in explicit else "deterministic-round-robin-proposal"
            ),
        })
    return turns


def _pose_for_speaker(text: str, ordinal: int) -> str:
    if "!" in text:
        return "yell"
    if "?" in text:
        return "shrug"
    return ("talk", "point", "talk", "pray")[ordinal % 4]


def _character_pose_events(
    member_id: str,
    turns: list[dict],
    placement: dict,
) -> tuple[list[dict], list[dict]]:
    poses = []
    reactions = []
    side = placement["side"]
    look_to_stage = "look-right" if side == "left" else "look-left"

    for ordinal, turn in enumerate(turns):
        start = float(turn["start"])
        end = float(turn["end"])
        if turn["speakerId"] == member_id:
            poses.append({
                "start": start,
                "end": end,
                "pose": _pose_for_speaker(turn["text"], ordinal),
                "cueIndex": turn["cueIndex"],
                "role": "speaker",
            })
        elif member_id in turn["listenerIds"]:
            poses.append({
                "start": start,
                "end": end,
                "pose": look_to_stage,
                "cueIndex": turn["cueIndex"],
                "role": "listener-eyeline",
            })
            if turn.get("primaryListenerId") == member_id:
                react_start = min(end, start + max(0.16, (end - start) * 0.58))
                react_end = min(end + 0.28, react_start + 0.38)
                reaction_pose = "side-eye" if "?" not in turn["text"] else "shrug"
                reactions.append({
                    "start": react_start,
                    "end": react_end,
                    "pose": reaction_pose,
                    "cueIndex": turn["cueIndex"],
                    "role": "owned-reaction",
                    "speakerId": turn["speakerId"],
                })
                poses.append(reactions[-1])
    poses.sort(key=lambda row: (row["start"], row["end"], row["role"]))
    return poses, reactions


def _mouth_events_for_member(member_id: str, turns: list[dict]) -> list[dict]:
    events = []
    for turn in turns:
        if turn["speakerId"] != member_id:
            continue
        words = [w for w in str(turn["text"]).split() if w]
        if not words:
            continue
        start = float(turn["start"])
        end = max(start + 0.08, float(turn["end"]))
        each = max(0.04, (end - start) / len(words))
        for index, word in enumerate(words):
            ws = start + index * each
            we = min(end, ws + each * 0.86)
            events.append({
                "start": round(ws, 6),
                "end": round(we, 6),
                "shape": puppet_factory._shape_for_word(word),
                "word": word,
                "cueIndex": turn["cueIndex"],
                "speakerId": member_id,
            })
    return events


def _visibility_keyframes(
    frames: list[dict],
    *,
    enter_at: float,
    exit_at: float,
    duration: float,
    x_shift: float,
) -> list[dict]:
    epsilon = 0.06
    visible = []
    for frame in frames:
        row = dict(frame)
        t = float(row["time"])
        row["opacity"] = float(row.get("opacity", 1))
        if t < enter_at - 1e-9 or t > exit_at + 1e-9:
            row["opacity"] = 0.0
            row["x"] = float(row.get("x", 0)) + x_shift
        visible.append(row)

    if enter_at > 0:
        base = dict(frames[0])
        visible.extend([
            {**base, "time": max(0.0, enter_at - epsilon), "opacity": 0.0, "x": float(base.get("x", 0)) + x_shift},
            {**base, "time": enter_at, "opacity": 1.0},
        ])
    if exit_at < duration:
        tail = dict(frames[-1])
        visible.extend([
            {**tail, "time": max(enter_at, exit_at - epsilon), "opacity": 1.0},
            {**tail, "time": exit_at, "opacity": 0.0, "x": float(tail.get("x", 0)) - x_shift},
            {**tail, "time": duration, "opacity": 0.0, "x": float(tail.get("x", 0)) - x_shift},
        ])

    unique = {}
    for row in visible:
        unique[round(float(row["time"]), 6)] = row
    return [unique[key] for key in sorted(unique)]


def _mouth_visibility(
    frames: list[dict],
    *,
    enter_at: float,
    exit_at: float,
    duration: float,
) -> list[dict]:
    result = []
    for row in frames:
        new = dict(row)
        t = float(new["time"])
        if t < enter_at or t > exit_at:
            new["opacity"] = 0.0
        result.append(new)
    if enter_at > 0:
        result.append({"time": max(0.0, enter_at - 0.04), "opacity": 0.0})
    if exit_at < duration:
        result.append({"time": exit_at, "opacity": 0.0})
        result.append({"time": duration, "opacity": 0.0})
    unique = {}
    for row in result:
        unique[round(float(row["time"]), 6)] = row
    return [unique[key] for key in sorted(unique)]


def compile_ensemble(
    spec: dict,
    timing: dict,
    output_dir: str | Path,
    *,
    cutaway_plan: dict | None = None,
) -> dict:
    if spec.get("schema") != SPEC_SCHEMA:
        raise ValueError("Expected haunted-blender/ensemble-spec/v1")
    if timing.get("schema") != TIMING_SCHEMA:
        raise ValueError("Expected normalized track timing")
    duration = float(timing["duration"])
    if duration <= 0:
        raise ValueError("Timing duration must be positive")

    raw_cast = spec.get("cast") or []
    if not (2 <= len(raw_cast) <= 4):
        raise ValueError("Ensemble requires 2–4 cast members")

    cast = []
    seen = set()
    for row in raw_cast:
        member_id = str(row.get("id") or "").strip()
        if not member_id or member_id in seen:
            raise ValueError("Cast ids must be unique and non-empty")
        seen.add(member_id)
        rig = _read(row["rigPath"]) if row.get("rigPath") else row.get("rig")
        if not isinstance(rig, dict) or rig.get("schema") != puppet_factory.RIG_SCHEMA:
            raise ValueError(f"Cast member {member_id} lacks a valid puppet rig")
        cast.append({**row, "id": member_id, "rig": rig})

    canvas = cast[0]["rig"]["canvas"]
    width, height, fps = int(canvas["width"]), int(canvas["height"]), int(canvas["fps"])
    for member in cast[1:]:
        other = member["rig"]["canvas"]
        if (
            int(other["width"]) != width
            or int(other["height"]) != height
            or int(other["fps"]) != fps
        ):
            raise ValueError("All ensemble rigs must share canvas geometry and fps")

    root = Path(output_dir).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    geo_dir = root / "lyric-geography"
    geo_dir.mkdir(parents=True, exist_ok=True)

    placements = _layout(cast, width, height)
    cast_ids = [m["id"] for m in cast]
    turns = _dialogue_turns(spec, timing, cast_ids)

    layers = [{
        "id": "room",
        "source": cast[0]["rig"]["room"]["path"],
        "z": 0,
        "x": 0,
        "y": 0,
    }]

    geography = []
    for n, cue in enumerate(timing.get("lyricsCues") or []):
        out = geo_dir / f"cue-{cue['index']:04d}.png"
        asset = puppet_factory._lyric_geography_asset(
            cue, out, width=width, height=height, variant=n
        )
        geography.append({"cueIndex": cue["index"], **asset})
        layers.append(
            puppet_factory._cue_layer(cue, asset, duration=duration, z=8)
        )

    cast_meta = []
    all_pose_events = []
    all_mouth_events = []
    all_reactions = []

    for member_index, member in enumerate(cast):
        member_id = member["id"]
        rig = member["rig"]
        placement = placements[member_id]
        enter_at = max(0.0, min(duration, float(member.get("enterAt", 0))))
        exit_at = max(enter_at, min(duration, float(member.get("exitAt", duration))))
        x_shift = -width * 0.18 if placement["side"] == "left" else width * 0.18

        pose_events, reactions = _character_pose_events(
            member_id, turns, placement
        )
        mouth_events = _mouth_events_for_member(member_id, turns)
        all_pose_events.extend({**row, "characterId": member_id} for row in pose_events)
        all_mouth_events.extend(mouth_events)
        all_reactions.extend({**row, "characterId": member_id} for row in reactions)

        for part in rig["parts"]:
            transformed = _transformed_part(part, placement, member_index)
            frames = puppet_factory._hold_keyframes(
                transformed, pose_events, duration=duration, fps=fps
            )
            frames = material_surface.apply_motion(
                frames,
                part.get("material") or rig.get("materialDefaults"),
                fps=fps,
                role=part["role"],
            )
            frames = _visibility_keyframes(
                frames,
                enter_at=enter_at,
                exit_at=exit_at,
                duration=duration,
                x_shift=x_shift,
            )
            layers.append({
                "id": f"{member_id}--{part['id']}",
                "source": part.get("renderSource") or part["source"],
                "sourceAuthoritySha256": part["sourceSha256"],
                "material": part.get("material"),
                "materializedAssetId": part.get("materializedAssetId"),
                "z": transformed["z"],
                "x": transformed["x"],
                "y": transformed["y"],
                "scale": transformed["scale"],
                "rotation": transformed["rotation"],
                "opacity": 0.0 if enter_at > 0 else transformed["opacity"],
                "keyframes": frames,
            })

        mouth_anchor = _transform_anchor(rig["mouth"], placement, member_index)
        for shape in puppet_factory.MOUTH_SHAPES:
            mouth_frames = puppet_factory._opacity_keyframes(
                shape, mouth_events, duration=duration, fps=fps
            )
            mouth_frames = _mouth_visibility(
                mouth_frames,
                enter_at=enter_at,
                exit_at=exit_at,
                duration=duration,
            )
            layers.append({
                "id": f"{member_id}--mouth-{shape}",
                "source": rig["mouth"]["atlas"][shape]["path"],
                "z": mouth_anchor["z"],
                "x": mouth_anchor["x"],
                "y": mouth_anchor["y"],
                "scale": mouth_anchor["scale"],
                "opacity": 0.0,
                "keyframes": mouth_frames,
            })

        cast_meta.append({
            "id": member_id,
            "label": str(member.get("label") or rig.get("label") or member_id),
            "rigId": rig["id"],
            "materialDefault": rig.get("materialDefaults"),
            "materialTypes": rig.get("materialTypes") or [],
            "slot": member_index,
            "side": placement["side"],
            "box": placement["box"],
            "enterAt": round(enter_at, 6),
            "exitAt": round(exit_at, 6),
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
            layers.append(
                cutaway_machine.card_layer(
                    entry, card, duration=duration, z=1000 + index
                )
            )
            cutaway_layers.append({
                "entryId": entry["id"],
                "kind": entry["kind"],
                "card": card,
            })

    ensemble_body = {
        "schema": ENSEMBLE_SCHEMA,
        "cast": cast_meta,
        "dialogueTurns": turns,
        "reactionEvents": all_reactions,
        "castCount": len(cast_meta),
        "dialogueTurnCount": len(turns),
        "laws": [
            "SPEAKER ASSIGNMENT != VOICE IDENTITY",
            "LISTENER REACTION != INNER STATE",
            "EYELINE != GAZE EVIDENCE",
            "CAST PLACEMENT != CHARACTER AUTHORITY",
            "REACTION OWNERSHIP IS EDITORIAL GRAMMAR",
        ],
    }
    ensemble = {**ensemble_body, "id": "ensemble:" + _hash(ensemble_body)[:24]}

    plan = {
        "schema": puppet_factory.CUTOUT_SCHEMA,
        "canvas": {
            "width": width,
            "height": height,
            "fps": fps,
            "duration": duration,
        },
        "layers": layers,
    }

    body = {
        "schema": puppet_factory.PERFORMANCE_SCHEMA,
        "rigId": ensemble["id"],
        "timingId": timing["id"],
        "duration": duration,
        "poseEvents": all_pose_events,
        "mouthEvents": all_mouth_events,
        "lyricGeography": geography,
        "cutaways": cutaway_layers,
        "cutoutPlan": plan,
        "ensemble": ensemble,
        "materials": {
            "cast": {
                row["id"]: {
                    "default": row.get("materialDefault"),
                    "types": row.get("materialTypes") or [],
                }
                for row in cast_meta
            },
            "room": (cast[0]["rig"].get("room") or {}).get("material"),
        },
        "cost": {"externalGenerations": 0, "providerCredits": 0, "usdMicros": 0},
        "laws": [
            "MIXED MATERIAL CAST != COLLAPSED MATERIAL IDENTITY",
            "ENSEMBLE PERFORMANCE != MULTIPLE SOURCE AUTHORITIES COLLAPSED",
            "ONE ROOM MAY HOST MULTIPLE HASHED RIGS",
            "ONLY ASSIGNED SPEAKER RECEIVES MOUTH EVENTS",
            "LISTENER MAY REACT WITHOUT SPEAKING",
            "ENTRANCE AND EXIT ARE STAGE GRAMMAR",
        ],
    }
    return {**body, "id": "puppet-performance:" + _hash(body)[:24]}
