"""SCENE-ARTIFACT-001: approved static scene-world shots -> existing N0 renderer.

No changes to film/v1, scene-world/v0, alchemy/v1, the asset catalog or N0
render code. An artifact is a frozen instruction and source lineage, not footage
or evidence that a depicted fictional event happened.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

from . import alchemy, catalog, project, render, scene_weave

SCHEMA = "haunted-blender/accepted-scene-artifact/v0"
RECEIPT = "haunted-blender/scene-artifact-render-receipt/v0"
STILL_MS = 1800


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _sha(value):
    return hashlib.sha256(project.stable_bytes(value)).hexdigest()


def _root(root):
    return Path(root).expanduser().resolve()


def _snapshot_path(root, artifact_id, digest):
    _require(re.fullmatch(r"sceneart-[0-9a-f]{16}", artifact_id), "Invalid artifact ID")
    _require(re.fullmatch(r"[0-9a-f]{64}", digest), "Invalid artifact digest")
    return _root(root) / "snapshots" / "scene-artifacts" / artifact_id / (digest + ".json")


def _source_alignment(world, alchemy_plan):
    _require(world["material"]["alchemy_snapshot_sha256"] == alchemy_plan["snapshot_sha256"]
             and world["material"]["alchemy_recipe_id"] == alchemy_plan["recipe_id"],
             "SceneWorld is not sourced from this frozen Alchemy recipe")
    expected = [{"role": row["role"], "requested_asset_id": row["requested_asset_id"],
                 "frame_sha256": row["sha256"]} for row in alchemy_plan["segments"]]
    _require(world["material"]["roles"] == expected, "SceneWorld source order or frozen frame digests differ")


def _prepare(root, world_snapshot, alchemy_snapshot, selections):
    root = _root(root)
    world_path = Path(world_snapshot).expanduser().resolve(strict=True)
    alchemy_path = Path(alchemy_snapshot).expanduser().resolve(strict=True)
    world = scene_weave.load_snapshot(root, world_path)
    parent = alchemy.plan(root, alchemy_path)  # verifies frozen original and edited-image bytes
    _source_alignment(world, parent)
    _require(isinstance(selections, list) and 1 <= len(selections) <= len(world["beats"]),
             "Select one or more distinct story beats")
    chosen = []
    used = set()
    available = {item["role"]: item for item in parent["segments"]}
    con = catalog.connect(root)
    try:
        for selector in selections:
            _require(isinstance(selector, dict) and set(selector) == {"beat", "role", "candidate"},
                     "Selection requires beat, role and candidate only")
            beat, role, candidate_id = selector["beat"], selector["role"], selector["candidate"]
            _require(type(beat) is int and 0 <= beat < len(world["beats"]) and beat not in used,
                     "Invalid or repeated beat")
            used.add(beat)
            _require(role in available, "Unknown photographic role")
            # The existing renderer accepts only static framing. Do not claim an
            # insert or negative-space treatment was actually realized by it.
            _require(candidate_id == "wide",
                     "Only 'wide' is supported by the N0 static-image renderer")
            composition = scene_weave.compose(world, beat)
            candidate = next(item for item in composition["candidates"]
                             if item["id"] == candidate_id)
            _require(not candidate["story_patch"] and not candidate["knowledge_patch"]
                     and not candidate["possible_reveals"],
                     "A presentation-only shot cannot change story or disclosure")
            material = available[role]
            frame_id = material["frame_asset_id"]
            frame = con.execute("SELECT id,sha256,rights FROM assets WHERE id=?", (frame_id,)).fetchone()
            original = con.execute("SELECT id,rights FROM assets WHERE id=?",
                                   (material["requested_asset_id"],)).fetchone()
            _require(frame is not None and original is not None
                     and frame["sha256"] == material["sha256"],
                     "Catalog source or edited frame differs from frozen material")
            chosen.append({
                "beat": beat, "beat_id": world["beats"][beat]["id"], "role": role,
                "candidate_id": candidate_id, "candidate_sha256": candidate["candidate_sha256"],
                "known_to_audience": candidate["audience_fact_ids"],
                "requested_asset_id": material["requested_asset_id"],
                "frame_asset_id": frame_id, "frame_sha256": material["sha256"],
                "source_rights": original["rights"], "frame_rights": frame["rights"],
                "duration_ms": STILL_MS,
            })
    finally:
        con.close()
    _require([x["beat"] for x in chosen] == sorted(used), "Selected beats must be chronological")
    foundation = {
        "schema": SCHEMA, "status": "filmmaker_accepted_local_preview",
        "world_snapshot": str(world_path), "world_sha256": scene_weave.sha(world),
        "alchemy_snapshot": str(alchemy_path),
        "alchemy_snapshot_sha256": parent["snapshot_sha256"],
        "film_title": world["title"], "world_id": world["id"],
        "shots": chosen,
        "render_adapter": "ffmpeg-static-storyboard/v1",
        "render_scope": "silent 720p static photographic storyboard only",
        "distribution_authorized": False,
        "nonclaims": [
            "Approval of a local preview is not publication or likeness consent",
            "A still photograph does not perform fictional dialogue or motion",
            "An audience-disclosure proposal is not a witnessed audience event",
            "The source photograph does not establish fictional character identity",
        ],
    }
    foundation["id"] = "sceneart-" + _sha(foundation)[:16]
    return foundation


def accept(root, world_snapshot, alchemy_snapshot, selections, *, filmmaker_approval=False):
    _require(filmmaker_approval is True, "Explicit filmmaker approval required")
    artifact = _prepare(root, world_snapshot, alchemy_snapshot, selections)
    digest = _sha(artifact)
    dest = _snapshot_path(root, artifact["id"], digest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    expected = project.stable_bytes(artifact) + b"\n"
    try:
        with dest.open("xb") as handle:
            handle.write(expected)
    except FileExistsError:
        _require(dest.read_bytes() == expected, "Previously accepted artifact has changed")
    return {"artifact_id": artifact["id"], "snapshot": str(dest), "sha256": digest,
            "shot_count": len(artifact["shots"])}


def load(root, snapshot):
    path = Path(snapshot).expanduser().resolve(strict=True)
    _require(path.parent.parent == _root(root) / "snapshots" / "scene-artifacts",
             "Artifact is outside the private snapshot vault")
    artifact = json.loads(path.read_text(encoding="utf-8"))
    _require(artifact.get("schema") == SCHEMA and artifact.get("status") ==
             "filmmaker_accepted_local_preview" and artifact.get("distribution_authorized") is False,
             "Unknown artifact schema or publication scope")
    _require(path == _snapshot_path(root, artifact["id"], _sha(artifact)),
             "Artifact snapshot hash or identity mismatch")
    selections = [{"beat": s["beat"], "role": s["role"], "candidate": s["candidate_id"]}
                  for s in artifact["shots"]]
    fresh = _prepare(root, artifact["world_snapshot"], artifact["alchemy_snapshot"], selections)
    _require(fresh == artifact, "Accepted artifact has stale or changed source, world or candidate")
    return artifact, _sha(artifact)


def _film(artifact, digest):
    film = {
        "schema": project.SCHEMA, "id": "film-" + digest[:16],
        "title": artifact["film_title"],
        "logline": "", "creative_intent": "Local static photographic preview of accepted SceneWorld beats",
        "scenes": [], "assertions": [],
        "sound_design": {"status": "unimplemented", "notes": ""},
        "provenance_policy": "local preview; source and story witnesses in accepted Scene Artifact",
    }
    for item in artifact["shots"]:
        suffix = hashlib.sha256((digest + ":" + str(item["beat"])).encode()).hexdigest()[:16]
        film["scenes"].append({
            "id": "scene-" + suffix,
            "title": str(item["beat_id"]), "location": "", "dramatic_question": "",
            "character_references": [],
            "shots": [{
                "id": "shot-" + suffix, "source_asset_id": item["frame_asset_id"],
                "duration_ms": item["duration_ms"],
                "direction": "Static still preview; accepted candidate " + item["candidate_id"],
                "framing": "static", "dialogue": "", "render_mode": "still-image/v1",
            }],
        })
    project.validate(film)
    return film


def render_accepted(root, artifact_snapshot, out):
    root = _root(root)
    artifact, digest = load(root, artifact_snapshot)
    out = Path(out).expanduser().resolve()
    witness_path = out.with_suffix(out.suffix + ".scene-artifact.json")
    n0_receipt_path = out.with_suffix(out.suffix + ".receipt.json")
    _require(not out.exists() and not witness_path.exists() and not n0_receipt_path.exists(),
             "Refusing to overwrite an existing output or receipt")
    film = _film(artifact, digest)
    payload = project.stable_bytes(film)
    film_digest = hashlib.sha256(payload).hexdigest()
    folder = root / "snapshots" / film["id"]
    folder.mkdir(parents=True, exist_ok=True)
    film_snapshot = folder / (film_digest + ".json")
    expected = payload + b"\n"
    try:
        with film_snapshot.open("xb") as handle:
            handle.write(expected)
    except FileExistsError:
        _require(film_snapshot.read_bytes() == expected, "Existing film snapshot changed")
    # Reject a changed frame or forged N0 mapping before spending render time.
    preview = render.plan(root, film_snapshot)
    _require([s["sha256"] for s in preview["shots"]] ==
             [s["frame_sha256"] for s in artifact["shots"]],
             "N0 render plan disagrees with the accepted photographic artifact")
    # Existing N0 renderer owns FFmpeg, MP4 and its scoped execution receipt.
    result = render.render(root, film_snapshot, out)
    _require(result["status"] == "scoped_complete"
             and result["output_sha256"] == catalog.digest_file(out)
             and result["snapshot_sha256"] == film_digest,
             "N0 execution receipt did not match its accepted film")
    witness = {
        "schema": RECEIPT, "status": "scoped_complete",
        "artifact_snapshot_sha256": digest,
        "artifact_id": artifact["id"], "scene_world_sha256": artifact["world_sha256"],
        "source_alchemy_sha256": artifact["alchemy_snapshot_sha256"],
        "n0_film_snapshot_sha256": film_digest, "n0_receipt_sha256": catalog.digest_file(n0_receipt_path),
        "output_sha256": result["output_sha256"], "shot_count": len(artifact["shots"]),
        "claim": "One silent photographic storyboard rendered; no dialogue, animation or story realization",
        "distribution_authorized": False,
    }
    temp = witness_path.with_suffix(witness_path.suffix + ".tmp")
    try:
        with temp.open("xb") as handle:
            handle.write(project.stable_bytes(witness) + b"\n")
        os.replace(temp, witness_path)
    except Exception:
        temp.unlink(missing_ok=True)
        raise
    return {"artifact": artifact["id"], "output": str(out), "witness": str(witness_path),
            "shot_count": len(artifact["shots"]), "output_sha256": result["output_sha256"]}
