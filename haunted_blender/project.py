"""Versioned screenplay/scene/shot contracts and immutable production snapshots."""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from pathlib import Path

SCHEMA = "haunted-blender/film/v1"


def stable_bytes(data: dict) -> bytes:
    return json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def project_path(root: Path, project_id: str) -> Path:
    if not re.fullmatch(r"film-[0-9a-f]{16}", project_id):
        raise ValueError("Invalid film id")
    return root.expanduser().resolve() / "projects" / (project_id + ".json")


def new_film(root: Path, title: str) -> dict:
    title = title.strip()
    if not 0 < len(title) <= 240:
        raise ValueError("Film title must contain 1–240 characters")
    film = {
        "schema": SCHEMA,
        "id": "film-" + uuid.uuid4().hex[:16],
        "title": title,
        "logline": "",
        "creative_intent": "",
        "scenes": [],
        "assertions": [],  # claims about continuity are author-provided, never inferred facts
        "sound_design": {"status": "unimplemented", "notes": ""},
        "provenance_policy": "local-only; explicit source references; no implicit subject identity or consent",
    }
    save(root, film)
    return film


def load(root: Path, project_id: str) -> dict:
    return json.loads(project_path(root, project_id).read_text(encoding="utf-8"))


def save(root: Path, film: dict) -> None:
    validate(film)
    path = project_path(root, film["id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_bytes(stable_bytes(film) + b"\n")
    tmp.replace(path)


def add_scene(root: Path, film_id: str, title: str) -> dict:
    film = load(root, film_id)
    scene = {
        "id": "scene-" + uuid.uuid4().hex[:16],
        "title": title.strip() or "Untitled scene",
        "location": "",
        "dramatic_question": "",
        "character_references": [],
        "shots": [],
    }
    film["scenes"].append(scene)
    save(root, film)
    return scene


def add_shot(root: Path, film_id: str, scene_id: str, asset_id: str, duration_ms: int, direction: str = "") -> dict:
    film = load(root, film_id)
    scene = next((s for s in film["scenes"] if s["id"] == scene_id), None)
    if scene is None:
        raise ValueError(f"Unknown scene: {scene_id}")
    shot = {
        "id": "shot-" + uuid.uuid4().hex[:16],
        "source_asset_id": asset_id,
        "duration_ms": duration_ms,
        "direction": direction,
        "framing": "static",  # renderer v0 only handles static framing
        "dialogue": "",     # intentionally not emitted as speech by the v0 renderer
        "render_mode": "still-image/v1",
    }
    scene["shots"].append(shot)
    save(root, film)
    return shot


def validate(film: dict) -> None:
    if film.get("schema") != SCHEMA:
        raise ValueError("Unknown film schema version")
    if not isinstance(film.get("id"), str) or not re.fullmatch(r"film-[0-9a-f]{16}", film["id"]):
        raise ValueError("Invalid film id")
    if not isinstance(film.get("title"), str) or not film["title"].strip():
        raise ValueError("Missing film title")
    if not isinstance(film.get("scenes"), list):
        raise ValueError("Scenes must be a list")
    ids = set()
    for scene in film["scenes"]:
        if not isinstance(scene, dict) or not isinstance(scene.get("shots"), list):
            raise ValueError("Malformed scene")
        sid = scene.get("id")
        if not isinstance(sid, str) or sid in ids or not sid.startswith("scene-"):
            raise ValueError("Malformed or duplicate scene id")
        ids.add(sid)
        for shot in scene["shots"]:
            if not isinstance(shot, dict):
                raise ValueError("Malformed shot")
            shot_id = shot.get("id")
            if not isinstance(shot_id, str) or shot_id in ids or not shot_id.startswith("shot-"):
                raise ValueError("Malformed or duplicate shot id")
            ids.add(shot_id)
            if not isinstance(shot.get("source_asset_id"), str) or not shot["source_asset_id"].startswith("asset-"):
                raise ValueError("Shot needs a source asset id")
            if not isinstance(shot.get("duration_ms"), int) or not 250 <= shot["duration_ms"] <= 600000:
                raise ValueError("Shot duration must be 250–600000 milliseconds")
            if shot.get("render_mode") != "still-image/v1" or shot.get("framing") != "static":
                raise ValueError("Unknown or unsupported render mode/framing")


def freeze(root: Path, film_id: str) -> Path:
    film = load(root, film_id)
    validate(film)
    from .catalog import connect, digest_file, source_for_render
    con = connect(root)
    try:
        bindings = {}
        for scene in film["scenes"]:
            for shot in scene["shots"]:
                source = source_for_render(con, shot["source_asset_id"])
                path = Path(source["path"])
                if not path.is_file() or digest_file(path) != source["sha256"]:
                    raise ValueError(f"Source missing or changed since cataloging: {path}")
                bindings[shot["id"]] = {"frame_asset_id": source["id"], "sha256": source["sha256"]}
        film["asset_bindings"] = bindings
    finally:
        con.close()
    contents = stable_bytes(film)
    sha = hashlib.sha256(contents).hexdigest()
    folder = root.expanduser().resolve() / "snapshots" / film_id
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / (sha + ".json")
    if dest.exists() and dest.read_bytes() != contents + b"\n":
        raise ValueError("Snapshot collision or unexpected snapshot mutation")
    if not dest.exists():
        dest.write_bytes(contents + b"\n")
    return dest


def load_snapshot(root: Path, path: Path) -> tuple[dict, str]:
    path = path.expanduser().resolve(strict=True)
    allowed = (root.expanduser().resolve() / "snapshots").resolve()
    if allowed not in path.parents:
        raise ValueError("Render only frozen snapshots inside the local project vault")
    film = json.loads(path.read_text(encoding="utf-8"))
    validate(film)
    if not isinstance(film.get("asset_bindings"), dict) or set(film["asset_bindings"]) != {
        shot["id"] for scene in film["scenes"] for shot in scene["shots"]
    }:
        raise ValueError("Snapshot needs a binding for every shot")
    sha = hashlib.sha256(stable_bytes(film)).hexdigest()
    if path.name != sha + ".json" or path.parent.name != film["id"]:
        raise ValueError("Snapshot hash or project identity mismatch")
    return film, sha
