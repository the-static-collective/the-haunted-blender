"""FRANKEN BLENDER 008h — harvested-parts stage dresser.

Turns a Parts Drawer into ordinary Cutout Stage layers. The important composition
is appearance/motion separation: a crop from one source may be animated by a
motion behavior harvested from another source, with both provenances retained.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from . import moving_insert_stage, parts_harvester

SCHEMA = "haunted-blender/parts-stage-dressing/v1"


def _stable(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha(value: object) -> str:
    return hashlib.sha256(_stable(value)).hexdigest()


def _image_size(path: str | Path) -> tuple[int, int]:
    from PIL import Image
    with Image.open(Path(path).expanduser().resolve(strict=True)) as image:
        return image.size


def _pick(rows: list[dict], kinds: tuple[str, ...], *, exclude_source: str | None = None) -> dict | None:
    for kind in kinds:
        for row in rows:
            if row.get("kind") != kind:
                continue
            if exclude_source and row.get("sourceSha256") == exclude_source:
                continue
            return row
    return None


def plan(
    drawer: dict,
    *,
    width: int,
    height: int,
    duration_seconds: float,
) -> dict:
    if drawer.get("schema") != parts_harvester.DRAWER_SCHEMA:
        raise ValueError("Expected Parts Drawer")
    if width < 64 or height < 64 or duration_seconds <= 0:
        raise ValueError("Invalid stage geometry")

    rows = list(drawer.get("artifacts") or [])
    poster = _pick(rows, ("still", "crop"))
    texture = _pick(rows, ("texture", "mask"))
    behavior_row = _pick(rows, ("motion-behavior",))
    prop = None
    transplant = None

    if behavior_row is not None:
        prop = _pick(
            rows,
            ("crop", "still", "texture"),
            exclude_source=behavior_row.get("sourceSha256"),
        )
        if prop is None:
            prop = _pick(rows, ("crop", "still", "texture"))
        behavior = json.loads(Path(behavior_row["path"]).read_text(encoding="utf-8"))
        if prop is not None:
            transplant = parts_harvester.behavior_transplant(
                behavior,
                target_source_sha256=prop["sha256"],
                duration_seconds=duration_seconds,
                base_state={
                    "x": width * 0.69,
                    "y": height * 0.54,
                    "scale": 0.28,
                    "rotation": 0,
                },
            )

    layers = []
    witnesses = []

    if texture is not None:
        iw, ih = _image_size(texture["path"])
        scale = max(width / iw, height / ih)
        layers.append({
            "id": "harvest-texture",
            "source": texture["path"],
            "z": 3,
            "x": 0,
            "y": 0,
            "scale": round(scale, 6),
            "opacity": 0.22,
        })
        witnesses.append({
            "role": "texture",
            "artifactSha256": texture["sha256"],
            "sourceSha256": texture["sourceSha256"],
            "harvestId": texture["harvestId"],
        })

    if poster is not None:
        iw, ih = _image_size(poster["path"])
        target_w = width * 0.24
        scale = target_w / max(1, iw)
        layers.append({
            "id": "harvest-poster",
            "source": poster["path"],
            "z": 6,
            "x": round(width * 0.07, 6),
            "y": round(height * 0.12, 6),
            "scale": round(scale, 6),
            "rotation": -3,
            "opacity": 0.92,
        })
        witnesses.append({
            "role": "poster",
            "artifactSha256": poster["sha256"],
            "sourceSha256": poster["sourceSha256"],
            "harvestId": poster["harvestId"],
        })

    if prop is not None and transplant is not None:
        iw, ih = _image_size(prop["path"])
        target_w = width * 0.18
        base_scale = target_w / max(1, iw)
        keyframes = parts_harvester.behavior_keyframes(
            json.loads(Path(behavior_row["path"]).read_text(encoding="utf-8")),
            duration_seconds=duration_seconds,
            base_x=width * 0.69,
            base_y=height * 0.54,
            base_scale=base_scale,
            base_rotation=0,
        )
        layers.append({
            "id": "harvest-behavior-prop",
            "source": prop["path"],
            "z": 65,
            "x": round(width * 0.69, 6),
            "y": round(height * 0.54, 6),
            "scale": round(base_scale, 6),
            "rotation": 0,
            "opacity": 0.88,
            "keyframes": keyframes,
        })
        witnesses.append({
            "role": "behavior-prop",
            "appearanceArtifactSha256": prop["sha256"],
            "appearanceSourceSha256": prop["sourceSha256"],
            "behaviorArtifactSha256": behavior_row["sha256"],
            "behaviorSourceSha256": behavior_row["sourceSha256"],
            "behaviorTransplantId": transplant["id"],
        })

    moving = [
        {
            "kind": row["kind"],
            "path": row["path"],
            "sha256": row["sha256"],
            "sourceSha256": row["sourceSha256"],
            "harvestId": row["harvestId"],
            "suggestedRoles": ["television", "window", "portal", "dream", "flashback"],
        }
        for row in rows
        if row.get("kind") in {"loop", "fragment"}
    ][:8]

    body = {
        "schema": SCHEMA,
        "drawerId": drawer["id"],
        "canvas": {"width": width, "height": height, "duration": duration_seconds},
        "layers": layers,
        "witnesses": witnesses,
        "movingInserts": moving,
        "cost": {"externalGenerations": 0, "providerCredits": 0, "usdMicros": 0},
        "laws": [
            "APPEARANCE AUTHORITY != BEHAVIOR AUTHORITY",
            "STAGE DRESSING != SOURCE CANON",
            "MOVING INSERT PROPOSAL != AUTOMATIC PLACEMENT",
            "BEHAVIOR TRANSPLANT != SEMANTIC CORRESPONDENCE",
        ],
    }
    return {**body, "id": "parts-stage-dressing:" + _sha(body)[:24]}


def apply_to_performance(performance: dict, dressing: dict) -> dict:
    if performance.get("schema") != "haunted-blender/puppet-performance/v1":
        raise ValueError("Expected puppet performance")
    if dressing.get("schema") != SCHEMA:
        raise ValueError("Expected stage dressing")
    if abs(float(performance["duration"]) - float(dressing["canvas"]["duration"])) > 1e-6:
        raise ValueError("Stage dressing duration does not match performance")

    result = json.loads(json.dumps(performance))
    existing = {layer["id"] for layer in result["cutoutPlan"]["layers"]}
    for layer in dressing.get("layers") or []:
        if layer["id"] in existing:
            raise ValueError("Stage dressing layer id collision")
        result["cutoutPlan"]["layers"].append(layer)
        existing.add(layer["id"])

    result["harvestedStageDressing"] = {
        "id": dressing["id"],
        "drawerId": dressing["drawerId"],
        "witnesses": dressing["witnesses"],
        "movingInserts": dressing["movingInserts"],
    }
    canvas = result["cutoutPlan"]["canvas"]
    if dressing.get("movingInserts"):
        result["movingInsertPlan"] = moving_insert_stage.plan_from_dressing(
            dressing,
            width=int(canvas["width"]),
            height=int(canvas["height"]),
            fps=int(canvas["fps"]),
            duration_seconds=float(canvas["duration"]),
        )
    body = {k: v for k, v in result.items() if k != "id"}
    result["id"] = "puppet-performance:" + _sha(body)[:24]
    return result
